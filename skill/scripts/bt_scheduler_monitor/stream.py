"""Bounded in-memory queue for frames received by the M3 methodology adapter."""
from __future__ import annotations

import queue
import threading
from dataclasses import dataclass

from .contracts import ExecutionOutputFrame, NormalizedEvent
from .store import MonitorStore, SourceCursor

MAX_QUEUE_FRAMES = 10_000
MAX_QUEUE_BYTES = 16 * 1024 * 1024
MAX_TRACKED_SOURCE_GAPS = MAX_QUEUE_FRAMES
MAX_PENDING_GAPS = MAX_QUEUE_FRAMES
MAX_SOURCE_ID_LENGTH = 512


class GapCapacityError(ValueError):
    """The bounded gap ledger is full; persist pending gaps before draining more input."""


@dataclass(frozen=True)
class StreamGap:
    stream: str
    sequence: int
    offset_bytes: int
    dropped_bytes: int
    reason: str
    last_sequence: int | None = None
    last_offset_bytes: int | None = None
    dropped_frames: int = 1
    coalesced: bool = False
    source_id: str | None = None
    execution_id: str | None = None
    host_boot_id: str | None = None


class BoundedFrameQueue:
    """Nonblocking adapter handoff; rejected frames become observable gap metadata."""

    def __init__(self, max_frames: int = MAX_QUEUE_FRAMES, max_bytes: int = MAX_QUEUE_BYTES):
        if max_frames < 1 or max_bytes < 1:
            raise ValueError("queue limits must be positive")
        self._queue: queue.Queue[ExecutionOutputFrame] = queue.Queue(maxsize=max_frames)
        self._max_bytes = max_bytes
        self._bytes = 0
        self._lock = threading.Lock()
        self._max_frames_observed = 0
        self._max_bytes_observed = 0
        self._gaps: list[StreamGap] = []
        self._coalesced_gap_indices: dict[str, int] = {}
        self._source_gap_indices: dict[str, int] = {}
        self._source_gap_snapshots: dict[str, StreamGap] = {}

    def _append_gap(self, gap: StreamGap) -> None:
        if len(self._gaps) < min(64, MAX_PENDING_GAPS):
            self._gaps.append(gap)
            return
        bucket_key = f"{gap.execution_id or ''}:{gap.stream}"
        index = self._coalesced_gap_indices.get(bucket_key)
        if index is None:
            if len(self._gaps) >= MAX_PENDING_GAPS:
                raise GapCapacityError("pending stream gap metadata limit reached; persist gaps before draining more input")
            reason = f"{gap.reason}_ranges_coalesced"
            self._coalesced_gap_indices[bucket_key] = len(self._gaps)
            self._gaps.append(StreamGap(gap.stream, gap.sequence, gap.offset_bytes, gap.dropped_bytes, reason,
                                       gap.last_sequence, gap.last_offset_bytes, gap.dropped_frames, True,
                                       gap.source_id, gap.execution_id, gap.host_boot_id))
            return
        first = self._gaps[index]
        self._gaps[index] = StreamGap(first.stream, first.sequence, first.offset_bytes,
                                      first.dropped_bytes + gap.dropped_bytes, first.reason,
                                      gap.last_sequence, gap.last_offset_bytes,
                                      first.dropped_frames + gap.dropped_frames, True,
                                      first.source_id, first.execution_id, first.host_boot_id)

    def _record_versioned_gap(self, gap: StreamGap) -> None:
        source_id = gap.source_id
        previous = self._source_gap_snapshots.get(source_id)
        index = self._source_gap_indices.get(source_id)
        if previous == gap:
            return
        if index is not None and index < 64:
            self._gaps[index] = gap
        elif index is not None:
            bucket = self._gaps[index]
            old_bytes = previous.dropped_bytes if previous is not None else 0
            old_frames = previous.dropped_frames if previous is not None else 0
            first_sequence = min(bucket.sequence, gap.sequence)
            first_offset = bucket.offset_bytes if bucket.sequence <= gap.sequence else gap.offset_bytes
            last_sequence = max(bucket.last_sequence or bucket.sequence, gap.last_sequence or gap.sequence)
            last_offset = bucket.last_offset_bytes if (bucket.last_sequence or bucket.sequence) >= (gap.last_sequence or gap.sequence) \
                else gap.last_offset_bytes
            self._gaps[index] = StreamGap(bucket.stream, first_sequence, first_offset,
                                          bucket.dropped_bytes + gap.dropped_bytes - old_bytes,
                                          bucket.reason, last_sequence, last_offset,
                                          bucket.dropped_frames + gap.dropped_frames - old_frames, True,
                                          gap.source_id, gap.execution_id, gap.host_boot_id)
        else:
            next_gap = gap
            if previous is not None:
                dropped_bytes = gap.dropped_bytes - previous.dropped_bytes
                dropped_frames = gap.dropped_frames - previous.dropped_frames
                if dropped_bytes < 0 or dropped_frames < 0:
                    raise ValueError("source gap totals must be cumulative")
                if dropped_bytes == 0 and dropped_frames == 0:
                    self._source_gap_snapshots[source_id] = gap
                    return
                previous_last_sequence = (previous.last_sequence if previous.last_sequence is not None
                                          else previous.sequence)
                last_sequence = gap.last_sequence if gap.last_sequence is not None else gap.sequence
                sequence = min(last_sequence, max(gap.sequence, previous_last_sequence + 1))
                previous_last_offset = (previous.last_offset_bytes if previous.last_offset_bytes is not None
                                        else previous.offset_bytes)
                last_offset = gap.last_offset_bytes if gap.last_offset_bytes is not None else gap.offset_bytes
                offset_bytes = min(last_offset, max(gap.offset_bytes, previous_last_offset))
                coalesced = gap.coalesced or dropped_frames != last_sequence - sequence + 1
                next_gap = StreamGap(gap.stream, sequence, offset_bytes, dropped_bytes, gap.reason,
                                     last_sequence, last_offset, dropped_frames, coalesced, source_id,
                                     gap.execution_id, gap.host_boot_id)
            if len(self._gaps) < min(64, MAX_PENDING_GAPS):
                self._source_gap_indices[source_id] = len(self._gaps)
                self._gaps.append(next_gap)
            else:
                bucket_key = f"{gap.execution_id or ''}:{gap.stream}"
                index = self._coalesced_gap_indices.get(bucket_key)
                if index is None:
                    if len(self._gaps) >= MAX_PENDING_GAPS:
                        raise GapCapacityError("pending stream gap metadata limit reached; persist gaps before draining more input")
                    index = len(self._gaps)
                    self._coalesced_gap_indices[bucket_key] = index
                    self._gaps.append(StreamGap(next_gap.stream, next_gap.sequence, next_gap.offset_bytes,
                                                next_gap.dropped_bytes,
                                                f"{next_gap.reason}_ranges_coalesced", next_gap.last_sequence,
                                                next_gap.last_offset_bytes, next_gap.dropped_frames, True,
                                                next_gap.source_id, next_gap.execution_id, next_gap.host_boot_id))
                else:
                    bucket = self._gaps[index]
                    last_sequence = (next_gap.last_sequence if next_gap.last_sequence is not None
                                     else next_gap.sequence)
                    bucket_last_sequence = (bucket.last_sequence if bucket.last_sequence is not None
                                            else bucket.sequence)
                    last_offset = (next_gap.last_offset_bytes if next_gap.last_offset_bytes is not None
                                   else next_gap.offset_bytes)
                    bucket_last_offset = (bucket.last_offset_bytes if bucket.last_offset_bytes is not None
                                          else bucket.offset_bytes)
                    self._gaps[index] = StreamGap(bucket.stream, min(bucket.sequence, next_gap.sequence),
                                                  bucket.offset_bytes if bucket.sequence <= next_gap.sequence else next_gap.offset_bytes,
                                                  bucket.dropped_bytes + next_gap.dropped_bytes,
                                                  bucket.reason, max(bucket_last_sequence, last_sequence),
                                                  bucket_last_offset if bucket_last_sequence >= last_sequence else last_offset,
                                                  bucket.dropped_frames + next_gap.dropped_frames, True,
                                                  bucket.source_id, bucket.execution_id, bucket.host_boot_id)
                self._source_gap_indices[source_id] = index
        self._source_gap_snapshots[source_id] = gap

    def _record_gap(self, frame: ExecutionOutputFrame, size: int) -> None:
        if self._gaps:
            last = self._gaps[-1]
            last_sequence = last.last_sequence if last.last_sequence is not None else last.sequence
            if last.stream == frame.stream and last.execution_id == frame.execution_id and last_sequence + 1 == frame.sequence:
                self._gaps[-1] = StreamGap(last.stream, last.sequence, last.offset_bytes,
                                           last.dropped_bytes + size, last.reason, frame.sequence,
                                           frame.offset_bytes + size, last.dropped_frames + 1,
                                           last.coalesced, last.source_id, last.execution_id, last.host_boot_id)
                return
        gap = StreamGap(frame.stream, frame.sequence, frame.offset_bytes, size, "queue_overflow",
                        frame.sequence, frame.offset_bytes + size, execution_id=frame.execution_id,
                        host_boot_id=frame.host_boot_id)
        self._append_gap(gap)

    def record_gap(self, stream: str, sequence: int, offset_bytes: int, dropped_bytes: int,
                   dropped_frames: int, *, reason: str = "source_gap", last_sequence: int | None = None,
                   last_offset_bytes: int | None = None, coalesced: bool = False,
                   source_id: str | None = None, execution_id: str | None = None,
                   host_boot_id: str | None = None) -> None:
        """Record a source-reported gap without adding payload to the bounded frame queue."""
        if stream not in ("stdout", "stderr") or min(sequence, offset_bytes, dropped_bytes) < 0 or dropped_frames < 1:
            raise ValueError("invalid stream gap")
        if source_id is not None and (not isinstance(source_id, str) or not source_id
                                      or len(source_id) > MAX_SOURCE_ID_LENGTH):
            raise ValueError("source_id must be non-empty text of at most 512 characters")
        final_sequence = last_sequence if last_sequence is not None else sequence + dropped_frames - 1
        final_offset = last_offset_bytes if last_offset_bytes is not None else offset_bytes + dropped_bytes
        if final_sequence < sequence or final_offset < offset_bytes:
            raise ValueError("stream gap bounds must be ordered")
        if not coalesced and dropped_frames != final_sequence - sequence + 1:
            raise ValueError("non-coalesced gap frames must cover a contiguous sequence range")
        with self._lock:
            if source_id is None and self._gaps:
                last = self._gaps[-1]
                end_sequence = last.last_sequence if last.last_sequence is not None else last.sequence
                if last.stream == stream and last.execution_id == execution_id and end_sequence + 1 == sequence:
                    self._gaps[-1] = StreamGap(last.stream, last.sequence, last.offset_bytes,
                                               last.dropped_bytes + dropped_bytes, last.reason,
                                               last_sequence if last_sequence is not None else sequence + dropped_frames - 1,
                                               last_offset_bytes if last_offset_bytes is not None else offset_bytes + dropped_bytes,
                                               last.dropped_frames + dropped_frames,
                                               last.coalesced or coalesced, last.source_id, last.execution_id,
                                               last.host_boot_id or host_boot_id)
                    return
            gap = StreamGap(stream, sequence, offset_bytes, dropped_bytes, reason,
                            last_sequence if last_sequence is not None else sequence + dropped_frames - 1,
                            last_offset_bytes if last_offset_bytes is not None else offset_bytes + dropped_bytes,
                            dropped_frames, coalesced, source_id, execution_id, host_boot_id)
            if source_id is not None:
                if source_id not in self._source_gap_snapshots \
                        and len(self._source_gap_snapshots) >= MAX_TRACKED_SOURCE_GAPS:
                    raise GapCapacityError("source gap tracking limit reached; forget completed sources")
                self._record_versioned_gap(gap)
                return
            self._append_gap(gap)

    def put(self, frame: ExecutionOutputFrame) -> bool:
        size = len(frame.data)
        with self._lock:
            if size > self._max_bytes or self._bytes + size > self._max_bytes:
                self._record_gap(frame, size)
                return False
            try:
                self._queue.put_nowait(frame)
            except queue.Full:
                self._record_gap(frame, size)
                return False
            self._bytes += size
            self._max_frames_observed = max(self._max_frames_observed, self._queue.qsize())
            self._max_bytes_observed = max(self._max_bytes_observed, self._bytes)
            return True

    def get(self, timeout: float | None = None) -> ExecutionOutputFrame:
        frame = self._queue.get(timeout=timeout)
        with self._lock:
            self._bytes -= len(frame.data)
        return frame

    def peek_frame(self) -> ExecutionOutputFrame | None:
        """Return the next frame without releasing its bounded queue capacity."""
        with self._queue.mutex:
            return self._queue.queue[0] if self._queue.queue else None

    def pending_frames(self) -> tuple[ExecutionOutputFrame, ...]:
        """Snapshot queued frames without changing ownership or releasing capacity."""
        with self._queue.mutex:
            return tuple(self._queue.queue)

    def pending_inputs(self) -> tuple[ExecutionOutputFrame | StreamGap, ...]:
        """Snapshot frames and gaps in per-stream source order for a durable consumer."""
        with self._lock, self._queue.mutex:
            items: list[tuple[tuple[str, str, int, int], ExecutionOutputFrame | StreamGap]] = []
            for frame in self._queue.queue:
                items.append(((frame.execution_id, frame.stream, frame.sequence, 1), frame))
            for gap in self._gaps:
                items.append(((gap.execution_id or "", gap.stream, gap.sequence, 0), gap))
            return tuple(item for _, item in sorted(items, key=lambda pair: pair[0]))

    def acknowledge_frame(self, frame: ExecutionOutputFrame) -> bool:
        """Release a frame only after the caller's durable event transaction commits."""
        with self._lock, self._queue.mutex:
            if not self._queue.queue or self._queue.queue[0] is not frame:
                return False
            self._queue.queue.popleft()
            self._bytes -= len(frame.data)
            self._queue.not_full.notify()
            return True

    def acknowledge_frames(self, frames: tuple[ExecutionOutputFrame, ...]) -> bool:
        """Release exact frames after commit, including safe frames behind another stream's partial line."""
        if not frames:
            return True
        with self._lock, self._queue.mutex:
            pending = list(self._queue.queue)
            indices = []
            for frame in frames:
                index = next((i for i, item in enumerate(pending) if item is frame), None)
                if index is None:
                    return False
                indices.append(index)
            remove = set(indices)
            self._queue.queue = type(self._queue.queue)(item for i, item in enumerate(pending) if i not in remove)
            self._bytes -= sum(len(frame.data) for frame in frames)
            self._queue.not_full.notify(len(frames))
            return True

    def persist_event(self, store: MonitorStore, frame: ExecutionOutputFrame,
                      event: NormalizedEvent, cursor: SourceCursor) -> bool:
        """Persist one normalized frame and release its queue slot only after commit."""
        if self.peek_frame() is not frame:
            raise ValueError("frame must be the next pending queue item")
        if (event.execution_id, event.stream, event.sequence, event.offset_bytes, event.host_boot_id) != (
                frame.execution_id, frame.stream, frame.sequence, frame.offset_bytes, frame.host_boot_id):
            raise ValueError("normalized event does not describe the queued frame")
        inserted = store.append_event(event, cursor)
        if not self.acknowledge_frame(frame):
            raise RuntimeError("event committed but queue frame changed before acknowledgment")
        return inserted

    def pending_gaps(self) -> tuple[StreamGap, ...]:
        with self._lock:
            return tuple(self._gaps)

    def acknowledge_gap(self, gap: StreamGap) -> bool:
        """Remove only the exact gap snapshot already committed by the store."""
        with self._lock:
            try:
                index = self._gaps.index(gap)
            except ValueError:
                return False
            self._gaps.pop(index)
            self._coalesced_gap_indices.clear()
            self._source_gap_indices.clear()
            return True

    def drain_gaps(self) -> tuple[StreamGap, ...]:
        with self._lock:
            gaps, self._gaps = tuple(self._gaps), []
            self._coalesced_gap_indices.clear()
            self._source_gap_indices.clear()
            return gaps

    def forget_source_prefix(self, source_id_prefix: str) -> None:
        """Release cumulative gap snapshots after their source can no longer report updates."""
        if not source_id_prefix:
            raise ValueError("source id prefix must not be empty")
        with self._lock:
            for source_id in tuple(self._source_gap_snapshots):
                if source_id.startswith(source_id_prefix):
                    self._source_gap_snapshots.pop(source_id)
                    self._source_gap_indices.pop(source_id, None)

    @property
    def buffered_bytes(self) -> int:
        with self._lock:
            return self._bytes

    @property
    def buffered_frames(self) -> int:
        return self._queue.qsize()

    @property
    def max_frames_observed(self) -> int:
        with self._lock:
            return self._max_frames_observed

    @property
    def max_bytes_observed(self) -> int:
        with self._lock:
            return self._max_bytes_observed
