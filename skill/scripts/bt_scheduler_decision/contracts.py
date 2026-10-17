"""Frozen, JSON-compatible inputs and outputs for a single M2 recommendation."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

API_VERSION = "1.2.0"
LEGACY_API_VERSIONS = frozenset({"1.0.0", "1.1.0"})
COMPLEXITY_VALUES = ("low", "medium", "high", "extreme")
SCOPE_VALUES = ("isolated_fix", "small_change", "large_change", "full_feature", "full_system")
LEVEL_VALUES = ("low", "medium", "high")
EVIDENCE_DIMENSIONS = ("complexity", "scope", "duration", "risk", "coupling", "confidence")
EVIDENCE_KINDS = ("file", "command", "precedent", "spec", "task", "assumption")
CANDIDATE_STATES = ("available", "unknown", "quota_exhausted", "temporarily_unavailable", "auth_invalid",
                    "provider_unavailable", "project_denied", "capacity_unknown", "capacity_exhausted")
QUOTA_STATES = ("available", "unknown", "stale", "exhausted")
AUTH_STATES = ("valid", "invalid", "unknown")
RUNTIME_STATES = ("available", "unavailable", "unknown")
HISTORY_QUALITIES = ("observed", "sparse", "estimated", "unknown")
DECISION_STATUSES = ("recommended", "no_eligible_candidate")
DECISION_METHODS = ("deterministic", "laya", "deterministic_fallback")
SOURCE_REASON_CODES = ("capacity_unknown", "capacity_exhausted", "cooldown_active")
EXCLUSION_REASON_CODES = (
    "profile_not_authorized", "source_unknown", "source_quota_exhausted", "source_temporarily_unavailable",
    "source_auth_invalid", "source_provider_unavailable", "source_unavailable", "project_denied",
    "capacity_unknown", "capacity_exhausted", "route_cooling_down", "auth_invalid", "auth_unknown",
    "runtime_unavailable", "runtime_unknown", "quota_stale", "quota_exhausted", "quota_unknown",
)
DECISION_FACTOR_CODES = (
    "baseline_route", "no_eligible_candidate", "task_ambiguous", "task_unambiguous", "classification_incomplete",
    "risk_floor_applied", "effort_floor_applied", "quota_headroom", "verified_history", "history_sparse",
    "history_no_verified_samples", "duration_measured", "tokens_measured", "laya_choice_accepted",
    "laya_score_below_cutoff", "laya_invalid_choice", "laya_fallback", "candidate_set_small",
    "candidate_set_large", "resource_pressure", "estimated_duration",
)
FALLBACK_REASONS = (
    "laya_unavailable", "laya_timeout", "laya_runtime_error", "laya_invalid_output", "laya_low_confidence",
    "laya_circuit_open", "laya_quality_gate_disabled", "task_not_ambiguous", "insufficient_candidates",
    "candidate_limit_exceeded",
)
CONFIDENCE_SOURCES = ("laya_answer_confidence", "deterministic_policy_margin", "none")
CONFIDENCE_SEMANTICS = ("laya_calibrated_choice_score", "deterministic_policy_margin", "none")
_CONFIDENCE_SEMANTICS_BY_SOURCE = {
    "laya_answer_confidence": "laya_calibrated_choice_score",
    "deterministic_policy_margin": "deterministic_policy_margin",
    "none": "none",
}


def _unit_interval(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and 0 <= value <= 1


class DecisionInputError(ValueError):
    """Stable, redacted input error. `issues` contains field paths, never user-provided values."""

    code = "decision_input_invalid"

    def __init__(self, issues: tuple[str, ...] | list[str]):
        self.issues = tuple(sorted(set(issues)))
        super().__init__(f"{self.code}: {', '.join(self.issues[:8])}")


@dataclass(frozen=True)
class TaskFacts:
    task_id: str
    brief: str
    classifications: Mapping[str, object]
    classification_evidence: Mapping[str, object]
    dependencies: tuple[str, ...] = ()
    acceptance_criteria: tuple[str, ...] = ()
    verification: tuple[Mapping[str, object], ...] = ()
    shared_resources: tuple[str, ...] = ()
    expected_paths: tuple[str, ...] = ()


@dataclass(frozen=True)
class RouteHistory:
    source_quality: str = "unknown"
    verified_successes: int = 0
    verified_failures: int = 0
    claimed_unverified: int = 0
    other_failures: int = 0
    duration_samples: int = 0
    median_duration_seconds: float | None = None
    token_samples: int = 0
    median_total_tokens: int | None = None


@dataclass(frozen=True)
class Candidate:
    route_id: str
    provider: str
    model: str
    profile: str
    account_ref: str
    effort: str | None
    source_status: str
    source_reason_codes: tuple[str, ...]
    profile_authorized: bool
    auth_status: str
    runtime_status: str
    quota_status: str
    quota_observed_at: float | None
    quota_valid_until: float | None
    quota_used_percent: float | None
    baseline_rank: int | None
    history: RouteHistory


@dataclass(frozen=True)
class DecisionRequest:
    plan_id: str
    revision: int
    plan_sha256: str
    free_slots: int
    requested_at: float
    task: TaskFacts
    candidates: tuple[Candidate, ...]
    policy_version: str
    checkpoint_revision: str | None


@dataclass(frozen=True)
class ValidatedRequest:
    request: DecisionRequest
    task_input_sha256: str
    candidate_snapshot_sha256: str
    quota_snapshot_sha256: str
    classification_warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class LayaChoice:
    """Normalized model output; the core validates its route and cutoff before using it."""
    route_id: str
    answer_confidence: float
    checkpoint_revision: str


@dataclass(frozen=True)
class RouteSummary:
    route_id: str
    provider: str
    model: str
    profile: str
    account_ref: str
    effort: str | None
    baseline_rank: int | None = None
    factor_codes: tuple[str, ...] = ()
    quota_observed_at: float | None = None
    quota_used_percent: float | None = None
    quota_valid_until: float | None = None


@dataclass(frozen=True)
class RouteBinding:
    """What a persisted decision says about WHERE its selected route is valid: the plan, revision and task it was made
    for, and whether a later decision for the same plan/task has replaced it (`superseded_by`)."""
    route: RouteSummary
    decision_id: str
    plan_id: str
    revision: int
    plan_sha256: str
    task_id: str
    created_at: float
    superseded_by: str | None = None


@dataclass(frozen=True)
class Exclusion:
    route_id: str
    provider: str
    model: str
    profile: str
    account_ref: str
    effort: str | None
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class Confidence:
    value: float | None
    source: str
    semantics: str
    calibration_version: str | None = None
    accepted_cutoff: float | None = None

    def __post_init__(self) -> None:
        if self.source not in CONFIDENCE_SOURCES or \
                self.semantics != _CONFIDENCE_SEMANTICS_BY_SOURCE.get(self.source):
            raise ValueError("confidence source and semantics are not supported")
        if self.source == "laya_answer_confidence":
            if not _unit_interval(self.value) or not _unit_interval(self.accepted_cutoff) or \
                    self.value < self.accepted_cutoff or not isinstance(self.calibration_version, str) or \
                    not self.calibration_version.strip() or len(self.calibration_version) > 128:
                raise ValueError("Laya confidence must pass a bounded local choice calibration")
            try:
                self.calibration_version.encode("utf-8", errors="strict")
            except UnicodeEncodeError as exc:
                raise ValueError("calibration version must be valid Unicode") from exc
        elif self.source == "deterministic_policy_margin":
            if self.value is not None and not _unit_interval(self.value) or \
                    self.calibration_version is not None or self.accepted_cutoff is not None:
                raise ValueError("deterministic confidence must describe only a bounded policy margin")
        elif self.value is not None or self.calibration_version is not None or self.accepted_cutoff is not None:
            raise ValueError("empty confidence cannot carry a score or calibration")


@dataclass(frozen=True)
class DecisionRecord:
    schema_version: str
    decision_id: str
    idempotency_key: str
    previous_decision_id: str | None
    plan_id: str
    revision: int
    plan_sha256: str
    task_id: str
    created_at: float
    status: str
    selected: RouteSummary | None
    alternatives: tuple[RouteSummary, ...]
    exclusions: tuple[Exclusion, ...]
    baseline_route_id: str | None
    method: str
    fallback_reason: str | None
    policy_version: str
    checkpoint_revision: str | None
    candidate_snapshot_sha256: str
    quota_snapshot_sha256: str
    confidence: Confidence
    factor_codes: tuple[str, ...]
    rationale: str
