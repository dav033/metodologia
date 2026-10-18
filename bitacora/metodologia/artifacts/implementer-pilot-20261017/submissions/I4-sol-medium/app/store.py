"""Transactional migration and read access for the items database."""

import sqlite3
from pathlib import Path


def _create_items(connection, table):
    # Table names are internal constants, never supplied by callers.
    connection.execute(
        f"CREATE TABLE {table} ("
        "id INTEGER PRIMARY KEY, value TEXT NOT NULL, normalized TEXT NOT NULL)"
    )


def migrate(path: str, fault=None) -> None:
    """Create or upgrade the schema atomically, preserving legacy values."""
    connection = sqlite3.connect(path, isolation_level=None)
    try:
        connection.execute("BEGIN IMMEDIATE")
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        if version > 1:
            raise ValueError(f"Unsupported database version: {version}")
        if version == 1:
            connection.commit()
            return

        has_items = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'items'"
        ).fetchone()
        if has_items:
            _create_items(connection, "items_migration_v1")
            rows = connection.execute("SELECT id, value FROM items")
            try:
                connection.executemany(
                    "INSERT INTO items_migration_v1 (id, value, normalized) "
                    "VALUES (?, ?, ?)",
                    ((item_id, value, value.strip().lower()) for item_id, value in rows),
                )
            finally:
                rows.close()
            if fault is not None:
                fault("after_copy")
            connection.execute("DROP TABLE items")
            connection.execute("ALTER TABLE items_migration_v1 RENAME TO items")
        else:
            _create_items(connection, "items")

        connection.execute("PRAGMA user_version = 1")
        if fault is not None:
            fault("before_commit")
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
    finally:
        connection.close()


def read_items(path: str) -> list[tuple[int, str]]:
    """Read normalized items from a migrated database without creating a file."""
    uri = Path(path).absolute().as_uri() + "?mode=ro"
    connection = sqlite3.connect(uri, uri=True, isolation_level=None)
    try:
        connection.execute("BEGIN")
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        if version != 1:
            raise ValueError(f"Database must be migrated before reading (version {version})")
        return connection.execute(
            "SELECT id, normalized FROM items ORDER BY id"
        ).fetchall()
    finally:
        connection.close()
