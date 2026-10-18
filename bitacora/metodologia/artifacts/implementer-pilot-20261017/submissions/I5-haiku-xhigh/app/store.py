import sqlite3
from contextlib import contextmanager

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
BUSY_TIMEOUT_SECONDS = 30.0
INT64_MIN = -(2**63)
INT64_MAX = 2**63 - 1


def _check_path(path):
    if not isinstance(path, str):
        raise TypeError('path must be str')


def _check_str(name, value):
    if not isinstance(value, str):
        raise TypeError(f'{name} must be str')


def _check_int(name, value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f'{name} must be int')
    if not INT64_MIN <= value <= INT64_MAX:
        raise ValueError(f'{name} is outside the 64-bit integer range')


@contextmanager
def _connect(path):
    """Open a private connection to path and always close it."""
    _check_path(path)
    conn = sqlite3.connect(path, timeout=BUSY_TIMEOUT_SECONDS, isolation_level=None)
    try:
        conn.execute('PRAGMA synchronous=FULL')
        yield conn
    finally:
        conn.close()


@contextmanager
def _write_transaction(conn):
    """Run a block as one write transaction, taking the write lock up front.

    Commits on normal exit and rolls back on any exception, including a
    failed COMMIT, so no partial mutation survives.
    """
    conn.execute('BEGIN IMMEDIATE')
    try:
        yield conn
        conn.execute('COMMIT')
    except BaseException:
        if conn.in_transaction:
            conn.execute('ROLLBACK')
        raise


def init(path):
    with _connect(path) as conn:
        conn.execute('PRAGMA journal_mode=WAL').fetchone()
        with _write_transaction(conn):
            conn.execute(SCHEMA)


def enqueue(path, id, payload, depends_on=None):
    _check_str('id', id)
    _check_str('payload', payload)
    if depends_on is not None:
        _check_str('depends_on', depends_on)
    with _connect(path) as conn:
        with _write_transaction(conn):
            conn.execute(
                'INSERT OR IGNORE INTO jobs(id,payload,depends_on) VALUES(?,?,?)',
                (id, payload, depends_on),
            )


def claim(path, now, ttl):
    _check_int('now', now)
    _check_int('ttl', ttl)
    if ttl <= 0:
        raise ValueError('ttl must be positive')
    lease_until = now + ttl
    _check_int('lease_until', lease_until)
    with _connect(path) as conn:
        with _write_transaction(conn):
            row = conn.execute(
                "SELECT id, payload FROM jobs "
                "WHERE state = 'pending' OR (state = 'running' AND lease_until <= ?) "
                "ORDER BY id COLLATE BINARY LIMIT 1",
                (now,),
            ).fetchone()
            if row is None:
                return None
            job_id, payload = row
            conn.execute(
                "UPDATE jobs SET state = 'running', token = token + 1, "
                "lease_until = ?, attempts = attempts + 1 WHERE id = ?",
                (lease_until, job_id),
            )
            token = conn.execute(
                'SELECT token FROM jobs WHERE id = ?', (job_id,)
            ).fetchone()[0]
            return job_id, payload, token


def complete(path, id, token, result, now, fault=None):
    """Mark a job done if the caller still holds its current lease.

    fault is None or a zero-argument callable run after the update and before
    commit (fault injection). If it raises, the transaction is rolled back.
    Returns False, with no mutation, for stale, expired, or missing jobs.
    """
    _check_str('id', id)
    _check_int('token', token)
    _check_str('result', result)
    _check_int('now', now)
    if fault is not None and not callable(fault):
        raise TypeError('fault must be None or callable')
    with _connect(path) as conn:
        with _write_transaction(conn):
            cursor = conn.execute(
                "UPDATE jobs SET state = 'done', result = ?, lease_until = NULL "
                "WHERE id = ? AND state = 'running' AND token = ? AND lease_until > ?",
                (result, id, token, now),
            )
            if cursor.rowcount != 1:
                return False
            if fault is not None:
                fault()
            return True


def inspect(path, id):
    _check_str('id', id)
    with _connect(path) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute('SELECT * FROM jobs WHERE id = ?', (id,)).fetchone()
    return dict(row) if row is not None else None


def retry(path, id, token, now):return False
def publish(path,deliver):return 0
def consume(path,id,body):return False
