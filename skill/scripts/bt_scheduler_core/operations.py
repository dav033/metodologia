"""Authorised operator operations: pause, resume, cancel, reopen, manual resolution of an uncertain attempt.

Each one needs `by` (who authorises) and leaves an audit entry. None of them can complete a task: completion only
ever comes from an independent verdict.
"""
from __future__ import annotations

from .contracts import ExecutionStatus
from .errors import SchedulerError
from .recovery import apply_observation
from .states import ATTEMPT_LIVE
from .states import AttemptState as A
from .states import TaskState as T
from .transitions import Ctx, add_outbox, end_attempt, live_attempt, set_task, void_outbox


def _who(by: object, reason: object) -> tuple[str, str]:
    if not isinstance(by, str) or not by.strip():
        raise SchedulerError("NOT_ALLOWED", "an operation needs `by` (who authorises it)")
    return by.strip(), str(reason or "")[:300]


def pause(ctx: Ctx, by: str, reason: str = "") -> None:
    by, reason = _who(by, reason)
    ctx.state.paused = True
    ctx.audit("run_paused", by=by, reason=reason)


def resume(ctx: Ctx, by: str, reason: str = "") -> None:
    by, reason = _who(by, reason)
    ctx.state.paused = False
    ctx.audit("run_resumed", by=by, reason=reason)


def cancel(ctx: Ctx, by: str, reason: str = "") -> None:
    """Cancel everything that has not started; ask the executor to stop what is running (the attempt closes when the
    executor confirms, or when reconciliation shows it gone)."""
    by, reason = _who(by, reason)
    state = ctx.state
    state.cancel_requested = True
    ctx.audit("run_cancel_requested", by=by, reason=reason)
    for spec in ctx.plan.tasks:
        rec = state.tasks[spec.id]
        if rec.state in (T.PENDING.value, T.READY.value, T.RECOVERING.value, T.BLOCKED.value):
            rec.reason = "cancelled"
            set_task(ctx, spec.id, T.CANCELLED, by=by)
        elif rec.state == T.ACTIVE.value:
            att = live_attempt(state, spec.id)
            if att is None:
                continue
            start = next((i for i in state.outbox if i.attempt_id == att.id and i.kind == "start"), None)
            if A(att.state) == A.RESERVED and start is not None and start.status == "pending" and start.deliveries == 0:
                end_attempt(ctx, att.id, A.CANCELLED, "cancelled", "cancelled_before_dispatch")
            else:
                void_outbox(ctx, att.id, "start")      # a start still pending must never be (re)sent after a cancel
                if not any(i.attempt_id == att.id and i.kind == "cancel" for i in state.outbox):
                    add_outbox(ctx, "cancel", att.id, {"token": att.token, "reason": reason})


def reopen(ctx: Ctx, task_id: str, by: str, reason: str = "") -> None:
    """BLOCKED -> READY with a fresh attempt budget. Completed and cancelled tasks never reopen (new revision instead)."""
    by, reason = _who(by, reason)
    if task_id not in ctx.state.tasks:
        raise SchedulerError("UNKNOWN_TASK", task_id)
    rec = ctx.state.tasks[task_id]
    if rec.state != T.BLOCKED.value or ctx.state.cancel_requested:
        raise SchedulerError("NOT_ALLOWED", f"only a blocked task of a live run can be reopened ({task_id} is {rec.state})")
    rec.budget_base, rec.reason, rec.hold_until, rec.waits = len(rec.attempts), "", 0.0, 0
    set_task(ctx, task_id, T.READY, by=by, reason=reason, decision="reopen")


def resolve_attempt(ctx: Ctx, attempt_id: str, outcome: str, by: str, reason: str = "") -> str:
    """Manual answer for an attempt reconciliation could not settle: failed | finished | cancelled | running."""
    by, reason = _who(by, reason)
    att = ctx.state.attempts.get(attempt_id)
    if att is None:
        raise SchedulerError("UNKNOWN_ATTEMPT", attempt_id)
    if A(att.state) not in ATTEMPT_LIVE:
        raise SchedulerError("NOT_ALLOWED", f"attempt {attempt_id} is already {att.state}")
    if outcome not in ("failed", "finished", "cancelled", "running"):
        raise SchedulerError("NOT_ALLOWED", f"unknown outcome {outcome!r}")
    ctx.audit("attempt_resolved_manually", att.task_id, attempt_id, by=by, outcome=outcome, reason=reason)
    return apply_observation(ctx, attempt_id, ExecutionStatus(outcome, f"manual: {reason}"), manual=True)
