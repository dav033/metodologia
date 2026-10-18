"""SQLite item store with a versioned schema migration (user_version 0 -> 1)."""

import os
import pathlib
import sqlite3

LEGACY_VERSION = 0
CURRENT_VERSION = 1
ITEMS_TABLE = "items"
REPLACEMENT_TABLE = "items_v1"

ITEMS_SCHEMA = """
CREATE TABLE {table}(
    id INTEGER PRIMARY KEY,
    value TEXT NOT NULL,
    normalized TEXT NOT NULL
)
"""


def migrate(path, fault=None):
    """Bring the database at ``path`` up to CURRENT_VERSION in one transaction.

    ``fault`` is an optional hook called with 'after_copy' and 'before_commit'
    during a migration. Any exception rolls the whole migration back.
    """
    conn = _connect(path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        _migrate_in_transaction(conn, fault)
        conn.execute("COMMIT")
    except BaseException:
        _rollback(conn)
        raise
    finally:
        conn.close()


def read_items(path):
    """Return ``(id, normalized)`` pairs ordered by id from a migrated database."""
    conn = _connect_read_only(path)
    try:
        version = _user_version(conn)
        if version != CURRENT_VERSION:
            raise ValueError(
                f"database must be at version {CURRENT_VERSION} to read; found {version}"
            )
        return conn.execute(
            f"SELECT id, normalized FROM {ITEMS_TABLE} ORDER BY id"
        ).fetchall()
    finally:
        conn.close()


def _migrate_in_transaction(conn, fault):
    version = _user_version(conn)
    if version > CURRENT_VERSION:
        raise ValueError(
            f"unsupported database version {version}; maximum supported is {CURRENT_VERSION}"
        )
    if version == CURRENT_VERSION:
        return

    if version == LEGACY_VERSION and _table_exists(conn, ITEMS_TABLE):
        _convert_legacy_items(conn, fault)
    else:
        _create_items_table(conn, ITEMS_TABLE)

    _set_version(conn, CURRENT_VERSION)
    _call_fault(fault, "before_commit")


def _convert_legacy_items(conn, fault):
    rows = conn.execute(f"SELECT id, value FROM {ITEMS_TABLE} ORDER BY id").fetchall()

    _create_items_table(conn, REPLACEMENT_TABLE)
    conn.executemany(
        f"INSERT INTO {REPLACEMENT_TABLE}(id, value, normalized) VALUES (?, ?, ?)",
        ((item_id, value, _normalize(item_id, value)) for item_id, value in rows),
    )
    _call_fault(fault, "after_copy")

    conn.execute(f"DROP TABLE {ITEMS_TABLE}")
    conn.execute(f"ALTER TABLE {REPLACEMENT_TABLE} RENAME TO {ITEMS_TABLE}")


def _create_items_table(conn, table):
    conn.execute(f"DROP TABLE IF EXISTS {table}")
    conn.execute(ITEMS_SCHEMA.format(table=table))


def _normalize(item_id, value):
    if not isinstance(value, str):
        raise ValueError(f"item {item_id} has non-text value of type {type(value).__name__}")
    return value.strip().lower()


def _user_version(conn):
    return conn.execute("PRAGMA user_version").fetchone()[0]


def _set_version(conn, version):
    # PRAGMA does not accept bound parameters; version is an internal integer constant.
    conn.execute(f"PRAGMA user_version = {int(version)}")


def _table_exists(conn, table):
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)
    ).fetchone()
    return row is not None


def _call_fault(fault, point):
    if fault is not None:
        fault(point)


def _connect(path):
    return sqlite3.connect(path, isolation_level=None)


def _connect_read_only(path):
    uri = pathlib.Path(os.path.abspath(path)).as_uri() + "?mode=ro"
    return sqlite3.connect(uri, uri=True, isolation_level=None)


def _rollback(conn):
    if conn.in_transaction:
        conn.execute("ROLLBACK")
