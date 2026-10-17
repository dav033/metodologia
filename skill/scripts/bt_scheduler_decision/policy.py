"""Deterministic candidate eligibility and reference ordering."""
from __future__ import annotations

import math
import re
from collections.abc import Mapping
from dataclasses import dataclass

from .contracts import (
    API_VERSION,
    LEVEL_VALUES,
    Candidate,
    DecisionInputError,
    Exclusion,
    ValidatedRequest,
)
from .history import (
    HISTORY_LEVELS,
    MIN_VERIFIED_SAMPLES,
    ContextualHistoryAssessment,
    PerformanceMeasurement,
)
from .validation import validate_request

POLICY_SCHEMA_VERSION = 1
ROUTE_POLICY_VERSION = "m2-route-policy-v1"
OBJECTIVE_ORDER = (
    "hard_eligibility",
    "quality_floor",
    "verified_quality_lower_bound",
    "quality_uncertainty",
    "quota_window_pressure",
    "duration_estimate",
    "relative_cost",
    "risk_reserve",
    "upcoming_reset",
    "baseline_rank",
    "route_id",
)
MAX_QUALITY_FLOORS = len(LEVEL_VALUES)
MAX_POLICY_EVIDENCE = 256
_WINDOW_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}\Z")


def _is_count(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _finite_at_least(value: object, minimum: float) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        numeric = float(value)
    except (OverflowError, ValueError):
        return False
    return math.isfinite(numeric) and numeric >= minimum


def _finite_in_range(value: object, minimum: float, maximum: float) -> bool:
    return _finite_at_least(value, minimum) and value <= maximum

_SOURCE_REASONS = {
    "unknown": "source_unknown",
    "quota_exhausted": "source_quota_exhausted",
    "temporarily_unavailable": "source_temporarily_unavailable",
    "auth_invalid": "source_auth_invalid",
    "provider_unavailable": "source_provider_unavailable",
    "project_denied": "project_denied",
    "capacity_unknown": "capacity_unknown",
    "capacity_exhausted": "capacity_exhausted",
}
_BLOCKING_SOURCE_REASONS = {
    "capacity_unknown": "capacity_unknown",
    "capacity_exhausted": "capacity_exhausted",
    "cooldown_active": "route_cooling_down",
}


@dataclass(frozen=True)
class CandidateRanking:
    eligible: tuple[Candidate, ...]
    exclusions: tuple[Exclusion, ...]
    selected: Candidate | None


@dataclass(frozen=True)
class QuotaWindowPreference:
    """Comparable cached pressure/reset facts for one already-eligible quota window."""

    window_id: str
    used_percent: float
    seconds_to_reset: float | None

    def __post_init__(self) -> None:
        if not isinstance(self.window_id, str) or _WINDOW_ID.fullmatch(self.window_id) is None or \
                not _finite_in_range(self.used_percent, 0, 100) or \
                self.seconds_to_reset is not None and not _finite_at_least(self.seconds_to_reset, 0):
            raise DecisionInputError(("route_policy.quota_window",))


@dataclass(frozen=True)
class RoutePolicyEvidence:
    """Optional comparable evidence; quality is accepted only from correlated verified outcomes."""

    quality_assessment: ContextualHistoryAssessment | None = None
    quota_windows: tuple[QuotaWindowPreference, ...] = ()
    duration_seconds: float | None = None
    relative_cost: float | None = None
    relative_cost_scale: str | None = None
    reserved_for_higher_risk: bool = False

    def __post_init__(self) -> None:
        if (self.quality_assessment is not None and
                not isinstance(self.quality_assessment, ContextualHistoryAssessment)) or \
                not isinstance(self.quota_windows, tuple) or len(self.quota_windows) > 64 or \
                any(not isinstance(window, QuotaWindowPreference) for window in self.quota_windows) or \
                len({window.window_id for window in self.quota_windows}) != len(self.quota_windows) or \
                self.duration_seconds is not None and not _finite_at_least(self.duration_seconds, 0) or \
                self.relative_cost is not None and not _finite_at_least(self.relative_cost, 0) or \
                (self.relative_cost is None) != (self.relative_cost_scale is None) or \
                self.relative_cost_scale is not None and (not isinstance(self.relative_cost_scale, str) or
                                                          not _WINDOW_ID.fullmatch(self.relative_cost_scale)) or \
                not isinstance(self.reserved_for_higher_risk, bool):
            raise DecisionInputError(("route_policy.evidence",))


@dataclass(frozen=True)
class RoutePolicyConfig:
    """Versioned lexicographic policy; absent risk floors remain deliberately unconfigured."""

    quality_floors_by_risk: tuple[tuple[str, float], ...] = ()
    minimum_verified_samples: int = MIN_VERIFIED_SAMPLES
    upcoming_reset_window_seconds: int = 1800
    schema_version: int = POLICY_SCHEMA_VERSION
    version: str = ROUTE_POLICY_VERSION

    def __post_init__(self) -> None:
        floors = self.quality_floors_by_risk
        if self.schema_version != POLICY_SCHEMA_VERSION or self.version != ROUTE_POLICY_VERSION or \
                not _is_count(self.minimum_verified_samples) or \
                self.minimum_verified_samples < MIN_VERIFIED_SAMPLES or \
                not _is_count(self.upcoming_reset_window_seconds) or self.upcoming_reset_window_seconds > 86_400 or \
                not isinstance(floors, tuple) or len(floors) > MAX_QUALITY_FLOORS:
            raise DecisionInputError(("route_policy.config",))
        risks: set[str] = set()
        for item in floors:
            if not isinstance(item, tuple) or len(item) != 2 or not isinstance(item[0], str) or \
                    item[0] not in LEVEL_VALUES or \
                    item[0] in risks or not _finite_in_range(item[1], 0, 1):
                raise DecisionInputError(("route_policy.quality_floor",))
            risks.add(item[0])

    def quality_floor_for(self, risk: str | None) -> float | None:
        return dict(self.quality_floors_by_risk).get(risk)


@dataclass(frozen=True)
class RoutePolicyExclusion:
    route_id: str
    reason_code: str = "quality_floor_not_met"


@dataclass(frozen=True)
class RoutePolicyRanking:
    eligible: tuple[Candidate, ...]
    hard_exclusions: tuple[Exclusion, ...]
    quality_exclusions: tuple[RoutePolicyExclusion, ...]
    selected: Candidate | None
    policy_version: str
    fallback_reason: str | None


DEFAULT_ROUTE_POLICY = RoutePolicyConfig()


def _candidate_reasons(candidate: Candidate) -> tuple[str, ...]:
    reasons: set[str] = set()
    if not candidate.profile_authorized:
        reasons.add("profile_not_authorized")
    if candidate.source_status != "available":
        reasons.add(_SOURCE_REASONS.get(candidate.source_status, "source_unavailable"))
    for code in candidate.source_reason_codes:
        if code in _BLOCKING_SOURCE_REASONS:
            reasons.add(_BLOCKING_SOURCE_REASONS[code])
    if candidate.auth_status != "valid":
        reasons.add("auth_invalid" if candidate.auth_status == "invalid" else "auth_unknown")
    if candidate.runtime_status != "available":
        reasons.add("runtime_unavailable" if candidate.runtime_status == "unavailable" else "runtime_unknown")
    if candidate.quota_status != "available":
        reasons.add({"stale": "quota_stale", "exhausted": "quota_exhausted"}.get(
            candidate.quota_status, "quota_unknown"))
    if reasons:
        reasons.update(candidate.source_reason_codes)
    return tuple(sorted(reasons))


def _validated(value: object) -> ValidatedRequest:
    if isinstance(value, ValidatedRequest):
        return validate_request(value.request)
    return validate_request(value)


def rank_candidates(request: object) -> CandidateRanking:
    """Filter invalid routes, then preserve existing router rank and break ties by stable route identity."""
    validated = _validated(request)
    eligible: list[Candidate] = []
    exclusions: list[Exclusion] = []
    for candidate in validated.request.candidates:
        reasons = _candidate_reasons(candidate)
        if not reasons:
            eligible.append(candidate)
            continue
        exclusions.append(Exclusion(
            route_id=candidate.route_id,
            provider=candidate.provider,
            model=candidate.model,
            profile=candidate.profile,
            account_ref=candidate.account_ref,
            effort=candidate.effort,
            reason_codes=reasons,
        ))
    eligible.sort(key=lambda candidate: (
        candidate.baseline_rank is None,
        candidate.baseline_rank if candidate.baseline_rank is not None else 0,
        candidate.route_id,
    ))
    exclusions.sort(key=lambda exclusion: exclusion.route_id)
    frozen = tuple(eligible)
    return CandidateRanking(frozen, tuple(exclusions), frozen[0] if frozen else None)


def rank_with_route_policy(request: object, evidence_by_route: Mapping[str, RoutePolicyEvidence], *,
                           risk: str | None = None,
                           preserve_baseline: bool = False,
                           policy: RoutePolicyConfig = DEFAULT_ROUTE_POLICY) -> RoutePolicyRanking:
    """Apply optional lexicographic objectives only to routes that passed every existing hard filter."""
    if not isinstance(policy, RoutePolicyConfig) or not isinstance(evidence_by_route, Mapping) or \
            not isinstance(preserve_baseline, bool) or \
            len(evidence_by_route) > MAX_POLICY_EVIDENCE:
        raise DecisionInputError(("route_policy.input",))
    normalized_policy = RoutePolicyConfig(
        policy.quality_floors_by_risk, policy.minimum_verified_samples, policy.upcoming_reset_window_seconds,
        policy.schema_version, policy.version,
    )
    ranking = rank_candidates(request)
    all_route_ids = {candidate.route_id for candidate in ranking.eligible} | \
        {item.route_id for item in ranking.exclusions}
    normalized_evidence: dict[str, RoutePolicyEvidence] = {}
    for route_id, raw in evidence_by_route.items():
        if not isinstance(route_id, str) or route_id not in all_route_ids or not isinstance(raw, RoutePolicyEvidence):
            raise DecisionInputError(("route_policy.evidence_identity",))
        windows = tuple(QuotaWindowPreference(window.window_id, window.used_percent, window.seconds_to_reset)
                        for window in raw.quota_windows if isinstance(window, QuotaWindowPreference))
        if len(windows) != len(raw.quota_windows):
            raise DecisionInputError(("route_policy.evidence",))
        normalized_evidence[route_id] = RoutePolicyEvidence(
            raw.quality_assessment, windows, raw.duration_seconds, raw.relative_cost, raw.relative_cost_scale,
            raw.reserved_for_higher_risk,
        )

    configured_floors = dict(normalized_policy.quality_floors_by_risk)
    if risk is not None and risk not in LEVEL_VALUES:
        raise DecisionInputError(("route_policy.risk",))
    if risk is None and configured_floors:
        quality_floor = max(configured_floors.values())
    else:
        quality_floor = normalized_policy.quality_floor_for(risk)

    if not ranking.eligible:
        return RoutePolicyRanking((), ranking.exclusions, (), None, normalized_policy.version,
                                  "no_hard_eligible_route")
    if preserve_baseline:
        return RoutePolicyRanking(ranking.eligible, ranking.exclusions, (), ranking.selected,
                                  normalized_policy.version, "baseline_preserved")

    eligible: list[Candidate] = []
    quality_exclusions: list[RoutePolicyExclusion] = []
    for candidate in ranking.eligible:
        evidence = normalized_evidence.get(candidate.route_id, RoutePolicyEvidence())
        quality_interval = _quality_interval(evidence, candidate.route_id,
                                             normalized_policy.minimum_verified_samples)
        if quality_floor is not None and (quality_interval is None or quality_interval[0] < quality_floor):
            has_quality = quality_interval is not None
            reason = "quality_floor_not_met" if has_quality else "quality_evidence_insufficient"
            quality_exclusions.append(RoutePolicyExclusion(candidate.route_id, reason))
        else:
            eligible.append(candidate)

    if not eligible:
        return RoutePolicyRanking((), ranking.exclusions, tuple(sorted(quality_exclusions,
                                                                       key=lambda item: item.route_id)), None,
                                  normalized_policy.version, "quality_floor_no_supported_route")

    cost_scales = {evidence.relative_cost_scale for candidate in eligible
                   if (evidence := normalized_evidence.get(candidate.route_id, RoutePolicyEvidence())).relative_cost
                   is not None}
    cost_is_comparable = len(cost_scales) == 1 and all(
        (evidence := normalized_evidence.get(candidate.route_id, RoutePolicyEvidence())).relative_cost is not None and
        evidence.relative_cost_scale in cost_scales for candidate in eligible
    )
    quality_is_comparable = _quality_objective_is_comparable(eligible, normalized_evidence, normalized_policy)
    eligible.sort(key=lambda candidate: _route_objective_key(
        candidate, normalized_evidence.get(candidate.route_id, RoutePolicyEvidence()), normalized_policy,
        quality_is_comparable, cost_is_comparable,
    ))
    return RoutePolicyRanking(tuple(eligible), ranking.exclusions, tuple(sorted(quality_exclusions,
                                                                                 key=lambda item: item.route_id)),
                              eligible[0], normalized_policy.version, None)


def _quality_interval(evidence: RoutePolicyEvidence, route_id: str, minimum_samples: int
                      ) -> tuple[float, float] | None:
    assessment = evidence.quality_assessment
    if not isinstance(assessment, ContextualHistoryAssessment) or assessment.schema_version != API_VERSION or \
            assessment.route_id != route_id or assessment.selected_level not in HISTORY_LEVELS or \
            not _is_count(assessment.minimum_verified_samples) or assessment.minimum_verified_samples < minimum_samples or \
            not isinstance(assessment.measurements, tuple):
        return None
    selected = [item for item in assessment.measurements
                if isinstance(item, PerformanceMeasurement) and item.level == assessment.selected_level]
    if len(selected) != 1:
        return None
    measurement = selected[0]
    interval = measurement.uncertainty_interval_95
    if measurement.schema_version != API_VERSION or measurement.source_quality != "observed" or \
            not _is_count(measurement.verified_samples) or measurement.verified_samples < minimum_samples or \
            not _is_count(measurement.verified_successes) or not _is_count(measurement.verified_failures) or \
            measurement.verified_successes + measurement.verified_failures != measurement.verified_samples or \
            not isinstance(interval, tuple) or len(interval) != 2 or \
            not _finite_in_range(interval[0], 0, 1) or not _finite_in_range(interval[1], interval[0], 1):
        return None
    return interval


def _quality_objective_is_comparable(candidates: tuple[Candidate, ...] | list[Candidate],
                                     evidence_by_route: Mapping[str, RoutePolicyEvidence],
                                     policy: RoutePolicyConfig) -> bool:
    selected_levels: set[str] = set()
    for candidate in candidates:
        evidence = evidence_by_route.get(candidate.route_id, RoutePolicyEvidence())
        assessment = evidence.quality_assessment
        if _quality_interval(evidence, candidate.route_id, policy.minimum_verified_samples) is None or \
                not isinstance(assessment, ContextualHistoryAssessment):
            return False
        selected_levels.add(assessment.selected_level)
    return len(selected_levels) == 1


def _route_objective_key(candidate: Candidate, evidence: RoutePolicyEvidence, policy: RoutePolicyConfig,
                         quality_is_comparable: bool, cost_is_comparable: bool) -> tuple[object, ...]:
    quality_interval = _quality_interval(evidence, candidate.route_id, policy.minimum_verified_samples)
    if quality_is_comparable and quality_interval is not None:
        quality_lower, quality_upper = quality_interval
        quality_key = (0, -quality_lower, quality_upper - quality_lower)
    else:
        quality_key = (0, 0.0, 0.0)

    pressure = max((window.used_percent for window in evidence.quota_windows),
                   default=candidate.quota_used_percent if candidate.quota_used_percent is not None else math.inf)
    measured_duration = candidate.history.median_duration_seconds if candidate.history.duration_samples else None
    duration = evidence.duration_seconds if evidence.duration_seconds is not None else \
        measured_duration if measured_duration is not None else math.inf
    relative_cost = evidence.relative_cost if cost_is_comparable and evidence.relative_cost is not None else math.inf
    if evidence.quota_windows:
        limiting_pressure = max(window.used_percent for window in evidence.quota_windows)
        reset_soon = any(window.used_percent == limiting_pressure and window.seconds_to_reset is not None and
                         window.seconds_to_reset <= policy.upcoming_reset_window_seconds
                         for window in evidence.quota_windows)
    else:
        reset_soon = False
    return (
        *quality_key,
        pressure,
        duration,
        relative_cost,
        evidence.reserved_for_higher_risk,
        not reset_soon,
        candidate.baseline_rank is None,
        candidate.baseline_rank if candidate.baseline_rank is not None else 0,
        candidate.route_id,
    )


def deterministic_reference(request: object) -> Candidate | None:
    """Return the router's first eligible route, or `None` when hard filters leave no candidate."""
    return rank_candidates(request).selected
