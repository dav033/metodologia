"""Conservative historical measurements for route comparison."""
from __future__ import annotations

import math
import re
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .contracts import (
    API_VERSION,
    COMPLEXITY_VALUES,
    LEVEL_VALUES,
    SCOPE_VALUES,
    DecisionInputError,
    RouteHistory,
    ValidatedRequest,
)
from .performance_events import PerformanceEvent, reduce_performance_events
from .validation import validate_request

MIN_VERIFIED_SAMPLES = 5
PRIOR_SUCCESS = 2
PRIOR_FAILURE = 2
MAX_PERFORMANCE_CONTEXTS = 100_000
PERFORMANCE_HISTORY_VERSION = API_VERSION
HISTORY_LEVELS = ("exact_context", "complexity_class", "task_family", "route")
FALLBACK_REASON_CODES = (
    "exact_context_incomplete", "exact_context_missing", "exact_context_no_verified_samples", "exact_context_sparse",
    "complexity_class_unavailable", "complexity_class_missing", "complexity_class_no_verified_samples",
    "complexity_class_sparse", "task_family_unavailable", "task_family_missing",
    "task_family_no_verified_samples", "task_family_sparse", "route_missing", "route_no_verified_samples",
    "route_sparse",
)
_SAFE_FAMILY = re.compile(r"[a-z][a-z0-9_-]{0,63}\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_CONTEXT_FIELDS = {"schema_version", "task_family", "complexity", "scope", "risk", "coupling"}


class PerformanceHistoryError(ValueError):
    """Stable input error; issues name fields only and never include external values."""

    code = "performance_history_invalid"

    def __init__(self, issues: Sequence[str]):
        self.issues = tuple(sorted(set(issues)))
        super().__init__(f"{self.code}: {', '.join(self.issues[:8])}")


def _context_text(value: object, field: str, allowed: tuple[str, ...] | None = None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise PerformanceHistoryError((f"context.{field}:text_required",))
    normalized = unicodedata.normalize("NFC", value.strip().lower())
    try:
        normalized.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise PerformanceHistoryError((f"context.{field}:invalid_unicode",)) from exc
    valid = normalized in allowed if allowed is not None else _SAFE_FAMILY.fullmatch(normalized) is not None
    if not valid:
        raise PerformanceHistoryError((f"context.{field}:value_invalid",))
    return normalized


@dataclass(frozen=True)
class PerformanceContext:
    """Allowlisted task dimensions used to group observations without retaining task text."""

    task_family: str | None = None
    complexity: str | None = None
    scope: str | None = None
    risk: str | None = None
    coupling: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": PERFORMANCE_HISTORY_VERSION,
            "task_family": self.task_family,
            "complexity": self.complexity,
            "scope": self.scope,
            "risk": self.risk,
            "coupling": self.coupling,
        }

    @classmethod
    def from_dict(cls, data: object) -> PerformanceContext:
        if not isinstance(data, Mapping) or set(data) != _CONTEXT_FIELDS or \
                any(not isinstance(key, str) for key in data):
            raise PerformanceHistoryError(("context:shape_invalid",))
        if data["schema_version"] != PERFORMANCE_HISTORY_VERSION:
            raise PerformanceHistoryError(("context.schema_version:unsupported",))
        return cls(
            _context_text(data["task_family"], "task_family"),
            _context_text(data["complexity"], "complexity", COMPLEXITY_VALUES),
            _context_text(data["scope"], "scope", SCOPE_VALUES),
            _context_text(data["risk"], "risk", LEVEL_VALUES),
            _context_text(data["coupling"], "coupling", LEVEL_VALUES),
        )

    @property
    def exact_context_available(self) -> bool:
        return all(value is not None for value in
                   (self.task_family, self.complexity, self.scope, self.risk, self.coupling))


@dataclass(frozen=True)
class PerformanceMeasurement:
    """Descriptive bucket counts; intervals summarize observed outcomes, not future success probability."""

    schema_version: str
    level: str
    attempt_count: int
    verified_samples: int
    verified_successes: int
    verified_failures: int
    claimed_unverified: int
    cancelled: int
    infrastructure_failures: int
    unknown: int
    coverage: float | None
    observed_rate: float | None
    uncertainty_interval_95: tuple[float, float] | None
    shrunk_feature: float | None
    source_quality: str

    def to_dict(self) -> dict[str, object]:
        interval = list(self.uncertainty_interval_95) if self.uncertainty_interval_95 is not None else None
        return {
            "schema_version": self.schema_version,
            "level": self.level,
            "attempt_count": self.attempt_count,
            "verified_samples": self.verified_samples,
            "verified_successes": self.verified_successes,
            "verified_failures": self.verified_failures,
            "claimed_unverified": self.claimed_unverified,
            "cancelled": self.cancelled,
            "infrastructure_failures": self.infrastructure_failures,
            "unknown": self.unknown,
            "coverage": self.coverage,
            "observed_rate": self.observed_rate,
            "uncertainty_interval_95": interval,
            "shrunk_feature": self.shrunk_feature,
            "source_quality": self.source_quality,
        }


@dataclass(frozen=True)
class ContextualHistoryAssessment:
    """Context hierarchy and the conservative level that can inform a route-ranking feature."""

    schema_version: str
    route_id: str
    minimum_verified_samples: int
    measurements: tuple[PerformanceMeasurement, ...]
    selected_level: str
    selected_shrunk_feature: float | None
    fallback_reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "route_id": self.route_id,
            "minimum_verified_samples": self.minimum_verified_samples,
            "measurements": [item.to_dict() for item in self.measurements],
            "selected_level": self.selected_level,
            "selected_shrunk_feature": self.selected_shrunk_feature,
            "fallback_reasons": list(self.fallback_reasons),
        }


@dataclass
class _OutcomeCounts:
    attempt_count: int = 0
    verified_successes: int = 0
    verified_failures: int = 0
    claimed_unverified: int = 0
    cancelled: int = 0
    infrastructure_failures: int = 0
    unknown: int = 0

    def add(self, outcome: str) -> None:
        self.attempt_count += 1
        if outcome == "pass":
            self.verified_successes += 1
        elif outcome == "fail":
            self.verified_failures += 1
        elif outcome == "claimed_unverified":
            self.claimed_unverified += 1
        elif outcome == "cancelled":
            self.cancelled += 1
        elif outcome == "infrastructure_failure":
            self.infrastructure_failures += 1
        else:
            self.unknown += 1


def _wilson_interval(successes: int, samples: int) -> tuple[float, float] | None:
    if samples == 0:
        return None
    z = 1.959963984540054
    rate = successes / samples
    denominator = 1 + z * z / samples
    center = (rate + z * z / (2 * samples)) / denominator
    margin = z * math.sqrt(rate * (1 - rate) / samples + z * z / (4 * samples * samples)) / denominator
    return max(0.0, center - margin), min(1.0, center + margin)


def _measurement(level: str, counts: _OutcomeCounts) -> PerformanceMeasurement:
    samples = counts.verified_successes + counts.verified_failures
    rate = counts.verified_successes / samples if samples else None
    coverage = samples / counts.attempt_count if counts.attempt_count else None
    quality = "observed" if samples >= MIN_VERIFIED_SAMPLES else "sparse" if samples else "unknown"
    shrunk = (counts.verified_successes + PRIOR_SUCCESS) / \
        (samples + PRIOR_SUCCESS + PRIOR_FAILURE) if samples else None
    return PerformanceMeasurement(
        PERFORMANCE_HISTORY_VERSION, level, counts.attempt_count, samples, counts.verified_successes,
        counts.verified_failures, counts.claimed_unverified, counts.cancelled, counts.infrastructure_failures,
        counts.unknown, coverage, rate, _wilson_interval(counts.verified_successes, samples), shrunk, quality,
    )


def _context_from(value: object, path: str) -> PerformanceContext:
    if not isinstance(value, PerformanceContext):
        raise PerformanceHistoryError((f"{path}:context_required",))
    return PerformanceContext.from_dict(value.to_dict())


def _validated_contexts(contexts: Mapping[tuple[str, int, str], PerformanceContext]
                        ) -> dict[tuple[str, int, str], PerformanceContext]:
    if not isinstance(contexts, Mapping) or len(contexts) > MAX_PERFORMANCE_CONTEXTS:
        raise PerformanceHistoryError(("contexts:collection_invalid",))
    result: dict[tuple[str, int, str], PerformanceContext] = {}
    for key, value in contexts.items():
        if not isinstance(key, tuple) or len(key) != 3 or not isinstance(key[1], int) or isinstance(key[1], bool) or \
                key[1] < 1 or not all(isinstance(item, str) and item.strip() for item in (key[0], key[2])):
            raise PerformanceHistoryError(("contexts:identity_invalid",))
        normalized_key = (unicodedata.normalize("NFC", key[0].strip()), key[1],
                          unicodedata.normalize("NFC", key[2].strip()))
        if normalized_key in result:
            raise PerformanceHistoryError(("contexts:duplicate_identity",))
        result[normalized_key] = _context_from(value, "contexts.item")
    return result


def _attempt_outcomes(events: Sequence[PerformanceEvent]) -> tuple[tuple[tuple[str, int, str, str], str | None, str], ...]:
    grouped: dict[tuple[str, int, str, str], list[PerformanceEvent]] = {}
    for event in reduce_performance_events(events):
        key = (event.plan_id, event.revision, event.task_id, event.attempt_id)
        grouped.setdefault(key, []).append(event)
    result = []
    for key in sorted(grouped):
        rows = grouped[key]
        eligible = [item for item in rows if item.eligible_for_history and item.outcome in ("pass", "fail")]
        if len(eligible) == 1:
            result.append((key, eligible[0].route_id, eligible[0].outcome))
            continue
        routes = {item.route_id for item in rows}
        route_id = next(iter(routes)) if len(routes) == 1 and None not in routes else None
        outcomes = {item.outcome if item.outcome not in ("pass", "fail") else "unknown" for item in rows}
        result.append((key, route_id, next(iter(outcomes)) if len(outcomes) == 1 else "unknown"))
    return tuple(result)


def _fallback_reason(level: str, measurement: PerformanceMeasurement) -> str:
    if measurement.verified_samples:
        return f"{level}_sparse"
    if measurement.attempt_count:
        return f"{level}_no_verified_samples"
    return f"{level}_missing"


def aggregate_performance_history(
    events: Sequence[PerformanceEvent],
    contexts: Mapping[tuple[str, int, str], PerformanceContext],
    *,
    route_id: str,
    target_context: PerformanceContext,
) -> ContextualHistoryAssessment:
    """Aggregate only unique, correlated PASS/FAIL facts and expose a deterministic sparse-data fallback."""
    if not isinstance(route_id, str) or not _SHA256.fullmatch(route_id):
        raise PerformanceHistoryError(("route_id:sha256_invalid",))
    target = _context_from(target_context, "target_context")
    known_contexts = _validated_contexts(contexts)
    accumulators = {level: _OutcomeCounts() for level in HISTORY_LEVELS}
    attempts = _attempt_outcomes(events)
    for identity, observed_route, outcome in attempts:
        if observed_route != route_id:
            continue
        context = known_contexts.get(identity[:3])
        accumulators["route"].add(outcome)
        if context is None:
            continue
        if target.exact_context_available and context.exact_context_available and \
                (context.task_family, context.complexity, context.scope, context.risk, context.coupling) == \
                (target.task_family, target.complexity, target.scope, target.risk, target.coupling):
            accumulators["exact_context"].add(outcome)
        if target.complexity is not None and context.complexity == target.complexity:
            accumulators["complexity_class"].add(outcome)
        if target.task_family is not None and context.task_family == target.task_family:
            accumulators["task_family"].add(outcome)

    measurements = tuple(_measurement(level, accumulators[level]) for level in HISTORY_LEVELS)
    by_level = {item.level: item for item in measurements}
    availability = {
        "exact_context": target.exact_context_available,
        "complexity_class": target.complexity is not None,
        "task_family": target.task_family is not None,
        "route": True,
    }
    selected_level = "baseline"
    fallback_reasons: list[str] = []
    selected_feature = None
    for level in HISTORY_LEVELS:
        if not availability[level]:
            fallback_reasons.append("exact_context_incomplete" if level == "exact_context" else
                                    f"{level}_unavailable")
            continue
        measurement = by_level[level]
        if measurement.verified_samples >= MIN_VERIFIED_SAMPLES:
            selected_level = level
            selected_feature = measurement.shrunk_feature
            break
        fallback_reasons.append(_fallback_reason(level, measurement))
    return ContextualHistoryAssessment(
        PERFORMANCE_HISTORY_VERSION, route_id, MIN_VERIFIED_SAMPLES, measurements, selected_level,
        selected_feature, tuple(fallback_reasons),
    )


@dataclass(frozen=True)
class HistoryAssessment:
    """Observed measurements; `shrunk_verified_score` is a ranking feature, not a success probability."""

    source_quality: str
    verified_samples: int
    verified_rate: float | None
    shrunk_verified_score: float | None
    sample_weight: float
    duration_samples: int
    median_duration_seconds: float | None
    token_samples: int
    median_total_tokens: int | None
    factor_codes: tuple[str, ...]


def _assess_validated_history(history: RouteHistory) -> HistoryAssessment:
    verified = history.verified_successes + history.verified_failures
    if verified:
        rate = history.verified_successes / verified
        score = (history.verified_successes + PRIOR_SUCCESS) / (verified + PRIOR_SUCCESS + PRIOR_FAILURE)
        weight = verified / (verified + PRIOR_SUCCESS + PRIOR_FAILURE)
        quality_factor = "history_observed" if verified >= MIN_VERIFIED_SAMPLES else "history_sparse"
    else:
        rate = score = None
        weight = 0.0
        quality_factor = "history_no_verified_samples"
    factors = [quality_factor]
    if history.duration_samples:
        factors.append("duration_measured")
    if history.token_samples:
        factors.append("tokens_measured")
    return HistoryAssessment(
        source_quality=history.source_quality,
        verified_samples=verified,
        verified_rate=rate,
        shrunk_verified_score=score,
        sample_weight=weight,
        duration_samples=history.duration_samples,
        median_duration_seconds=history.median_duration_seconds,
        token_samples=history.token_samples,
        median_total_tokens=history.median_total_tokens,
        factor_codes=tuple(factors),
    )


def assess_history(request: object, route_id: str) -> HistoryAssessment:
    """Validate the request, then score one route's observed history without counting unverified claims."""
    raw_request = request.request if isinstance(request, ValidatedRequest) else request
    validated = validate_request(raw_request)
    candidate = next((item for item in validated.request.candidates if item.route_id == route_id), None)
    if candidate is None:
        raise DecisionInputError(["candidate:not_found"])
    return _assess_validated_history(candidate.history)
