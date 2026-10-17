"""Atomic M4 persistence for normalized stream batches and their source cursors."""
from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import AbstractContextManager
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .contracts import MetricSample, NormalizedEvent
from .retention import ensure_metric_extension
from .serialization import event_from_dict, event_to_dict, metric_to_dict
from .storage_limits import (WRITE_RESERVE_BYTES, StoreError, measured_store_bytes,
                             ensure_write_capacity)


class _Store(Protocol):
    path: Path
    max_store_bytes: int
    busy_timeout_ms: int

    def _session(self) -> AbstractContextManager[sqlite3.Connection]: ...
    @staticmethod
    def _raise_sqlite(exc: sqlite3.Error) -> StoreError: ...


@dataclass(frozen=True)
class SourceCursor:
    execution_id: str
    stream: str
    host_boot_id: str | None
    sequence: int
    offset_bytes: int

    def __post_init__(self) -> None:
        if not isinstance(self.execution_id, str) or not self.execution_id:
            raise ValueError("execution_id must be non-empty text")
        if self.stream not in ("stdout", "stderr"):
            raise ValueError("stream must be stdout or stderr")
        if self.host_boot_id is not None and (not isinstance(self.host_boot_id, str) or not self.host_boot_id):
            raise ValueError("host_boot_id must be non-empty text or None")
        for name in ("sequence", "offset_bytes"):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise ValueError(f"{name} must be a nonnegative integer")


@dataclass(frozen=True)
class StreamGapRecord:
    gap_id: str
    execution_id: str
    stream: str
    first_sequence: int
    last_sequence: int
    first_offset: int
    last_offset: int
    dropped_bytes: int
    dropped_frames: int
    reason: str
    recorded_at: str

    def __post_init__(self) -> None:
        _bounded_token(self.gap_id, "gap_id", 256)
        _bounded_token(self.execution_id, "execution_id", 512)
        _bounded_token(self.reason, "reason", 64)
        _bounded_token(self.recorded_at, "recorded_at", 64)
        if self.stream not in ("stdout", "stderr"):
            raise ValueError("stream must be stdout or stderr")
        values = (self.first_sequence, self.last_sequence, self.first_offset, self.last_offset,
                  self.dropped_bytes, self.dropped_frames)
        if any(type(value) is not int or value < 0 for value in values) or self.dropped_frames < 1:
            raise ValueError("gap coordinates and counts must be nonnegative; dropped_frames must be positive")
        if self.last_sequence < self.first_sequence or self.last_offset < self.first_offset:
            raise ValueError("gap bounds must be ordered")


def _bounded_token(value: object, name: str, maximum: int) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be non-empty text")
    try:
        size = len(value.encode("utf-8"))
    except UnicodeEncodeError as exc:
        raise ValueError(f"{name} must be valid UTF-8") from exc
    if size > maximum:
        raise ValueError(f"{name} exceeds its {maximum}-byte limit")
    return value


def _json(value: object) -> str:
    def validate(item: object, depth: int = 0) -> None:
        if depth > 32:
            raise ValueError("record JSON exceeds its nesting bound")
        if item is None or type(item) in (str, bool, int, float):
            return
        if type(item) in (list, tuple):
            if len(item) > 4_096:
                raise ValueError("record JSON exceeds its item bound")
            for child in item:
                validate(child, depth + 1)
            return
        if type(item) is dict:
            if len(item) > 4_096 or any(type(key) is not str for key in item):
                raise ValueError("record JSON objects require bounded string keys")
            for key, child in item.items():
                validate(key, depth + 1)
                validate(child, depth + 1)
            return
        raise ValueError("record must contain only JSON values")

    validate(value)
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError, RecursionError) as exc:
        raise ValueError("record must be bounded JSON-compatible data") from exc


def append_batch(store: _Store, *, events: tuple[NormalizedEvent, ...] = (),
                 metrics: tuple[MetricSample, ...] = (),
                 gaps: tuple[StreamGapRecord, ...] = (),
                 cursors: tuple[SourceCursor, ...] = ()) -> bool:
    """Atomically persist normalized output, metric samples, gaps and their source cursors."""
    if any(not isinstance(item, NormalizedEvent) for item in events):
        raise ValueError("events must contain validated NormalizedEvent contracts")
    if any(not isinstance(item, MetricSample) for item in metrics):
        raise ValueError("metrics must contain validated MetricSample contracts")
    if any(not isinstance(item, StreamGapRecord) for item in gaps):
        raise ValueError("gaps must contain validated StreamGapRecord contracts")
    if any(not isinstance(item, SourceCursor) for item in cursors):
        raise ValueError("cursors must contain validated SourceCursor contracts")
    if len(events) + len(metrics) + len(gaps) + len(cursors) > 512:
        raise ValueError("monitor batch exceeds its 512-item bound")

    event_bodies = tuple((event, _json(event_to_dict(event))) for event in events)
    metric_bodies = tuple((sample, _json(metric_to_dict(sample))) for sample in metrics)
    cursor_by_source: dict[tuple[str, str], SourceCursor] = {}
    for cursor in cursors:
        key = (cursor.execution_id, cursor.stream)
        previous = cursor_by_source.get(key)
        if previous is not None and previous.host_boot_id != cursor.host_boot_id:
            raise ValueError("cursor boot identity changed within a monitor batch")
        if previous is None or (cursor.sequence, cursor.offset_bytes) > (previous.sequence, previous.offset_bytes):
            cursor_by_source[key] = cursor
    for event in events:
        cursor = cursor_by_source.get((event.execution_id, event.stream))
        if cursor is None or event.host_boot_id != cursor.host_boot_id \
                or (event.sequence, event.offset_bytes) > (cursor.sequence, cursor.offset_bytes):
            raise ValueError("every normalized event must be covered by a same-stream source cursor")
    for gap in gaps:
        cursor = cursor_by_source.get((gap.execution_id, gap.stream))
        if cursor is None or (gap.last_sequence, gap.last_offset) > (cursor.sequence, cursor.offset_bytes):
            raise ValueError("every persisted stream gap must be covered by a same-stream source cursor")

    estimated_bytes = sum(len(body.encode("utf-8")) + 512 for _, body in event_bodies)
    estimated_bytes += sum(len(body.encode("utf-8")) + 512 for _, body in metric_bodies)
    estimated_bytes += len(gaps) * 512 + len(cursor_by_source) * 128
    reserve = max(WRITE_RESERVE_BYTES, estimated_bytes * 2)
    try:
        with store._session() as connection:
            connection.execute("BEGIN IMMEDIATE")
            ensure_write_capacity(store.path, store.max_store_bytes, reserve)
            if metric_bodies:
                ensure_metric_extension(connection, store.path, store.max_store_bytes)
            for event, body in event_bodies:
                existing = connection.execute("SELECT body FROM normalized_events WHERE event_id=?",
                                              (event.event_id,)).fetchone()
                if existing is not None:
                    if existing["body"] != body:
                        raise ValueError("event_id replay has different content")
                    continue
                connection.execute("INSERT INTO normalized_events VALUES(?,?,?,?,?,?)",
                                   (event.event_id, event.execution_id, event.stream, event.sequence,
                                    event.offset_bytes, body))
            for sample, body in metric_bodies:
                prior = connection.execute("SELECT body FROM metric_samples WHERE metric_id=?",
                                           (sample.metric_id,)).fetchone()
                if prior is not None:
                    if prior["body"] != body:
                        raise ValueError("metric_id replay has different content")
                    continue
                connection.execute("INSERT INTO metric_samples VALUES(?,?,?)",
                                   (sample.metric_id, sample.observed_at, body))
            for gap in gaps:
                row = connection.execute("SELECT * FROM stream_gaps WHERE gap_id=?", (gap.gap_id,)).fetchone()
                body = (gap.execution_id, gap.stream, gap.first_sequence, gap.last_sequence,
                        gap.first_offset, gap.last_offset, gap.dropped_bytes, gap.dropped_frames,
                        gap.reason, gap.recorded_at)
                if row is None:
                    connection.execute("INSERT INTO stream_gaps VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                                       (gap.gap_id, *body))
                    continue
                existing = tuple(row[key] for key in ("execution_id", "stream", "first_sequence", "last_sequence",
                                  "first_offset", "last_offset", "dropped_bytes", "dropped_frames", "reason", "recorded_at"))
                if existing == body:
                    continue
                immutable = (0, 1, 2, 4, 8, 9)
                monotonic = (3, 5, 6, 7)
                if any(existing[index] != body[index] for index in immutable) or any(
                        body[index] < existing[index] for index in monotonic):
                    raise ValueError("gap_id replay has different or regressing content")
                connection.execute("""UPDATE stream_gaps SET last_sequence=?,last_offset=?,dropped_bytes=?,
                    dropped_frames=? WHERE gap_id=?""", (body[3], body[5], body[6], body[7], gap.gap_id))
            for cursor in cursor_by_source.values():
                prior = connection.execute("SELECT * FROM source_cursors WHERE execution_id=? AND stream=?",
                                           (cursor.execution_id, cursor.stream)).fetchone()
                if prior is not None:
                    if prior["host_boot_id"] != cursor.host_boot_id:
                        raise ValueError("cursor boot identity changed within an execution stream")
                    if cursor.sequence < prior["sequence"] or cursor.offset_bytes < prior["offset_bytes"]:
                        raise ValueError("cursor cannot regress sequence or byte offset")
                connection.execute("""INSERT INTO source_cursors VALUES(?,?,?,?,?)
                    ON CONFLICT(execution_id,stream) DO UPDATE SET host_boot_id=excluded.host_boot_id,
                    sequence=excluded.sequence, offset_bytes=excluded.offset_bytes""",
                                   (cursor.execution_id, cursor.stream, cursor.host_boot_id,
                                    cursor.sequence, cursor.offset_bytes))
            measured = measured_store_bytes(store.path)
            if measured > store.max_store_bytes:
                raise StoreError(f"storage_pressure: projected batch size={measured} limit_bytes={store.max_store_bytes}")
            connection.commit()
            return bool(event_bodies or metric_bodies or gaps or cursor_by_source)
    except sqlite3.Error as exc:
        raise store._raise_sqlite(exc) from exc
    except BaseException:
        raise


def append_event(store: _Store, event: NormalizedEvent, cursor: SourceCursor) -> bool:
    if not isinstance(event, NormalizedEvent) or not isinstance(cursor, SourceCursor):
        raise ValueError("append_event requires validated event and cursor contracts")
    if (event.execution_id, event.stream, event.sequence, event.offset_bytes, event.host_boot_id) != (
        cursor.execution_id, cursor.stream, cursor.sequence, cursor.offset_bytes, cursor.host_boot_id
    ):
        raise ValueError("cursor must describe the event execution, stream, boot, sequence and offset")
    body = _json(event_to_dict(event))
    try:
        with store._session() as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute("SELECT body FROM normalized_events WHERE event_id=?",
                                          (event.event_id,)).fetchone()
            if existing is not None:
                if existing["body"] != body:
                    raise ValueError("event_id replay has different content")
                connection.commit()
                return False
            ensure_write_capacity(store.path, store.max_store_bytes)
            prior = connection.execute("SELECT * FROM source_cursors WHERE execution_id=? AND stream=?",
                                       (cursor.execution_id, cursor.stream)).fetchone()
            if prior is not None:
                if prior["host_boot_id"] != cursor.host_boot_id:
                    raise ValueError("cursor boot identity changed within an execution stream")
                if cursor.sequence < prior["sequence"] or cursor.offset_bytes < prior["offset_bytes"]:
                    raise ValueError("cursor cannot regress sequence or byte offset")
            connection.execute("INSERT INTO normalized_events VALUES(?,?,?,?,?,?)",
                               (event.event_id, event.execution_id, event.stream, event.sequence,
                                event.offset_bytes, body))
            connection.execute("""INSERT INTO source_cursors VALUES(?,?,?,?,?)
                ON CONFLICT(execution_id,stream) DO UPDATE SET host_boot_id=excluded.host_boot_id,
                sequence=excluded.sequence, offset_bytes=excluded.offset_bytes""",
                               (cursor.execution_id, cursor.stream, cursor.host_boot_id,
                                cursor.sequence, cursor.offset_bytes))
            connection.commit()
            return True
    except sqlite3.Error as exc:
        raise store._raise_sqlite(exc) from exc


def get_cursor(store: _Store, execution_id: str, stream: str) -> SourceCursor | None:
    try:
        with store._session() as connection:
            row = connection.execute("SELECT * FROM source_cursors WHERE execution_id=? AND stream=?",
                                     (execution_id, stream)).fetchone()
            return None if row is None else SourceCursor(row["execution_id"], row["stream"], row["host_boot_id"],
                                                          row["sequence"], row["offset_bytes"])
    except sqlite3.Error as exc:
        raise store._raise_sqlite(exc) from exc


def get_event(store: _Store, event_id: str) -> NormalizedEvent | None:
    try:
        with store._session() as connection:
            row = connection.execute("SELECT body FROM normalized_events WHERE event_id=?", (event_id,)).fetchone()
            return None if row is None else event_from_dict(json.loads(row["body"]))
    except (sqlite3.Error, ValueError, TypeError) as exc:
        if isinstance(exc, sqlite3.Error):
            raise store._raise_sqlite(exc) from exc
        raise StoreError(f"stored event is invalid: {exc}") from exc


def record_stream_gap(store: _Store, *, gap_id: str, execution_id: str, stream: str,
                      first_sequence: int, last_sequence: int, first_offset: int,
                      last_offset: int, dropped_bytes: int, dropped_frames: int,
                      reason: str, recorded_at: str) -> bool:
    _bounded_token(gap_id, "gap_id", 256)
    _bounded_token(execution_id, "execution_id", 512)
    _bounded_token(reason, "reason", 64)
    _bounded_token(recorded_at, "recorded_at", 64)
    if stream not in ("stdout", "stderr"):
        raise ValueError("stream must be stdout or stderr")
    values = (first_sequence, last_sequence, first_offset, last_offset, dropped_bytes, dropped_frames)
    if any(type(value) is not int or value < 0 for value in values) or dropped_frames < 1:
        raise ValueError("gap coordinates and counts must be nonnegative; dropped_frames must be positive")
    if last_sequence < first_sequence or last_offset < first_offset:
        raise ValueError("gap bounds must be ordered")
    try:
        with store._session() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM stream_gaps WHERE gap_id=?", (gap_id,)).fetchone()
            body = (execution_id, stream, first_sequence, last_sequence, first_offset, last_offset,
                    dropped_bytes, dropped_frames, reason, recorded_at)
            if row is not None:
                existing = tuple(row[key] for key in ("execution_id", "stream", "first_sequence", "last_sequence",
                                  "first_offset", "last_offset", "dropped_bytes", "dropped_frames", "reason", "recorded_at"))
                if existing == body:
                    connection.commit()
                    return False
                ensure_write_capacity(store.path, store.max_store_bytes, 8 * 1024)
                immutable = (0, 1, 2, 4, 8)
                monotonic = (3, 5, 6, 7)
                if any(existing[index] != body[index] for index in immutable) or any(
                        body[index] < existing[index] for index in monotonic):
                    raise ValueError("gap_id replay has different or regressing content")
                connection.execute("""UPDATE stream_gaps SET last_sequence=?,last_offset=?,dropped_bytes=?,
                    dropped_frames=? WHERE gap_id=?""", (body[3], body[5], body[6], body[7], gap_id))
                connection.commit()
                return False
            ensure_write_capacity(store.path, store.max_store_bytes, 8 * 1024)
            connection.execute("INSERT INTO stream_gaps VALUES(?,?,?,?,?,?,?,?,?,?,?)", (gap_id, *body))
            connection.commit()
            return True
    except sqlite3.Error as exc:
        raise store._raise_sqlite(exc) from exc


def list_stream_gaps(store: _Store, *, execution_id: str | None = None,
                     limit: int = 100) -> tuple[dict[str, object], ...]:
    if type(limit) is not int or not 1 <= limit <= 1000:
        raise ValueError("limit must be between 1 and 1000")
    if execution_id is not None:
        _bounded_token(execution_id, "execution_id", 512)
    try:
        with store._session() as connection:
            if execution_id is None:
                rows = connection.execute("SELECT * FROM stream_gaps ORDER BY recorded_at,gap_id LIMIT ?",
                                          (limit,)).fetchall()
            else:
                rows = connection.execute("SELECT * FROM stream_gaps WHERE execution_id=? "
                                          "ORDER BY recorded_at,gap_id LIMIT ?", (execution_id, limit)).fetchall()
            return tuple(dict(row) for row in rows)
    except sqlite3.Error as exc:
        raise store._raise_sqlite(exc) from exc


__all__ = ["SourceCursor", "StreamGapRecord", "append_batch", "append_event", "get_cursor", "get_event",
           "list_stream_gaps", "record_stream_gap"]
