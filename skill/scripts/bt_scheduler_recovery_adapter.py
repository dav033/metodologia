"""M5 RecoveryPort boundary: read official evidence, persist advice, return the unchanged M1 contract.

Only this methodology module imports the isolated recovery package. No free-form failure detail, provider output,
profile configuration or filesystem path is copied into its ledger. Source readers are supplied by the executor wiring.
"""
from __future__ import annotations

import hashlib
import re
import json
import logging
import math
from collections.abc import Callable, Mapping
from pathlib import Path

from bt_scheduler_recovery_lifecycle import DiagnosticRecoveryLifecycle, read_cycle_status

import bt_scheduler_adapter as sched
import bt_scheduler_recovery as m5
from bt_scheduler_recovery.conflict_contracts import ConflictObservation
from bt_scheduler_recovery.conflict_delivery import (EvidenceUnavailable, integration_problem,
                                                     refusal_detail, publish_or_raise, start_rejection_detail)

SCHEMA = "m5.executor-facts/1"
M6_MANIFEST_SCHEMAS = frozenset({"m6.evidence-manifest/1", "m6.evidence-manifest/1.1"})
M6_REASONS = frozenset({"PASS", "FAIL_CODE", "BLOCKED_EXTERNAL", "BLOCKED_ENV", "TIMEOUT",
                        "FLAKY_SUSPECTED", "NOT_RUN"})
ACTIONABLE_NOTICES = {
    "m6_blocked_external_owner_must_restore_dependency":
        "M6 is blocked on an external dependency; restore the declared dependency and rerun verification.",
    "m6_blocked_env_operator_must_repair_environment":
        "M6 is blocked on its environment; repair the verifier environment and rerun verification.",
    "flaky_requires_m6_rerun_policy":
        "M6 marked the evidence flaky; use M6's configured check rerun policy and do not accept this pass.",
    "m6_not_run": "M6 did not run verification; resolve the blocker and request verification again.",
    "m6_pass_not_recovery": "M6 PASS is not a recovery action; only M6 may decide acceptance.",
}
CAUSES = frozenset({"quota_exhausted", "connection_lost", "agent_error", "timeout", "killed", "incomplete_output",
                    "start_failed", "lost", "artifact_error", "cancelled", "clean"})


def opaque_ref(kind: str, value: object) -> str:
    digest = hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                       ensure_ascii=True, allow_nan=False).encode()).hexdigest()
    return f"{kind}:{digest}"


class RecoveryAdapter(DiagnosticRecoveryLifecycle):
    """Advice only. Source or persistence failures block visibly rather than letting absent evidence authorize retry."""

    def __init__(self, path: Path | str, *, scheduler, run_id: str,
                 describe: Callable[[str], Mapping[str, object] | None], policy: Mapping[str, object] | None = None,
                 rdir: Path | str | None = None, recovery_sources: Callable[[], Mapping[str, object]] | None = None,
                 diagnostic_pipeline: Callable[[Mapping[str, object]], Mapping[str, object]] | None = None,
                 m6_evidence_reader: Callable[[str], bytes | None] | None = None,
                 composition_propagation: Callable[[str], Mapping[str, object] | None] | None = None):
        self.scheduler, self.run_id, self.describe = scheduler, run_id, describe
        self.policy = m5.Policy(**dict(policy or {}))
        self.path = Path(path)
        self.rdir = Path(rdir) if rdir is not None else None
        self.recovery_sources = recovery_sources
        self.diagnostic_pipeline = diagnostic_pipeline
        self.m6_evidence_reader = m6_evidence_reader
        self.composition_propagation = composition_propagation
        self.store = None

    def _validate_conflict_observation(self, observation):
        validate_conflict_observation(observation)

    def _parse_conflict_observation(self, observation):
        return parse_conflict_observation(observation)

    def _open(self):
        if self.store is None:
            self.store = m5.DecisionStore(self.path, max_decisions=self.policy.max_decisions)
        return self.store

    def _official(self, context):
        used = self.scheduler.attempts_used(context.task_id)
        def read(ctx):
            task = ctx.state.tasks.get(context.task_id)
            attempt = ctx.state.attempts.get(context.attempt_id)
            if task is None or attempt is None:
                return None
            current = ((context.plan_id, context.cause, context.attempts_used, context.max_attempts) ==
                       (ctx.state.plan_id, task.reason, used, ctx.config.max_attempts)
                       and task.attempts[-1:] == [context.attempt_id] and attempt.task_id == context.task_id
                       and task.state == "recovering" and attempt.state in ("failed", "rejected"))
            return {"plan_id": ctx.state.plan_id, "revision": ctx.state.revision,
                    "plan_sha256": ctx.state.plan_sha256, "task_id": context.task_id, "attempt_id": attempt.id,
                    "token": attempt.token, "current": current, "manual_cancel": ctx.state.cancel_requested,
                    "attempts_used": used, "max_attempts": ctx.config.max_attempts, "recovery_round": task.waits,
                    "max_waits": ctx.config.max_recovery_waits, "max_wait_seconds": ctx.config.max_recovery_wait,
                    "failure_at": attempt.updated_at, "now": ctx.now, "evidence": attempt.evidence,
                    "verifier": attempt.verifier, "failure": attempt.failure}
        return self.scheduler.read(read)

    def _case(self, context, official, facts):
        request = facts.get("request", {})
        identity = ("plan_id", "plan_sha256", "revision", "task_id", "attempt_id", "token")
        verified = (facts.get("schema_version") == SCHEMA and isinstance(request, Mapping)
                    and all(type(request.get(k)) is type(official[k]) and request.get(k) == official[k] for k in identity))
        state = facts.get("state", "unknown") if verified else "unknown"
        state = state if state in {"failed", "finished", "cancelled"} else "live" if state in {
            "running", "queued", "preparing", "settling"} else "unknown"
        outcome = facts.get("outcome")
        outcome = outcome if verified and isinstance(outcome, Mapping) else {}
        cause = outcome.get("cause", "unknown")
        cause = cause if isinstance(cause, str) and cause in CAUSES else "unknown"
        handoff = facts.get("handoff")
        handoff = handoff if isinstance(handoff, Mapping) else {}
        sha = handoff.get("snapshot_sha") if verified and handoff.get("status") == "captured" \
            and facts.get("snapshot_verified") is True else None
        reset = outcome.get("reset_epoch")
        if type(reset) not in (int, float) or not math.isfinite(reset) or reset < 0:
            reset = None
        verification_ref = opaque_ref("verdict", official["evidence"]) if official["evidence"] \
            and official["verifier"] and context.cause == "verification_rejected" else None
        if context.cause == "verification_rejected":
            cause = "verification_rejected"
        refs = (opaque_ref("attempt", {k: official[k] for k in identity}),)
        if verified:
            refs += (opaque_ref("outcome", {"cause": cause, "state": state, "reset_epoch": reset}),)
        if verification_ref:
            refs += (verification_ref,)
        reason_code = self._m6_reason(official, facts, verified)
        values = {k: v for k, v in official.items() if k not in {"evidence", "verifier", "failure"}}
        # M5's historical case contract requires at least one observed attempt. A start refused before
        # M3 execution is represented as the current failed attempt; M1's code-retry counter remains zero.
        values["attempts_used"] = max(1, int(official["attempts_used"]))
        values["manual_cancel"] = official["manual_cancel"] or verified and facts.get("cancel_requested") is True
        return m5.RecoveryCase(
            **values, run_id=self.run_id, core_cause=context.cause,
            technical_cause=cause, confidence="reported" if verified else "unknown", evidence_refs=refs,
            handoff_sha=sha, execution_state=state, identity_verified=verified,
            transient_confirmed=verified and cause in {"connection_lost", "timeout", "incomplete_output"},
            verification_ref=verification_ref, reset_epoch=reset, reason_code=reason_code,
        )

    def _m6_reason(self, official, facts, executor_identity_verified):
        reference = official.get("evidence")
        if self.m6_evidence_reader is None or not isinstance(reference, str) or not reference.startswith("m6://result/"):
            return "UNCLASSIFIED"
        if not executor_identity_verified:
            raise ValueError("M6 evidence has no verified executor handoff")
        digest = reference.removeprefix("m6://result/")
        if re.fullmatch(r"[a-f0-9]{64}", digest) is None:
            raise ValueError("M6 evidence reference is invalid")
        encoded = self.m6_evidence_reader(reference)
        if not isinstance(encoded, bytes) or len(encoded) > 1024 * 1024:
            raise ValueError("M6 persisted evidence exceeds the 1 MiB size limit")
        if hashlib.sha256(encoded).hexdigest() != digest:
            raise ValueError("M6 persisted evidence is unavailable or has a mismatched digest")
        manifest = json.loads(encoded)
        if not isinstance(manifest, Mapping) or manifest.get("schema_version") not in M6_MANIFEST_SCHEMAS:
            raise ValueError("M6 persisted evidence schema is unsupported")
        request = manifest.get("request")
        evidence_input = manifest.get("input")
        handoff = facts.get("handoff") if isinstance(facts, Mapping) else None
        expected = {"plan_id": official.get("plan_id"), "revision": official.get("revision"),
                    "task_id": official.get("task_id"), "attempt_id": official.get("attempt_id"),
                    "token": official.get("token")}
        if (not isinstance(request, Mapping)
                or any(type(request.get(key)) is not type(value) or request.get(key) != value
                       for key, value in expected.items())
                or not isinstance(evidence_input, Mapping)
                or not isinstance(handoff, Mapping)):
            raise ValueError("M6 evidence identity or snapshot is stale")
        reason = manifest.get("reason_code")
        if reason not in M6_REASONS:
            return "UNCLASSIFIED"
        if (handoff.get("status") != "captured"
                or evidence_input.get("snapshot_sha") != handoff.get("snapshot_sha")
                or facts.get("snapshot_verified") is not True):
            raise ValueError("M6 evidence snapshot is stale")
        tree = evidence_input.get("tree_digest")
        if not isinstance(tree, str) or re.fullmatch(r"[a-f0-9]{40}|[a-f0-9]{64}", tree) is None:
            raise ValueError("M6 evidence tree identity is invalid")
        facts_tree = facts.get("tree_digest")
        if facts_tree is None:
            facts_tree = handoff.get("tree_digest")
        if facts_tree is not None and (not isinstance(facts_tree, str)
                or re.fullmatch(r"[a-f0-9]{40}|[a-f0-9]{64}", facts_tree) is None
                or tree != facts_tree):
            raise ValueError("M6 evidence tree identity is stale")
        checks = manifest.get("checks")
        if not isinstance(checks, list):
            raise ValueError("M6 evidence checks are invalid")
        for check in checks:
            if not isinstance(check, Mapping):
                raise ValueError("M6 evidence check is invalid")
            check_tree = check.get("tree_digest")
            if check_tree is not None and (not isinstance(check_tree, str)
                    or re.fullmatch(r"[a-f0-9]{40}|[a-f0-9]{64}", check_tree) is None):
                raise ValueError("M6 evidence check tree identity is invalid")
            if facts_tree is not None and check_tree is not None and check_tree != facts_tree:
                raise ValueError("M6 evidence check tree identity is stale")
        return reason

    def propose(self, context):
        try:
            official = self._official(context)
            if official is None or not official["current"] or official["manual_cancel"]:
                return sched.core.RecoveryProposal("block", "m5_stale_or_cancelled")
            if context.cause == "verification_rejected" and str(official.get("evidence", "")).startswith(
                    "verification_replan/blocked:"):
                return sched.core.RecoveryProposal("block", "verification_replan_blocked")
            facts = self.describe(context.attempt_id) or {}
            if not isinstance(facts, Mapping):
                raise TypeError("invalid evidence object")
            started = re.match(r"(start|verify) rejected: ([A-Z][A-Z_]+)", str(official.get("failure") or ""))
            if started and (started.group(1) == "verify" or not facts):
                # the scheduler itself refused to start the attempt, or the verifier refused its order: a fact of its own records, not an
                # integrity anomaly. A start rejection never had an executor record by design (39 of 44 real `identity_unverified` blocks);
                # a refused order is sent again unchanged by a retry, so it blocks with its code and the snapshot waits for `continue-from`
                return sched.core.RecoveryProposal("block", f"m5:{started.group(1)}_rejected_{started.group(2).lower()}")
            case = self._case(context, official, facts)
            decision = self._open().decide(case, self.policy)
        except Exception as error:  # noqa: BLE001 - a broken recovery store must not enable the core retry fallback
            try:
                self.scheduler.record("recovery_unavailable", task_id=context.task_id, attempt_id=context.attempt_id,
                                      source="m5", error=type(error).__name__)
            except Exception as audit_error:  # noqa: BLE001 - audit outage must not turn missing evidence into retry
                logging.getLogger(__name__).error("M5 evidence/history unavailable (%s); audit unavailable (%s)",
                                                  type(error).__name__, type(audit_error).__name__)
            return sched.core.RecoveryProposal("block", "m5_evidence_or_history_unavailable")
        reason = f"m5:{decision.reason_code}"
        if decision.reason_code in ACTIONABLE_NOTICES:
            reason += f"; {ACTIONABLE_NOTICES[decision.reason_code]}"
        return sched.core.RecoveryProposal(decision.action, reason, decision.wait_seconds)

    def latest(self):
        return self._open().latest(run_id=self.run_id)

    def metrics(self):
        return self._open().metrics()

    def close(self):
        if self.store is not None:
            self.store.close()
            self.store = None

    def demonstrated_frontier(self, change_id: str):
        """Read only the explicit composition frontier; M5 never derives descendants from ancestry."""
        if self.composition_propagation is None:
            raise m5.RecoveryError("PROPAGATION_UNAVAILABLE")
        if not isinstance(change_id, str) or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}", change_id) is None:
            raise m5.RecoveryError("INVALID_INPUT")
        raw = self.composition_propagation(change_id)
        advice = m5.DemonstratedFrontier.from_dict(raw)
        if advice.change_id != change_id:
            raise m5.RecoveryError("PROPAGATION_STALE")
        task_ids = self.scheduler.snapshot().tasks.keys()
        if advice.source_task_id not in task_ids or advice.source_task_id in advice.frontier \
                or any(task_id not in task_ids for task_id in advice.frontier):
            raise m5.RecoveryError("PROPAGATION_STALE")
        return advice

    def needs_review_advice(self, case: Mapping[str, object]) -> str:
        """Classify one persisted M6 NEEDS_REVIEW result; missing or stale evidence blocks closed."""
        if self.m6_evidence_reader is None or not isinstance(case, Mapping):
            raise m5.RecoveryError("M6_EVIDENCE_UNAVAILABLE")
        reference = case.get("evidence_ref")
        if not isinstance(reference, str) or re.fullmatch(r"m6://result/[0-9a-f]{64}", reference) is None:
            raise m5.RecoveryError("M6_EVIDENCE_INVALID")
        encoded = self.m6_evidence_reader(reference)
        digest = reference.removeprefix("m6://result/")
        if not isinstance(encoded, bytes) or len(encoded) > 1024 * 1024 or hashlib.sha256(encoded).hexdigest() != digest:
            raise m5.RecoveryError("M6_EVIDENCE_INVALID")
        manifest = json.loads(encoded)
        expected = {key: case.get(key) for key in ("plan_id", "revision", "task_id", "attempt_id", "token")}
        request = manifest.get("request") if isinstance(manifest, Mapping) else None
        if (not isinstance(manifest, Mapping) or manifest.get("schema_version") not in M6_MANIFEST_SCHEMAS or
                not isinstance(request, Mapping) or not all(
                type(request.get(key)) is type(value) and request.get(key) == value
                for key, value in expected.items())):
            raise m5.RecoveryError("M6_EVIDENCE_STALE")
        checks = manifest.get("checks", [])
        issues = manifest.get("issues", [])
        codes = {item.get("reason_code") or item.get("issue_code") or item.get("code")
                 for item in (*checks, *issues) if isinstance(item, Mapping)} if isinstance(checks, list) and isinstance(issues, list) else set()
        top_reason = manifest.get("reason_code")
        if top_reason not in M6_REASONS or top_reason == "PASS":
            raise m5.RecoveryError("M6_RESULT_NOT_NEEDS_REVIEW")
        codes.add(top_reason)
        if codes & {"TIMEOUT", "FLAKY_SUSPECTED", "CHECK_TIMEOUT"}:
            return "resume"
        if codes & {"BLOCKED_ENV", "BLOCKED_EXTERNAL", "NOT_RUN", "CHECK_MANUAL", "CHECK_UNAVAILABLE",
                    "SANDBOX_UNAVAILABLE", "CHECK_UNSUPPORTED"}:
            return "wait"
        return "block"


def inspect_store(path: Path | str, *, metrics: bool = False):
    """Operational reads use the module's read-only API; they never create an empty store."""
    return m5.inspect_store(path, metrics=metrics)



def validate_conflict_observation(observation: Mapping[str, object]) -> None:
    """Validate a plain conflict observation through the sole M5 package boundary."""
    ConflictObservation.from_dict(dict(observation))


def parse_verification_map(value: object):
    """Parse the shared M5 verification-map/1 contract without leaking its package boundary."""
    return m5.VerificationMap.from_dict(value)


def parse_conflict_observation(value: Mapping[str, object]):
    """Parse the T3a conflict envelope at the sole M5 package boundary."""
    return ConflictObservation.from_dict(dict(value))
