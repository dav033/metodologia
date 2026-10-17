"""Immutable contracts owned by M5; no scheduler or executor imports."""
from __future__ import annotations

from dataclasses import asdict, dataclass

from .validation import (
    decode,
    digest,
    enum,
    identifier,
    integer,
    number,
    reference,
    refs,
    require,
    snapshot,
)

CAUSES = ("clean", "quota_exhausted", "connection_lost", "agent_error", "timeout", "killed",
          "incomplete_output", "start_failed", "lost", "artifact_error", "cancelled",
          "verification_rejected", "integration_conflict", "predecessor_missing", "unknown")
CONFIDENCES = ("confirmed", "reported", "inferred", "unknown")


@dataclass(frozen=True)
class RecoveryCase:
    run_id: str
    plan_id: str
    revision: int
    plan_sha256: str
    task_id: str
    attempt_id: str
    token: int
    core_cause: str
    technical_cause: str = "unknown"
    confidence: str = "unknown"
    evidence_refs: tuple[str, ...] = ()
    handoff_sha: str | None = None
    execution_state: str = "unknown"
    current: bool = False
    manual_cancel: bool = False
    identity_verified: bool = False
    transient_confirmed: bool = False
    verification_ref: str | None = None
    reset_epoch: float | None = None
    attempts_used: int = 1
    max_attempts: int = 1
    recovery_round: int = 0
    max_waits: int = 3
    max_wait_seconds: float = 3600
    failure_at: float = 0
    now: float = 0

    def __post_init__(self) -> None:
        for value in (self.run_id, self.plan_id, self.task_id, self.attempt_id):
            identifier(value)
        digest(self.plan_sha256)
        integer(self.revision, 1)
        integer(self.token, 1, 2**63 - 1)
        enum(self.core_cause, ("execution_failed", "verification_rejected", "lost"))
        enum(self.technical_cause, CAUSES)
        enum(self.confidence, CONFIDENCES)
        enum(self.execution_state, ("failed", "finished", "cancelled", "live", "unknown"))
        refs(self.evidence_refs)
        if self.handoff_sha is not None:
            snapshot(self.handoff_sha)
        if self.verification_ref is not None:
            reference(self.verification_ref)
        for value in (self.current, self.manual_cancel, self.identity_verified, self.transient_confirmed):
            require(type(value) is bool)
        for value in (self.attempts_used, self.max_attempts):
            integer(value, 1)
        for value in (self.recovery_round, self.max_waits):
            integer(value)
        number(self.max_wait_seconds, 1, 86400)
        number(self.failure_at)
        number(self.now)
        if self.reset_epoch is not None:
            number(self.reset_epoch)

    def to_dict(self) -> dict:
        return {"schema_version": "m5.recovery-case/1", **asdict(self), "evidence_refs": list(self.evidence_refs)}

    @classmethod
    def from_dict(cls, raw: object) -> RecoveryCase:
        data = decode(cls, raw, "m5.recovery-case/1")
        try:
            return cls(**data)
        except TypeError:
            require(False)


@dataclass(frozen=True)
class Policy:
    version: str = "1.0.0"
    base_backoff_seconds: float = 1
    max_backoff_seconds: float = 60
    max_same_cause: int = 2
    evidence_max_age_seconds: float = 86400
    max_elapsed_seconds: float = 86400
    reset_margin_seconds: float = 1
    max_decisions: int = 10000

    def __post_init__(self) -> None:
        identifier(self.version)
        number(self.base_backoff_seconds, 1, 86400)
        number(self.max_backoff_seconds, 1, 86400)
        require(self.base_backoff_seconds <= self.max_backoff_seconds)
        integer(self.max_same_cause, 1, 100)
        integer(self.max_decisions, 1, 1_000_000)
        number(self.evidence_max_age_seconds, 1, 31_536_000)
        number(self.max_elapsed_seconds, 1, 31_536_000)
        number(self.reset_margin_seconds, 0, 3600)


@dataclass(frozen=True)
class HistorySummary:
    same_cause_attempts: int = 0
    decisions: int = 0

    def __post_init__(self) -> None:
        integer(self.same_cause_attempts)
        integer(self.decisions)


@dataclass(frozen=True)
class RecoveryDecision:
    decision_id: str
    action: str
    reason_code: str
    evidence_refs: tuple[str, ...]
    confidence: str
    policy_version: str
    wait_seconds: float
    retry_budget_remaining: int
    routing_hint: str | None
    human_required: bool
    cooldown_until: float | None
    waits_remaining: int

    def __post_init__(self) -> None:
        digest(self.decision_id)
        enum(self.action, ("retry", "wait", "block"))
        identifier(self.reason_code)
        refs(self.evidence_refs)
        enum(self.confidence, CONFIDENCES)
        identifier(self.policy_version)
        number(self.wait_seconds, 0, 86400)
        integer(self.retry_budget_remaining)
        integer(self.waits_remaining)
        require(type(self.human_required) is bool)
        if self.routing_hint is not None:
            enum(self.routing_hint, ("same_route", "reevaluate", "avoid_last_route"))
        if self.cooldown_until is not None:
            number(self.cooldown_until, high=1e12 + 86400)
        require((self.action == "wait") == (self.wait_seconds > 0))
        require(self.action != "retry" or self.retry_budget_remaining > 0)

    def to_dict(self) -> dict:
        return {"schema_version": "m5.recovery-decision/1", **asdict(self), "evidence_refs": list(self.evidence_refs)}

    @classmethod
    def from_dict(cls, raw: object) -> RecoveryDecision:
        data = decode(cls, raw, "m5.recovery-decision/1")
        try:
            return cls(**data)
        except TypeError:
            require(False)
