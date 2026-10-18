"""SQLite connection helpers for the job store."""
import sqlite3
from contextlib import contextmanager

BUSY_TIMEOUT_SECONDS = 30.0

SCHEMA = (
    "CREATE TABLE IF NOT EXISTS jobs("
    "id TEXT PRIMARY KEY,"
    "payload TEXT NOT NULL,"
    "state TEXT NOT NULL DEFAULT 'pending',"
    "token INTEGER NOT NULL DEFAULT 0,"
    "lease_until INTEGER,"
    "attempts INTEGER NOT NULL DEFAULT 0,"
    "depends_on TEXT,"
    "result TEXT)"
)


@contextmanager
def connect(path):
    """Yield a connection with explicit transaction control; always closes it."""
    conn = sqlite3.connect(path, timeout=BUSY_TIMEOUT_SECONDS, isolation_level=None)
    try:
        conn.execute("PRAGMA synchronous=FULL")
        yield conn
    finally:
        conn.close()


@contextmanager
def write_transaction(path):
    """Run the block inside BEGIN IMMEDIATE; COMMIT on success, ROLLBACK on error."""
    with connect(path) as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            yield conn
        except BaseException:
            conn.execute("ROLLBACK")
            raise
        conn.execute("COMMIT")


def create_schema(path):
    """Enable WAL mode and create the jobs table if it is missing."""
    with connect(path) as conn:
        # journal_mode cannot change inside a transaction, so it runs first.
        conn.execute("PRAGMA journal_mode=WAL").fetchone()
    with write_transaction(path) as conn:
        conn.execute(SCHEMA)
