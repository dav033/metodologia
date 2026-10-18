"""SQLite storage and schema migration helpers."""

import sqlite3


def _table_exists(connection, name):
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (name,),
    ).fetchone()
    return row is not None


def migrate(path: str, fault=None) -> None:
    """Migrate a version 0 items database to schema version 1.

    All schema and data changes are made inside one SQLite transaction, so an
    exception (including one raised by ``fault``) leaves the database intact.
    """
    connection = sqlite3.connect(path, isolation_level=None)
    try:
        connection.execute("BEGIN IMMEDIATE")
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        if version > 1:
            raise ValueError("database schema version is newer than supported")
        if version == 1:
            connection.execute("COMMIT")
            return

        if _table_exists(connection, "items"):
            # Populate a separate table first. Keeping the source table in place
            # until the after_copy hook also makes injected failures reversible.
            connection.execute(
                "CREATE TABLE items_new ("
                "id INTEGER PRIMARY KEY, "
                "value TEXT NOT NULL, "
                "normalized TEXT NOT NULL)"
            )
            rows = connection.execute("SELECT id, value FROM items").fetchall()
            connection.executemany(
                "INSERT INTO items_new (id, value, normalized) VALUES (?, ?, ?)",
                [(item_id, value, value.strip().lower()) for item_id, value in rows],
            )
            if fault is not None:
                fault("after_copy")
            connection.execute("DROP TABLE items")
            connection.execute("ALTER TABLE items_new RENAME TO items")
        else:
            connection.execute(
                "CREATE TABLE items ("
                "id INTEGER PRIMARY KEY, "
                "value TEXT NOT NULL, "
                "normalized TEXT NOT NULL)"
            )

        connection.execute("PRAGMA user_version = 1")
        if fault is not None:
            fault("before_commit")
        connection.execute("COMMIT")
    except BaseException:
        if connection.in_transaction:
            connection.execute("ROLLBACK")
        raise
    finally:
        connection.close()


def read_items(path: str) -> list[tuple[int, str]]:
    """Return normalized item values from a migrated database, by id."""
    connection = sqlite3.connect(path)
    try:
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        if version != 1:
            raise ValueError("database has not been migrated to schema version 1")
        rows = connection.execute(
            "SELECT id, normalized FROM items ORDER BY id"
        ).fetchall()
        return [(item_id, normalized) for item_id, normalized in rows]
    finally:
        connection.close()
