"""Atomic reservation: one transaction decides capacity, exclusivity, resources and writes the dispatch intent.

Called with an open transaction, so two concurrent callers are serialised by the repository: at most one wins a task,
and incompatible resource claims can never both be held. Nothing external is called here (write-ahead intent only).
"""
from __future__ import annotations

from dataclasses import dataclass

from .contracts import Assignment, route_metadata_valid
from .model import AttemptRec
from .resources import claims_for, first_conflict
from .states import AttemptState as A
from .states import TaskState as T
from .transitions import Ctx, add_outbox, live_attempt, set_task


@dataclass(frozen=True)
class ClaimResult:
    ok: bool
    reason: str = ""            # when refused: stable short code
    attempt_id: str = ""
    task_id: str = ""


def live_task_count(ctx: Ctx) -> int:
    return sum(1 for rec in ctx.state.tasks.values() if rec.state == T.ACTIVE.value)


def free_slots(ctx: Ctx) -> int:
    return max(0, ctx.config.max_parallel_tasks - live_task_count(ctx))


def claim(ctx: Ctx, assignment: Assignment) -> ClaimResult:
    state = ctx.state
    task_id = getattr(assignment, "task_id", None)
    if not isinstance(assignment, Assignment) or not isinstance(task_id, str) or task_id not in state.tasks:
        return ClaimResult(False, "unknown_task", task_id=str(task_id))
    if not isinstance(assignment.executor, str) or not assignment.executor.strip():
        return ClaimResult(False, "invalid_executor", task_id=task_id)
    if not route_metadata_valid(assignment.route_metadata):
        return ClaimResult(False, "invalid_route_metadata", task_id=task_id)
    refuse = _refusal(ctx, task_id)
    if refuse:
        ctx.audit("reservation_refused", task_id, reason=refuse)
        return ClaimResult(False, refuse, task_id=task_id)
    spec = ctx.plan.task(task_id)
    wanted = claims_for(spec, ctx.config)
    holder = first_conflict(wanted, state.holds)
    if holder:
        ctx.audit("reservation_refused", task_id, reason="resource_conflict", holder=holder)
        return ClaimResult(False, "resource_conflict", task_id=task_id)
    rec = state.tasks[task_id]
    rec.route_metadata = dict(assignment.route_metadata)
    rec.route_status = "assigned"
    rec.route_reason = ""
    number = len(rec.attempts) + 1
    attempt_id = f"att-{state.next('attempt'):04d}"
    token = state.next("token")
    att = AttemptRec(id=attempt_id, task_id=task_id, number=number, state=A.RESERVED.value, token=token,
                     executor=assignment.executor.strip(), key=f"{state.plan_id}:r{state.revision}:{task_id}:{attempt_id}",
                     created_at=ctx.now, updated_at=ctx.now, lease_expires_at=ctx.now + ctx.config.lease_seconds)
    state.attempts[attempt_id] = att
    rec.attempts.append(attempt_id)
    state.holds[attempt_id] = [list(c) for c in wanted]
    set_task(ctx, task_id, T.ACTIVE, attempt=attempt_id)
    ctx.audit("reserved", task_id, attempt_id, token=token, executor=att.executor, resources=[c[0] for c in wanted])
    add_outbox(ctx, "start", attempt_id, {
        "task_id": task_id, "token": token, "executor": att.executor, "key": att.key,
        "acceptance_criteria": list(spec.acceptance_criteria), "verification": [dict(v) for v in spec.verification]})
    return ClaimResult(True, attempt_id=attempt_id, task_id=task_id)


def _refusal(ctx: Ctx, task_id: str) -> str:
    state = ctx.state
    barrier = state.revision_barrier
    if barrier is not None and barrier["deadline"] > ctx.now:
        return "revision_pending"
    if state.cancel_requested:
        return "cancel_requested"
    if state.paused:
        return "paused"
    if state.tasks[task_id].state != T.READY.value:
        return "not_ready"
    if live_attempt(state, task_id) is not None:
        return "attempt_active"
    if free_slots(ctx) < 1:
        return "no_capacity"
    return ""
