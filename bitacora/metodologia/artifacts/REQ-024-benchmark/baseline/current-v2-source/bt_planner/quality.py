"""Plan-level coherence beyond the schema: what the dependency graph and the classifications say together.

`conflicts` and `redundant_edges` are linted by `contract.validate`; `analyze` is a read-only summary (critical path,
widest antichain level, distributions, evidence coverage) that a planner reads to judge whether a plan is sound and that
a scheduler may ignore. Pure functions over a parsed PLAN.json; they assume nothing about execution.
"""
from __future__ import annotations

import fnmatch
import re

_WILD = re.compile(r"[*?\[]")


def _static(path: str) -> str:
    flat = path.replace("\\", "/").strip().strip("/")
    parts = flat.split("/")
    out = []
    for part in parts:
        if _WILD.search(part):
            break
        out.append(part)
    return "/".join(out)


def paths_overlap(a: str, b: str) -> bool:
    """Two path patterns can name the same file: equal static prefixes, one directory containing the other, an empty
    prefix (`**`) or a glob that matches the other."""
    sa, sb = _static(a), _static(b)
    if not sa or not sb or sa == sb or sa.startswith(sb + "/") or sb.startswith(sa + "/"):
        return True
    return fnmatch.fnmatchcase(a, b) or fnmatch.fnmatchcase(b, a)


def _tasks(plan: dict) -> dict[str, dict]:
    return {t["id"]: t for t in plan.get("tasks", []) if isinstance(t, dict) and isinstance(t.get("id"), str)}


def _after(task: dict) -> list[str]:
    after = task.get("after")
    return [a for a in after if isinstance(a, str)] if isinstance(after, list) else []


MAX_LINTED_TASKS = 1500  # pairwise checks are quadratic; a plan this size is reported, not silently slow


def _order(plan: dict) -> tuple[list[str], dict[str, dict]]:
    """Task ids in dependency order (prerequisites first). Ids caught in a cycle are left out: the validator reports
    cycles itself. Iterative, so a long chain cannot exhaust the recursion limit."""
    tasks = _tasks(plan)
    pending = {tid: {d for d in _after(task) if d in tasks and d != tid} for tid, task in tasks.items()}
    users: dict[str, list[str]] = {}
    for tid, deps in pending.items():
        for dep in deps:
            users.setdefault(dep, []).append(tid)
    ready = sorted(tid for tid, deps in pending.items() if not deps)
    order: list[str] = []
    while ready:
        node = ready.pop(0)
        order.append(node)
        for user in users.get(node, ()):
            pending[user].discard(node)
            if not pending[user] and user not in order and user not in ready:
                ready.append(user)
    return order, tasks


def ancestors(plan: dict) -> dict[str, set[str]]:
    """task id -> every task that must finish before it (transitive)."""
    order, _, bit, mask = _ordered_masks(plan)
    return {tid: {other for other in order if mask[tid] & bit[other]} for tid in order}


def _ordered_masks(plan: dict) -> tuple[list[str], dict[str, dict], dict[str, int], dict[str, int]]:
    order, tasks = _order(plan)
    bit = {tid: 1 << i for i, tid in enumerate(order)}
    mask: dict[str, int] = {}
    for tid in order:
        value = 0
        for dep in _after(tasks[tid]):
            if dep in mask:
                value |= mask[dep] | bit[dep]
        mask[tid] = value
    return order, tasks, bit, mask


def conflicts(plan: dict) -> list[str]:
    """Tasks that nothing orders yet share a path or a resource while one of them claims `coupling: low`: a
    scheduler reading `low` would run them side by side and they would collide."""
    order, tasks, bit, mask = _ordered_masks(plan)
    if len(order) > MAX_LINTED_TASKS:
        return []
    out = []
    for i, a in enumerate(order):
        ta = tasks[a]
        for b in order[i + 1:]:
            if mask[b] & bit[a] or mask[a] & bit[b]:
                continue
            tb = tasks[b]
            if ta.get("coupling") != "low" and tb.get("coupling") != "low":
                continue
            if str(ta.get("repository")) != str(tb.get("repository")):
                continue
            paths = [(p, q) for p in _strs(ta.get("expected_paths")) for q in _strs(tb.get("expected_paths"))
                     if paths_overlap(p, q)]
            shared = sorted(set(_strs(ta.get("shared_resources"))) & set(_strs(tb.get("shared_resources"))))
            if paths or shared:
                what = f"path {paths[0][0]!r}~{paths[0][1]!r}" if paths else f"resource {shared[0]!r}"
                first, second = sorted((a, b))
                out.append(f"{first} and {second}: nothing orders them yet both touch {what}, and one declares "
                           "coupling low; add `after` between them or raise the coupling")
    return sorted(out)


def shared_unordered(plan: dict) -> list[str]:
    """Same overlap as `conflicts`, but where nobody claims `coupling: low`: the plan admits the interaction yet leaves
    the two tasks unordered, so whoever schedules them has to serialise or coordinate. A warning, never a decision."""
    order, tasks, bit, mask = _ordered_masks(plan)
    if len(order) > MAX_LINTED_TASKS:
        return []
    out = []
    for i, a in enumerate(order):
        ta = tasks[a]
        for b in order[i + 1:]:
            if mask[b] & bit[a] or mask[a] & bit[b]:
                continue
            tb = tasks[b]
            if ta.get("coupling") == "low" or tb.get("coupling") == "low":
                continue  # reported as an error by `conflicts`
            if str(ta.get("repository")) != str(tb.get("repository")):
                continue
            shared = sorted(set(_strs(ta.get("shared_resources"))) & set(_strs(tb.get("shared_resources"))))
            paths = [p for p in _strs(ta.get("expected_paths")) for q in _strs(tb.get("expected_paths"))
                     if paths_overlap(p, q)]
            if shared or paths:
                what = f"resource {shared[0]!r}" if shared else f"path {paths[0]!r}"
                first, second = sorted((a, b))
                out.append(f"{first} and {second}: unordered but both touch {what}; order them with `after` or the "
                           "scheduler must serialise them")
    return sorted(out)


def unconsumed_results(plan: dict) -> list[str]:
    """A task that nothing waits for, outside the plan's last milestone: its result can be lost or arrive after the
    final verification already ran (an `after`-driven scheduler may overlap them). Warning only."""
    tasks = _tasks(plan)
    raw = plan.get("milestones")
    milestones = [m.get("id") for m in raw if isinstance(m, dict)] if isinstance(raw, list) else []
    if len(tasks) < 2 or not milestones:
        return []
    depended = {d for t in tasks.values() for d in _after(t)}
    last = milestones[-1]
    out = []
    for tid, task in tasks.items():
        if tid in depended or task.get("milestone_id") == last:
            continue
        out.append(f"{tid}: no task waits for it (nothing lists it in `after`) and it is not in the last milestone; "
                   "a final verification could run before its result exists")
    return sorted(out)


def redundant_edges(plan: dict) -> list[str]:
    """`after` entries already implied by another prerequisite (T3 after T1, T2 while T2 after T1)."""
    order, tasks, bit, mask = _ordered_masks(plan)
    out = []
    for tid in order:
        deps = [d for d in _after(tasks[tid]) if d in bit]
        for dep in deps:
            if any(mask.get(other, 0) & bit[dep] for other in deps if other != dep):
                out.append(f"{tid}.after: {dep} is already implied by another prerequisite; drop it to keep the "
                           "graph honest")
    return out


def _strs(value: object) -> list[str]:
    return [v for v in value if isinstance(v, str)] if isinstance(value, list) else []


def _minutes(task: dict) -> int:
    m = task.get("estimated_minutes")
    return m if isinstance(m, int) and not isinstance(m, bool) and m > 0 else 0


def analyze(plan: dict) -> dict:
    """Read-only quality summary of a (valid) plan."""
    order, tasks, _, _ = _ordered_masks(plan)
    finish: dict[str, int] = {}
    parent: dict[str, str | None] = {}
    level: dict[str, int] = {}
    for tid in order:
        best, via, depth = 0, None, 0
        for dep in _after(tasks[tid]):
            if dep in finish:
                if finish[dep] > best:
                    best, via = finish[dep], dep
                depth = max(depth, level[dep])
        finish[tid] = best + _minutes(tasks[tid])
        parent[tid] = via
        level[tid] = depth + 1
    end = max(order, key=lambda t: (finish[t], t)) if order else None
    path: list[str] = []
    node = end
    while node:
        path.append(node)
        node = parent.get(node)
    width: dict[int, int] = {}
    for value in level.values():
        width[value] = width.get(value, 0) + 1

    def dist(key: str) -> dict[str, int]:
        out: dict[str, int] = {}
        for task in tasks.values():
            out[str(task.get(key))] = out.get(str(task.get(key)), 0) + 1
        return dict(sorted(out.items()))

    def has_command(task: dict) -> bool:
        return any(isinstance(v, dict) and v.get("type") == "command" for v in task.get("verification") or [])

    return {
        "tasks": len(tasks), "milestones": len(plan["milestones"]) if isinstance(plan.get("milestones"), list) else 0,
        "total_minutes": sum(_minutes(t) for t in tasks.values()),
        "critical_path": {"tasks": path[::-1], "minutes": finish.get(end, 0) if end else 0},
        "widest_level": max(width.values(), default=0),
        "distribution": {k: dist(k) for k in ("complexity", "scope", "risk", "coupling", "confidence")},
        "without_command_verification": sorted(t["id"] for t in tasks.values() if not has_command(t)),
        "low_confidence": sorted(t["id"] for t in tasks.values() if t.get("confidence") == "low"),
        "with_evidence": sorted(t["id"] for t in tasks.values() if isinstance(t.get("classification_evidence"), dict)),
        "unordered_conflicts": conflicts(plan),
        "unordered_shared": shared_unordered(plan),
        "unconsumed_results": unconsumed_results(plan),
        "redundant_edges": redundant_edges(plan),
    }
