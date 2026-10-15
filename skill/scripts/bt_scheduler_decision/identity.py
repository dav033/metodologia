"""Canonical identities and opaque references; no filesystem or environment access."""
from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from typing import Any

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_EXECUTOR_REF = re.compile(r"m2:v1:([0-9a-f]{64}):([0-9a-f]{64})\Z")


def _normalise_text(value: str) -> str:
    normalized = unicodedata.normalize("NFC", value)
    try:
        normalized.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise ValueError("strings must contain valid Unicode scalar values") from exc
    return normalized


def _normalise(value: Any) -> Any:
    if is_dataclass(value):
        return _normalise({field.name: getattr(value, field.name) for field in fields(value)})
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("non-finite number")
        return value
    if isinstance(value, str):
        return _normalise_text(value)
    if isinstance(value, Mapping):
        if not all(isinstance(key, str) for key in value):
            raise ValueError("object keys must be strings")
        normalized = {}
        for key in sorted(value):
            normalized_key = _normalise_text(key)
            if normalized_key in normalized:
                raise ValueError("object keys collide after Unicode normalization")
            normalized[normalized_key] = _normalise(value[key])
        return normalized
    if isinstance(value, (tuple, list)):
        return [_normalise(item) for item in value]
    raise ValueError("value is not JSON-compatible")


def canonical_json(value: Any) -> str:
    """Canonical JSON with NFC strings, sorted keys and no non-finite numbers."""
    return json.dumps(_normalise(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def candidate_route_id(provider: str, model: str, profile: str, effort: str | None) -> str:
    return sha256_json({"provider": provider, "model": model, "profile": profile, "effort": effort})


def account_reference(account_key: str) -> str:
    """Hash the router's account key before it crosses into M2 persistence or diagnostics."""
    if not isinstance(account_key, str) or not account_key.strip():
        raise ValueError("account key must be non-empty text")
    return "acct:" + hashlib.sha256(_normalise_text(account_key).encode("utf-8")).hexdigest()


def executor_reference(decision_id: str, route_id: str) -> str:
    if not _SHA256.fullmatch(decision_id or "") or not _SHA256.fullmatch(route_id or ""):
        raise ValueError("decision and route ids must be lowercase SHA-256 hex")
    return f"m2:v1:{decision_id}:{route_id}"


def parse_executor_reference(reference: str) -> tuple[str, str] | None:
    if not isinstance(reference, str):
        return None
    match = _EXECUTOR_REF.fullmatch(reference)
    return (match.group(1), match.group(2)) if match else None
