"""PENDING.md as a sorted backlog: every open item carries urgency and complexity, and the file keeps itself ordered.

Canonical item line (detail lines indented under it move with it):
  - P-012 · <task> · urgency: high · complexity: S · added 2026-10-09 · <source>
Sections: ## Open (sorted: urgency high → med → low, then complexity S → M → L → ?, then ID), ## Blocked,
## Recently closed. Older formats are understood and rewritten: "Now/Next/Problems" sections, bare "high/med/low"
or "medium/alta/baja" tokens, unbulleted lines, items marked DONE/FIXED/MERGED/CLOSED (moved to Recently closed).
Nothing is ever dropped: unknown lines inside a section stay attached to the previous item or the section.
"""
from __future__ import annotations

import re

from bt_core import *  # noqa: F403

ITEM = re.compile(r"^\s*(?:[-*]\s+)?(?:~~)?(P-\d{3,})\b(.*)$")
URG = {"high": 0, "med": 1, "low": 2}
CPX = {"S": 0, "M": 1, "L": 2, "?": 3}
URG_WORDS = {"high": "high", "alta": "high", "urgent": "high", "critical": "high", "med": "med", "medium": "med",
             "media": "med", "normal": "med", "low": "low", "baja": "low"}
SECTION_URGENCY = {"now": "high", "problems": "high", "bugs": "high", "next": "med", "later": "low"}
# done markers: upper-case anywhere in the title ("Furniture — MERGED into …", "DONE 2026-10-09 …"), so a lower-case
# "merged" inside a description doesn't close an item
DONE_RE = re.compile(r"(?:^\s*✓)|\b(DONE|FIXED|MERGED|CLOSED|CERRADO|HECHO|RESUELTO)\b")

HEADER = """# {project} — Pending

_Sorted automatically by `bitacora.py pending` (urgency high → low, then complexity S → L: quick urgent wins first).
One line per item: `P-012 · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`._
"""


def _segments(rest: str) -> list[str]:
    return [s.strip() for s in re.split(r"\s+·\s+|\s·\s", rest.strip().lstrip("·—-: ").strip()) if s.strip()]


def parse_item(first: str, section: str) -> dict:
    m = ITEM.match(first)
    pid, rest = m.group(1), m.group(2)
    segs = _segments(rest)
    title = segs[0] if segs else ""
    urgency = complexity = None
    others = []
    for s in segs[1:]:
        low = s.lower()
        mu = re.match(r"urgency:\s*(\w+)", low)
        mc = re.match(r"complexity:\s*(\S+)", s, re.I)
        if mu:
            urgency = URG_WORDS.get(mu.group(1), "med")
        elif mc:
            complexity = mc.group(1).upper()[:1] if mc.group(1).upper()[:1] in CPX else "?"
        elif low in URG_WORDS and urgency is None:
            urgency = URG_WORDS[low]
        elif re.fullmatch(r"[sml]", low) and complexity is None:
            complexity = low.upper()
        else:
            others.append(s)
    sec = section.lower()
    if urgency is None:
        urgency = next((u for k, u in SECTION_URGENCY.items() if k in sec), "med")
    if "problem" in sec or "bug" in sec:
        title = title if title.lower().startswith("[bug]") else f"[bug] {title}"
    return {"id": pid, "title": title, "urgency": urgency, "complexity": complexity or "?", "others": others,
            "done": bool(DONE_RE.search(title)) or "closed" in sec}


def render_item(it: dict) -> str:
    parts = [it["id"], it["title"], f"urgency: {it['urgency']}", f"complexity: {it['complexity']}", *it["others"]]
    return "- " + " · ".join(p for p in parts if p)


def parse(text: str) -> tuple[dict[str, list[dict]], list[str]]:
    """→ ({section: [items with 'details']}, loose lines that weren't items)."""
    sections: dict[str, list[dict]] = {}
    loose: list[str] = []
    section = "Open"
    current = None
    for line in text.splitlines():
        if line.startswith("## "):
            section, current = line[3:].strip(), None
            continue
        if line.startswith("# ") or (line.startswith("_") and current is None) or not line.strip():
            continue
        if ITEM.match(line):
            current = parse_item(line, section)
            current["details"] = []
            sections.setdefault(section, []).append(current)
        elif current is not None:
            current["details"].append(line if line.startswith((" ", "\t")) else "  " + line.strip())
        elif line.strip() not in ("_None_", "-"):
            loose.append(line)
    return sections, loose


def sort_key(it: dict) -> tuple:
    return (URG.get(it["urgency"], 1), CPX.get(it["complexity"], 3), int(it["id"].split("-")[1]))


def normalize(text: str, project: str) -> str:
    sections, loose = parse(text)
    open_items, blocked, closed = [], [], []
    for name, items in sections.items():
        low = name.lower()
        for it in items:
            if "block" in low:
                blocked.append(it)
            elif it["done"] or "closed" in low or "done" in low:
                closed.append(it)
            else:
                open_items.append(it)

    def block(items: list[dict], sort: bool = True) -> str:
        if not items:
            return "_None_\n"
        items = sorted(items, key=sort_key) if sort else items
        return "".join(render_item(it) + "\n" + "".join(d + "\n" for d in it["details"]) for it in items)

    out = HEADER.format(project=project)
    out += "\n## Open\n" + block(open_items)
    out += "\n## Blocked\n" + block(blocked)
    out += "\n## Recently closed\n" + block(closed, sort=False)
    if loose:
        out += "\n## Notes\n" + "\n".join(loose) + "\n"
    return out


def sort_file(pdir: Path) -> bool:
    f = pdir / "PENDING.md"
    if not f.exists():
        return False
    old = f.read_text(encoding="utf-8")
    new = normalize(old, pdir.name)
    if new != old:
        f.write_text(new, encoding="utf-8")
        return True
    return False


def top(pdir: Path, n: int = 5) -> list[str]:
    """First n open items (already sorted) as short lines, for indexes and context."""
    f = pdir / "PENDING.md"
    if not f.exists():
        return []
    sections, _ = parse(f.read_text(encoding="utf-8"))
    items = [it for name, its in sections.items() if "block" not in name.lower() and "closed" not in name.lower()
             for it in its if not it["done"]]
    return [f"{it['id']} · {it['title'][:90]} · {it['urgency']}/{it['complexity']}"
            for it in sorted(items, key=sort_key)[:n]]
