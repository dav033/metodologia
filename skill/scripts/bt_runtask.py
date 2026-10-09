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


def _tick_plan(rdir: Path, task_id: str, line: str) -> None:
    plan = rdir / "PLAN.md"
    if not plan.exists():
        return
    text = plan.read_text(encoding="utf-8")
    text = re.sub(rf"^(\s*[-*]\s+)\[ \](\s+{re.escape(task_id)}\b)", r"\1[x]\2", text, count=1, flags=re.M)
    plan.write_text(text.rstrip("\n") + f"\n- {dt.datetime.now():%Y-%m-%d %H:%M} {line}\n", encoding="utf-8")


def task_done(rdir: Path, task_id: str, evidence: str) -> str:
    def fn(state):
        rs.mark(state, task_id, "done", evidence=evidence or "(none given)", last_error=None)
    rs.update(rdir, fn)
    _tick_plan(rdir, task_id, f"{task_id} done (marathon) — {_one_line(evidence, 200)}")
    return f"{task_id} marked done"


def task_fail(rdir: Path, task_id: str, reason: str, blocked: bool = False) -> str:
    def fn(state):
        t = rs.get_task(state, task_id)
        if t is None:
            raise SystemExit(f"{task_id} is not in RUN.json")
        t["last_error"] = reason or "(no reason given)"
        t["status"] = "blocked" if blocked else "todo"
    rs.update(rdir, fn)
    return f"{task_id} marked {'blocked' if blocked else 'failed (the supervisor will retry or block it)'}"


def task_note(rdir: Path, task_id: str, text: str) -> str:
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
