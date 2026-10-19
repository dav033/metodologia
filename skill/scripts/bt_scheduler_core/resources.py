"""Logical resource claims and their conflicts. Conservative: when the surface is unknown, serialise.

A claim is `(resource, mode)`; mode "s" = shared, "x" = exclusive. Resources are normalised ids:
`*` (everything), `repo:<name>`, `res:<name>` (declared shared_resources, always exclusive), `path:<repo>:<pattern>`
(expected_paths; two path claims in one repository conflict when one static prefix contains the other). Paths are
hints, not proof of independence: they only ever ADD conflicts. Worktree isolation is M3's job; this is logical.
A task whose plan `scope` is in `Config.exclusive_scopes` claims its whole repository exclusively: it runs alone there.
"""
from __future__ import annotations

from collections.abc import Iterable

from .config import Config
from .plan import TaskSpec

Claim = tuple[str, str]
ALL = "*"
_GLOB = "*?[{"


def claims_for(task: TaskSpec, config: Config) -> list[Claim]:
    out: list[Claim] = [(f"res:{r.strip()}", "x") for r in task.shared_resources]
    repo = task.repository.strip()
    if repo:
        out.append((f"repo:{repo}", "x" if config.repository_isolation == "exclusive" else "s"))
        out += [(f"path:{repo}:{_norm(p)}", "x") for p in task.expected_paths]
    if config.exclusive_scopes and task.meta.get("scope") in config.exclusive_scopes:
        out.append((f"repo:{repo}", "x") if repo else (ALL, "x"))
    known = bool(task.shared_resources or (repo and task.expected_paths))
    if not known and config.unknown_surface == "serialize":
        out.append((f"repo:{repo}", "x") if repo else (ALL, "x"))
    merged: dict[str, str] = {}
    for resource, mode in out:
        merged[resource] = "x" if "x" in (mode, merged.get(resource, "s")) else "s"   # exclusive dominates
    return sorted(merged.items())


def _norm(pattern: str) -> str:
    return pattern.strip().replace("\\", "/").lstrip("./").rstrip("/")


def _prefix(resource: str) -> tuple[str, str]:
    _kind, repo, pattern = resource.split(":", 2)
    cut = min((pattern.find(ch) for ch in _GLOB if ch in pattern), default=len(pattern))
    return repo, pattern[:cut].rstrip("/")


def _overlap(a: str, b: str) -> bool:
    (ra, pa), (rb, pb) = _prefix(a), _prefix(b)
    if ra != rb:
        return False
    if not pa or not pb:
        return True
    return pa == pb or pa.startswith(pb + "/") or pb.startswith(pa + "/")


def conflict(a: Iterable[Claim], b: Iterable[Claim]) -> bool:
    b = list(b)
    for ra, ma in a:
        for rb, mb in b:
            if ra == ALL or rb == ALL:
                return True
            if ra.startswith("path:") and rb.startswith("path:"):
                if _overlap(ra, rb):
                    return True
            elif ra == rb and "x" in (ma, mb):
                return True
    return False


def first_conflict(wanted: Iterable[Claim], held: dict[str, list[list[str]]]) -> str:
    """The attempt id holding a conflicting claim, or ''."""
    wanted = list(wanted)
    for attempt_id, claims in held.items():
        if conflict(wanted, [(r, m) for r, m in claims]):
            return attempt_id
    return ""
