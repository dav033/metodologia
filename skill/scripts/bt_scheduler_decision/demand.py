"""Conservative, unit-separated provider usage and quota demand estimates."""
from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from statistics import median, median_low
from typing import Literal

from .contracts import API_VERSION, DecisionInputError
from .quota import QuotaObservation

DemandState = Literal["observed", "estimated", "unknown"]
DemandUnit = Literal["provider_tokens", "quota_percentage_points"]
DEMAND_UNITS = ("provider_tokens", "quota_percentage_points")
DEMAND_REASONS = (
    "provider_usage_missing", "invalid_provider_usage", "attribution_unknown", "identity_mismatch",
    "unknown_window", "stale_observation", "no_comparable_samples", "stale_samples", "future_sample",
)
TOKEN_SOURCES = {
    "claude": frozenset({"claude-stream-json"}),
    "codex": frozenset({"codex-exec-json", "codex-exec-text"}),
    "antigravity": frozenset({"agy-stream-json"}),
}
QUOTA_DELTA_SOURCE = "quota_observation_delta"
MAX_PROVIDER_TOKENS = 1_000_000_000_000
MAX_DEMAND_SAMPLES = 1000
MAX_SAMPLE_AGE_SECONDS = 31_536_000
MAX_ESTIMATE_TTL_SECONDS = 86_400
_ACCOUNT_REF = re.compile(r"^acct:[0-9a-f]{64}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")


@dataclass(frozen=True)
class DemandEstimate:
    """One usage value with its unit, provenance, sample count, interval and bounded freshness."""

    state: DemandState
    provider: str
    account_ref: str
    model: str
    window_id: str | None
    context_ref: str
    unit: DemandUnit
    value: int | float | None
    lower_bound: int | float | None
    upper_bound: int | float | None
    sample_count: int
    source: str
    observed_at: float | None
    computed_at: float | None
    valid_until: float | None
    reason_code: str | None
    schema_version: str = API_VERSION

    def to_dict(self) -> dict[str, str | int | float | None]:
        return {
            "schema_version": self.schema_version,
            "state": self.state,
            "provider": self.provider,
            "account_ref": self.account_ref,
            "model": self.model,
            "window_id": self.window_id,
            "context_ref": self.context_ref,
            "unit": self.unit,
            "value": self.value,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "sample_count": self.sample_count,
            "source": self.source,
            "observed_at": self.observed_at,
            "computed_at": self.computed_at,
            "valid_until": self.valid_until,
            "reason_code": self.reason_code,
        }

    @classmethod
    def from_dict(cls, value: object) -> DemandEstimate:
        required = {
            "schema_version", "state", "provider", "account_ref", "model", "window_id", "context_ref", "unit",
            "value", "lower_bound", "upper_bound", "sample_count", "source", "observed_at", "computed_at",
            "valid_until", "reason_code",
        }
        if not isinstance(value, Mapping) or len(value) != len(required) or set(value) != required:
            raise DecisionInputError(("demand_estimate.fields",))
        try:
            result = cls(**value)
        except TypeError as exc:
            raise DecisionInputError(("demand_estimate.fields",)) from exc
        _validate_estimate(result)
        return result


@dataclass(frozen=True)
class DemandSample:
    """A deduplicable, attributable observation eligible for an exact-context estimate."""

    sample_id: str
    provider: str
    account_ref: str
    model: str
    window_id: str | None
    context_ref: str
    unit: DemandUnit
    value: int | float
    source: str
    observed_at: float
    attribution: str
    schema_version: str = API_VERSION

    def to_dict(self) -> dict[str, str | int | float | None]:
        return {
            "sample_id": self.sample_id,
            "provider": self.provider,
            "account_ref": self.account_ref,
            "model": self.model,
            "window_id": self.window_id,
            "context_ref": self.context_ref,
            "unit": self.unit,
            "value": self.value,
            "source": self.source,
            "observed_at": self.observed_at,
            "attribution": self.attribution,
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, value: object) -> DemandSample:
        if not isinstance(value, Mapping):
            raise DecisionInputError(("demand_sample",))
        required = {
            "sample_id", "provider", "account_ref", "model", "window_id", "context_ref", "unit", "value",
            "source", "observed_at", "attribution", "schema_version",
        }
        if len(value) != len(required) or set(value) != required:
            raise DecisionInputError(("demand_sample.fields",))
        sample = cls(**value)
        _validate_sample(sample)
        return sample

    @classmethod
    def from_estimate(cls, sample_id: str, estimate: DemandEstimate) -> DemandSample:
        if not isinstance(estimate, DemandEstimate):
            raise DecisionInputError(("demand_sample.source_estimate",))
        estimate = DemandEstimate.from_dict(estimate.to_dict())
        if (estimate.state != "observed" or estimate.value is None or estimate.observed_at is None or
                not isinstance(sample_id, str) or _SHA256.fullmatch(sample_id) is None):
            raise DecisionInputError(("demand_sample.source_estimate",))
        attribution = "provider_reported" if estimate.unit == "provider_tokens" else "account_window_attributed"
        sample = cls(sample_id, estimate.provider, estimate.account_ref, estimate.model, estimate.window_id,
                     estimate.context_ref, estimate.unit, estimate.value, estimate.source, estimate.observed_at,
                     attribution)
        _validate_sample(sample)
        return sample


def _number(value: object) -> float | None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    try:
        result = float(value)
    except OverflowError:
        return None
    return result if math.isfinite(result) else None


def _valid_identity(provider: object, account_ref: object, model: object, context_ref: object) -> bool:
    return (
        isinstance(provider, str) and provider in TOKEN_SOURCES and
        isinstance(account_ref, str) and _ACCOUNT_REF.fullmatch(account_ref) is not None and
        isinstance(model, str) and _TOKEN.fullmatch(model) is not None and
        isinstance(context_ref, str) and _SHA256.fullmatch(context_ref) is not None
    )


def _valid_source(provider: str, unit: str, source: object) -> bool:
    if unit == "provider_tokens":
        return isinstance(source, str) and source in TOKEN_SOURCES[provider]
    return unit == "quota_percentage_points" and isinstance(source, str) and source == QUOTA_DELTA_SOURCE


def _validate_unit_window(unit: object, window_id: object) -> bool:
    if unit == "provider_tokens":
        return window_id is None
    return unit == "quota_percentage_points" and isinstance(window_id, str) and _TOKEN.fullmatch(window_id) is not None


def _validate_sample(sample: DemandSample) -> None:
    if not isinstance(sample, DemandSample):
        raise DecisionInputError(("demand_sample",))
    expected_attribution = "provider_reported" if sample.unit == "provider_tokens" else "account_window_attributed"
    if (sample.schema_version != API_VERSION or not isinstance(sample.sample_id, str) or
            _SHA256.fullmatch(sample.sample_id) is None or
            not _valid_identity(sample.provider, sample.account_ref, sample.model, sample.context_ref) or
            sample.unit not in DEMAND_UNITS or not _validate_unit_window(sample.unit, sample.window_id) or
            not _valid_source(sample.provider, sample.unit, sample.source) or
            sample.attribution != expected_attribution):
        raise DecisionInputError(("demand_sample",))
    observed = _number(sample.observed_at)
    value = _number(sample.value)
    if observed is None or observed < 0 or value is None or value < 0:
        raise DecisionInputError(("demand_sample.value",))
    if sample.unit == "provider_tokens":
        if not isinstance(sample.value, int) or isinstance(sample.value, bool) or sample.value > MAX_PROVIDER_TOKENS:
            raise DecisionInputError(("demand_sample.provider_tokens",))
    elif value > 100:
        raise DecisionInputError(("demand_sample.quota_percentage_points",))


def _validate_estimate(estimate: DemandEstimate) -> None:
    if not isinstance(estimate, DemandEstimate) or estimate.schema_version != API_VERSION or \
            estimate.state not in ("observed", "estimated", "unknown") or \
            not _valid_identity(estimate.provider, estimate.account_ref, estimate.model, estimate.context_ref) or \
            estimate.unit not in DEMAND_UNITS or not _validate_unit_window(estimate.unit, estimate.window_id) or \
            not _valid_source(estimate.provider, estimate.unit, estimate.source):
        raise DecisionInputError(("demand_estimate",))
    if (not isinstance(estimate.sample_count, int) or isinstance(estimate.sample_count, bool) or
            not 0 <= estimate.sample_count <= MAX_DEMAND_SAMPLES):
        raise DecisionInputError(("demand_estimate.sample_count",))
    numbers = tuple(_number(value) for value in
                    (estimate.value, estimate.lower_bound, estimate.upper_bound))
    if estimate.state == "unknown":
        if (any(value is not None for value in numbers) or estimate.sample_count != 0 or
                estimate.observed_at is not None or estimate.computed_at is not None or
                estimate.valid_until is not None or estimate.reason_code not in DEMAND_REASONS):
            raise DecisionInputError(("demand_estimate.unknown",))
        return
    value, lower, upper = numbers
    observed = _number(estimate.observed_at)
    computed = _number(estimate.computed_at)
    if (any(number is None for number in numbers) or observed is None or observed < 0 or
            computed is None or computed < observed or estimate.reason_code is not None or
            estimate.sample_count < 1 or lower is None or upper is None or not lower <= value <= upper):
        raise DecisionInputError(("demand_estimate.observed",))
    if estimate.unit == "provider_tokens":
        if any(not isinstance(number, int) or isinstance(number, bool) or number > MAX_PROVIDER_TOKENS
               for number in (estimate.value, estimate.lower_bound, estimate.upper_bound)):
            raise DecisionInputError(("demand_estimate.provider_tokens",))
    elif lower < 0 or upper > 100:
        raise DecisionInputError(("demand_estimate.quota_percentage_points",))
    if estimate.state == "observed":
        if estimate.sample_count != 1 or estimate.lower_bound != estimate.value or \
                estimate.upper_bound != estimate.value or estimate.valid_until is not None:
            raise DecisionInputError(("demand_estimate.observed",))
    else:
        valid_until = _number(estimate.valid_until)
        if (valid_until is None or valid_until <= computed or
                valid_until - computed > MAX_ESTIMATE_TTL_SECONDS):
            raise DecisionInputError(("demand_estimate.estimated",))


def _unknown(*, provider: str, account_ref: str, model: str, window_id: str | None, context_ref: str,
             unit: DemandUnit, source: str, reason: str) -> DemandEstimate:
    return DemandEstimate("unknown", provider, account_ref, model, window_id, context_ref, unit,
                          None, None, None, 0, source, None, None, None, reason)


def observed_token_usage(*, provider: str, account_ref: str, model: str, context_ref: str, source: str,
                         tokens: object, observed_at: object, now: object) -> DemandEstimate:
    """Keep provider-reported tokens as tokens; a missing or invalid field is never inferred from quota percent."""
    if not _valid_identity(provider, account_ref, model, context_ref) or not _valid_source(
            provider, "provider_tokens", source):
        raise DecisionInputError(("demand_identity",))
    clock, observed, count = _number(now), _number(observed_at), _number(tokens)
    if clock is None or clock < 0:
        raise DecisionInputError(("demand_clock",))
    if tokens is None:
        return _unknown(provider=provider, account_ref=account_ref, model=model, window_id=None,
                        context_ref=context_ref, unit="provider_tokens", source=source,
                        reason="provider_usage_missing")
    if (not isinstance(tokens, int) or isinstance(tokens, bool) or count is None or count < 0 or
            count > MAX_PROVIDER_TOKENS):
        return _unknown(provider=provider, account_ref=account_ref, model=model, window_id=None,
                        context_ref=context_ref, unit="provider_tokens", source=source,
                        reason="invalid_provider_usage")
    if observed is None or observed < 0 or observed > clock:
        return _unknown(provider=provider, account_ref=account_ref, model=model, window_id=None,
                        context_ref=context_ref, unit="provider_tokens", source=source,
                        reason="provider_usage_missing")
    return DemandEstimate("observed", provider, account_ref, model, None, context_ref, "provider_tokens",
                          tokens, tokens, tokens, 1, source, observed, clock, None, None)


def attribute_quota_delta(*, before: QuotaObservation, after: QuotaObservation, context_ref: str,
                          active_task_count: object, external_usage: object, now: object) -> DemandEstimate:
    """Attribute percentage-point changes only across one clean, unrestarted, single-task interval."""
    if not isinstance(context_ref, str) or _SHA256.fullmatch(context_ref) is None:
        raise DecisionInputError(("demand_context",))
    first = QuotaObservation.from_dict(before.to_dict()) if isinstance(before, QuotaObservation) else None
    last = QuotaObservation.from_dict(after.to_dict()) if isinstance(after, QuotaObservation) else None
    if first is None or last is None:
        raise DecisionInputError(("demand_observations",))
    clock = _number(now)
    if clock is None or clock < 0:
        raise DecisionInputError(("demand_clock",))
    unit: DemandUnit = "quota_percentage_points"
    source = QUOTA_DELTA_SOURCE
    identity = (first.provider, first.account_ref, first.model, first.window_id, first.source)
    after_identity = (last.provider, last.account_ref, last.model, last.window_id, last.source)
    if identity != after_identity:
        return _unknown(provider=first.provider, account_ref=first.account_ref, model=first.model,
                        window_id=first.window_id, context_ref=context_ref, unit=unit, source=source,
                        reason="identity_mismatch")
    if (not isinstance(active_task_count, int) or isinstance(active_task_count, bool) or active_task_count != 1 or
            external_usage is not False):
        return _unknown(provider=first.provider, account_ref=first.account_ref, model=first.model,
                        window_id=first.window_id, context_ref=context_ref, unit=unit, source=source,
                        reason="attribution_unknown")
    if first.state == "stale" or last.state == "stale":
        return _unknown(provider=first.provider, account_ref=first.account_ref, model=first.model,
                        window_id=first.window_id, context_ref=context_ref, unit=unit, source=source,
                        reason="stale_observation")
    if (first.state not in {"available", "exhausted"} or last.state not in {"available", "exhausted"} or
            first.used_percent is None or last.used_percent is None):
        return _unknown(provider=first.provider, account_ref=first.account_ref, model=first.model,
                        window_id=first.window_id, context_ref=context_ref, unit=unit, source=source,
                        reason="unknown_window")
    if (first.observed_at is None or last.observed_at is None or first.valid_until is None or
            last.valid_until is None or first.observed_at >= last.observed_at or last.observed_at > clock or
            first.valid_until <= last.observed_at or last.valid_until <= last.observed_at):
        return _unknown(provider=first.provider, account_ref=first.account_ref, model=first.model,
                        window_id=first.window_id, context_ref=context_ref, unit=unit, source=source,
                        reason="stale_observation")
    if (first.resets_at is None or last.resets_at is None or first.reset_confidence != "reported" or
            last.reset_confidence != "reported" or first.resets_at != last.resets_at or
            first.resets_at <= last.observed_at):
        return _unknown(provider=first.provider, account_ref=first.account_ref, model=first.model,
                        window_id=first.window_id, context_ref=context_ref, unit=unit, source=source,
                        reason="attribution_unknown")
    delta = last.used_percent - first.used_percent
    if delta < 0:
        return _unknown(provider=first.provider, account_ref=first.account_ref, model=first.model,
                        window_id=first.window_id, context_ref=context_ref, unit=unit, source=source,
                        reason="attribution_unknown")
    return DemandEstimate("observed", first.provider, first.account_ref, first.model, first.window_id,
                          context_ref, unit, delta, delta, delta, 1, source, last.observed_at, clock, None, None)


def estimate_demand(samples: Sequence[DemandSample], *, provider: str, account_ref: str, model: str,
                    window_id: str | None, context_ref: str, unit: DemandUnit, source: str,
                    now: object, valid_for_seconds: object) -> DemandEstimate:
    """Summarize only exact-context observations; min/max are empirical bounds, not confidence intervals."""
    if (not _valid_identity(provider, account_ref, model, context_ref) or unit not in DEMAND_UNITS or
            not _validate_unit_window(unit, window_id) or not _valid_source(provider, unit, source)):
        raise DecisionInputError(("demand_identity",))
    clock, ttl = _number(now), _number(valid_for_seconds)
    if clock is None or clock < 0 or ttl is None or not 0 < ttl <= MAX_ESTIMATE_TTL_SECONDS:
        raise DecisionInputError(("demand_estimate_bounds",))
    if (not isinstance(samples, Sequence) or isinstance(samples, (str, bytes)) or
            len(samples) > MAX_DEMAND_SAMPLES):
        raise DecisionInputError(("demand_samples",))
    matching: list[DemandSample] = []
    seen_ids: set[str] = set()
    stale_count = 0
    future_match = False
    for raw in samples:
        sample = DemandSample.from_dict(raw.to_dict()) if isinstance(raw, DemandSample) else DemandSample.from_dict(raw)
        if sample.sample_id in seen_ids:
            raise DecisionInputError(("demand_sample.duplicate_id",))
        seen_ids.add(sample.sample_id)
        same_context = (sample.provider, sample.account_ref, sample.model, sample.window_id, sample.context_ref,
                        sample.unit, sample.source) == \
            (provider, account_ref, model, window_id, context_ref, unit, source)
        if not same_context:
            continue
        if sample.observed_at > clock:
            future_match = True
        elif clock - sample.observed_at > MAX_SAMPLE_AGE_SECONDS:
            stale_count += 1
        else:
            matching.append(sample)
    if future_match:
        return _unknown(provider=provider, account_ref=account_ref, model=model, window_id=window_id,
                        context_ref=context_ref, unit=unit, source=source, reason="future_sample")
    if not matching:
        reason = "stale_samples" if stale_count else "no_comparable_samples"
        return _unknown(provider=provider, account_ref=account_ref, model=model, window_id=window_id,
                        context_ref=context_ref, unit=unit, source=source, reason=reason)
    values = [sample.value for sample in matching]
    middle = median_low(values) if unit == "provider_tokens" else median(values)
    valid_until = _number(clock + ttl)
    if valid_until is None:
        raise DecisionInputError(("demand_estimate_bounds",))
    return DemandEstimate("estimated", provider, account_ref, model, window_id, context_ref, unit,
                          middle, min(values), max(values), len(matching), source,
                          max(sample.observed_at for sample in matching), clock, valid_until, None)
