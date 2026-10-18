"""Connection, transaction, and schema helpers for the job store."""

import sqlite3
from contextlib import contextmanager

BUSY_TIMEOUT_SECONDS = 30.0

SCHEMA = (
    "CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,payload TEXT NOT NULL,state TEXT NOT NULL DEFAULT 'pending',token INTEGER NOT NULL DEFAULT 0,lease_until INTEGER,attempts INTEGER NOT NULL DEFAULT 0,depends_on TEXT,result TEXT)",
    "CREATE TABLE IF NOT EXISTS outbox(id TEXT PRIMARY KEY,body TEXT NOT NULL,delivered INTEGER NOT NULL DEFAULT 0)",
    "CREATE TABLE IF NOT EXISTS inbox(id TEXT PRIMARY KEY,body TEXT NOT NULL)",
)


@contextmanager
def connect(path):
    """Yield an autocommit connection that fsyncs on commit and is always closed."""
    conn = sqlite3.connect(path, timeout=BUSY_TIMEOUT_SECONDS, isolation_level=None)
    try:
        conn.execute('PRAGMA synchronous=FULL')
        yield conn
    finally:
        conn.close()


@contextmanager
def write_transaction(conn):
    """Run the block in BEGIN IMMEDIATE; commit on success, roll back on any error."""
    conn.execute('BEGIN IMMEDIATE')
    try:
        yield conn
        conn.execute('COMMIT')
    except BaseException:
        if conn.in_transaction:
            conn.execute('ROLLBACK')
        raise


def initialize_schema(path):
    with connect(path) as conn:
        conn.execute('PRAGMA journal_mode=WAL').fetchall()
        with write_transaction(conn):
            for statement in SCHEMA:
                conn.execute(statement)
