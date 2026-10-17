"""M3 FIFO reader and typed in-memory handoff to the M4 monitor package."""
from __future__ import annotations

import errno
import hashlib
import json
import os
import stat
import struct
import time
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from bt_scheduler_monitor_adapter import (
    BoundedFrameQueue,
    ExecutionOutputFrame,
    GapCapacityError,
    ProcessIdentity,
)

_HEADER = struct.Struct("!4sBBHQQ")
_MAX_DATA = 3840
MAX_DRAIN_FRAMES = 128
MAX_SUMMARY_GAP_RANGES = 128
MAX_TRACKED_SUMMARY_GAPS = 10_000
TERMINAL_STATES = frozenset({"finished", "failed", "cancelled", "rejected"})


class M3StreamAdapter:
    """Drain M3's private FIFO into bounded M4 frames; never enters the M1 lifecycle sink.

    A terminal status releases an execution's reader only after the FIFO reaches EOF with no partial frame buffered.
    Call `forget()` after an equivalent externally confirmed terminal drain; `close_all()` belongs to owner shutdown.
    """

    def __init__(self, project_state: Path | str, *, max_frames: int = 10_000,
                 max_bytes: int = 16 * 1024 * 1024, max_open_streams: int = 2):
        if not isinstance(max_open_streams, int) or isinstance(max_open_streams, bool) or max_open_streams < 1:
            raise ValueError("max_open_streams must be positive")
        self.project_state = Path(project_state).resolve()
        self.queue = BoundedFrameQueue(max_frames=max_frames, max_bytes=max_bytes)
        self._max_open_streams = max_open_streams
        self._fds: dict[str, int] = {}
        self._buffers: dict[str, bytearray] = {}
        self._summary_gaps: dict[tuple[str, str, int], tuple[int, int, int, int, int, bool]] = {}
        self._seen_gap_keys: set[tuple[Any, ...]] = set()
        self._seen_gap_order: list[tuple[Any, ...]] = []
        self._terminal_drained: set[str] = set()

    def close(self, execution_id: str) -> None:
        fd = self._fds.pop(execution_id, None)
        self._buffers.pop(execution_id, None)
        if fd is not None:
            os.close(fd)

    def close_all(self) -> None:
        """Close every FIFO reader and release per-execution state during owner shutdown."""
        first_error: OSError | None = None
        for fd in tuple(self._fds.values()):
            try:
                os.close(fd)
            except OSError as error:
                first_error = first_error or error
        self._fds.clear()
        self._buffers.clear()
        self._summary_gaps.clear()
        self._seen_gap_keys.clear()
        self._seen_gap_order.clear()
        self._terminal_drained.clear()
        self.queue.forget_source_prefix("m3:")
        if first_error is not None:
            raise first_error

    def persist_gaps(self, store: Any, *, recorded_at: str | None = None, limit: int = 64) -> int:
        """Commit observed gaps before removing them from the bounded in-memory queue."""
        stamp = recorded_at or datetime.now(UTC).isoformat()
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 64:
            raise ValueError("gap persistence limit must be between 1 and 64")
        persisted = 0
        for gap in self.queue.pending_gaps()[:limit]:
            if gap.execution_id is None:
                raise ValueError("gap is missing its execution identity")
            first_sequence = gap.sequence
            last_sequence = gap.last_sequence if gap.last_sequence is not None else gap.sequence
            last_offset = gap.last_offset_bytes if gap.last_offset_bytes is not None else gap.offset_bytes
            key_fields = (gap.execution_id, gap.stream, gap.sequence, gap.offset_bytes, gap.reason)
            gap_id = "m3-gap:" + hashlib.sha256(json.dumps(key_fields, separators=(",", ":")).encode()).hexdigest()
            store.record_stream_gap(gap_id=gap_id, execution_id=gap.execution_id, stream=gap.stream,
                                   first_sequence=first_sequence, last_sequence=last_sequence,
                                   first_offset=gap.offset_bytes, last_offset=last_offset,
                                   dropped_bytes=gap.dropped_bytes, dropped_frames=gap.dropped_frames,
                                   reason=gap.reason, recorded_at=stamp)
            self.queue.acknowledge_gap(gap)
            persisted += 1
        return persisted

    def forget(self, execution_id: str, *, preserve_terminal: bool = False) -> None:
        """Release deduplication state after the consumer durably handles all input for an execution."""
        try:
            self.close(execution_id)
        finally:
            if not preserve_terminal:
                self._terminal_drained.discard(execution_id)
            self._summary_gaps = {key: value for key, value in self._summary_gaps.items()
                                  if key[0] != execution_id}
            self._seen_gap_keys = {key for key in self._seen_gap_keys if key[0] != execution_id}
            self._seen_gap_order = [key for key in self._seen_gap_order if key[0] != execution_id]
            self.queue.forget_source_prefix(f"m3:{execution_id}:")

    def is_terminal_drained(self, execution_id: str) -> bool:
        """Whether the terminal FIFO reached EOF without a truncated transport frame."""
        return execution_id in self._terminal_drained

    def reader_open(self, execution_id: str) -> bool:
        """Whether this execution already owns one of the bounded FIFO reader slots."""
        return execution_id in self._fds

    def can_open_reader(self, execution_id: str) -> bool:
        """Whether a bounded FIFO reader slot is available for this execution."""
        return self.reader_open(execution_id) or len(self._fds) < self._max_open_streams

    def _record_source_gap(self, execution_id: str, stream: str, sequence: int, offset: int,
                           dropped_bytes: int, dropped_frames: int, last_sequence: int,
                           last_offset: int, *, reason: str, coalesced: bool = False,
                           host_boot_id: str | None = None) -> bool:
        key = (execution_id, stream, sequence, last_sequence, offset, last_offset, dropped_bytes, dropped_frames)
        if key in self._seen_gap_keys:
            return False
        source_id = f"m3:{execution_id}:{stream}:{sequence}"
        self.queue.record_gap(stream, sequence, offset, dropped_bytes, dropped_frames, reason=reason,
                              last_sequence=last_sequence, last_offset_bytes=last_offset,
                              coalesced=coalesced, source_id=source_id, execution_id=execution_id,
                              host_boot_id=host_boot_id)
        self._seen_gap_keys.add(key)
        self._seen_gap_order.append(key)
        while len(self._seen_gap_order) > 10_000:
            expired = self._seen_gap_order.pop(0)
            self._seen_gap_keys.discard(expired)
        return True

    def _recover_summary_gaps(self, execution_id: str, status: Mapping[str, Any]) -> None:
        ranges = status.get("dropped_ranges", ())
        if not isinstance(ranges, (list, tuple)):
            raise TypeError("M3 dropped_ranges must be a list")
        identity = status.get("process_identity")
        host_boot_id = identity.get("host_boot_id") if isinstance(identity, Mapping) else None
        if host_boot_id is not None and (not isinstance(host_boot_id, str) or not host_boot_id):
            raise ValueError("M3 process host_boot_id is invalid")
        for item in ranges:
            if not isinstance(item, Mapping):
                raise TypeError("M3 dropped range must be an object")
            stream = item.get("stream")
            first = item.get("first_sequence")
            last = item.get("last_sequence")
            first_offset = item.get("first_offset")
            last_offset = item.get("last_offset")
            dropped_bytes = item.get("dropped_bytes")
            dropped_frames = item.get("dropped_frames")
            if stream not in ("stdout", "stderr") or not all(isinstance(value, int) and not isinstance(value, bool)
                    and value >= 0 for value in (first, last, first_offset, last_offset, dropped_bytes, dropped_frames)):
                raise ValueError("M3 dropped range fields are invalid")
            if dropped_frames < 1 or last < first or last_offset < first_offset:
                raise ValueError("M3 dropped range bounds are invalid")
            coalesced = last - first + 1 > dropped_frames
            key = (execution_id, stream, first)
            previous = self._summary_gaps.get(key)
            signature = (first_offset, last, last_offset, dropped_bytes, dropped_frames, coalesced)
            if previous == signature:
                continue
            if previous is None and len(self._summary_gaps) >= MAX_TRACKED_SUMMARY_GAPS:
                raise GapCapacityError("tracked M3 summary gap limit reached; forget completed executions")
            if previous is None:
                self._record_source_gap(execution_id, stream, first, first_offset, dropped_bytes, dropped_frames,
                                        last, last_offset, reason="source_gap", coalesced=coalesced,
                                        host_boot_id=host_boot_id)
            else:
                old_first_offset, old_last, old_last_offset, old_bytes, old_frames, _ = previous
                delta_bytes, delta_frames = dropped_bytes - old_bytes, dropped_frames - old_frames
                if delta_bytes < 0 or delta_frames < 0:
                    raise ValueError("M3 dropped range summary moved backwards")
                if last < old_last or last_offset < old_last_offset or first_offset != old_first_offset:
                    raise ValueError("M3 dropped range bounds moved backwards")
                if delta_bytes or delta_frames or last != old_last or last_offset != old_last_offset:
                    self._record_source_gap(execution_id, stream, first, first_offset, dropped_bytes,
                                            dropped_frames, last, last_offset,
                                            reason="source_gap_ranges_coalesced" if coalesced else "source_gap",
                                            coalesced=coalesced, host_boot_id=host_boot_id)
            self._summary_gaps[key] = signature

    def drain(self, status: Mapping[str, Any], attempt_dir: Path | str, *, run_id: str,
              preserve_for_consumer: bool = False) -> int:
        """Read a bounded batch of currently available frames from a validated M3 status."""
        if not isinstance(run_id, str) or not run_id.strip():
            raise ValueError("run_id must come from the M1 boundary")
        if not isinstance(preserve_for_consumer, bool):
            raise TypeError("preserve_for_consumer must be a boolean")
        execution_id = status.get("execution_id")
        if not isinstance(execution_id, str) or not execution_id or len(execution_id) > 300:
            raise ValueError("M3 execution_id must be non-empty text of at most 300 characters")
        if execution_id in self._terminal_drained:
            return 0
        ranges = status.get("dropped_ranges", ())
        if not isinstance(ranges, (list, tuple)) or len(ranges) > MAX_SUMMARY_GAP_RANGES:
            raise ValueError("M3 dropped_ranges must contain at most 128 entries")
        self._recover_summary_gaps(execution_id, status)
        stream_ref = status.get("stream_ref")
        if not isinstance(stream_ref, str) or not stream_ref or Path(stream_ref).is_absolute() \
                or ".." in Path(stream_ref).parts:
            raise ValueError("M3 stream_ref must be a safe relative path")
        directory = Path(attempt_dir).resolve()
        if not directory.is_relative_to(self.project_state):
            raise ValueError("M3 attempt directory escapes project state")
        attempt_parts = directory.relative_to(self.project_state).parts
        fd = self._fds.get(execution_id)
        if fd is None:
            if len(self._fds) >= self._max_open_streams:
                raise ValueError("active stream reader limit reached; forget terminal executions")
            try:
                fd = self._open_fifo(self.project_state, attempt_parts, Path(stream_ref).parts)
            except FileNotFoundError:
                if status.get("state") in TERMINAL_STATES:
                    raise ValueError("terminal M3 stream endpoint is missing") from None
                return 0
            self._fds[execution_id] = fd
            self._buffers[execution_id] = bytearray()
        buffer = self._buffers[execution_id]
        count = 0
        reached_eof = False
        gap_capacity_error: GapCapacityError | None = None
        while count < MAX_DRAIN_FRAMES:
            while count < MAX_DRAIN_FRAMES and len(buffer) >= _HEADER.size:
                magic, version, stream_id, size, sequence, offset = _HEADER.unpack(buffer[:_HEADER.size])
                if magic != b"BTM4" or version != 1 or stream_id not in (1, 2, 3, 4) or size > _MAX_DATA:
                    self.forget(execution_id)
                    raise ValueError("invalid M3 stream frame header")
                frame_size = _HEADER.size + size
                if len(buffer) < frame_size:
                    break
                data = bytes(buffer[_HEADER.size:frame_size])
                if stream_id in (3, 4):
                    if size != 16:
                        self.forget(execution_id)
                        raise ValueError("invalid M3 stream gap frame")
                    dropped_bytes, dropped_frames = struct.unpack("!QQ", data)
                    stream = "stdout" if stream_id == 3 else "stderr"
                    last_sequence = sequence + dropped_frames - 1
                    last_offset = offset + dropped_bytes
                    covered_by_summary = any(
                        owner == execution_id and source_stream == stream and first <= sequence
                        and snapshot[1] >= last_sequence and first_offset <= offset and snapshot[2] >= last_offset
                        and (snapshot[5] or snapshot[4] == snapshot[1] - first + 1)
                        for (owner, source_stream, first), snapshot in self._summary_gaps.items()
                        for first_offset in (snapshot[0],))
                    if not covered_by_summary:
                        try:
                            self._record_source_gap(execution_id, stream, sequence, offset, dropped_bytes,
                                                    dropped_frames, last_sequence, last_offset, reason="source_gap",
                                                    host_boot_id=status["process_identity"].get("host_boot_id"))
                        except GapCapacityError as error:
                            gap_capacity_error = error
                            break
                    del buffer[:frame_size]
                    count += 1
                    continue
                identity = status["process_identity"]
                frame = ExecutionOutputFrame(
                    schema_version="1.0.0", run_id=run_id, plan_revision=status["plan_revision"],
                    task_id=status["task_id"], attempt_id=status["attempt_id"], execution_id=execution_id,
                    process_identity=ProcessIdentity.from_dict(identity), provider=status["provider"],
                    profile_id=status.get("profile_id"), model=status.get("model"),
                    stream="stdout" if stream_id == 1 else "stderr", sequence=sequence, offset_bytes=offset,
                    received_at=datetime.now(UTC).isoformat(), received_monotonic_ns=time.monotonic_ns(),
                    host_boot_id=identity.get("host_boot_id"), data=data)
                try:
                    self.queue.put(frame)
                except GapCapacityError as error:
                    gap_capacity_error = error
                    break
                del buffer[:frame_size]
                count += 1
            if gap_capacity_error is not None:
                break
            if count >= MAX_DRAIN_FRAMES:
                break
            try:
                chunk = os.read(fd, 65536)
            except BlockingIOError:
                break
            if not chunk:
                reached_eof = True
                break
            buffer.extend(chunk)
        if gap_capacity_error is not None:
            raise gap_capacity_error
        if reached_eof and status.get("state") in TERMINAL_STATES:
            if buffer:
                self.forget(execution_id)
                raise ValueError("terminal M3 stream ended with a truncated frame")
            self.close(execution_id)
            self._terminal_drained.add(execution_id)
            if not preserve_for_consumer:
                self.forget(execution_id)
        return count

    @staticmethod
    def _open_directory_tree(directory: Path) -> int:
        """Open a directory path by walking from root without following a symlink component."""
        if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
            raise OSError("safe M3 FIFO traversal is unavailable on this platform")
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
        descriptor = os.open(directory.anchor, flags)
        try:
            for part in directory.parts[1:]:
                next_descriptor = os.open(part, flags, dir_fd=descriptor)
                os.close(descriptor)
                descriptor = next_descriptor
            return descriptor
        except BaseException:
            os.close(descriptor)
            raise

    @staticmethod
    def _open_fifo(root: Path, attempt_parts: tuple[str, ...], parts: tuple[str, ...]) -> int:
        """Open a FIFO beneath the pinned project root without following any path symlink."""
        components = (*attempt_parts, *parts)
        if not parts or any(part in {"", ".", ".."} or "\x00" in part for part in components):
            raise ValueError("M3 stream_ref contains an invalid path component")
        if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
            raise OSError("safe M3 FIFO traversal is unavailable on this platform")
        directory_flags = os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_CLOEXEC", 0)
        component_flags = directory_flags | os.O_NOFOLLOW
        descriptors: list[int] = []
        stream_fd = -1
        try:
            parent_fd = M3StreamAdapter._open_directory_tree(root)
            descriptors.append(parent_fd)
            for part in (*attempt_parts, *parts[:-1]):
                parent_fd = os.open(part, component_flags, dir_fd=parent_fd)
                descriptors.append(parent_fd)
            info = os.stat(parts[-1], dir_fd=parent_fd, follow_symlinks=False)
            if not stat.S_ISFIFO(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
                raise ValueError("M3 stream endpoint has unexpected type, owner or permissions")
            stream_fd = os.open(
                parts[-1], os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0),
                dir_fd=parent_fd,
            )
            opened = os.fstat(stream_fd)
            if not stat.S_ISFIFO(opened.st_mode) or (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
                raise ValueError("M3 stream endpoint changed while it was opened")
            if opened.st_uid != os.getuid() or opened.st_mode & 0o077:
                raise ValueError("M3 stream endpoint has unexpected type, owner or permissions")
            result = stream_fd
            stream_fd = -1
            return result
        except OSError as error:
            if error.errno in {errno.ELOOP, errno.ENOTDIR}:
                raise ValueError("M3 stream_ref contains a symlink or non-directory component") from error
            raise
        finally:
            if stream_fd >= 0:
                os.close(stream_fd)
            for descriptor in reversed(descriptors):
                os.close(descriptor)
