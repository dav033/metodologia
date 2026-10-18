"""SQLite-backed item store with a versioned schema migration (v0 -> v1)."""

import sqlite3
from pathlib import Path

LEGACY_VERSION = 0
SCHEMA_VERSION = 1
ITEMS_TABLE = "items"
REPLACEMENT_TABLE = "items_v1"
CREATE_ITEMS_SQL = (
    "CREATE TABLE {name}(id INTEGER PRIMARY KEY, value TEXT NOT NULL, "
    "normalized TEXT NOT NULL)"
)


def normalize(value):
    """Return the normalized form of a stored item value."""
    if not isinstance(value, str):
        raise ValueError(f"item value must be TEXT, got {type(value).__name__}")
    return value.strip().lower()


def migrate(path, fault=None):
    """Bring the database at path to SCHEMA_VERSION in a single transaction.

    fault, if given, is called with 'after_copy' and 'before_commit' during
    conversion. Any exception (including from fault) rolls the migration back.
    """
    conn = sqlite3.connect(path, isolation_level=None)
    try:
        conn.execute("BEGIN IMMEDIATE")
        try:
            _apply_migration(conn, fault)
            conn.execute("COMMIT")
        except BaseException:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise
    finally:
        conn.close()


def read_items(path):
    """Return (id, normalized) pairs ordered by id from a migrated database."""
    conn = _connect_read_only(path)
    try:
        version = _read_version(conn)
        if version != SCHEMA_VERSION:
            raise ValueError(
                f"database is at version {version}, expected {SCHEMA_VERSION}"
            )
        return conn.execute(
            f"SELECT id, normalized FROM {ITEMS_TABLE} ORDER BY id"
        ).fetchall()
    finally:
        conn.close()


def _apply_migration(conn, fault):
    version = _read_version(conn)
    if version == SCHEMA_VERSION:
        return
    if version != LEGACY_VERSION:
        raise ValueError(
            f"unsupported database version {version}; "
            f"this build handles up to {SCHEMA_VERSION}"
        )
    if _table_exists(conn, ITEMS_TABLE):
        _convert_legacy_items(conn, fault)
    else:
        conn.execute(CREATE_ITEMS_SQL.format(name=ITEMS_TABLE))
    conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
    _call_fault(fault, "before_commit")


def _convert_legacy_items(conn, fault):
    """Copy legacy rows into a replacement table and swap it into place."""
    rows = conn.execute(
        f"SELECT id, value FROM {ITEMS_TABLE} ORDER BY id"
    ).fetchall()
    conn.execute(CREATE_ITEMS_SQL.format(name=REPLACEMENT_TABLE))
    conn.executemany(
        f"INSERT INTO {REPLACEMENT_TABLE}(id, value, normalized) VALUES (?, ?, ?)",
        ((item_id, value, normalize(value)) for item_id, value in rows),
    )
    _call_fault(fault, "after_copy")
    conn.execute(f"DROP TABLE {ITEMS_TABLE}")
    conn.execute(f"ALTER TABLE {REPLACEMENT_TABLE} RENAME TO {ITEMS_TABLE}")


def _call_fault(fault, point):
    if fault is not None:
        fault(point)


def _read_version(conn):
    return conn.execute("PRAGMA user_version").fetchone()[0]


def _table_exists(conn, name):
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)
    ).fetchone()
    return row is not None


def _connect_read_only(path):
    # mode=ro makes a missing file an error instead of silently creating it.
    uri = Path(path).resolve().as_uri() + "?mode=ro"
    return sqlite3.connect(uri, uri=True, isolation_level=None)
