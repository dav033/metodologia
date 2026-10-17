"""M4 SQLite schema migrations with storage-capacity guards."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from .storage_limits import WRITE_RESERVE_BYTES, StoreError, measured_store_bytes


def ensure_duplicate_table_headroom(path: Path, max_store_bytes: int, migration: str) -> None:
    """Refuse a table rebuild without room for a full measured DB+WAL copy."""
    measured_bytes = measured_store_bytes(path)
    estimated_bytes = (2 * measured_bytes) + WRITE_RESERVE_BYTES
    if estimated_bytes > max_store_bytes:
        raise StoreError(
            f"storage_pressure: {migration} requires bounded duplicate-table headroom "
            f"estimated_bytes={estimated_bytes} limit_bytes={max_store_bytes}"
        )


def ensure_v1_migration_capacity(path: Path, max_store_bytes: int) -> None:
    ensure_duplicate_table_headroom(path, max_store_bytes, "schema migration")


def migrate_v1_event_schema(connection: sqlite3.Connection, path: Path, max_store_bytes: int) -> None:
    """Replace v1's per-sequence uniqueness rule without exceeding the configured store ceiling."""
    connection.execute("BEGIN IMMEDIATE")
    try:
        connection.execute("ALTER TABLE normalized_events RENAME TO normalized_events_v1")
        connection.execute("""CREATE TABLE normalized_events (
            event_id TEXT PRIMARY KEY, execution_id TEXT NOT NULL, stream TEXT NOT NULL,
            sequence INTEGER NOT NULL, offset_bytes INTEGER NOT NULL, body TEXT NOT NULL
        )""")
        connection.execute("""INSERT INTO normalized_events
            SELECT event_id,execution_id,stream,sequence,offset_bytes,body FROM normalized_events_v1""")
        connection.execute("DROP TABLE normalized_events_v1")
        connection.execute("UPDATE schema_meta SET version=2")
        projected_bytes = measured_store_bytes(path)
        if projected_bytes > max_store_bytes:
            raise StoreError(
                "storage_pressure: schema migration projected size exceeds configured limit "
                f"projected_bytes={projected_bytes} limit_bytes={max_store_bytes}"
            )
        connection.commit()
    except BaseException:
        connection.rollback()
        raise


__all__ = ["ensure_duplicate_table_headroom", "ensure_v1_migration_capacity", "migrate_v1_event_schema"]
