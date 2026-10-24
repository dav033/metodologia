"""Read models: run status, per-task view, attention list, and a neutral projection for other tools.

Derived from the plan and the state on demand, never stored (so they cannot drift from the truth)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .model import RunState
from .plan import Plan
from .states import ATTEMPT_LIVE, RunStatus
from .states import AttemptState as A
from .states import TaskState as T
from .subplans import gate_waiting, stale_subplan_members, subplan_status


def unreachable(plan: Plan, state: RunState) -> frozenset[str]:
    """Tasks that cannot start because a prerequisite (direct or indirect) is BLOCKED or CANCELLED. Derived, so
    reopening the blocked prerequisite frees them again; they are never stored as blocked themselves."""
    dead = {tid for tid, rec in state.tasks.items() if rec.state in (T.BLOCKED.value, T.CANCELLED.value)}
    children, seen, stack = plan.dependents(), set(), list(dead)
    while stack:
        for child in children[stack.pop()]:
            if child not in seen:
                seen.add(child)
                stack.append(child)
    return frozenset(d for d in seen if state.tasks[d].state in (T.PENDING.value, T.READY.value))


def run_status(plan: Plan, state: RunState) -> RunStatus:
    states = [rec.state for rec in state.tasks.values()]
    if all(s == T.COMPLETED.value for s in states):
        return RunStatus.COMPLETED     # the only road to success: every task completed with an accepted verdict
    if state.cancel_requested:
        return RunStatus.RUNNING if T.ACTIVE.value in states else RunStatus.CANCELLED
    if state.paused:
        return RunStatus.PAUSED
    movable = (T.ACTIVE.value, T.RECOVERING.value, T.READY.value)
    return RunStatus.RUNNING if any(s in movable for s in states) else RunStatus.BLOCKED


def attention(plan: Plan, state: RunState) -> list[dict[str, str]]:
    """Things waiting for a human or another module: uncertain attempts, blocked tasks."""
    out = [{"kind": "uncertain_attempt", "task_id": a.task_id, "attempt_id": a.id}
           for a in state.attempts.values() if a.state == A.UNCERTAIN.value]
    out += [{"kind": "blocked_task", "task_id": tid, "reason": rec.reason}
            for tid, rec in state.tasks.items() if rec.state == T.BLOCKED.value]
    out += [{"kind": "composition_waiting", "task_id": gate.task,
             "reason": ";".join(f"{reason}:{member}" for member, reason in
                                stale_subplan_members(plan, state, gate.task))}
            for gate in plan.composition_gates
            if gate_waiting(plan, state, gate.task) and state.tasks[gate.task].state == T.PENDING.value]
    return out


@dataclass(frozen=True)
class Snapshot:
    plan_id: str
    revision: int
    plan_sha256: str
    status: str
    paused: bool
    cancel_requested: bool
    tasks: dict[str, dict[str, Any]]
    counts: dict[str, int]
    unreachable: tuple[str, ...]
    attention: tuple[dict[str, str], ...]
    pending_outbox: int
    subplans: dict[str, str] | None = None

    def to_dict(self) -> dict[str, Any]:
        result = {"plan_id": self.plan_id, "revision": self.revision, "plan_sha256": self.plan_sha256,
                  "status": self.status, "paused": self.paused, "cancel_requested": self.cancel_requested,
                  "tasks": self.tasks, "counts": self.counts, "unreachable": list(self.unreachable),
                  "attention": list(self.attention), "pending_outbox": self.pending_outbox}
        if self.subplans:
            result["subplans"] = dict(self.subplans)
        return result


def snapshot(plan: Plan, state: RunState) -> Snapshot:
    dead = unreachable(plan, state)
    tasks: dict[str, dict[str, Any]] = {}
    for spec in plan.tasks:
        rec = state.tasks[spec.id]
        last = state.attempts[rec.attempts[-1]] if rec.attempts else None
        tasks[spec.id] = {"state": rec.state, "unreachable": spec.id in dead, "attempts": len(rec.attempts),
                          "reason": rec.reason, "attempt": last.id if last else "", "attempt_state": last.state if last else "",
                          "executor": last.executor if last else "", "verifier": last.verifier if last else "",
                          "evidence": last.evidence if last else "", "route_metadata": dict(rec.route_metadata),
                          "route_status": rec.route_status,
                          "route_reason": rec.route_reason}
    counts: dict[str, int] = {}
    for rec in state.tasks.values():
        counts[rec.state] = counts.get(rec.state, 0) + 1
    live = sum(1 for a in state.attempts.values() if A(a.state) in ATTEMPT_LIVE)
    counts["live_attempts"] = live
    return Snapshot(plan_id=state.plan_id, revision=state.revision, plan_sha256=state.plan_sha256,
                    status=run_status(plan, state).value, paused=state.paused, cancel_requested=state.cancel_requested,
                    tasks=tasks, counts=counts, unreachable=tuple(sorted(dead)), attention=tuple(attention(plan, state)),
                    pending_outbox=sum(1 for i in state.outbox if i.status == "pending"),
                    subplans=subplan_status(plan, state) or None)
