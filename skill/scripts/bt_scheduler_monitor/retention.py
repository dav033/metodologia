"""Versioned metric-history extension and bounded M4 retention operations."""
from __future__ import annotations

import json
import shutil
import sqlite3
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .contracts import MetricSample
from .serialization import metric_to_dict
from .storage_limits import (
    MAX_STORE_BYTES,
    WRITE_RESERVE_BYTES,
    StoreError,
    ensure_write_capacity,
    measured_store_bytes,
)
from .store_migrations import ensure_duplicate_table_headroom

RETENTION_DAYS = 90
RESOLVED_INCIDENT_DAYS = 365
AGGREGATE_DAYS = 730
METRIC_EXTENSION_VERSION = 2
RETENTION_BATCH_SIZE = 4
RETENTION_BATCH_RESERVE_BYTES = WRITE_RESERVE_BYTES // 4
RETENTION_ITEM_RESERVE_BYTES = RETENTION_BATCH_RESERVE_BYTES // RETENTION_BATCH_SIZE

_METRIC_SCHEMA = (
    "CREATE TABLE IF NOT EXISTS m4_extension_meta (name TEXT PRIMARY KEY, version INTEGER NOT NULL)",
    "CREATE TABLE IF NOT EXISTS metric_samples (metric_id TEXT PRIMARY KEY, observed_at TEXT NOT NULL, body TEXT NOT NULL)",
    "CREATE INDEX IF NOT EXISTS metric_samples_observed ON metric_samples(observed_at)",
    """CREATE TABLE IF NOT EXISTS daily_metric_aggregates (
      day TEXT NOT NULL, group_key TEXT NOT NULL, provider TEXT NOT NULL, name TEXT NOT NULL,
      unit TEXT NOT NULL, source TEXT NOT NULL, quality TEXT NOT NULL, comparability_key TEXT NOT NULL,
      profile_id TEXT, model TEXT, value_sum REAL, sample_count INTEGER NOT NULL,
      first_observed_at TEXT NOT NULL, last_observed_at TEXT NOT NULL, PRIMARY KEY(day, group_key))""",
    """CREATE TABLE IF NOT EXISTS m4_retention_health (
      singleton INTEGER PRIMARY KEY CHECK(singleton=1), state TEXT NOT NULL, measured_bytes INTEGER NOT NULL,
      updated_at TEXT NOT NULL)""",
)


@dataclass(frozen=True)
class RetentionResult:
    deleted_events: int
    deleted_incidents: int
    compacted_samples: int
    deleted_aggregates: int
    measured_bytes: int
    storage_pressure: bool


def _connect(path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(Path(path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def _ensure_extension(connection: sqlite3.Connection, path: Path, max_store_bytes: int) -> None:
    has_meta = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='m4_extension_meta'"
    ).fetchone() is not None
    prior = (connection.execute("SELECT version FROM m4_extension_meta WHERE name='metrics'").fetchone()
             if has_meta else None)
    if prior is not None and prior["version"] == 1:
        ensure_duplicate_table_headroom(path, max_store_bytes, "M4 metric extension migration")
    for statement in _METRIC_SCHEMA:
        connection.execute(statement)
    row = connection.execute("SELECT version FROM m4_extension_meta WHERE name='metrics'").fetchone()
    if row is None:
        connection.execute("INSERT INTO m4_extension_meta(name,version) VALUES('metrics',?)",
                           (METRIC_EXTENSION_VERSION,))
    elif row["version"] == 1:
        connection.execute("""CREATE TABLE daily_metric_aggregates_v2 (
          day TEXT NOT NULL, group_key TEXT NOT NULL, provider TEXT NOT NULL, name TEXT NOT NULL,
          unit TEXT NOT NULL, source TEXT NOT NULL, quality TEXT NOT NULL, comparability_key TEXT NOT NULL,
          profile_id TEXT, model TEXT, value_sum REAL, sample_count INTEGER NOT NULL,
          first_observed_at TEXT NOT NULL, last_observed_at TEXT NOT NULL, PRIMARY KEY(day, group_key))""")
        connection.execute("""INSERT INTO daily_metric_aggregates_v2
            SELECT day,group_key,provider,name,unit,source,quality,comparability_key,profile_id,model,value_sum,
            sample_count,first_observed_at,last_observed_at FROM daily_metric_aggregates""")
        connection.execute("DROP TABLE daily_metric_aggregates")
        connection.execute("ALTER TABLE daily_metric_aggregates_v2 RENAME TO daily_metric_aggregates")
        connection.execute("UPDATE m4_extension_meta SET version=? WHERE name='metrics'",
                           (METRIC_EXTENSION_VERSION,))
    elif row["version"] != METRIC_EXTENSION_VERSION:
        raise RuntimeError(f"unsupported M4 metrics extension version {row['version']}")


def ensure_metric_extension(connection: sqlite3.Connection, path: str | Path,
                            max_store_bytes: int = MAX_STORE_BYTES) -> None:
    """Ensure metric tables exist inside the caller's active transaction."""
    _ensure_extension(connection, Path(path), max_store_bytes)


def record_metric_sample(path: str | Path, sample: MetricSample, *,
                         max_store_bytes: int = MAX_STORE_BYTES) -> bool:
    if not isinstance(sample, MetricSample):
        raise ValueError("sample must be a validated MetricSample")
    body = json.dumps(metric_to_dict(sample), sort_keys=True, separators=(",", ":"), allow_nan=False)
    connection = _connect(path)
    try:
        connection.execute("BEGIN IMMEDIATE")
        ensure_write_capacity(path, max_store_bytes)
        _ensure_extension(connection, Path(path), max_store_bytes)
        prior = connection.execute("SELECT body FROM metric_samples WHERE metric_id=?", (sample.metric_id,)).fetchone()
        if prior is not None:
            if prior["body"] != body:
                raise ValueError("metric_id replay has different content")
            if measured_store_bytes(path) > max_store_bytes:
                raise StoreError("storage_pressure: projected metric extension size exceeds configured limit")
            connection.commit()
            return False
        connection.execute("INSERT INTO metric_samples VALUES(?,?,?)", (sample.metric_id, sample.observed_at, body))
        projected_bytes = measured_store_bytes(path)
        if projected_bytes > max_store_bytes:
            raise StoreError(
                f"storage_pressure: projected metric size={projected_bytes} limit_bytes={max_store_bytes}"
            )
        connection.commit()
        return True
    except BaseException:
        connection.rollback()
        raise
    finally:
        connection.close()


def _group_key(sample: dict[str, object], day: str) -> str:
    fields = ["provider", "name", "unit", "source", "quality", "comparability_key", "profile_id", "model"]
    values = [sample.get(field) for field in fields]
    if sample.get("comparability_key") in (None, "", "unknown", "unavailable"):
        values.append(sample.get("metric_id"))
    encoded = json.dumps([day, *values], ensure_ascii=False, separators=(",", ":"), sort_keys=False)
    import hashlib
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _compact(connection: sqlite3.Connection, cutoff: str, limit: int = RETENTION_BATCH_SIZE) -> int:
    rows = connection.execute(
        """SELECT metric_id,observed_at,body FROM metric_samples
        WHERE julianday(observed_at)<julianday(?) ORDER BY julianday(observed_at),metric_id LIMIT ?""",
        (cutoff, limit),
    ).fetchall()
    groups: dict[tuple[str, str], list[object]] = {}
    for row in rows:
        sample = json.loads(row["body"])
        day = sample["observed_at"][:10]
        key = (day, _group_key(sample, day))
        group = groups.setdefault(key, [sample, None, 0, sample["observed_at"], sample["observed_at"]])
        value = sample["value"]
        if value is not None:
            group[1] = (0.0 if group[1] is None else float(group[1])) + float(value)
            group[2] = int(group[2]) + int(sample["sample_count"])
        observed = datetime.fromisoformat(sample["observed_at"].replace("Z", "+00:00"))
        first_seen = datetime.fromisoformat(str(group[3]).replace("Z", "+00:00"))
        last_seen = datetime.fromisoformat(str(group[4]).replace("Z", "+00:00"))
        if observed < first_seen:
            group[3] = sample["observed_at"]
        if observed > last_seen:
            group[4] = sample["observed_at"]
    for (day, group_key), (sample, value_sum, sample_count, first, last) in groups.items():
        existing = connection.execute("""SELECT value_sum,sample_count,first_observed_at,last_observed_at
            FROM daily_metric_aggregates WHERE day=? AND group_key=?""", (day, group_key)).fetchone()
        if existing is None:
            connection.execute("INSERT INTO daily_metric_aggregates VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                               (day, group_key, sample["provider"], sample["name"], sample["unit"], sample["source"],
                                sample["quality"], sample["comparability_key"], sample.get("profile_id"), sample.get("model"),
                                value_sum, sample_count, first, last))
            continue
        prior_first = datetime.fromisoformat(existing["first_observed_at"].replace("Z", "+00:00"))
        next_first = datetime.fromisoformat(str(first).replace("Z", "+00:00"))
        prior_last = datetime.fromisoformat(existing["last_observed_at"].replace("Z", "+00:00"))
        next_last = datetime.fromisoformat(str(last).replace("Z", "+00:00"))
        merged_first = first if next_first < prior_first else existing["first_observed_at"]
        merged_last = last if next_last > prior_last else existing["last_observed_at"]
        prior_value = existing["value_sum"]
        merged_value = (None if prior_value is None and value_sum is None else
                        (0.0 if prior_value is None else float(prior_value)) +
                        (0.0 if value_sum is None else float(value_sum)))
        connection.execute("""UPDATE daily_metric_aggregates SET value_sum=?,sample_count=?,
            first_observed_at=?,last_observed_at=? WHERE day=? AND group_key=?""",
                           (merged_value, existing["sample_count"] + sample_count, merged_first, merged_last,
                            day, group_key))
    if rows:
        connection.executemany("DELETE FROM metric_samples WHERE metric_id=?", ((row["metric_id"],) for row in rows))
    return len(rows)


def _store_size(path: Path) -> int:
    return measured_store_bytes(path)


def _vacuum_has_temporary_space(path: Path, sqlite_temp_dirs: tuple[Path, ...]) -> bool:
    if not sqlite_temp_dirs:
        return False
    try:
        database_bytes = path.stat().st_size
        database_required_bytes = database_bytes * 2 + RETENTION_BATCH_RESERVE_BYTES
        temporary_required_bytes = database_bytes + RETENTION_BATCH_RESERVE_BYTES
        if shutil.disk_usage(path.parent).free < database_required_bytes:
            return False
        return all(directory.is_dir()
                   and shutil.disk_usage(directory).free >= temporary_required_bytes
                   for directory in sqlite_temp_dirs)
    except OSError:
        return False


def vacuum_for_recovery(path: str | Path, *, sqlite_temp_dirs: Iterable[str | Path]) -> int:
    """Compact an offline recovery copy using every explicitly supplied SQLite temp directory."""
    if isinstance(sqlite_temp_dirs, (str, bytes, Path)):
        raise ValueError("sqlite_temp_dirs must be an iterable of directory paths")
    try:
        temp_dirs = tuple(Path(directory) for directory in sqlite_temp_dirs)
    except (TypeError, ValueError) as exc:
        raise ValueError("sqlite_temp_dirs must contain valid directory paths") from exc
    path_obj = Path(path)
    if not temp_dirs or not _vacuum_has_temporary_space(path_obj, temp_dirs):
        raise StoreError("recovery_vacuum_space_unavailable: every sqlite_temp_dirs path needs headroom")
    connection = _connect(path_obj)
    try:
        connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        if not _vacuum_has_temporary_space(path_obj, temp_dirs):
            raise StoreError("recovery_vacuum_space_unavailable: headroom changed before VACUUM")
        _vacuum_store(connection)
        connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        return _store_size(path_obj)
    except sqlite3.Error as exc:
        raise StoreError(f"recovery_vacuum_failed: {exc}") from exc
    finally:
        connection.close()


def _begin_retention_batch(connection: sqlite3.Connection, path: Path, max_store_bytes: int,
                           requested_batch_size: int, *, maintenance: bool) -> tuple[int, int] | None:
    connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    connection.execute("BEGIN IMMEDIATE")
    baseline = _store_size(path)
    batch_size = requested_batch_size
    available = max_store_bytes - baseline
    if available < RETENTION_ITEM_RESERVE_BYTES:
        connection.rollback()
        return None
    batch_size = min(batch_size, available // RETENTION_ITEM_RESERVE_BYTES)
    return baseline, batch_size


def _finish_retention_batch(connection: sqlite3.Connection, path: Path, max_store_bytes: int,
                            baseline: int, *, maintenance: bool) -> bool:
    projected = _store_size(path)
    if projected > max_store_bytes:
        connection.rollback()
        connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        return False
    connection.commit()
    connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    return True


def _run_retention_batch(connection: sqlite3.Connection, path: Path, max_store_bytes: int,
                         operation: Callable[[int], tuple[int, ...]], *,
                         batch_size: int = RETENTION_BATCH_SIZE, adaptive: bool = True,
                         maintenance: bool = False) -> tuple[int, ...] | None:
    started = _begin_retention_batch(connection, path, max_store_bytes, batch_size,
                                     maintenance=maintenance)
    if started is None:
        return None
    baseline, batch_size = started
    try:
        counts = operation(batch_size)
        if not any(counts):
            connection.rollback()
            return counts
        if _finish_retention_batch(connection, path, max_store_bytes, baseline, maintenance=maintenance):
            return counts
        if adaptive and batch_size > 1:
            return _run_retention_batch(connection, path, max_store_bytes, operation,
                                        batch_size=max(1, batch_size // 2), adaptive=adaptive,
                                        maintenance=maintenance)
        return None
    except BaseException:
        connection.rollback()
        raise


def _persist_health(connection: sqlite3.Connection, path: Path, max_store_bytes: int,
                    state: str, measured: int, stamp: str) -> bool:
    counts = _run_retention_batch(connection, path, max_store_bytes, lambda _limit: (
        connection.execute("""INSERT INTO m4_retention_health VALUES(1,?,?,?)
            ON CONFLICT(singleton) DO UPDATE SET state=excluded.state,
            measured_bytes=excluded.measured_bytes,updated_at=excluded.updated_at""",
                           (state, measured, stamp)).rowcount,
    ), adaptive=False, maintenance=True)
    return counts is not None


def _persist_stable_health(connection: sqlite3.Connection, path: Path, max_store_bytes: int,
                            stamp: str) -> tuple[int, bool]:
    for _ in range(5):
        connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        measured = _store_size(path)
        pressure = measured + WRITE_RESERVE_BYTES > max_store_bytes
        state = "storage_pressure" if pressure else "healthy"
        stored = connection.execute("SELECT state,measured_bytes FROM m4_retention_health WHERE singleton=1").fetchone()
        if stored is not None and stored["state"] == state and stored["measured_bytes"] == measured:
            return measured, pressure
        if not _persist_health(connection, path, max_store_bytes, state, measured, stamp):
            return measured, pressure
    raise RuntimeError("retention health size measurement did not stabilize")


def apply_retention(path: str | Path, *, now: datetime | None = None,
                    max_store_bytes: int = MAX_STORE_BYTES,
                    sqlite_temp_dirs: Iterable[str | Path] = ()) -> RetentionResult:
    """Apply bounded cleanup; VACUUM needs the full SQLite temporary-directory candidate list."""
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None or current.utcoffset() is None:
        raise ValueError("now must include a timezone")
    if type(max_store_bytes) is not int or max_store_bytes <= 0:
        raise ValueError("max_store_bytes must be a positive integer")
    if isinstance(sqlite_temp_dirs, (str, bytes, Path)):
        raise ValueError("sqlite_temp_dirs must be an iterable of directory paths")
    try:
        temp_dirs = tuple(Path(directory) for directory in sqlite_temp_dirs)
    except (TypeError, ValueError) as exc:
        raise ValueError("sqlite_temp_dirs must contain valid directory paths") from exc
    current = current.astimezone(timezone.utc)
    event_cutoff = (current - timedelta(days=RETENTION_DAYS)).isoformat().replace("+00:00", "Z")
    incident_cutoff = (current - timedelta(days=RESOLVED_INCIDENT_DAYS)).isoformat().replace("+00:00", "Z")
    aggregate_cutoff = (current - timedelta(days=AGGREGATE_DAYS)).date().isoformat()
    path_obj = Path(path)
    connection = _connect(path_obj)
    try:
        blocked = False
        events = incidents = acked_outbox = evidence_refs = compacted = aggregates = 0

        def initialize(_limit: int) -> tuple[int, ...]:
            _ensure_extension(connection, path_obj, max_store_bytes)
            connection.execute("INSERT INTO store_limits(singleton,max_store_bytes) VALUES(1,?) "
                               "ON CONFLICT(singleton) DO UPDATE SET max_store_bytes=excluded.max_store_bytes",
                               (max_store_bytes,))
            return (1,)

        if _run_retention_batch(connection, path_obj, max_store_bytes, initialize,
                                adaptive=False, maintenance=True) is None:
            blocked = True

        while not blocked:
            def delete_event_batch(limit: int) -> tuple[int, ...]:
                deleted = connection.execute(
                    """DELETE FROM normalized_events WHERE event_id IN (
                    SELECT event_id FROM normalized_events
                    WHERE julianday(json_extract(body,'$.received_at'))<julianday(?)
                    ORDER BY rowid LIMIT ?)""",
                    (event_cutoff, limit),
                ).rowcount
                return (deleted,)

            batch = _run_retention_batch(connection, path_obj, max_store_bytes, delete_event_batch,
                                         maintenance=True)
            if batch is None:
                blocked = True
                break
            if batch[0] == 0:
                break
            events += batch[0]

        while not blocked:
            def delete_incident_batch(limit: int) -> tuple[int, ...]:
                rows = connection.execute(
                    """SELECT incident_id FROM incidents WHERE resolution_state='resolved'
                    AND julianday(json_extract(body,'$.resolved_at'))<julianday(?)
                    AND NOT EXISTS (SELECT 1 FROM m1_outbox WHERE m1_outbox.incident_id=incidents.incident_id
                                    AND m1_outbox.state!='acked')
                    ORDER BY rowid LIMIT 1""",
                    (incident_cutoff,),
                ).fetchall()
                if not rows:
                    return (0, 0, 0)
                incident_id = rows[0][0]
                evidence_rows = connection.execute(
                    "SELECT rowid FROM incident_evidence_refs WHERE incident_id=? ORDER BY rowid LIMIT ?",
                    (incident_id, limit),
                ).fetchall()
                if evidence_rows:
                    connection.executemany("DELETE FROM incident_evidence_refs WHERE rowid=?",
                                           ((row[0],) for row in evidence_rows))
                    return len(evidence_rows), 0, 0
                outbox_rows = connection.execute(
                    "SELECT rowid FROM m1_outbox WHERE incident_id=? AND state='acked' ORDER BY rowid LIMIT ?",
                    (incident_id, limit),
                ).fetchall()
                if outbox_rows:
                    connection.executemany("DELETE FROM m1_outbox WHERE rowid=?",
                                           ((row[0],) for row in outbox_rows))
                    return 0, len(outbox_rows), 0
                deleted = connection.execute(
                    """DELETE FROM incidents WHERE incident_id=?
                    AND NOT EXISTS (SELECT 1 FROM incident_evidence_refs WHERE incident_id=?)
                    AND NOT EXISTS (SELECT 1 FROM m1_outbox WHERE incident_id=?)""",
                    (incident_id, incident_id, incident_id),
                ).rowcount
                return 0, 0, deleted

            batch = _run_retention_batch(connection, path_obj, max_store_bytes, delete_incident_batch,
                                         maintenance=True)
            if batch is None:
                blocked = True
                break
            if not any(batch):
                break
            evidence_refs += batch[0]
            acked_outbox += batch[1]
            incidents += batch[2]

        while not blocked:
            batch = _run_retention_batch(
                connection, path_obj, max_store_bytes,
                lambda limit: (_compact(connection, event_cutoff, limit),),
                maintenance=True,
            )
            if batch is None:
                blocked = True
                break
            if batch[0] == 0:
                break
            compacted += batch[0]

        while not blocked:
            def delete_aggregate_batch(limit: int) -> tuple[int, ...]:
                deleted = connection.execute(
                    """DELETE FROM daily_metric_aggregates WHERE rowid IN (
                    SELECT rowid FROM daily_metric_aggregates WHERE day<? ORDER BY day,group_key LIMIT ?)""",
                    (aggregate_cutoff, limit),
                ).rowcount
                return (deleted,)

            batch = _run_retention_batch(connection, path_obj, max_store_bytes, delete_aggregate_batch,
                                         maintenance=True)
            if batch is None:
                blocked = True
                break
            if batch[0] == 0:
                break
            aggregates += batch[0]

        measured = _store_size(path_obj)
        pressure = measured + WRITE_RESERVE_BYTES > max_store_bytes
        stamp = current.isoformat().replace("+00:00", "Z")
        reclaimed_rows = events + incidents + acked_outbox + evidence_refs + compacted + aggregates
        needs_write_reserve = measured + WRITE_RESERVE_BYTES > max_store_bytes
        vacuum_has_headroom = measured + RETENTION_BATCH_RESERVE_BYTES <= max_store_bytes
        vacuum_due = (pressure or needs_write_reserve) and bool(
            reclaimed_rows or connection.execute("PRAGMA freelist_count").fetchone()[0]
        )
        vacuumed = (vacuum_has_headroom and vacuum_due
                    and _vacuum_has_temporary_space(path_obj, temp_dirs))
        if vacuumed:
            _vacuum_store(connection)
        if not blocked:
            measured, pressure = _persist_stable_health(connection, path_obj, max_store_bytes, stamp)
        if ((pressure or measured + WRITE_RESERVE_BYTES > max_store_bytes) and not vacuumed
                and measured + RETENTION_BATCH_RESERVE_BYTES <= max_store_bytes
                and connection.execute("PRAGMA freelist_count").fetchone()[0]
                and _vacuum_has_temporary_space(path_obj, temp_dirs)):
            _vacuum_store(connection)
            measured = _store_size(path_obj)
            pressure = measured + WRITE_RESERVE_BYTES > max_store_bytes
            if not blocked:
                measured, pressure = _persist_stable_health(connection, path_obj, max_store_bytes, stamp)
        return RetentionResult(events, incidents, compacted, aggregates, measured, pressure)
    except BaseException:
        connection.rollback()
        raise
    finally:
        connection.close()


def _vacuum_store(connection: sqlite3.Connection) -> None:
    connection.execute("VACUUM")
    connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")


__all__ = ["AGGREGATE_DAYS", "MAX_STORE_BYTES", "METRIC_EXTENSION_VERSION", "RetentionResult",
           "apply_retention", "record_metric_sample", "vacuum_for_recovery"]
