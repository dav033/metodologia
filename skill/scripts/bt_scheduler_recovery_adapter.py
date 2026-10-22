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
                 diagnostic_pipeline: Callable[[Mapping[str, object]], Mapping[str, object]] | None = None):
        self.scheduler, self.run_id, self.describe = scheduler, run_id, describe
        self.policy = m5.Policy(**dict(policy or {}))
        self.path = Path(path)
        self.rdir = Path(rdir) if rdir is not None else None
        self.recovery_sources = recovery_sources
        self.diagnostic_pipeline = diagnostic_pipeline
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
        def read(ctx):
            task = ctx.state.tasks.get(context.task_id)
            attempt = ctx.state.attempts.get(context.attempt_id)
            if task is None or attempt is None:
                return None
            used = len(task.attempts) - task.budget_base
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
        values = {k: v for k, v in official.items() if k not in {"evidence", "verifier", "failure"}}
        values["manual_cancel"] = official["manual_cancel"] or verified and facts.get("cancel_requested") is True
        return m5.RecoveryCase(
            **values, run_id=self.run_id, core_cause=context.cause,
            technical_cause=cause, confidence="reported" if verified else "unknown", evidence_refs=refs,
            handoff_sha=sha, execution_state=state, identity_verified=verified,
            transient_confirmed=verified and cause in {"connection_lost", "timeout", "incomplete_output"},
            verification_ref=verification_ref, reset_epoch=reset,
        )

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
            started = re.match(r"start rejected: ([A-Z][A-Z_]+)", str(official.get("failure") or ""))
            if not facts and started:
                # the scheduler itself refused to start the attempt (an integration clash, a predecessor that is not accepted...): the
                # executor never had a record BY DESIGN, and the evidence is the scheduler's own. It was filed as `identity_unverified`
                # (an integrity anomaly nobody answers for): 39 of its 44 real blocks were these, and a person had to look at each one
                return sched.core.RecoveryProposal("block", f"m5:start_rejected_{started.group(1).lower()}")
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
        return sched.core.RecoveryProposal(decision.action, f"m5:{decision.reason_code}", decision.wait_seconds)

    def latest(self):
        return self._open().latest(run_id=self.run_id)

    def metrics(self):
        return self._open().metrics()

    def close(self):
        if self.store is not None:
            self.store.close()
            self.store = None


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
