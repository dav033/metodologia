"""After a bad attempt: recovery decisions, and what reconciliation learned about an attempt.

M5 only advises (a `RecoveryProposal`); this module decides whether the advice is valid and applies it, or falls back
to the explicit deterministic policy "retry while the attempt budget lasts, then block". No semantic diagnosis here.
"""
from __future__ import annotations

from .contracts import (
    EXEC_STATES,
    RECOVERY_ACTIONS,
    ExecutionStatus,
    FailureContext,
    RecoveryProposal,
)
from .events import request_verification
from .model import RunState
from .states import AttemptState as A
from .states import TaskState as T
from .transitions import (
    Ctx,
    advance,
    end_attempt,
    mark_delivered,
    set_attempt,
    set_task,
)


MIN_WAIT = 1.0     # a `wait` of 0 would be re-asked at once, forever: every wait holds at least this long


def attempts_used(state: RunState, task_id: str) -> int:
    rec = state.tasks[task_id]
    return len(rec.attempts) - rec.budget_base


def pending(ctx: Ctx) -> list[FailureContext]:
    """RECOVERING tasks whose hold (if any) has elapsed, in plan order."""
    out = []
    for spec in ctx.plan.tasks:
        rec = ctx.state.tasks[spec.id]
        if rec.state != T.RECOVERING.value or rec.hold_until > ctx.now:
            continue
        last = ctx.state.attempts[rec.attempts[-1]]
        out.append(FailureContext(plan_id=ctx.state.plan_id, task_id=spec.id, attempt_id=last.id, cause=rec.reason,
                                  attempts_used=attempts_used(ctx.state, spec.id), max_attempts=ctx.config.max_attempts,
                                  detail=last.failure))
    return out


def valid_proposal(value: object) -> bool:
    return (isinstance(value, RecoveryProposal) and value.action in RECOVERY_ACTIONS
            and isinstance(value.wait_seconds, (int, float)) and not isinstance(value.wait_seconds, bool)
            and value.wait_seconds >= 0 and isinstance(value.reason, str))


def apply_recovery(ctx: Ctx, context: FailureContext, proposal: object) -> str:
    """Apply a (possibly absent or invalid) proposal; returns the source of the decision (port | policy), `waiting` when
    it only deferred the decision, or `stale`."""
    rec = ctx.state.tasks[context.task_id]
    if rec.state != T.RECOVERING.value or rec.attempts[-1] != context.attempt_id:
        return "stale"
    remaining = ctx.config.max_attempts - attempts_used(ctx.state, context.task_id)
    source = "port" if valid_proposal(proposal) else "policy"
    if source == "policy":
        if proposal is not None:
            ctx.audit("port_invalid", context.task_id, context.attempt_id, port="recovery")
        proposal = RecoveryProposal("retry", "default_policy") if remaining > 0 else RecoveryProposal("block", "attempts_exhausted")
    action = proposal.action
    if action == "retry" and remaining <= 0:
        ctx.audit("recovery_refused", context.task_id, context.attempt_id, wanted="retry", why="attempts_exhausted")
        action, proposal = "block", RecoveryProposal("block", "attempts_exhausted")
    if action == "retry":
        rec.reason = ""
        set_task(ctx, context.task_id, T.READY, decision="retry", source=source)
    elif action == "block":
        rec.reason = proposal.reason or "recovery_block"
        set_task(ctx, context.task_id, T.BLOCKED, decision="block", source=source, reason=rec.reason)
    elif rec.waits >= ctx.config.max_recovery_waits:
        rec.reason = "recovery_wait_limit"
        set_task(ctx, context.task_id, T.BLOCKED, decision="block", source="policy", reason=rec.reason)
    else:
        rec.waits += 1
        rec.hold_until = ctx.now + min(max(float(proposal.wait_seconds), MIN_WAIT), ctx.config.max_recovery_wait)
        ctx.audit("recovery_wait", context.task_id, context.attempt_id, until=rec.hold_until, source=source, waits=rec.waits)
        return "waiting"
    return source


def apply_observation(ctx: Ctx, attempt_id: str, status: object, *, manual: bool = False) -> str:
    """Fold what an executor said about an attempt (reconciliation) into the state. Unknown -> UNCERTAIN, never a guess.

    A VERIFYING attempt is settled by a verdict, not by what the executor says afterwards: only an operator
    (`manual`) can override that."""
    att = ctx.state.attempts[attempt_id]
    current = A(att.state)
    if current not in (A.RESERVED, A.DISPATCHED, A.RUNNING, A.VERIFYING, A.UNCERTAIN):
        return "closed"
    verdict = status.state if isinstance(status, ExecutionStatus) and status.state in EXEC_STATES else "unknown"
    if current == A.VERIFYING and not manual and verdict in ("failed", "not_found", "cancelled", "unknown"):
        ctx.audit("observation_ignored", att.task_id, attempt_id, observed=verdict, why="verifying_is_settled_by_verdict")
        return "ignored"
    att.needs_reconcile = False
    # an answer we could not read is asked again soon, not after a whole lease
    att.lease_expires_at = ctx.now + (min(ctx.config.lease_seconds, ctx.config.reconcile_seconds)
                                      if verdict == "unknown" else ctx.config.lease_seconds)
    if verdict == "running":
        mark_delivered(ctx, attempt_id, "start")
        if current != A.RUNNING:
            advance(ctx, attempt_id, A.RUNNING, via="reconcile")
    elif verdict == "finished":
        mark_delivered(ctx, attempt_id, "start")
        advance(ctx, attempt_id, A.VERIFYING, via="reconcile")
        request_verification(ctx, attempt_id)
    elif verdict == "failed":
        end_attempt(ctx, attempt_id, A.FAILED, "execution_failed", getattr(status, "detail", "") or "reported_failed")
    elif verdict == "cancelled":
        end_attempt(ctx, attempt_id, A.CANCELLED, "execution_failed", "cancelled_by_executor")
    elif verdict == "not_found":
        start = next((i for i in ctx.state.outbox if i.attempt_id == attempt_id and i.kind == "start"), None)
        if start is not None and start.status == "pending" and current in (A.RESERVED, A.UNCERTAIN):
            if current == A.UNCERTAIN:
                set_attempt(ctx, attempt_id, A.RESERVED, why="executor never received the order")
            ctx.audit("reconcile_redeliver", att.task_id, attempt_id)   # never reached the executor: safe to deliver
        else:
            end_attempt(ctx, attempt_id, A.FAILED, "lost", "executor has no record of the attempt")
    else:
        if current != A.UNCERTAIN:
            set_attempt(ctx, attempt_id, A.UNCERTAIN, why="executor_state_unknown")
    ctx.audit("reconciled", att.task_id, attempt_id, observed=verdict)
    return verdict
