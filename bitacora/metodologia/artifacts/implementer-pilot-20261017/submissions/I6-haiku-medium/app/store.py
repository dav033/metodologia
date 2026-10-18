import json
import sqlite3
from contextlib import contextmanager

BUSY_TIMEOUT_S = 30

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

# A job is eligible when it is pending or its lease has expired, and its
# parent (if any) exists and is done. Missing parents and cycles never match.
ELIGIBLE_SQL = (
    "SELECT j.id, j.payload FROM jobs AS j "
    "WHERE (j.state = 'pending' OR (j.state = 'running' AND j.lease_until <= ?)) "
    "AND (j.depends_on IS NULL OR EXISTS ("
    "SELECT 1 FROM jobs AS p WHERE p.id = j.depends_on AND p.state = 'done')) "
    "ORDER BY j.id LIMIT 1"
)


def _require_str(name, value):
    if not isinstance(value, str):
        raise TypeError(f"{name} must be str, not {type(value).__name__}")


def _require_int(name, value):
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{name} must be int, not {type(value).__name__}")


def _connect(path):
    _require_str("path", path)
    # isolation_level=None: transactions are opened explicitly with BEGIN IMMEDIATE.
    conn = sqlite3.connect(path, timeout=BUSY_TIMEOUT_S, isolation_level=None)
    conn.execute("PRAGMA synchronous=FULL")
    return conn


@contextmanager
def _connection(path):
    conn = _connect(path)
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def _write_tx(path):
    """Yield a connection inside an IMMEDIATE transaction.

    Commits when the block exits normally and rolls back (re-raising) on any error.
    """
    with _connection(path) as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            yield conn
        except BaseException:
            conn.execute("ROLLBACK")
            raise
        else:
            conn.execute("COMMIT")


def _fire(fault, point):
    if fault is not None:
        fault(point)


def _event_body(job_id, result):
    return json.dumps({"id": job_id, "result": result}, sort_keys=True)


def init(path):
    with _connection(path) as conn:
        # journal_mode is persistent and cannot be changed inside a transaction.
        conn.execute("PRAGMA journal_mode=WAL").fetchone()
    with _write_tx(path) as conn:
        for statement in SCHEMA:
            conn.execute(statement)


def enqueue(path, id, payload, depends_on=None):
    _require_str("id", id)
    _require_str("payload", payload)
    if depends_on is not None:
        _require_str("depends_on", depends_on)
    with _write_tx(path) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO jobs(id, payload, depends_on) VALUES(?, ?, ?)",
            (id, payload, depends_on),
        )


def claim(path, now, ttl):
    _require_int("now", now)
    _require_int("ttl", ttl)
    if ttl <= 0:
        raise ValueError("ttl must be positive")
    with _write_tx(path) as conn:
        row = conn.execute(ELIGIBLE_SQL, (now,)).fetchone()
        if row is None:
            return None
        job_id, payload = row
        conn.execute(
            "UPDATE jobs SET state = 'running', token = token + 1, "
            "attempts = attempts + 1, lease_until = ? WHERE id = ?",
            (now + ttl, job_id),
        )
        (token,) = conn.execute("SELECT token FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return job_id, payload, token


def _holds_lease(conn, id, token, now):
    row = conn.execute(
        "SELECT state, token, lease_until FROM jobs WHERE id = ?", (id,)
    ).fetchone()
    if row is None:
        return False
    state, current_token, lease_until = row
    return (
        state == "running"
        and current_token == token
        and lease_until is not None
        and lease_until > now
    )


def complete(path, id, token, result, now, fault=None):
    _require_str("id", id)
    _require_int("token", token)
    _require_str("result", result)
    _require_int("now", now)
    if fault is not None and not callable(fault):
        raise TypeError("fault must be callable or None")
    with _write_tx(path) as conn:
        if not _holds_lease(conn, id, token, now):
            return False
        conn.execute(
            "UPDATE jobs SET state = 'done', result = ?, lease_until = NULL WHERE id = ?",
            (result, id),
        )
        _fire(fault, "after_result")
        conn.execute(
            "INSERT INTO outbox(id, body) VALUES(?, ?)",
            (id, _event_body(id, result)),
        )
        _fire(fault, "before_commit")
    return True


def inspect(path, id):
    _require_str("id", id)
    with _connection(path) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (id,)).fetchone()
    return dict(row) if row is not None else None


def retry(path, id, token, now):
    _require_str("id", id)
    _require_int("token", token)
    _require_int("now", now)
    with _write_tx(path) as conn:
        cursor = conn.execute(
            "UPDATE jobs SET state = 'pending', lease_until = NULL "
            "WHERE id = ? AND state = 'running' AND token = ? AND lease_until > ?",
            (id, token, now),
        )
        return cursor.rowcount == 1


def _undelivered(path):
    with _connection(path) as conn:
        return conn.execute(
            "SELECT id, body FROM outbox WHERE delivered = 0 ORDER BY id"
        ).fetchall()


def _mark_delivered(path, id):
    with _write_tx(path) as conn:
        conn.execute("UPDATE outbox SET delivered = 1 WHERE id = ?", (id,))


def publish(path, deliver):
    if not callable(deliver):
        raise TypeError("deliver must be callable")
    # Rows are read before any callback runs, so no transaction or lock is held
    # while the callback executes (it may call consume on the same database).
    pending = _undelivered(path)
    delivered = 0
    for event_id, body in pending:
        deliver(event_id, body)
        _mark_delivered(path, event_id)
        delivered += 1
    return delivered


def consume(path, id, body):
    _require_str("id", id)
    _require_str("body", body)
    with _write_tx(path) as conn:
        cursor = conn.execute(
            "INSERT OR IGNORE INTO inbox(id, body) VALUES(?, ?)", (id, body)
        )
        return cursor.rowcount == 1
