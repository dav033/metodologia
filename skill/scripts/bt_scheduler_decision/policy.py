"""Deterministic candidate eligibility and reference ordering."""
from __future__ import annotations

from dataclasses import dataclass

from .contracts import Candidate, Exclusion, ValidatedRequest
from .validation import validate_request

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


def deterministic_reference(request: object) -> Candidate | None:
    """Return the router's first eligible route, or `None` when hard filters leave no candidate."""
    return rank_candidates(request).selected
