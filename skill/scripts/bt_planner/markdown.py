"""PLAN.md reader: the task-line and milestone grammar this module understands (no other part of the methodology).

    ### M1 — title                      milestone heading (`###` or `####`, M<number>); any other heading ends it
    - [ ] T1 — title · repo: backend · after: T0, T0a · verify: `pytest -q` · files: src/a.py · resources: db · risk: high

Task ids look like T1, T2.1, T3a. Fields are separated by ` · `; `verify` counts only when backticked; `after` keeps
only task-id tokens; `files` with absolute or `..` paths are dropped as a whole. HTML comments are ignored. Legacy
`complexity:`/`size:`/`risk:` values are returned verbatim (lower-cased) and never converted to contract values.
"""
from __future__ import annotations

import re
from pathlib import Path

TASK_RE = re.compile(r"^\s*[-*]\s+\[( |x|X)\]\s+(T[0-9]+(?:\.[0-9]+)?[a-z]?)\s*(?:—|–|--|-|:)\s*(.+?)\s*$")
MILESTONE_RE = re.compile(r"^#{3,4}\s+(M[0-9]+)\b\s*(?:—|–|--|-|:)?\s*(.*?)\s*$")
HEADING_RE = re.compile(r"^#{1,4}\s+\S")
TASK_TOKEN_RE = re.compile(r"T[0-9]+(?:\.[0-9]+)?[a-z]?")


def _strip_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def _unsafe(value: str) -> bool:
    path = value.replace("\\", "/")
    return (path.startswith("/") or re.match(r"^[A-Za-z]:", path) is not None
            or any(part in ("", ".", "..") for part in path.split("/")))


def _list(raw: str | None, *, paths: bool) -> list[str] | None:
    if not raw or not raw.strip():
        return None
    values = [item.strip().strip("`\"'").strip() for item in raw.split(",")]
    if any(not v for v in values) or (paths and any(_unsafe(v) for v in values)):
        return None
    return values


def parse_task_line(rest: str) -> dict:
    verify = None
    found = re.search(r"verify:\s*`([^`]+)`", rest)
    if found:
        verify = found.group(1).strip()
        rest = rest[:found.start()] + "verify:" + rest[found.end():]
    parts = re.split(r"\s+·\s+", rest)
    fields = {}
    for part in parts[1:]:
        key, _, value = part.partition(":")
        fields[key.strip().lower()] = value.strip()
    return {"title": parts[0].strip(), "repo": fields.get("repo") or None, "verify": verify,
            "after": [t for t in re.split(r"[,\s]+", fields.get("after", "")) if TASK_TOKEN_RE.fullmatch(t)],
            "files": _list(fields.get("files"), paths=True), "resources": _list(fields.get("resources"), paths=False),
            "complexity": (fields.get("complexity") or fields.get("size") or "").lower() or None,
            "risk": (fields.get("risk") or "").lower() or None}


def parse(text: str) -> tuple[list[dict], list[dict]]:
    """(tasks, milestones). Tasks keep document order; milestones list only those that contain tasks."""
    tasks, titles, milestone = [], {}, None
    for line in _strip_comments(text).splitlines():
        head = MILESTONE_RE.match(line)
        if head:
            milestone = head.group(1)
            titles[milestone] = head.group(2)
            continue
        if HEADING_RE.match(line):
            milestone = None
            continue
        task = TASK_RE.match(line)
        if task:
            tasks.append({"id": task.group(2), "done": task.group(1) != " ", "milestone": milestone,
                          **parse_task_line(task.group(3))})
    stones: dict[str, dict] = {}
    for task in tasks:
        if task["milestone"]:
            stones.setdefault(task["milestone"], {"id": task["milestone"], "title": titles.get(task["milestone"], ""),
                                                  "tasks": []})["tasks"].append(task["id"])
    return tasks, list(stones.values())


def read(path: Path) -> tuple[list[dict], list[dict]]:
    try:
        return parse(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError):
        return [], []


def status(text: str) -> str:
    """First word of the `status:` front-matter value, lower-cased ('' when absent)."""
    for line in text.splitlines()[:12]:
        if line.startswith("status:"):
            value = line.partition(":")[2].strip()
            return value.split()[0].lower() if value else ""
    return ""
