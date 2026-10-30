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
import logging
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
from bt_scheduler_quality.runner import SandboxRunner
from bt_scheduler_quality.snapshot import SnapshotSource
from bt_scheduler_quality.store import QualityStore

from ..legacy import TaskSpec

LOG = logging.getLogger("bt_durable.m6")
# What a check must never inherit under `verifier.inherit_env` (the operator's environment): the engine's own variables
# (its database URL, DBOS settings, the service manager's per-unit names; the same rule as an agent's environment,
# adapters/m3.py) and the names that point at the host session's devices and sockets, which the sandbox does not have:
# with VK_DRIVER_FILES naming the host's GPU driver, Chromium's software WebGL (SwiftShader over Vulkan) cannot start in
# the sandbox (pictures REQ-021 T3.11, every attempt, both runtimes).
HOST_SESSION_ENV = frozenset({
    "VK_DRIVER_FILES", "VK_ICD_FILENAMES", "VK_ADD_DRIVER_FILES", "VK_LAYER_PATH", "VK_ADD_LAYER_PATH",
    "__EGL_VENDOR_LIBRARY_FILENAMES", "__EGL_VENDOR_LIBRARY_DIRS", "__GLX_VENDOR_LIBRARY_NAME", "LIBVA_DRIVER_NAME",
    "AQ_DRM_DEVICES", "WLR_DRM_DEVICES", "DISPLAY", "WAYLAND_DISPLAY", "XDG_RUNTIME_DIR", "DBUS_SESSION_BUS_ADDRESS",
    "HYPRLAND_INSTANCE_SIGNATURE", "XAUTHORITY",
})


def sandbox_policy(policy: QualityPolicy) -> QualityPolicy:
    """`policy` with the inherited environment cleared of engine and host-session names; what the operator declares
    explicitly (`environment`: the project's env file, the plan's `requires`) is kept as it is."""
    from bt_supervisor.model import MANAGER_ENV

    from .m3 import ENGINE_INTERPRETER_ENV, ENGINE_ONLY_PREFIXES
    kept = tuple((name, value) for name, value in policy.ambient_environment
                 if not name.startswith(ENGINE_ONLY_PREFIXES) and name not in MANAGER_ENV and name not in HOST_SESSION_ENV
                 and name not in ENGINE_INTERPRETER_ENV)
    return policy if kept == policy.ambient_environment else dataclasses.replace(policy, ambient_environment=kept)
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


class EngineCommands:
    """The checks the engine owns, answered without the sandbox, as the legacy owner's runner answers them
    (`quality_audit_evidence.EvidenceRunner`): the findings-ledger contract `bitacora.py audit-ledger check <ledger>`
    of every audit task. A product's sandbox has no bitácora code, so run there the check could only fail as
    `M6_SETUP_ERROR:EXEC` (pictures REQ-021 T2.7, the first audit on the durable runtime). Everything else runs in the
    sandbox unchanged."""

    def __init__(self, runner):
        self.runner = runner

    def run(self, spec, snapshot_root, **kwargs):
        from bitacora_platform.quality_ledger_command import run as ledger_check
        owned = ledger_check(spec, snapshot_root)
        return owned if owned is not None else self.runner.run(spec, snapshot_root, **kwargs)

    def __getattr__(self, name):
        return getattr(self.runner, name)


class M6Verifier:
    """`policy_for(run)` / `authority_for(run)` give each run its operator policy (verifier env, requires, accepted
    fingerprints) and its authorization callbacks, the same ones the legacy owner uses."""

    def __init__(self, *, store_path: Path, policy_for=None, authority_for=None, attestations=None,
                 attestations_for=None, on_verdict=None):
        Path(store_path).parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        Path(store_path).parent.chmod(0o700)                 # the M6 store refuses a directory others can read
        self.store = QualityStore(Path(store_path))
        self.policy_for = policy_for or (lambda run: QualityPolicy())
        self.authority_for = authority_for or (lambda run: None)
        # `attestations_for(run)`: the run's coordinator receipts (bt_attestation.lookup of its requirement folder);
        # a valid receipt settles only its own manual check, command checks still have to pass
        self.attestations_for = attestations_for or (lambda run: attestations)
        # `on_verdict(attempt, outcome)`: the shared notes trail (RUN.notes history and last verification failure)
        self.on_verdict = on_verdict
        self._engines: dict[tuple[str, str], QualityEngine] = {}

    def recover_interrupted(self) -> tuple[str, ...]:
        """On engine start, before any verification: a request a stopped engine left `running` is recorded as
        interrupted (ENGINE_INTERRUPTED, no check replayed) and queued again, once per request, as the legacy owner does
        on start. The DBOS verify step that re-runs after the restart then claims it and verifies the same snapshot.
        Without this the re-run step met its own orphaned request (REQUEST_IN_PROGRESS) and the task waited for the owner
        (pictures REQ-021 T95, 2026-10-29 18:44, D-171). Only the engine process may call it: it owns this store.
        Returns the requests queued again; a second interruption of the same request stays a review for the owner."""
        from bt_scheduler_quality.contracts import QualityError
        again = []
        for key in QualityEngine(QualityPolicy(), self.store).recover_interrupted():
            try:
                self.store.retry_interrupted(key, "engine-restart",
                                             "verification interrupted by a restart of the durable engine; rerun it")
                again.append(key)
            except QualityError as error:
                LOG.warning("interrupted verification %s stays for review: %s", key, error)
        return tuple(again)

    def _engine(self, run, profile: str) -> QualityEngine:
        key = (run.run_id, profile)
        if key not in self._engines:
            policy = sandbox_policy(self.policy_for(run))
            policy = relaxed(policy) if profile == "relaxed" else policy
            self._engines[key] = QualityEngine(policy, self.store, runner=EngineCommands(SandboxRunner(policy)),
                                               verification_authority=self.authority_for(run),
                                               attestations=self.attestations_for(run))
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
        # profiles: standard | relaxed (bounded environment repair) | owner<N> (the owner asked for a new verdict of the
        # same snapshot, e.g. after attesting a manual check: same policy, its own request key so M6 runs it again)
        key = attempt.verify_key if profile == "standard" else f"{attempt.verify_key}:{profile}"
        # the trusted handoff manifest names the attempt that produced the snapshot (a legacy one when reconciling)
        producer = json.loads(snapshot.manifest_path.read_text(encoding="utf-8")).get("attempt_id") or attempt.attempt_key
        order = {"idempotency_key": key, "plan_id": attempt.run.plan_id, "revision": attempt.run.revision,
                 "task_id": attempt.task_id, "attempt_id": producer, "token": attempt.number,
                 "acceptance_criteria": list(task.acceptance_criteria), "verification": [dict(v) for v in task.verification]}
        source = SnapshotSource(producer, prepared.repository, prepared.attempt_dir, snapshot.manifest_path,
                                snapshot.base_sha, snapshot.snapshot_sha, prepared.worktree)
        result = self._engine(attempt.run, "relaxed" if profile == "relaxed" else "standard").verify(order, source)
        outcome = outcome_of(result, self.store)
        if self.on_verdict is not None:
            try:
                self.on_verdict(attempt, outcome)
            except Exception as error:  # noqa: BLE001 - the notes trail informs; it never changes a verdict
                LOG.warning("notes for %s not written: %s", attempt.attempt_key, error)
        return outcome


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
    issues = tuple(dict.fromkeys(str(item.get("code")) for item in result.get("issues") or ()
                                 if isinstance(item, dict) and item.get("code")))
    # the result's criteria name what is still unproven ({criterion, status, evidence}); when the only doubt is manual
    # evidence (CRITERION_MANUAL), those are exactly the manual checks a receipt must cover
    manual = tuple(str(c.get("criterion")) for c in result.get("criteria") or ()
                   if isinstance(c, dict) and c.get("status") != "pass") if "CRITERION_MANUAL" in issues else ()
    return VerifyOutcome(status=VerifyStatus(status), reason_code=reason[:80], result_ref=ref[:200],
                         failing_checks=failing[:50], passing_checks=passing[:50], digest=digest[:12000],
                         issue_codes=issues[:20], manual_checks=manual[:20])
