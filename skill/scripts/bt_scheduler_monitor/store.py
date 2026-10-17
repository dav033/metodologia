"""Durable, M4-owned SQLite storage for normalized monitor records."""
from __future__ import annotations

import json
import math
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from collections.abc import Iterator, Mapping

from .contracts import Incident, MetricSample, NormalizedEvent
from .serialization import incident_from_dict, incident_to_dict
from .store_migrations import ensure_v1_migration_capacity, migrate_v1_event_schema
from .storage_limits import (MAX_STORE_BYTES, WRITE_RESERVE_BYTES, StoreError,
                             ensure_write_capacity)
from .stream_store import (SourceCursor, StreamGapRecord, _bounded_token, _json, append_batch,
                           append_event, get_cursor, get_event, list_stream_gaps, record_stream_gap)

SCHEMA_VERSION = 2
MAX_OUTBOX_REFERENCE_BYTES = 4_096
MAX_OUTBOX_KEY_BYTES = 256
MAX_OUTBOX_CLAIM_TOKEN_BYTES = 256
MAX_OUTBOX_ERROR_CODE_BYTES = 32
# Includes the reference, bounded keys, SQLite record/index overhead, and free-page margin.
MAX_OUTBOX_ITEM_BYTES = 8_192
MAX_OUTBOX_ITEMS = MAX_STORE_BYTES // MAX_OUTBOX_ITEM_BYTES
MAX_OUTBOX_CLAIM_BATCH = 1_000
OUTBOX_RETRY_ERROR_CODES = frozenset(("temporary_failure", "timeout", "unavailable", "invalid_ack",
                                     "rejected", "unknown"))

_SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_meta (version INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS store_limits (singleton INTEGER PRIMARY KEY CHECK(singleton=1),
  max_store_bytes INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS normalized_events (
  event_id TEXT PRIMARY KEY, execution_id TEXT NOT NULL, stream TEXT NOT NULL,
  sequence INTEGER NOT NULL, offset_bytes INTEGER NOT NULL, body TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS source_cursors (
  execution_id TEXT NOT NULL, stream TEXT NOT NULL, host_boot_id TEXT,
  sequence INTEGER NOT NULL, offset_bytes INTEGER NOT NULL,
  PRIMARY KEY(execution_id, stream)
);
CREATE TABLE IF NOT EXISTS stream_gaps (
  gap_id TEXT PRIMARY KEY, execution_id TEXT NOT NULL, stream TEXT NOT NULL,
  first_sequence INTEGER NOT NULL, last_sequence INTEGER NOT NULL,
  first_offset INTEGER NOT NULL, last_offset INTEGER NOT NULL,
  dropped_bytes INTEGER NOT NULL, dropped_frames INTEGER NOT NULL,
  reason TEXT NOT NULL, recorded_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS incidents (
  incident_id TEXT PRIMARY KEY, resolution_state TEXT NOT NULL, body TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS incident_evidence_refs (
  incident_id TEXT NOT NULL REFERENCES incidents(incident_id) ON DELETE CASCADE,
  evidence_ref TEXT NOT NULL, PRIMARY KEY(incident_id, evidence_ref)
);
CREATE TABLE IF NOT EXISTS m1_outbox (
  idempotency_key TEXT PRIMARY KEY, incident_id TEXT NOT NULL REFERENCES incidents(incident_id),
  body TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'pending', claim_token TEXT,
  lease_until REAL, attempts INTEGER NOT NULL DEFAULT 0, last_error TEXT
);
CREATE INDEX IF NOT EXISTS m1_outbox_ready ON m1_outbox(state, lease_until);
"""


@dataclass(frozen=True)
class OutboxItem:
    idempotency_key: str
    incident_id: str
    payload: Mapping[str, object]
    attempts: int
    claim_token: str


def _incident_reference(incident: Incident) -> dict[str, object]:
    return {"schema_version": incident.schema_version, "incident_id": incident.incident_id,
            "run_id": incident.run_id, "task_id": incident.task_id,
            "attempt_id": incident.attempt_id, "execution_id": incident.execution_id,
            "detector_id": incident.detector_id, "type": incident.type,
            "severity": incident.severity}


class MonitorStore:
    """Separate WAL database. In-memory activity and detector caches are not durable here."""

    def __init__(self, path: str | Path, *, busy_timeout_ms: int = 5_000,
                 max_outbox_items: int = MAX_OUTBOX_ITEMS, max_store_bytes: int = MAX_STORE_BYTES):
        self.path = Path(path)
        if type(busy_timeout_ms) is not int or busy_timeout_ms < 0:
            raise ValueError("busy_timeout_ms must be a nonnegative integer")
        if type(max_outbox_items) is not int or not 0 < max_outbox_items <= MAX_OUTBOX_ITEMS:
            raise ValueError(f"max_outbox_items must be between 1 and {MAX_OUTBOX_ITEMS}")
        if type(max_store_bytes) is not int or max_store_bytes <= WRITE_RESERVE_BYTES:
            raise ValueError(f"max_store_bytes must be greater than {WRITE_RESERVE_BYTES}")
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self._session(busy_timeout_ms) as connection:
                connection.execute("PRAGMA foreign_keys=ON")
                has_schema_meta = connection.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_meta'"
                ).fetchone() is not None
                prior_version = (connection.execute("SELECT version FROM schema_meta LIMIT 1").fetchone()
                                 if has_schema_meta else None)
                if prior_version is not None and prior_version[0] == 1:
                    ensure_v1_migration_capacity(self.path, max_store_bytes)
                ensure_write_capacity(self.path, max_store_bytes)
                connection.execute("PRAGMA journal_mode=WAL")
                connection.executescript(_SCHEMA)
                row = connection.execute("SELECT version FROM schema_meta LIMIT 1").fetchone()
                if row is None:
                    connection.execute("INSERT INTO schema_meta(version) VALUES(?)", (SCHEMA_VERSION,))
                elif row[0] == 1:
                    migrate_v1_event_schema(connection, self.path, max_store_bytes)
                elif row[0] != SCHEMA_VERSION:
                    raise StoreError(f"unsupported M4 store schema version {row[0]}")
                connection.execute("INSERT INTO store_limits(singleton,max_store_bytes) VALUES(1,?) "
                                   "ON CONFLICT(singleton) DO UPDATE SET max_store_bytes=excluded.max_store_bytes",
                                   (max_store_bytes,))
                connection.commit()
        except sqlite3.Error as exc:
            raise StoreError(f"SQLite initialization failed: {exc}") from exc
        self.busy_timeout_ms = busy_timeout_ms
        self.max_outbox_items = max_outbox_items
        self.max_store_bytes = max_store_bytes

    def _connect(self, timeout_ms: int | None = None) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=(self.busy_timeout_ms if timeout_ms is None else timeout_ms) / 1000)
        connection.row_factory = sqlite3.Row
        connection.execute(f"PRAGMA busy_timeout={self.busy_timeout_ms if timeout_ms is None else timeout_ms}")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    @contextmanager
    def _session(self, timeout_ms: int | None = None) -> Iterator[sqlite3.Connection]:
        connection = self._connect(timeout_ms)
        try:
            yield connection
        finally:
            connection.close()

    @staticmethod
    def _raise_sqlite(exc: sqlite3.Error) -> StoreError:
        # SQLITE_BUSY/FULL remain visible as store failures; upstream must retain the frame.
        return StoreError(f"SQLite operation failed: {exc}")

    def append_event(self, event: NormalizedEvent, cursor: SourceCursor) -> bool:
        return append_event(self, event, cursor)

    def append_batch(self, *, events: tuple[NormalizedEvent, ...] = (),
                     metrics: tuple[MetricSample, ...] = (),
                     gaps: tuple[StreamGapRecord, ...] = (),
                     cursors: tuple[SourceCursor, ...] = ()) -> bool:
        return append_batch(self, events=events, metrics=metrics, gaps=gaps, cursors=cursors)

    def get_cursor(self, execution_id: str, stream: str) -> SourceCursor | None:
        return get_cursor(self, execution_id, stream)

    def get_event(self, event_id: str) -> NormalizedEvent | None:
        return get_event(self, event_id)

    def record_stream_gap(self, *, gap_id: str, execution_id: str, stream: str,
                          first_sequence: int, last_sequence: int, first_offset: int,
                          last_offset: int, dropped_bytes: int, dropped_frames: int,
                          reason: str, recorded_at: str) -> bool:
        return record_stream_gap(self, gap_id=gap_id, execution_id=execution_id, stream=stream,
                                 first_sequence=first_sequence, last_sequence=last_sequence,
                                 first_offset=first_offset, last_offset=last_offset,
                                 dropped_bytes=dropped_bytes, dropped_frames=dropped_frames,
                                 reason=reason, recorded_at=recorded_at)

    def list_stream_gaps(self, *, execution_id: str | None = None, limit: int = 100) -> tuple[dict[str, object], ...]:
        return list_stream_gaps(self, execution_id=execution_id, limit=limit)

    def put_incident(self, incident: Incident) -> bool:
        if not isinstance(incident, Incident):
            raise ValueError("incident must be a validated Incident contract")
        body = _json(incident_to_dict(incident))
        try:
            with self._session() as connection:
                connection.execute("BEGIN IMMEDIATE")
                existing = connection.execute("SELECT body FROM incidents WHERE incident_id=?",
                                              (incident.incident_id,)).fetchone()
                if existing is None:
                    ensure_write_capacity(self.path, self.max_store_bytes, 64 * 1024)
                    connection.execute("INSERT INTO incidents VALUES(?,?,?)",
                                       (incident.incident_id, incident.resolution_state, body))
                    connection.executemany("INSERT INTO incident_evidence_refs VALUES(?,?)",
                                           ((incident.incident_id, ref) for ref in incident.evidence_refs))
                    connection.commit()
                    return True
                old = incident_from_dict(json.loads(existing["body"]))
                if (old.schema_version, old.run_id, old.task_id, old.attempt_id, old.execution_id,
                        old.detector_id, old.type, old.severity) != (
                    incident.schema_version, incident.run_id, incident.task_id, incident.attempt_id,
                    incident.execution_id, incident.detector_id, incident.type, incident.severity
                ):
                    raise ValueError("incident reference identity cannot change")
                if old.resolution_state == "resolved" and incident.resolution_state == "open":
                    raise ValueError("resolved incident cannot be reopened")
                incoming_at = incident.last_seen_at
                stored_at = old.last_seen_at
                incoming_last_seen = datetime.fromisoformat(
                    incoming_at[:-1] + "+00:00" if incoming_at.endswith("Z") else incoming_at
                )
                stored_last_seen = datetime.fromisoformat(
                    stored_at[:-1] + "+00:00" if stored_at.endswith("Z") else stored_at
                )
                if incoming_last_seen < stored_last_seen:
                    raise ValueError("incident observations must be chronological")
                if old.resolution_state == "resolved" and body != existing["body"]:
                    raise ValueError("resolved incident is immutable")
                ensure_write_capacity(self.path, self.max_store_bytes, 64 * 1024)
                connection.execute("UPDATE incidents SET resolution_state=?, body=? WHERE incident_id=?",
                                   (incident.resolution_state, body, incident.incident_id))
                connection.executemany("INSERT OR IGNORE INTO incident_evidence_refs VALUES(?,?)",
                                       ((incident.incident_id, ref) for ref in incident.evidence_refs))
                connection.commit()
                return False
        except sqlite3.Error as exc:
            raise self._raise_sqlite(exc) from exc

    def get_incident(self, incident_id: str) -> Incident | None:
        try:
            with self._session() as connection:
                row = connection.execute("SELECT body FROM incidents WHERE incident_id=?", (incident_id,)).fetchone()
                return None if row is None else incident_from_dict(json.loads(row["body"]))
        except sqlite3.Error as exc:
            raise self._raise_sqlite(exc) from exc

    def enqueue_incident(self, incident: Incident, idempotency_key: str,
                         payload: Mapping[str, object] | None = None) -> bool:
        if not isinstance(incident, Incident):
            raise ValueError("validated incident and non-empty idempotency key are required")
        idempotency_key = _bounded_token(idempotency_key, "idempotency_key", MAX_OUTBOX_KEY_BYTES)
        expected = _incident_reference(incident)
        reference = expected if payload is None else payload
        if (not isinstance(reference, Mapping) or set(reference) != set(expected) or
                any(type(reference[field]) is not type(value) or reference[field] != value
                    for field, value in expected.items())):
            raise ValueError("outbox payload must match the versioned incident-reference fields")
        body = _json(dict(reference))
        if len(body.encode("utf-8")) > MAX_OUTBOX_REFERENCE_BYTES:
            raise ValueError(f"outbox incident reference exceeds {MAX_OUTBOX_REFERENCE_BYTES} bytes")
        try:
            with self._session() as connection:
                connection.execute("BEGIN IMMEDIATE")
                stored = connection.execute("SELECT body FROM incidents WHERE incident_id=?",
                                            (incident.incident_id,)).fetchone()
                ensure_write_capacity(self.path, self.max_store_bytes, 64 * 1024)
                if stored is None:
                    connection.execute("INSERT INTO incidents VALUES(?,?,?)",
                                       (incident.incident_id, incident.resolution_state,
                                        _json(incident_to_dict(incident))))
                    connection.executemany("INSERT INTO incident_evidence_refs VALUES(?,?)",
                                           ((incident.incident_id, ref) for ref in incident.evidence_refs))
                else:
                    stored_incident = incident_from_dict(json.loads(stored["body"]))
                    if _incident_reference(stored_incident) != expected:
                        raise ValueError("outbox incident reference does not match the persisted incident")
                existing = connection.execute("SELECT incident_id,body FROM m1_outbox WHERE idempotency_key=?",
                                              (idempotency_key,)).fetchone()
                if existing is not None:
                    if existing["incident_id"] != incident.incident_id or existing["body"] != body:
                        raise ValueError("outbox idempotency key reused with different content")
                    connection.commit()
                    return False
                undelivered = connection.execute(
                    "SELECT COUNT(*) FROM m1_outbox WHERE state IN ('pending','claimed')"
                ).fetchone()[0]
                if undelivered >= self.max_outbox_items:
                    raise StoreError(f"M1 incident outbox reached its {self.max_outbox_items}-item limit")
                connection.execute("INSERT INTO m1_outbox(idempotency_key,incident_id,body) VALUES(?,?,?)",
                                   (idempotency_key, incident.incident_id, body))
                connection.commit()
                return True
        except sqlite3.Error as exc:
            raise self._raise_sqlite(exc) from exc

    def claim_outbox(self, claim_token: str, *, now: float, lease_seconds: float, limit: int = 100) -> tuple[OutboxItem, ...]:
        if (isinstance(now, bool) or not isinstance(now, (int, float)) or isinstance(lease_seconds, bool) or
                not isinstance(lease_seconds, (int, float)) or type(limit) is not int or
                not 0 < limit <= MAX_OUTBOX_CLAIM_BATCH):
            raise ValueError("valid claim token, times and positive limit are required")
        claim_token = _bounded_token(claim_token, "claim_token", MAX_OUTBOX_CLAIM_TOKEN_BYTES)
        try:
            now_value, lease_value = float(now), float(lease_seconds)
        except OverflowError as exc:
            raise ValueError("claim times must be finite numbers") from exc
        expires_at = now_value + lease_value
        if (not math.isfinite(now_value) or now_value < 0 or not math.isfinite(lease_value) or
                lease_value <= 0 or not math.isfinite(expires_at)):
            raise ValueError("claim times and lease expiry must be finite, with a positive lease")
        try:
            with self._session() as connection:
                connection.execute("BEGIN IMMEDIATE")
                ensure_write_capacity(self.path, self.max_store_bytes,
                                      WRITE_RESERVE_BYTES + limit * 512)
                rows = connection.execute("""SELECT idempotency_key,incident_id,body,attempts FROM m1_outbox
                    WHERE state='pending' OR (state='claimed' AND lease_until<=?)
                    ORDER BY idempotency_key LIMIT ?""", (now_value, limit)).fetchall()
                claimed: list[OutboxItem] = []
                for row in rows:
                    connection.execute("""UPDATE m1_outbox SET state='claimed',claim_token=?,lease_until=?,
                        attempts=attempts+1 WHERE idempotency_key=?""",
                                       (claim_token, expires_at, row["idempotency_key"]))
                    claimed.append(OutboxItem(row["idempotency_key"], row["incident_id"],
                                              json.loads(row["body"]), row["attempts"] + 1, claim_token))
                connection.commit()
                return tuple(claimed)
        except sqlite3.Error as exc:
            raise self._raise_sqlite(exc) from exc

    def ack_outbox(self, idempotency_key: str, claim_token: str) -> bool:
        return self._settle_outbox(idempotency_key, claim_token, None)

    def retry_outbox(self, idempotency_key: str, claim_token: str, error: str) -> bool:
        if (not isinstance(error, str) or error not in OUTBOX_RETRY_ERROR_CODES or
                len(error.encode("utf-8")) > MAX_OUTBOX_ERROR_CODE_BYTES):
            raise ValueError("retry error must be an allowlisted code")
        return self._settle_outbox(idempotency_key, claim_token, error)

    def _settle_outbox(self, key: str, token: str, error: str | None) -> bool:
        key = _bounded_token(key, "idempotency_key", MAX_OUTBOX_KEY_BYTES)
        token = _bounded_token(token, "claim_token", MAX_OUTBOX_CLAIM_TOKEN_BYTES)
        try:
            with self._session() as connection:
                connection.execute("BEGIN IMMEDIATE")
                ensure_write_capacity(self.path, self.max_store_bytes, 8 * 1024)
                if error is None:
                    cursor = connection.execute("""UPDATE m1_outbox SET state='acked',claim_token=NULL,lease_until=NULL
                        WHERE idempotency_key=? AND state='claimed' AND claim_token=?""", (key, token))
                else:
                    cursor = connection.execute("""UPDATE m1_outbox SET state='pending',claim_token=NULL,lease_until=NULL,last_error=?
                        WHERE idempotency_key=? AND state='claimed' AND claim_token=?""", (error, key, token))
                connection.commit()
                return cursor.rowcount == 1
        except sqlite3.Error as exc:
            raise self._raise_sqlite(exc) from exc


__all__ = ["MonitorStore", "OutboxItem", "SourceCursor", "StoreError"]
