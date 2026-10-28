"""Which tasks of a frozen plan may start now (pure; replayed identically by a recovered run workflow).

The dependency graph and the resource claims are the legacy core's own rules (`bt_scheduler_core.plan` and
`bt_scheduler_core.resources`): this module only applies them to the durable runtime's view of the run, where a task
is `done`, `running` or not started. A blocked task blocks only its dependents; independent work keeps going.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from bt_scheduler_core.config import Config
from bt_scheduler_core.plan import Plan, TaskSpec
from bt_scheduler_core.resources import claims_for, conflict

DONE = frozenset({"completed", "inherited"})
STOPPED = frozenset({"blocked", "cancelled"})


@dataclass(frozen=True)
class Frontier:
    ready: tuple[str, ...]           # may start now, in plan order
    waiting: tuple[str, ...]         # dependencies not done yet
    held_by_resources: tuple[str, ...]  # dependencies done, but a running task holds a conflicting claim
    unreachable: tuple[str, ...]     # a dependency is blocked or cancelled: needs recovery or the owner
    finished: bool                   # every task is done (nothing left to run)


def compute(plan: Plan, states: Mapping[str, str], *, max_parallel: int, config: Config | None = None) -> Frontier:
    """`states` maps task id -> one of completed|inherited|blocked|cancelled|running (absent = not started)."""
    config = config or Config(max_parallel_tasks=max(1, max_parallel), unknown_surface="allow")
    by_id = {t.id: t for t in plan.tasks}
    running = [by_id[t] for t, s in states.items() if s == "running" and t in by_id]
    held = [claims_for(t, config) for t in running]
    unreachable = _unreachable(plan, states)
    ready: list[str] = []
    waiting: list[str] = []
    resource_held: list[str] = []
    slots = max(0, max_parallel - len(running))
    for task in plan.tasks:
        state = states.get(task.id)
        if state is not None or task.id in unreachable:
            continue
        if not all(states.get(dep) in DONE for dep in task.after):
            waiting.append(task.id)
            continue
        wanted = claims_for(task, config)
        if any(conflict(wanted, other) for other in held):
            resource_held.append(task.id)
            continue
        if slots <= 0:
            waiting.append(task.id)
            continue
        ready.append(task.id)
        held.append(wanted)             # two ready tasks that conflict with each other never start together
        slots -= 1
    finished = all(states.get(t.id) in DONE for t in plan.tasks)
    return Frontier(tuple(ready), tuple(waiting), tuple(resource_held), tuple(sorted(unreachable)), finished)


def _unreachable(plan: Plan, states: Mapping[str, str]) -> set[str]:
    stopped = {t for t, s in states.items() if s in STOPPED}
    out: set[str] = set()
    changed = True
    while changed:
        changed = False
        for task in plan.tasks:
            if task.id in out or states.get(task.id) is not None:
                continue
            if any(dep in stopped or dep in out for dep in task.after):
                out.add(task.id)
                changed = True
    return out


def settled(plan: Plan, states: Mapping[str, str]) -> bool:
    """Nothing is running and nothing more can start: the run waits for recovery or the owner, or it is finished."""
    if any(s == "running" for s in states.values()):
        return False
    front = compute(plan, states, max_parallel=1)
    return not front.ready and not front.held_by_resources and not front.waiting


def task(plan: Plan, task_id: str) -> TaskSpec:
    for item in plan.tasks:
        if item.id == task_id:
            return item
    raise KeyError(task_id)


def ids(plan: Plan) -> Iterable[str]:
    return (t.id for t in plan.tasks)
