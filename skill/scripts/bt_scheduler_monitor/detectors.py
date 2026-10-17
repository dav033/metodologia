"""Deterministic incident detection from allowlisted M4 and M1/M3 facts."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Iterable

from .contracts import Incident, NormalizedEvent, ProcessIdentity
from .process_identity import corroborate_process_identity
from .validation import SCHEMA_VERSION


@dataclass(frozen=True)
class DetectorConfig:
    heartbeat_period_seconds: int = 30
    silent_seconds: int = 300
    repetitive_count: int = 20
    repetitive_window_seconds: int = 300
    max_frame_bytes: int = 65_536
    max_event_bytes: int = 16_384
    max_evidence_bytes: int = 4_096
    cancel_grace_seconds: int = 2
    disagreement_seconds: int = 30

    def __post_init__(self) -> None:
        for name, value in vars(self).items():
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")


@dataclass(frozen=True)
class DetectorContext:
    """Versioned snapshots and monotonic clock inputs; absent facts remain unknown."""

    observed_at: str
    monotonic_now_ns: int | None = None
    monotonic_boot_id: str | None = None
    m1_attempt_state: str | None = None
    m1_state_version: str | None = None
    m3_state_version: str | None = None
    m3_process_state: str | None = None
    m3_process_identity: ProcessIdentity | None = None
    proc_identity: ProcessIdentity | None = None
    last_heartbeat_monotonic_ns: int | None = None
    last_heartbeat_boot_id: str | None = None
    last_output_monotonic_ns: int | None = None
    last_output_boot_id: str | None = None
    last_parser_event_monotonic_ns: int | None = None
    last_parser_event_boot_id: str | None = None
    m3_last_io_monotonic_ns: int | None = None
    m3_last_io_boot_id: str | None = None
    m3_last_heartbeat_monotonic_ns: int | None = None
    m3_last_heartbeat_boot_id: str | None = None
    stream_started_monotonic_ns: int | None = None
    stream_started_boot_id: str | None = None
    stream_version: str | None = None
    m3_terminal_reason: str | None = None
    m3_exit_code: int | None = None
    authorized_cancel: bool = False
    cancel_revision: str | None = None
    cancel_monotonic_ns: int | None = None
    cancel_boot_id: str | None = None
    m1_terminal_monotonic_ns: int | None = None
    m1_terminal_boot_id: str | None = None
    m3_terminal_monotonic_ns: int | None = None
    m3_terminal_boot_id: str | None = None
    stream_frame_bytes: int | None = None
    normalized_event_bytes: int | None = None
    evidence_bytes: int | None = None
    stream_schema: str | None = None
    deadline_monotonic_ns: int | None = None
    deadline_boot_id: str | None = None
    deadline_version: str | None = None

    def __post_init__(self) -> None:
        _utc(self.observed_at)
        for name, value in vars(self).items():
            if name.endswith("_monotonic_ns") and value is not None and (
                    isinstance(value, bool) or not isinstance(value, int) or value < 0):
                raise ValueError(f"{name} must be a nonnegative integer")
        if self.m1_attempt_state not in (None, "active", "terminal", "unknown"):
            raise ValueError("m1_attempt_state is unsupported")
        if self.m3_process_state not in (None, "running", "terminal", "unknown"):
            raise ValueError("m3_process_state is unsupported")
        if self.m3_exit_code is not None and (isinstance(self.m3_exit_code, bool) or
                                              not isinstance(self.m3_exit_code, int) or
                                              not 0 <= self.m3_exit_code <= 255):
            raise ValueError("m3_exit_code must be in the range 0..255")
        if not isinstance(self.authorized_cancel, bool):
            raise ValueError("authorized_cancel must be a boolean")
        for name in ("stream_frame_bytes", "normalized_event_bytes", "evidence_bytes"):
            value = getattr(self, name)
            if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 0):
                raise ValueError(f"{name} must be a nonnegative integer")
        for name in ("m3_process_identity", "proc_identity"):
            value = getattr(self, name)
            if value is not None and not isinstance(value, ProcessIdentity):
                raise ValueError(f"{name} must be ProcessIdentity or None")


def _utc(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("observed_at must be a UTC RFC3339 timestamp")
    parsed = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError("observed_at must be a UTC RFC3339 timestamp")
    return parsed.isoformat().replace("+00:00", "Z")


def _is_version(value: str | None) -> bool:
    return isinstance(value, str) and len(value.split(".")) == 3 and all(
        component.isdigit() and (component == "0" or not component.startswith("0"))
        for component in value.split("."))


def _elapsed(now: int | None, now_boot: str | None, then: int | None, then_boot: str | None) -> int | None:
    if any(value is None for value in (now, now_boot, then, then_boot)) or now_boot != then_boot or now < then:
        return None
    return now - then


def _key(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _incident(event: NormalizedEvent, detector: str, kind: str, severity: str, confidence: str,
              window_key: str, at: str, facts: dict[str, object] | None = None,
              evidence: tuple[str, ...] | None = None) -> Incident:
    identity = json.dumps((event.run_id, event.attempt_id, event.execution_id, detector, window_key),
                          ensure_ascii=True, separators=(",", ":"))
    digest = _key(identity)
    return Incident(SCHEMA_VERSION, f"sha256:{digest}", event.run_id, event.task_id, event.attempt_id,
                    event.execution_id, detector, kind, severity, confidence, _utc(at), _utc(at), 1,
                    tuple(sorted((facts or {}).items())), evidence or (event.evidence_ref or event.event_id,),
                    "open", None, event.process_identity)


def _payload(event: NormalizedEvent) -> dict[str, object]:
    return dict(event.payload)


def detect_events(events: Iterable[NormalizedEvent], context: DetectorContext,
                  config: DetectorConfig = DetectorConfig()) -> tuple[Incident, ...]:
    """Emit only contract incidents; all timing and external facts are caller supplied."""
    result: list[Incident] = []
    parsed = tuple(events)
    if not parsed:
        return ()
    attempt_key = (parsed[0].run_id, parsed[0].task_id, parsed[0].attempt_id, parsed[0].execution_id,
                   parsed[0].process_identity)
    if any((item.run_id, item.task_id, item.attempt_id, item.execution_id, item.process_identity) != attempt_key
           for item in parsed):
        raise ValueError("detector input must contain one exact execution identity")
    for event in parsed:
        p = _payload(event)
        identity_ok = context.m3_process_identity is not None and \
            corroborate_process_identity(event.process_identity, context.m3_process_identity) == "match"
        if event.event_type == "process_exited" and isinstance(p.get("exit_code"), int) and p["exit_code"] != 0 \
                and context.m1_attempt_state == "active" and _is_version(context.m1_state_version) \
                and context.m3_process_state == "terminal" and _is_version(context.m3_state_version) \
                and identity_ok and not context.authorized_cancel:
            result.append(_incident(event, "unexpected_exit", "unexpected_exit", "high", "high",
                                    f"terminal:{event.event_id}", context.observed_at,
                                    {"process_exit": p["exit_code"]}))
        if event.event_type == "quota_error":
            source_code = p.get("source_code")
            code_key = f"code:{source_code}" if isinstance(source_code, str) else f"event:{event.event_id}"
            result.append(_incident(event, "quota_explicit", "quota_error", "high", "high",
                                    code_key, context.observed_at,
                                    {"source_code": source_code} if isinstance(source_code, str) else {}))
        if event.event_type == "auth_error":
            source_code = p.get("source_code")
            code_key = f"code:{source_code}" if isinstance(source_code, str) else f"event:{event.event_id}"
            result.append(_incident(event, "auth_failure", "auth_error", "high", "high",
                                    code_key, context.observed_at,
                                    {"source_code": source_code} if isinstance(source_code, str) else {}))
        if event.event_type == "transport_error":
            source_code = p.get("source_code")
            code_key = f"code:{source_code}" if isinstance(source_code, str) else f"event:{event.event_id}"
            result.append(_incident(event, "connection_error", "connection_error", "medium", "medium",
                                    code_key, context.observed_at,
                                    {"source_code": source_code} if isinstance(source_code, str) else {}))
        if event.event_type == "stderr_diagnostic" and p.get("diagnostic_code") in ("quota", "rate_limit") \
                and context.m3_exit_code not in (None, 0):
            result.append(_incident(event, "quota_probable", "quota_error", "medium", "medium",
                                    f"attempt:{event.attempt_id}", context.observed_at,
                                    {"diagnostic_code": "quota", "process_exit": context.m3_exit_code}))
        if event.event_type == "stderr_diagnostic" and p.get("diagnostic_code") in ("connection", "connection_lost") \
                and (context.m3_exit_code not in (None, 0) or context.m3_terminal_reason == "timeout"):
            result.append(_incident(event, "connection_error", "connection_error", "medium", "medium",
                                    f"connection:{event.event_id}", context.observed_at,
                                    {"diagnostic_code": "connection"}))
        if event.event_type == "stream_gap":
            facts = {k: p[k] for k in ("first_sequence", "last_sequence", "first_offset", "last_offset",
                                        "dropped_bytes", "dropped_frames") if k in p}
            result.append(_incident(event, "stream_gap", "stream_gap", "info", "medium",
                                    f"gap:{p.get('first_sequence', event.sequence)}:{p.get('first_offset', event.offset_bytes)}",
                                    context.observed_at, facts))

    event = parsed[-1]
    m3_timeout_confirmed = context.m3_process_state == "terminal" \
        and context.m3_terminal_reason == "timeout" and _is_version(context.m3_state_version) \
        and identity_ok
    if m3_timeout_confirmed and not context.authorized_cancel:
        result.append(_incident(event, "timeout", "timeout", "high", "high",
                                f"m3-timeout:{context.m3_terminal_monotonic_ns}", context.observed_at))
    deadline_elapsed = _elapsed(context.monotonic_now_ns, context.monotonic_boot_id,
                                 context.deadline_monotonic_ns, context.deadline_boot_id)
    if deadline_elapsed is not None and _is_version(context.deadline_version) \
            and not context.authorized_cancel and not m3_timeout_confirmed:
        result.append(_incident(event, "timeout", "timeout", "medium", "medium",
                                f"deadline:{context.deadline_monotonic_ns}", context.observed_at))
    if context.last_heartbeat_monotonic_ns is not None and _is_version(context.m3_state_version) and identity_ok:
        elapsed = _elapsed(context.monotonic_now_ns, context.monotonic_boot_id,
                           context.last_heartbeat_monotonic_ns, context.last_heartbeat_boot_id)
        if elapsed is not None and elapsed >= config.heartbeat_period_seconds * 3 * 1_000_000_000:
            result.append(_incident(event, "missed_heartbeat", "missed_heartbeat", "medium", "low",
                                    f"heartbeat:{context.last_heartbeat_monotonic_ns}", context.observed_at,
                                    {"window_seconds": config.heartbeat_period_seconds * 3}))
    alive = context.m3_process_state == "running" and _is_version(context.m3_state_version) and identity_ok
    quiet = _elapsed(context.monotonic_now_ns, context.monotonic_boot_id,
                     context.last_output_monotonic_ns, context.last_output_boot_id)
    if alive and quiet is not None and quiet >= config.silent_seconds * 1_000_000_000:
        result.append(_incident(event, "silent_but_alive", "silent_but_alive", "info", "low",
                                f"quiet-after-output:{context.last_output_monotonic_ns}",
                                context.observed_at, {"window_seconds": config.silent_seconds}))
    parser_anchor_ns = context.last_parser_event_monotonic_ns
    parser_anchor_boot = context.last_parser_event_boot_id
    if parser_anchor_ns is None:
        parser_anchor_ns = context.stream_started_monotonic_ns
        parser_anchor_boot = context.stream_started_boot_id
    parser_silence = _elapsed(context.monotonic_now_ns, context.monotonic_boot_id,
                              parser_anchor_ns, parser_anchor_boot)
    m3_io = _elapsed(context.monotonic_now_ns, context.monotonic_boot_id,
                     context.m3_last_io_monotonic_ns, context.m3_last_io_boot_id)
    m3_hb = _elapsed(context.monotonic_now_ns, context.monotonic_boot_id,
                     context.m3_last_heartbeat_monotonic_ns, context.m3_last_heartbeat_boot_id)
    if identity_ok and _is_version(context.m3_state_version) and _is_version(context.stream_version) \
            and parser_silence is not None \
            and parser_silence >= config.silent_seconds * 1_000_000_000 \
            and any(value is not None and value <= config.heartbeat_period_seconds * 3 * 1_000_000_000
                    for value in (m3_io, m3_hb)):
        schema = context.stream_schema or event.source_schema_version
        result.append(_incident(event, "provider_stream_silence", "provider_stream_silence", "info", "low",
                                f"schema:{schema}:after:{parser_anchor_ns}", context.observed_at,
                                {"source_code": "parser_silence"}))

    repetitive = _repetitive_candidate(parsed, config)
    if repetitive is not None:
        representative, signature, occurrences, first_mono = repetitive
        facts: dict[str, object] = {"occurrence_count": occurrences, "window_seconds": config.repetitive_window_seconds}
        if isinstance(signature[0], str):
            facts["tool_label"] = signature[0]
        if isinstance(signature[1], str):
            facts["argument_digest"] = signature[1]
        result.append(_incident(representative, "repetitive_activity", "repetitive_activity", "info", "low",
                                f"tool:{signature[0]}:{signature[1]}:{first_mono}",
                                context.observed_at, facts))

    if any(value is not None and value > limit for value, limit in (
        (context.stream_frame_bytes, config.max_frame_bytes),
        (context.normalized_event_bytes, config.max_event_bytes),
        (context.evidence_bytes, config.max_evidence_bytes))):
        bucket = context.monotonic_now_ns // (config.silent_seconds * 1_000_000_000) \
            if context.monotonic_now_ns is not None else event.sequence
        result.append(_incident(event, "oversized_output", "oversized_output", "info", "medium",
                                f"oversize:{event.stream}:{bucket}", context.observed_at))

    if _is_version(context.m3_state_version) and context.proc_identity is not None \
            and context.m3_process_identity is not None and \
            corroborate_process_identity(context.m3_process_identity, context.proc_identity) == "pid_reuse":
        old = context.m3_process_identity
        new = context.proc_identity
        pair = json.dumps((old.platform, old.host_boot_id, old.pid, old.start_ticks,
                           new.platform, new.host_boot_id, new.pid, new.start_ticks),
                          ensure_ascii=True, separators=(",", ":"))
        result.append(_incident(event, "pid_reuse", "pid_reuse", "high", "high",
                                pair,
                                context.observed_at))
    if context.authorized_cancel and context.cancel_revision is not None and context.cancel_monotonic_ns is not None \
            and context.m3_process_state == "terminal" and context.m3_terminal_reason == "cancelled" \
            and _is_version(context.m3_state_version) \
            and _elapsed(context.monotonic_now_ns, context.monotonic_boot_id,
                         context.cancel_monotonic_ns, context.cancel_boot_id) is not None:
        terminal_ns = context.m3_terminal_monotonic_ns
        terminal_boot = context.m3_terminal_boot_id
        if terminal_ns is None or terminal_boot != context.monotonic_boot_id:
            terminal_ns = None
        stream_types = {"tool_started", "tool_finished", "message_delta", "usage_reported",
                        "checkpoint_written", "stderr_diagnostic", "stream_gap", "unsupported_source_schema"}
        grace_ns = config.cancel_grace_seconds * 1_000_000_000
        if terminal_ns is not None and any(e.event_type in stream_types and _mono(e) is not None
                and context.m3_process_identity is not None
                and corroborate_process_identity(e.process_identity, context.m3_process_identity) == "match"
                and _is_version(context.m3_state_version)
                and e.host_boot_id == terminal_boot and _mono(e) > terminal_ns + grace_ns
                and _elapsed(context.monotonic_now_ns, context.monotonic_boot_id,
                             _mono(e), e.host_boot_id) is not None for e in parsed):
            result.append(_incident(event, "stale_post_cancel", "stale_post_cancel", "medium", "medium",
                                    f"cancel:{context.cancel_revision}", context.observed_at))

    active_age = _elapsed(context.monotonic_now_ns, context.monotonic_boot_id,
                          context.m1_terminal_monotonic_ns, context.m1_terminal_boot_id)
    if active_age is not None and active_age >= config.disagreement_seconds * 1_000_000_000 and \
            context.m1_attempt_state == "terminal" and _is_version(context.m1_state_version) \
            and _is_version(context.m3_state_version) and context.m3_process_state == "running" and identity_ok:
        result.append(_incident(event, "source_disagreement", "source_disagreement", "medium", "medium",
                                "m1_terminal_m3_running", context.observed_at,
                                {"expected_state": "terminal", "observed_state": "running"}))
    if _is_version(context.m3_state_version) and context.m3_process_state == "terminal" \
            and context.m3_terminal_monotonic_ns is not None:
        frame_age = _elapsed(context.monotonic_now_ns, context.monotonic_boot_id,
                             context.m3_terminal_monotonic_ns, context.m3_terminal_boot_id)
        later = any(_mono(e) is not None and e.host_boot_id == context.m3_terminal_boot_id and
                    _mono(e) > context.m3_terminal_monotonic_ns for e in parsed)
        if frame_age is not None and frame_age >= config.disagreement_seconds * 1_000_000_000 and later and identity_ok:
            result.append(_incident(event, "source_disagreement", "source_disagreement", "medium", "medium",
                                    "m3_terminal_later_stream", context.observed_at,
                                    {"expected_state": "terminal", "observed_state": "stream_active"}))
    return tuple(result)


def _mono(event: NormalizedEvent) -> int | None:
    return event.received_monotonic_ns


def _repetitive_candidate(events: tuple[NormalizedEvent, ...], config: DetectorConfig) -> tuple[
        NormalizedEvent, tuple[str | None, str | None], int, int] | None:
    if any(event.received_monotonic_ns is None or event.host_boot_id is None for event in events):
        return None
    boots = {event.host_boot_id for event in events}
    if len(boots) != 1:
        return None
    unique: dict[str, NormalizedEvent] = {}
    for event in events:
        previous = unique.setdefault(event.event_id, event)
        if previous != event:
            return None
    timed = [event for event in unique.values() if _mono(event) is not None and event.host_boot_id is not None]
    timed.sort(key=lambda item: (_mono(item), item.sequence, item.event_id))
    window_ns = config.repetitive_window_seconds * 1_000_000_000
    for current in reversed(timed):
        if current.event_type != "tool_started":
            continue
        payload = _payload(current)
        signature = (payload.get("tool_label"), payload.get("argument_digest"))
        if not isinstance(signature[0], str):
            continue
        current_ns = _mono(current)
        window = [item for item in timed if item.host_boot_id == current.host_boot_id and
                  current_ns - window_ns <= _mono(item) <= current_ns]
        if any(item.event_type != "tool_started" or
               (_payload(item).get("tool_label"), _payload(item).get("argument_digest")) != signature
               for item in window):
            continue
        if len(window) >= config.repetitive_count:
            first_ns = _mono(window[0])
            if current_ns - first_ns <= window_ns:
                return current, signature, len(window), first_ns
    return None


__all__ = ["DetectorConfig", "DetectorContext", "detect_events"]
