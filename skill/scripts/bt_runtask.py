"""Marathon commands used by the session agent and the user: `task done|fail|note|escalate` and `run-control`.

Also the one place that turns a stuck task into a PENDING.md item, shared with the supervisor (bt_run).
"""
from __future__ import annotations

import re

from bt_core import *  # noqa: F403
import bt_runstate as rs
import bt_runtier as tier_

_DONE_WORDS = re.compile(r"\b(DONE|FIXED|MERGED|CLOSED|CERRADO|HECHO|RESUELTO)\b")


def _one_line(text: str, limit: int = 160) -> str:
    """Single line, no '·' (the PENDING field separator), no upper-case 'DONE' markers (they would close the item)."""
    text = " ".join((text or "").replace("·", "-").split())[:limit]
    return _DONE_WORDS.sub(lambda m: m.group(0).lower(), text)


def _comment_spans(text: str) -> list[tuple[int, int]]:
    return [m.span() for m in re.finditer(r"<!--.*?-->", text, re.S)]


def tick_plan(rdir: Path, task_id: str, line: str) -> None:
    """Tick the task's checkbox (first match OUTSIDE html comments: the template keeps examples there) and log it."""
    from bt_lock import central_lock
    plan = rdir / "PLAN.md"
    with central_lock("plan"):  # concurrent sessions each tick their own task: read-modify-write must not interleave
        if not plan.exists():
            return
        text = plan.read_text(encoding="utf-8")
        spans = _comment_spans(text)
        pat = re.compile(rf"^([ \t]*[-*][ \t]+)\[ \](\s+{re.escape(task_id)}\b)", re.M)
        for m in pat.finditer(text):
            if not any(a <= m.start() < b for a, b in spans):
                text = text[:m.start()] + m.group(1) + "[x]" + m.group(2) + text[m.end():]
                break
        plan.write_text(text.rstrip("\n") + f"\n- {dt.datetime.now():%Y-%m-%d %H:%M} {line}\n", encoding="utf-8")


def _own_task(task_id: str, rdir: Path) -> None:
    """Inside a supervised session the agent may only touch the task it was given, in the run it belongs to: a task id
    alone is ambiguous across requirements (every plan has a T1) and projects."""
    run, project, current = os.environ.get("BITACORA_RUN"), os.environ.get("BITACORA_PROJECT"), \
        os.environ.get("BITACORA_TASK")
    req = "-".join(Path(rdir).name.split("-")[:2])
    owner = Path(rdir).parents[1].name
    if run and run != req:
        raise SystemExit(f"this session belongs to {run}, not {req}: it cannot change that run's tasks")
    if project and project != owner:
        raise SystemExit(f"this session belongs to project {project}, not {owner}")
    if current and task_id not in current.split(","):  # a milestone session owns several tasks
        raise SystemExit(f"this session works on {current}, not {task_id}: only {current} can be marked")


def _safe_text(text: str) -> str:
    """Evidence, reasons and notes are stored in RUN.json (versioned) and quoted in later prompts, possibly to another
    provider: anything that looks like a secret is withheld."""
    try:
        import bt_learn
        if bt_learn._secret(text or ""):
            return "[withheld: the text looked like it contained a secret; refer to files instead]"
    except Exception:
        pass
    return text


def task_done(rdir: Path, task_id: str, evidence: str) -> str:
    """Mark the task done in RUN.json. Under a supervisor (env BITACORA_RUN) this is only a claim (`claimed_done`): the
    task becomes `done` and the PLAN.md tick happens once the supervisor's own verify passes (bt_runsettle), also after
    a restart. Run by hand it is done and ticked right away."""
    _own_task(task_id, rdir)
    supervised = bool(os.environ.get("BITACORA_RUN"))
    evidence = _safe_text(evidence)

    def fn(state):
        fields = {"evidence": evidence or "(none given)", "last_error": None}
        if supervised:
            if (rs.get_task(state, task_id) or {}).get("status") in ("done", "blocked"):
                return  # a late or duplicate `done` must not reopen a verified or blocked task
            rs.mark(state, task_id, "in_progress", claimed_done=True, **fields)
        else:
            rs.mark(state, task_id, "done", **fields).pop("claimed_done", None)
    rs.update(rdir, fn)
    if not supervised:
        tick_plan(rdir, task_id, f"{task_id} done (marathon) — {_one_line(evidence, 200)}")
    return f"{task_id} marked done" + (" (the supervisor verifies it next)" if supervised else "")


def task_fail(rdir: Path, task_id: str, reason: str, blocked: bool = False) -> str:
    _own_task(task_id, rdir)

    def fn(state):
        t = rs.get_task(state, task_id)
        if t is None:
            raise SystemExit(f"{task_id} is not in RUN.json")
        t["last_error"] = _safe_text(reason) or "(no reason given)"
        t["status"] = "blocked" if blocked else "todo"
        t.pop("claimed_done", None)  # the agent took its `done` back
    rs.update(rdir, fn)
    return f"{task_id} marked {'blocked' if blocked else 'failed (the supervisor will retry or block it)'}"


def task_note(rdir: Path, task_id: str, text: str) -> str:
    _own_task(task_id, rdir)

    def fn(state):
        t = rs.get_task(state, task_id)
        if t is None:
            raise SystemExit(f"{task_id} is not in RUN.json")
        t.setdefault("notes", []).append(" ".join(_safe_text(text).split())[:500])
        t["notes"] = t["notes"][-10:]
    rs.update(rdir, fn)
    return f"note saved on {task_id}"


def task_escalate(rdir: Path, task_id: str, to: str, reason: str) -> str:
    """Move the task up the model ladder (only up: a target at or below its tier is refused). From inside a supervised
    session it also flags the session as
    'escalated': the supervisor counts it toward max_attempts but not as a failure for stuck detection."""
    _own_task(task_id, rdir)
    target = tier_.TARGETS.get((to or "").strip().lower())
    if target is None:
        raise SystemExit(f"--to must be one of: {', '.join(tier_.TARGETS)}")
    reason = " ".join((reason or "(no reason given)").split())[:500]

    def fn(state):
        t = rs.get_task(state, task_id)
        if t is None:
            raise SystemExit(f"{task_id} is not in RUN.json")
        if tier_.tier_of(t) >= target:  # escalating in place would burn attempts without changing anything
            raise SystemExit(f"{task_id} already runs at tier {tier_.tier_of(t)} (>= {to}): nothing to escalate to; "
                             f"use `task fail --reason \"...\"` (add --blocked if it needs a human)")
        t["tier"] = target
        t["notes"] = (t.get("notes", []) + [f"escalated to {to}: {reason}"])[-10:]
        if os.environ.get("BITACORA_RUN"):
            t["escalation"] = {"to": to, "reason": reason, "session": os.environ.get("BITACORA_SESSION"),
                               "at": rs.now_iso()}
    rs.update(rdir, fn)
    return f"{task_id} escalated to {to}: stop now, the next session runs on the stronger model"


def run_control(rdir: Path, action: str) -> str:
    value = None if action == "resume" else action

    def fn(state):
        state["control"] = value
    state = rs.update(rdir, fn)
    msg = f"control: {value or 'cleared (resume)'}"
    if state.get("status") in ("stopped", "blocked", "done") or rs.is_stale(state, 5):
        msg += f"\nNo supervisor seems to be running (status {state.get('status')}). Start it: bitacora.py run {state['req']} --resume"
    return msg


def add_blocked_pending(project: str, req: str, task: dict, reason: str) -> str:
    """Append a [blocked] item to PENDING.md > Open and re-sort. Returns its P-id."""
    import bt_pending
    from bt_lock import central_lock
    pdir = ROOT / project
    with central_lock("pending"):  # id allocation + read-modify-write of PENDING.md is one critical section
        pid = next_id(pdir, "P")  # noqa: F405
        line = (f"- {pid} · [blocked] {req} {task['id']}: {_one_line(task['title'], 80)} — {_one_line(reason, 140)}"
                f" · urgency: high · complexity: ? · added {today().isoformat()} · marathon\n")  # noqa: F405
        f = pdir / "PENDING.md"
        text = f.read_text(encoding="utf-8") if f.exists() else ""
        if re.search(r"^## Open\s*$", text, re.M):
            text = re.sub(r"^(## Open[ \t]*\n)(\s*_None_\s*\n)?", lambda m: m.group(1) + line, text, count=1,
                          flags=re.M)
        else:
            text = text.rstrip("\n") + "\n\n## Open\n" + line
        f.write_text(text, encoding="utf-8")
        bt_pending.sort_file(pdir)
    return pid
