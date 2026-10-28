"""Recovery policy (REQ-030 M5): what the durable runtime does after a classified failure, within hard limits.

The policy is a pure function of the failure, what the task already spent and the budget, so a recovered workflow
replays the same decision. Principles it encodes:

- an infrastructure or environment failure never costs an agent attempt when it can be retried or repaired without
  one (re-verify the same snapshot, wait for capacity);
- the same failure twice is not progress: the second repetition becomes a coordinated remediation, then the owner;
- permissions, missing secrets and product decisions always go to the owner; nothing is bypassed;
- every path is bounded (attempts, same signature, elapsed time, tokens, waits, route changes, repairs).
"""
from __future__ import annotations

from collections.abc import Iterable

from bt_contracts.execution import AttemptOutcome
from bt_contracts.failure import (
    Budget,
    FailureClass,
    FailureReport,
    RecoveryAction,
    RecoveryDecision,
    Spent,
)

TRANSIENT_BACKOFF = (30.0, 120.0, 600.0, 1800.0)
QUOTA_COOLDOWN = 1800.0            # bt_config quota.default_cooldown_min when the provider gives no reset time
REPAIRABLE_ENVIRONMENT = frozenset({"VERIFIER_OOM", "AGENT_OOM", "CHECK_TIMEOUT"})
REVERIFY = frozenset({"VERIFIER_OOM", "CHECK_TIMEOUT", "FLAKY_SUSPECTED"})   # same snapshot, no new agent run


def spent(outcomes: Iterable[AttemptOutcome], *, waits: int = 0, repairs: int = 0, route_changes: int = 0,
          started_at: float | None = None, now: float | None = None) -> Spent:
    """What a task consumed, derived from its attempt outcomes (the only source; nothing is counted by hand)."""
    attempts = tokens = regressions = 0
    signatures: dict[str, int] = {}
    passed: set[str] = set()
    for outcome in outcomes:
        if outcome.process is not None:
            attempts += 1
        if outcome.agent and outcome.agent.total_tokens:
            tokens += outcome.agent.total_tokens
        if outcome.failure is not None:
            signatures[outcome.failure.signature] = signatures.get(outcome.failure.signature, 0) + 1
        if outcome.verify is not None:
            failing = set(outcome.verify.failing_checks)
            regressions = regressions + 1 if failing & passed else 0
            passed |= set(outcome.verify.passing_checks)
    elapsed = max(0.0, (now - started_at)) if started_at is not None and now is not None else 0.0
    return Spent(attempts=attempts, elapsed_seconds=elapsed, tokens=tokens, route_changes=route_changes,
                 environment_repairs=repairs, waits=waits, signatures=signatures,
                 consecutive_regressions=regressions)


def decide(failure: FailureReport, used: Spent, budget: Budget, *, now: float, other_route: bool,
           reset_epoch: float | None = None, remediated: bool = False) -> RecoveryDecision:
    def make(action: RecoveryAction, reason: str, *, not_before: float | None = None, note: str = "",
             limit: str = "") -> RecoveryDecision:
        return RecoveryDecision(action=action, reason=reason[:500], failure=failure, not_before=not_before,
                                note_for_agent=(note or failure.agent_note)[:6000], spent=used, limit_hit=limit)

    cls = failure.failure_class
    if cls in (FailureClass.PERMISSION, FailureClass.PRODUCT_DECISION):
        return make(RecoveryAction.ESCALATE, f"{cls.value}: {failure.summary}")
    if cls == FailureClass.INTERNAL:
        return make(RecoveryAction.STOP, f"runtime defect, not retried blindly: {failure.summary}")
    if cls == FailureClass.CONTRACT:
        return make(RecoveryAction.ESCALATE, f"the plan or order data is invalid: {failure.summary}")
    if used.elapsed_seconds >= budget.max_elapsed_seconds:
        return make(RecoveryAction.ESCALATE, "the task used its time budget", limit="max_elapsed_seconds")
    if budget.max_tokens is not None and used.tokens >= budget.max_tokens:
        return make(RecoveryAction.ESCALATE, "the task used its token budget", limit="max_tokens")
    if cls == FailureClass.QUOTA:
        if other_route and used.route_changes < budget.max_route_changes:
            return make(RecoveryAction.RETRY_OTHER_ROUTE, "the route has no capacity; another allowed route has")
        if used.waits >= budget.max_waits:
            return make(RecoveryAction.ESCALATE, "no capacity after the allowed waits", limit="max_waits")
        until = reset_epoch if reset_epoch and reset_epoch > now else now + QUOTA_COOLDOWN
        why = "until the provider's reset" if reset_epoch and reset_epoch > now else "cooldown (reset time unknown)"
        return make(RecoveryAction.WAIT, f"waiting for capacity {why}", not_before=until)
    repeats = used.signatures.get(failure.signature, 0)
    if cls == FailureClass.TRANSIENT:
        if repeats > len(TRANSIENT_BACKOFF) or used.waits >= budget.max_waits:
            return make(RecoveryAction.ESCALATE, "the transient failure keeps coming back", limit="max_waits")
        delay = TRANSIENT_BACKOFF[min(max(repeats - 1, 0), len(TRANSIENT_BACKOFF) - 1)]
        return make(RecoveryAction.WAIT, f"transient failure, retry after {int(delay)} s", not_before=now + delay)
    if cls in (FailureClass.ENVIRONMENT, FailureClass.VERIFICATION):
        if failure.code in REPAIRABLE_ENVIRONMENT | REVERIFY and used.environment_repairs < budget.max_environment_repairs:
            return make(RecoveryAction.REPAIR_ENVIRONMENT, f"bounded environment repair for {failure.code}")
        return make(RecoveryAction.ESCALATE, f"environment needs the owner: {failure.summary}",
                    limit="max_environment_repairs" if failure.code in REPAIRABLE_ENVIRONMENT | REVERIFY else "")
    if cls == FailureClass.INTEGRATION:
        if repeats < budget.max_same_signature:
            return make(RecoveryAction.RECONCILE_INTEGRATION, "rebuild on the current integration line")
        return make(RecoveryAction.ESCALATE, "the integration conflict keeps coming back", limit="max_same_signature")
    # implementation
    if used.attempts >= budget.max_attempts:
        return make(RecoveryAction.ESCALATE, "the task used its attempts", limit="max_attempts")
    if used.consecutive_regressions >= budget.max_consecutive_regressions:
        return make(RecoveryAction.ESCALATE, "attempts keep breaking checks that passed before",
                    limit="max_consecutive_regressions")
    if repeats >= budget.max_same_signature:
        if not remediated:
            return make(RecoveryAction.REMEDIATE, "the same failure repeated: one coordinated repair with the probes")
        return make(RecoveryAction.ESCALATE, "the same failure survived a coordinated repair", limit="max_same_signature")
    return make(RecoveryAction.RETRY, "the checks failed; retry from the last snapshot with the decisive lines")
