"""M1-owned durable holds for M6 NEEDS_REVIEW results."""
from __future__ import annotations

import re
from collections.abc import Mapping

from .errors import SchedulerError
from .states import AttemptState as A, TaskState as T
from .transitions import Ctx, end_attempt, set_task

_RESULT = re.compile(r"m6://result/[0-9a-f]{64}")
_ADVICE = {"resume", "wait", "block"}


def record_needs_review_hold(ctx: Ctx, *, plan_id: str, revision: int, task_id: str, attempt_id: str,
                             token: int, evidence_ref: str) -> Mapping[str, object] | None:
    """Persist and return the exact M6 case. `None` means an identical result was already applied."""
    state = ctx.state
    if ((plan_id, revision) != (state.plan_id, state.revision) or task_id not in state.tasks or
            not isinstance(evidence_ref, str) or _RESULT.fullmatch(evidence_ref) is None or
            type(token) is not int or token < 1):
        raise SchedulerError("CONTRACT_VIOLATION", "NEEDS_REVIEW identity is malformed or stale")
    attempt = state.attempts.get(attempt_id)
    if (attempt is None or attempt.task_id != task_id or attempt.token != token or
            state.tasks[task_id].attempts[-1:] != [attempt_id] or attempt.state != A.VERIFYING.value or
            state.tasks[task_id].state != T.ACTIVE.value):
        raise SchedulerError("NOT_ALLOWED", "NEEDS_REVIEW must name the current verifying M1 attempt")
    identity = {"plan_id": plan_id, "revision": revision, "task_id": task_id, "attempt_id": attempt_id,
                "token": token, "evidence_ref": evidence_ref}
    previous = state.review_holds.get(attempt_id)
    if previous and previous["evidence_ref"] == evidence_ref and previous["state"] in {"resumed", "blocked"}:
        return None
    if previous and any(previous[key] != identity[key] for key in identity if key != "evidence_ref"):
        raise SchedulerError("NOT_ALLOWED", "NEEDS_REVIEW attempt identity changed")
    state.review_holds[attempt_id] = {**identity, "state": "held", "advice": ""}
    ctx.audit("needs_review_held", task_id, attempt_id, evidence_ref=evidence_ref)
    return identity


def apply_needs_review_advice(ctx: Ctx, identity: Mapping[str, object], advice: str) -> str:
    """Apply M5 advice after its port has returned, revalidating the held identity in M1."""
    attempt_id, task_id = identity["attempt_id"], identity["task_id"]
    evidence_ref = identity["evidence_ref"]
    state = ctx.state
    hold = state.review_holds.get(attempt_id)
    attempt = state.attempts.get(attempt_id)
    if (hold is None or attempt is None or any(hold.get(key) != value for key, value in identity.items()) or
            attempt.task_id != task_id or attempt.token != identity["token"] or
            attempt.state != A.VERIFYING.value or state.tasks[task_id].state != T.ACTIVE.value):
        raise SchedulerError("NOT_ALLOWED", "NEEDS_REVIEW hold changed while M5 advice was pending")
    if advice not in _ADVICE:
        raise SchedulerError("CONTRACT_VIOLATION", "M5 NEEDS_REVIEW advice must be resume, wait, or block")
    hold["advice"] = advice
    if advice == "wait":
        hold["state"] = "waiting"
        ctx.audit("needs_review_waiting", task_id, attempt_id, evidence_ref=evidence_ref)
        return "waiting"
    if advice == "resume":
        hold["state"] = "resumed"
        ctx.audit("needs_review_resumed", task_id, attempt_id, evidence_ref=evidence_ref)
        return "resumed"
    end_attempt(ctx, attempt_id, A.FAILED, "needs_review_blocked", "M5 blocked unresolved M6 review")
    set_task(ctx, task_id, T.BLOCKED, reason="needs_review_blocked", evidence_ref=evidence_ref)
    hold["state"] = "blocked"
    ctx.audit("needs_review_blocked", task_id, attempt_id, evidence_ref=evidence_ref)
    return "blocked"


def handle_on_scheduler(scheduler, *, plan_id: str, revision: int, task_id: str, attempt_id: str,
                        token: int, evidence_ref: str, advice_port) -> str:
    identity = scheduler.write(lambda ctx: record_needs_review_hold(
        ctx, plan_id=plan_id, revision=revision, task_id=task_id, attempt_id=attempt_id,
        token=token, evidence_ref=evidence_ref))
    if identity is None:
        return scheduler.read(lambda ctx: ctx.state.review_holds[attempt_id]["state"])
    advice = advice_port(identity)
    result = scheduler.write(lambda ctx: apply_needs_review_advice(ctx, identity, advice))
    scheduler._wake.set()
    return result


def block_exhausted_resume(ctx: Ctx, identity: Mapping[str, object]) -> str:
    """End an M1 review hold after M6 reports that its one same-attempt resume was consumed."""
    attempt_id, task_id = identity.get("attempt_id"), identity.get("task_id")
    hold = ctx.state.review_holds.get(attempt_id)
    attempt = ctx.state.attempts.get(attempt_id)
    if (not isinstance(attempt_id, str) or not isinstance(task_id, str) or task_id not in ctx.state.tasks or
            hold is None or attempt is None or any(
            hold.get(key) != identity.get(key) for key in ("plan_id", "revision", "task_id", "attempt_id", "token")
            ) or
            hold.get("state") != "resumed" or attempt.task_id != task_id or
            attempt.state != A.VERIFYING.value or ctx.state.tasks[task_id].state != T.ACTIVE.value):
        raise SchedulerError("NOT_ALLOWED", "M6 resume exhaustion does not match a resumed M1 review hold")
    end_attempt(ctx, attempt_id, A.FAILED, "needs_review_retry_exhausted", "M6 same-attempt resume exhausted")
    set_task(ctx, task_id, T.BLOCKED, reason="needs_review_retry_exhausted", evidence_ref=hold["evidence_ref"])
    hold["state"] = "blocked"
    hold["advice"] = "block"
    ctx.audit("needs_review_retry_exhausted", task_id, attempt_id)
    return "blocked"
