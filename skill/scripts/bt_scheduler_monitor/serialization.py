"""JSON boundary codecs for M4 versioned contracts.

Unknown values are accepted only as JSON scalars, dicts, lists, or tuples within
the 64 KiB digest budget, 32 container levels, and 4,096 items per container.
These deliberate limits are checked before JSON encoding to bound allocation.
"""
from __future__ import annotations

import base64
import hashlib
import json
import math
from collections.abc import Iterable, Mapping
from dataclasses import fields

from .contracts import (
    MAX_FRAME_DATA_BYTES,
    _INCIDENT_FACT_FIELDS,
    _PAYLOAD_FIELDS,
    DroppedRange,
    ExecutionOutputFrame,
    Incident,
    M3StreamSummary,
    MetricSample,
    NormalizedEvent,
    ProcessIdentity,
)
from .validation import _DIGEST_RE, _nonnegative_int
from .validation import MAX_UNKNOWN_DIGEST_INPUT_BYTES, MAX_UNKNOWN_FIELDS


def _bounded_field_name(value: object) -> str:
    if not isinstance(value, str) or len(value) > 256:
        raise ValueError("field names must be bounded UTF-8 text")
    try:
        if len(value.encode("utf-8", "strict")) > 256:
            raise ValueError("field names must be bounded UTF-8 text")
    except UnicodeError as exc:
        raise ValueError("field names must be valid UTF-8 text") from exc
    return value


def _object(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be an object with string keys")
    try:
        if len(value) > MAX_UNKNOWN_FIELDS + 64:
            raise ValueError(f"{name} exceeds its member bound")
    except (TypeError, OverflowError) as exc:
        raise ValueError(f"{name} must have a bounded member count") from exc
    for key in value:
        try:
            _bounded_field_name(key)
        except ValueError as exc:
            raise ValueError(f"{name} contains an invalid or oversized field name") from exc
    return value


def _required(data: Mapping[str, object], *names: str) -> None:
    missing = [name for name in names if name not in data]
    if missing:
        raise ValueError(f"missing required fields: {', '.join(missing)}")


def _identity_from_dict(value: object) -> ProcessIdentity:
    return identity_from_dict(value)


def identity_from_dict(value: object) -> ProcessIdentity:
    data = _object(value, "process_identity")
    _required(data, "platform")
    known = {"platform", "host_boot_id", "pid", "start_ticks"}
    count, digest = _unknown_metadata(data, known)
    return ProcessIdentity(data["platform"], data.get("host_boot_id"), data.get("pid"), data.get("start_ticks"),
                           unknown_field_count=count, unknown_field_digest=digest)


def _identity_to_dict(value: ProcessIdentity) -> dict[str, object]:
    return {"platform": value.platform, "host_boot_id": value.host_boot_id, "pid": value.pid,
            "start_ticks": value.start_ticks, "unknown_field_count": value.unknown_field_count,
            "unknown_field_digest": value.unknown_field_digest}


def identity_to_dict(value: ProcessIdentity) -> dict[str, object]:
    return _identity_to_dict(value)


def _unknown_value_budget(value: object, remaining: int, depth: int = 0,
                          ancestors: set[int] | None = None) -> int:
    """Return a conservative encoded-size estimate without copying large values."""
    if depth > 32:
        raise ValueError("unknown field nesting exceeds its depth bound")
    if type(value) is str:
        if len(value) > remaining // 6:
            raise ValueError("canonical unknown field input exceeds its byte cap")
        try:
            value.encode("utf-8", "strict")
        except UnicodeError as exc:
            raise ValueError("unknown fields must contain valid Unicode") from exc
        return len(value) * 6 + 2
    if value is None or type(value) is bool:
        return 5
    if type(value) is int:
        if value.bit_length() > remaining * 3:
            raise ValueError("canonical unknown field input exceeds its byte cap")
        return len(str(value)) + 1
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("unknown fields must contain finite numbers")
        return 32
    if type(value) in (dict, list, tuple):
        if len(value) > 4_096:
            raise ValueError("unknown field container exceeds its item bound")
        active = ancestors if ancestors is not None else set()
        marker = id(value)
        if marker in active:
            raise ValueError("unknown fields cannot contain cycles")
        active.add(marker)
        total = 2
        try:
            entries = value.items() if isinstance(value, dict) else enumerate(value)
            for key, item in entries:
                total += 2
                if type(value) is dict:
                    if type(key) is not str:
                        raise ValueError("unknown field objects require string keys")
                    total += _unknown_value_budget(key, remaining - total, depth + 1, active)
                total += _unknown_value_budget(item, remaining - total, depth + 1, active)
                if total > remaining:
                    raise ValueError("canonical unknown field input exceeds its byte cap")
        finally:
            active.remove(marker)
        return total
    raise ValueError("unknown fields must contain only JSON values")


def _unknown_pairs_digest(pairs: list[tuple[str, object]]) -> str:
    ordered = sorted(pairs, key=lambda pair: pair[0])
    budget = 2
    for path, value in ordered:
        budget += _unknown_value_budget(path, MAX_UNKNOWN_DIGEST_INPUT_BYTES - budget)
        budget += _unknown_value_budget(value, MAX_UNKNOWN_DIGEST_INPUT_BYTES - budget)
        budget += 4
        if budget > MAX_UNKNOWN_DIGEST_INPUT_BYTES:
            raise ValueError("canonical unknown field input exceeds its byte cap")
    try:
        encoded = json.dumps(ordered, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":"), allow_nan=False).encode("utf-8", "strict")
    except (UnicodeError, TypeError, ValueError, RecursionError) as exc:
        raise ValueError("unknown fields must be JSON-encodable Unicode data") from exc
    if len(encoded) > MAX_UNKNOWN_DIGEST_INPUT_BYTES:
        raise ValueError("canonical unknown field input exceeds its byte cap")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _unknown_metadata(data: Mapping[str, object], known_names: set[str],
                      extra_fields: Iterable[tuple[str, str, object]] | None = None
                      ) -> tuple[int, str | None]:
    prior_count = data.get("unknown_field_count", 0)
    prior_digest = data.get("unknown_field_digest")
    _nonnegative_int("unknown_field_count", prior_count)
    if prior_count > MAX_UNKNOWN_FIELDS:
        raise ValueError("unknown_field_count exceeds its bound")
    if (prior_count == 0) != (prior_digest is None):
        raise ValueError("unknown field count and digest must be provided together")
    if prior_digest is not None and (not isinstance(prior_digest, str) or not _DIGEST_RE.fullmatch(prior_digest)):
        raise ValueError("unknown_field_digest must be a SHA-256 digest")
    unknown: list[tuple[str, object]] = []
    limit = MAX_UNKNOWN_FIELDS - prior_count
    excluded = known_names | {"unknown_field_count", "unknown_field_digest"}
    for name in data:
        if name in excluded:
            continue
        if len(unknown) >= limit:
            raise ValueError("unknown field count exceeds its bound")
        unknown.append(("root:" + _bounded_field_name(name), data[name]))
    for prefix, name, value in extra_fields or ():
        if len(unknown) >= limit:
            raise ValueError("unknown field count exceeds its bound")
        unknown.append((prefix + _bounded_field_name(name), value))
    if not unknown:
        return prior_count, prior_digest
    digest = _unknown_pairs_digest(unknown)
    if prior_count:
        digest = "sha256:" + hashlib.sha256(json.dumps([prior_digest, digest], separators=(",", ":")).encode()).hexdigest()
    return prior_count + len(unknown), digest


def _metadata_dict(record: object) -> dict[str, object]:
    return {"unknown_field_count": record.unknown_field_count, "unknown_field_digest": record.unknown_field_digest}


def frame_from_dict(value: object) -> ExecutionOutputFrame:
    data = _object(value, "frame")
    required = ("schema_version", "run_id", "plan_revision", "task_id", "attempt_id", "execution_id",
                "process_identity", "provider", "stream", "sequence", "offset_bytes", "received_at", "data")
    _required(data, *required)
    encoded = data["data"]
    if not isinstance(encoded, str) or data.get("data_encoding", "base64") != "base64":
        raise ValueError("data must use base64 encoding")
    if len(encoded) > 4 * ((MAX_FRAME_DATA_BYTES + 2) // 3):
        raise ValueError("encoded frame data exceeds the frame cap")
    try:
        raw_data = base64.b64decode(encoded, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise ValueError("data must be valid base64") from exc
    optional = ("profile_id", "model", "received_monotonic_ns", "host_boot_id", "data_encoding")
    count, digest = _unknown_metadata(data, set(required) | set(optional))
    return ExecutionOutputFrame(
        data["schema_version"], data["run_id"], data["plan_revision"], data["task_id"], data["attempt_id"],
        data["execution_id"], _identity_from_dict(data["process_identity"]), data["provider"], data["stream"],
        data["sequence"], data["offset_bytes"], data["received_at"], raw_data, data.get("profile_id"),
        data.get("model"), data.get("received_monotonic_ns"), data.get("host_boot_id"),
        unknown_field_count=count, unknown_field_digest=digest,
    )


def frame_to_dict(frame: ExecutionOutputFrame) -> dict[str, object]:
    return {"schema_version": frame.schema_version, "run_id": frame.run_id, "plan_revision": frame.plan_revision,
            "task_id": frame.task_id, "attempt_id": frame.attempt_id, "execution_id": frame.execution_id,
            "process_identity": _identity_to_dict(frame.process_identity), "provider": frame.provider,
            "stream": frame.stream, "sequence": frame.sequence, "offset_bytes": frame.offset_bytes,
            "received_at": frame.received_at, "data": base64.b64encode(frame.data).decode("ascii"),
            "data_encoding": "base64", "profile_id": frame.profile_id, "model": frame.model,
            "received_monotonic_ns": frame.received_monotonic_ns, "host_boot_id": frame.host_boot_id,
            **_metadata_dict(frame)}


def dropped_range_from_dict(value: object) -> DroppedRange:
    data = _object(value, "dropped range")
    names = ("stream", "first_sequence", "last_sequence", "first_offset", "last_offset", "dropped_bytes", "dropped_frames")
    _required(data, *names)
    count, digest = _unknown_metadata(data, set(names))
    return DroppedRange(*(data[name] for name in names), unknown_field_count=count, unknown_field_digest=digest)


def dropped_range_to_dict(item: DroppedRange) -> dict[str, object]:
    return {field.name: getattr(item, field.name) for field in fields(item)}


def summary_from_dict(value: object) -> M3StreamSummary:
    data = _object(value, "M3 stream summary")
    required = ("schema_version", "execution_id", "process_identity", "provider", "stdout_bytes_read",
                "stdout_bytes_sent", "stdout_bytes_dropped", "stderr_bytes_read", "stderr_bytes_sent",
                "stderr_bytes_dropped")
    _required(data, *required)
    ranges = data.get("dropped_ranges", ())
    if not isinstance(ranges, (list, tuple)):
        raise ValueError("dropped_ranges must be a list")
    if len(ranges) > 1024:
        raise ValueError("too many dropped ranges")
    optional = ("stdout_last_sequence", "stdout_last_offset", "stderr_last_sequence", "stderr_last_offset",
                "profile_id", "model", "stream_ref", "dropped_ranges")
    count, digest = _unknown_metadata(data, set(required) | set(optional))
    kwargs = {name: data[name] for name in required if name != "process_identity"}
    kwargs["process_identity"] = _identity_from_dict(data["process_identity"])
    kwargs["dropped_ranges"] = tuple(dropped_range_from_dict(item) for item in ranges)
    kwargs["unknown_field_count"], kwargs["unknown_field_digest"] = count, digest
    for name in optional:
        if name == "dropped_ranges":
            continue
        if name in data:
            kwargs[name] = data[name]
    return M3StreamSummary(**kwargs)


def summary_to_dict(summary: M3StreamSummary) -> dict[str, object]:
    result = {field.name: getattr(summary, field.name) for field in fields(summary)}
    result["process_identity"] = _identity_to_dict(summary.process_identity)
    result["dropped_ranges"] = [dropped_range_to_dict(item) for item in summary.dropped_ranges]
    return result


def event_from_dict(value: object) -> NormalizedEvent:
    data = _object(value, "normalized event")
    required = ("schema_version", "event_id", "source_schema_version", "normalizer_version", "run_id",
                "plan_revision", "task_id", "attempt_id", "execution_id", "process_identity", "provider",
                "event_type", "source_event_type", "received_at", "stream", "sequence", "offset_bytes",
                "payload", "quality")
    _required(data, *required)
    raw_payload = _object(data["payload"], "payload")
    allowlist = _PAYLOAD_FIELDS.get(data["event_type"], frozenset())
    optional = ("profile_id", "model", "source_event_id", "source_occurred_at", "received_monotonic_ns",
                "host_boot_id", "evidence_ref")
    envelope_names = set(required) | set(optional) | {"unknown_field_count", "unknown_field_digest"}
    unknown = (("payload:", name, raw_payload[name]) for name in raw_payload if name not in allowlist)
    kwargs = {name: data[name] for name in required if name not in ("process_identity", "payload")}
    kwargs["process_identity"] = _identity_from_dict(data["process_identity"])
    kwargs["payload"] = tuple(sorted((name, raw_payload[name]) for name in raw_payload if name in allowlist))
    count, digest = _unknown_metadata(data, envelope_names, unknown)
    kwargs["unknown_field_count"], kwargs["unknown_field_digest"] = count, digest
    for name in optional:
        if name in data:
            kwargs[name] = data[name]
    return NormalizedEvent(**kwargs)


def event_to_dict(event: NormalizedEvent) -> dict[str, object]:
    result = {field.name: getattr(event, field.name) for field in fields(event)}
    result["process_identity"] = _identity_to_dict(event.process_identity)
    result["payload"] = dict(event.payload)
    return result


def incident_from_dict(value: object) -> Incident:
    data = _object(value, "incident")
    required = ("schema_version", "incident_id", "run_id", "task_id", "attempt_id", "execution_id", "detector_id",
                "type", "severity", "confidence", "first_seen_at", "last_seen_at", "occurrence_count", "facts",
                "evidence_refs", "resolution_state")
    _required(data, *required)
    facts = _object(data["facts"], "facts")
    optional = ("resolved_at", "process_identity")
    count, digest = _unknown_metadata(data, set(required) | set(optional),
                                      (("facts:", name, facts[name]) for name in facts
                                       if name not in _INCIDENT_FACT_FIELDS))
    refs = data["evidence_refs"]
    if not isinstance(refs, (list, tuple)):
        raise ValueError("evidence_refs must be a list")
    kwargs = {name: data[name] for name in required if name not in ("facts", "evidence_refs")}
    kwargs["facts"], kwargs["evidence_refs"] = tuple(sorted((name, facts[name]) for name in facts
                                                              if name in _INCIDENT_FACT_FIELDS)), tuple(refs)
    kwargs["unknown_field_count"], kwargs["unknown_field_digest"] = count, digest
    if data.get("process_identity") is not None:
        kwargs["process_identity"] = _identity_from_dict(data["process_identity"])
    if "resolved_at" in data:
        kwargs["resolved_at"] = data["resolved_at"]
    return Incident(**kwargs)


def incident_to_dict(incident: Incident) -> dict[str, object]:
    result = {field.name: getattr(incident, field.name) for field in fields(incident)}
    result["facts"], result["evidence_refs"] = dict(incident.facts), list(incident.evidence_refs)
    result["process_identity"] = _identity_to_dict(incident.process_identity) if incident.process_identity else None
    return result


def metric_from_dict(value: object) -> MetricSample:
    data = _object(value, "metric sample")
    required = ("schema_version", "metric_id", "provider", "name", "value", "unit", "source", "observed_at",
                "quality", "sample_count", "comparability_key")
    _required(data, *required)
    count, digest = _unknown_metadata(data, set(required) | {"profile_id", "model"})
    kwargs = {name: data[name] for name in required}
    kwargs["unknown_field_count"], kwargs["unknown_field_digest"] = count, digest
    for name in ("profile_id", "model"):
        if name in data:
            kwargs[name] = data[name]
    return MetricSample(**kwargs)


def metric_to_dict(metric: MetricSample) -> dict[str, object]:
    return {field.name: getattr(metric, field.name) for field in fields(metric)}


__all__ = ["dropped_range_from_dict", "dropped_range_to_dict", "event_from_dict", "event_to_dict", "frame_from_dict",
           "frame_to_dict", "incident_from_dict", "incident_to_dict", "metric_from_dict", "metric_to_dict",
           "summary_from_dict", "summary_to_dict"]
