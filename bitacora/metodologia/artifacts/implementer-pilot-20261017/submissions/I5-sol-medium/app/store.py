"""Durable SQLite jobs with expiring leases and persistent fencing tokens."""

from contextlib import closing, contextmanager
import sqlite3


@contextmanager
def _connection(path):
    """Commit successful operations, roll back failures, and always close."""
    with closing(sqlite3.connect(path, timeout=30)) as connection:
        with connection:
            yield connection


def init(path):
    with _connection(path) as connection:
        connection.execute(
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


def enqueue(path, id, payload, depends_on=None):
    with _connection(path) as connection:
        connection.execute(
            "INSERT INTO jobs(id,payload,depends_on) VALUES(?,?,?) "
            "ON CONFLICT(id) DO NOTHING",
            (id, payload, depends_on),
        )


def claim(path, now, ttl):
    if ttl <= 0:
        raise ValueError("ttl must be positive")

    with _connection(path) as connection:
        # Reserve the writer before selecting so independent clients cannot
        # select the same eligible lease before either has updated it.
        connection.execute("BEGIN IMMEDIATE")
        job = connection.execute(
            "SELECT id,payload,token FROM jobs "
            "WHERE state='pending' "
            "OR (state='running' AND lease_until<=?) "
            "ORDER BY id LIMIT 1",
            (now,),
        ).fetchone()
        if job is None:
            return None
        id, payload, token = job
        connection.execute(
            "UPDATE jobs SET state='running',token=token+1,"
            "lease_until=?,attempts=attempts+1 WHERE id=?",
            (now + ttl, id),
        )
        return id, payload, token + 1


def complete(path, id, token, result, now, fault=None):
    with _connection(path) as connection:
        cursor = connection.execute(
            "UPDATE jobs SET state='done',result=?,lease_until=NULL "
            "WHERE id=? AND state='running' AND token=? AND lease_until>?",
            (result, id, token, now),
        )
        return cursor.rowcount == 1


def inspect(path, id):
    with _connection(path) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            "SELECT * FROM jobs WHERE id=?", (id,)
        ).fetchone()
        return dict(row) if row is not None else None


def retry(path, id, token, now):
    return False


def publish(path, deliver):
    return 0


def consume(path, id, body):
    return False
