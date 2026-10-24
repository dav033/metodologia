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
    ctx.state.next("stop")
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
    state.next("stop")
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


def block_task(ctx: Ctx, task_id: str, by: str, reason: str = "") -> None:
    by, reason = _who(by, reason)
    rec = ctx.state.tasks.get(task_id)
    if rec is None:
        raise SchedulerError("UNKNOWN_TASK", task_id)
    if ctx.state.cancel_requested or T(rec.state) not in (T.READY, T.RECOVERING):
        raise SchedulerError("NOT_ALLOWED", f"only a ready or recovering task can be blocked ({task_id} is {rec.state})")
    rec.reason = reason
    set_task(ctx, task_id, T.BLOCKED, by=by, reason=reason, decision="operator_block")


def reopen(ctx: Ctx, task_id: str, by: str, reason: str = "") -> None:
    """BLOCKED/RECOVERING -> READY with a fresh attempt budget. Completed tasks come back only through `rework`; cancelled ones never (new revision instead)."""
    by, reason = _who(by, reason)
    if task_id not in ctx.state.tasks:
        raise SchedulerError("UNKNOWN_TASK", task_id)
    rec = ctx.state.tasks[task_id]
    if rec.state not in (T.BLOCKED.value, T.RECOVERING.value) or ctx.state.cancel_requested:
        raise SchedulerError("NOT_ALLOWED", f"only a blocked or recovering task of a live run can be reopened ({task_id} is {rec.state})")
    rec.budget_base = sum(ctx.state.attempts[attempt_id].budget_consumed for attempt_id in rec.attempts)
    rec.reason, rec.hold_until, rec.waits = "", 0.0, 0
    waiting = [a for a in ctx.plan.ancestors(task_id) if ctx.state.tasks[a].state != T.COMPLETED.value]
    # a task whose prerequisites are being redone waits for them like any other pending task
    set_task(ctx, task_id, T.PENDING if waiting else T.READY, by=by, reason=reason, decision="reopen")


def rework_scope(ctx: Ctx, task_ids: tuple[str, ...], cascade: bool = True) -> tuple[str, ...]:
    """The tasks a rework of `task_ids` sends back, in plan order: each one and, with `cascade`, everything downstream of
    it. Without it only the tasks named are redone (the caller names whatever else must rerun, such as the checks over
    the changed result); what depends on them keeps its accepted result, which the integrator merges with the redo."""
    for task_id in task_ids:
        if task_id not in ctx.state.tasks:
            raise SchedulerError("UNKNOWN_TASK", task_id)
    wanted = set(task_ids)
    for task_id in task_ids if cascade else ():
        wanted |= ctx.plan.descendants(task_id)
    return tuple(spec.id for spec in ctx.plan.tasks if spec.id in wanted)


def _building(ctx: Ctx, task_id: str):
    """The live attempt of a task that is still producing work (reserved, dispatched or running). An attempt that already
    finished and only waits for its verdict (VERIFYING) is not building anything: a rework supersedes it."""
    att = live_attempt(ctx.state, task_id)
    return att if att is not None and A(att.state) != A.VERIFYING else None


def rework_impact(ctx: Ctx, scope: tuple[str, ...], also: tuple[str, ...] = ()) -> tuple[str, ...]:
    """The ACCEPTED tasks a rework over `scope` would throw away (what the owner is asked to confirm past a ceiling)."""
    return tuple(task_id for task_id in scope if task_id not in also
                 and ctx.state.tasks[task_id].state == T.COMPLETED.value)


def rework_problem(ctx: Ctx, task_ids: tuple[str, ...], also: tuple[str, ...] = (), *, owner: bool = False,
                   cascade: bool = True, confirmed: bool = False) -> str:
    """Why a rework cannot start now ('' when it can). The text starts with a code: `cancelled` (the run is being
    cancelled), `limit` (a named task was already sent back `max_reworks` times: only the owner can decide more),
    `impact` (it would throw away more accepted tasks than `Config.rework_confirm_over`: only an owner who confirms
    it can) or `busy` (a task it would reset is still building: its result would sit on work being redone, try later). `also` is
    the task whose rejecting verdict asks for the rework: its attempt closes with that verdict. An attempt waiting for
    its verdict does not count: two audits that both reject would otherwise wait for each other forever, so the rework
    supersedes it instead (see `rework`)."""
    if ctx.state.cancel_requested:
        return "cancelled: the run is being cancelled"
    scope = rework_scope(ctx, (*task_ids, *also), cascade)
    for task_id in () if owner else task_ids:      # the owner may send work back more often than the system does
        if ctx.state.tasks[task_id].reworks >= ctx.config.max_reworks:
            return f"limit: {task_id} was already sent back {ctx.config.max_reworks} time(s)"
    ceiling = ctx.config.rework_confirm_over
    if ceiling and not confirmed:
        lost = rework_impact(ctx, scope, also)
        if len(lost) > ceiling:
            return f"impact: it would send back {len(lost)} accepted tasks ({', '.join(lost[:8])}{', …' if len(lost) > 8 else ''}); " \
                   f"more than {ceiling} needs the owner's confirmation"
    live = [task_id for task_id in scope if task_id not in also and _building(ctx, task_id) is not None]
    if live:
        return f"busy: live attempt on {', '.join(live)}"
    return ""


def rework(ctx: Ctx, task_ids: tuple[str, ...], by: str, reason: str = "", *, also: tuple[str, ...] = (),
           owner: bool = False, cascade: bool = True, confirmed: bool = False) -> tuple[str, ...]:
    """Send accepted work back: the named tasks, the tasks downstream of them and `also` (the task whose rejection asked
    for it) return to PENDING with a fresh attempt budget; those whose prerequisites are all still completed become
    READY at once. It never completes anything: the redone work needs a new independent verdict. Cancelled tasks stay."""
    by, reason = _who(by, reason)
    if not task_ids:
        raise SchedulerError("NOT_ALLOWED", "rework needs at least one task")
    problem = rework_problem(ctx, task_ids, also, owner=owner, cascade=cascade, confirmed=confirmed)
    if problem:
        raise SchedulerError("NOT_ALLOWED", f"rework refused: {problem}")
    scope = rework_scope(ctx, (*task_ids, *also), cascade)
    moved = []
    for task_id in scope:
        att = live_attempt(ctx.state, task_id)
        if att is not None and task_id not in also and A(att.state) == A.VERIFYING:
            # finished work waiting for a verdict that would judge the old result: its verdict becomes stale
            end_attempt(ctx, att.id, A.CANCELLED, "superseded_by_rework", f"superseded_by_rework: reworked by {by}")
        rec = ctx.state.tasks[task_id]
        if rec.state in (T.PENDING.value, T.CANCELLED.value):
            continue
        rec.budget_base = sum(ctx.state.attempts[attempt_id].budget_consumed for attempt_id in rec.attempts)
        rec.reason, rec.hold_until, rec.waits = "", 0.0, 0
        rec.reworks += 1
        set_task(ctx, task_id, T.PENDING, by=by, reason=reason, decision="rework")
        moved.append(task_id)
    if not cascade:
        _hold_dependents(ctx, set(moved), by)
    ctx.audit("rework_requested", by=by, reason=reason, named=list(task_ids), tasks=moved, cascade=cascade)
    promote_ready(ctx)
    return tuple(moved)


def _hold_dependents(ctx: Ctx, moved: set[str], by: str) -> None:
    """Tasks that depend on a task just sent back and keep their own state (a rework without cascade) must not start while
    it is redone: those waiting to start (ready, blocked or recovering, with no live attempt) go back to pending and
    become ready again when every ancestor is completed. A dependent already running keeps going on what it started from."""
    for spec in ctx.plan.tasks:
        rec = ctx.state.tasks[spec.id]
        if spec.id in moved or rec.state not in (T.READY.value, T.BLOCKED.value, T.RECOVERING.value):
            continue
        if live_attempt(ctx.state, spec.id) is None and moved & set(ctx.plan.ancestors(spec.id)):
            set_task(ctx, spec.id, T.PENDING, by=by, reason="prerequisite_sent_back", decision="rework_wait")


def withdraw_rework(ctx: Ctx, task_ids: tuple[str, ...], by: str, reason: str = "") -> tuple[str, ...]:
    """Take a rework back: each task returns to COMPLETED on the accepted result it already had. Allowed only while nothing
    has been redone since (no live attempt, and every attempt after the accepted one ended without producing a result),
    so no work is lost and no verdict is invented: the result was accepted by an independent verdict before. Tasks that
    were never accepted, or that were redone, are refused and nothing changes."""
    by, reason = _who(by, reason)
    if not task_ids:
        raise SchedulerError("NOT_ALLOWED", "withdraw needs at least one task")
    for task_id in task_ids:
        if task_id not in ctx.state.tasks:
            raise SchedulerError("UNKNOWN_TASK", task_id)
        rec = ctx.state.tasks[task_id]
        if rec.state not in (T.PENDING.value, T.READY.value, T.BLOCKED.value, T.RECOVERING.value) or rec.reworks < 1:
            raise SchedulerError("NOT_ALLOWED", f"{task_id} is {rec.state} with {rec.reworks} rework(s): nothing to take back")
        accepted = [a for a in rec.attempts if A(ctx.state.attempts[a].state) == A.ACCEPTED]
        if not accepted:
            raise SchedulerError("NOT_ALLOWED", f"{task_id} has no accepted result to restore")
        later = rec.attempts[rec.attempts.index(accepted[-1]) + 1:]
        if any(A(ctx.state.attempts[a].state) not in (A.CANCELLED, A.FAILED) for a in later):
            raise SchedulerError("NOT_ALLOWED", f"{task_id} was redone since its accepted result: it cannot be taken back")
    for task_id in task_ids:
        rec = ctx.state.tasks[task_id]
        rec.reworks -= 1
        rec.reason, rec.hold_until, rec.waits = "", 0.0, 0
        set_task(ctx, task_id, T.COMPLETED, restore=True, by=by, reason=reason, decision="withdraw_rework")
    ctx.audit("rework_withdrawn", by=by, reason=reason, tasks=list(task_ids))
    promote_ready(ctx)
    return tuple(task_ids)


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
