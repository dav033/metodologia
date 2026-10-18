"""SQLite-backed job storage.

Each public operation owns its connection so callers can safely use the
functions from independent threads or processes.
"""

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
    connection = sqlite3.connect(path, timeout=30)
    try:
        # Explicit transactions are used where more than one statement must
        # be serialized. A context manager commits successful work and rolls
        # back failures; finally always closes the handle.
        with connection:
            yield connection
    finally:
        connection.close()


def init(path):
    """Create the jobs table if it does not already exist."""
    with _connection(path) as connection:
        connection.execute(_SCHEMA)


def enqueue(path, id, payload, depends_on=None):
    """Insert a job once, leaving the original payload on duplicate ids."""
    with _connection(path) as connection:
        connection.execute(
            "INSERT OR IGNORE INTO jobs(id, payload, depends_on) VALUES (?, ?, ?)",
            (id, payload, depends_on),
        )


def claim(path, now, ttl):
    """Lease the lexicographically smallest pending or expired job."""
    if ttl <= 0:
        raise ValueError("ttl must be greater than zero")

    with _connection(path) as connection:
        # BEGIN IMMEDIATE ensures another connection cannot select the same
        # eligible row before this transaction updates it.
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            """SELECT id, payload, token
               FROM jobs
               WHERE state = 'pending'
                  OR (state = 'running' AND lease_until <= ?)
               ORDER BY id
               LIMIT 1""",
            (now,),
        ).fetchone()
        if row is None:
            return None

        job_id, payload, old_token = row
        token = old_token + 1
        connection.execute(
            """UPDATE jobs
               SET state = 'running', token = ?, lease_until = ?,
                   attempts = attempts + 1
               WHERE id = ?""",
            (token, now + ttl, job_id),
        )
        return job_id, payload, token


def complete(path, id, token, result, now, fault=None):
    """Complete a job only while the supplied lease token remains valid."""
    with _connection(path) as connection:
        cursor = connection.execute(
            """UPDATE jobs
               SET state = 'done', result = ?, lease_until = NULL
               WHERE id = ? AND state = 'running' AND token = ?
                 AND lease_until > ?""",
            (result, id, token, now),
        )
        return cursor.rowcount == 1


def inspect(path, id):
    """Return all stored columns for a job, or None when it is absent."""
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
