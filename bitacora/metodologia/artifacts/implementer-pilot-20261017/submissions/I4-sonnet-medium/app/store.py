import sqlite3
from contextlib import closing

SCHEMA_VERSION = 1

_CREATE_SQL = (
    "CREATE TABLE {name}(id INTEGER PRIMARY KEY, value TEXT NOT NULL, "
    "normalized TEXT NOT NULL)"
)


def _normalize(value):
    return str(value).strip().lower()


def _has_items(conn):
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='items'"
    ).fetchone()
    return row is not None


def _convert_legacy(conn, fault):
    conn.execute("DROP TABLE IF EXISTS items_new")
    conn.execute(_CREATE_SQL.format(name="items_new"))
    rows = conn.execute("SELECT id, value FROM items ORDER BY id").fetchall()
    conn.executemany(
        "INSERT INTO items_new(id, value, normalized) VALUES (?, ?, ?)",
        [(i, v, _normalize(v)) for i, v in rows],
    )
    if fault:
        fault("after_copy")
    conn.execute("DROP TABLE items")
    conn.execute("ALTER TABLE items_new RENAME TO items")


def migrate(path, fault=None):
    """Migrate the DB at path to user_version 1 in a single transaction."""
    conn = sqlite3.connect(path, isolation_level=None)
    try:
        conn.execute("BEGIN IMMEDIATE")
        try:
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            if version > SCHEMA_VERSION:
                raise ValueError(f"unsupported schema version: {version}")
            if version == SCHEMA_VERSION:
                conn.execute("ROLLBACK")
                return
            if _has_items(conn):
                _convert_legacy(conn, fault)
            else:
                conn.execute(_CREATE_SQL.format(name="items"))
            conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
            if fault:
                fault("before_commit")
            conn.execute("COMMIT")
        except BaseException:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise
    finally:
        conn.close()


def read_items(path):
    """Return [(id, normalized)] ordered by id from a migrated DB."""
    uri = "file:" + path.replace("?", "%3f").replace("#", "%23") + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as conn:
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        if version != SCHEMA_VERSION:
            raise ValueError(f"database not migrated (version {version})")
        return [
            (i, n)
            for i, n in conn.execute(
                "SELECT id, normalized FROM items ORDER BY id"
            )
        ]
