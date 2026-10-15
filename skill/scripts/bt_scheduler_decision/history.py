"""Conservative historical measurements for route comparison."""
from __future__ import annotations

from dataclasses import dataclass

from .contracts import DecisionInputError, RouteHistory, ValidatedRequest
from .validation import validate_request

MIN_VERIFIED_SAMPLES = 5
PRIOR_SUCCESS = 2
PRIOR_FAILURE = 2


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
