"""Versioned, validated data contracts for the isolated M4 monitor."""
from __future__ import annotations

import json
from dataclasses import dataclass, fields
from datetime import datetime

from .validation import (
    CONFIDENCES, EVENT_TYPES, INCIDENT_TYPES, MAX_EVENT_BYTES, MAX_EVIDENCE_BYTES, MAX_EVIDENCE_REF_BYTES,
    MAX_EVIDENCE_REFS, MAX_FIFO_FRAME_BYTES, MAX_FIFO_HEADER_BYTES, MAX_FRAME_DATA_BYTES, MAX_WIRE_FRAME_BYTES,
    MAX_UNKNOWN_DIGEST_INPUT_BYTES, MAX_UNKNOWN_FIELDS, METRIC_QUALITIES, METRIC_SOURCES,
    NORMALIZER_VERSION, PROVIDERS, RESOLUTION_STATES, SCHEMA_VERSION, SEVERITIES, STREAMS,
    _INCIDENT_FACT_FIELDS, _PAYLOAD_FIELDS, JsonValue, _nonnegative_int, _number, _optional_text,
    _positive_int, _text, _timestamp, _utc_timestamp, _version,
    validate_safe_token,
    validate_unknown_metadata,
)


@dataclass(frozen=True)
class ProcessIdentity:
    platform: str
    host_boot_id: str | None = None
    pid: int | None = None
    start_ticks: int | None = None
    unknown_field_count: int = 0
    unknown_field_digest: str | None = None

    def __post_init__(self) -> None:
        validate_unknown_metadata(self.unknown_field_count, self.unknown_field_digest)
        _text("platform", self.platform, maximum=64)
        _optional_text("host_boot_id", self.host_boot_id)
        if self.pid is not None:
            _positive_int("pid", self.pid)
        if self.start_ticks is not None:
            _nonnegative_int("start_ticks", self.start_ticks)

    @classmethod
    def from_dict(cls, value: object) -> ProcessIdentity:
        from .serialization import identity_from_dict
        return identity_from_dict(value)

    def to_dict(self) -> dict[str, object]:
        from .serialization import identity_to_dict
        return identity_to_dict(self)


@dataclass(frozen=True)
class ExecutionOutputFrame:
    """T2 writes cap data plus binary header; JSON/base64 fixture size is separate."""
    schema_version: str
    run_id: str
    plan_revision: int
    task_id: str
    attempt_id: str
    execution_id: str
    process_identity: ProcessIdentity
    provider: str
    stream: str
    sequence: int
    offset_bytes: int
    received_at: str
    data: bytes
    profile_id: str | None = None
    model: str | None = None
    received_monotonic_ns: int | None = None
    host_boot_id: str | None = None
    unknown_field_count: int = 0
    unknown_field_digest: str | None = None

    def __post_init__(self) -> None:
        validate_unknown_metadata(self.unknown_field_count, self.unknown_field_digest)
        _version("schema_version", self.schema_version)
        for name in ("run_id", "task_id", "attempt_id", "execution_id"):
            _text(name, getattr(self, name))
        _positive_int("plan_revision", self.plan_revision)
        _optional_text("profile_id", self.profile_id)
        _optional_text("model", self.model)
        if not isinstance(self.process_identity, ProcessIdentity):
            raise ValueError("process_identity must be ProcessIdentity")
        if self.provider not in PROVIDERS or self.stream not in STREAMS:
            raise ValueError("provider or stream is unsupported")
        _nonnegative_int("sequence", self.sequence)
        _nonnegative_int("offset_bytes", self.offset_bytes)
        _utc_timestamp("received_at", self.received_at)
        if self.received_monotonic_ns is not None:
            _nonnegative_int("received_monotonic_ns", self.received_monotonic_ns)
        _optional_text("host_boot_id", self.host_boot_id)
        if not isinstance(self.data, bytes) or len(self.data) > MAX_FRAME_DATA_BYTES:
            raise ValueError("data must be bytes no larger than 3840 bytes")
        if len(self.data) + MAX_FIFO_HEADER_BYTES > MAX_FIFO_FRAME_BYTES:
            raise ValueError("frame data plus binary header exceeds the 4096 byte FIFO cap")

    @classmethod
    def from_dict(cls, value: object) -> ExecutionOutputFrame:
        from .serialization import frame_from_dict
        return frame_from_dict(value)

    def to_dict(self) -> dict[str, object]:
        """Return JSON fixture/control data; the base64 encoding is not the M3 FIFO wire frame."""
        from .serialization import frame_to_dict
        return frame_to_dict(self)


@dataclass(frozen=True)
class DroppedRange:
    stream: str
    first_sequence: int
    last_sequence: int
    first_offset: int
    last_offset: int
    dropped_bytes: int
    dropped_frames: int
    unknown_field_count: int = 0
    unknown_field_digest: str | None = None

    def __post_init__(self) -> None:
        validate_unknown_metadata(self.unknown_field_count, self.unknown_field_digest)
        if self.stream not in STREAMS:
            raise ValueError("stream must be stdout or stderr")
        for name in ("first_sequence", "last_sequence", "first_offset", "last_offset", "dropped_bytes"):
            _nonnegative_int(name, getattr(self, name))
        _positive_int("dropped_frames", self.dropped_frames)
        if self.last_sequence < self.first_sequence or self.last_offset < self.first_offset:
            raise ValueError("dropped range bounds must be ordered")

    @classmethod
    def from_dict(cls, value: object) -> DroppedRange:
        from .serialization import dropped_range_from_dict
        return dropped_range_from_dict(value)

    def to_dict(self) -> dict[str, object]:
        from .serialization import dropped_range_to_dict
        return dropped_range_to_dict(self)


@dataclass(frozen=True)
class M3StreamSummary:
    schema_version: str
    execution_id: str
    process_identity: ProcessIdentity
    provider: str
    stdout_bytes_read: int
    stdout_bytes_sent: int
    stdout_bytes_dropped: int
    stderr_bytes_read: int
    stderr_bytes_sent: int
    stderr_bytes_dropped: int
    stdout_last_sequence: int | None = None
    stdout_last_offset: int | None = None
    stderr_last_sequence: int | None = None
    stderr_last_offset: int | None = None
    dropped_ranges: tuple[DroppedRange, ...] = ()
    profile_id: str | None = None
    model: str | None = None
    stream_ref: str | None = None
    unknown_field_count: int = 0
    unknown_field_digest: str | None = None

    def __post_init__(self) -> None:
        validate_unknown_metadata(self.unknown_field_count, self.unknown_field_digest)
        _version("schema_version", self.schema_version)
        _text("execution_id", self.execution_id)
        if not isinstance(self.process_identity, ProcessIdentity) or self.provider not in PROVIDERS:
            raise ValueError("process identity or provider is invalid")
        for name in ("stdout_bytes_read", "stdout_bytes_sent", "stdout_bytes_dropped", "stderr_bytes_read",
                     "stderr_bytes_sent", "stderr_bytes_dropped"):
            _nonnegative_int(name, getattr(self, name))
        for name in ("stdout_last_sequence", "stdout_last_offset", "stderr_last_sequence", "stderr_last_offset"):
            value = getattr(self, name)
            if value is not None:
                _nonnegative_int(name, value)
        if not isinstance(self.dropped_ranges, tuple) or any(not isinstance(item, DroppedRange) for item in self.dropped_ranges):
            raise ValueError("dropped_ranges must be a tuple of DroppedRange")
        if len(self.dropped_ranges) > 1024:
            raise ValueError("too many dropped ranges")
        _optional_text("profile_id", self.profile_id)
        _optional_text("model", self.model)
        if self.stream_ref is not None:
            _text("stream_ref", self.stream_ref, maximum=1024)
            if self.stream_ref.startswith("/") or ".." in self.stream_ref.split("/"):
                raise ValueError("stream_ref must be a relative path without parent traversal")

    @classmethod
    def from_dict(cls, value: object) -> M3StreamSummary:
        from .serialization import summary_from_dict
        return summary_from_dict(value)

    def to_dict(self) -> dict[str, object]:
        from .serialization import summary_to_dict
        return summary_to_dict(self)


@dataclass(frozen=True)
class NormalizedEvent:
    schema_version: str
    event_id: str
    source_schema_version: str
    normalizer_version: str
    run_id: str
    plan_revision: int
    task_id: str
    attempt_id: str
    execution_id: str
    process_identity: ProcessIdentity
    provider: str
    profile_id: str | None
    model: str | None
    event_type: str
    source_event_type: str
    received_at: str
    stream: str
    sequence: int
    offset_bytes: int
    payload: tuple[tuple[str, JsonValue], ...]
    quality: str
    source_event_id: str | None = None
    source_occurred_at: str | None = None
    received_monotonic_ns: int | None = None
    host_boot_id: str | None = None
    evidence_ref: str | None = None
    unknown_field_count: int = 0
    unknown_field_digest: str | None = None
    def __post_init__(self) -> None:
        validate_unknown_metadata(self.unknown_field_count, self.unknown_field_digest)
        _version("schema_version", self.schema_version)
        _version("normalizer_version", self.normalizer_version)
        _text("source_schema_version", self.source_schema_version, maximum=128)
        for name in ("event_id", "run_id", "task_id", "attempt_id", "execution_id", "source_event_type"):
            _text(name, getattr(self, name))
        _positive_int("plan_revision", self.plan_revision)
        if not isinstance(self.process_identity, ProcessIdentity) or self.provider not in PROVIDERS:
            raise ValueError("process identity or provider is invalid")
        _optional_text("profile_id", self.profile_id)
        _optional_text("model", self.model)
        if self.event_type not in EVENT_TYPES or self.stream not in STREAMS or self.quality not in METRIC_QUALITIES:
            raise ValueError("event type, stream or quality is unsupported")
        _optional_text("source_event_id", self.source_event_id)
        if self.source_occurred_at is not None:
            _timestamp("source_occurred_at", self.source_occurred_at)
        _utc_timestamp("received_at", self.received_at)
        if self.received_monotonic_ns is not None:
            _nonnegative_int("received_monotonic_ns", self.received_monotonic_ns)
        _optional_text("host_boot_id", self.host_boot_id)
        _optional_text("evidence_ref", self.evidence_ref)
        _nonnegative_int("sequence", self.sequence)
        _nonnegative_int("offset_bytes", self.offset_bytes)
        if not isinstance(self.payload, tuple):
            raise ValueError("payload must be an immutable normalized mapping")
        payload_obj = dict(self.payload)
        if len(payload_obj) != len(self.payload) or any(not isinstance(key, str) for key in payload_obj):
            raise ValueError("payload keys must be unique strings")
        if not set(payload_obj).issubset(_PAYLOAD_FIELDS[self.event_type]):
            raise ValueError("payload contains a field outside the event allowlist")
        from .validation import validate_payload
        validate_payload(payload_obj)
        try:
            record = {field.name: getattr(self, field.name) for field in fields(self)}
            record["process_identity"] = {
                "platform": self.process_identity.platform, "host_boot_id": self.process_identity.host_boot_id,
                "pid": self.process_identity.pid, "start_ticks": self.process_identity.start_ticks,
            }
            encoded = json.dumps(record, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise ValueError("normalized event must contain only finite JSON-compatible values") from exc
        if len(encoded) > MAX_EVENT_BYTES:
            raise ValueError("normalized event exceeds 16 KiB")

    @classmethod
    def from_dict(cls, value: object) -> NormalizedEvent:
        from .serialization import event_from_dict
        return event_from_dict(value)

    def to_dict(self) -> dict[str, object]:
        from .serialization import event_to_dict
        return event_to_dict(self)


@dataclass(frozen=True)
class Incident:
    schema_version: str
    incident_id: str
    run_id: str
    task_id: str
    attempt_id: str
    execution_id: str
    detector_id: str
    type: str
    severity: str
    confidence: str
    first_seen_at: str
    last_seen_at: str
    occurrence_count: int
    facts: tuple[tuple[str, JsonValue], ...]
    evidence_refs: tuple[str, ...]
    resolution_state: str
    resolved_at: str | None = None
    process_identity: ProcessIdentity | None = None
    unknown_field_count: int = 0
    unknown_field_digest: str | None = None

    def __post_init__(self) -> None:
        validate_unknown_metadata(self.unknown_field_count, self.unknown_field_digest)
        _version("schema_version", self.schema_version)
        for name in ("incident_id", "run_id", "task_id", "attempt_id", "execution_id"):
            _text(name, getattr(self, name))
        validate_safe_token("detector_id", self.detector_id)
        if self.type not in INCIDENT_TYPES or self.severity not in SEVERITIES or self.confidence not in CONFIDENCES:
            raise ValueError("incident type, severity or confidence is unsupported")
        _utc_timestamp("first_seen_at", self.first_seen_at)
        _utc_timestamp("last_seen_at", self.last_seen_at)
        first_seen = datetime.fromisoformat(self.first_seen_at[:-1] + "+00:00" if self.first_seen_at.endswith("Z") else self.first_seen_at)
        last_seen = datetime.fromisoformat(self.last_seen_at[:-1] + "+00:00" if self.last_seen_at.endswith("Z") else self.last_seen_at)
        if last_seen < first_seen:
            raise ValueError("last_seen_at must not precede first_seen_at")
        _positive_int("occurrence_count", self.occurrence_count)
        if not isinstance(self.facts, tuple) or not isinstance(self.evidence_refs, tuple):
            raise ValueError("facts and evidence_refs must be immutable tuples")
        facts = dict(self.facts)
        if len(facts) != len(self.facts) or not set(facts).issubset(_INCIDENT_FACT_FIELDS):
            raise ValueError("incident facts contain a field outside the allowlist")
        from .validation import validate_incident_facts
        validate_incident_facts(facts)
        if len(self.evidence_refs) > MAX_EVIDENCE_REFS:
            raise ValueError("too many evidence references")
        for ref in self.evidence_refs:
            validate_safe_token("evidence_ref", ref)
        if sum(len(ref.encode("utf-8")) for ref in self.evidence_refs) > MAX_EVIDENCE_REF_BYTES:
            raise ValueError("evidence references exceed the aggregate size limit")
        encoded = json.dumps(facts, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
        if len(encoded) > MAX_EVIDENCE_BYTES:
            raise ValueError("incident facts exceed the 4 KiB evidence limit")
        if self.resolution_state not in RESOLUTION_STATES:
            raise ValueError("resolution_state is unsupported")
        if self.resolved_at is not None:
            _utc_timestamp("resolved_at", self.resolved_at)
            resolved = datetime.fromisoformat(self.resolved_at[:-1] + "+00:00" if self.resolved_at.endswith("Z") else self.resolved_at)
            if resolved < last_seen:
                raise ValueError("resolved_at must not precede last_seen_at")
        if (self.resolution_state == "resolved") != (self.resolved_at is not None):
            raise ValueError("resolved incidents require resolved_at; open incidents must omit it")
        if self.process_identity is not None and not isinstance(self.process_identity, ProcessIdentity):
            raise ValueError("process_identity must be ProcessIdentity or None")

    @classmethod
    def from_dict(cls, value: object) -> Incident:
        from .serialization import incident_from_dict
        return incident_from_dict(value)

    def to_dict(self) -> dict[str, object]:
        from .serialization import incident_to_dict
        return incident_to_dict(self)


@dataclass(frozen=True)
class MetricSample:
    schema_version: str
    metric_id: str
    provider: str
    name: str
    value: int | float | None
    unit: str
    source: str
    observed_at: str
    quality: str
    sample_count: int
    comparability_key: str
    profile_id: str | None = None
    model: str | None = None
    unknown_field_count: int = 0
    unknown_field_digest: str | None = None

    def __post_init__(self) -> None:
        validate_unknown_metadata(self.unknown_field_count, self.unknown_field_digest)
        _version("schema_version", self.schema_version)
        for name in ("metric_id", "name", "unit", "comparability_key"):
            _text(name, getattr(self, name))
        if self.provider not in PROVIDERS or self.source not in METRIC_SOURCES or self.quality not in METRIC_QUALITIES:
            raise ValueError("provider, source or quality is unsupported")
        if self.value is None:
            if self.quality not in ("unavailable", "unknown") or self.sample_count != 0:
                raise ValueError("missing metric values require unavailable/unknown quality and zero samples")
        else:
            _number("value", self.value)
            if self.value < 0 or self.quality not in ("reported", "partial", "estimated"):
                raise ValueError("metric values must be nonnegative and carry measured quality")
            _positive_int("sample_count", self.sample_count)
        _utc_timestamp("observed_at", self.observed_at)
        _nonnegative_int("sample_count", self.sample_count)
        _optional_text("profile_id", self.profile_id)
        _optional_text("model", self.model)

    @classmethod
    def from_dict(cls, value: object) -> MetricSample:
        from .serialization import metric_from_dict
        return metric_from_dict(value)

    def to_dict(self) -> dict[str, object]:
        from .serialization import metric_to_dict
        return metric_to_dict(self)


__all__ = [
    "CONFIDENCES", "EVENT_TYPES", "INCIDENT_TYPES", "MAX_EVENT_BYTES", "MAX_EVIDENCE_BYTES",
    "MAX_EVIDENCE_REF_BYTES", "MAX_EVIDENCE_REFS",
    "MAX_FIFO_FRAME_BYTES", "MAX_FIFO_HEADER_BYTES", "MAX_FRAME_DATA_BYTES", "MAX_WIRE_FRAME_BYTES",
    "MAX_UNKNOWN_DIGEST_INPUT_BYTES", "MAX_UNKNOWN_FIELDS",
    "METRIC_QUALITIES", "METRIC_SOURCES",
    "NORMALIZER_VERSION", "PROVIDERS", "RESOLUTION_STATES", "SCHEMA_VERSION", "SEVERITIES", "STREAMS",
    "DroppedRange", "ExecutionOutputFrame", "Incident", "M3StreamSummary", "MetricSample",
    "NormalizedEvent", "ProcessIdentity",
]
