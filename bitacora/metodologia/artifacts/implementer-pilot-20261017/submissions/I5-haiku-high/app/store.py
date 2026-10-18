"""Durable SQLite job queue with fenced lease tokens (standard library only).

Each public operation opens its own connection and closes it before returning.
Writes run in a BEGIN IMMEDIATE transaction, which takes the write lock up
front so concurrent claimants are serialized and a job never has two live
leases. Commits are synchronous, so a returned call is durable.
"""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

SCHEMA = ("CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,payload TEXT NOT NULL,"
          "state TEXT NOT NULL DEFAULT 'pending',token INTEGER NOT NULL DEFAULT 0,"
          "lease_until INTEGER,attempts INTEGER NOT NULL DEFAULT 0,depends_on TEXT,result TEXT)")
BUSY_TIMEOUT_SECONDS = 30
INT64_MIN = -(2 ** 63)
INT64_MAX = 2 ** 63 - 1


def _check_str(name, value):
    if not isinstance(value, str):
        raise TypeError(f'{name} must be str')


def _check_int(name, value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f'{name} must be int')
    if not INT64_MIN <= value <= INT64_MAX:
        raise ValueError(f'{name} is outside the 64-bit integer range')


@contextmanager
def _connect(path, create=False):
    """Open a dedicated connection to an existing database (or create it)."""
    _check_str('path', path)
    # mode=rw makes operations on a missing database fail instead of silently creating it.
    mode = 'rwc' if create else 'rw'
    uri = Path(os.path.abspath(path)).as_uri() + '?mode=' + mode
    conn = sqlite3.connect(uri, uri=True, timeout=BUSY_TIMEOUT_SECONDS, isolation_level=None)
    try:
        conn.execute('PRAGMA synchronous=FULL')
        yield conn
    finally:
        conn.close()


@contextmanager
def _write_transaction(conn):
    """Run the body in an immediate transaction; roll back on any error."""
    conn.execute('BEGIN IMMEDIATE')
    try:
        yield conn
        conn.execute('COMMIT')
    except BaseException:
        if conn.in_transaction:
            conn.execute('ROLLBACK')
        raise


def init(path):
    with _connect(path, create=True) as conn:
        conn.execute(SCHEMA)


def enqueue(path, id, payload, depends_on=None):
    _check_str('id', id)
    _check_str('payload', payload)
    if depends_on is not None:
        _check_str('depends_on', depends_on)
    with _connect(path) as conn, _write_transaction(conn):
        # OR IGNORE keeps the first payload for duplicate ids.
        conn.execute('INSERT OR IGNORE INTO jobs(id,payload,depends_on) VALUES(?,?,?)',
                     (id, payload, depends_on))


def claim(path, now, ttl):
    _check_int('now', now)
    _check_int('ttl', ttl)
    if ttl <= 0:
        raise ValueError('ttl must be positive')
    lease_until = now + ttl
    _check_int('lease_until', lease_until)
    with _connect(path) as conn, _write_transaction(conn):
        row = conn.execute(
            "SELECT id,payload,token FROM jobs "
            "WHERE state='pending' OR (state='running' AND lease_until<=?) "
            "ORDER BY id LIMIT 1",
            (now,),
        ).fetchone()
        if row is None:
            return None
        job_id, payload, token = row
        new_token = token + 1
        conn.execute(
            "UPDATE jobs SET state='running',token=?,lease_until=?,attempts=attempts+1 WHERE id=?",
            (new_token, lease_until, job_id),
        )
        return (job_id, payload, new_token)


def complete(path, id, token, result, now, fault=None):
    """Mark a job done. Returns False, changing nothing, unless the caller holds
    the current, unexpired lease.

    `fault`, if given, is a zero-argument callable run inside the transaction
    after the update and before commit. If it raises, the change is rolled back.
    """
    _check_str('id', id)
    _check_int('token', token)
    _check_str('result', result)
    _check_int('now', now)
    if fault is not None and not callable(fault):
        raise TypeError('fault must be callable or None')
    with _connect(path) as conn, _write_transaction(conn):
        cur = conn.execute(
            "UPDATE jobs SET state='done',result=?,lease_until=NULL "
            "WHERE id=? AND state='running' AND token=? AND lease_until>?",
            (result, id, token, now),
        )
        applied = cur.rowcount == 1
        if fault is not None:
            fault()
        return applied


def inspect(path, id):
    _check_str('id', id)
    with _connect(path) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute('SELECT * FROM jobs WHERE id=?', (id,)).fetchone()
        return dict(row) if row is not None else None


# Outbox/retry helpers are outside the current contract and remain unimplemented.
def retry(path,id,token,now):return False
def publish(path,deliver):return 0
def consume(path,id,body):return False
