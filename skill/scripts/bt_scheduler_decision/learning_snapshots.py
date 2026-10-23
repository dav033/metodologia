"""Append-only storage for bounded, redacted contextual learning snapshots."""
from __future__ import annotations

import json
import math
import re
import sqlite3
import unicodedata
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from .contracts import API_VERSION
from .history import PerformanceContext, aggregate_performance_history
from .identity import canonical_json, sha256_json
from .ledger_errors import DecisionLedgerError
from .performance_events import PerformanceEvent, reduce_performance_events

LEARNING_SNAPSHOT_LEDGER_SCHEMA_VERSION = 2
CURRENT_LEDGER_SCHEMA_VERSION = 3
LEGACY_LEDGER_SCHEMA_VERSION = 1
MAX_LEARNING_SNAPSHOTS = 10_000
MAX_LEARNING_SNAPSHOT_BYTES = 32_768
MAX_LEARNING_SOURCE_EVENTS = 100_000
MAX_LEARNING_CONTEXTS = 100_000
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_POLICY_VERSION = re.compile(r"[a-z][a-z0-9._-]{0,63}\Z")
_SNAPSHOT_FIELDS = {
    "schema_version", "source_fingerprint", "route_id", "policy_version", "learning_cutoff",
    "source_event_count", "source_context_count", "target_context", "assessment",
}
_ASSESSMENT_FIELDS = {
    "schema_version", "route_id", "minimum_verified_samples", "measurements", "selected_level",
    "selected_shrunk_feature", "fallback_reasons",
}
_MEASUREMENT_FIELDS = {
    "schema_version", "level", "attempt_count", "verified_samples", "verified_successes",
    "verified_failures", "claimed_unverified", "cancelled", "infrastructure_failures", "unknown", "coverage",
    "observed_rate", "uncertainty_interval_95", "shrunk_feature", "source_quality",
}
_LEVELS = ("exact_context", "complexity_class", "task_family", "route")
_SELECTED_LEVELS = {*_LEVELS, "baseline"}
_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS learning_snapshots (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    source_fingerprint TEXT NOT NULL UNIQUE CHECK(length(source_fingerprint) = 64),
    snapshot_sha256 TEXT NOT NULL CHECK(length(snapshot_sha256) = 64),
    route_id TEXT NOT NULL CHECK(length(route_id) = 64),
    created_at REAL NOT NULL,
    snapshot_json TEXT NOT NULL
)
"""
_CREATE_INDEX_SQL = "CREATE INDEX IF NOT EXISTS learning_snapshots_route_latest ON learning_snapshots(route_id, seq DESC)"
_CREATE_UPDATE_TRIGGER_SQL = """
CREATE TRIGGER IF NOT EXISTS learning_snapshots_immutable_update
BEFORE UPDATE ON learning_snapshots
BEGIN SELECT RAISE(ABORT, 'learning snapshots are immutable'); END
"""
_CREATE_DELETE_TRIGGER_SQL = """
CREATE TRIGGER IF NOT EXISTS learning_snapshots_immutable_delete
BEFORE DELETE ON learning_snapshots
BEGIN SELECT RAISE(ABORT, 'learning snapshots are immutable'); END
"""


@dataclass(frozen=True)
class LearningSnapshot:
    """Immutable serialized result; `to_dict()` returns a fresh redacted projection."""

    source_fingerprint: str
    created_at: float
    snapshot_json: str

    def to_dict(self) -> dict[str, object]:
        snapshot = json.loads(self.snapshot_json)
        return {**snapshot, "created_at": self.created_at}


def create_learning_snapshot_table(connection: sqlite3.Connection) -> None:
    """Install the append-only table and guards in a new ledger or an additive migration."""
    connection.execute(_CREATE_TABLE_SQL)
    connection.execute(_CREATE_INDEX_SQL)
    connection.execute(_CREATE_UPDATE_TRIGGER_SQL)
    connection.execute(_CREATE_DELETE_TRIGGER_SQL)


def migrate_legacy_ledger(connection: sqlite3.Connection) -> None:
    """Add snapshot storage to a verified schema-1 ledger without rewriting decision records."""
    try:
        connection.execute("BEGIN IMMEDIATE")
        create_learning_snapshot_table(connection)
        connection.execute(f"PRAGMA user_version = {LEARNING_SNAPSHOT_LEDGER_SCHEMA_VERSION}")
        connection.execute("COMMIT")
    except sqlite3.Error:
        if connection.in_transaction:
            connection.execute("ROLLBACK")
        raise


def _valid_epoch(value: object) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value) and value >= 0
    except OverflowError:
        return False


def _snapshot_from_row(source_fingerprint: object, snapshot_sha256: object, created_at: object,
                       snapshot_json: object) -> LearningSnapshot:
    try:
        if not isinstance(source_fingerprint, str) or not _SHA256.fullmatch(source_fingerprint) or \
                not isinstance(snapshot_sha256, str) or not _SHA256.fullmatch(snapshot_sha256) or \
                not _valid_epoch(created_at) or not isinstance(snapshot_json, str) or \
                len(snapshot_json.encode("utf-8", errors="strict")) > MAX_LEARNING_SNAPSHOT_BYTES:
            raise ValueError("snapshot row invalid")
        raw = json.loads(snapshot_json)
        if not isinstance(raw, dict) or set(raw) != _SNAPSHOT_FIELDS or \
                raw["schema_version"] != API_VERSION or raw["source_fingerprint"] != source_fingerprint or \
                not isinstance(raw["route_id"], str) or not _SHA256.fullmatch(raw["route_id"]) or \
                not isinstance(raw["policy_version"], str) or not _POLICY_VERSION.fullmatch(raw["policy_version"]) or \
                not _valid_epoch(raw["learning_cutoff"]) or \
                not isinstance(raw["source_event_count"], int) or isinstance(raw["source_event_count"], bool) or \
                not 0 <= raw["source_event_count"] <= MAX_LEARNING_SOURCE_EVENTS or \
                not isinstance(raw["source_context_count"], int) or isinstance(raw["source_context_count"], bool) or \
                not 0 <= raw["source_context_count"] <= MAX_LEARNING_CONTEXTS:
            raise ValueError("snapshot fields invalid")
        PerformanceContext.from_dict(raw["target_context"])
        assessment = raw["assessment"]
        if not isinstance(assessment, dict) or set(assessment) != _ASSESSMENT_FIELDS or \
                assessment["schema_version"] != API_VERSION or assessment["route_id"] != raw["route_id"] or \
                not isinstance(assessment["minimum_verified_samples"], int) or \
                isinstance(assessment["minimum_verified_samples"], bool) or \
                assessment["minimum_verified_samples"] < 1 or \
                assessment["selected_level"] not in _SELECTED_LEVELS or \
                not isinstance(assessment["measurements"], list) or len(assessment["measurements"]) != len(_LEVELS) or \
                not isinstance(assessment["fallback_reasons"], list) or \
                any(not isinstance(reason, str) or len(reason) > 64 for reason in assessment["fallback_reasons"]):
            raise ValueError("assessment fields invalid")
        for level, measurement in zip(_LEVELS, assessment["measurements"]):
            if not isinstance(measurement, dict) or set(measurement) != _MEASUREMENT_FIELDS or \
                    measurement["schema_version"] != API_VERSION or measurement["level"] != level:
                raise ValueError("measurement fields invalid")
        if canonical_json(raw) != snapshot_json or sha256_json(raw) != snapshot_sha256:
            raise ValueError("snapshot checksum invalid")
        return LearningSnapshot(source_fingerprint, float(created_at), snapshot_json)
    except DecisionLedgerError:
        raise
    except (KeyError, TypeError, ValueError, UnicodeEncodeError) as exc:
        raise DecisionLedgerError("learning_snapshot_corrupt") from exc


class LearningSnapshotStore:
    """Idempotent append-only snapshot storage sharing the decision ledger's SQLite file."""

    def __init__(self, connection_factory: Callable[[bool], sqlite3.Connection], *, writable: bool,
                 schema_version: int):
        self._connection_factory = connection_factory
        self._writable = writable
        self._schema_version = schema_version

    def _prepare(self, events: Sequence[PerformanceEvent],
                 contexts: Mapping[tuple[str, int, str], PerformanceContext], *, route_id: str,
                 target_context: PerformanceContext, policy_version: str, learning_cutoff: float
                 ) -> tuple[str, str, str]:
        if not isinstance(policy_version, str) or not _POLICY_VERSION.fullmatch(policy_version) or \
                not _valid_epoch(learning_cutoff) or not isinstance(contexts, Mapping) or \
                len(contexts) > MAX_LEARNING_CONTEXTS or isinstance(events, (str, bytes)) or \
                not isinstance(events, Sequence) or len(events) > MAX_LEARNING_SOURCE_EVENTS:
            raise DecisionLedgerError("learning_snapshot_invalid")
        try:
            event_snapshot = tuple(events)
            context_snapshot = dict(contexts)
            reduced_events = reduce_performance_events(event_snapshot)
            target = PerformanceContext.from_dict(target_context.to_dict())
            assessment = aggregate_performance_history(
                reduced_events, context_snapshot, route_id=route_id, target_context=target,
            )
            event_hashes = sorted(sha256_json(event.to_dict()) for event in reduced_events)
            context_hashes = []
            for key, value in context_snapshot.items():
                identity = (unicodedata.normalize("NFC", key[0].strip()), key[1],
                            unicodedata.normalize("NFC", key[2].strip()))
                context = PerformanceContext.from_dict(value.to_dict())
                context_hashes.append(sha256_json({"identity": identity, "context": context.to_dict()}))
            context_hashes.sort()
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            raise DecisionLedgerError("learning_snapshot_invalid") from exc

        cutoff = float(learning_cutoff)
        fingerprint = sha256_json({
            "schema_version": API_VERSION,
            "policy_version": policy_version,
            "learning_cutoff": cutoff,
            "route_id": route_id,
            "target_context": target.to_dict(),
            "source_event_hashes": event_hashes,
            "source_context_hashes": context_hashes,
            "assessment": assessment.to_dict(),
        })
        snapshot = {
            "schema_version": API_VERSION,
            "source_fingerprint": fingerprint,
            "route_id": route_id,
            "policy_version": policy_version,
            "learning_cutoff": cutoff,
            "source_event_count": len(reduced_events),
            "source_context_count": len(context_snapshot),
            "target_context": target.to_dict(),
            "assessment": assessment.to_dict(),
        }
        payload = canonical_json(snapshot)
        if len(payload.encode("utf-8")) > MAX_LEARNING_SNAPSHOT_BYTES:
            raise DecisionLedgerError("learning_snapshot_too_large")
        return fingerprint, payload, route_id

    def persist(self, events: Sequence[PerformanceEvent],
                contexts: Mapping[tuple[str, int, str], PerformanceContext], *, route_id: str,
                target_context: PerformanceContext, policy_version: str, learning_cutoff: float,
                created_at: float) -> LearningSnapshot:
        """Store one deterministic aggregate per normalized source fingerprint; duplicates keep first bytes/time."""
        if not self._writable:
            raise DecisionLedgerError("read_only")
        if self._schema_version != CURRENT_LEDGER_SCHEMA_VERSION:
            raise DecisionLedgerError("learning_snapshot_schema_unavailable")
        if not _valid_epoch(created_at):
            raise DecisionLedgerError("learning_snapshot_invalid")
        fingerprint, payload, normalized_route_id = self._prepare(
            events, contexts, route_id=route_id, target_context=target_context,
            policy_version=policy_version, learning_cutoff=learning_cutoff,
        )
        snapshot_hash = sha256_json(json.loads(payload))
        try:
            connection = self._connection_factory(False)
        except sqlite3.Error as exc:
            raise DecisionLedgerError("ledger_unavailable") from exc
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT snapshot_sha256, created_at, snapshot_json FROM learning_snapshots "
                "WHERE source_fingerprint = ?", (fingerprint,),
            ).fetchone()
            if row:
                if row[0] != snapshot_hash or row[2] != payload:
                    raise DecisionLedgerError("learning_snapshot_fingerprint_conflict")
                connection.execute("COMMIT")
                return _snapshot_from_row(fingerprint, row[0], row[1], row[2])
            count = connection.execute("SELECT COUNT(*) FROM learning_snapshots").fetchone()[0]
            if count >= MAX_LEARNING_SNAPSHOTS:
                raise DecisionLedgerError("learning_snapshot_store_full")
            connection.execute(
                "INSERT INTO learning_snapshots(source_fingerprint,snapshot_sha256,route_id,created_at,snapshot_json) "
                "VALUES(?,?,?,?,?)", (fingerprint, snapshot_hash, normalized_route_id, float(created_at), payload),
            )
            connection.execute("COMMIT")
            return _snapshot_from_row(fingerprint, snapshot_hash, float(created_at), payload)
        except DecisionLedgerError:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        except sqlite3.Error as exc:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise DecisionLedgerError("ledger_unavailable") from exc
        finally:
            connection.close()

    def get(self, source_fingerprint: str) -> LearningSnapshot | None:
        """Read one immutable snapshot by its content-addressed source fingerprint."""
        if not isinstance(source_fingerprint, str) or not _SHA256.fullmatch(source_fingerprint):
            raise DecisionLedgerError("learning_snapshot_invalid")
        if self._schema_version == LEGACY_LEDGER_SCHEMA_VERSION:
            return None
        try:
            connection = self._connection_factory(True)
        except sqlite3.Error as exc:
            raise DecisionLedgerError("ledger_unavailable") from exc
        try:
            row = connection.execute(
                "SELECT snapshot_sha256, created_at, snapshot_json FROM learning_snapshots "
                "WHERE source_fingerprint = ?", (source_fingerprint,),
            ).fetchone()
        except sqlite3.Error as exc:
            raise DecisionLedgerError("ledger_unavailable") from exc
        finally:
            connection.close()
        if row is None:
            return None
        return _snapshot_from_row(source_fingerprint, row[0], row[1], row[2])
