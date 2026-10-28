"""Plan 1.3.0 subplans and composition gates as the durable control plane reads them (REQ-030 item 1). Pure.

What a subplan IS comes from the legacy core unchanged: `Plan.subplans` / `Plan.composition_gates` are parsed and
validated by `bt_scheduler_core.subplans.parse_plan_extensions`, and a subplan's line holds the tasks
`bt_integration_line.scoped_task_ids` names (its members plus their frozen-plan ancestors), exactly as the legacy
`SubplanLineRouter` scopes `refs/m3/line/<run>/<role>/<SP>`. What a gate needs is the legacy rule too: every member
subplan is complete (its members, its UI design and visual review tasks, its audit) before the gate task may start, on
the composition candidate of those subplans; work after a gate never starts before the gate passed.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from ..legacy import Plan, scoped_task_ids

DONE = frozenset({"completed", "inherited"})


def enabled(plan: Plan) -> bool:
    return getattr(plan, "schema_version", "") == "1.3.0" and bool(getattr(plan, "subplans", ()))


def members(plan: Plan, subplan_id: str) -> frozenset[str]:
    """The tasks that must be accepted for the subplan to be complete (legacy `_accepted_identity`)."""
    spec = next(item for item in plan.subplans if item.id == subplan_id)
    found = {task.id for task in plan.tasks if task.meta.get("subplan_id") == subplan_id}
    found.add(spec.audit_task)
    if spec.ui is not None:
        found.update((spec.ui.design_task, spec.ui.visual_review_task))
    return frozenset(found)


def scopes(plan: Plan) -> dict[str, frozenset[str]]:
    """Subplan id -> the tasks its integration line holds."""
    return {item.id: scoped_task_ids(plan, item.id) for item in plan.subplans} if enabled(plan) else {}


def lines_of(plan: Plan, task_id: str) -> tuple[str, ...]:
    """The subplan lines a task's accepted work belongs to, in plan order."""
    return tuple(sp for sp, scope in scopes(plan).items() if task_id in scope)


def gate_of(plan: Plan, task_id: str):
    return next((gate for gate in getattr(plan, "composition_gates", ()) if gate.task == task_id), None)


def home(plan: Plan, task_id: str) -> str:
    """Where a task starts: `gate:<CG>` (the composition candidate), `<SP>` (its subplan line) or "" (the run line)."""
    if not enabled(plan):
        return ""
    gate = gate_of(plan, task_id)
    if gate is not None:
        return f"gate:{gate.id}"
    return str(plan.task(task_id).meta.get("subplan_id") or "")


def complete(plan: Plan, states: Mapping[str, str], subplan_id: str) -> bool:
    return all(states.get(task) in DONE for task in members(plan, subplan_id))


@dataclass(frozen=True)
class Gates:
    """The run's gate facts: `composed` gate id -> candidate id (built, not rejected); `rejected` gate id -> reason."""
    composed: Mapping[str, str] = field(default_factory=dict)
    rejected: Mapping[str, str] = field(default_factory=dict)


def gate_ready(plan: Plan, states: Mapping[str, str], gate) -> bool:
    return all(complete(plan, states, member) for member in gate.subplans)


def to_compose(plan: Plan, states: Mapping[str, str], gates: Gates) -> tuple:
    """Gates whose member subplans are complete and whose candidate is not built yet (in plan order)."""
    if not enabled(plan):
        return ()
    return tuple(gate for gate in plan.composition_gates
                 if gate.id not in gates.composed and gate.id not in gates.rejected
                 and states.get(gate.task) is None and gate_ready(plan, states, gate))


def held(plan: Plan, states: Mapping[str, str], gates: Gates, task_id: str) -> str:
    """Why a task whose dependencies are done may still not start because of a gate ('' = it may):
    a gate task waits for complete members and a built candidate; anything after a gate waits for the gate to pass."""
    if not enabled(plan):
        return ""
    gate = gate_of(plan, task_id)
    if gate is not None:
        if gate.id in gates.rejected:
            return f"{gate.id}: candidate rejected ({gates.rejected[gate.id]})"
        if not gate_ready(plan, states, gate):
            return f"{gate.id}: member subplans are not complete"
        if gate.id not in gates.composed:
            return f"{gate.id}: composition candidate not built yet"
    ancestors = plan.ancestors(task_id)
    for other in plan.composition_gates:
        if other.task in ancestors and states.get(other.task) not in DONE:
            return f"{other.id}: the gate has not passed"
    return ""


def evidence(plan: Plan, subplan_id: str, results: Mapping[str, Mapping]) -> list[dict[str, str]]:
    """The accepted member verdicts a subplan version is bound to (bt_composition version evidence)."""
    out = []
    for task_id in sorted(members(plan, subplan_id), key=[t.id for t in plan.tasks].index):
        result = results.get(task_id) or {}
        ref = str(result.get("verdict_ref") or "")
        if not ref:
            provenance = str(result.get("provenance") or "")
            ref = next((word for word in provenance.split() if word.startswith("m6://")), "")
        out.append({"task_id": task_id, "kind": str(plan.task(task_id).meta.get("kind") or "task"),
                    "verdict_id": ref or "unrecorded", "snapshot": str(result.get("snapshot_sha") or "")})
    return out
