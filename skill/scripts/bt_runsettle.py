"""Marathon outcomes: classify a finished session (done / failed / timeout / usage limit / verify failed / blocked),
update the task and the log, and turn stuck tasks into PENDING items."""
from __future__ import annotations

import subprocess
import time

from bt_core import *  # noqa: F403
import bt_runprompt as rp
import bt_runstate as rs
import bt_runtask as rt
from bt_runutil import backoff_override, notify, say

LIMIT_RE = re.compile(r"usage limit|rate[ _]limit|\b429\b|quota|limit reached|try again at|hit your limit|"
                      r"limit will reset|overloaded_error", re.I)
VERIFY_TIMEOUT = 600
LIMIT_STREAK_MAX = 8  # consecutive usage-limit results on one task before the next one counts as a failed attempt


def _result_text(info: dict) -> tuple[str, bool]:
    """(human text of the session output, looks like an error). Claude's --output-format json is unwrapped."""
    raw = info["text"].strip()
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict):
            return str(obj.get("result") or obj.get("error") or ""), bool(obj.get("is_error"))
    except ValueError:
        pass
    return raw[-4000:], False


def detect_limit(info: dict) -> int | None:
    """A usage/rate-limit message in the output of a FAILED session (non-zero exit or is_error): a successful run whose
    text merely mentions '429' or 'quota' is never a limit. Returns the reset epoch (0 = unknown) or None."""
    text, is_error = _result_text(info)
    if not (info["rc"] or is_error) or not LIMIT_RE.search(text[-4000:]):
        return None
    m = re.search(r"limit reached\|(\d{9,10})", info["text"])
    return int(m.group(1)) if m else 0


def verify_task(project: str, t: dict, workdir: Path) -> tuple[bool, str]:
    """Run the task's verify command in its repo. An unknown repo role fails (it must not fall back to another dir)."""
    if not t["verify"]:
        return True, ""
    cwd = workdir
    if t["repo"]:
        repos = ws.repos(ROOT, project)
        if t["repo"] not in repos:
            return False, f"unknown repo role '{t['repo']}' (registered: {', '.join(repos) or 'none'})"
        cwd = repos[t["repo"]]
    return run_verify(t["verify"], cwd)


def run_verify(cmd: str, cwd: Path) -> tuple[bool, str]:
    try:
        res = subprocess.run(cmd, shell=True, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8",
                             errors="replace", timeout=VERIFY_TIMEOUT)
    except subprocess.TimeoutExpired:
        return False, f"timeout after {VERIFY_TIMEOUT // 60} min"
    return res.returncode == 0, ((res.stdout or "") + (res.stderr or ""))[-600:]


# ---------------------------------------------------------------- outcomes

def enter_wait(rdir: Path, project: str, req: str, epoch: int, notified: bool) -> bool:
    def fn(s):
        step = s.get("wait_step", 0)
        minutes = min(30 * 2 ** step, 240)
        override = backoff_override()
        until = dt.datetime.fromtimestamp(epoch) if epoch and 0 < epoch - time.time() < 8 * 3600 \
            else dt.datetime.now() + dt.timedelta(minutes=minutes)
        if override is not None:
            until = dt.datetime.now() + dt.timedelta(seconds=override)
        s.update(status="waiting", waiting_until=until.isoformat(timespec="seconds"), wait_step=step + 1)
    state = rs.update(rdir, fn)
    msg = f"usage/rate limit; waiting until {state['waiting_until']}"
    say(state, msg)
    if not notified:
        notify(f"{project} {req}: marathon waiting", msg)
    return True


def _stuck_reason(t: dict, max_attempts: int, repeated: bool) -> str | None:
    if repeated:
        return "same error twice"
    return f"{t['attempts']} failed attempts" if t["attempts"] >= max_attempts else None


def settle_task(project: str, rdir: Path, task_id: str, n: int, info: dict, workdir: Path) -> str:
    """Classify the finished session, update the task, record the log. Returns the result label."""
    state = rs.load(rdir)
    t = rs.get_task(state, task_id)
    err, summary = None, _result_text(info)[0][:300]
    if info["stopped"]:
        result, summary = "failed", "stopped by the user"
    elif t["status"] == "done":
        ok, out = verify_task(project, t, workdir)
        result = "done" if ok else "verify_failed"
        err = None if ok else f"verify failed: {t['verify']} -> {out}"
        summary = (t["evidence"] or summary) if ok else err
    elif t["status"] == "blocked":
        result, summary = "blocked", t["last_error"] or "blocked by the agent"
    elif detect_limit(info) is not None:
        result = "usage_limit"
        if t.get("limit_streak", 0) + 1 >= LIMIT_STREAK_MAX:  # never-ending 'limit' = a misread failure, not a limit
            result, err = "failed", f"usage-limit message {LIMIT_STREAK_MAX} sessions in a row: {summary[:160]}"
    elif info["timed_out"]:
        result, err = "timeout", f"session timeout after {state['limits']['session_timeout_min']} min"
    else:
        result = "failed"
        err = t["last_error"] if t["status"] == "todo" and t["last_error"] else \
            f"session ended without task done/fail (rc={info['rc']}): {summary[:200]}"
    stuck = {}

    def fn(s):
        task = rs.get_task(s, task_id)
        task["limit_streak"] = task.get("limit_streak", 0) + 1 if result == "usage_limit" else 0
        if result == "usage_limit" or info["stopped"]:
            task["status"] = "todo"
        elif result in ("timeout", "failed", "verify_failed"):
            h = rs.error_hash(err)
            repeated = h in task["error_hashes"]
            task.update(status="todo", attempts=task["attempts"] + 1, last_error=err,
                        error_hashes=(task["error_hashes"] + [h])[-10:])
            reason = _stuck_reason(task, s["limits"]["max_attempts"], repeated)
            if reason:
                stuck.update(reason=f"{reason}: {err}", task=dict(task))
                task["status"] = "blocked"
        elif result == "blocked":
            stuck.update(reason=task["last_error"] or "blocked by the agent", task=dict(task))
        if result != "usage_limit":
            s["wait_step"] = 0
        rs.record(s, n, task_id, result, summary, info["seconds"])
    state = rs.update(rdir, fn)
    if result == "done":  # the checkbox is ticked only once verify passed, so --resume can trust it
        rt.tick_plan(rdir, task_id, f"{task_id} done (marathon) — {rt._one_line(t['evidence'] or summary, 200)}")
    if stuck:
        pid = rt.add_blocked_pending(project, state["req"], stuck["task"], stuck["reason"])
        rs.update(rdir, lambda s: rs.mark(s, task_id, "blocked", pending_id=pid))
        notify(f"{project} {state['req']}: {task_id} blocked", f"{stuck['reason'][:120]} ({pid})")
        say(state, f"{task_id} BLOCKED -> {pid}")
    return result


def settle_final(project: str, rdir: Path, n: int, info: dict, started: float) -> str:
    report = rdir / "REPORT.md"
    if report.exists() and report.stat().st_mtime >= started - 1:
        result = "done"
    elif detect_limit(info) is not None:
        result = "usage_limit"
    else:
        result = "timeout" if info["timed_out"] else "failed"

    def fn(s):
        fin = s.setdefault("final", {"attempts": 0})
        if result == "done":
            fin["done"] = True
        elif result != "usage_limit" and not info["stopped"]:
            fin["attempts"] += 1
        if result != "usage_limit":
            s["wait_step"] = 0
        rs.record(s, n, rp.FINAL_TASK, result, _result_text(info)[0][:300], info["seconds"])
    rs.update(rdir, fn)
    return result
