"""Versioned account/window observations normalized from already cached quota data."""
from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

from .contracts import API_VERSION, DecisionInputError

QUOTA_SCHEMA_VERSION = API_VERSION
QUOTA_STATES = ("available", "unknown", "stale", "exhausted")
RESET_CONFIDENCE = ("reported", "source_allows_unknown", "unknown")
QUOTA_SOURCES = ("subscription_cache", "antigravity_cache")
QUOTA_PROVIDERS = ("claude", "codex", "antigravity")
REASON_CODES = (
    "source_unavailable", "missing_observation", "future_observation", "stale_observation",
    "missing_required_window", "invalid_window", "reset_missing", "reset_elapsed", "window_exhausted",
    "duplicate_window", "identity_mismatch", "window_unknown",
)
MAX_REQUIRED_WINDOWS = 64
MAX_OBSERVATIONS = 4096
MAX_VALIDITY_SECONDS = 86_400
_ACCOUNT_REF = re.compile(r"^acct:[0-9a-f]{64}$")
_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
_SOURCE_BY_PROVIDER = {"claude": "subscription_cache", "codex": "subscription_cache",
                       "antigravity": "antigravity_cache"}

QuotaState = Literal["available", "unknown", "stale", "exhausted"]


@dataclass(frozen=True)
class QuotaObservation:
    """One bounded provider/model quota window; percentages never represent tokens or currency."""

    schema_version: str
    account_ref: str
    provider: str
    model: str | None
    window_id: str
    source: str
    state: QuotaState
    observed_at: float | None
    valid_until: float | None
    resets_at: float | None
    reset_confidence: str
    used_percent: float | None
    reason_code: str | None = None

    def to_dict(self) -> dict[str, str | float | None]:
        return {
            "schema_version": self.schema_version,
            "account_ref": self.account_ref,
            "provider": self.provider,
            "model": self.model,
            "window_id": self.window_id,
            "source": self.source,
            "state": self.state,
            "observed_at": self.observed_at,
            "valid_until": self.valid_until,
            "resets_at": self.resets_at,
            "reset_confidence": self.reset_confidence,
            "used_percent": self.used_percent,
            "reason_code": self.reason_code,
        }

    @classmethod
    def from_dict(cls, value: object) -> QuotaObservation:
        if not isinstance(value, Mapping):
            raise DecisionInputError(("quota_observation",))
        required = {
            "schema_version", "account_ref", "provider", "model", "window_id", "source", "state",
            "observed_at", "valid_until", "resets_at", "reset_confidence", "used_percent", "reason_code",
        }
        if len(value) != len(required) or set(value) != required:
            raise DecisionInputError(("quota_observation.fields",))
        result = _build_observation(
            schema_version=value.get("schema_version"), account_ref=value.get("account_ref"),
            provider=value.get("provider"), model=value.get("model"), window_id=value.get("window_id"),
            source=value.get("source"), state=value.get("state"), observed_at=value.get("observed_at"),
            valid_until=value.get("valid_until"), resets_at=value.get("resets_at"),
            reset_confidence=value.get("reset_confidence"), used_percent=value.get("used_percent"),
            reason_code=value.get("reason_code"),
        )
        return result


@dataclass(frozen=True)
class QuotaAssessment:
    """Strict result across every caller-declared relevant window for one effective account."""

    state: QuotaState
    pressure_percent: float | None
    checked_windows: tuple[str, ...]
    unavailable_windows: tuple[str, ...]
    exhausted_windows: tuple[str, ...]
    reason_code: str | None


def _number(value: object) -> float | None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    try:
        result = float(value)
    except OverflowError:
        return None
    return result if math.isfinite(result) else None


def _text(value: object, pattern: re.Pattern[str]) -> str | None:
    return value if isinstance(value, str) and pattern.fullmatch(value) else None


def _build_observation(*, schema_version: object, account_ref: object, provider: object, model: object,
                       window_id: object, source: object, state: object, observed_at: object,
                       valid_until: object, resets_at: object, reset_confidence: object,
                       used_percent: object, reason_code: object) -> QuotaObservation:
    account = _text(account_ref, _ACCOUNT_REF)
    provider_text = provider if isinstance(provider, str) and provider in QUOTA_PROVIDERS else None
    model_text = None if model is None else _text(model, _TOKEN)
    window = _text(window_id, _TOKEN)
    source_text = source if isinstance(source, str) and source in QUOTA_SOURCES else None
    state_text = state if isinstance(state, str) and state in QUOTA_STATES else None
    reset_text = reset_confidence if isinstance(reset_confidence, str) and reset_confidence in RESET_CONFIDENCE else None
    observed = None if observed_at is None else _number(observed_at)
    expires = None if valid_until is None else _number(valid_until)
    reset = None if resets_at is None else _number(resets_at)
    percent = None if used_percent is None else _number(used_percent)
    reason = None if reason_code is None else reason_code if isinstance(reason_code, str) and reason_code in REASON_CODES else False
    invalid = (
        schema_version != QUOTA_SCHEMA_VERSION or account is None or provider_text is None or
        (model is not None and model_text is None) or window is None or source_text is None or
        source_text != _SOURCE_BY_PROVIDER.get(provider_text) or state_text is None or
        reset_text is None or (observed_at is not None and (observed is None or observed < 0)) or
        (valid_until is not None and (expires is None or expires < 0)) or
        (resets_at is not None and (reset is None or reset < 0)) or
        (used_percent is not None and (percent is None or not 0 <= percent <= 100)) or
        (reason_code is not None and reason is False) or
        (observed is not None and expires is not None and expires <= observed) or
        (observed is not None and expires is not None and expires - observed > MAX_VALIDITY_SECONDS) or
        (reset is not None and reset_text != "reported") or
        (reset is not None and observed is not None and state_text in {"available", "exhausted"} and
         reset <= observed) or
        (reset_text == "source_allows_unknown" and provider_text != "claude") or
        (reset is None and state_text == "available" and reset_text == "unknown") or
        (state_text == "available" and (observed is None or expires is None or percent is None)) or
        (state_text == "exhausted" and percent != 100) or
        (state_text == "available" and reason is not None) or
        (state_text in {"unknown", "stale", "exhausted"} and reason is None) or
        (state_text == "stale" and reason != "stale_observation") or
        (state_text == "exhausted" and reason != "window_exhausted")
    )
    if invalid:
        raise DecisionInputError(("quota_observation",))
    return QuotaObservation(
        QUOTA_SCHEMA_VERSION, account, provider_text, model_text, window, source_text, state_text,
        observed, expires, reset, reset_text, percent, reason if isinstance(reason, str) else None,
    )


def _unknown(account_ref: str, provider: str, model: str | None, window_id: str, source: str,
             observed_at: float | None, valid_until: float | None, reason: str) -> QuotaObservation:
    return _build_observation(
        schema_version=QUOTA_SCHEMA_VERSION, account_ref=account_ref, provider=provider, model=model,
        window_id=window_id, source=source, state="unknown", observed_at=observed_at,
        valid_until=valid_until, resets_at=None, reset_confidence="unknown", used_percent=None,
        reason_code=reason,
    )


def normalize_cached_windows(*, account_ref: object, provider: object, model: object, source: object,
                             source_status: object, windows: object, observed_at: object, now: object,
                             valid_for_seconds: object, required_windows: Mapping[str, int],
                             unknown_reset_windows: Sequence[str] = ()) -> tuple[QuotaObservation, ...]:
    """Normalize caller-supplied cache fields; this function performs no filesystem or network access."""
    account = _text(account_ref, _ACCOUNT_REF)
    provider_text = provider if isinstance(provider, str) and provider in QUOTA_PROVIDERS else None
    model_text = None if model is None else _text(model, _TOKEN)
    source_text = source if isinstance(source, str) and source in QUOTA_SOURCES else None
    clock, ttl = _number(now), _number(valid_for_seconds)
    observed = _number(observed_at)
    if (account is None or provider_text is None or (model is not None and model_text is None) or
            source_text is None or source_text != _SOURCE_BY_PROVIDER.get(provider_text) or
            clock is None or clock < 0 or ttl is None or not 0 < ttl <= MAX_VALIDITY_SECONDS or
            not isinstance(required_windows, Mapping) or not 1 <= len(required_windows) <= MAX_REQUIRED_WINDOWS):
        raise DecisionInputError(("quota_cache",))
    for name, duration in required_windows.items():
        if _text(name, _TOKEN) is None or not isinstance(duration, int) or isinstance(duration, bool) or duration <= 0:
            raise DecisionInputError(("quota_cache.required_windows",))
    if (not isinstance(unknown_reset_windows, Sequence) or isinstance(unknown_reset_windows, (str, bytes)) or
            len(unknown_reset_windows) > MAX_REQUIRED_WINDOWS):
        raise DecisionInputError(("quota_cache.unknown_reset_windows",))
    allowed_names = tuple(unknown_reset_windows)
    if (any(_text(name, _TOKEN) is None or name not in required_windows for name in allowed_names) or
            allowed_names and provider_text != "claude"):
        raise DecisionInputError(("quota_cache.unknown_reset_windows",))
    allow_unknown = set(allowed_names)
    expires = observed + ttl if observed is not None and observed >= 0 else None
    rows = windows if isinstance(windows, Mapping) else {}
    normalized: list[QuotaObservation] = []
    for window_id, duration in required_windows.items():
        normalized.append(_normalize_one(
            account, provider_text, model_text, source_text, source_status, rows.get(window_id),
            window_id, duration, observed, expires, clock, window_id in allow_unknown,
        ))
    return tuple(normalized)


def _normalize_one(account: str, provider: str, model: str | None, source: str, source_status: object,
                   raw: object, window_id: str, duration: int, observed: float | None,
                   expires: float | None, now: float, allow_unknown_reset: bool) -> QuotaObservation:
    if source_status != "ok":
        return _unknown(account, provider, model, window_id, source, observed, expires, "source_unavailable")
    if observed is None:
        return _unknown(account, provider, model, window_id, source, None, None, "missing_observation")
    if observed > now:
        return _unknown(account, provider, model, window_id, source, observed, expires, "future_observation")
    if expires is None or now >= expires:
        return _build_observation(
            schema_version=QUOTA_SCHEMA_VERSION, account_ref=account, provider=provider, model=model,
            window_id=window_id, source=source, state="stale", observed_at=observed, valid_until=expires,
            resets_at=None, reset_confidence="unknown", used_percent=None, reason_code="stale_observation",
        )
    if not isinstance(raw, Mapping):
        return _unknown(account, provider, model, window_id, source, observed, expires, "missing_required_window")
    percent = _number(raw.get("used_percent"))
    raw_duration = raw.get("window_minutes")
    if (percent is None or not 0 <= percent <= 100 or not isinstance(raw_duration, (int, float)) or
            isinstance(raw_duration, bool) or raw_duration != duration):
        return _unknown(account, provider, model, window_id, source, observed, expires, "invalid_window")
    if "resets_at" not in raw:
        return _unknown(account, provider, model, window_id, source, observed, expires, "reset_missing")
    reset_value = raw.get("resets_at")
    if reset_value is None:
        if not allow_unknown_reset:
            return _unknown(account, provider, model, window_id, source, observed, expires, "reset_missing")
        reset, confidence = None, "source_allows_unknown"
    else:
        reset = _number(reset_value)
        if reset is None or reset <= 0:
            return _unknown(account, provider, model, window_id, source, observed, expires, "invalid_window")
        if reset <= now:
            return _unknown(account, provider, model, window_id, source, observed, expires, "reset_elapsed")
        confidence = "reported"
    if percent >= 100:
        return _build_observation(
            schema_version=QUOTA_SCHEMA_VERSION, account_ref=account, provider=provider, model=model,
            window_id=window_id, source=source, state="exhausted", observed_at=observed, valid_until=expires,
            resets_at=reset, reset_confidence=confidence, used_percent=percent, reason_code="window_exhausted",
        )
    return _build_observation(
        schema_version=QUOTA_SCHEMA_VERSION, account_ref=account, provider=provider, model=model,
        window_id=window_id, source=source, state="available", observed_at=observed, valid_until=expires,
        resets_at=reset, reset_confidence=confidence, used_percent=percent, reason_code=None,
    )


def assess_required_windows(observations: Sequence[QuotaObservation], *, account_ref: str, provider: str,
                            model: str | None, required_windows: Sequence[str], now: float) -> QuotaAssessment:
    """Require one fresh, correctly scoped observation per relevant window before reporting capacity."""
    clock = _number(now)
    if (clock is None or clock < 0 or _text(account_ref, _ACCOUNT_REF) is None or provider not in QUOTA_PROVIDERS or
            (model is not None and _text(model, _TOKEN) is None) or not required_windows or
            not isinstance(required_windows, Sequence) or isinstance(required_windows, (str, bytes)) or
            len(required_windows) > MAX_REQUIRED_WINDOWS or any(_text(name, _TOKEN) is None for name in required_windows) or
            len(set(required_windows)) != len(required_windows) or
            not isinstance(observations, Sequence) or isinstance(observations, (str, bytes)) or
            len(observations) > MAX_OBSERVATIONS):
        raise DecisionInputError(("quota_assessment",))
    by_window: dict[str, QuotaObservation] = {}
    identity_mismatch = False
    for item in observations:
        if not isinstance(item, QuotaObservation):
            raise DecisionInputError(("quota_assessment.observations",))
        item = QuotaObservation.from_dict(item.to_dict())
        if item.provider != provider or item.window_id not in required_windows:
            continue
        if item.account_ref != account_ref or item.model != model:
            identity_mismatch = True
            continue
        if item.window_id in required_windows:
            if item.window_id in by_window:
                return _assessment("unknown", required_windows, (item.window_id,), (), "duplicate_window")
            by_window[item.window_id] = item
    missing = tuple(name for name in required_windows if name not in by_window)
    if missing:
        reason = "identity_mismatch" if identity_mismatch else "missing_required_window"
        return _assessment("unknown", required_windows, missing, (), reason)
    unavailable: list[str] = []
    exhausted: list[str] = []
    percentages: list[float] = []
    for name in required_windows:
        item = by_window[name]
        if item.observed_at is None or item.observed_at > clock or item.valid_until is None or clock >= item.valid_until:
            unavailable.append(name)
            continue
        if item.resets_at is not None and item.resets_at <= clock:
            unavailable.append(name)
            continue
        if item.state == "exhausted":
            exhausted.append(name)
        elif item.state != "available" or item.used_percent is None:
            unavailable.append(name)
        else:
            percentages.append(item.used_percent)
    if exhausted:
        return _assessment("exhausted", required_windows, tuple(unavailable), tuple(exhausted), "window_exhausted")
    if unavailable:
        return _assessment("unknown", required_windows, tuple(unavailable), (), "window_unknown")
    return QuotaAssessment("available", max(percentages), tuple(required_windows), (), (), None)


def assess_account_windows(observations: Sequence[QuotaObservation], *, account_ref: str, provider: str,
                           required_windows: Mapping[str | None, Sequence[str]], now: float) -> QuotaAssessment:
    """Assess base and model-specific windows once per effective account, coalescing identical alias copies."""
    clock = _number(now)
    if (clock is None or clock < 0 or _text(account_ref, _ACCOUNT_REF) is None or provider not in QUOTA_PROVIDERS or
            not isinstance(required_windows, Mapping) or not 1 <= len(required_windows) <= MAX_REQUIRED_WINDOWS or
            not isinstance(observations, Sequence) or isinstance(observations, (str, bytes)) or
            len(observations) > MAX_OBSERVATIONS):
        raise DecisionInputError(("account_quota_assessment",))
    required: list[tuple[str | None, str]] = []
    for model, names in required_windows.items():
        if model is not None and _text(model, _TOKEN) is None:
            raise DecisionInputError(("account_quota_assessment.model",))
        if not isinstance(names, Sequence) or isinstance(names, (str, bytes)) or not names:
            raise DecisionInputError(("account_quota_assessment.windows",))
        if any(_text(name, _TOKEN) is None for name in names):
            raise DecisionInputError(("account_quota_assessment.windows",))
        required.extend((model, name) for name in names)
        if len(required) > MAX_REQUIRED_WINDOWS:
            raise DecisionInputError(("account_quota_assessment.windows",))
    if len(set(required)) != len(required):
        raise DecisionInputError(("account_quota_assessment.duplicate_required_window",))
    ordered = tuple(sorted(required, key=lambda key: (key[0] or "", key[1])))
    labels = tuple(_window_label(model, name) for model, name in ordered)
    by_window: dict[tuple[str | None, str], QuotaObservation] = {}
    identity_mismatch = False
    for raw in observations:
        if not isinstance(raw, QuotaObservation):
            raise DecisionInputError(("account_quota_assessment.observations",))
        item = QuotaObservation.from_dict(raw.to_dict())
        key = (item.model, item.window_id)
        if item.provider != provider or key not in required:
            continue
        if item.account_ref != account_ref:
            identity_mismatch = True
            continue
        previous = by_window.get(key)
        if previous is not None and previous != item:
            unavailable = (_window_label(*key),)
            return _assessment("unknown", labels, unavailable, (), "duplicate_window")
        by_window[key] = item
    missing = tuple(_window_label(*key) for key in ordered if key not in by_window)
    if missing:
        reason = "identity_mismatch" if identity_mismatch else "missing_required_window"
        return _assessment("unknown", labels, missing, (), reason)
    unavailable: list[str] = []
    exhausted: list[str] = []
    percentages: list[float] = []
    for model, name in ordered:
        item = by_window[(model, name)]
        label = _window_label(model, name)
        if item.observed_at is None or item.observed_at > clock or item.valid_until is None or clock >= item.valid_until:
            unavailable.append(label)
            continue
        if item.resets_at is not None and item.resets_at <= clock:
            unavailable.append(label)
            continue
        if item.state == "exhausted":
            exhausted.append(label)
        elif item.state != "available" or item.used_percent is None:
            unavailable.append(label)
        else:
            percentages.append(item.used_percent)
    if exhausted:
        return _assessment("exhausted", labels, tuple(unavailable), tuple(exhausted), "window_exhausted")
    if unavailable:
        return _assessment("unknown", labels, tuple(unavailable), (), "window_unknown")
    return QuotaAssessment("available", max(percentages), labels, (), (), None)


def _window_label(model: str | None, window_id: str) -> str:
    scope = "base" if model is None else model
    return f"{scope}:{window_id}"


def _assessment(state: QuotaState, required: Sequence[str], unavailable: tuple[str, ...],
                exhausted: tuple[str, ...], reason: str) -> QuotaAssessment:
    return QuotaAssessment(state, None, tuple(required), unavailable, exhausted, reason)
