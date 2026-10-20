"""Authorised operations: pause, resume, cancel, reopen, rework, manual resolution of an uncertain attempt.

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
from .transitions import Ctx, add_outbox, end_attempt, live_attempt, promote_ready, set_task, void_outbox


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
    """BLOCKED -> READY with a fresh attempt budget. Completed tasks come back only through `rework`; cancelled ones never (new revision instead)."""
    by, reason = _who(by, reason)
    if task_id not in ctx.state.tasks:
        raise SchedulerError("UNKNOWN_TASK", task_id)
    rec = ctx.state.tasks[task_id]
    if rec.state != T.BLOCKED.value or ctx.state.cancel_requested:
        raise SchedulerError("NOT_ALLOWED", f"only a blocked task of a live run can be reopened ({task_id} is {rec.state})")
    rec.budget_base, rec.reason, rec.hold_until, rec.waits = len(rec.attempts), "", 0.0, 0
    set_task(ctx, task_id, T.READY, by=by, reason=reason, decision="reopen")


def rework_scope(ctx: Ctx, task_ids: tuple[str, ...]) -> tuple[str, ...]:
    """The tasks a rework of `task_ids` sends back: each one and everything downstream of it, in plan order."""
    for task_id in task_ids:
        if task_id not in ctx.state.tasks:
            raise SchedulerError("UNKNOWN_TASK", task_id)
    wanted = set(task_ids)
    for task_id in task_ids:
        wanted |= ctx.plan.descendants(task_id)
    return tuple(spec.id for spec in ctx.plan.tasks if spec.id in wanted)


def _building(ctx: Ctx, task_id: str):
    """The live attempt of a task that is still producing work (reserved, dispatched or running). An attempt that already
    finished and only waits for its verdict (VERIFYING) is not building anything: a rework supersedes it."""
    att = live_attempt(ctx.state, task_id)
    return att if att is not None and A(att.state) != A.VERIFYING else None


def rework_problem(ctx: Ctx, task_ids: tuple[str, ...], also: tuple[str, ...] = (), *, owner: bool = False) -> str:
    """Why a rework cannot start now ('' when it can). The text starts with a code: `cancelled` (the run is being
    cancelled), `limit` (a named task was already sent back `max_reworks` times: only the owner can decide more) or
    `busy` (a task it would reset is still building: its result would sit on work being redone, try later). `also` is
    the task whose rejecting verdict asks for the rework: its attempt closes with that verdict. An attempt waiting for
    its verdict does not count: two audits that both reject would otherwise wait for each other forever, so the rework
    supersedes it instead (see `rework`)."""
    if ctx.state.cancel_requested:
        return "cancelled: the run is being cancelled"
    scope = rework_scope(ctx, (*task_ids, *also))
    for task_id in () if owner else task_ids:      # the owner may send work back more often than the system does
        if ctx.state.tasks[task_id].reworks >= ctx.config.max_reworks:
            return f"limit: {task_id} was already sent back {ctx.config.max_reworks} time(s)"
    live = [task_id for task_id in scope if task_id not in also and _building(ctx, task_id) is not None]
    if live:
        return f"busy: live attempt on {', '.join(live)}"
    return ""


def rework(ctx: Ctx, task_ids: tuple[str, ...], by: str, reason: str = "", *, also: tuple[str, ...] = (),
           owner: bool = False) -> tuple[str, ...]:
    """Send accepted work back: the named tasks, the tasks downstream of them and `also` (the task whose rejection asked
    for it) return to PENDING with a fresh attempt budget; those whose prerequisites are all still completed become
    READY at once. It never completes anything: the redone work needs a new independent verdict. Cancelled tasks stay."""
    by, reason = _who(by, reason)
    if not task_ids:
        raise SchedulerError("NOT_ALLOWED", "rework needs at least one task")
    problem = rework_problem(ctx, task_ids, also, owner=owner)
    if problem:
        raise SchedulerError("NOT_ALLOWED", f"rework refused: {problem}")
    scope = rework_scope(ctx, (*task_ids, *also))
    moved = []
    for task_id in scope:
        att = live_attempt(ctx.state, task_id)
        if att is not None and task_id not in also and A(att.state) == A.VERIFYING:
            # finished work waiting for a verdict that would judge the old result: its verdict becomes stale
            end_attempt(ctx, att.id, A.CANCELLED, "superseded_by_rework", f"superseded_by_rework: reworked by {by}")
        rec = ctx.state.tasks[task_id]
        if rec.state in (T.PENDING.value, T.CANCELLED.value):
            continue
        rec.budget_base, rec.reason, rec.hold_until, rec.waits = len(rec.attempts), "", 0.0, 0
        rec.reworks += 1
        set_task(ctx, task_id, T.PENDING, by=by, reason=reason, decision="rework")
        moved.append(task_id)
    ctx.audit("rework_requested", by=by, reason=reason, named=list(task_ids), tasks=moved)
    promote_ready(ctx)
    return tuple(moved)


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
