"""Marathon outcomes: classify a finished session (done / failed / timeout / usage limit / verify failed / blocked /
escalated), update the task (attempts, model tier) and the log, and turn stuck tasks into PENDING items."""
from __future__ import annotations

import subprocess
import time

from bt_core import *  # noqa: F403
import bt_runprompt as rp
import bt_runstate as rs
import bt_runtask as rt
import bt_runtier as tier_
from bt_runutil import backoff_override, notify, say

LIMIT_RE = re.compile(r"usage limit|rate[ _]limit|\b429\b|quota|limit reached|try again at|hit your limit|"
                      r"limit will reset|overloaded_error", re.I)
VERIFY_TIMEOUT = 600
LIMIT_STREAK_MAX = 8  # consecutive usage-limit results on one task before the next one counts as an attempt
LIMIT_RESULTS = ("usage_limit", "limit_streak")  # results that send the supervisor to wait


def _json(text: str):
    try:
        return json.loads(text)
    except ValueError:
        return None


def _from_result(obj: dict) -> dict:
    return {"text": str(obj.get("result") or obj.get("error") or ""), "cost": obj.get("total_cost_usd"),
            "is_error": bool(obj.get("is_error")) or str(obj.get("subtype") or "").startswith("error")}


def parse_output(raw: str) -> dict:
    """{text, is_error, cost} of a session. Claude stream-json: the last `result` event (when it never came, only the
    non-JSON lines count, so tool output inside the transcript is not mistaken for the agent's verdict); a single JSON
    object (--output-format json) is unwrapped; anything else is plain text."""
    raw = (raw or "").strip()
    whole = _json(raw) if raw.startswith("{") else None
    if isinstance(whole, dict):
        return _from_result(whole)
    plain, events = [], False
    for line in reversed(raw.splitlines()):
        if line.startswith("{"):  # an event, even one cut in half by a kill
            obj = _json(line)
            if isinstance(obj, dict) and obj.get("type") == "result":
                return _from_result(obj)
            events = True
        elif len(plain) < 200:
            plain.append(line)
    text = "\n".join(reversed(plain)) if events else raw
    return {"text": text[-4000:], "is_error": False, "cost": None}


def _result_text(info: dict) -> tuple[str, bool]:
    out = info.get("parsed") or parse_output(info["text"])
    info["parsed"] = out
    return out["text"], out["is_error"]


_RESETS_IN = re.compile(r"resets?\s+in\s+(?:(\d+)\s*d(?:ays?)?\s*)?(?:(\d+)\s*h(?:ours?)?\s*)?(?:(\d+)\s*m(?:in(?:ute)?s?)?\s*)?"
                        r"(?:(\d+)\s*s(?:ec(?:ond)?s?)?)?", re.I)


def reset_epoch(text: str, now: float | None = None) -> int:
    """Epoch of a relative reset announcement ('Resets in 166h43m25s'); 0 when the text carries none."""
    for m in _RESETS_IN.finditer(text or ""):
        days, hours, minutes, seconds = (int(g or 0) for g in m.groups())
        total = days * 86400 + hours * 3600 + minutes * 60 + seconds
        if total > 0:
            return int((time.time() if now is None else now) + total)
    return 0


_MONTHS = {m: i + 1 for i, m in enumerate(("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov",
                                            "dec"))}
_MONTHS.update({"ene": 1, "abr": 4, "ago": 8, "set": 9, "dic": 12, "fev": 2, "avr": 4, "mai": 5, "out": 10, "dez": 12})
_TRY_AT = re.compile(r"(?:try again|resets?|available again)\s+(?:at|on)\s+(?:([A-Za-z]{3})[a-z]*\.?\s+(\d{1,2})"
                     r"(?:st|nd|rd|th)?,?\s+(?:(\d{4}),?\s+)?(?:at\s+)?)?(\d{1,2})(?::(\d{2}))?\s*([AaPp]\.?[Mm]\.?)?")


def absolute_reset_epoch(text: str, now: float | None = None) -> int:
    """Epoch of an absolute reset announcement in local time ('try again at Oct 13th, 2026 1:08 AM', 'resets at
    3pm'); 0 when the text carries none. A time without a date means its next occurrence."""
    current = dt.datetime.fromtimestamp(time.time() if now is None else now)
    for m in _TRY_AT.finditer(text or ""):
        month, day, year, hour, minute, ampm = m.groups()
        if not (month or ampm or minute):  # a bare number after "at" is not a time
            continue
        hour, minute = int(hour), int(minute or 0)
        mark = (ampm or "").replace(".", "").lower()
        if mark == "pm" and hour < 12:
            hour += 12
        if mark == "am" and hour == 12:
            hour = 0
        try:
            if month:
                if month[:3].lower() not in _MONTHS:
                    continue
                when = dt.datetime(int(year or current.year), _MONTHS[month[:3].lower()], int(day), hour, minute)
                if not year and when < current - dt.timedelta(days=1):
                    when = when.replace(year=when.year + 1)
            else:
                when = current.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if when <= current:
                    when += dt.timedelta(days=1)
        except ValueError:
            continue
        if when > current:
            return int(when.timestamp())
    return 0


def limit_line(text: str, context: int = 0) -> str:
    """The line that announces the limit (for logs and the quota record), not whatever the output ended with.
    `context` adds that many following lines (a reset time is sometimes printed right below the message)."""
    lines = (text or "").splitlines()
    for i in range(len(lines) - 1, -1, -1):
        if LIMIT_RE.search(lines[i]) and not lines[i].lstrip().startswith(("{", "[")):
            return " ".join(" ".join(lines[i:i + 1 + context]).split())[:200 + 200 * context]
    return ""


def detect_limit(info: dict) -> int | None:
    """A usage/rate-limit message in the output of a FAILED session (non-zero exit or is_error): a successful run whose
    text merely mentions '429' or 'quota' is never a limit. Returns the reset epoch (0 = unknown) or None."""
    text, is_error = _result_text(info)
    if not (info["rc"] or is_error) or not LIMIT_RE.search(text[-4000:]):
        return None
    m = re.search(r"limit reached\|(\d{9,10})", text) or re.search(r"limit reached\|(\d{9,10})", info["text"][-20000:])
    if m:
        return int(m.group(1))
    # Only the provider's own limit message says when the limit resets: any other "resets in" of the transcript
    # (a cache, a test fixture) must not send the run to sleep.
    for source in (text, info["text"][-4000:]):
        line = limit_line(source, 2) or (source if len(source) < 400 else "")
        epoch = reset_epoch(line) or absolute_reset_epoch(line)
        if epoch:
            return epoch
    return 0


def _session_fields(info: dict) -> dict:
    """What the session ran with, for its log entry."""
    _result_text(info)
    return {"model": info.get("model"), "effort": info.get("effort"), "cost_usd": info["parsed"].get("cost"),
            "agent": info.get("agent"), "profile": info.get("profile"),
            "early_exit": True if info.get("early_exit") else None}


def verify_task(project: str, t: dict, workdir: Path, state: dict | None = None) -> tuple[bool, str]:
    """Run the task's verify command in its repo. An unknown repo role fails (it must not fall back to another dir).
    An audit has no command of its own: every verify of the milestone it closes must pass again (the auditor may
    have changed code)."""
    if t.get("synthetic") and t.get("kind") == "audit" and state is not None:
        seen = set()
        for tid in t.get("after") or []:
            member = rs.get_task(state, tid)
            if not member or not member.get("verify") or (member["verify"], member.get("repo")) in seen:
                continue
            seen.add((member["verify"], member.get("repo")))
            ok, out = verify_task(project, member, workdir)
            if not ok:
                return False, f"{tid}: {member['verify']} -> {out}"
        return True, ""
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
        remaining = epoch - time.time() if epoch else 0
        if remaining > 0:  # a known reset: wait for it, but wake at least every 12 h (a wrong parse can't lock a run)
            until = dt.datetime.now() + dt.timedelta(seconds=min(remaining + 60, 12 * 3600))
        else:
            until = dt.datetime.now() + dt.timedelta(minutes=minutes)
        if override is not None:
            until = dt.datetime.now() + dt.timedelta(seconds=override)
        s.update(status="waiting", waiting_until=until.isoformat(timespec="seconds"), wait_step=step + 1)
    state = rs.update(rdir, fn)
    msg = f"usage/rate limit; waiting until {state['waiting_until']}"
    say(state, msg)
    if not notified:
        notify(f"{project} {req}: marathon waiting", msg)
    return True


def _fail_attempt(task: dict, err: str, max_attempts: int) -> str | None:
    """Count a failed attempt and climb one tier. Returns why the task is stuck, or None. A repeated error only
    blocks once the task already failed at the top tier; below it, it escalates like any other failure."""
    h = rs.error_hash(err)
    repeated = h in task["error_hashes"]
    tier = tier_.tier_of(task)
    task.update(status="todo", attempts=task["attempts"] + 1, last_error=err,
                error_hashes=(task["error_hashes"] + [h])[-10:])
    if task["attempts"] >= max_attempts:
        return f"{task['attempts']} failed attempts"
    if repeated and tier >= tier_.TOP:
        return "same error twice, the second time at the top model tier"
    task["tier"] = min(tier + 1, tier_.TOP)
    return None


def _escalation(t: dict, n: int) -> dict | None:
    """The `task escalate` this very session asked for, if any."""
    esc = t.get("escalation")
    return esc if esc and str(esc.get("session")) == str(n) else None


def settle_task(project: str, rdir: Path, task_id: str, n: int, info: dict, workdir: Path,
                skip_reason: str | None = None) -> str:
    """Classify the finished session, update the task (attempts, model tier), record the log. Returns the result."""
    state = rs.load(rdir)
    t = rs.get_task(state, task_id)
    err, summary = None, _result_text(info)[0][:300]
    escalation = _escalation(t, n)
    if info["stopped"]:
        result, summary = "failed", "stopped by the user"
    elif t.get("claimed_done") or t["status"] == "done":  # a bare "done" is a RUN.json from before claims existed
        ok, out = verify_task(project, t, workdir, state)
        result = "done" if ok else "verify_failed"
        err = None if ok else f"verify failed: {t['verify'] or 'milestone verifies'} -> {out}"
        summary = (t["evidence"] or summary) if ok else err
    elif t["status"] == "blocked":
        result, summary = "blocked", t["last_error"] or "blocked by the agent"
    elif escalation:
        result, summary = "escalated", f"escalated to {escalation['to']}: {escalation['reason']}"
    elif t["status"] == "todo" and t["last_error"]:  # the agent called task fail (the session began as in_progress)
        result, err = "failed", t["last_error"]
    elif skip_reason:  # a milestone session never reached it because a task it depends on did not finish
        result, summary = "skipped", skip_reason
    elif info["timed_out"]:  # before the limit check: a killed session's half-written output proves nothing
        result, err = "timeout", f"session timeout after {state['limits']['session_timeout_min']} min"
    elif detect_limit(info) is not None:
        result = "usage_limit"
        if t.get("limit_streak", 0) + 1 >= LIMIT_STREAK_MAX:  # never-ending 'limit' = a misread failure, not a limit
            result = "limit_streak"
            summary = f"usage-limit message {LIMIT_STREAK_MAX} sessions in a row: {summary[:160]}"
    else:
        result, err = "failed", f"session ended without task done/fail (rc={info['rc']}): {summary[:200]}"
    if info.get("recovered"):
        summary = f"re-verified after a supervisor restart: {summary}"
    stuck = {}

    def fn(s):
        task = rs.get_task(s, task_id)
        task.pop("escalation", None)
        if not info["stopped"]:  # a claim cut short by a stop is verified on the next start (recover_claims)
            task.pop("claimed_done", None)
        task["limit_streak"] = task.get("limit_streak", 0) + 1 if result == "usage_limit" else 0
        if info.get("agent") and result != "skipped":  # who ran it last: the router alternates providers on failure
            task["last_route"] = {"agent": info.get("agent"), "profile": info.get("profile"),
                                  "model": info.get("model"), "effort": info.get("effort"),
                                  "result": "stopped" if info["stopped"] else result}  # a stop is nobody's failure
        reason = None
        if result == "done":
            task["status"] = "done"
        elif result in ("usage_limit", "skipped") or info["stopped"]:
            task["status"] = "todo"
        elif result == "limit_streak":  # not an attempt nor a failure: no error_hash, no tier climb, never blocks
            task.update(status="todo", limit_streaks=task.get("limit_streaks", 0) + 1)
        elif result == "escalated":  # counts toward max_attempts, not toward 'same error twice'
            task.update(status="todo", attempts=task["attempts"] + 1)
            if task["attempts"] >= s["limits"]["max_attempts"]:
                reason = f"{task['attempts']} attempts, the last one escalated ({summary})"
        elif result in ("timeout", "failed", "verify_failed"):
            reason = _fail_attempt(task, err, s["limits"]["max_attempts"])
            reason = reason and f"{reason}: {err}"
        elif result == "blocked":
            stuck.update(reason=task["last_error"] or "blocked by the agent", task=dict(task))
        if reason:
            stuck.update(reason=reason, task=dict(task))
            task["status"] = "blocked"
        if result not in LIMIT_RESULTS:
            s["wait_step"] = 0
        rs.record(s, n, task_id, "stopped" if info["stopped"] else result, summary, info["seconds"],
                  **_session_fields(info))
    state = rs.update(rdir, fn)
    if result == "done":  # the checkbox is ticked only once verify passed, so --resume can trust it
        rt.tick_plan(rdir, task_id, f"{task_id} done (marathon) — {rt._one_line(t['evidence'] or summary, 200)}")
    if result == "limit_streak":  # a real limit or a misread failure: only a human can tell, so say it every time
        count = rs.get_task(state, task_id)["limit_streaks"]
        notify(f"{project} {state['req']}: {task_id} limit streak #{count}",
               f"{LIMIT_STREAK_MAX} sessions in a row hit a usage-limit message; check the session logs")
    if stuck:
        pid = rt.add_blocked_pending(project, state["req"], stuck["task"], stuck["reason"])
        rs.update(rdir, lambda s: rs.mark(s, task_id, "blocked", pending_id=pid))
        notify(f"{project} {state['req']}: {task_id} blocked", f"{stuck['reason'][:120]} ({pid})")
        say(state, f"{task_id} BLOCKED -> {pid}")
    return result


def recover_claims(project: str, rdir: Path, workdir: Path) -> None:
    """After a crash between the agent's `task done` and the supervisor's verify, the claim is still unverified: verify
    it now, before any new work is picked, and settle it like a finished session (done, or a failed attempt)."""
    for task in list(rs.load(rdir)["tasks"]):
        if task.get("claimed_done") and task["status"] in ("todo", "in_progress"):
            state = rs.load(rdir)
            info = {"rc": 0, "text": "", "stopped": False, "timed_out": False, "seconds": 0, "model": None,
                    "effort": None, "recovered": True}
            say(state, f"{task['id']} claimed done before a restart; re-running its verify")
            result = settle_task(project, rdir, task["id"], state["sessions"], info, workdir)
            say(rs.load(rdir), f"{task['id']} re-verified -> {result}")


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
        rs.record(s, n, rp.FINAL_TASK, result, _result_text(info)[0][:300], info["seconds"], **_session_fields(info))
    rs.update(rdir, fn)
    return result
