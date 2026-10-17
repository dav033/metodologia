"""Normalize M3 output at the methodology boundary and commit it to M4 before queue acknowledgment."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime

from bt_scheduler_monitor_adapter import (
    NORMALIZER_VERSION,
    SCHEMA_VERSION,
    BoundedFrameQueue,
    CollectorOutput,
    DetectorContext,
    DroppedRange,
    ExecutionOutputFrame,
    JsonlCollector,
    MetricSample,
    MonitorStore,
    NormalizedEvent,
    ProcessIdentity,
    ProviderGap,
    ProviderRecord,
    SourceCursor,
    StreamGap,
    StreamGapRecord,
    allowlist_payload,
    detect_events,
)


@dataclass(frozen=True)
class _FrameContext:
    run_id: str
    plan_revision: int
    task_id: str
    attempt_id: str
    execution_id: str
    process_identity: ProcessIdentity
    provider: str
    stream: str
    received_at: str
    received_monotonic_ns: int | None
    host_boot_id: str | None
    profile_id: str | None
    model: str | None

    @classmethod
    def from_frame(cls, frame: ExecutionOutputFrame) -> _FrameContext:
        return cls(frame.run_id, frame.plan_revision, frame.task_id, frame.attempt_id, frame.execution_id,
                   frame.process_identity, frame.provider, frame.stream, frame.received_at,
                   frame.received_monotonic_ns, frame.host_boot_id, frame.profile_id, frame.model)


@dataclass(frozen=True)
class _PendingWrite:
    events: tuple[NormalizedEvent, ...]
    metrics: tuple[MetricSample, ...]
    gaps: tuple[StreamGapRecord, ...]
    cursors: tuple[SourceCursor, ...]
    stream_key: tuple[str, str]
    input_gap: StreamGap | None = None


class M4StreamIngestor:
    """Keep queued M3 input until every normalized output and source cursor commits."""

    _PARSERS = frozenset(("claude", "codex", "antigravity", "gemini_fixture"))

    def __init__(self, queue: BoundedFrameQueue, store: MonitorStore):
        self.queue = queue
        self.store = store
        self._collectors: dict[str, JsonlCollector] = {}
        self._fed_frames: dict[int, ExecutionOutputFrame] = {}
        self._contexts: dict[tuple[str, str], _FrameContext] = {}
        self._pending_write: _PendingWrite | None = None

    @staticmethod
    def _stable_id(prefix: str, value: object) -> str:
        encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return prefix + hashlib.sha256(encoded).hexdigest()

    def _collector(self, frame: ExecutionOutputFrame) -> JsonlCollector | None:
        if frame.provider not in self._PARSERS:
            return None
        current = self._collectors.get(frame.execution_id)
        if current is None:
            current = JsonlCollector(frame.provider)
            self._collectors[frame.execution_id] = current
        return current

    def _event(self, context: _FrameContext, *, event_id: str, event_type: str,
               source_event_type: str, source_schema_version: str, quality: str,
               payload: dict[str, object] | tuple[tuple[str, object], ...],
               sequence: int, offset_bytes: int, source_event_id: str | None = None,
               source_occurred_at: str | None = None, unknown_field_count: int = 0,
               unknown_field_digest: str | None = None) -> NormalizedEvent:
        allowed = allowlist_payload(event_type, dict(payload))
        return NormalizedEvent(
            schema_version=SCHEMA_VERSION, event_id=event_id, source_schema_version=source_schema_version,
            normalizer_version=NORMALIZER_VERSION, run_id=context.run_id, plan_revision=context.plan_revision,
            task_id=context.task_id, attempt_id=context.attempt_id, execution_id=context.execution_id,
            process_identity=context.process_identity, provider=context.provider, profile_id=context.profile_id,
            model=context.model, event_type=event_type, source_event_type=source_event_type,
            received_at=context.received_at, stream=context.stream, sequence=sequence, offset_bytes=offset_bytes,
            payload=allowed.fields, quality=quality, source_event_id=source_event_id,
            source_occurred_at=source_occurred_at, received_monotonic_ns=context.received_monotonic_ns,
            host_boot_id=context.host_boot_id, unknown_field_count=unknown_field_count,
            unknown_field_digest=unknown_field_digest,
        )

    def _record_event(self, context: _FrameContext, record: ProviderRecord, index: int
                      ) -> tuple[NormalizedEvent | None, MetricSample | None, SourceCursor]:
        parsed = record.parsed
        cursor = SourceCursor(context.execution_id, context.stream, context.host_boot_id,
                              record.last_sequence, record.last_offset)
        if parsed.status != "parsed" or parsed.event_type is None or parsed.source_event_type is None:
            return None, None, cursor
        values = dict(parsed.payload)
        event_id = self._stable_id("m4-event:", (context.execution_id, context.stream, record.first_sequence,
                                record.first_offset, record.last_sequence, record.last_offset,
                                parsed.source_event_id, index, parsed.event_type))
        event = self._event(context, event_id=event_id, event_type=parsed.event_type,
                            source_event_type=parsed.source_event_type,
                            source_schema_version=parsed.source_schema_version, quality=parsed.quality,
                            payload=values, sequence=record.first_sequence, offset_bytes=record.first_offset,
                            source_event_id=parsed.source_event_id, source_occurred_at=parsed.source_occurred_at,
                            unknown_field_count=parsed.unknown_field_count,
                            unknown_field_digest=parsed.unknown_field_digest)
        sample = None
        if parsed.event_type == "usage_reported":
            name, value, unit = values.get("metric_name"), values.get("value"), values.get("unit")
            source, count = values.get("source"), values.get("sample_count")
            if not isinstance(name, str) or not isinstance(unit, str) or not isinstance(source, str) \
                    or not isinstance(count, int) or isinstance(count, bool):
                raise ValueError("provider usage event does not meet the M4 metric contract")
            metric_id = self._stable_id("m4-metric:", event_id)
            comparability_key = self._stable_id("m4-usage:",
                (context.provider, context.profile_id, context.model, name, unit))
            sample = MetricSample(
                schema_version=SCHEMA_VERSION, metric_id=metric_id, provider=context.provider,
                name=name, value=value, unit=unit, source=source, observed_at=context.received_at,
                quality=parsed.quality, sample_count=count, comparability_key=comparability_key,
                profile_id=context.profile_id, model=context.model,
                unknown_field_count=parsed.unknown_field_count,
                unknown_field_digest=parsed.unknown_field_digest,
            )
        return event, sample, cursor

    def _gap_event(self, context: _FrameContext, gap: ProviderGap, index: int) -> NormalizedEvent:
        payload = {"cause": gap.reason, "first_sequence": gap.first_sequence, "last_sequence": gap.last_sequence,
                   "first_offset": gap.first_offset, "last_offset": gap.last_offset,
                   "dropped_bytes": gap.byte_count, "dropped_frames": gap.frame_count,
                   "unknown_field_count": 0}
        event_id = self._stable_id("m4-gap:", (context.execution_id, gap.stream, gap.first_sequence,
                                gap.first_offset, gap.last_sequence, gap.last_offset, gap.reason, gap.digest, index))
        return self._event(context, event_id=event_id, event_type="stream_gap", source_event_type=gap.reason,
                           source_schema_version="m3-stream/1", quality="partial", payload=payload,
                           sequence=gap.first_sequence, offset_bytes=gap.first_offset)

    def _make_write(self, context: _FrameContext, output: CollectorOutput, *,
                    source_gap: StreamGap | None = None) -> _PendingWrite | None:
        events: list[NormalizedEvent] = []
        metrics: list[MetricSample] = []
        gaps: list[StreamGapRecord] = []
        cursors: list[SourceCursor] = []
        for index, record in enumerate(output.records):
            event, sample, cursor = self._record_event(context, record, index)
            cursors.append(cursor)
            if event is not None:
                events.append(event)
            if sample is not None:
                metrics.append(sample)
        for index, provider_gap in enumerate(output.gaps):
            cursor = SourceCursor(context.execution_id, context.stream, context.host_boot_id,
                                  provider_gap.last_sequence, provider_gap.last_offset)
            cursors.append(cursor)
            events.append(self._gap_event(context, provider_gap, index))
        if source_gap is not None:
            last_sequence = source_gap.last_sequence if source_gap.last_sequence is not None else source_gap.sequence
            last_offset = source_gap.last_offset_bytes if source_gap.last_offset_bytes is not None else source_gap.offset_bytes
            gaps.append(StreamGapRecord(
                gap_id=self._stable_id("m3-gap:", (source_gap.execution_id, source_gap.stream,
                    source_gap.sequence, source_gap.offset_bytes, source_gap.source_id)),
                execution_id=context.execution_id, stream=source_gap.stream,
                first_sequence=source_gap.sequence, last_sequence=last_sequence,
                first_offset=source_gap.offset_bytes, last_offset=last_offset,
                dropped_bytes=source_gap.dropped_bytes, dropped_frames=source_gap.dropped_frames,
                reason=source_gap.reason[:64], recorded_at=datetime.now(UTC).isoformat(),
            ))
            cursors.append(SourceCursor(context.execution_id, source_gap.stream, context.host_boot_id,
                                        last_sequence, last_offset))
        if not (events or metrics or gaps or cursors):
            return None
        return _PendingWrite(tuple(events), tuple(metrics), tuple(gaps), tuple(cursors),
                             (context.execution_id, context.stream), source_gap)

    def _safe_frames(self, execution_id: str, stream: str) -> tuple[ExecutionOutputFrame, ...]:
        collector = self._collectors.get(execution_id)
        pending_start = collector.pending_start(stream) if collector is not None else None
        safe = []
        for frame in self._fed_frames.values():
            if frame.execution_id != execution_id or frame.stream != stream:
                continue
            frame_end = (frame.sequence, frame.offset_bytes + len(frame.data))
            if pending_start is None or frame_end <= pending_start:
                safe.append(frame)
        return tuple(safe)

    def _ack_safe_frames(self, execution_id: str, stream: str) -> None:
        safe = self._safe_frames(execution_id, stream)
        if safe and self.queue.acknowledge_frames(safe):
            for frame in safe:
                self._fed_frames.pop(id(frame), None)

    def _commit_pending(self) -> None:
        pending = self._pending_write
        if pending is None:
            return
        self.store.append_batch(events=pending.events, metrics=pending.metrics,
                                gaps=pending.gaps, cursors=pending.cursors)
        for event in pending.events:
            for incident in detect_events((event,), DetectorContext(event.received_at)):
                self.store.enqueue_incident(incident, "m4:" + incident.incident_id)
        self._pending_write = None
        if pending.input_gap is not None:
            self.queue.acknowledge_gap(pending.input_gap)
        self._ack_safe_frames(*pending.stream_key)

    def _submit(self, pending: _PendingWrite | None) -> None:
        if pending is None:
            return
        self._pending_write = pending
        self._commit_pending()

    def consume(self, execution_id: str, *, terminal_drained: bool = False) -> int:
        """Persist queued frames and source gaps for one execution; retries retain exact uncommitted input."""
        if not isinstance(execution_id, str) or not execution_id:
            raise ValueError("execution_id must be non-empty text")
        committed = 0
        self._commit_pending()
        for item in self.queue.pending_inputs():
            if isinstance(item, ExecutionOutputFrame):
                if item.execution_id != execution_id or id(item) in self._fed_frames:
                    continue
                self._fed_frames[id(item)] = item
                context = _FrameContext.from_frame(item)
                self._contexts[(item.execution_id, item.stream)] = context
                collector = self._collector(item)
                if collector is None:
                    digest = "sha256:" + hashlib.sha256(item.data).hexdigest()
                    unsupported = ProviderGap("unsupported_provider", item.stream, item.sequence, item.sequence,
                                              item.offset_bytes, item.offset_bytes + len(item.data), len(item.data),
                                              1, digest)
                    output = CollectorOutput(gaps=(unsupported,))
                else:
                    output = collector.feed(item)
                pending = self._make_write(context, output)
                if pending is not None:
                    self._submit(pending)
                    committed += 1
            elif item.execution_id == execution_id:
                context = self._contexts.get((execution_id, item.stream))
                if context is None:
                    next_frame = next((frame for frame in self.queue.pending_frames()
                                       if frame.execution_id == execution_id and frame.stream == item.stream), None)
                    if next_frame is not None:
                        context = _FrameContext.from_frame(next_frame)
                if context is None:
                    last_sequence = item.last_sequence if item.last_sequence is not None else item.sequence
                    last_offset = item.last_offset_bytes if item.last_offset_bytes is not None else item.offset_bytes
                    raw_gap = StreamGapRecord(
                        gap_id=self._stable_id("m3-gap:", (item.execution_id, item.stream, item.sequence,
                                            item.offset_bytes, item.source_id)),
                        execution_id=execution_id, stream=item.stream, first_sequence=item.sequence,
                        last_sequence=last_sequence, first_offset=item.offset_bytes, last_offset=last_offset,
                        dropped_bytes=item.dropped_bytes, dropped_frames=item.dropped_frames,
                        reason=item.reason[:64], recorded_at=datetime.now(UTC).isoformat(),
                    )
                    cursor = SourceCursor(execution_id, item.stream, item.host_boot_id, last_sequence, last_offset)
                    pending = _PendingWrite((), (), (raw_gap,), (cursor,), (execution_id, item.stream), item)
                    self._submit(pending)
                    committed += 1
                    continue
                collector = self._collectors.get(execution_id)
                output = CollectorOutput()
                last_sequence = item.last_sequence if item.last_sequence is not None else item.sequence
                last_offset = item.last_offset_bytes if item.last_offset_bytes is not None else item.offset_bytes
                if collector is not None:
                    dropped = DroppedRange(item.stream, item.sequence, last_sequence, item.offset_bytes,
                                           last_offset, item.dropped_bytes, item.dropped_frames)
                    output = collector.feed_source_gap(dropped)
                if not output.records and not output.gaps:
                    output = CollectorOutput(gaps=(ProviderGap(
                        item.reason, item.stream, item.sequence, last_sequence,
                        item.offset_bytes, last_offset, item.dropped_bytes, item.dropped_frames,
                        "sha256:" + hashlib.sha256(b"").hexdigest()),))
                self._submit(self._make_write(context, output, source_gap=item))
                committed += 1
        if terminal_drained:
            collector = self._collectors.get(execution_id)
            if collector is not None:
                for stream in ("stdout", "stderr"):
                    context = self._contexts.get((execution_id, stream))
                    if context is None:
                        continue
                    output = collector.finish(stream)
                    if output.records or output.gaps:
                        self._submit(self._make_write(context, output))
                        committed += 1
                    self._ack_safe_frames(execution_id, stream)
            self._collectors.pop(execution_id, None)
            for key in tuple(self._contexts):
                if key[0] == execution_id:
                    self._contexts.pop(key, None)
        return committed


__all__ = ["M4StreamIngestor"]
