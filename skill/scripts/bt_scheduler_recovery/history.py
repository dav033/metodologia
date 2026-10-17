"""Private bounded decision history; no scheduler state is stored here."""
from __future__ import annotations

import json
import os
import sqlite3
import stat
from contextlib import closing
from dataclasses import asdict
from pathlib import Path
from typing import Self
from urllib.parse import quote

from .contracts import HistorySummary, Policy, RecoveryCase, RecoveryDecision
from .policy import DEFAULT_POLICY, logical_key, propose
from .validation import RecoveryError, identifier, integer, number, require

APP_ID = 0x4D355231
SCHEMA = """
CREATE TABLE decisions (
    seq INTEGER PRIMARY KEY,
    decision_id TEXT UNIQUE NOT NULL,
    run_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    attempt_id TEXT NOT NULL,
    cause TEXT NOT NULL,
    facts TEXT NOT NULL,
    case_json TEXT NOT NULL,
    policy_json TEXT NOT NULL,
    decision_json TEXT NOT NULL,
    action TEXT NOT NULL
);
CREATE INDEX cause_history ON decisions(run_id, task_id, cause, attempt_id);
CREATE INDEX last_task ON decisions(run_id, task_id, seq);
"""


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _facts(case: RecoveryCase) -> str:
    data = case.to_dict()
    data.pop("now")  # Wall clock advancement does not change the logical incident.
    return _json(data)


def _private_path(path: Path) -> None:
    missing = []
    parent = path.parent
    while not parent.exists():
        missing.append(parent)
        parent = parent.parent
    for directory in reversed(missing):
        try:
            directory.mkdir(mode=0o700)
        except FileExistsError:
            require(directory.is_dir() and not directory.is_symlink(), "STORE_PATH")
    require(not path.is_symlink(), "STORE_PATH")
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        require(path.is_file(), "STORE_PATH")
    else:
        os.close(descriptor)
    if os.name == "posix":
        info = path.stat()
        require(stat.S_IMODE(info.st_mode) & 0o077 == 0 and info.st_uid == os.getuid(), "STORE_PERMISSIONS")


def _check_schema(connection: sqlite3.Connection) -> None:
    require(connection.execute("PRAGMA application_id").fetchone()[0] == APP_ID, "STORE_SCHEMA")
    require(connection.execute("PRAGMA user_version").fetchone()[0] == 1, "STORE_SCHEMA")


def _latest(connection: sqlite3.Connection, run_id: str | None, task_id: str | None) -> dict | None:
    terms, args = [], []
    for column, value in (("run_id", run_id), ("task_id", task_id)):
        if value is not None:
            identifier(value)
            terms.append(column + " = ?")
            args.append(value)
    query = "SELECT decision_json FROM decisions"
    if terms:
        query += " WHERE " + " AND ".join(terms)
    row = connection.execute(query + " ORDER BY seq DESC LIMIT 1", args).fetchone()
    return RecoveryDecision.from_dict(json.loads(row[0])).to_dict() if row else None


def _metrics(connection: sqlite3.Connection) -> dict:
    rows = connection.execute("SELECT action, count(*) FROM decisions GROUP BY action").fetchall()
    counts = {"retry": 0, "wait": 0, "block": 0}
    counts.update(dict(rows))
    return {"schema_version": "m5.recovery-metrics/1", "decisions": sum(counts.values()), "actions": counts}


class DecisionStore:
    def __init__(self, path: str | Path, *, max_decisions: int = 10000, timeout_seconds: float = 2):
        integer(max_decisions, 1, 1_000_000)
        number(timeout_seconds, 0.001, 30)
        self.max_decisions = max_decisions
        self.connection: sqlite3.Connection | None = None
        try:
            target = Path(path).absolute()
            _private_path(target)
            self.connection = sqlite3.connect(target, timeout=timeout_seconds, isolation_level=None)
            self.connection.execute("PRAGMA synchronous=FULL")
            self.connection.execute("BEGIN IMMEDIATE")
            tables = self.connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            if not tables:
                # executescript commits first; create each statement within the same transaction.
                for statement in SCHEMA.split(";"):
                    if statement.strip():
                        self.connection.execute(statement)
                self.connection.execute(f"PRAGMA application_id={APP_ID}")
                self.connection.execute("PRAGMA user_version=1")
            _check_schema(self.connection)
            self.connection.commit()
        except (OSError, sqlite3.Error) as error:
            self.close()
            raise _store_error(error) from None
        except RecoveryError:
            self.close()
            raise

    def decide(self, case: RecoveryCase, policy: Policy = DEFAULT_POLICY) -> RecoveryDecision:
        require(type(case) is RecoveryCase and type(policy) is Policy)
        connection = self._open()
        key = logical_key(case, policy)
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT facts, decision_json FROM decisions WHERE decision_id=?", (key,)).fetchone()
            if row:
                require(row[0] == _facts(case), "CASE_CONFLICT")
                decision = RecoveryDecision.from_dict(json.loads(row[1]))
                current = propose(case, policy)
                if current.reason_code in {"evidence_stale", "evidence_from_future", "elapsed_limit"}:
                    raise RecoveryError("EVIDENCE_STALE")
            else:
                count = connection.execute("SELECT count(*) FROM decisions").fetchone()[0]
                require(count < min(self.max_decisions, policy.max_decisions), "STORE_FULL")
                same = connection.execute(
                    "SELECT count(DISTINCT attempt_id) FROM decisions WHERE run_id=? AND task_id=? AND cause=? AND attempt_id<>?",
                    (case.run_id, case.task_id, case.technical_cause, case.attempt_id)).fetchone()[0]
                decision = propose(case, policy, HistorySummary(same, count))
                connection.execute("INSERT INTO decisions(decision_id,run_id,task_id,attempt_id,cause,facts,case_json,"
                                   "policy_json,decision_json,action) VALUES (?,?,?,?,?,?,?,?,?,?)",
                                   (key, case.run_id, case.task_id, case.attempt_id, case.technical_cause, _facts(case),
                                    _json(case.to_dict()), _json(asdict(policy)), _json(decision.to_dict()), decision.action))
            connection.commit()
            return decision
        except RecoveryError:
            connection.rollback()
            raise
        except (sqlite3.Error, ValueError, TypeError) as error:
            connection.rollback()
            raise _store_error(error) from None

    def latest(self, run_id: str | None = None, task_id: str | None = None) -> dict | None:
        try:
            return _latest(self._open(), run_id, task_id)
        except (sqlite3.Error, ValueError, TypeError) as error:
            if isinstance(error, RecoveryError):
                raise
            raise _store_error(error) from None

    def metrics(self) -> dict:
        try:
            return _metrics(self._open())
        except sqlite3.Error as error:
            raise _store_error(error) from None

    def _open(self) -> sqlite3.Connection:
        require(self.connection is not None, "STORE_CLOSED")
        return self.connection

    def close(self) -> None:
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


def _store_error(error: Exception) -> RecoveryError:
    if isinstance(error, sqlite3.OperationalError) and getattr(error, "sqlite_errorcode", None) in (5, 6):
        return RecoveryError("STORE_BUSY")
    return RecoveryError("STORE_IO")


def inspect_store(path: str | Path, *, metrics: bool = False) -> dict | None:
    """Read-only inspection never creates a database or its parent directory."""
    target = Path(path).absolute()
    require(target.is_file() and not target.is_symlink(), "STORE_MISSING")
    try:
        with closing(sqlite3.connect("file:" + quote(str(target)) + "?mode=ro", uri=True, timeout=2)) as connection:
            _check_schema(connection)
            return _metrics(connection) if metrics else _latest(connection, None, None)
    except (OSError, sqlite3.Error, ValueError, TypeError) as error:
        if isinstance(error, RecoveryError):
            raise
        raise _store_error(error) from None
