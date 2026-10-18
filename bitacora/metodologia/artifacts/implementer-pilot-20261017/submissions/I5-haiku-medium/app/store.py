"""Durable, lease-based job queue on SQLite.

Every call opens its own connection and closes it before returning. Writes run
inside BEGIN IMMEDIATE transactions, so concurrent clients serialise on the
database write lock and each job has at most one current lease.
"""
import sqlite3

from .db import connect, create_schema, write_transaction


def _require_str(name, value):
    if not isinstance(value, str):
        raise TypeError(f"{name} must be str, not {type(value).__name__}")


def _require_int(name, value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be int, not {type(value).__name__}")


def init(path):
    """Create the store at path if needed. Safe to call repeatedly."""
    create_schema(path)


def enqueue(path, id, payload, depends_on=None):
    """Insert a job. A duplicate id is ignored and keeps its first payload."""
    _require_str("id", id)
    _require_str("payload", payload)
    if depends_on is not None:
        _require_str("depends_on", depends_on)
    with write_transaction(path) as conn:
        conn.execute(
            "INSERT INTO jobs(id, payload, depends_on) VALUES(?, ?, ?) "
            "ON CONFLICT(id) DO NOTHING",
            (id, payload, depends_on),
        )


def claim(path, now, ttl):
    """Lease the smallest eligible job and return (id, payload, token), or None.

    Eligible jobs are pending jobs and running jobs whose lease has expired
    (lease_until <= now). The returned token is the job's new persistent
    fencing token; older tokens can no longer complete the job.
    """
    _require_int("now", now)
    _require_int("ttl", ttl)
    if ttl <= 0:
        raise ValueError(f"ttl must be positive, got {ttl}")
    with write_transaction(path) as conn:
        row = conn.execute(
            "SELECT id, payload FROM jobs "
            "WHERE state = 'pending' OR (state = 'running' AND lease_until <= ?) "
            "ORDER BY id LIMIT 1",
            (now,),
        ).fetchone()
        if row is None:
            return None
        job_id, payload = row
        conn.execute(
            "UPDATE jobs SET state = 'running', token = token + 1, "
            "lease_until = ?, attempts = attempts + 1 WHERE id = ?",
            (now + ttl, job_id),
        )
        token = conn.execute(
            "SELECT token FROM jobs WHERE id = ?", (job_id,)
        ).fetchone()[0]
        return (job_id, payload, token)


def complete(path, id, token, result, now, fault=None):
    """Mark a job done and store its result.

    Succeeds only if the job is running, the token matches exactly, and the
    lease is still live (lease_until > now). Otherwise returns False and
    changes nothing. The fault argument is accepted for interface
    compatibility and is not used.
    """
    _require_str("id", id)
    _require_str("result", result)
    _require_int("token", token)
    _require_int("now", now)
    with write_transaction(path) as conn:
        cur = conn.execute(
            "UPDATE jobs SET state = 'done', result = ?, lease_until = NULL "
            "WHERE id = ? AND state = 'running' AND token = ? AND lease_until > ?",
            (result, id, token, now),
        )
        return cur.rowcount == 1


def inspect(path, id):
    """Return all columns of the job as a dict, or None if it does not exist."""
    _require_str("id", id)
    with connect(path) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (id,)).fetchone()
    return dict(row) if row is not None else None
