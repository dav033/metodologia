"""SQLite storage for items, with a versioned schema.

Version 0 is the legacy layout ``items(id, value)``. Version 1 adds
``normalized``, which holds ``value.strip().lower()``.
"""

import os
import pathlib
import sqlite3

LEGACY_VERSION = 0
CURRENT_VERSION = 1
TABLE = "items"
REPLACEMENT_TABLE = "items_new"
LEGACY_COLUMNS = ["id", "value"]


def migrate(path, fault=None):
    """Create or upgrade the database at ``path`` to schema version 1.

    An empty database gets the new schema. A legacy version-0 database is
    converted in place. Any exception rolls the whole migration back.
    ``fault`` is an optional hook called with 'after_copy' and
    'before_commit' during a legacy conversion.
    """
    conn = sqlite3.connect(path)
    try:
        version = _user_version(conn)
        if version == CURRENT_VERSION:
            return
        _check_upgradable(version)
        _in_transaction(conn, _upgrade, fault)
    finally:
        conn.close()


def read_items(path):
    """Return ``(id, normalized)`` pairs ordered by id from a migrated database."""
    conn = _connect_read_only(path)
    try:
        version = _user_version(conn)
        if version != CURRENT_VERSION:
            raise ValueError(
                f"database is at schema version {version}, expected "
                f"{CURRENT_VERSION}; run migrate() first"
            )
        return conn.execute(f"SELECT id, normalized FROM {TABLE} ORDER BY id").fetchall()
    finally:
        conn.close()


def _upgrade(conn, fault):
    # Re-check under the write lock in case another connection migrated first.
    version = _user_version(conn)
    if version == CURRENT_VERSION:
        return
    _check_upgradable(version)
    if _table_exists(conn, TABLE):
        _convert_legacy(conn, fault)
    else:
        _create_schema(conn)


def _convert_legacy(conn, fault):
    _check_legacy_columns(conn)
    _check_text_values(conn)
    conn.create_function("normalize_value", 1, _normalize, deterministic=True)
    conn.execute(_create_table_sql(REPLACEMENT_TABLE))
    conn.execute(
        f"INSERT INTO {REPLACEMENT_TABLE} (id, value, normalized) "
        f"SELECT id, value, normalize_value(value) FROM {TABLE} ORDER BY id"
    )
    _call_fault(fault, "after_copy")
    conn.execute(f"DROP TABLE {TABLE}")
    conn.execute(f"ALTER TABLE {REPLACEMENT_TABLE} RENAME TO {TABLE}")
    conn.execute(f"PRAGMA user_version = {CURRENT_VERSION}")
    _call_fault(fault, "before_commit")


def _create_schema(conn):
    conn.execute(_create_table_sql(TABLE))
    conn.execute(f"PRAGMA user_version = {CURRENT_VERSION}")


def _create_table_sql(name):
    return (
        f"CREATE TABLE {name} ("
        "id INTEGER PRIMARY KEY, value TEXT NOT NULL, normalized TEXT NOT NULL)"
    )


def _normalize(value):
    return value.strip().lower()


def _check_upgradable(version):
    if version != LEGACY_VERSION:
        raise ValueError(
            f"cannot migrate database at schema version {version}; "
            f"supported source version is {LEGACY_VERSION}"
        )


def _check_legacy_columns(conn):
    names = [row[1] for row in conn.execute(f"PRAGMA table_info({TABLE})")]
    if names != LEGACY_COLUMNS:
        raise ValueError(f"unexpected legacy columns {names}; expected {LEGACY_COLUMNS}")


def _check_text_values(conn):
    count = conn.execute(
        f"SELECT COUNT(*) FROM {TABLE} WHERE typeof(value) <> 'text'"
    ).fetchone()[0]
    if count:
        raise ValueError(f"{count} legacy row(s) have a non-text value")


def _in_transaction(conn, work, *args):
    conn.execute("BEGIN IMMEDIATE")
    try:
        work(conn, *args)
        conn.execute("COMMIT")
    except BaseException:
        conn.rollback()
        raise


def _call_fault(fault, checkpoint):
    if fault is not None:
        fault(checkpoint)


def _user_version(conn):
    return conn.execute("PRAGMA user_version").fetchone()[0]


def _table_exists(conn, name):
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)
    ).fetchone()
    return row is not None


def _connect_read_only(path):
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    uri = pathlib.Path(os.path.abspath(path)).as_uri() + "?mode=ro"
    return sqlite3.connect(uri, uri=True)
