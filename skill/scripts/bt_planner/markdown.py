"""PLAN.md reader: the task-line and milestone grammar this module understands (no other part of the methodology).

    ### M1 — title                      milestone heading (`###` or `####`, M<number>); any other heading ends it
    - [ ] T1 — title · repo: backend · after: T0, T0a · verify: `pytest -q` · files: src/a.py · resources: db · risk: high

Task ids look like T1, T2.1, T3a. Fields are separated by ` · `; `verify` counts only when backticked; `after` keeps
only task-id tokens; `files` with absolute or `..` paths are dropped as a whole. HTML comments are ignored. Legacy
`complexity:`/`size:`/`risk:` values are returned verbatim (lower-cased) and never converted to contract values.

What the tolerant fields above silently drop is reported, never swallowed: `parse_document` returns `problems` for a
task id or milestone heading that appears twice, a field repeated on one line, an `after` entry that is not a task id,
an unusable `files`/`resources` value, a `verify:` that is not a backticked command, a misspelt field name
(`repository:` for `repo:`) and a checkbox line whose id is a near miss (`t1`, `T-1`). `sync.check` turns those
into errors, so PLAN.md cannot say one thing to the supervisor and another to the contract.
"""
from __future__ import annotations

import re
from pathlib import Path

TASK_RE = re.compile(r"^\s*[-*]\s+\[( |x|X)\]\s+(T[0-9]+(?:\.[0-9]+)?[a-z]?)\s*(?:—|–|--|-|:)\s*(.+?)\s*$")
MILESTONE_RE = re.compile(r"^#{3,4}\s+(M[0-9]+)\b\s*(?:—|–|--|-|:)?\s*(.*?)\s*$")
HEADING_RE = re.compile(r"^#{1,4}\s+\S")
TASK_TOKEN_RE = re.compile(r"T[0-9]+(?:\.[0-9]+)?[a-z]?")


def _strip_comments(text: str) -> str:
    """Remove HTML comments but keep their newlines, so reported line numbers match the file. Linear: an unclosed
    `<!--` swallows the rest of the document instead of backtracking."""
    out: list[str] = []
    pos = 0
    while True:
        start = text.find("<!--", pos)
        if start < 0:
            out.append(text[pos:])
            break
        out.append(text[pos:start])
        end = text.find("-->", start + 4)
        stop = len(text) if end < 0 else end + 3
        out.append("\n" * text.count("\n", start, stop))
        if end < 0:
            break
        pos = stop
    return "".join(out)


def _unsafe(value: str) -> bool:
    path = value.replace("\\", "/")
    return ("\0" in path or path.startswith("/") or re.match(r"^[A-Za-z]:", path) is not None
            or any(part in ("", ".", "..") for part in path.split("/")))


def _list(raw: str | None, *, paths: bool) -> list[str] | None:
    if not raw or not raw.strip():
        return None
    values = [item.strip().strip("`\"'").strip() for item in raw.split(",")]
    if any(not v for v in values) or (paths and any(_unsafe(v) for v in values)):
        return None
    return values


NEAR_MISS_KEYS = {"repository": "repo", "depends": "after", "depends_on": "after", "dependencies": "after",
                  "deps": "after", "verification": "verify", "test": "verify", "tests": "verify", "file": "files",
                  "paths": "files", "resource": "resources", "shared_resources": "resources", "cover": "covers",
                  "subplan_id": "subplan", "ui_work": "ui"}
SCHEMA_13_KEYS = ("subplan", "ui")
NEAR_TASK_RE = re.compile(r"^\s*[-*]\s+\[[ xX]\]\s+[*_`]*([Tt][-_.]?[0-9][\w.-]*?)[*_`]*(?:\s|$)")


def parse_task_line(rest: str, problems: list[str] | None = None, annotations: list[str] | None = None) -> dict:
    """Fields of one task line. Pass `problems` to collect what the tolerant parsing would otherwise drop silently;
    `annotations` collects schema 1.3 `subplan`/`ui` issues, which only a 1.3 plan reports (legacy plans ignore them)."""
    issues = problems if problems is not None else []
    notes = annotations if annotations is not None else issues
    verify = None
    found = re.search(r"verify:\s*`([^`]+)`", rest)
    if found:
        verify = found.group(1).strip()
        rest = rest[:found.start()] + "verify:" + rest[found.end():]
    parts = re.split(r"\s+·\s+", rest)
    fields: dict[str, str] = {}
    for part in parts[1:]:
        key, _, value = part.partition(":")
        key = key.strip().lower()
        if key in fields:
            issues.append(f"field '{key}' is given more than once")
        if key in NEAR_MISS_KEYS:
            (notes if NEAR_MISS_KEYS[key] in SCHEMA_13_KEYS else issues).append(f"field '{key}:' is not read; the field is '{NEAR_MISS_KEYS[key]}:'")
        fields[key] = value.strip()
    if "verify" in fields and verify is None:
        issues.append("verify must be a backticked command (verify: `cmd`); it is ignored as written")
    after_raw = [t for t in re.split(r"[,\s]+", fields.get("after", "")) if t]
    after = [t for t in after_raw if TASK_TOKEN_RE.fullmatch(t)]
    for token in after_raw:
        if token not in after:
            issues.append(f"after: {token!r} is not a task id")
    if len(set(after)) != len(after):
        issues.append("after: lists the same task more than once")
    files = _list(fields.get("files"), paths=True)
    if fields.get("files", "").strip() and files is None:
        issues.append("files: contains an empty entry or an absolute / '..' path; the whole list is ignored")
    resources = _list(fields.get("resources"), paths=False)
    if fields.get("resources", "").strip() and resources is None:
        issues.append("resources: contains an empty entry; the whole list is ignored")
    covers = _list(fields.get("covers"), paths=False)
    if "covers" in fields and covers is None:
        issues.append("covers: needs a non-empty comma-separated list; the whole list is ignored")
    elif covers is not None and len(set(covers)) != len(covers):
        issues.append("covers: lists the same requirement more than once")
    kind = fields.get("kind") or None
    if "kind" in fields and kind is None:
        issues.append("kind: needs a non-empty Scheduler-supported kind")
    result = {"title": parts[0].strip(), "repo": fields.get("repo") or None, "verify": verify, "after": after,
              "files": files, "resources": resources, "covers": covers, "kind": kind,
              "complexity": (fields.get("complexity") or fields.get("size") or "").lower() or None,
              "risk": (fields.get("risk") or "").lower() or None}
    if "subplan" in fields:
        subplan = fields["subplan"].strip()
        if re.fullmatch(r"SP-[1-9][0-9]*", subplan):
            result["subplan"] = subplan
        else:
            notes.append("subplan: must be SP-n with a positive integer")
    if "ui" in fields:
        ui = fields["ui"].strip().lower()
        if ui in ("yes", "no"):
            result["ui"] = ui == "yes"
        else:
            notes.append("ui: must be yes or no")
    return result


def parse_document(text: str) -> dict:
    """{tasks, milestones, problems, annotation_problems}. Tasks keep document order and carry `line`; milestones list only those that
    contain tasks. `problems` are PLAN.md-only ambiguities (see module docstring), each naming its line."""
    tasks: list[dict] = []
    titles: dict[str, str] = {}
    headings: dict[str, list[tuple[int, str]]] = {}
    problems: list[str] = []
    annotations: list[str] = []
    milestone = None
    for number, line in enumerate(_strip_comments(text).splitlines(), start=1):
        head = MILESTONE_RE.match(line)
        if head:
            milestone = head.group(1)
            titles[milestone] = head.group(2)  # last heading wins, exactly as the supervisor's parser reads it
            headings.setdefault(milestone, []).append((number, head.group(2)))
            continue
        if HEADING_RE.match(line):
            milestone = None
            continue
        task = TASK_RE.match(line)
        near = None if task else NEAR_TASK_RE.match(line)
        if near:
            problems.append(f"PLAN.md line {number}: {near.group(1)!r} looks like a task line but is not a task id "
                            "(use T1, T2.1, T3a); it is not part of the plan")
        if task:
            local: list[str] = []
            notes: list[str] = []
            fields = parse_task_line(task.group(3), local, notes)
            problems += [f"PLAN.md line {number}: {task.group(2)}: {issue}" for issue in local]
            annotations += [f"PLAN.md line {number}: {task.group(2)}: {issue}" for issue in notes]
            tasks.append({"id": task.group(2), "done": task.group(1) != " ", "milestone": milestone, "line": number,
                          **fields})
    seen: dict[str, list[int]] = {}
    for task in tasks:
        seen.setdefault(task["id"], []).append(task["line"])
    for tid, lines in seen.items():
        if len(lines) > 1:
            problems.append(f"{tid}: defined {len(lines)} times in PLAN.md (lines {', '.join(map(str, lines))}); "
                            "task ids must be unique")
    for mid, found in headings.items():
        if len(found) > 1 and len({title.strip().casefold() for _, title in found}) > 1:
            problems.append(f"{mid}: milestone heading appears {len(found)} times in PLAN.md with different titles "
                            f"(lines {', '.join(str(n) for n, _ in found)}); a milestone has one title")
    stones: dict[str, dict] = {}
    for task in tasks:
        if task["milestone"]:
            stones.setdefault(task["milestone"], {"id": task["milestone"], "title": titles.get(task["milestone"], ""),
                                                  "tasks": []})["tasks"].append(task["id"])
    return {"tasks": tasks, "milestones": list(stones.values()), "problems": problems,
            "annotation_problems": annotations}


def parse(text: str) -> tuple[list[dict], list[dict]]:
    """(tasks, milestones) — the tolerant view; use `parse_document` to also learn what was ambiguous."""
    doc = parse_document(text)
    return doc["tasks"], doc["milestones"]


def read_document(path: Path) -> dict:
    try:
        return parse_document(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError):
        return {"tasks": [], "milestones": [], "problems": [], "annotation_problems": []}


def read(path: Path) -> tuple[list[dict], list[dict]]:
    doc = read_document(path)
    return doc["tasks"], doc["milestones"]


def status(text: str) -> str:
    """First word of the `status:` front-matter value, lower-cased ('' when absent)."""
    for line in text.splitlines()[:12]:
        if line.startswith("status:"):
            value = line.partition(":")[2].strip()
            return value.split()[0].lower() if value else ""
    return ""
