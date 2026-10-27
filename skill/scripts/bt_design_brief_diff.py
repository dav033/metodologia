"""Mechanical, readable difference between two UI briefs (`bt_design_ui_brief.build` output).

Lines are compared per `##` section; a removed and an added line with the same leading id (`R9`, `T2.5`) are one
change. Repository lines and the omitted-fields footer are machine-specific bookkeeping and never count.
"""
from __future__ import annotations

import re

HEAD = "Encabezado"
IGNORED_SECTIONS = ("Omitido a propósito",)
_ID = re.compile(r"^\s*(?:[-*]|\d+\.)\s+\**([A-Z]+[0-9][\w.]*)\**\s*[:—–.)-]")
_REPO = re.compile(r"^\s*-\s+repo\s")


def sections(text: str) -> dict[str, list[str]]:
    """`## heading` → its non-empty lines, in order; lines before the first heading go under HEAD."""
    out: dict[str, list[str]] = {HEAD: []}
    current = HEAD
    for line in (text or "").splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            out.setdefault(current, [])
        elif line.strip() and not _REPO.match(line):
            out[current].append(line.rstrip())
    return {k: v for k, v in out.items() if k not in IGNORED_SECTIONS}


def _key(line: str) -> str | None:
    found = _ID.match(line)
    return found.group(1) if found else None


def diff(before: str, after: str) -> list[dict]:
    """[{section, kind: changed|removed|added, before, after}] from `before` to `after`, section by section."""
    old, new = sections(before), sections(after)
    out = []
    for name in [*new, *(k for k in old if k not in new)]:
        was, now = old.get(name, []), new.get(name, [])
        removed = [line for line in was if line not in now]
        added = [line for line in now if line not in was]
        by_key = {_key(line): line for line in removed if _key(line)}
        fresh = []
        for line in added:
            pair = by_key.pop(_key(line), None) if _key(line) else None
            if pair is not None:
                removed.remove(pair)
                out.append({"section": name, "kind": "changed", "before": pair.strip(), "after": line.strip()})
            else:
                fresh.append({"section": name, "kind": "added", "before": "", "after": line.strip()})
        out += [{"section": name, "kind": "removed", "before": line.strip(), "after": ""} for line in removed] + fresh
    return out


def render(changes: list[dict]) -> str:
    """Plain-text form for a Designer brief: `+` added, `-` removed, `~` changed (before → after)."""
    if not changes:
        return "  (no UI-relevant difference between the two briefs)"
    lines, section = [], None
    for c in changes:
        if c["section"] != section:
            section = c["section"]
            lines.append(f"  [{section}]")
        if c["kind"] == "added":
            lines.append(f"    + {c['after']}")
        elif c["kind"] == "removed":
            lines.append(f"    - {c['before']}")
        else:
            lines.append(f"    ~ {c['before']}  →  {c['after']}")
    return "\n".join(lines)
