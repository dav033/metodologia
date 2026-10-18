"""A durable SQLite work queue with fenced leases and an outbox."""

from contextlib import contextmanager
import sqlite3


@contextmanager
def _connection(path):
    """Commit successful operations, roll back failures, and always close."""
    connection = sqlite3.connect(path, timeout=30)
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def init(path):
    with _connection(path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            "CREATE TABLE IF NOT EXISTS jobs("
            "id TEXT PRIMARY KEY,payload TEXT NOT NULL,"
            "state TEXT NOT NULL DEFAULT 'pending',"
            "token INTEGER NOT NULL DEFAULT 0,lease_until INTEGER,"
            "attempts INTEGER NOT NULL DEFAULT 0,depends_on TEXT,result TEXT)"
        )
        connection.execute(
            "CREATE TABLE IF NOT EXISTS outbox("
            "id TEXT PRIMARY KEY,body TEXT NOT NULL,"
            "delivered INTEGER NOT NULL DEFAULT 0)"
        )
        connection.execute(
            "CREATE TABLE IF NOT EXISTS inbox("
            "id TEXT PRIMARY KEY,body TEXT NOT NULL)"
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
        # Serialize selection and update across independent clients.
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            "SELECT id,payload,token FROM jobs AS job "
            "WHERE (state='pending' OR (state='running' AND lease_until<=?)) "
            "AND (depends_on IS NULL OR EXISTS ("
            "SELECT 1 FROM jobs AS parent "
            "WHERE parent.id=job.depends_on AND parent.state='done')) "
            "ORDER BY id LIMIT 1",
            (now,),
        ).fetchone()
        if row is None:
            return None
        id, payload, token = row
        token += 1
        connection.execute(
            "UPDATE jobs SET state='running',token=?,lease_until=?,"
            "attempts=attempts+1 WHERE id=?",
            (token, now + ttl, id),
        )
        return id, payload, token


def complete(path, id, token, result, now, fault=None):
    with _connection(path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        updated = connection.execute(
            "UPDATE jobs SET state='done',result=?,lease_until=NULL "
            "WHERE id=? AND state='running' AND token=? AND lease_until>?",
            (result, id, token, now),
        )
        if updated.rowcount == 0:
            return False
        if fault is not None:
            fault('after_result')
        connection.execute(
            "INSERT INTO outbox(id,body) VALUES(?,?)", (id, result)
        )
        if fault is not None:
            fault('before_commit')
        return True


def inspect(path, id):
    with _connection(path) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            "SELECT * FROM jobs WHERE id=?", (id,)
        ).fetchone()
        return dict(row) if row is not None else None


def retry(path, id, token, now):
    with _connection(path) as connection:
        updated = connection.execute(
            "UPDATE jobs SET state='pending',lease_until=NULL "
            "WHERE id=? AND state='running' AND token=? AND lease_until>?",
            (id, token, now),
        )
        return updated.rowcount == 1


def publish(path, deliver):
    # Materialize and close before callbacks: a callback can write to this DB.
    with _connection(path) as connection:
        rows = connection.execute(
            "SELECT id,body FROM outbox WHERE delivered=0 ORDER BY id"
        ).fetchall()
    delivered = 0
    for id, body in rows:
        deliver(id, body)
        with _connection(path) as connection:
            connection.execute(
                "UPDATE outbox SET delivered=1 WHERE id=?", (id,)
            )
        delivered += 1
    return delivered


def consume(path, id, body):
    with _connection(path) as connection:
        inserted = connection.execute(
            "INSERT INTO inbox(id,body) VALUES(?,?) "
            "ON CONFLICT(id) DO NOTHING",
            (id, body),
        )
        return inserted.rowcount == 1
