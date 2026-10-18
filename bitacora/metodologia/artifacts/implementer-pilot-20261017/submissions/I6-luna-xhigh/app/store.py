"""A small, durable SQLite-backed job queue."""

from contextlib import contextmanager
import sqlite3


@contextmanager
def _connection(path):
    """Open a fully synchronous connection and always close it."""
    connection = sqlite3.connect(path, timeout=30, isolation_level=None)
    try:
        connection.execute("PRAGMA synchronous=FULL")
        yield connection
    finally:
        connection.close()


@contextmanager
def _transaction(connection):
    """Run a transaction that reserves the write lock before reading."""
    connection.execute("BEGIN IMMEDIATE")
    try:
        yield
    except BaseException:
        if connection.in_transaction:
            connection.rollback()
        raise
    else:
        try:
            connection.commit()
        except BaseException:
            if connection.in_transaction:
                connection.rollback()
            raise


def init(path):
    with _connection(path) as connection:
        with _transaction(connection):
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
            connection.execute(
                "CREATE TABLE IF NOT EXISTS outbox("
                "id TEXT PRIMARY KEY,"
                "body TEXT NOT NULL,"
                "delivered INTEGER NOT NULL DEFAULT 0)"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS inbox("
                "id TEXT PRIMARY KEY,"
                "body TEXT NOT NULL)"
            )


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
        with _transaction(connection):
            row = connection.execute(
                "SELECT job.id, job.payload, job.token "
                "FROM jobs AS job "
                "WHERE (job.state = 'pending' "
                "       OR (job.state = 'running' AND job.lease_until <= ?)) "
                "AND (job.depends_on IS NULL OR EXISTS ("
                "    SELECT 1 FROM jobs AS parent "
                "    WHERE parent.id = job.depends_on AND parent.state = 'done'"
                ")) "
                "ORDER BY job.id COLLATE BINARY LIMIT 1",
                (now,),
            ).fetchone()
            if row is None:
                return None

            job_id, payload, previous_token = row
            token = previous_token + 1
            connection.execute(
                "UPDATE jobs SET state = 'running', token = ?, lease_until = ?, "
                "attempts = attempts + 1 WHERE id = ?",
                (token, now + ttl, job_id),
            )
            return job_id, payload, token


def complete(path, id, token, result, now, fault=None):
    with _connection(path) as connection:
        with _transaction(connection):
            cursor = connection.execute(
                "UPDATE jobs SET state = 'done', result = ?, lease_until = NULL "
                "WHERE id = ? AND state = 'running' AND token = ? "
                "AND lease_until > ?",
                (result, id, token, now),
            )
            if cursor.rowcount != 1:
                return False

            if fault is not None:
                fault("after_result")
            connection.execute(
                "INSERT INTO outbox(id, body) VALUES (?, ?)", (id, result)
            )
            if fault is not None:
                fault("before_commit")
            return True


def inspect(path, id):
    with _connection(path) as connection:
        cursor = connection.execute("SELECT * FROM jobs WHERE id = ?", (id,))
        row = cursor.fetchone()
        if row is None:
            return None
        return {description[0]: value for description, value in zip(cursor.description, row)}


def retry(path, id, token, now):
    with _connection(path) as connection:
        with _transaction(connection):
            cursor = connection.execute(
                "UPDATE jobs SET state = 'pending', lease_until = NULL "
                "WHERE id = ? AND state = 'running' AND token = ? "
                "AND lease_until > ?",
                (id, token, now),
            )
            return cursor.rowcount == 1


def publish(path, deliver):
    # Fetch and close the reader before invoking user code. A callback may use
    # this database itself (for example, by calling consume).
    with _connection(path) as connection:
        rows = connection.execute(
            "SELECT id, body FROM outbox WHERE delivered = 0 ORDER BY id COLLATE BINARY"
        ).fetchall()

    delivered = 0
    for id, body in rows:
        deliver(id, body)
        with _connection(path) as connection:
            with _transaction(connection):
                connection.execute(
                    "UPDATE outbox SET delivered = 1 WHERE id = ? AND delivered = 0",
                    (id,),
                )
        delivered += 1
    return delivered


def consume(path, id, body):
    with _connection(path) as connection:
        cursor = connection.execute(
            "INSERT OR IGNORE INTO inbox(id, body) VALUES (?, ?)", (id, body)
        )
        return cursor.rowcount == 1
