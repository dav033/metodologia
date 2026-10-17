"""Fixture-driven provider event parsers; parsed values contain only bounded metadata."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from ..serialization import _unknown_metadata
from ..validation import EVENT_TYPES, _PAYLOAD_FIELDS, _timestamp, validate_payload, validate_safe_token

MAX_LINE_BYTES = 65_536
_STREAMS = ("stdout", "stderr")


@dataclass(frozen=True)
class ParseResult:
    status: str
    code: str
    source_schema_version: str
    source_event_type: str | None = None
    event_type: str | None = None
    payload: tuple[tuple[str, str | int | float | bool | None], ...] = ()
    source_event_id: str | None = None
    source_occurred_at: str | None = None
    quality: str = "unknown"
    unknown_field_count: int = 0
    unknown_field_digest: str | None = None


@dataclass(frozen=True)
class ProviderRecord:
    parsed: ParseResult
    stream: str
    first_sequence: int
    last_sequence: int
    first_offset: int
    last_offset: int


@dataclass(frozen=True)
class ProviderGap:
    reason: str
    stream: str
    first_sequence: int
    last_sequence: int
    first_offset: int
    last_offset: int
    byte_count: int
    frame_count: int
    digest: str


@dataclass(frozen=True)
class CollectorOutput:
    records: tuple[ProviderRecord, ...] = ()
    gaps: tuple[ProviderGap, ...] = ()


@dataclass
class _StreamState:
    buffer: bytearray
    first_sequence: int | None = None
    last_sequence: int | None = None
    first_offset: int | None = None
    last_offset: int | None = None
    previous_sequence: int | None = None
    expected_offset: int | None = None
    discarding: bool = False
    discard_hash: Any = None
    discard_bytes: int = 0
    discard_first_sequence: int | None = None
    discard_last_sequence: int | None = None
    discard_first_offset: int | None = None
    discard_last_offset: int | None = None


def digest_json(value: object) -> tuple[int, str]:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                         allow_nan=False).encode("utf-8", "strict")
    if len(encoded) > MAX_LINE_BYTES:
        raise ValueError("nested_value_too_large")
    return len(encoded), "sha256:" + hashlib.sha256(encoded).hexdigest()


def safe_tool_label(value: object) -> str:
    try:
        validate_safe_token("tool_label", value)
    except (ValueError, TypeError):
        return "tool"
    return value if isinstance(value, str) else "tool"


class JsonlCollector:
    """Reassemble bounded provider JSONL from M3 frames and expose only parsed data or gap metadata."""

    def __init__(self, provider: str):
        if provider not in ("claude", "codex", "antigravity", "gemini_fixture"):
            raise ValueError("provider has no fixture normalizer")
        self.provider = provider
        self._states = {stream: _StreamState(bytearray()) for stream in _STREAMS}

    def _normalize(self, line: bytes) -> tuple[ParseResult, ...]:
        from . import antigravity, claude, codex, gemini

        parser = {"claude": claude, "codex": codex, "antigravity": antigravity,
                  "gemini_fixture": gemini}[self.provider]
        return parser.normalize(line)

    @staticmethod
    def _clear_line(state: _StreamState) -> None:
        state.buffer.clear()
        state.first_sequence = state.last_sequence = None
        state.first_offset = state.last_offset = None

    @staticmethod
    def _gap(reason: str, stream: str, first_sequence: int, last_sequence: int,
             first_offset: int, last_offset: int, byte_count: int, frame_count: int, digest: str) -> ProviderGap:
        return ProviderGap(reason, stream, first_sequence, last_sequence, first_offset, last_offset,
                           byte_count, frame_count, digest)

    def _finish_line(self, stream: str, state: _StreamState, *, end_offset: int, newline: bool,
                     records: list[ProviderRecord], gaps: list[ProviderGap]) -> None:
        if state.first_sequence is None or state.last_sequence is None or state.first_offset is None:
            return
        raw = bytes(state.buffer)
        parsed = self._normalize(raw)
        bad = [item for item in parsed if item.status in ("malformed", "unsupported")]
        if bad:
            code = bad[0].code
            reason = {"invalid_utf8": "invalid_utf8", "line_too_large": "oversized_line",
                      "invalid_json": "truncated_input" if not newline else "malformed_json",
                      "event_not_object": "unsupported_event"}.get(code, "malformed_event"
                          if bad[0].status == "malformed" else "unsupported_event")
            gaps.append(self._gap(reason, stream, state.first_sequence, state.last_sequence,
                                  state.first_offset, end_offset, len(raw),
                                  state.last_sequence - state.first_sequence + 1,
                                  "sha256:" + hashlib.sha256(raw).hexdigest()))
        else:
            for item in parsed:
                records.append(ProviderRecord(item, stream, state.first_sequence, state.last_sequence,
                                              state.first_offset, end_offset))
        self._clear_line(state)

    def _finish_oversized(self, stream: str, state: _StreamState, gaps: list[ProviderGap]) -> None:
        if not state.discarding:
            return
        gaps.append(self._gap("oversized_line", stream, state.discard_first_sequence or 0,
                              state.discard_last_sequence or state.discard_first_sequence or 0,
                              state.discard_first_offset or 0, state.discard_last_offset or 0,
                              state.discard_bytes,
                              (state.discard_last_sequence or 0) - (state.discard_first_sequence or 0) + 1,
                              "sha256:" + state.discard_hash.hexdigest()))
        state.discarding = False
        state.discard_hash = None
        state.discard_bytes = 0
        state.discard_first_sequence = state.discard_last_sequence = None
        state.discard_first_offset = state.discard_last_offset = None

    def feed(self, frame: object) -> CollectorOutput:
        from ..contracts import ExecutionOutputFrame

        if not isinstance(frame, ExecutionOutputFrame):
            raise ValueError("frame must be ExecutionOutputFrame")
        if frame.stream not in self._states:
            raise ValueError("unsupported stream")
        stream = frame.stream
        state = self._states[stream]
        records: list[ProviderRecord] = []
        gaps: list[ProviderGap] = []
        if frame.provider != self.provider and not (self.provider == "gemini_fixture" and frame.provider == "gemini_fixture"):
            raw = bytes(state.buffer)
            self._finish_oversized(stream, state, gaps)
            if raw:
                first_sequence = state.first_sequence if state.first_sequence is not None else frame.sequence
                last_sequence = state.last_sequence if state.last_sequence is not None else first_sequence
                first_offset = state.first_offset if state.first_offset is not None else frame.offset_bytes
                end_offset = state.expected_offset if state.expected_offset is not None else first_offset + len(raw)
                gaps.append(self._gap("truncated_input", stream, first_sequence, last_sequence,
                                      first_offset, end_offset, len(raw), max(1, last_sequence - first_sequence + 1),
                                      "sha256:" + hashlib.sha256(raw).hexdigest()))
            if raw or state.first_sequence is not None:
                self._clear_line(state)
            digest = hashlib.sha256(frame.data).hexdigest()
            gaps.append(self._gap("provider_mismatch", stream, frame.sequence, frame.sequence,
                                  frame.offset_bytes, frame.offset_bytes + len(frame.data), len(frame.data), 1,
                                  "sha256:" + digest))
            state.previous_sequence = frame.sequence
            state.expected_offset = frame.offset_bytes + len(frame.data)
            return CollectorOutput(tuple(records), tuple(gaps))
        discontinuity = None
        missing_frames = 0
        missing_bytes = 0
        if state.previous_sequence is not None:
            missing_frames = frame.sequence - state.previous_sequence - 1
            if missing_frames != 0:
                discontinuity = "sequence_discontinuity"
            if frame.offset_bytes != state.expected_offset and discontinuity is None:
                discontinuity = "offset_discontinuity"
            if frame.offset_bytes > (state.expected_offset or 0):
                missing_bytes = frame.offset_bytes - (state.expected_offset or 0)
        if discontinuity:
            pending = bytes(state.buffer)
            pending_first_sequence = state.first_sequence
            pending_last_sequence = state.last_sequence
            pending_first_offset = state.first_offset
            expected_offset = state.expected_offset if state.expected_offset is not None else frame.offset_bytes
            prior_sequence = state.previous_sequence if state.previous_sequence is not None else frame.sequence
            self._finish_oversized(stream, state, gaps)
            self._clear_line(state)
            pending_frame_count = (pending_last_sequence - pending_first_sequence + 1
                                   if pending_first_sequence is not None and pending_last_sequence is not None else 0)
            if pending:
                gaps.append(self._gap("truncated_input", stream,
                                      pending_first_sequence if pending_first_sequence is not None else prior_sequence,
                                      pending_last_sequence if pending_last_sequence is not None else prior_sequence,
                                      pending_first_offset if pending_first_offset is not None else expected_offset,
                                      expected_offset, len(pending),
                                      max(1, pending_frame_count),
                                      "sha256:" + hashlib.sha256(pending).hexdigest()))
            if missing_frames > 0:
                gaps.append(self._gap("sequence_discontinuity", stream, prior_sequence + 1, frame.sequence - 1,
                                      expected_offset, max(expected_offset, frame.offset_bytes), missing_bytes,
                                      missing_frames, "sha256:" + hashlib.sha256(b"").hexdigest()))
            elif missing_frames < 0:
                gaps.append(self._gap("sequence_discontinuity", stream, frame.sequence, prior_sequence,
                                      min(expected_offset, frame.offset_bytes), max(expected_offset, frame.offset_bytes),
                                      0, 0, "sha256:" + hashlib.sha256(b"").hexdigest()))
            else:
                gaps.append(self._gap("offset_discontinuity", stream, prior_sequence, prior_sequence,
                                      min(expected_offset, frame.offset_bytes), max(expected_offset, frame.offset_bytes),
                                      missing_bytes, 0, "sha256:" + hashlib.sha256(b"").hexdigest()))
        data = frame.data
        for index, byte in enumerate(data):
            offset = frame.offset_bytes + index
            if state.discarding:
                if byte == 10:
                    state.discard_last_sequence = frame.sequence
                    state.discard_last_offset = offset + 1
                    self._finish_oversized(stream, state, gaps)
                    continue
                state.discard_hash.update(bytes((byte,)))
                state.discard_bytes += 1
                state.discard_last_sequence = frame.sequence
                state.discard_last_offset = offset + 1
                continue
            if byte == 10:
                state.last_sequence = frame.sequence
                state.last_offset = offset + 1
                self._finish_line(stream, state, end_offset=offset + 1, newline=True,
                                  records=records, gaps=gaps)
                continue
            if state.first_sequence is None:
                state.first_sequence = frame.sequence
                state.first_offset = offset
            state.last_sequence = frame.sequence
            state.last_offset = offset + 1
            if len(state.buffer) >= MAX_LINE_BYTES:
                state.discarding = True
                state.discard_hash = hashlib.sha256(bytes(state.buffer))
                state.discard_bytes = len(state.buffer)
                state.discard_first_sequence = state.first_sequence
                state.discard_last_sequence = frame.sequence
                state.discard_first_offset = state.first_offset
                state.discard_last_offset = offset
                state.buffer.clear()
                state.first_sequence = state.last_sequence = None
                state.first_offset = state.last_offset = None
                state.discard_hash.update(bytes((byte,)))
                state.discard_bytes += 1
                continue
            state.buffer.append(byte)
        state.previous_sequence = frame.sequence
        state.expected_offset = frame.offset_bytes + len(frame.data)
        return CollectorOutput(tuple(records), tuple(gaps))

    def feed_source_gap(self, gap: object) -> CollectorOutput:
        from ..contracts import DroppedRange

        if not isinstance(gap, DroppedRange) or gap.stream not in self._states:
            raise ValueError("gap must be a supported DroppedRange")
        state = self._states[gap.stream]
        pending = bytes(state.buffer)
        pending_first_sequence = state.first_sequence
        pending_last_sequence = state.last_sequence
        pending_first_offset = state.first_offset
        pending_frame_count = (pending_last_sequence - pending_first_sequence + 1
                               if pending_first_sequence is not None and pending_last_sequence is not None else 0)
        first_sequence = min(pending_first_sequence if pending_first_sequence is not None else gap.first_sequence,
                             gap.first_sequence)
        last_sequence = max(pending_last_sequence if pending_last_sequence is not None else gap.last_sequence,
                            gap.last_sequence)
        first_offset = min(pending_first_offset if pending_first_offset is not None else gap.first_offset,
                           gap.first_offset)
        last_offset = max(state.expected_offset if pending else gap.last_offset, gap.last_offset)
        prior_gaps: list[ProviderGap] = []
        self._finish_oversized(gap.stream, state, prior_gaps)
        self._clear_line(state)
        digest = hashlib.sha256(pending).hexdigest()
        overlap = 0
        if pending_first_sequence is not None and pending_last_sequence is not None:
            overlap = max(0, min(pending_last_sequence, gap.last_sequence) -
                          max(pending_first_sequence, gap.first_sequence) + 1)
            overlap = min(overlap, pending_frame_count, gap.dropped_frames)
        frame_count = pending_frame_count + gap.dropped_frames - overlap
        result = self._gap("source_gap", gap.stream, first_sequence, last_sequence, first_offset,
                           last_offset, len(pending) + gap.dropped_bytes,
                           frame_count, "sha256:" + digest)
        state.previous_sequence = gap.last_sequence
        state.expected_offset = gap.last_offset
        return CollectorOutput(gaps=tuple(prior_gaps) + (result,))

    def finish(self, stream: str) -> CollectorOutput:
        if stream not in self._states:
            raise ValueError("unsupported stream")
        state = self._states[stream]
        records: list[ProviderRecord] = []
        gaps: list[ProviderGap] = []
        self._finish_oversized(stream, state, gaps)
        self._finish_line(stream, state, end_offset=state.last_offset or 0, newline=False,
                          records=records, gaps=gaps)
        return CollectorOutput(tuple(records), tuple(gaps))

    def pending_start(self, stream: str) -> tuple[int, int] | None:
        """Return the first source coordinate still held in an incomplete or oversized line."""
        if stream not in self._states:
            raise ValueError("unsupported stream")
        state = self._states[stream]
        if state.discarding and state.discard_first_sequence is not None and state.discard_first_offset is not None:
            return state.discard_first_sequence, state.discard_first_offset
        if state.first_sequence is not None and state.first_offset is not None:
            return state.first_sequence, state.first_offset
        return None


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate_json_key")
        value[key] = item
    return value


def decode_line(raw: bytes | str, schema: str) -> tuple[dict[str, Any] | None, ParseResult | None]:
    if isinstance(raw, bytes):
        if len(raw) > MAX_LINE_BYTES:
            return None, ParseResult("malformed", "line_too_large", schema)
        try:
            text = raw.decode("utf-8", "strict")
        except UnicodeDecodeError:
            return None, ParseResult("malformed", "invalid_utf8", schema)
    elif isinstance(raw, str):
        try:
            if len(raw.encode("utf-8", "strict")) > MAX_LINE_BYTES:
                return None, ParseResult("malformed", "line_too_large", schema)
        except UnicodeError:
            return None, ParseResult("malformed", "invalid_utf8", schema)
        text = raw
    else:
        return None, ParseResult("malformed", "invalid_input_type", schema)
    try:
        value = json.loads(text, object_pairs_hook=_unique_object,
                           parse_constant=lambda _: (_ for _ in ()).throw(ValueError("invalid number")))
    except (json.JSONDecodeError, ValueError, RecursionError):
        return None, ParseResult("malformed", "invalid_json", schema)
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        return None, ParseResult("unsupported", "event_not_object", schema)
    return value, None


def result(schema: str, source_type: str, event_type: str, payload: dict[str, object], obj: dict[str, Any],
           known: set[str], *, event_id: object = None, occurred_at: object = None,
           nested: tuple[tuple[str, dict[str, Any], set[str]], ...] = (), quality: str = "reported") -> ParseResult:
    try:
        if event_type not in EVENT_TYPES or not set(payload).issubset(_PAYLOAD_FIELDS[event_type]):
            return ParseResult("malformed", "invalid_event_payload", schema)
        validate_payload(payload)
    except (ValueError, TypeError, UnicodeError, RecursionError):
        return ParseResult("malformed", "invalid_event_payload", schema)
    try:
        extras = ((prefix + ".", key, value) for prefix, source, source_known in nested
                  for key, value in source.items() if key not in source_known)
        count, digest = _unknown_metadata(obj, known, extras)
    except (ValueError, TypeError, UnicodeError, RecursionError):
        return ParseResult("malformed", "invalid_unknown_fields", schema)
    if occurred_at is not None:
        try:
            _timestamp("source_occurred_at", occurred_at)
        except (ValueError, TypeError):
            return ParseResult("malformed", "invalid_source_timestamp", schema)
    if event_id is not None:
        try:
            validate_safe_token("source_event_id", event_id)
        except (ValueError, TypeError):
            event_id = None
    return ParseResult("parsed", "ok", schema, source_type, event_type, tuple(sorted(payload.items())),
                       event_id,
                       occurred_at if isinstance(occurred_at, str) and len(occurred_at) <= 128 else None,
                       quality, count, digest)


__all__ = ["CollectorOutput", "JsonlCollector", "MAX_LINE_BYTES", "ParseResult", "ProviderGap",
           "ProviderRecord", "digest_json", "safe_tool_label"]
