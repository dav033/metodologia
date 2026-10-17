"""Pure value validators shared by M4 contracts and boundary codecs."""
from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from typing import TypeAlias

SCHEMA_VERSION = "1.0.0"
NORMALIZER_VERSION = "1.0.0"
MAX_FRAME_DATA_BYTES = 3_840
MAX_FIFO_HEADER_BYTES = 256
MAX_FIFO_FRAME_BYTES = 4_096
MAX_WIRE_FRAME_BYTES = MAX_FIFO_FRAME_BYTES
MAX_EVENT_BYTES = 16 * 1024
MAX_EVIDENCE_BYTES = 4 * 1024
MAX_EVIDENCE_REFS = 256
MAX_EVIDENCE_REF_BYTES = 16 * 1024
MAX_UNKNOWN_FIELDS = 4_096
MAX_UNKNOWN_DIGEST_INPUT_BYTES = 64 * 1024
PROVIDERS = ("claude", "codex", "antigravity", "gemini_fixture", "unknown")
STREAMS = ("stdout", "stderr")
EVENT_TYPES = (
    "process_started", "tool_started", "tool_finished", "message_delta", "usage_reported", "checkpoint_written",
    "process_exited", "heartbeat", "auth_error", "quota_error", "transport_error", "timeout", "launch_error",
    "stderr_diagnostic", "stream_gap", "unsupported_source_schema",
)
SEVERITIES = ("info", "low", "medium", "high", "critical")
CONFIDENCES = ("low", "medium", "high")
RESOLUTION_STATES = ("open", "resolved")
INCIDENT_TYPES = (
    "unexpected_exit", "quota_error", "auth_error", "connection_error", "timeout", "missed_heartbeat",
    "silent_but_alive", "repetitive_activity", "oversized_output", "provider_stream_silence", "pid_reuse",
    "stale_post_cancel", "source_disagreement", "stream_gap",
)
METRIC_SOURCES = ("provider_reported", "m3_observed", "m4_derived")
METRIC_QUALITIES = ("reported", "partial", "estimated", "unavailable", "unknown")
_VERSION_RE = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$")
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_SAFE_TOKEN_RE = re.compile(r"^[A-Za-z0-9_.:@-]{1,128}$")
_IDENTIFIER_MAX_BYTES = 256
_PAYLOAD_FIELDS = {
    "process_started": frozenset(("pid", "exit_code")),
    "tool_started": frozenset(("tool_label", "argument_bytes", "argument_digest")),
    "tool_finished": frozenset(("tool_label", "duration_ms", "exit_code")),
    "message_delta": frozenset(("message_count", "byte_count")),
    "usage_reported": frozenset(("metric_name", "value", "unit", "source", "sample_count")),
    "checkpoint_written": frozenset(("checkpoint_ref", "byte_count", "digest")),
    "process_exited": frozenset(("exit_code", "signal")),
    "heartbeat": frozenset(("status",)),
    "auth_error": frozenset(("source_code",)),
    "quota_error": frozenset(("source_code",)),
    "transport_error": frozenset(("source_code",)),
    "timeout": frozenset(("deadline_ms",)),
    "launch_error": frozenset(("source_code",)),
    "stderr_diagnostic": frozenset(("diagnostic_code", "byte_count", "digest")),
    "stream_gap": frozenset(("cause", "first_sequence", "last_sequence", "first_offset", "last_offset",
                              "dropped_bytes", "dropped_frames", "unknown_field_count", "unknown_field_digest")),
    "unsupported_source_schema": frozenset(("source_schema_version", "unknown_field_count", "unknown_field_digest")),
}
_INCIDENT_FACT_FIELDS = frozenset((
    "source_code", "process_exit", "diagnostic_code", "first_sequence", "last_sequence", "first_offset",
    "last_offset", "dropped_bytes", "dropped_frames", "expected_state", "observed_state", "deadline_ms",
    "occurrence_count", "window_seconds", "argument_digest", "tool_label",
))
_NONNEGATIVE_INT_FIELDS = frozenset((
    "argument_bytes", "duration_ms", "message_count", "byte_count", "sample_count", "deadline_ms",
    "first_sequence", "last_sequence", "first_offset", "last_offset", "dropped_bytes", "dropped_frames",
    "unknown_field_count", "window_seconds",
))
_POSITIVE_INT_FIELDS = frozenset(("pid", "occurrence_count"))
_SIGNAL_FIELDS = frozenset(("signal",))
_EXIT_CODE_FIELDS = frozenset(("exit_code", "process_exit"))
_DIGEST_FIELDS = frozenset(("argument_digest", "digest", "unknown_field_digest"))
_SAFE_TOKEN_FIELDS = frozenset((
    "tool_label", "metric_name", "unit", "source", "checkpoint_ref", "status", "source_code", "cause",
    "source_schema_version", "diagnostic_code", "expected_state", "observed_state",
))

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | tuple["JsonValue", ...] | tuple[tuple[str, "JsonValue"], ...]


def _text(name: str, value: object, *, maximum: int = _IDENTIFIER_MAX_BYTES, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not value and not allow_empty):
        raise ValueError(f"{name} must be bounded UTF-8 text")
    try:
        if len(value.encode("utf-8", "strict")) > maximum:
            raise ValueError(f"{name} must be bounded UTF-8 text")
    except UnicodeError as exc:
        raise ValueError(f"{name} must be valid UTF-8 text") from exc
    return value


def _optional_text(name: str, value: object, *, maximum: int = _IDENTIFIER_MAX_BYTES) -> None:
    if value is not None:
        _text(name, value, maximum=maximum)


def _nonnegative_int(name: str, value: object) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")


def _positive_int(name: str, value: object) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


def _number(name: str, value: object) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{name} must be numeric")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{name} must be finite")


def _version(name: str, value: object) -> None:
    if not isinstance(value, str) or not _VERSION_RE.fullmatch(value):
        raise ValueError(f"{name} must be a major.minor.patch version")
    if value.split(".", 1)[0] != SCHEMA_VERSION.split(".", 1)[0]:
        raise ValueError(f"{name} has an unsupported schema major")


def _timestamp(name: str, value: object, *, utc_only: bool = False) -> datetime:
    if not isinstance(value, str) or not _TIMESTAMP_RE.fullmatch(value):
        raise ValueError(f"{name} must be an RFC3339 timestamp")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an RFC3339 timestamp") from exc
    if parsed.tzinfo is None or (utc_only and parsed.utcoffset() != timezone.utc.utcoffset(parsed)):
        raise ValueError(f"{name} must be UTC")
    return parsed


def _utc_timestamp(name: str, value: object) -> datetime:
    return _timestamp(name, value, utc_only=True)


def _flat_json_value(name: str, value: object) -> None:
    if isinstance(value, (dict, list, tuple)):
        raise ValueError(f"{name} cannot contain nested containers")
    if isinstance(value, str):
        _text(name, value, maximum=MAX_EVENT_BYTES, allow_empty=True)
    elif value is not None and not isinstance(value, (bool, int, float)):
        raise ValueError(f"{name} must be a JSON scalar")
    elif isinstance(value, float):
        _number(name, value)


def _validate_field(name: str, value: object) -> None:
    _flat_json_value(name, value)
    if name in _NONNEGATIVE_INT_FIELDS:
        _nonnegative_int(name, value)
    elif name in _POSITIVE_INT_FIELDS:
        _positive_int(name, value)
    elif name in _SIGNAL_FIELDS:
        _positive_int(name, value)
        if value > 64:
            raise ValueError("signal must be in the range 1..64")
    elif name in _EXIT_CODE_FIELDS:
        _nonnegative_int(name, value)
        if value > 255:
            raise ValueError(f"{name} must be in the range 0..255")
    elif name in _DIGEST_FIELDS:
        if not isinstance(value, str) or not _DIGEST_RE.fullmatch(value):
            raise ValueError(f"{name} must be a SHA-256 digest")
    elif name in _SAFE_TOKEN_FIELDS:
        validate_safe_token(name, value)
    elif name == "value":
        _number(name, value)
        if value < 0:
            raise ValueError("value must be nonnegative")


def validate_safe_token(name: str, value: object) -> None:
    if not isinstance(value, str) or value in (".", "..") or not _SAFE_TOKEN_RE.fullmatch(value):
        raise ValueError(f"{name} must be a bounded safe token")


def validate_unknown_metadata(count: object, digest: object) -> None:
    _nonnegative_int("unknown_field_count", count)
    if count > MAX_UNKNOWN_FIELDS:
        raise ValueError("unknown_field_count exceeds its bound")
    _optional_text("unknown_field_digest", digest)
    if bool(count) != bool(digest):
        raise ValueError("unknown field count and digest must be provided together")
    if digest is not None and (not isinstance(digest, str) or not _DIGEST_RE.fullmatch(digest)):
        raise ValueError("unknown_field_digest must be a SHA-256 digest")


def validate_payload(payload: dict[str, object]) -> None:
    for name, value in payload.items():
        _validate_field(name, value)


def validate_incident_facts(facts: dict[str, object]) -> None:
    for name, value in facts.items():
        _validate_field(name, value)


__all__ = [
    "CONFIDENCES", "EVENT_TYPES", "INCIDENT_TYPES", "MAX_EVENT_BYTES", "MAX_EVIDENCE_BYTES",
    "MAX_EVIDENCE_REF_BYTES", "MAX_EVIDENCE_REFS", "MAX_FIFO_FRAME_BYTES", "MAX_FIFO_HEADER_BYTES",
    "MAX_FRAME_DATA_BYTES", "MAX_UNKNOWN_DIGEST_INPUT_BYTES", "MAX_UNKNOWN_FIELDS", "MAX_WIRE_FRAME_BYTES",
    "METRIC_QUALITIES", "METRIC_SOURCES", "NORMALIZER_VERSION", "PROVIDERS", "RESOLUTION_STATES",
    "SCHEMA_VERSION", "SEVERITIES", "STREAMS", "_DIGEST_RE", "_INCIDENT_FACT_FIELDS", "_PAYLOAD_FIELDS",
    "_flat_json_value", "_nonnegative_int", "_number", "_optional_text", "_positive_int", "_text",
    "_utc_timestamp", "_version", "validate_incident_facts", "validate_payload", "validate_safe_token",
    "validate_unknown_metadata",
]
