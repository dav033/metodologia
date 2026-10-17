"""Approved-plan loader: reads a frozen PLAN.json, binds it to an approved hash, resolves the dependency DAG.

The core never decides what "approved" means: the caller supplies the sha256 of the approved revision (whatever
trusted record it keeps) and the text must hash to it. Any valid JSON is NOT an approved plan. Only the fields the
core uses are validated here; classification fields travel untouched as opaque `meta` for the decision module.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .errors import SchedulerError

SUPPORTED_MAJOR = 1
PLAN_SCHEMA_CAPABILITIES = frozenset({"1.0.0", "1.1.0", "1.2.0"})
SCHEMA_1_2_SINCE = (1, 2, 0)
TASK_KINDS = frozenset({"implement", "test", "docs", "audit", "research"})
VERIFICATION_CATEGORIES = frozenset({"static", "functional", "integration", "regression", "product"})
MAX_BYTES = 2_000_000
MAX_TASKS = 10_000
HASH_RE = re.compile(r"[0-9a-f]{64}")
VERSION_RE = re.compile(r"([0-9]+)\.([0-9]+)\.([0-9]+)")
LEGACY_OPAQUE_KEYS = ("title", "objective", "complexity", "scope", "estimated_minutes", "risk", "coupling",
                      "confidence", "estimate_rationale", "classification_evidence")
OPAQUE_KEYS = (*LEGACY_OPAQUE_KEYS, "kind")


@dataclass(frozen=True, eq=False)
class TaskSpec:
    id: str
    milestone_id: str
    after: tuple[str, ...]
    repository: str
    shared_resources: tuple[str, ...]
    expected_paths: tuple[str, ...]
    acceptance_criteria: tuple[str, ...]
    verification: tuple[Mapping[str, Any], ...]
    meta: Mapping[str, Any] = field(default_factory=dict)  # opaque to the core: passed to the decision port as is


@dataclass(frozen=True, eq=False)
class Plan:
    plan_id: str
    revision: int
    schema_version: str
    sha256: str
    tasks: tuple[TaskSpec, ...]  # in the order of the plan (the deterministic tie-break everywhere)

    def __post_init__(self):
        object.__setattr__(self, "_by_id", {t.id: t for t in self.tasks})

    def task(self, task_id: str) -> TaskSpec:
        try:
            return self._by_id[task_id]  # type: ignore[attr-defined]
        except KeyError:
            raise SchedulerError("UNKNOWN_TASK", f"{task_id!r} is not in plan {self.plan_id} r{self.revision}") from None

    def ids(self) -> tuple[str, ...]:
        return tuple(t.id for t in self.tasks)

    def dependents(self) -> dict[str, tuple[str, ...]]:
        out: dict[str, list[str]] = {t.id: [] for t in self.tasks}
        for t in self.tasks:
            for dep in t.after:
                out[dep].append(t.id)
        return {k: tuple(v) for k, v in out.items()}

    def descendants(self, task_id: str) -> frozenset[str]:
        children, seen, stack = self.dependents(), set(), [task_id]
        while stack:
            for child in children[stack.pop()]:
                if child not in seen:
                    seen.add(child)
                    stack.append(child)
        return frozenset(seen)

    def ancestors(self, task_id: str) -> frozenset[str]:
        seen, stack = set(), [task_id]
        while stack:
            for dep in self.task(stack.pop()).after:
                if dep not in seen:
                    seen.add(dep)
                    stack.append(dep)
        return frozenset(seen)


def _reject_constant(name: str):
    raise ValueError(f"non-standard JSON constant {name}")


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _strings(value: object) -> bool:
    return isinstance(value, list) and all(_text(v) for v in value)


def _int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def load_plan(source: str | bytes, *, approved_sha256: str, plan_id: str | None = None,
              revision: int | None = None) -> Plan:
    """Parse and validate `source` (the exact text of the frozen revision). Raises SchedulerError; creates nothing."""
    if not isinstance(approved_sha256, str) or not HASH_RE.fullmatch(approved_sha256):
        raise SchedulerError("PLAN_NOT_APPROVED", "an approved sha256 (64 lowercase hex chars) is required")
    raw = source.encode("utf-8") if isinstance(source, str) else bytes(source)
    if len(raw) > MAX_BYTES:
        raise SchedulerError("PLAN_UNREADABLE", f"plan larger than {MAX_BYTES} bytes")
    digest = hashlib.sha256(raw).hexdigest()
    if digest != approved_sha256:
        raise SchedulerError("PLAN_NOT_APPROVED", f"plan hash {digest[:12]}… is not the approved {approved_sha256[:12]}…")
    try:
        data = json.loads(raw.decode("utf-8"), parse_constant=_reject_constant)
    except (UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise SchedulerError("PLAN_UNREADABLE", f"not valid JSON: {type(exc).__name__}") from exc
    return _build(data, digest, plan_id, revision)


def load_plan_file(path: str | Path, *, approved_sha256: str, plan_id: str | None = None,
                   revision: int | None = None) -> Plan:
    """Read-only: the file is opened for reading and never rewritten."""
    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        raise SchedulerError("PLAN_UNREADABLE", f"{path}: {type(exc).__name__}") from exc
    return load_plan(raw, approved_sha256=approved_sha256, plan_id=plan_id, revision=revision)


def _build(data: object, digest: str, want_id: str | None, want_revision: int | None) -> Plan:
    issues: list[str] = []
    if not isinstance(data, dict):
        raise SchedulerError("PLAN_INVALID", "top level must be a JSON object")
    version = data.get("schema_version")
    match = VERSION_RE.fullmatch(version) if isinstance(version, str) else None
    if not match:
        raise SchedulerError("PLAN_INVALID", "schema_version must look like 1.0.0")
    try:
        schema_version = tuple(int(match.group(index)) for index in (1, 2, 3))
    except ValueError as exc:
        raise SchedulerError("PLAN_INVALID", "schema_version components are too large") from exc
    if schema_version[0] != SUPPORTED_MAJOR:
        raise SchedulerError("PLAN_SCHEMA_UNSUPPORTED", f"schema major {schema_version[0]}; this core reads {SUPPORTED_MAJOR}.x")
    schema_1_2 = schema_version >= SCHEMA_1_2_SINCE
    pid, rev = data.get("plan_id"), data.get("revision")
    if not _text(pid):
        issues.append("plan_id must be a non-empty string")
    if not _int(rev) or rev < 1:
        issues.append("revision must be an integer >= 1")
    if issues:
        raise SchedulerError("PLAN_INVALID", issues)
    if want_id is not None and pid != want_id:
        raise SchedulerError("PLAN_MISMATCH", f"plan_id {pid!r} is not the expected {want_id!r}")
    if want_revision is not None and rev != want_revision:
        raise SchedulerError("PLAN_MISMATCH", f"revision {rev} is not the expected {want_revision}")
    raw_tasks = data.get("tasks")
    if not isinstance(raw_tasks, list) or not raw_tasks:
        raise SchedulerError("PLAN_INVALID", "tasks must be a non-empty list")
    if len(raw_tasks) > MAX_TASKS:
        raise SchedulerError("PLAN_INVALID", f"more than {MAX_TASKS} tasks")
    tasks, seen = [], set()
    for index, item in enumerate(raw_tasks):
        where = f"tasks[{index}]"
        if not isinstance(item, dict) or not _text(item.get("id")):
            issues.append(f"{where}: needs a string id")
            continue
        tid = item["id"]
        if tid in seen:
            issues.append(f"{where}: duplicate id {tid!r}")
        seen.add(tid)
        for key in ("after", "shared_resources", "expected_paths", "acceptance_criteria"):
            if key in item and not _strings(item[key]):
                issues.append(f"{tid}: {key} must be a list of non-empty strings")
        for key in ("repository", "milestone_id"):
            if key in item and not isinstance(item[key], str):
                issues.append(f"{tid}: {key} must be a string")
        verification = item.get("verification", [])
        if not isinstance(verification, list) or not all(isinstance(v, dict) for v in verification):
            issues.append(f"{tid}: verification must be a list of objects")
            verification = []
        if schema_1_2:
            if item.get("kind") not in TASK_KINDS:
                issues.append(f"{tid}: kind must be one of {', '.join(sorted(TASK_KINDS))}")
            for check_index, check in enumerate(verification):
                if check.get("category") not in VERIFICATION_CATEGORIES:
                    issues.append(f"{tid}: verification[{check_index}].category must be one of "
                                  f"{', '.join(sorted(VERIFICATION_CATEGORIES))}")
        if len(set(item.get("after", []) if _strings(item.get("after", [])) else [])) != len(item.get("after", [])):
            issues.append(f"{tid}: duplicate entries in after")
        meta_keys = OPAQUE_KEYS if schema_1_2 else LEGACY_OPAQUE_KEYS
        tasks.append(TaskSpec(
            id=tid, milestone_id=str(item.get("milestone_id", "")), after=tuple(item.get("after", ())) if _strings(item.get("after", [])) else (),
            repository=str(item.get("repository", "")).strip(),
            shared_resources=tuple(item.get("shared_resources", ())) if _strings(item.get("shared_resources", [])) else (),
            expected_paths=tuple(item.get("expected_paths", ())) if _strings(item.get("expected_paths", [])) else (),
            acceptance_criteria=tuple(item.get("acceptance_criteria", ())) if _strings(item.get("acceptance_criteria", [])) else (),
            verification=tuple(json.loads(json.dumps(v)) for v in verification),
            meta={k: item[k] for k in meta_keys if k in item}))
    for task in tasks:
        for dep in task.after:
            if dep not in seen:
                issues.append(f"{task.id}: after references unknown task {dep!r}")
            elif dep == task.id:
                issues.append(f"{task.id}: depends on itself")
    if issues:
        raise SchedulerError("PLAN_INVALID", issues)
    cycle = _cycle(tasks)
    if cycle:
        raise SchedulerError("PLAN_INVALID", "dependency cycle: " + " -> ".join(cycle))
    return Plan(plan_id=pid, revision=rev, schema_version=version, sha256=digest, tasks=tuple(tasks))


def _cycle(tasks: list[TaskSpec]) -> list[str]:
    """One cycle as a list of ids, or [] (iterative three-colour DFS: plans may be deep)."""
    after = {t.id: t.after for t in tasks}
    colour: dict[str, int] = {}
    for root, deps in after.items():
        if colour.get(root):
            continue
        stack = [(root, iter(deps))]
        path = [root]
        colour[root] = 1
        while stack:
            node, children = stack[-1]
            for child in children:
                if colour.get(child) == 1:
                    return path[path.index(child):] + [child]
                if not colour.get(child):
                    colour[child] = 1
                    path.append(child)
                    stack.append((child, iter(after[child])))
                    break
            else:
                colour[node] = 2
                path.pop()
                stack.pop()
    return []
