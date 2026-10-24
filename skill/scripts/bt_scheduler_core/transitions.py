"""Guarded state changes: every task/attempt transition, hold release and outbox write goes through here."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .config import Config
from .errors import SchedulerError
from .model import OUTBOX_KEEP, OUTBOX_LIMIT, AttemptRec, OutboxItem, RunState
from .plan import Plan
from .repository import Transaction
from .states import ATTEMPT_LIVE, ATTEMPT_TRANSITIONS, RESTORABLE, TASK_TRANSITIONS
from .states import AttemptState as A
from .states import TaskState as T
from .subplans import gate_waiting, prune_composition_holds, stale_subplan_members


@dataclass
class Ctx:
    """Everything a state change needs: the plan, limits, the open transaction and 'now'."""
    plan: Plan
    config: Config
    tx: Transaction
    now: float

    @property
    def state(self) -> RunState:
        assert self.tx.state is not None
        return self.tx.state

    def audit(self, kind: str, /, task_id: str = "", attempt_id: str = "", **detail: Any) -> None:
        self.tx.audit(kind, at=self.now, task_id=task_id, attempt_id=attempt_id, **detail)


def set_task(ctx: Ctx, task_id: str, new: T, *, restore: bool = False, **detail: Any) -> None:
    """`restore` is the one way back to COMPLETED without a verdict (`operations.withdraw_rework`): a task whose accepted
    result was sent back for rework and has not been redone returns to it. Nothing else may pass it."""
    rec = ctx.state.tasks[task_id]
    old = T(rec.state)
    if not (restore and new == T.COMPLETED and old in RESTORABLE) and new not in TASK_TRANSITIONS[old]:
        raise SchedulerError("ILLEGAL_TRANSITION", f"task {task_id}: {old.value} -> {new.value}")
    rec.state = new.value
    ctx.audit("task_transition", task_id, **{"from": old.value, "to": new.value}, **detail)


def set_attempt(ctx: Ctx, attempt_id: str, new: A, **detail: Any) -> AttemptRec:
    att = ctx.state.attempts[attempt_id]
    old = A(att.state)
    if new not in ATTEMPT_TRANSITIONS[old]:
        raise SchedulerError("ILLEGAL_TRANSITION", f"attempt {attempt_id}: {old.value} -> {new.value}")
    att.state, att.updated_at = new.value, ctx.now
    ctx.audit("attempt_transition", att.task_id, attempt_id, **{"from": old.value, "to": new.value}, **detail)
    return att


_ORDER = (A.RESERVED, A.DISPATCHED, A.RUNNING, A.VERIFYING)


def advance(ctx: Ctx, attempt_id: str, target: A, **detail: Any) -> None:
    """Move a live attempt forward to `target`, recording the implicit steps an executor skipped (a lost 'started'
    event must not wedge the attempt)."""
    att = ctx.state.attempts[attempt_id]
    current = A(att.state)
    if current == A.UNCERTAIN or current == target:
        if current != target:
            set_attempt(ctx, attempt_id, target, **detail)
        return
    for step in _ORDER[_ORDER.index(current) + 1:_ORDER.index(target) + 1]:
        set_attempt(ctx, attempt_id, step, **detail)


def release(ctx: Ctx, attempt_id: str) -> None:
    if ctx.state.holds.pop(attempt_id, None) is not None:
        ctx.audit("reservation_released", ctx.state.attempts[attempt_id].task_id, attempt_id)


def add_outbox(ctx: Ctx, kind: str, attempt_id: str, payload: dict[str, Any]) -> OutboxItem:
    state = ctx.state
    item = OutboxItem(id=f"out-{state.next('outbox'):05d}", kind=kind, attempt_id=attempt_id,
                      key=f"{state.plan_id}:r{state.revision}:{attempt_id}:{kind}", payload=payload)
    state.outbox.append(item)
    ctx.audit("dispatch_intent", state.attempts[attempt_id].task_id, attempt_id, kind=kind, outbox=item.id)
    return item


def void_outbox(ctx: Ctx, attempt_id: str, *kinds: str) -> None:
    for item in ctx.state.outbox:
        if item.attempt_id == attempt_id and item.status == "pending" and (not kinds or item.kind in kinds):
            item.status = "void"
            ctx.audit("dispatch_voided", ctx.state.attempts[attempt_id].task_id, attempt_id, kind=item.kind)


def prune_outbox(ctx: Ctx) -> int:
    """Bound the outbox: past OUTBOX_LIMIT items, drop settled orders of closed attempts, except the newest OUTBOX_KEEP.
    Pending orders and anything of a live attempt are never dropped."""
    outbox = ctx.state.outbox
    if len(outbox) <= OUTBOX_LIMIT:
        return 0
    cutoff = len(outbox) - OUTBOX_KEEP
    kept = [item for index, item in enumerate(outbox)
            if index >= cutoff or item.status == "pending" or A(ctx.state.attempts[item.attempt_id].state) in ATTEMPT_LIVE]
    dropped = len(outbox) - len(kept)
    if dropped:
        outbox[:] = kept
        ctx.audit("outbox_pruned", dropped=dropped)
    return dropped


def mark_delivered(ctx: Ctx, attempt_id: str, kind: str) -> None:
    for item in ctx.state.outbox:
        if item.attempt_id == attempt_id and item.kind == kind and item.status == "pending":
            item.status = "delivered"


def promote_ready(ctx: Ctx) -> int:
    """PENDING -> READY for tasks whose every prerequisite is COMPLETED (which only a verdict can cause). The test is on
    every ancestor, not only the direct ones: after a rework that sends back a task and not what depends on it, a task can
    have all its direct prerequisites completed while one further up is being redone."""
    prune_composition_holds(ctx.plan, ctx.state)
    enforce_gate_waiting(ctx)
    moved = 0
    for spec in ctx.plan.tasks:
        rec = ctx.state.tasks[spec.id]
        if rec.state == T.PENDING.value and all(ctx.state.tasks[d].state == T.COMPLETED.value
                                                for d in (*spec.after, *ctx.plan.ancestors(spec.id))):
            if gate_waiting(ctx.plan, ctx.state, spec.id):
                continue
            set_task(ctx, spec.id, T.READY, reason="prerequisites_completed")
            moved += 1
    return moved


def enforce_gate_waiting(ctx: Ctx, *, confirmed_unsent_attempt: str = "") -> int:
    """Demote blocked gates and descendants before they are reserved or dispatched."""
    prune_composition_holds(ctx.plan, ctx.state)
    moved = 0
    for spec in ctx.plan.tasks:
        rec = ctx.state.tasks[spec.id]
        if not gate_waiting(ctx.plan, ctx.state, spec.id):
            continue
        held_gate = next((gate for gate in ctx.plan.composition_gates
                          if gate.task in ({spec.id} | ctx.plan.ancestors(spec.id)) and
                          gate.task in ctx.state.composition_holds), None)
        reasons = (f"composition_hold:{held_gate.task}:"
                   f"{ctx.state.composition_holds[held_gate.task]['composition_id']}"
                   if held_gate else ",".join(f"{kind}:{member}" for member, kind in
                                                stale_subplan_members(ctx.plan, ctx.state, spec.id)))
        if rec.state == T.READY.value:
            set_task(ctx, spec.id, T.PENDING, reason="composition_waiting", detail=reasons)
            moved += 1
        elif rec.state == T.ACTIVE.value:
            attempt = live_attempt(ctx.state, spec.id)
            pending_start = next((item for item in ctx.state.outbox if attempt is not None and
                                  item.attempt_id == attempt.id and item.kind == "start" and
                                  item.status == "pending" and
                                  (item.deliveries == 0 or item.attempt_id == confirmed_unsent_attempt)), None)
            if attempt is not None and A(attempt.state) == A.RESERVED and pending_start is not None:
                end_attempt(ctx, attempt.id, A.CANCELLED, "composition_waiting", reasons)
                set_task(ctx, spec.id, T.PENDING, reason="composition_waiting", detail=reasons)
                moved += 1
    return moved


def live_attempt(state: RunState, task_id: str) -> AttemptRec | None:
    for attempt_id in reversed(state.tasks[task_id].attempts):
        att = state.attempts[attempt_id]
        if A(att.state) in ATTEMPT_LIVE:
            return att
    return None


def end_attempt(ctx: Ctx, attempt_id: str, new: A, cause: str, detail: str = "", *, classification: str = "") -> None:
    """Close an attempt as failed/rejected/cancelled: free its resources and move the task on.

    The task goes to RECOVERING (a decision is due) or, when a cancellation was authorised, to CANCELLED."""
    att = ctx.state.attempts[attempt_id]
    set_attempt(ctx, attempt_id, new, cause=cause)
    att.failure = detail or cause
    att.failure_classification = classification
    release(ctx, attempt_id)
    void_outbox(ctx, attempt_id)
    rec = ctx.state.tasks[att.task_id]
    if T(rec.state) != T.ACTIVE:
        return
    if ctx.state.cancel_requested:
        set_task(ctx, att.task_id, T.CANCELLED, reason="cancelled")
    else:
        rec.reason = cause
        set_task(ctx, att.task_id, T.RECOVERING, cause=cause)
