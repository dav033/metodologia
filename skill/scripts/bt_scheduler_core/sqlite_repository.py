"""SQLite (WAL) implementation of StateRepository: the durable single authority for a run.

Each transaction opens its own connection and starts `BEGIN IMMEDIATE`, so concurrent writers (threads or processes)
queue on the database lock and see each other's committed state. The state is one JSON document plus an append-only
audit table; both change in the same SQLite transaction.
"""
from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from .errors import SchedulerError
from .model import AuditEntry, RunState
from .repository import Transaction

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY CHECK (id = 1), version INTEGER NOT NULL, doc TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS audit (seq INTEGER PRIMARY KEY, at REAL NOT NULL, kind TEXT NOT NULL, plan_id TEXT NOT NULL,
                                  task_id TEXT NOT NULL, attempt_id TEXT NOT NULL, detail TEXT NOT NULL);
"""


class SqliteRepository:
    def __init__(self, path: str | Path, *, busy_timeout: float = 30.0, create: bool = True):
        self.path = str(path)
        self.busy_timeout = busy_timeout
        if not create and not Path(self.path).is_file():
            raise SchedulerError("STATE_MISSING", f"{self.path}: no such run database")
        conn = self._connect()
        try:
            if create:
                conn.execute("PRAGMA journal_mode=WAL")
                conn.executescript(SCHEMA_SQL)
            else:                                   # look, never touch: an unrelated database is refused unchanged
                names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
                if not {"state", "audit"} <= names:
                    raise SchedulerError("STATE_MISSING", f"{self.path}: not a scheduler run database")
        except sqlite3.Error as exc:
            raise SchedulerError("STATE_UNAVAILABLE", f"{self.path}: {exc}") from exc
        finally:
            conn.close()

    def _connect(self) -> sqlite3.Connection:
        conn = None
        try:
            conn = sqlite3.connect(self.path, timeout=self.busy_timeout, isolation_level=None)
            conn.execute("PRAGMA synchronous=NORMAL")
        except sqlite3.Error as exc:
            if conn is not None:
                conn.close()
            raise SchedulerError("STATE_UNAVAILABLE", f"{self.path}: {exc}") from exc
        return conn

    @contextmanager
    def transaction(self) -> Iterator[Transaction]:
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT version, doc FROM state WHERE id = 1").fetchone()
            tx = Transaction(self._decode(row))
            yield tx
            doc = json.dumps(tx.state.to_dict(), sort_keys=True) if tx.state is not None else None
            if doc is not None and (not row or row[1] != doc):          # untouched state: no write, no version bump
                conn.execute("INSERT INTO state (id, version, doc) VALUES (1, 1, ?) "
                             "ON CONFLICT(id) DO UPDATE SET version = version + 1, doc = excluded.doc", (doc,))
            conn.executemany("INSERT INTO audit (seq, at, kind, plan_id, task_id, attempt_id, detail) VALUES (?,?,?,?,?,?,?)",
                             [(e.seq, e.at, e.kind, e.plan_id, e.task_id, e.attempt_id, json.dumps(e.detail, sort_keys=True))
                              for e in tx.entries])
            conn.execute("COMMIT")
        except sqlite3.Error as exc:                                # busy/locked/disk errors: the caller sees one error type
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise SchedulerError("STATE_UNAVAILABLE", f"{self.path}: {exc}") from exc
        except BaseException:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise
        finally:
            conn.close()

    def _decode(self, row) -> RunState | None:
        try:
            return RunState.from_dict(json.loads(row[1])) if row else None
        except SchedulerError:
            raise
        except ValueError as exc:                   # not JSON at all
            raise SchedulerError("STATE_UNREADABLE", f"{self.path}: {type(exc).__name__}") from exc

    @contextmanager
    def read_transaction(self) -> Iterator[Transaction]:
        """Deferred read of one consistent snapshot (WAL): never blocks a writer, never writes."""
        conn = self._connect()
        try:
            conn.execute("BEGIN")
            yield Transaction(self._decode(conn.execute("SELECT version, doc FROM state WHERE id = 1").fetchone()),
                              readonly=True)
        except sqlite3.Error as exc:
            raise SchedulerError("STATE_UNAVAILABLE", f"{self.path}: {exc}") from exc
        finally:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            conn.close()

    def audit_log(self, since: int = 0) -> list[AuditEntry]:
        conn = self._connect()
        try:
            rows = conn.execute("SELECT seq, at, kind, plan_id, task_id, attempt_id, detail FROM audit "
                                "WHERE seq > ? ORDER BY seq", (since,)).fetchall()
        finally:
            conn.close()
        return [AuditEntry(r[0], r[1], r[2], r[3], r[4], r[5], json.loads(r[6])) for r in rows]
