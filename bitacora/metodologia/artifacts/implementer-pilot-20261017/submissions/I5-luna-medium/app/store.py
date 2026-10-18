"""SQLite-backed job storage and lease operations."""

import sqlite3
from contextlib import contextmanager


_SCHEMA = """CREATE TABLE IF NOT EXISTS jobs(
    id TEXT PRIMARY KEY,
    payload TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'pending',
    token INTEGER NOT NULL DEFAULT 0,
    lease_until INTEGER,
    attempts INTEGER NOT NULL DEFAULT 0,
    depends_on TEXT,
    result TEXT
)"""


@contextmanager
def _connection(path):
    """Open one connection per operation and always close it."""
    connection = sqlite3.connect(path, timeout=30)
    try:
        yield connection
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
    finally:
        connection.close()


def init(path):
    with _connection(path) as connection:
        connection.execute(_SCHEMA)


def enqueue(path, id, payload, depends_on=None):
    with _connection(path) as connection:
        connection.execute(
            "INSERT OR IGNORE INTO jobs(id, payload, depends_on) VALUES (?, ?, ?)",
            (id, payload, depends_on),
        )


def claim(path, now, ttl):
    if ttl <= 0:
        raise ValueError("ttl must be positive")

    with _connection(path) as connection:
        # Serialize selection and update across independent SQLite connections.
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            "SELECT id, payload, token FROM jobs "
            "WHERE state = 'pending' OR (state = 'running' AND lease_until <= ?) "
            "ORDER BY id LIMIT 1",
            (now,),
        ).fetchone()
        if row is None:
            return None

        job_id, payload, old_token = row
        token = old_token + 1
        connection.execute(
            "UPDATE jobs SET state = 'running', token = ?, lease_until = ?, "
            "attempts = attempts + 1 WHERE id = ?",
            (token, now + ttl, job_id),
        )
        return job_id, payload, token


def complete(path, id, token, result, now, fault=None):
    with _connection(path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        cursor = connection.execute(
            "UPDATE jobs SET state = 'done', result = ?, lease_until = NULL "
            "WHERE id = ? AND state = 'running' AND token = ? AND lease_until > ?",
            (result, id, token, now),
        )
        succeeded = cursor.rowcount == 1
        if succeeded and fault is not None:
            # A supplied fault hook can exercise rollback of the completion.
            fault() if callable(fault) else None
        return succeeded


def inspect(path, id):
    with _connection(path) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute("SELECT * FROM jobs WHERE id = ?", (id,)).fetchone()
        return dict(row) if row is not None else None


def retry(path, id, token, now):
    return False


def publish(path, deliver):
    return 0


def consume(path, id, body):
    return False
