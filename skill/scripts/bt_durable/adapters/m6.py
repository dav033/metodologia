"""Verifier port over the legacy M6 engine (CONSERVAR): sandboxed checks, evidence manifests, pass cache.

The durable runtime calls `QualityEngine.verify` directly from a DBOS step; M6's own request table makes a repeated
step return the stored verdict instead of running the checks twice. M6's outbox and its M1 delivery are not used:
the step result is the delivery. The failure digest the agent reads is the shared one (`quality_delivery`).

Profiles: `standard` is the operator's policy; `relaxed` is the bounded environment repair the recovery policy may
ask for once (more time, more workspace, a larger Node heap) — it never changes a command or a criterion.
"""
from __future__ import annotations

import dataclasses
from pathlib import Path
from types import SimpleNamespace

from bt_contracts.execution import AttemptRef, Prepared, Snapshot, VerifyOutcome, VerifyStatus
from bt_scheduler_core.plan import TaskSpec
from bt_scheduler_quality.engine import QualityEngine
from bt_scheduler_quality.policy import QualityPolicy
from bt_scheduler_quality.snapshot import SnapshotSource
from bt_scheduler_quality.store import QualityStore

RELAXED_NODE_HEAP_MB = 6144


def relaxed(policy: QualityPolicy) -> QualityPolicy:
    env = dict(policy.environment)
    if "NODE_OPTIONS" not in env:
        env["NODE_OPTIONS"] = f"--max-old-space-size={RELAXED_NODE_HEAP_MB}"
    return dataclasses.replace(
        policy,
        max_command_seconds=min(policy.max_command_seconds * 2, 3 * 3600),
        max_total_seconds=min(policy.max_total_seconds * 2, 4 * 3600),
        max_workspace_bytes=min(policy.max_workspace_bytes * 2, 8 << 30),
        max_tmp_bytes=min(policy.max_tmp_bytes * 2, 8 << 30),
        environment=tuple(sorted(env.items())),
        rerun_failed_checks=max(policy.rerun_failed_checks, 1),
    )


class M6Verifier:
    def __init__(self, *, store_path: Path, policy: QualityPolicy | None = None, authority=None, attestations=None):
        self.store = QualityStore(Path(store_path))
        self.policy = policy or QualityPolicy()
        self.authority = authority
        self.attestations = attestations
        self._engines: dict[str, QualityEngine] = {}

    def _engine(self, profile: str) -> QualityEngine:
        if profile not in self._engines:
            policy = relaxed(self.policy) if profile == "relaxed" else self.policy
            self._engines[profile] = QualityEngine(policy, self.store, verification_authority=self.authority,
                                                   attestations=self.attestations)
        return self._engines[profile]

    def close(self) -> None:
        close = getattr(self.store, "close", None)
        if close:
            close()

    def verify(self, attempt: AttemptRef, task: TaskSpec, prepared: Prepared, snapshot: Snapshot, *,
               profile: str) -> VerifyOutcome:
        if not snapshot.snapshot_sha or snapshot.manifest_path is None:
            return VerifyOutcome(status=VerifyStatus.NEEDS_REVIEW, reason_code="SNAPSHOT_INVALID",
                                 digest="the attempt left no snapshot to verify")
        key = attempt.verify_key if profile == "standard" else f"{attempt.verify_key}:{profile}"
        order = {"idempotency_key": key, "plan_id": attempt.run.plan_id, "revision": attempt.run.revision,
                 "task_id": attempt.task_id, "attempt_id": attempt.attempt_key, "token": attempt.number,
                 "acceptance_criteria": list(task.acceptance_criteria), "verification": [dict(v) for v in task.verification]}
        source = SnapshotSource(attempt.attempt_key, prepared.repository, prepared.attempt_dir, snapshot.manifest_path,
                                snapshot.base_sha, snapshot.snapshot_sha, prepared.worktree)
        result = self._engine(profile).verify(order, source)
        return outcome_of(result, self.store)


def outcome_of(result: dict, store) -> VerifyOutcome:
    status = str(result.get("status") or "NEEDS_REVIEW")
    if status not in VerifyStatus.__members__:
        status = "NEEDS_REVIEW"
    checks = [c for c in result.get("checks") or () if isinstance(c, dict)]
    failing = tuple(str(c.get("command") or c.get("id")) for c in checks if c.get("status") != "pass")
    passing = tuple(str(c.get("command") or c.get("id")) for c in checks if c.get("status") == "pass")
    reason = str(result.get("reason_code") or next((c.get("reason_code") or c.get("issue_code") for c in checks
                                                    if c.get("status") != "pass" and (c.get("reason_code") or c.get("issue_code"))),
                                                   "UNCLASSIFIED"))
    digest = ""
    if status != "PASS":
        from bitacora_platform.quality_delivery import QualityDeliveryMethods
        digest = QualityDeliveryMethods._failure_digest(SimpleNamespace(store=store), result) or ""
    ref = str(result.get("evidence_manifest") or "")
    return VerifyOutcome(status=VerifyStatus(status), reason_code=reason[:80], result_ref=ref[:200],
                         failing_checks=failing[:50], passing_checks=passing[:50], digest=digest[:12000])
