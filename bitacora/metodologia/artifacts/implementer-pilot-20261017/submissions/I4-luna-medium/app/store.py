"""SQLite storage and schema migration for items."""

import sqlite3


_SCHEMA = (
    "CREATE TABLE items ("
    "id INTEGER PRIMARY KEY, "
    "value TEXT NOT NULL, "
    "normalized TEXT NOT NULL)"
)


def _call_fault(fault, point):
    if fault is not None:
        fault(point)


def migrate(path: str, fault=None) -> None:
    """Create or upgrade the items table to schema version 1 atomically."""
    connection = sqlite3.connect(path, isolation_level=None)
    try:
        connection.execute("BEGIN")
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        if version > 1:
            raise ValueError("database schema version is newer than supported")
        if version == 1:
            connection.execute("COMMIT")
            return
        if version < 0:
            raise ValueError("invalid database schema version")

        table = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'items'"
        ).fetchone()
        if table is None:
            connection.execute(_SCHEMA)
        else:
            # Use a replacement table so the original values and ids are retained
            # while normalized values are computed with Python's string rules.
            connection.execute("DROP TABLE IF EXISTS items_new")
            connection.execute(
                "CREATE TABLE items_new ("
                "id INTEGER PRIMARY KEY, value TEXT NOT NULL, normalized TEXT NOT NULL)"
            )
            rows = connection.execute("SELECT id, value FROM items ORDER BY id").fetchall()
            connection.executemany(
                "INSERT INTO items_new (id, value, normalized) VALUES (?, ?, ?)",
                ((item_id, value, value.strip().lower()) for item_id, value in rows),
            )
            _call_fault(fault, "after_copy")
            connection.execute("DROP TABLE items")
            connection.execute("ALTER TABLE items_new RENAME TO items")

        connection.execute("PRAGMA user_version = 1")
        _call_fault(fault, "before_commit")
        connection.execute("COMMIT")
    except BaseException:
        if connection.in_transaction:
            connection.execute("ROLLBACK")
        raise
    finally:
        connection.close()


def read_items(path: str) -> list[tuple[int, str]]:
    """Read normalized values from a version 1 database in id order."""
    connection = sqlite3.connect(path)
    try:
        return connection.execute(
            "SELECT id, normalized FROM items ORDER BY id"
        ).fetchall()
    finally:
        connection.close()
