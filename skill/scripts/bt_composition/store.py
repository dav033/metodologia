"""One SQLite WAL database belongs to one caller-supplied run path."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from .contracts import Candidate, SubplanVersion


class Store:
    SCHEMA_VERSION = 3

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path, timeout=5.0, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        schema_version = int(self.connection.execute("PRAGMA user_version").fetchone()[0])
        if schema_version not in (0, 1, 2, self.SCHEMA_VERSION):
            self.connection.close()
            raise ValueError("UNSUPPORTED_SCHEMA_VERSION")
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA foreign_keys=ON")
        self._initialize_schema(schema_version)

    def _initialize_schema(self, version: int) -> None:
        if version == self.SCHEMA_VERSION:
            return
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            self.connection.execute("""CREATE TABLE IF NOT EXISTS versions(
                plan_id TEXT NOT NULL, subplan_id TEXT NOT NULL, version INTEGER NOT NULL,
                body TEXT NOT NULL, request_sha256 TEXT NOT NULL,
                PRIMARY KEY(plan_id, subplan_id, version))""")
            columns = self.connection.execute("PRAGMA table_info(candidates)").fetchall()
            if columns:
                self.connection.execute("ALTER TABLE candidates RENAME TO candidates_v1")
            self.connection.execute("""CREATE TABLE IF NOT EXISTS candidates(
                id TEXT PRIMARY KEY, plan_id TEXT NOT NULL, request_sha256 TEXT NOT NULL,
                body TEXT NOT NULL)""")
            if columns:
                self._copy_legacy_candidates()
                self.connection.execute("DROP TABLE candidates_v1")
            self.connection.execute("""CREATE TABLE IF NOT EXISTS version_reservations(
                plan_id TEXT NOT NULL, subplan_id TEXT NOT NULL, version INTEGER NOT NULL,
                body TEXT NOT NULL, request_sha256 TEXT NOT NULL UNIQUE,
                PRIMARY KEY(plan_id, subplan_id, version))""")
            self.connection.execute("""CREATE TABLE IF NOT EXISTS candidate_reservations(
                id TEXT PRIMARY KEY, plan_id TEXT NOT NULL, request_sha256 TEXT NOT NULL UNIQUE,
                body TEXT NOT NULL)""")
            self.connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS versions_request ON versions(request_sha256)")
            self._backfill_published_at()
            self.connection.execute(f"PRAGMA user_version={self.SCHEMA_VERSION}")
            self.connection.commit()
        except BaseException:
            if self.connection.in_transaction:
                self.connection.rollback()
            self.connection.close()
            raise

    def _copy_legacy_candidates(self) -> None:
        self.connection.execute("INSERT INTO candidates SELECT id,plan_id,request_sha256,body FROM candidates_v1")

    def _backfill_published_at(self) -> None:
        rows = self.connection.execute("SELECT plan_id,subplan_id,version,body FROM versions").fetchall()
        published_at = datetime.now(timezone.utc).isoformat()
        for row in rows:
            body = json.loads(row["body"])
            if "published_at" not in body:
                body["published_at"] = published_at
                self.connection.execute("UPDATE versions SET body=? WHERE plan_id=? AND subplan_id=? AND version=?",
                                        (self._dump(body), row["plan_id"], row["subplan_id"], row["version"]))

    @contextmanager
    def write_transaction(self) -> Iterator[None]:
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.connection.commit()
        except BaseException:
            self.connection.rollback()
            raise

    @staticmethod
    def _dump(value: object) -> str:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @staticmethod
    def _version(row: sqlite3.Row | None) -> SubplanVersion | None:
        if row is None:
            return None
        body = json.loads(row["body"])
        body["evidence"] = tuple(body["evidence"])
        return SubplanVersion(**body)

    @staticmethod
    def _candidate(row: sqlite3.Row | None) -> Candidate | None:
        if row is None:
            return None
        body = json.loads(row["body"])
        body["required_verdicts"] = tuple(body["required_verdicts"])
        body["conflict_paths"] = tuple(body["conflict_paths"])
        body["member_order"] = tuple(body.get("member_order", ()))
        body.setdefault("required_verifiers", None)
        body.setdefault("verdict_proofs", None)
        if body.get("conflicts") is not None:
            body["conflicts"] = {key: tuple(paths) for key, paths in body["conflicts"].items()}
        return Candidate(**body)

    def next_version(self, plan_id: str, subplan_id: str) -> int:
        row = self.connection.execute("""SELECT COALESCE(MAX(version),0)+1 FROM (
            SELECT version FROM versions WHERE plan_id=? AND subplan_id=?
            UNION ALL SELECT version FROM version_reservations WHERE plan_id=? AND subplan_id=?)""",
                                      (plan_id, subplan_id, plan_id, subplan_id)).fetchone()
        return int(row[0])

    def get_version(self, plan_id: str, subplan_id: str, version: int) -> SubplanVersion | None:
        row = self.connection.execute("SELECT body FROM versions WHERE plan_id=? AND subplan_id=? AND version=?",
                                      (plan_id, subplan_id, version)).fetchone()
        return self._version(row)

    def find_version(self, request_sha256: str) -> SubplanVersion | None:
        row = self.connection.execute("SELECT body FROM versions WHERE request_sha256=?", (request_sha256,)).fetchone()
        return self._version(row)

    def find_version_reservation(self, request_sha256: str) -> SubplanVersion | None:
        row = self.connection.execute("SELECT body FROM version_reservations WHERE request_sha256=?",
                                      (request_sha256,)).fetchone()
        return self._version(row)

    def reserve_version(self, version: SubplanVersion, request_sha256: str) -> None:
        body = self._dump({**version.__dict__, "evidence": list(version.evidence)})
        self._execute_write("INSERT INTO version_reservations VALUES(?,?,?,?,?)",
                            (version.plan_id, version.subplan_id, version.version, body, request_sha256))

    def complete_version(self, version: SubplanVersion, request_sha256: str) -> None:
        existing = self.find_version(request_sha256)
        if existing is None:
            body = self._dump({**version.__dict__, "evidence": list(version.evidence)})
            self._execute_write("INSERT INTO versions VALUES(?,?,?,?,?)",
                                (version.plan_id, version.subplan_id, version.version, body, request_sha256))
        self._execute_write("DELETE FROM version_reservations WHERE request_sha256=?", (request_sha256,))

    def put_version(self, version: SubplanVersion, request_sha256: str) -> None:
        body = self._dump({**version.__dict__, "evidence": list(version.evidence)})
        self._execute_write("INSERT INTO versions VALUES(?,?,?,?,?)",
                            (version.plan_id, version.subplan_id, version.version, body, request_sha256))

    def list_versions(self, plan_id: str, subplan_id: str) -> tuple[SubplanVersion, ...]:
        rows = self.connection.execute("SELECT body FROM versions WHERE plan_id=? AND subplan_id=? ORDER BY version",
                                       (plan_id, subplan_id)).fetchall()
        return tuple(self._version(row) for row in rows if row is not None)  # type: ignore[arg-type]

    def get_candidate(self, candidate_id: str) -> Candidate | None:
        row = self.connection.execute("SELECT body FROM candidates WHERE id=?", (candidate_id,)).fetchone()
        return self._candidate(row)

    def candidate_for_commit(self, plan_id: str, commit: str) -> Candidate | None:
        rows = self.connection.execute("SELECT body FROM candidates WHERE plan_id=?", (plan_id,)).fetchall()
        for row in rows:
            candidate = self._candidate(row)
            if candidate is not None and candidate.integrated_commit == commit and candidate.state == "published":
                return candidate
        return None

    def find_candidate(self, request_sha256: str) -> Candidate | None:
        rows = self.connection.execute("SELECT body FROM candidates WHERE request_sha256=?", (request_sha256,)).fetchall()
        for row in rows:
            candidate = self._candidate(row)
            if candidate is not None and candidate.state in ("candidate", "verifying", "published"):
                return candidate
        return None

    def next_candidate(self, plan_id: str) -> int:
        rows = self.connection.execute("SELECT id FROM candidates WHERE plan_id=? UNION ALL "
                                       "SELECT id FROM candidate_reservations WHERE plan_id=?",
                                       (plan_id, plan_id)).fetchall()
        return max((int(row["id"].rsplit("C", 1)[1]) for row in rows), default=0) + 1

    def find_candidate_reservation(self, request_sha256: str) -> Candidate | None:
        row = self.connection.execute("SELECT body FROM candidate_reservations WHERE request_sha256=?",
                                      (request_sha256,)).fetchone()
        return self._candidate(row)

    def reserve_candidate(self, candidate: Candidate, request_sha256: str) -> None:
        self._execute_write("INSERT INTO candidate_reservations VALUES(?,?,?,?)",
                            (candidate.id, candidate.plan_id, request_sha256, self._dump(candidate.__dict__)))

    def complete_candidate(self, candidate: Candidate, request_sha256: str) -> None:
        if self.get_candidate(candidate.id) is None:
            self._execute_write("INSERT INTO candidates VALUES(?,?,?,?)",
                                (candidate.id, candidate.plan_id, request_sha256, self._dump(candidate.__dict__)))
        self._execute_write("DELETE FROM candidate_reservations WHERE request_sha256=?", (request_sha256,))

    def put_candidate(self, candidate: Candidate, request_sha256: str) -> None:
        body = self._dump(candidate.__dict__)
        self._execute_write("INSERT INTO candidates VALUES(?,?,?,?)",
                            (candidate.id, candidate.plan_id, request_sha256, body))

    def update_candidate(self, candidate: Candidate) -> None:
        self._execute_write("UPDATE candidates SET body=? WHERE id=?",
                            (self._dump(candidate.__dict__), candidate.id))

    def _execute_write(self, statement: str, values: tuple[object, ...]) -> None:
        if self.connection.in_transaction:
            self.connection.execute(statement, values)
            return
        with self.connection:
            self.connection.execute(statement, values)

    def close(self) -> None:
        self.connection.close()


__all__ = ["Store"]
