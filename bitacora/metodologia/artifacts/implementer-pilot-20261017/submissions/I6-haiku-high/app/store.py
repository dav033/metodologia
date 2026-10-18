"""Durable SQLite-backed job queue with leases, dependencies, retry and an outbox/inbox.

Every public function opens its own connection and closes it before returning.
Writes run in ``BEGIN IMMEDIATE`` transactions so concurrent clients are serialized
by SQLite, and each job has at most one current lease (fenced by its token).
"""

import os
import sqlite3
import urllib.parse
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
    "result TEXT)",
    "CREATE TABLE IF NOT EXISTS outbox("
    "id TEXT PRIMARY KEY,"
    "body TEXT NOT NULL,"
    "delivered INTEGER NOT NULL DEFAULT 0)",
    "CREATE TABLE IF NOT EXISTS inbox("
    "id TEXT PRIMARY KEY,"
    "body TEXT NOT NULL)",
)

# A job is eligible when it is pending, or running with an expired lease, and its
# dependency (if any) exists and is done. Ordering by id gives the smallest eligible id.
ELIGIBLE_SQL = (
    "SELECT id, payload FROM jobs AS j "
    "WHERE (j.state = 'pending' OR (j.state = 'running' AND j.lease_until <= ?)) "
    "AND (j.depends_on IS NULL OR EXISTS ("
    "SELECT 1 FROM jobs AS p WHERE p.id = j.depends_on AND p.state = 'done')) "
    "ORDER BY j.id LIMIT 1"
)


def _require_str(name, value):
    if not isinstance(value, str):
        raise TypeError(f"{name} must be str, not {type(value).__name__}")


def _require_int(name, value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be int, not {type(value).__name__}")


def _uri(path, create):
    # Opening with mode=rw prevents non-init calls from silently creating an empty database.
    mode = "rwc" if create else "rw"
    return f"file:{urllib.parse.quote(os.path.abspath(path))}?mode={mode}"


@contextmanager
def _connection(path, create=False):
    conn = sqlite3.connect(
        _uri(path, create),
        uri=True,
        timeout=BUSY_TIMEOUT_SECONDS,
        isolation_level=None,  # autocommit; transactions are explicit
    )
    try:
        conn.execute("PRAGMA synchronous=FULL")
        yield conn
    finally:
        conn.close()


@contextmanager
def _transaction(path, create=False):
    with _connection(path, create) as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            yield conn
        except BaseException:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise
        conn.execute("COMMIT")


def _call_fault(fault, stage):
    if fault is not None:
        fault(stage)


def init(path):
    _require_str("path", path)
    with _connection(path, create=True) as conn:
        conn.execute("PRAGMA journal_mode=WAL")  # persistent; cannot be set inside a transaction
    with _transaction(path, create=True) as conn:
        for statement in SCHEMA:
            conn.execute(statement)


def enqueue(path, id, payload, depends_on=None):
    _require_str("id", id)
    _require_str("payload", payload)
    if depends_on is not None:
        _require_str("depends_on", depends_on)
    with _transaction(path) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO jobs(id, payload, depends_on) VALUES(?, ?, ?)",
            (id, payload, depends_on),
        )


def claim(path, now, ttl):
    _require_int("now", now)
    _require_int("ttl", ttl)
    if ttl <= 0:
        raise ValueError("ttl must be positive")
    with _transaction(path) as conn:
        row = conn.execute(ELIGIBLE_SQL, (now,)).fetchone()
        if row is None:
            return None
        job_id, payload = row
        conn.execute(
            "UPDATE jobs SET state = 'running', lease_until = ?, "
            "attempts = attempts + 1, token = token + 1 WHERE id = ?",
            (now + ttl, job_id),
        )
        (token,) = conn.execute("SELECT token FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return job_id, payload, token


def complete(path, id, token, result, now, fault=None):
    """Mark a currently leased job done and enqueue its outbox event in one transaction.

    ``fault`` is an optional hook called with 'after_result' and 'before_commit'. Exceptions
    from the hook roll the transaction back and propagate. Stale completions return False
    without invoking hooks or writing anything.
    """
    _require_str("id", id)
    _require_int("token", token)
    _require_str("result", result)
    _require_int("now", now)
    with _transaction(path) as conn:
        lease = conn.execute(
            "SELECT 1 FROM jobs WHERE id = ? AND state = 'running' AND token = ? AND lease_until > ?",
            (id, token, now),
        ).fetchone()
        if lease is None:
            return False
        conn.execute(
            "UPDATE jobs SET state = 'done', result = ?, lease_until = NULL WHERE id = ?",
            (result, id),
        )
        _call_fault(fault, "after_result")
        # The outbox id is the job id, so each job produces at most one event; body is the result.
        conn.execute("INSERT INTO outbox(id, body) VALUES(?, ?)", (id, result))
        _call_fault(fault, "before_commit")
    return True


def inspect(path, id):
    _require_str("id", id)
    with _connection(path) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (id,)).fetchone()
        return dict(row) if row is not None else None


def retry(path, id, token, now):
    """Release a currently valid lease back to pending. Returns False if the lease is not valid."""
    _require_str("id", id)
    _require_int("token", token)
    _require_int("now", now)
    with _transaction(path) as conn:
        cursor = conn.execute(
            "UPDATE jobs SET state = 'pending', lease_until = NULL "
            "WHERE id = ? AND state = 'running' AND token = ? AND lease_until > ?",
            (id, token, now),
        )
        return cursor.rowcount == 1


def _next_undelivered(path):
    with _connection(path) as conn:
        return conn.execute(
            "SELECT id, body FROM outbox WHERE delivered = 0 ORDER BY id LIMIT 1"
        ).fetchone()


def _mark_delivered(path, event_id):
    with _transaction(path) as conn:
        conn.execute("UPDATE outbox SET delivered = 1 WHERE id = ?", (event_id,))


def publish(path, deliver):
    """Deliver undelivered outbox rows in id order, marking each after its callback succeeds.

    No transaction is held while ``deliver`` runs, so it may call ``consume`` on the same
    database. Delivery is at-least-once: a crash after a callback but before the mark replays it.
    """
    delivered = 0
    while True:
        event = _next_undelivered(path)
        if event is None:
            return delivered
        event_id, body = event
        deliver(event_id, body)
        _mark_delivered(path, event_id)
        delivered += 1


def consume(path, id, body):
    """Record an inbox entry once. Returns True on first delivery, False for duplicates."""
    _require_str("id", id)
    _require_str("body", body)
    with _transaction(path) as conn:
        cursor = conn.execute("INSERT OR IGNORE INTO inbox(id, body) VALUES(?, ?)", (id, body))
        return cursor.rowcount == 1
