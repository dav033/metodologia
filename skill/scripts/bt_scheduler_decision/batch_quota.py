"""Quota window assessment for batches, independent of task-route matching."""
from __future__ import annotations

import math
import re
from collections.abc import Sequence
from dataclasses import dataclass

from .contracts import API_VERSION, DecisionInputError
from .quota import (
    MAX_OBSERVATIONS,
    MAX_REQUIRED_WINDOWS,
    QUOTA_PROVIDERS,
    QuotaAssessment,
    QuotaObservation,
    assess_account_windows,
)

MAX_BATCH_ROUTES = 256
_ACCOUNT_REF = re.compile(r"^acct:[0-9a-f]{64}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")


@dataclass(frozen=True)
class RouteQuotaRequirement:
    """Quota windows required by one candidate route; aliases share account_ref, not budget rows."""

    route_id: str
    provider: str
    account_ref: str
    required_windows: tuple[tuple[str | None, str], ...]
    schema_version: str = API_VERSION


@dataclass(frozen=True)
class BatchRouteQuotaAssessment:
    route_id: str
    account_ref: str
    assessment: QuotaAssessment
    schema_version: str = API_VERSION

    @property
    def eligible(self) -> bool:
        return self.assessment.state == "available"


@dataclass(frozen=True)
class BatchQuotaAssessment:
    schema_version: str
    unique_account_count: int
    routes: tuple[BatchRouteQuotaAssessment, ...]

    @property
    def eligible_route_ids(self) -> tuple[str, ...]:
        return tuple(row.route_id for row in self.routes if row.eligible)

    @property
    def excluded_route_ids(self) -> tuple[str, ...]:
        return tuple(row.route_id for row in self.routes if not row.eligible)


def assess_batch_quota(requirements: Sequence[RouteQuotaRequirement], observations: Sequence[QuotaObservation], *,
                       now: object) -> BatchQuotaAssessment:
    """Assess routes against current account windows without summing aliases or reserving capacity."""
    clock = _number(now)
    if (clock is None or clock < 0 or not isinstance(requirements, Sequence) or
            isinstance(requirements, (str, bytes)) or not 1 <= len(requirements) <= MAX_BATCH_ROUTES or
            not isinstance(observations, Sequence) or isinstance(observations, (str, bytes)) or
            len(observations) > MAX_OBSERVATIONS):
        raise DecisionInputError(("batch_quota",))
    normalized = tuple(_validate_requirement(row) for row in requirements)
    route_ids = tuple(row.route_id for row in normalized)
    if len(set(route_ids)) != len(route_ids):
        raise DecisionInputError(("batch_quota.duplicate_route",))
    grouped: dict[tuple[str, str, tuple[tuple[str | None, str], ...]], list[str]] = {}
    for row in normalized:
        key = (row.provider, row.account_ref, tuple(sorted(row.required_windows, key=lambda item: (item[0] or "", item[1]))))
        grouped.setdefault(key, []).append(row.route_id)
    results: dict[str, BatchRouteQuotaAssessment] = {}
    for (provider, account_ref, windows), grouped_routes in grouped.items():
        required_by_model: dict[str | None, list[str]] = {}
        for model, window_id in windows:
            required_by_model.setdefault(model, []).append(window_id)
        assessment = assess_account_windows(
            observations, account_ref=account_ref, provider=provider,
            required_windows={model: tuple(names) for model, names in required_by_model.items()}, now=clock,
        )
        for route_id in grouped_routes:
            results[route_id] = BatchRouteQuotaAssessment(route_id, account_ref, assessment)
    ordered_results = tuple(results[route_id] for route_id in sorted(results))
    unique_accounts = len({(row.provider, row.account_ref) for row in normalized})
    return BatchQuotaAssessment(API_VERSION, unique_accounts, ordered_results)


def _validate_requirement(value: object) -> RouteQuotaRequirement:
    if not isinstance(value, RouteQuotaRequirement):
        raise DecisionInputError(("batch_quota.requirement",))
    if (value.schema_version != API_VERSION or not isinstance(value.route_id, str) or
            _SHA256.fullmatch(value.route_id) is None or not isinstance(value.provider, str) or
            value.provider not in QUOTA_PROVIDERS or not isinstance(value.account_ref, str) or
            _ACCOUNT_REF.fullmatch(value.account_ref) is None or
            not isinstance(value.required_windows, Sequence) or isinstance(value.required_windows, (str, bytes)) or
            not 1 <= len(value.required_windows) <= MAX_REQUIRED_WINDOWS):
        raise DecisionInputError(("batch_quota.requirement",))
    normalized: list[tuple[str | None, str]] = []
    for key in value.required_windows:
        if (not isinstance(key, tuple) or len(key) != 2 or
                key[0] is not None and (not isinstance(key[0], str) or not _TOKEN.fullmatch(key[0])) or
                not isinstance(key[1], str) or not _TOKEN.fullmatch(key[1])):
            raise DecisionInputError(("batch_quota.windows",))
        normalized.append((key[0], key[1]))
    if len(set(normalized)) != len(normalized):
        raise DecisionInputError(("batch_quota.duplicate_window",))
    return RouteQuotaRequirement(value.route_id, value.provider, value.account_ref, tuple(normalized))


def _number(value: object) -> float | None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    try:
        result = float(value)
    except OverflowError:
        return None
    return result if math.isfinite(result) else None
