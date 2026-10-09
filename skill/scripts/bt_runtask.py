"""Marathon commands used by the session agent and the user: `task done|fail|note` and `run-control`.

Also the one place that turns a stuck task into a PENDING.md item, shared with the supervisor (bt_run).
"""
from __future__ import annotations

import re

from bt_core import *  # noqa: F403
import bt_runstate as rs

_DONE_WORDS = re.compile(r"\b(DONE|FIXED|MERGED|CLOSED|CERRADO|HECHO|RESUELTO)\b")


def _one_line(text: str, limit: int = 160) -> str:
    """Single line, no '·' (the PENDING field separator), no upper-case 'DONE' markers (they would close the item)."""
    text = " ".join((text or "").replace("·", "-").split())[:limit]
    return _DONE_WORDS.sub(lambda m: m.group(0).lower(), text)


def _comment_spans(text: str) -> list[tuple[int, int]]:
    return [m.span() for m in re.finditer(r"<!--.*?-->", text, re.S)]


def tick_plan(rdir: Path, task_id: str, line: str) -> None:
    """Tick the task's checkbox (first match OUTSIDE html comments: the template keeps examples there) and log it."""
    plan = rdir / "PLAN.md"
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


def _own_task(task_id: str) -> None:
    """Inside a supervised session the agent may only touch the task it was given."""
    current = os.environ.get("BITACORA_TASK")
    if current and current != task_id:
        raise SystemExit(f"this session works on {current}, not {task_id}: only {current} can be marked")


def task_done(rdir: Path, task_id: str, evidence: str) -> str:
    """Mark the task done in RUN.json. Under a supervisor (env BITACORA_RUN) the PLAN.md tick is deferred until the
    supervisor's own verify passes (bt_runsettle); run by hand it ticks right away."""
    _own_task(task_id)

    def fn(state):
        rs.mark(state, task_id, "done", evidence=evidence or "(none given)", last_error=None)
    rs.update(rdir, fn)
    if not os.environ.get("BITACORA_RUN"):
        tick_plan(rdir, task_id, f"{task_id} done (marathon) — {_one_line(evidence, 200)}")
    return f"{task_id} marked done"


def task_fail(rdir: Path, task_id: str, reason: str, blocked: bool = False) -> str:
    _own_task(task_id)

    def fn(state):
        t = rs.get_task(state, task_id)
        if t is None:
            raise SystemExit(f"{task_id} is not in RUN.json")
        t["last_error"] = reason or "(no reason given)"
        t["status"] = "blocked" if blocked else "todo"
    rs.update(rdir, fn)
    return f"{task_id} marked {'blocked' if blocked else 'failed (the supervisor will retry or block it)'}"


def task_note(rdir: Path, task_id: str, text: str) -> str:
    _own_task(task_id)

    def fn(state):
        t = rs.get_task(state, task_id)
        if t is None:
            raise SystemExit(f"{task_id} is not in RUN.json")
        t.setdefault("notes", []).append(" ".join(text.split())[:500])
        t["notes"] = t["notes"][-10:]
    rs.update(rdir, fn)
    return f"note saved on {task_id}"


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
    pdir = ROOT / project
    pid = next_id(pdir, "P")  # noqa: F405
    line = (f"- {pid} · [blocked] {req} {task['id']}: {_one_line(task['title'], 80)} — {_one_line(reason, 140)}"
            f" · urgency: high · complexity: ? · added {today().isoformat()} · marathon\n")  # noqa: F405
    f = pdir / "PENDING.md"
    text = f.read_text(encoding="utf-8") if f.exists() else ""
    if re.search(r"^## Open\s*$", text, re.M):
        text = re.sub(r"^(## Open[ \t]*\n)(\s*_None_\s*\n)?", lambda m: m.group(1) + line, text, count=1, flags=re.M)
    else:
        text = text.rstrip("\n") + "\n\n## Open\n" + line
    f.write_text(text, encoding="utf-8")
    bt_pending.sort_file(pdir)
    return pid
