"""Append-only diagnostic case/event storage with generation-fenced writes."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Self

from .diagnostic_contracts import DiagnosticCase, RecoveryProposal
from .history import APP_ID, _check_schema, _json, _migrate_schema, _private_path, _store_error
from .validation import RecoveryError, identifier, integer, number, require


class DiagnosticStore:
    def __init__(self, path: str | Path, *, timeout_seconds: float = 2):
        number(timeout_seconds, 0.001, 30)
        self.connection: sqlite3.Connection | None = None
        try:
            target = Path(path).absolute()
            _private_path(target)
            self.connection = sqlite3.connect(target, timeout=timeout_seconds, isolation_level=None)
            self.connection.execute("PRAGMA synchronous=FULL")
            self.connection.execute("BEGIN IMMEDIATE")
            tables = self.connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            if not tables:
                # Keep schema-1 decision ownership intact; the shared migration adds diagnostic tables.
                from .history import SCHEMA
                for statement in SCHEMA.split(";"):
                    if statement.strip():
                        self.connection.execute(statement)
                self.connection.execute(f"PRAGMA application_id={APP_ID}")
                self.connection.execute("PRAGMA user_version=1")
            _migrate_schema(self.connection)
            _check_schema(self.connection)
            self.connection.commit()
        except (OSError, sqlite3.Error) as error:
            self.close()
            raise _store_error(error) from None
        except RecoveryError:
            self.close()
            raise

    def create_case(self, case: DiagnosticCase, proposal: RecoveryProposal, *, now: float) -> dict:
        require(type(case) is DiagnosticCase and type(proposal) is RecoveryProposal)
        number(now)
        require(proposal.trigger_id == case.trigger_id and proposal.generation == 0, "CASE_CONFLICT")
        connection = self._open()
        case_json = _json(case.to_dict())
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT case_json,generation FROM recovery_cases WHERE trigger_id=?",
                                     (case.trigger_id,)).fetchone()
            if row:
                require(row[0] == case_json, "CASE_CONFLICT")
                initial = connection.execute("SELECT payload_json FROM recovery_events WHERE trigger_id=? "
                                             "AND event_type='case_created' ORDER BY seq LIMIT 1",
                                             (case.trigger_id,)).fetchone()
                require(initial is not None and json.loads(initial[0])["proposal"] == proposal.to_dict(),
                        "CASE_CONFLICT")
                connection.commit()
                return {"trigger_id": case.trigger_id, "generation": row[1], "created": False}
            connection.execute("INSERT INTO recovery_cases(trigger_id,generation,case_json) VALUES(?,0,?)",
                               (case.trigger_id, case_json))
            connection.execute("INSERT INTO recovery_events(event_id,trigger_id,generation,event_type,payload_json,created_at) "
                               "VALUES(?,?,0,'case_created',?,?)",
                               (_event_id(case.trigger_id, "created"), case.trigger_id,
                                _json({"case": case.to_dict(), "proposal": proposal.to_dict()}), now))
            connection.commit()
            return {"trigger_id": case.trigger_id, "generation": 0, "created": True}
        except RecoveryError:
            connection.rollback()
            raise
        except (sqlite3.Error, ValueError, TypeError) as error:
            connection.rollback()
            raise _store_error(error) from None

    def get_case(self, trigger_id: str) -> dict | None:
        identifier(trigger_id)
        try:
            row = self._open().execute("SELECT generation,case_json FROM recovery_cases WHERE trigger_id=?",
                                       (trigger_id,)).fetchone()
            return {"trigger_id": trigger_id, "generation": row[0], "case": json.loads(row[1])} if row else None
        except (sqlite3.Error, ValueError, TypeError) as error:
            raise _store_error(error) from None

    def events(self, trigger_id: str) -> list[dict]:
        identifier(trigger_id)
        try:
            rows = self._open().execute(
                "SELECT event_id,generation,event_type,payload_json,created_at FROM recovery_events "
                "WHERE trigger_id=? ORDER BY seq", (trigger_id,)).fetchall()
            return [{"event_id": row[0], "generation": row[1], "event_type": row[2],
                     "payload": json.loads(row[3]), "created_at": row[4]} for row in rows]
        except (sqlite3.Error, ValueError, TypeError) as error:
            raise _store_error(error) from None

    def acquire_lease(self, trigger_id: str, expected_generation: int, owner_id: str,
                      *, now: float, lease_seconds: float) -> dict:
        identifier(trigger_id)
        identifier(owner_id)
        integer(expected_generation)
        number(now)
        number(lease_seconds, 1, 86400)
        connection = self._open()
        try:
            connection.execute("BEGIN IMMEDIATE")
            case = connection.execute("SELECT generation FROM recovery_cases WHERE trigger_id=?", (trigger_id,)).fetchone()
            require(case is not None and case[0] == expected_generation, "GENERATION_CONFLICT")
            lease = connection.execute("SELECT generation,owner_id,expires_at FROM recovery_leases WHERE trigger_id=?",
                                       (trigger_id,)).fetchone()
            require(lease is None or lease[2] <= now or (lease[0] == expected_generation and lease[1] == owner_id),
                    "LEASE_HELD")
            expires_at = now + lease_seconds
            connection.execute("INSERT INTO recovery_leases(trigger_id,generation,owner_id,expires_at) VALUES(?,?,?,?) "
                               "ON CONFLICT(trigger_id) DO UPDATE SET generation=excluded.generation,"
                               "owner_id=excluded.owner_id,expires_at=excluded.expires_at",
                               (trigger_id, expected_generation, owner_id, expires_at))
            connection.commit()
            return {"trigger_id": trigger_id, "generation": expected_generation,
                    "owner_id": owner_id, "expires_at": expires_at}
        except RecoveryError:
            connection.rollback()
            raise
        except (sqlite3.Error, ValueError, TypeError) as error:
            connection.rollback()
            raise _store_error(error) from None

    def transition(self, trigger_id: str, expected_generation: int, owner_id: str, event_id: str,
                   event_type: str, payload: dict, *, now: float) -> int:
        identifier(trigger_id)
        integer(expected_generation)
        identifier(owner_id)
        identifier(event_id)
        identifier(event_type)
        require(type(payload) is dict)
        number(now)
        connection = self._open()
        try:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute("SELECT trigger_id,generation,event_type,payload_json FROM recovery_events "
                                          "WHERE event_id=?", (event_id,)).fetchone()
            if existing:
                require(existing == (trigger_id, expected_generation + 1, event_type, _json(payload)),
                        "EVENT_CONFLICT")
                connection.commit()
                return existing[1]
            row = connection.execute("SELECT generation FROM recovery_cases WHERE trigger_id=?", (trigger_id,)).fetchone()
            lease = connection.execute("SELECT generation,owner_id,expires_at FROM recovery_leases WHERE trigger_id=?",
                                       (trigger_id,)).fetchone()
            require(row is not None and row[0] == expected_generation, "GENERATION_CONFLICT")
            require(lease is not None and lease[0] == expected_generation and lease[1] == owner_id and lease[2] > now,
                    "LEASE_LOST")
            next_generation = expected_generation + 1
            connection.execute("INSERT INTO recovery_events(event_id,trigger_id,generation,event_type,payload_json,created_at) "
                               "VALUES(?,?,?,?,?,?)", (event_id, trigger_id, next_generation,
                                                      event_type, _json(payload), now))
            updated = connection.execute("UPDATE recovery_cases SET generation=? WHERE trigger_id=? AND generation=?",
                                         (next_generation, trigger_id, expected_generation))
            require(updated.rowcount == 1, "GENERATION_CONFLICT")
            connection.execute("DELETE FROM recovery_leases WHERE trigger_id=? AND generation=? AND owner_id=?",
                               (trigger_id, expected_generation, owner_id))
            connection.commit()
            return next_generation
        except RecoveryError:
            connection.rollback()
            raise
        except (sqlite3.Error, ValueError, TypeError) as error:
            connection.rollback()
            raise _store_error(error) from None

    def checkpoint_application(self, trigger_id: str, generation: int, owner_id: str, checkpoint_id: str,
                               checkpoint: dict, *, now: float) -> bool:
        identifier(trigger_id)
        integer(generation)
        identifier(owner_id)
        identifier(checkpoint_id)
        require(type(checkpoint) is dict)
        number(now)
        connection = self._open()
        try:
            connection.execute("BEGIN IMMEDIATE")
            old = connection.execute("SELECT trigger_id,generation,checkpoint_json FROM application_checkpoints "
                                     "WHERE checkpoint_id=?", (checkpoint_id,)).fetchone()
            encoded = _json(checkpoint)
            if old:
                require(old == (trigger_id, generation, encoded), "CHECKPOINT_CONFLICT")
                connection.commit()
                return False
            case = connection.execute("SELECT generation FROM recovery_cases WHERE trigger_id=?", (trigger_id,)).fetchone()
            lease = connection.execute("SELECT generation,owner_id,expires_at FROM recovery_leases WHERE trigger_id=?",
                                       (trigger_id,)).fetchone()
            require(case is not None and case[0] == generation, "GENERATION_CONFLICT")
            require(lease is not None and lease[0] == generation and lease[1] == owner_id and lease[2] > now,
                    "LEASE_LOST")
            connection.execute("INSERT INTO application_checkpoints VALUES(?,?,?,?,?)",
                               (checkpoint_id, trigger_id, generation, encoded, now))
            connection.execute("INSERT INTO recovery_events(event_id,trigger_id,generation,event_type,payload_json,created_at) "
                               "VALUES(?,?,?,'application_checkpoint',?,?)",
                               (checkpoint_id, trigger_id, generation, encoded, now))
            connection.commit()
            return True
        except RecoveryError:
            connection.rollback()
            raise
        except (sqlite3.Error, ValueError, TypeError) as error:
            connection.rollback()
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


def _event_id(trigger_id: str, name: str) -> str:
    import hashlib
    return hashlib.sha256(f"{trigger_id}:{name}".encode()).hexdigest()
