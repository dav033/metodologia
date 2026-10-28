"""Execution contracts of the durable runtime (REQ-030 M1/M2): run and attempt identity, routes, outcomes, ownership.

Every value that a DBOS step returns or a workflow receives is one of these models, so a structural mismatch (a
renamed field, an array where an object was expected, an unknown state) fails at the boundary, before an agent
process is started and quota is spent. Models are frozen and reject unknown fields; identifiers are validated with
the same alphabet the legacy runtime uses for directory and branch names.
"""
from __future__ import annotations

import hashlib
import re
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

CONTRACT_VERSION = "1.0.0"

Slug = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")]
ReqId = Annotated[str, StringConstraints(pattern=r"^REQ-\d{3,}$")]
TaskId = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,47}$")]
Sha256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
GitSha = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{40}$")]
_KEY = re.compile(r"[^A-Za-z0-9._-]+")


class Contract(BaseModel):
    """Frozen, closed record: unknown fields are an error, never silently dropped."""
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=False)


class Backend(StrEnum):
    LEGACY = "legacy"
    DBOS = "dbos"


class RunRef(Contract):
    """One approved plan revision of one requirement: the unit a run workflow owns."""
    project: Slug
    req: ReqId
    plan_id: str = Field(min_length=1, max_length=120)
    revision: int = Field(ge=1)
    plan_sha256: Sha256
    plan_path: Path

    @property
    def run_id(self) -> str:
        return f"{self.project}:{self.req}:r{self.revision}"


class AttemptRef(Contract):
    """Everything needed to name one attempt and every external effect it may have produced.

    `attempt_key` is deterministic from the run, task and attempt number, so a recovered workflow that re-runs a step
    names the same worktree, systemd unit and verification request instead of creating new ones."""
    run: RunRef
    task_id: TaskId
    number: int = Field(ge=1, le=999)
    workflow_id: str = Field(min_length=1, max_length=200)

    @property
    def attempt_key(self) -> str:
        base = _KEY.sub("-", f"{self.run.project}-{self.run.req}-r{self.run.revision}-{self.task_id}-a{self.number}")
        digest = hashlib.sha256(f"{self.run.run_id}:{self.task_id}:{self.number}".encode()).hexdigest()[:8]
        return f"{base[:88]}-{digest}"

    @property
    def verify_key(self) -> str:
        return f"{self.run.plan_id}:r{self.run.revision}:{self.attempt_key}:verify"


class Route(Contract):
    """A launchable route chosen by the decision layer. `reference` is opaque provenance for telemetry."""
    provider: Literal["claude", "codex", "antigravity", "fake"]
    model: str = Field(min_length=1, max_length=80)
    profile: str = Field(default="", max_length=80)
    effort: str = Field(default="", max_length=20)
    reference: str = Field(default="", max_length=300)


class RouteDecision(Contract):
    """The answer of the router: run now on `route`, wait until `not_before`, or stop because nothing is allowed."""
    kind: Literal["run", "wait", "unavailable"]
    route: Route | None = None
    not_before: float | None = None
    reason: str = Field(default="", max_length=500)

    @model_validator(mode="after")
    def _shape(self) -> RouteDecision:
        if self.kind == "run" and self.route is None:
            raise ValueError("a run decision needs a route")
        if self.kind == "wait" and self.not_before is None:
            raise ValueError("a wait decision needs not_before (an epoch); unknown resets are 'unavailable'")
        return self


class Prepared(Contract):
    """The isolated checkout and launch material of one attempt (secrets stay out: env is a file path)."""
    worktree: Path
    branch: str
    base_sha: GitSha
    repository: Path
    attempt_dir: Path
    prompt_path: Path
    argv: tuple[str, ...]
    env_file: Path
    stdin_path: Path | None = None
    timeout_seconds: int = Field(ge=1, le=6 * 3600)


class ProcessRecord(Contract):
    """What the Linux runtime reported about the agent process (copied from bt_supervisor's Observation)."""
    backend: Literal["systemd", "pgroup"]
    unit: str | None = None
    invocation_id: str | None = None
    state: Literal["running", "exited", "absent", "unknown"]
    exit_code: int | None = None
    result: str | None = None
    oom_killed: bool = False
    live_pids: tuple[int, ...] = ()      # stragglers still alive after the main process exited
    started_at: float | None = None
    ended_at: float | None = None
    log_path: Path


class AgentReport(Contract):
    """The provider-aware reading of a finished agent process (the legacy AgentDriver.classify, made explicit)."""
    status: Literal["completed", "failed", "limit", "partial", "timeout", "cancelled"]
    reset_epoch: int | None = None
    text: str = Field(default="", max_length=4000)
    total_tokens: int | None = None


class Snapshot(Contract):
    """The deterministic handoff commit of the attempt's final files."""
    snapshot_sha: GitSha | None
    base_sha: GitSha
    changed_paths: tuple[str, ...] = ()
    manifest_path: Path | None = None


class VerifyStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    STALE = "STALE"


class VerifyOutcome(Contract):
    """The M6 verdict, reduced to what the control plane decides on; `result_ref` points at the evidence manifest."""
    status: VerifyStatus
    reason_code: str = Field(default="UNCLASSIFIED", max_length=80)
    result_ref: str = Field(default="", max_length=200)
    failing_checks: tuple[str, ...] = ()
    passing_checks: tuple[str, ...] = ()
    digest: str = Field(default="", max_length=12000)


class AttemptStatus(StrEnum):
    ACCEPTED = "accepted"            # verified PASS and integrated
    REJECTED = "rejected"            # ran, verification said FAIL
    EXECUTION_FAILED = "execution_failed"
    NEEDS_REVIEW = "needs_review"
    CANCELLED = "cancelled"


class AttemptOutcome(Contract):
    attempt: AttemptRef
    status: AttemptStatus
    route: Route | None = None
    process: ProcessRecord | None = None
    agent: AgentReport | None = None
    snapshot: Snapshot | None = None
    verify: VerifyOutcome | None = None
    failure: FailureReport | None = None
    integrated_ref: GitSha | None = None


class TaskStatus(StrEnum):
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"
    INHERITED = "inherited"          # completed under the legacy runtime, evidence re-checked by the migration bridge


class TaskOutcome(Contract):
    run_id: str
    task_id: TaskId
    status: TaskStatus
    attempts: int = Field(ge=0)
    snapshot_sha: GitSha | None = None
    integrated_ref: GitSha | None = None
    decision: RecoveryDecision | None = None
    provenance: str = Field(default="", max_length=500)


class LegacyTask(Contract):
    """One task's legacy progress, re-proved by the migration bridge (bt_durable.migrate) from M6 evidence.

    `inherit`: a PASS for this exact task specification and a snapshot that still exists — integrated into the new
    line without running anything. `reconcile`: a snapshot exists but the evidence does not prove it — the snapshot is
    verified again first, and only a PASS makes it count."""
    task_id: TaskId
    verdict: Literal["inherit", "reconcile"]
    snapshot_sha: GitSha
    base_sha: GitSha
    repository: Path
    attempt_dir: Path
    manifest_path: Path
    worktree: Path | None = None
    provenance: str = Field(default="", max_length=500)


class LegacyProgress(Contract):
    inventory_digest: str = Field(default="", max_length=64)
    tasks: tuple[LegacyTask, ...] = ()

    def of(self, verdict: str) -> dict[str, LegacyTask]:
        return {t.task_id: t for t in self.tasks if t.verdict == verdict}


class OwnerRecord(Contract):
    """Who owns the execution state of one run. Exactly one backend; changes only through an explicit migration."""
    run_id: str
    backend: Backend
    workflow_id: str | None = None
    since: float
    by: str = Field(min_length=1, max_length=80)
    migrated_from: str | None = None


from .failure import FailureReport, RecoveryDecision

AttemptOutcome.model_rebuild()
TaskOutcome.model_rebuild()
