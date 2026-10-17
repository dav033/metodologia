"""The executor's durable record: attempts (state machine, unique ids/keys) and a write-ahead event outbox.

SQLite in WAL mode, one connection per transaction, `BEGIN IMMEDIATE`: concurrent threads and processes queue on the
database lock, so a uniqueness decision is made once. Everything the executor must remember across a restart is here;
process facts live in the attempt's artefact directory (`shim.json`, `exit.json`), never in memory only.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from .errors import ExecutorError
from .model import (
    LIVE,
    QUEUED,
    REJECTED,
    STATES,
    TERMINAL,
    TRANSITIONS,
    StartRequest,
    TechnicalEvent,
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS attempts (
  seq INTEGER PRIMARY KEY AUTOINCREMENT,
  attempt_id TEXT NOT NULL UNIQUE,
  idem_key TEXT NOT NULL UNIQUE,
  dirname TEXT NOT NULL,
  base_sha TEXT,
  state TEXT NOT NULL,
  request TEXT NOT NULL,
  route TEXT,
  workspace TEXT,
  shim TEXT,
  outcome TEXT,
  handoff TEXT,
  rejection TEXT,
  cancel_requested INTEGER NOT NULL DEFAULT 0,
  cancel_key TEXT,
  cancel_reason TEXT,
  created REAL NOT NULL,
  updated REAL NOT NULL,
  started_at REAL,
  ended_at REAL
);
CREATE INDEX IF NOT EXISTS attempts_state ON attempts(state);
CREATE UNIQUE INDEX IF NOT EXISTS attempts_dirname ON attempts(dirname);
CREATE TABLE IF NOT EXISTS events (
  seq INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id TEXT NOT NULL UNIQUE,
  attempt_id TEXT NOT NULL,
  kind TEXT NOT NULL,
  body TEXT NOT NULL,
  delivered INTEGER NOT NULL DEFAULT 0,
  created REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS events_pending ON events(delivered, seq);
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS route_refs (reference TEXT PRIMARY KEY, attempt_id TEXT NOT NULL);
"""
SCHEMA_VERSION = "1"
JSON_COLUMNS = ("request", "route", "workspace", "shim", "outcome", "handoff", "rejection")
MUTABLE = frozenset({"route", "workspace", "shim", "outcome", "handoff", "rejection", "cancel_requested", "cancel_key",
                     "cancel_reason", "started_at", "ended_at"})


def _dump(value: Any) -> str | None:
    return None if value is None else json.dumps(value, sort_keys=True, separators=(",", ":"))


class Ledger:
    def __init__(self, path: Path | str, *, clock=time.time, busy_seconds: float = 30.0, create: bool = True):
        self.path = Path(path)
        self.clock = clock
        self.busy = busy_seconds
        try:
            if create:                       # a reader (`create=False`) never changes the file: no pragma, no schema
                self.path.parent.mkdir(parents=True, exist_ok=True)
                con = self._connect()
                try:
                    con.execute("PRAGMA journal_mode=WAL")
                    con.executescript(SCHEMA)
                    con.execute("INSERT OR IGNORE INTO meta(key, value) VALUES('schema', ?)", (SCHEMA_VERSION,))
                    found = con.execute("SELECT value FROM meta WHERE key='schema'").fetchone()[0]
                    con.commit()
                finally:
                    con.close()
                os.chmod(self.path, 0o600)             # the order (criteria, checks) and outcomes are private
                if found != SCHEMA_VERSION:
                    raise ExecutorError("LEDGER_ERROR", f"ledger schema {found!r} is not supported (expected {SCHEMA_VERSION})")
        except (OSError, sqlite3.Error) as error:
            raise ExecutorError("LEDGER_ERROR", f"{type(error).__name__}: {error}") from None

    # ---------------------------------------------------------------------------------------------- plumbing
    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.path, timeout=self.busy, isolation_level=None)
        con.row_factory = sqlite3.Row
        con.execute(f"PRAGMA busy_timeout={int(self.busy * 1000)}")
        con.execute("PRAGMA synchronous=FULL")
        return con

    @contextmanager
    def _tx(self, write: bool = True) -> Iterator[sqlite3.Connection]:
        """One transaction. `write=False` is a deferred (read) transaction: it never queues behind the writer's lock."""
        try:
            con = self._connect()
        except sqlite3.Error as error:
            raise ExecutorError("LEDGER_ERROR", str(error)) from None
        try:
            con.execute("BEGIN IMMEDIATE" if write else "BEGIN")
            try:
                yield con
            except BaseException:
                con.execute("ROLLBACK")
                raise
            else:
                con.execute("COMMIT")
        except sqlite3.Error as error:
            raise ExecutorError("LEDGER_ERROR", f"{type(error).__name__}: {error}") from None
        finally:
            con.close()

    @staticmethod
    def _row(row: sqlite3.Row | None) -> dict[str, Any] | None:
        if row is None:
            return None
        out = dict(row)
        for column in JSON_COLUMNS:
            if out.get(column) is not None:
                out[column] = json.loads(out[column])
        out["cancel_requested"] = bool(out["cancel_requested"])
        return out

    # ---------------------------------------------------------------------------------------------- meta
    def meta(self, key: str) -> str | None:
        with self._tx(write=False) as con:
            row = con.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return row["value"] if row else None

    def bind_run(self, plan_id: str, revision: int) -> bool:
        """The first order fixes which run this executor root serves; a later order of another run is foreign."""
        ident = f"{plan_id}:r{revision}"
        with self._tx() as con:
            row = con.execute("SELECT value FROM meta WHERE key='run'").fetchone()
            if row is None:
                con.execute("INSERT INTO meta(key, value) VALUES('run', ?)", (ident,))
                return True
            return row["value"] == ident

    # ---------------------------------------------------------------------------------------------- attempts
    def run_matches(self, plan_id: str, revision: int) -> bool:
        """Read-only: True when this root serves that run or is not bound yet (binding happens with the first ACCEPTED order)."""
        with self._tx(write=False) as con:
            row = con.execute("SELECT value FROM meta WHERE key='run'").fetchone()
        return row is None or row["value"] == f"{plan_id}:r{revision}"

    def insert(self, request: StartRequest, *, dirname: str, state: str, route: Mapping[str, Any] | None = None,
               rejection: Mapping[str, Any] | None = None, max_queued: int | None = None,
               max_backlog: int | None = None, base_sha: str | None = None) -> tuple[dict[str, Any], bool]:
        """Atomically create the attempt unless its key exists. Returns (row, created).

        Same key -> the stored row (a replay); same attempt id under another key, or a key whose stored order differs
        from this one -> KEY_CONFLICT. A full queue is persisted as a rejection (the answer is stable on replay)."""
        now = self.clock()
        with self._tx() as con:
            same_key = con.execute("SELECT * FROM attempts WHERE idem_key=?", (request.idempotency_key,)).fetchone()
            if same_key is not None:
                row = self._row(same_key)
                if not request.matches_record(row["request"]):
                    raise ExecutorError("KEY_CONFLICT", "the idempotency key was used with a different order")
                return row, False
            if con.execute("SELECT 1 FROM attempts WHERE attempt_id=?", (request.attempt_id,)).fetchone():
                raise ExecutorError("KEY_CONFLICT", "the attempt id exists under another idempotency key")
            if state == QUEUED:                         # the first accepted order binds this root to its run
                ident = f"{request.plan_id}:r{request.revision}"
                con.execute("INSERT OR IGNORE INTO meta(key, value) VALUES('run', ?)", (ident,))
                if con.execute("SELECT value FROM meta WHERE key='run'").fetchone()["value"] != ident:
                    raise ExecutorError("FOREIGN_RUN", "this executor serves another plan/revision")
                queued = con.execute("SELECT COUNT(*) FROM attempts WHERE state=?", (QUEUED,)).fetchone()[0]
                backlog = con.execute("SELECT COUNT(*) FROM events WHERE delivered=0").fetchone()[0]
                if max_queued is not None and queued >= max_queued:
                    state, rejection = REJECTED, {"code": "QUEUE_FULL", "detail": f"{queued} orders already queued"}
                elif max_backlog is not None and backlog >= max_backlog:
                    state, rejection = REJECTED, {"code": "QUEUE_FULL", "detail": f"{backlog} undelivered events"}
            if state == QUEUED and route and route.get("single_use") and route.get("reference"):
                used = con.execute("SELECT attempt_id FROM route_refs WHERE reference=?", (route["reference"],)).fetchone()
                if used is not None:
                    raise ExecutorError("ROUTE_INVALID", f"this route reference already started attempt {used['attempt_id']}")
                con.execute("INSERT INTO route_refs(reference, attempt_id) VALUES(?,?)", (route["reference"], request.attempt_id))
            con.execute(
                "INSERT INTO attempts(attempt_id, idem_key, dirname, base_sha, state, request, route, rejection, created, updated,"
                " ended_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (request.attempt_id, request.idempotency_key, dirname, base_sha, state, _dump(request.to_dict()),
                 _dump(route), _dump(rejection), now, now, now if state == REJECTED else None))
            row = self._row(con.execute("SELECT * FROM attempts WHERE attempt_id=?", (request.attempt_id,)).fetchone())
        return row, True

    def get(self, attempt_id: str) -> dict[str, Any] | None:
        with self._tx(write=False) as con:
            return self._row(con.execute("SELECT * FROM attempts WHERE attempt_id=?", (attempt_id,)).fetchone())

    def by_key(self, key: str) -> dict[str, Any] | None:
        with self._tx(write=False) as con:
            return self._row(con.execute("SELECT * FROM attempts WHERE idem_key=?", (key,)).fetchone())

    def in_states(self, states: tuple[str, ...], limit: int | None = None) -> list[dict[str, Any]]:
        marks = ",".join("?" * len(states))
        sql = f"SELECT * FROM attempts WHERE state IN ({marks}) ORDER BY seq" + (f" LIMIT {int(limit)}" if limit else "")
        with self._tx(write=False) as con:
            return [self._row(r) for r in con.execute(sql, states).fetchall()]

    def ids_in_states(self, states: tuple[str, ...]) -> list[str]:
        """Read only the identities for a state-filtered owner poll, without decoding attempt payloads."""
        if not states:
            return []
        marks = ",".join("?" * len(states))
        with self._tx(write=False) as con:
            rows = con.execute(f"SELECT attempt_id FROM attempts WHERE state IN ({marks}) ORDER BY seq", states)
            return [row[0] for row in rows]

    def count(self, states: tuple[str, ...]) -> int:
        marks = ",".join("?" * len(states))
        with self._tx(write=False) as con:
            return con.execute(f"SELECT COUNT(*) FROM attempts WHERE state IN ({marks})", states).fetchone()[0]

    def all_ids(self) -> list[str]:
        with self._tx(write=False) as con:
            return [r[0] for r in con.execute("SELECT attempt_id FROM attempts ORDER BY seq").fetchall()]

    @staticmethod
    def _assign(fields: Mapping[str, Any]) -> tuple[str, list[Any]]:
        bad = set(fields) - MUTABLE
        if bad:
            raise ValueError(f"not mutable: {sorted(bad)}")
        names = list(fields)
        values = [_dump(fields[n]) if n in JSON_COLUMNS else (int(fields[n]) if n == "cancel_requested" else fields[n])
                  for n in names]
        return "".join(f", {n}=?" for n in names), values

    def transition(self, attempt_id: str, to: str, *, expect: tuple[str, ...], event: TechnicalEvent | None = None,
                   **fields: Any) -> bool:
        """Compare-and-set: move to `to` only from one of `expect` (and only along legal edges). False = lost the race."""
        if to not in STATES:
            raise ValueError(to)
        illegal = [s for s in expect if to not in TRANSITIONS[s]]
        if illegal:
            raise ValueError(f"illegal transition {illegal} -> {to}")
        sets, values = self._assign(fields)
        now = self.clock()
        marks = ",".join("?" * len(expect))
        with self._tx() as con:
            cur = con.execute(f"UPDATE attempts SET state=?, updated=?{sets} WHERE attempt_id=? AND state IN ({marks})",
                              [to, now, *values, attempt_id, *expect])
            if cur.rowcount != 1:
                return False
            if event is not None:
                self._add_event(con, event, now)
        return True

    def update(self, attempt_id: str, *, expect: tuple[str, ...] | None = None, **fields: Any) -> bool:
        """Set non-state fields (optionally only while in one of `expect`). False = not applied."""
        sets, values = self._assign(fields)
        if not fields:
            return True
        sql = f"UPDATE attempts SET updated=?{sets} WHERE attempt_id=?"
        args: list[Any] = [self.clock(), *values, attempt_id]
        if expect:
            sql += f" AND state IN ({','.join('?' * len(expect))})"
            args += list(expect)
        with self._tx() as con:
            return con.execute(sql, args).rowcount == 1

    def request_cancel(self, attempt_id: str, key: str, reason: str) -> str:
        """Record the cancel intent once. Returns 'recorded', 'duplicate' (same key again), 'terminal' or 'unknown'."""
        with self._tx() as con:
            row = con.execute("SELECT state, cancel_requested, cancel_key FROM attempts WHERE attempt_id=?",
                              (attempt_id,)).fetchone()
            if row is None:
                return "unknown"
            if row["state"] in TERMINAL:
                return "terminal"
            if row["cancel_requested"]:
                return "duplicate"
            con.execute("UPDATE attempts SET cancel_requested=1, cancel_key=?, cancel_reason=?, updated=? WHERE attempt_id=?",
                        (key, reason[:200], self.clock(), attempt_id))
            return "recorded"

    # ---------------------------------------------------------------------------------------------- events
    @staticmethod
    def _add_event(con: sqlite3.Connection, event: TechnicalEvent, now: float) -> None:
        con.execute("INSERT OR IGNORE INTO events(event_id, attempt_id, kind, body, created) VALUES(?,?,?,?,?)",
                    (event.event_id, event.attempt_id, event.kind, _dump(event.to_dict()), now))

    def add_event(self, event: TechnicalEvent) -> None:
        with self._tx() as con:
            self._add_event(con, event, self.clock())

    def pending_events(self, limit: int) -> list[TechnicalEvent]:
        with self._tx(write=False) as con:
            rows = con.execute("SELECT body FROM events WHERE delivered=0 ORDER BY seq LIMIT ?", (limit,)).fetchall()
        return [TechnicalEvent.from_dict(json.loads(r["body"])) for r in rows]

    def mark_delivered(self, event_id: str) -> None:
        with self._tx() as con:
            con.execute("UPDATE events SET delivered=1 WHERE event_id=?", (event_id,))

    def events(self, attempt_id: str | None = None) -> list[dict[str, Any]]:
        with self._tx(write=False) as con:
            if attempt_id is None:
                rows = con.execute("SELECT * FROM events ORDER BY seq").fetchall()
            else:
                rows = con.execute("SELECT * FROM events WHERE attempt_id=? ORDER BY seq", (attempt_id,)).fetchall()
        return [{**dict(r), "body": json.loads(r["body"]), "delivered": bool(r["delivered"])} for r in rows]

    def has_undelivered(self, attempt_id: str) -> bool:
        with self._tx(write=False) as con:
            return con.execute("SELECT 1 FROM events WHERE attempt_id=? AND delivered=0 LIMIT 1", (attempt_id,)).fetchone() is not None

    def bound_run(self) -> str | None:
        """The `<plan>:r<revision>` this root serves, or None while unbound."""
        return self.meta("run")

    def undelivered(self) -> int:
        with self._tx(write=False) as con:
            return con.execute("SELECT COUNT(*) FROM events WHERE delivered=0").fetchone()[0]


__all__ = ["LIVE", "TERMINAL", "Ledger"]
