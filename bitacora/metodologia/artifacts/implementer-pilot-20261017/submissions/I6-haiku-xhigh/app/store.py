"""SQLite-backed job queue with leases, dependencies, retries, and an outbox/inbox.

Each call opens its own connection, performs its writes in a BEGIN IMMEDIATE
transaction, and closes the connection before returning.
"""

import json
import sqlite3

from .checks import require_callable, require_int, require_optional_str, require_str
from .db import connect, initialize_schema, write_transaction

CLAIM_CANDIDATE = """
SELECT id, payload, token FROM jobs AS job
WHERE (job.state = 'pending' OR (job.state = 'running' AND job.lease_until <= ?))
  AND (job.depends_on IS NULL OR EXISTS (
        SELECT 1 FROM jobs AS parent WHERE parent.id = job.depends_on AND parent.state = 'done'))
ORDER BY job.id
LIMIT 1
"""
CLAIM_JOB = "UPDATE jobs SET state='running', token=?, lease_until=?, attempts=attempts+1 WHERE id=?"
COMPLETE_JOB = """
UPDATE jobs SET state='done', result=?, lease_until=NULL
WHERE id=? AND state='running' AND token=? AND lease_until>?
"""
RETRY_JOB = """
UPDATE jobs SET state='pending', lease_until=NULL
WHERE id=? AND state='running' AND token=? AND lease_until>?
"""
NEXT_UNDELIVERED = """
SELECT id, body FROM outbox
WHERE delivered=0 AND (? IS NULL OR id>?)
ORDER BY id
LIMIT 1
"""


def init(path):
    initialize_schema(path)


def enqueue(path, id, payload, depends_on=None):
    require_str('id', id)
    require_str('payload', payload)
    require_optional_str('depends_on', depends_on)
    with connect(path) as conn, write_transaction(conn):
        conn.execute('INSERT OR IGNORE INTO jobs(id,payload,depends_on) VALUES(?,?,?)', (id, payload, depends_on))


def claim(path, now, ttl):
    require_int('now', now)
    require_int('ttl', ttl)
    if ttl <= 0:
        raise ValueError('ttl must be greater than 0')
    lease_until = now + ttl
    require_int('now + ttl', lease_until)
    with connect(path) as conn, write_transaction(conn):
        candidates = conn.execute(CLAIM_CANDIDATE, (now,)).fetchall()
        if not candidates:
            return None
        job_id, payload, token = candidates[0]
        new_token = token + 1
        conn.execute(CLAIM_JOB, (new_token, lease_until, job_id))
        return job_id, payload, new_token


def complete(path, id, token, result, now, fault=None):
    require_str('id', id)
    require_int('token', token)
    require_str('result', result)
    require_int('now', now)
    if fault is not None:
        require_callable('fault', fault)
    with connect(path) as conn, write_transaction(conn):
        if conn.execute(COMPLETE_JOB, (result, id, token, now)).rowcount != 1:
            return False
        _fire(fault, 'after_result')
        conn.execute('INSERT INTO outbox(id,body) VALUES(?,?)', (id, _event_body(id, result)))
        _fire(fault, 'before_commit')
    return True


def inspect(path, id):
    require_str('id', id)
    with connect(path) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute('SELECT * FROM jobs WHERE id=?', (id,)).fetchone()
    return dict(row) if row is not None else None


def retry(path, id, token, now):
    require_str('id', id)
    require_int('token', token)
    require_int('now', now)
    with connect(path) as conn, write_transaction(conn):
        return conn.execute(RETRY_JOB, (id, token, now)).rowcount == 1


def publish(path, deliver):
    require_callable('deliver', deliver)
    delivered = 0
    after = None
    while True:
        event = _next_undelivered(path, after)
        if event is None:
            return delivered
        event_id, body = event
        deliver(event_id, body)
        _mark_delivered(path, event_id)
        delivered += 1
        after = event_id


def consume(path, id, body):
    require_str('id', id)
    require_str('body', body)
    with connect(path) as conn, write_transaction(conn):
        return conn.execute('INSERT OR IGNORE INTO inbox(id,body) VALUES(?,?)', (id, body)).rowcount == 1


def _fire(fault, point):
    if fault is not None:
        fault(point)


def _event_body(job_id, result):
    return json.dumps({'job_id': job_id, 'result': result}, sort_keys=True)


def _next_undelivered(path, after):
    # The connection is closed before the caller's callback runs, so no lock is held during delivery.
    with connect(path) as conn:
        rows = conn.execute(NEXT_UNDELIVERED, (after, after)).fetchall()
    return rows[0] if rows else None


def _mark_delivered(path, event_id):
    with connect(path) as conn, write_transaction(conn):
        conn.execute('UPDATE outbox SET delivered=1 WHERE id=?', (event_id,))
