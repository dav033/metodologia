"""`/go/<ID>`: one short link for every id the bitácora writes (REQ-005, T4, P-013, D-045, LG-001).

Agents and humans cite ids in the terminal; `resolve` maps one to the page and anchor that shows it, or to the list of
projects that all have it when the bare id is ambiguous. Pure over the bitácora root: it reads, never writes.

    /go/REQ-005            /go/metodologia/REQ-005         /go/metodologia/REQ-005/T4
    /go/P-013              /go/metodologia/P-013           /go/D-045      /go/LG-001
"""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import quote

_REQ = re.compile(r"REQ-(\d+)", re.I)
_TASK = re.compile(r"T(\d+)", re.I)
_KIND = {"P": ("PENDING.md", "pending"), "D": ("DECISIONS.md", "decisions")}


def _projects(root: Path) -> list[Path]:
    try:
        return sorted(p for p in Path(root).iterdir() if p.is_dir() and not p.name.startswith("."))
    except OSError:
        return []


def _has_req(pdir: Path, number: str) -> Path | None:
    for rdir in sorted((pdir / "requirements").glob(f"REQ-{int(number):03d}-*")):
        if rdir.is_dir():
            return rdir
    return None


def _plan_has(rdir: Path, task: str) -> bool:
    """Whether the requirement's plan names this task (so the anchor exists on its page)."""
    return any(_mentions(rdir / name, task) for name in ("PLAN.json", "PLAN.md"))


def _mentions(path: Path, ident: str) -> bool:
    try:
        return re.search(rf"(?<![\w-]){re.escape(ident)}(?!\d)", path.read_text(encoding="utf-8")) is not None
    except OSError:
        return False


def _target(pdir: Path, ident: str, task: str | None) -> str | None:
    """The URL of `ident` inside one project, or None when the project has no such id."""
    project = quote(pdir.name)
    req = _REQ.fullmatch(ident)
    if req:
        rdir = _has_req(pdir, req.group(1))
        if rdir is None:
            return None
        rid = f"REQ-{int(req.group(1)):03d}"
        if task and _plan_has(rdir, task):
            return f"/plans/{project}/{rid}#t-{quote(task)}"
        return f"/p/{project}/req/{rid}"
    kind = ident.split("-")[0]
    if kind in _KIND and _mentions(pdir / _KIND[kind][0], ident):
        return f"/p/{project}?tab={_KIND[kind][1]}#{ident}"
    return None


def normalize(ident: str) -> str | None:
    match = re.fullmatch(r"(REQ|LG|P|D)-(\d+)", ident.strip(), re.I)
    return f"{match.group(1).upper()}-{int(match.group(2)):03d}" if match else None


def resolve(root: Path, parts: list[str]) -> dict:
    """`parts` = the path after /go/. Returns {"url": ...} | {"choices": [(project, url)]} | {"error": text}."""
    root = Path(root)
    project = None
    if parts and not normalize(parts[0]) and (root / parts[0]).is_dir():
        project, parts = parts[0], parts[1:]
    if not parts or normalize(parts[0]) is None:
        return {"error": "No reconozco ese identificador (usa REQ-005, P-013, D-045 o LG-001)."}
    ident = normalize(parts[0])
    task = None
    if len(parts) > 1:
        match = _TASK.fullmatch(parts[1])
        task = f"T{int(match.group(1))}" if match else None
    if ident.startswith("LG-"):
        return {"url": f"/learnings#{ident}"} if _mentions(root / "LEARNINGS.md", ident) else \
            {"error": f"No encuentro {ident} en los aprendizajes."}
    pool = [root / project] if project else _projects(root)
    found = [(p.name, url) for p in pool if (url := _target(p, ident, task))]
    if len(found) == 1:
        return {"url": found[0][1]}
    if found:
        return {"choices": found, "id": ident}
    return {"error": f"No encuentro {ident}" + (f" en {project}." if project else " en ningún proyecto.")}
