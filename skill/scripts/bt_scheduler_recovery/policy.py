"""Pure, deterministic recovery recommendations. M1 alone applies them."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict

from .contracts import HistorySummary, Policy, RecoveryCase, RecoveryDecision
from .validation import require

DEFAULT_POLICY = Policy()
EMPTY_HISTORY = HistorySummary()


def logical_key(case: RecoveryCase, policy: Policy) -> str:
    identity = {key: getattr(case, key) for key in (
        "run_id", "plan_id", "revision", "plan_sha256", "task_id", "attempt_id", "token", "recovery_round")}
    if case.reason_code != "UNCLASSIFIED":
        identity["reason_code"] = case.reason_code
    encoded = json.dumps({"identity": identity, "policy": asdict(policy)}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


def propose(case: RecoveryCase, policy: Policy = DEFAULT_POLICY,
            history: HistorySummary = EMPTY_HISTORY) -> RecoveryDecision:
    require(type(case) is RecoveryCase and type(policy) is Policy and type(history) is HistorySummary)
    remaining = max(0, case.max_attempts - case.attempts_used)
    waits = max(0, case.max_waits - case.recovery_round)

    def decision(action: str, reason: str, *, cooldown: float | None = None,
                 route: str | None = None) -> RecoveryDecision:
        wait = max(1.0, cooldown - case.now) if action == "wait" else 0.0
        return RecoveryDecision(logical_key(case, policy), action, reason, case.evidence_refs, case.confidence,
                                policy.version, wait, remaining, route, action == "block", cooldown,
                                max(0, waits - (action == "wait")))

    def block(reason: str) -> RecoveryDecision:
        return decision("block", reason)

    def deferred(until: float, reason: str, route: str) -> RecoveryDecision:
        if until <= case.now:
            return decision("retry", reason + "_ready", cooldown=until, route=route)
        if waits <= 0:
            return block("wait_limit")
        if max(1.0, until - case.now) > case.max_wait_seconds:
            return block("wait_window_exceeded")
        if until - case.failure_at > policy.max_elapsed_seconds:
            return block("elapsed_limit")
        return decision("wait", reason + "_cooldown", cooldown=until, route=route)

    if case.manual_cancel or case.execution_state == "cancelled" or case.technical_cause == "cancelled":
        return block("manual_cancel")
    if not case.current or not case.identity_verified:
        return block("identity_unverified")
    if case.execution_state in ("live", "unknown") or case.core_cause == "lost":
        return block("execution_unsettled")
    if case.failure_at > case.now:
        return block("evidence_from_future")
    if case.now - case.failure_at > policy.evidence_max_age_seconds:
        return block("evidence_stale")
    if not case.evidence_refs or case.confidence not in ("confirmed", "reported"):
        return block("evidence_insufficient")
    reason = case.reason_code
    if reason == "BLOCKED_EXTERNAL":
        return block("m6_blocked_external_owner_must_restore_dependency")
    if reason == "BLOCKED_ENV":
        return block("m6_blocked_env_operator_must_repair_environment")
    if reason == "FLAKY_SUSPECTED":
        return block("flaky_requires_m6_rerun_policy")
    if reason == "NOT_RUN":
        return block("m6_not_run")
    if reason == "PASS":
        return block("m6_pass_not_recovery")
    if remaining <= 0:
        return block("attempts_exhausted")
    if history.decisions >= policy.max_decisions:
        return block("decision_limit")
    if case.now - case.failure_at > policy.max_elapsed_seconds:
        return block("elapsed_limit")
    if history.same_cause_attempts >= policy.max_same_cause:
        return block("same_cause_limit")
    cause = case.technical_cause
    if reason == "TIMEOUT" and case.core_cause == "verification_rejected":
        if case.verification_ref is None:
            return block("verification_evidence_missing")
        if case.execution_state != "finished":
            return block("cause_state_mismatch")
        if case.handoff_sha is None:
            return block("handoff_missing")
        if history.timeout_decisions >= 1:
            return block("timeout_repeated")
        return decision("retry", "verification_rejected", route="same_route")
    if case.core_cause == "verification_rejected" or cause == "verification_rejected":
        if case.core_cause != "verification_rejected" or case.verification_ref is None:
            return block("verification_evidence_missing")
        if case.execution_state != "finished":
            return block("cause_state_mismatch")
        if case.handoff_sha is None:
            return block("handoff_missing")
        return decision("retry", "verification_rejected", route="same_route")
    if cause in ("artifact_error", "start_failed", "integration_conflict", "predecessor_missing",
                 "killed", "lost", "clean", "cancelled", "unknown"):
        return block("permanent_or_unknown_cause")
    if case.handoff_sha is None:
        return block("handoff_missing")
    if case.execution_state != "failed":
        return block("cause_state_mismatch")
    if cause == "quota_exhausted":
        if case.reset_epoch is None:
            return block("quota_reset_unknown")
        return deferred(case.reset_epoch + policy.reset_margin_seconds, "quota_reset", "reevaluate")
    if cause in ("connection_lost", "incomplete_output", "agent_error", "timeout"):
        if not case.transient_confirmed:
            return block("transience_unconfirmed")
        if cause == "timeout" and history.same_cause_attempts >= 1:
            return block("timeout_repeated")
        delay = min(policy.max_backoff_seconds,
                    policy.base_backoff_seconds * 2 ** min(history.same_cause_attempts, 30))
        return deferred(case.failure_at + delay, "transient", "same_route")
    return block("permanent_or_unknown_cause")
