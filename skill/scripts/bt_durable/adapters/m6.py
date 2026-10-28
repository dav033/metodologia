"""Verifier port over the legacy M6 engine (CONSERVAR): sandboxed checks, evidence manifests, pass cache.

The durable runtime calls `QualityEngine.verify` directly from a DBOS step; M6's own request table makes a repeated
step return the stored verdict instead of running the checks twice. M6's outbox and its M1 delivery are not used:
the step result is the delivery. The failure digest the agent reads is the shared one (`quality_delivery`).

Profiles: `standard` is the operator's policy; `relaxed` is the bounded environment repair the recovery policy may
ask for once (more time, more workspace, a larger Node heap) — it never changes a command or a criterion.
"""
from __future__ import annotations

import dataclasses
import json
import re
from pathlib import Path
from types import SimpleNamespace

from bt_contracts.execution import (
    AttemptRef,
    Prepared,
    Snapshot,
    VerifyOutcome,
    VerifyStatus,
)
from bt_scheduler_quality import sandbox_mounts
from bt_scheduler_quality.engine import QualityEngine
from bt_scheduler_quality.policy import QualityPolicy
from bt_scheduler_quality.snapshot import SnapshotSource
from bt_scheduler_quality.store import QualityStore

from ..legacy import TaskSpec

RELAXED_NODE_HEAP_MB = 12288          # twice the sandbox default (sandbox_mounts.NODE_OPTIONS), the repair ceiling
_HEAP = re.compile(r"--max-old-space-size=(\d+)")


def relaxed(policy: QualityPolicy) -> QualityPolicy:
    env = dict(policy.environment)
    current = _HEAP.search(env.get("NODE_OPTIONS", "")) or _HEAP.search(sandbox_mounts.NODE_OPTIONS)
    heap = min(max(int(current.group(1)) * 2 if current else RELAXED_NODE_HEAP_MB, 4096), RELAXED_NODE_HEAP_MB)
    others = _HEAP.sub("", env.get("NODE_OPTIONS", "")).strip()
    env["NODE_OPTIONS"] = f"{others} --max-old-space-size={heap}".strip()
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
    """`policy_for(run)` / `authority_for(run)` give each run its operator policy (verifier env, requires, accepted
    fingerprints) and its authorization callbacks, the same ones the legacy owner uses."""

    def __init__(self, *, store_path: Path, policy_for=None, authority_for=None, attestations=None):
        Path(store_path).parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        Path(store_path).parent.chmod(0o700)                 # the M6 store refuses a directory others can read
        self.store = QualityStore(Path(store_path))
        self.policy_for = policy_for or (lambda run: QualityPolicy())
        self.authority_for = authority_for or (lambda run: None)
        self.attestations = attestations
        self._engines: dict[tuple[str, str], QualityEngine] = {}

    def _engine(self, run, profile: str) -> QualityEngine:
        key = (run.run_id, profile)
        if key not in self._engines:
            policy = self.policy_for(run)
            policy = relaxed(policy) if profile == "relaxed" else policy
            self._engines[key] = QualityEngine(policy, self.store, verification_authority=self.authority_for(run),
                                               attestations=self.attestations)
        return self._engines[key]

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
        # the trusted handoff manifest names the attempt that produced the snapshot (a legacy one when reconciling)
        producer = json.loads(snapshot.manifest_path.read_text(encoding="utf-8")).get("attempt_id") or attempt.attempt_key
        order = {"idempotency_key": key, "plan_id": attempt.run.plan_id, "revision": attempt.run.revision,
                 "task_id": attempt.task_id, "attempt_id": producer, "token": attempt.number,
                 "acceptance_criteria": list(task.acceptance_criteria), "verification": [dict(v) for v in task.verification]}
        source = SnapshotSource(producer, prepared.repository, prepared.attempt_dir, snapshot.manifest_path,
                                snapshot.base_sha, snapshot.snapshot_sha, prepared.worktree)
        result = self._engine(attempt.run, profile).verify(order, source)
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
