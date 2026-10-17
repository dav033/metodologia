"""Allowlist provider payloads and redact bounded text before persistence."""
from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from dataclasses import dataclass

from .validation import EVENT_TYPES, MAX_EVIDENCE_BYTES, _PAYLOAD_FIELDS, validate_payload

MAX_REDACTION_INPUT_BYTES = 64 * 1024

_SECRET_PATTERNS = (
    re.compile(r"(?i)(\bBearer\s+)[A-Za-z0-9._~+/=-]+"),
    re.compile(r"(?i)(\b(?:api[_-]?key|access[_-]?token|refresh[_-]?token|password|secret)\b\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
)


@dataclass(frozen=True)
class AllowlistedPayload:
    fields: tuple[tuple[str, object], ...]
    dropped_field_count: int


@dataclass(frozen=True)
class RedactedEvidence:
    excerpt: str | None
    digest: str | None
    byte_count: int
    withheld: bool


def allowlist_payload(event_type: str, value: object) -> AllowlistedPayload:
    """Keep only validated event fields; unknown nested objects are never serialized."""
    if event_type not in EVENT_TYPES or not isinstance(value, Mapping):
        raise ValueError("event payload must be a supported object")
    allowed = _PAYLOAD_FIELDS[event_type]
    retained = {key: item for key, item in value.items() if isinstance(key, str) and key in allowed}
    validate_payload(retained)
    return AllowlistedPayload(tuple(sorted(retained.items())), len(value) - len(retained))


def redact_evidence(value: object, *, max_bytes: int = MAX_EVIDENCE_BYTES,
                    filter_text: object = None) -> RedactedEvidence:
    """Return a bounded redacted excerpt; any decoding/filter error withholds it."""
    if not isinstance(value, (str, bytes)):
        raise ValueError("evidence must be text or bytes")
    if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or not 0 <= max_bytes <= MAX_EVIDENCE_BYTES:
        raise ValueError("evidence cap is outside the contract")
    try:
        raw = value.encode("utf-8", "strict") if isinstance(value, str) else value
    except UnicodeError:
        return RedactedEvidence(None, None, 0, True)
    byte_count = len(raw)
    if byte_count > MAX_REDACTION_INPUT_BYTES:
        return RedactedEvidence(None, None, byte_count, True)
    digest = "sha256:" + hashlib.sha256(raw).hexdigest()
    try:
        text = raw.decode("utf-8", "strict")
        if filter_text is not None:
            if not callable(filter_text):
                raise TypeError("filter must be callable")
            text = filter_text(text)
        if not isinstance(text, str):
            raise TypeError("filter must return text")
        for pattern in _SECRET_PATTERNS:
            text = pattern.sub("[REDACTED]", text)
        encoded = text.encode("utf-8", "strict")
        if len(encoded) > max_bytes:
            encoded = encoded[:max_bytes]
            text = encoded.decode("utf-8", "ignore")
        return RedactedEvidence(text or None, digest, byte_count, False)
    except Exception:
        return RedactedEvidence(None, digest, byte_count, True)


__all__ = ["AllowlistedPayload", "RedactedEvidence", "allowlist_payload", "redact_evidence"]
