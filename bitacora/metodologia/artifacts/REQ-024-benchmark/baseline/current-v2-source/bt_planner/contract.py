"""PLAN.json contract 1.x: enums, deterministic validation, canonical serialisation, read-only loading.

The planner describes and classifies work; it never chooses who runs it. Standard library only, so validation is
hand-written and `data/plan.schema.json` is the published contract document, kept in step with the constants below by
a test. Nothing here reads or writes execution state.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import evidence as ev
from . import quality

SCHEMA_VERSION = "1.1.0"  # 1.1.0 = classification evidence is mandatory (evidence.py); 1.0.0 still loads
EVIDENCE_SINCE = (1, 1, 0)
SUPPORTED_MAJOR = 1
MAX_BYTES = 2_000_000

COMPLEXITY = ("low", "medium", "high", "extreme")
SCOPE = ("isolated_fix", "small_change", "large_change", "full_feature", "full_system")
LEVELS = ("low", "medium", "high")  # risk, coupling and confidence share the three-step scale
VERIFICATION_TYPES = ("command", "manual")
TASK_ID_RE = re.compile(r"T[0-9]+(?:\.[0-9]+)?[a-z]?")  # ASCII digits only: \d would accept other scripts
MILESTONE_ID_RE = re.compile(r"M[0-9]+")
VERSION_RE = re.compile(r"[0-9]{1,6}\.[0-9]{1,6}\.[0-9]{1,6}")  # bounded: int() of 5000 digits raises
MAX_REVISION = 1_000_000
MAX_DEPTH = 24
LONG_TASK_MINUTES = 480  # warning threshold: consider splitting
MAX_MINUTES = 100_000  # hard cap: anything above is not an estimate

TOP_REQUIRED = ("schema_version", "plan_id", "revision", "spec_ref", "milestones", "tasks")
MILESTONE_KEYS = ("id", "title", "acceptance_criteria")
TASK_KEYS = ("id", "milestone_id", "title", "objective", "repository", "after", "complexity", "scope",
             "estimated_minutes", "risk", "coupling", "confidence", "estimate_rationale", "classification_evidence",
             "expected_paths", "shared_resources", "acceptance_criteria", "verification")
REQUIRED_TASK_KEYS = tuple(k for k in TASK_KEYS if k != "classification_evidence")  # evidence: required from 1.1.0
VERIFICATION_KEYS = ("type", "value", "purpose", "expected", "created_by")
# The plan classifies; scheduling and execution state belong to other systems (AC-11, AC-15).
FORBIDDEN_TASK_KEYS = frozenset({"model", "models", "agent", "agents", "account", "accounts", "profile", "provider",
                                 "worker", "workers", "worker_count", "assigned_to", "status", "state", "attempts",
                                 "sessions", "heartbeat", "cost"})


class PlanContractError(ValueError):
    """The PLAN.json cannot be used; `code` is stable for programmatic consumers, `issues` are actionable lines."""

    def __init__(self, code: str, issues: list[str]):
        self.code, self.issues = code, list(issues)
        super().__init__(f"{code}: " + "; ".join(self.issues[:5]) + (" …" if len(self.issues) > 5 else ""))


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _strings(value: object, *, allow_empty: bool) -> bool:
    return (isinstance(value, list) and (allow_empty or bool(value)) and all(_text(item) for item in value))


def _hashable_str(value: object) -> bool:
    return isinstance(value, str)


def unsafe_path(value: str) -> bool:
    path = value.replace("\\", "/")
    return "\0" in path or path.startswith("/") or re.match(r"^[A-Za-z]:", path) is not None or ".." in path.split("/")


def _enum(report: Report, where: str, task: dict, key: str, allowed: tuple[str, ...]) -> None:
    if key not in task:
        report.errors.append(f"{where}.{key}: missing (classification is never defaulted)")
    elif task[key] not in allowed:
        report.errors.append(f"{where}.{key}: {task[key]!r} is not one of {', '.join(allowed)}")


# Whole-word tokens that make a key a scheduling decision wherever they appear in it (`model_hint`, `numWorkers`,
# `max_parallel`, `assignee`): the planner describes work, it never assigns it.
SCHEDULING_TOKENS = frozenset({"model", "models", "agent", "agents", "account", "accounts", "profile", "provider",
                               "worker", "workers", "assignee", "assigned", "assign", "executor", "executors", "llm",
                               "concurrency", "concurrent", "parallel", "parallelism"})


_SCHEDULING_AFFIXES = ("model", "worker", "agent", "assignee", "assignedto", "assignto", "executor", "llm", "parallel",
                       "concurren")
_BENIGN_REMAINDERS = frozenset({"", "s", "ing", "ings", "ed", "er", "ers", "ler", "lers", "ling", "lings", "ity", "ize",
                                "ized", "ization", "cy", "t", "tly", "ce"})


def forbidden_key(key: str) -> bool:
    lowered = key.lower()
    if lowered in FORBIDDEN_TASK_KEYS:
        return True
    tokens = {w.lower() for w in re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])", key)}
    if tokens & SCHEDULING_TOKENS:
        return True
    # `modelhint`, `selectedmodel`, `assignedto`: a scheduling word glued to another with no separator
    flat = re.sub(r"[^a-z]", "", lowered)
    if flat in _SCHEDULING_AFFIXES:
        return True
    for word in _SCHEDULING_AFFIXES:
        if flat.startswith(word) and flat[len(word):] not in _BENIGN_REMAINDERS and len(flat) > len(word):
            return not flat.startswith(word + "ing")  # `modeling` is not `model`
        if flat.endswith(word) and flat != word:
            return True
    return False


def _scan_forbidden(report: Report, where: str, node: object, depth: int = 0) -> None:
    """Scheduling/execution keys are rejected at any nesting level (a plan never assigns models, accounts or workers)."""
    if depth > MAX_DEPTH:
        report.errors.append(f"{where}: nested deeper than {MAX_DEPTH} levels")
        return
    if isinstance(node, dict):
        for key, value in node.items():
            if isinstance(key, str) and forbidden_key(key):
                report.errors.append(f"{where}.{key}: not allowed in a plan (scheduling/execution state is not "
                                     "planned here)")
            _scan_forbidden(report, f"{where}.{key}", value, depth + 1)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            _scan_forbidden(report, f"{where}[{index}]", value, depth + 1)


def _check_milestones(report: Report, plan: dict) -> dict[str, int]:
    order: dict[str, int] = {}
    milestones = plan.get("milestones")
    if not isinstance(milestones, list) or not milestones:
        report.errors.append("milestones: must be a non-empty list")
        return order
    for index, item in enumerate(milestones):
        where = f"milestones[{index}]"
        if not isinstance(item, dict):
            report.errors.append(f"{where}: must be an object")
            continue
        mid = item.get("id")
        if not isinstance(mid, str) or not MILESTONE_ID_RE.fullmatch(mid):
            report.errors.append(f"{where}.id: {mid!r} must look like M1")
        elif mid in order:
            report.errors.append(f"{mid}: duplicate milestone id")
        else:
            order[mid] = index
            where = mid
        _scan_forbidden(report, where, item)
        if not _text(item.get("title")):
            report.errors.append(f"{where}.title: required")
        if not _strings(item.get("acceptance_criteria"), allow_empty=False):
            report.errors.append(f"{where}.acceptance_criteria: needs at least one non-empty criterion")
    return order


def _check_verification(report: Report, where: str, task: dict, ids: set[str]) -> None:
    items = task.get("verification")
    if not isinstance(items, list) or not items:
        report.errors.append(f"{where}.verification: needs at least one command or explicit manual check")
        return
    for index, item in enumerate(items):
        spot = f"{where}.verification[{index}]"
        if not isinstance(item, dict):
            report.errors.append(f"{spot}: must be an object")
            continue
        kind = item.get("type")
        if kind not in VERIFICATION_TYPES:
            report.errors.append(f"{spot}.type: {kind!r} is not one of {', '.join(VERIFICATION_TYPES)}")
        if not _text(item.get("value")):
            report.errors.append(f"{spot}.value: required")
        if not _text(item.get("purpose")):
            report.errors.append(f"{spot}.purpose: required")
        if kind == "manual" and not _text(item.get("expected")):
            report.errors.append(f"{spot}.expected: a manual check must state the expected result")
        created = item.get("created_by")
        if created is not None and not (isinstance(created, str) and created in ids):
            report.errors.append(f"{spot}.created_by: {created!r} is not a task of this plan")


def schema_tuple(plan: dict) -> tuple[int, int, int]:
    version = plan.get("schema_version")
    if isinstance(version, str) and VERSION_RE.fullmatch(version):
        major, minor, patch = (int(x) for x in version.split("."))
        return major, minor, patch
    return (0, 0, 0)


def _check_task(report: Report, task: object, index: int, milestones: dict[str, int], ids: set[str],
                strict: bool = False, file_exists: ev.FileExists | None = None,
                ref_exists: ev.RefExists | None = None) -> str | None:
    where = f"tasks[{index}]"
    if not isinstance(task, dict):
        report.errors.append(f"{where}: must be an object")
        return None
    tid = task.get("id")
    if isinstance(tid, str) and TASK_ID_RE.fullmatch(tid):
        where = tid
    else:
        report.errors.append(f"{where}.id: {tid!r} must look like T1")
        tid = None
    _scan_forbidden(report, where, task)
    for key in ("title", "objective", "repository", "estimate_rationale"):
        if not _text(task.get(key)):
            report.errors.append(f"{where}.{key}: required, non-empty text")
    mid = task.get("milestone_id")
    if not (isinstance(mid, str) and mid in milestones):
        report.errors.append(f"{where}.milestone_id: {mid!r} is not a milestone of this plan")
    _enum(report, where, task, "complexity", COMPLEXITY)
    _enum(report, where, task, "scope", SCOPE)
    for key in ("risk", "coupling", "confidence"):
        _enum(report, where, task, key, LEVELS)
    minutes = task.get("estimated_minutes")
    if not _int(minutes) or not 0 < minutes <= MAX_MINUTES:
        shown = minutes if _int(minutes) and abs(minutes) <= MAX_MINUTES * 10 else type(minutes).__name__
        report.errors.append(f"{where}.estimated_minutes: must be an integer between 1 and {MAX_MINUTES} (no number, "
                             f"no publication: decompose or add a research task), got {shown!r}")
    elif minutes > LONG_TASK_MINUTES:
        report.warnings.append(f"{where}.estimated_minutes: {minutes} exceeds {LONG_TASK_MINUTES}; consider splitting")
    if not _strings(task.get("after"), allow_empty=True):
        report.errors.append(f"{where}.after: must be a list of task ids ([] when none)")
    if not _strings(task.get("acceptance_criteria"), allow_empty=False):
        report.errors.append(f"{where}.acceptance_criteria: needs at least one observable, non-empty criterion")
    paths = task.get("expected_paths")
    if not _strings(paths, allow_empty=True):
        report.errors.append(f"{where}.expected_paths: must be a list of paths/patterns")
    elif any(unsafe_path(p) for p in paths):
        report.errors.append(f"{where}.expected_paths: absolute or '..' paths are not allowed")
    resources = task.get("shared_resources")
    if not _strings(resources, allow_empty=True):
        report.errors.append(f"{where}.shared_resources: must be a list ([] when none known)")
    elif task.get("coupling") in ("medium", "high") and not resources:
        report.warnings.append(f"{where}.shared_resources: coupling is {task['coupling']} but no shared resource is "
                               "named; name the contract/resource or lower the coupling")
    if task.get("scope") == "full_system":
        exc = task.get("scope_exception")
        if not (isinstance(exc, dict) and _text(exc.get("reason"))):
            report.errors.append(f"{where}.scope: full_system must be decomposed, or carry "
                                 "scope_exception {reason} for review")
        else:
            report.warnings.append(f"{where}.scope: full_system accepted only through scope_exception "
                                   f"({exc['reason'].strip()[:80]!r}); the owner must review it at approval")
    elif "scope_exception" in task:
        report.errors.append(f"{where}.scope_exception: only valid with scope=full_system")
    _check_verification(report, where, task, ids)
    found = ev.check_task(where, task, strict=strict, task_ids=ids, own_id=tid, file_exists=file_exists,
                          ref_exists=ref_exists)
    report.errors += found[0]
    report.warnings += found[1]
    found = ev.check_text_quality(where, task, strict=strict)
    report.errors += found[0]
    report.warnings += found[1]
    if task.get("risk") == "high" and isinstance(task.get("verification"), list) and not any(
            isinstance(v, dict) and v.get("type") == "command" for v in task["verification"]):
        report.warnings.append(f"{where}.verification: risk is high but nothing is machine-checked; add a command "
                               "(or a task that creates one, with created_by)")
    return tid


def _check_graph(report: Report, tasks: list[dict], milestones: dict[str, int]) -> None:
    by_id = {t["id"]: t for t in tasks if isinstance(t.get("id"), str) and TASK_ID_RE.fullmatch(t["id"])}
    edges: dict[str, list[str]] = {}
    for tid, task in by_id.items():
        deps = task["after"] if _strings(task.get("after"), allow_empty=True) else []
        if len(set(deps)) != len(deps):
            report.errors.append(f"{tid}.after: duplicate prerequisite")
        edges[tid] = []
        for dep in dict.fromkeys(d for d in deps if isinstance(d, str)):
            if dep == tid:
                report.errors.append(f"{tid}.after: a task cannot depend on itself")
            elif dep not in by_id:
                report.errors.append(f"{tid}.after: {dep!r} does not exist")
            else:
                edges[tid].append(dep)
                mine = milestones.get(task["milestone_id"]) if _hashable_str(task.get("milestone_id")) else None
                other = by_id[dep].get("milestone_id")
                theirs = milestones.get(other) if _hashable_str(other) else None
                if mine is not None and theirs is not None and theirs > mine:
                    report.errors.append(f"{tid}.after: {dep} belongs to a later milestone "
                                         f"({by_id[dep]['milestone_id']})")
    indegree = {tid: len(deps) for tid, deps in edges.items()}
    ready = [tid for tid, n in indegree.items() if n == 0]
    seen = 0
    while ready:
        node = ready.pop()
        seen += 1
        for other, deps in edges.items():
            if node in deps:
                indegree[other] -= 1
                if indegree[other] == 0:
                    ready.append(other)
    if seen < len(edges):
        cyclic = sorted(tid for tid, n in indegree.items() if n > 0)
        report.errors.append(f"tasks: dependency cycle among {', '.join(cyclic)}")


def validate(plan: object, file_exists: ev.FileExists | None = None, ref_exists: ev.RefExists | None = None) -> Report:
    """Deterministic validation of a parsed PLAN.json; every error names the task/field that causes it.
    `file_exists(repository, path)` lets a caller that knows the repositories verify `file:` evidence and
    `ref_exists(kind, value, repository)` does the same for `command:` and `precedent:` references."""
    report = Report()
    if not isinstance(plan, dict):
        report.errors.append("plan: top level must be an object")
        return report
    for key in TOP_REQUIRED:
        if key not in plan:
            report.errors.append(f"plan.{key}: missing")
    version = plan.get("schema_version")
    if "schema_version" in plan and not (isinstance(version, str) and VERSION_RE.fullmatch(version)
                                         and int(version.split(".")[0]) == SUPPORTED_MAJOR):
        report.errors.append(f"plan.schema_version: {version!r} unsupported (this reader handles {SUPPORTED_MAJOR}.x.y)")
    if "plan_id" in plan and not _text(plan["plan_id"]):
        report.errors.append("plan.plan_id: must be non-empty text")
    if "spec_ref" in plan and (not _text(plan["spec_ref"]) or unsafe_path(plan["spec_ref"])):
        report.errors.append("plan.spec_ref: must be a relative path inside the requirement folder")
    if "revision" in plan and (not _int(plan["revision"]) or not 1 <= plan["revision"] <= MAX_REVISION):
        shown = plan["revision"] if _int(plan["revision"]) and abs(plan["revision"]) <= MAX_REVISION * 10 \
            else type(plan["revision"]).__name__  # never str() a huge int: it raises past 4300 digits
        report.errors.append(f"plan.revision: must be an integer between 1 and {MAX_REVISION}, got {shown!r}")
    _scan_forbidden(report, "plan", {k: v for k, v in plan.items() if k not in ("tasks", "milestones")})
    try:
        json.dumps(plan, allow_nan=False, ensure_ascii=False).encode("utf-8")
    except UnicodeEncodeError:
        report.errors.append("plan: contains characters that are not valid Unicode (lone surrogates) and cannot be "
                             "written as UTF-8")
        return report
    except (ValueError, TypeError, RecursionError) as exc:
        report.errors.append(f"plan: not serialisable as standard JSON ({type(exc).__name__}: NaN/Infinity, "
                             "oversized numbers, non-JSON values or excessive nesting)")
        return report
    milestones = _check_milestones(report, plan)
    tasks = plan.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        report.errors.append("tasks: must be a non-empty list")
        return report
    ids = [t.get("id") for t in tasks if isinstance(t, dict) and _hashable_str(t.get("id"))]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        where_dup = ", ".join(f"tasks[{n}]" for n, x in enumerate(tasks) if isinstance(x, dict) and x.get("id") == dup)
        report.errors.append(f"{dup}: duplicate task id ({where_dup})")
    id_set = set(ids)
    strict = schema_tuple(plan) >= EVIDENCE_SINCE
    for index, task in enumerate(tasks):
        _check_task(report, task, index, milestones, id_set, strict, file_exists, ref_exists)
    _check_graph(report, [t for t in tasks if isinstance(t, dict)], milestones)
    if not report.errors or all("cycle" not in e for e in report.errors):
        (report.errors if strict else report.warnings).extend(quality.conflicts(plan))
        report.warnings.extend(quality.shared_unordered(plan))
        report.warnings.extend(quality.unconsumed_results(plan))
        report.warnings.extend(quality.redundant_edges(plan))
    reused: dict[str, set[str]] = {}
    for task in tasks:
        entries = task.get("classification_evidence") if isinstance(task, dict) else None
        for entry in entries.values() if isinstance(entries, dict) else ():
            if isinstance(entry, dict) and isinstance(entry.get("justification"), str):
                reused.setdefault(ev.normalise(entry["justification"]), set()).add(str(task.get("id")))
    for text, owners in reused.items():
        if len(owners) >= 3 and text:
            report.warnings.append(f"classification_evidence: the same justification is reused by {len(owners)} tasks "
                                   f"({', '.join(sorted(owners)[:5])}); classifications must be argued per task")
    used = {t.get("milestone_id") for t in tasks if isinstance(t, dict) and _hashable_str(t.get("milestone_id"))}
    for mid in milestones:
        if mid not in used:
            report.errors.append(f"{mid}: orphan milestone (no task belongs to it)")
    return report


LEGACY_TASK_KEYS = tuple(k for k in TASK_KEYS if k != "classification_evidence")


def _deep_sorted(value: object) -> object:
    """Nested objects get sorted keys, so any two spellings of one plan hash alike (schema 1.1.0 and later)."""
    if isinstance(value, dict):
        return {key: _deep_sorted(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, list):
        return [_deep_sorted(item) for item in value]
    return value


def _ordered(obj: object, keys: tuple[str, ...], deep: bool = True) -> object:
    """Named keys first in the given order, the rest sorted. `deep` also sorts nested values; schema 1.0.0 documents
    keep the exact serialisation they were frozen with (nested keys untouched), so their hashes never move."""
    if not isinstance(obj, dict):
        return obj  # malformed input is the validator's business; serialising must never raise on it
    fix = _deep_sorted if deep else (lambda value: value)
    head = {key: fix(obj[key]) for key in keys if key in obj}
    return {**head, **{key: fix(obj[key]) for key in sorted(obj, key=str) if key not in head}}


def canonicalize(plan: dict) -> dict:
    modern = schema_tuple(plan) >= EVIDENCE_SINCE
    task_keys = TASK_KEYS if modern else LEGACY_TASK_KEYS
    top = _ordered(plan, TOP_REQUIRED[:4], modern)
    milestones = plan.get("milestones", [])
    top["milestones"] = [_ordered(m, MILESTONE_KEYS, modern) for m in milestones] if isinstance(milestones, list) \
        else milestones
    tasks = []
    for task in plan.get("tasks", []) if isinstance(plan.get("tasks", []), list) else []:
        task = _ordered(task, task_keys, modern)
        if isinstance(task, dict):
            if isinstance(task.get("verification"), list):
                task["verification"] = [_ordered(v, VERIFICATION_KEYS, modern) for v in task["verification"]]
            elif "verification" not in task:
                task["verification"] = []  # as the original serialiser always wrote it (skeletons, invalid drafts)
            if modern and isinstance(task.get("classification_evidence"), dict):
                task["classification_evidence"] = _ordered(task["classification_evidence"], ev.DIMENSIONS)
        tasks.append(task)
    top["tasks"] = tasks if isinstance(plan.get("tasks", []), list) else plan.get("tasks")
    rest = {key: (_deep_sorted(plan[key]) if modern else plan[key]) for key in sorted(plan, key=str) if key not in top}
    return {**top, **rest}


def dumps(plan: dict) -> str:
    """Deterministic text: fixed key order, task order as planned, UTF-8, trailing newline."""
    try:
        return json.dumps(canonicalize(plan), indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    except (ValueError, TypeError, RecursionError, LookupError, AttributeError) as exc:
        raise PlanContractError("PLAN_NOT_SERIALISABLE", [f"{type(exc).__name__}: plan cannot be written as JSON"]) from exc


def _reject_constant(name: str):
    raise ValueError(f"non-standard JSON constant {name}")


def _no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    seen: dict[str, object] = {}
    for key, value in pairs:
        if key in seen:
            raise ValueError(f"duplicate key {key!r} (the later value would silently win)")
        seen[key] = value
    return seen


def loads(text: str) -> object:
    """json.loads that refuses NaN/Infinity and duplicate keys and turns runaway nesting into ValueError."""
    try:
        return json.loads(text, parse_constant=_reject_constant, object_pairs_hook=_no_duplicate_keys)
    except RecursionError as exc:
        raise ValueError("nesting too deep") from exc


def load(path: Path) -> dict:
    """Read and validate a PLAN.json for a consumer (read-only; never invokes agents). Raises PlanContractError."""
    try:
        if path.stat().st_size > MAX_BYTES:
            raise PlanContractError("PLAN_TOO_LARGE", [f"{path.name} exceeds {MAX_BYTES} bytes"])
        plan = loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PlanContractError("PLAN_NOT_FOUND", [str(path)]) from exc
    except (OSError, UnicodeError) as exc:
        raise PlanContractError("PLAN_UNREADABLE", [f"{type(exc).__name__}: {path}"]) from exc
    except json.JSONDecodeError as exc:
        raise PlanContractError("PLAN_NOT_JSON", [f"{path.name}: line {exc.lineno} column {exc.colno}"]) from exc
    except ValueError as exc:
        raise PlanContractError("PLAN_NOT_JSON", [f"{path.name}: {exc}"]) from exc
    report = validate(plan)
    if not report.ok:
        raise PlanContractError("PLAN_INVALID", report.errors)
    return plan
