"""Applying facts (events) and independent verdicts to the run state: idempotent, correlated, guarded.

Outcomes: applied | duplicate | stale | invalid | noop. A stale or invalid message is recorded in the audit trail and
changes nothing. An agent's "finished" only moves the attempt to VERIFYING; only a verdict can complete a task.
"""
from __future__ import annotations

from .contracts import Event, IngestResult, Verdict, verdict_problem
from .model import REJECTED_LIMIT
from .states import (
    ATTEMPT_LIVE,
    ATTEMPT_TERMINAL,
    EVENT_SOURCES,
    EVENT_TARGETS,
    EventKind,
    rank,
)
from .states import AttemptState as A
from .states import TaskState as T
from .transitions import (
    Ctx,
    add_outbox,
    advance,
    end_attempt,
    mark_delivered,
    promote_ready,
    release,
    set_attempt,
    set_task,
    void_outbox,
)


def _reject(ctx: Ctx, status: str, reason: str, msg_id: str, task_id: str = "", attempt_id: str = "") -> IngestResult:
    """Refuse a message. A refused id is NOT remembered as processed (a corrected retry with the same id may still be
    applied); a short window of recent refusals only stops the same refusal from being audited over and over."""
    state = ctx.state
    key = f"{msg_id}|{reason}"
    if key not in state.rejected_recent:
        ctx.audit("message_rejected", task_id, attempt_id, status=status, reason=reason, message=msg_id)
        state.rejected_recent.append(key)
        del state.rejected_recent[:-REJECTED_LIMIT]
    return IngestResult(status, reason, msg_id)


def _preflight(ctx: Ctx, msg_id: str, plan_id: str, revision: int, task_id: str, attempt_id: str,
               token: int | None, *, allow_superseded: bool = False) -> tuple[IngestResult | None, object]:
    state = ctx.state
    if plan_id != state.plan_id or revision != state.revision:
        return _reject(ctx, "invalid", "wrong_plan", msg_id), None
    if allow_superseded and ctx.tx.has_incident_event(msg_id):
        return IngestResult("duplicate", "already_processed", msg_id), None
    if state.has_seen(msg_id):
        return IngestResult("duplicate", "already_processed", msg_id), None
    att = state.attempts.get(attempt_id)
    if att is None or att.task_id != task_id:
        return _reject(ctx, "invalid", "unknown_attempt", msg_id, task_id, attempt_id), None
    if token is not None and token != att.token:
        return _reject(ctx, "stale", "token_mismatch", msg_id, task_id, attempt_id), None
    task = state.tasks.get(task_id)
    if task is None or (not allow_superseded and task.attempts[-1] != attempt_id):
        return _reject(ctx, "stale", "superseded_attempt", msg_id, task_id, attempt_id), None
    return None, att


def apply_event(ctx: Ctx, event: Event) -> IngestResult:
    kind = EventKind(event.kind)
    early, att = _preflight(ctx, event.event_id, event.plan_id, event.revision, event.task_id, event.attempt_id,
                            event.token, allow_superseded=kind == EventKind.INCIDENT_OBSERVED)
    if early:
        return early
    attempt_id, current = att.id, A(att.state)
    if kind == EventKind.INCIDENT_OBSERVED:
        detail = {key: value for key, value in event.payload.items() if key not in ("task_id", "attempt_id")}
        ctx.audit("incident_observed", att.task_id, attempt_id, **detail)
        ctx.state.remember(event.event_id)
        return IngestResult("applied", "", event.event_id)
    if current in ATTEMPT_TERMINAL:
        return _reject(ctx, "stale", "attempt_closed", event.event_id, att.task_id, attempt_id)
    att.last_event_at = ctx.now
    att.lease_expires_at, att.needs_reconcile = ctx.now + ctx.config.lease_seconds, False
    if kind == EventKind.HEARTBEAT:
        return IngestResult("noop", "liveness_hint", event.event_id)  # never changes a state, proves nothing
    target = EVENT_TARGETS[kind]
    if current == target or (kind == EventKind.EXECUTION_STARTED and rank(current) > rank(target)):
        reason = "already_in_state" if current == target else "already_past"
        return _reject(ctx, "noop" if current == target else "stale", reason, event.event_id, att.task_id, attempt_id)
    if current not in EVENT_SOURCES[kind]:
        reason = "already_past" if rank(current) > rank(target) else "illegal_for_state"
        return _reject(ctx, "stale" if reason == "already_past" else "invalid", reason, event.event_id, att.task_id, attempt_id)
    detail = str(event.payload.get("reason", ""))[:300]
    if kind == EventKind.EXECUTION_STARTED:
        att.budget_consumed = True
        mark_delivered(ctx, attempt_id, "start")
        advance(ctx, attempt_id, A.RUNNING, source=event.source)
    elif kind == EventKind.EXECUTION_FINISHED:
        att.budget_consumed = True
        mark_delivered(ctx, attempt_id, "start")
        advance(ctx, attempt_id, A.VERIFYING, source=event.source)
        request_verification(ctx, attempt_id)
    elif kind == EventKind.EXECUTION_FAILED:
        att.budget_consumed = True
        end_attempt(ctx, attempt_id, A.FAILED, "execution_failed", detail)
    else:
        end_attempt(ctx, attempt_id, A.CANCELLED, "execution_failed", detail or "cancelled_by_executor")
    ctx.state.remember(event.event_id)                 # only an applied message is remembered as processed
    return IngestResult("applied", "", event.event_id)


def request_verification(ctx: Ctx, attempt_id: str) -> None:
    att = ctx.state.attempts[attempt_id]
    if any(i.attempt_id == attempt_id and i.kind == "verify" and i.status in ("pending", "delivered")
           for i in ctx.state.outbox):
        return                                  # an abandoned (void) order may be asked again, e.g. by an operator
    spec = ctx.plan.task(att.task_id)
    add_outbox(ctx, "verify", attempt_id, {"task_id": att.task_id, "token": att.token,
                                           "acceptance_criteria": list(spec.acceptance_criteria),
                                           "verification": [dict(v) for v in spec.verification]})


def apply_verdict(ctx: Ctx, verdict: Verdict) -> IngestResult:
    problem = verdict_problem(verdict)
    if problem:
        return _reject(ctx, "invalid", problem, str(getattr(verdict, "verdict_id", "")))
    early, att = _preflight(ctx, verdict.verdict_id, verdict.plan_id, verdict.revision, verdict.task_id,
                            verdict.attempt_id, verdict.token)
    if early:
        return early
    attempt_id = att.id
    if A(att.state) != A.VERIFYING:
        reason = "attempt_not_verifying" if A(att.state) in ATTEMPT_LIVE else "attempt_closed"
        return _reject(ctx, "stale", reason, verdict.verdict_id, att.task_id, attempt_id)
    if not isinstance(verdict.verifier, str) or not verdict.verifier.strip():
        return _reject(ctx, "invalid", "verifier_missing", verdict.verdict_id, att.task_id, attempt_id)
    if ctx.config.require_independent_verifier and verdict.verifier.strip() == att.executor:
        return _reject(ctx, "invalid", "verifier_not_independent", verdict.verdict_id, att.task_id, attempt_id)
    evidence = verdict.evidence.strip() if isinstance(verdict.evidence, str) else ""
    if verdict.accepted and not evidence:
        return _reject(ctx, "invalid", "evidence_missing", verdict.verdict_id, att.task_id, attempt_id)
    att.verifier, att.evidence = verdict.verifier.strip(), evidence[:2000]
    if verdict.accepted:
        set_attempt(ctx, attempt_id, A.ACCEPTED, verifier=att.verifier)
        release(ctx, attempt_id)
        void_outbox(ctx, attempt_id)
        set_task(ctx, att.task_id, T.COMPLETED, attempt=attempt_id, verifier=att.verifier)
        promote_ready(ctx)
    else:
        end_attempt(ctx, attempt_id, A.REJECTED, "verification_rejected", evidence or "verdict rejected the work")
    ctx.state.remember(verdict.verdict_id)
    return IngestResult("applied", "", verdict.verdict_id)
