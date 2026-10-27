"""The Planner's working memory, kept in files so that any session can take over without losing anything.

An agent's conversation is not a safe place for what it learned: sessions get restarted, killed or replaced. Findings
(with file references), decisions and their reasons, open questions, to-dos and a handoff note are appended here with
`bitacora.py planning note REQ-NNN --kind K --text "..."`, and `planning resume` prints them first thing. Append-only
JSON lines in `<req>/.planning/notes.jsonl`.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
from pathlib import Path

DIR, FILE = ".planning", "notes.jsonl"
KINDS = ("finding", "decision", "question", "todo", "handoff")
MAX_TEXT = 1500
KEEP = 40


def _path(rdir: Path) -> Path:
    return Path(rdir) / DIR / FILE


def add(rdir: Path, text: str, kind: str = "finding", by: str = "planner") -> str:
    text = re.sub(r"[ \t]+", " ", (text or "").strip())[:MAX_TEXT]
    if not text:
        raise SystemExit("planning note needs --text")
    if kind not in KINDS:
        raise SystemExit(f"--kind must be one of {', '.join(KINDS)}")
    target = _path(rdir)
    target.parent.mkdir(parents=True, exist_ok=True)
    row = {"at": dt.datetime.now().astimezone().isoformat(timespec="seconds"), "kind": kind, "by": by, "text": text}
    with target.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(row, ensure_ascii=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    return f"Nota guardada ({kind})."


def notes(rdir: Path) -> list[dict]:
    out = []
    try:
        for line in _path(rdir).read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if isinstance(row, dict) and isinstance(row.get("text"), str) and row.get("kind") in KINDS:
                out.append(row)
    except (OSError, UnicodeError):
        pass
    return out


def render(rdir: Path, keep: int = KEEP) -> list[str]:
    """Lines for the resume briefing: the last handoff and the open questions/to-dos first, then recent findings."""
    rows = notes(rdir)
    if not rows:
        return []
    lines = [f"Planner notes ({len(rows)} saved; what your predecessor learned and why it decided things, oldest first):"]
    handoff = next((r for r in reversed(rows) if r["kind"] == "handoff"), None)
    if handoff:
        lines.append(f"- HANDOFF {handoff['at'][11:16]}: {handoff['text']}")
    for row in rows[-keep:]:
        if row is not handoff:
            lines.append(f"- {row['at'][11:16]} {row['kind']}: {row['text']}")
    return lines
