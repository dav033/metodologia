"""Shared run-task helpers: plan ticking, secret-safe text for stored evidence, and the one place that turns a stuck
task into a PENDING.md item."""
from __future__ import annotations

import re
import sys

from bt_core import *  # noqa: F403

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


def _safe_text(text: str) -> str:
    """Evidence, reasons and notes are stored in RUN.json (versioned) and quoted in later prompts, possibly to another
    provider: anything that looks like a secret is withheld."""
    try:
        import bt_learn
        if bt_learn._secret(text or ""):
            return "[withheld: the text looked like it contained a secret; refer to files instead]"
    except Exception as exc:  # fail closed: an unavailable detector must not let the text through
        print(f"[task] secret filter unavailable ({type(exc).__name__}); text withheld", file=sys.stderr)
        return "[withheld: the secret filter could not run]" if text else text
    return text


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
