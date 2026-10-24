"""Dependency graph queries shared by 1.3.0 subplan validation and reports."""
from __future__ import annotations

from collections import defaultdict, deque

from . import quality

_BARRIERS = {"test", "audit"}
_NON_BARRIERS = {"implement", "docs", "design", "research"}


def _dict_list(value: object) -> list[dict]:
    return [x for x in value if isinstance(x, dict)] if isinstance(value, list) else []


def graph(plan: dict) -> tuple[dict[str, dict], dict[str, set[str]], dict[str, set[str]]]:
    tasks = {t["id"]: t for t in _dict_list(plan.get("tasks")) if isinstance(t.get("id"), str)}
    ancestors = quality.ancestors(plan)
    descendants: dict[str, set[str]] = defaultdict(set)
    for tid, parents in ancestors.items():
        for parent in parents:
            descendants[parent].add(tid)
    return tasks, ancestors, descendants


def exposure(plan: dict, task_ids: set[str] | None = None, introducing_task: str | None = None) -> int:
    """Maximum tasks downstream of a task before its first same-scope test/audit barrier."""
    tasks, _, _ = graph(plan)
    users: dict[str, list[str]] = defaultdict(list)
    for tid, task in tasks.items():
        for dependency in task.get("after", []) if isinstance(task.get("after"), list) else []:
            if isinstance(dependency, str) and dependency in tasks:
                users[dependency].append(tid)
    subset = task_ids if task_ids is not None else set(tasks)
    result = 0
    sources = {introducing_task} if introducing_task is not None else subset & tasks.keys()
    for tid in sources & tasks.keys():
        task = tasks[tid]
        if task.get("kind") in _BARRIERS:
            continue
        scope = task.get("subplan_id")
        frontier = deque(child for child in users.get(tid, ())
                         if child in subset and (scope is None or tasks[child].get("subplan_id") == scope))
        seen: set[str] = set()
        distance = 0
        while frontier:
            node = frontier.popleft()
            if node in seen:
                continue
            seen.add(node)
            current = tasks[node]
            if current.get("kind") in _BARRIERS:
                continue
            distance += 1
            frontier.extend(child for child in users.get(node, ())
                            if child in subset and (scope is None or tasks[child].get("subplan_id") == scope))
        result = max(result, distance)
    return result


def first_barrier(plan: dict, introducing_task: str, task_ids: set[str] | None = None) -> str | None:
    """Nearest same-scope test/audit descendant of a task, with task id as a stable tie breaker."""
    tasks, _, _ = graph(plan)
    source = tasks.get(introducing_task)
    if source is None:
        return None
    scope = source.get("subplan_id")
    subset = task_ids if task_ids is not None else set(tasks)
    users: dict[str, list[str]] = defaultdict(list)
    for tid, task in tasks.items():
        for dependency in task.get("after", []) if isinstance(task.get("after"), list) else []:
            if isinstance(dependency, str):
                users[dependency].append(tid)
    frontier = sorted(users.get(introducing_task, []))
    visited: set[str] = set()
    while frontier:
        barriers = [tid for tid in frontier if tid in subset and tasks[tid].get("kind") in _BARRIERS
                    and (scope is None or tasks[tid].get("subplan_id") == scope)]
        if barriers:
            return barriers[0]
        next_frontier: set[str] = set()
        for tid in frontier:
            if tid in visited or tid not in subset or (scope is not None and tasks[tid].get("subplan_id") != scope):
                continue
            visited.add(tid)
            next_frontier.update(users.get(tid, []))
        frontier = sorted(next_frontier - visited)
    return None


def longest_unbarriered_chain(plan: dict, task_ids: set[str] | None = None) -> int:
    """Longest chain of implement/docs/design/research tasks before a same-scope barrier."""
    tasks, _, _ = graph(plan)
    subset = (task_ids if task_ids is not None else set(tasks)) & tasks.keys()
    users: dict[str, list[str]] = defaultdict(list)
    indegree = {tid: 0 for tid in subset}
    for tid in subset:
        task = tasks[tid]
        for dependency in task.get("after", []) if isinstance(task.get("after"), list) else []:
            if isinstance(dependency, str) and dependency in subset and dependency != tid:
                users[dependency].append(tid)
                indegree[tid] += 1
    ready = deque(sorted(tid for tid, degree in indegree.items() if degree == 0))
    order: list[str] = []
    while ready:
        node = ready.popleft()
        order.append(node)
        for child in users.get(node, []):
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
    depth: dict[str, int] = {}
    for tid in reversed(order):
        task = tasks[tid]
        if task.get("kind") in _BARRIERS:
            depth[tid] = 0
        elif task.get("kind") in _NON_BARRIERS:
            scope = task.get("subplan_id")
            depth[tid] = max((depth.get(child, 0) if tasks[child].get("kind") in _BARRIERS else
                              1 + depth.get(child, 0)
                              for child in users.get(tid, [])
                              if scope is None or tasks[child].get("subplan_id") == scope), default=1)
        else:
            depth[tid] = 0
    return max(depth.values(), default=0)


def report(plan: dict) -> list[dict[str, object]]:
    tasks, _, _ = graph(plan)
    rows = []
    for subplan in _dict_list(plan.get("subplans")):
        members = {tid for tid, task in tasks.items() if task.get("subplan_id") == subplan.get("id")}
        rows.append({"id": subplan.get("id"), "milestone_id": subplan.get("milestone_id"),
                     "covers": subplan.get("covers", []), "tasks": sorted(members),
                     "produces": subplan.get("produces", []), "consumes": subplan.get("consumes", []),
                     "checkpoints": subplan.get("checkpoints", []), "audit_task": subplan.get("audit_task"),
                     "integration_test_task": subplan.get("integration_test_task"), "ui": subplan.get("ui"),
                     "exposure": exposure(plan, members)})
    return rows
