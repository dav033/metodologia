"""Append-only persistence for deterministic READY-batch decisions."""
from __future__ import annotations

import json
import math
import re
import sqlite3
from collections.abc import Callable, Mapping, Sequence

from .batch import (
    BATCH_POLICY_VERSION,
    MAX_BATCH_CANDIDATES,
    MAX_BATCH_TASKS,
    AccountConcurrency,
    BatchAssignment,
    BatchPlan,
    BatchRouteExclusion,
    BatchUnassignment,
    plan_ready_batch,
)
from .batch_quota_evidence import (
    BATCH_EVIDENCE_VERSION,
    BATCH_PLAN_SCHEMA_VERSION,
    BatchQuotaEvidence,
)
from .contracts import API_VERSION, EXCLUSION_REASON_CODES, DecisionRequest
from .identity import canonical_json, sha256_json
from .learning_snapshots import CURRENT_LEDGER_SCHEMA_VERSION
from .ledger_errors import DecisionLedgerError
from .policy import (
    DEFAULT_ROUTE_POLICY,
    ROUTE_POLICY_VERSION,
    RoutePolicyConfig,
    RoutePolicyEvidence,
)

MAX_BATCH_RECORDS = 10_000
MAX_BATCH_RECORD_BYTES = 2_097_152
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_ACCOUNT_REF = re.compile(r"acct:[0-9a-f]{64}\Z")
_BATCH_ASSIGNMENT_REASONS = {"route_policy_preferred", "account_capacity_alternative"}
_BATCH_UNASSIGNMENT_REASONS = {
    "no_eligible_route", "quality_floor_no_supported_route", "free_slots_exhausted",
    "account_concurrency_exhausted",
}
_BATCH_EXCLUSION_REASONS = {*EXCLUSION_REASON_CODES, "quality_floor_not_met", "quality_evidence_insufficient"}
_BATCH_PLAN_FIELDS = {
    "schema_version", "batch_policy_version", "route_policy_version", "batch_id", "input_sha256",
    "free_slots", "considered_task_count", "assignments", "unassigned", "route_exclusions",
}
_LEGACY_BATCH_PLAN_FIELDS = _BATCH_PLAN_FIELDS
_BATCH_PLAN_FIELDS = {*_BATCH_PLAN_FIELDS, "quota_evidence"}
_LEGACY_BATCH_POLICY_VERSION = "m2-bounded-batch-v1"

_CREATE_BATCH_DECISIONS_SQL = """
CREATE TABLE IF NOT EXISTS batch_decisions (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id TEXT NOT NULL UNIQUE CHECK(length(batch_id) = 64),
    input_sha256 TEXT NOT NULL UNIQUE CHECK(length(input_sha256) = 64),
    plan_sha256 TEXT NOT NULL CHECK(length(plan_sha256) = 64),
    plan_json TEXT NOT NULL
)
"""
_CREATE_BATCH_UPDATE_TRIGGER_SQL = """
CREATE TRIGGER IF NOT EXISTS batch_decisions_immutable_update
BEFORE UPDATE ON batch_decisions
BEGIN SELECT RAISE(ABORT, 'batch decisions are immutable'); END
"""
_CREATE_BATCH_DELETE_TRIGGER_SQL = """
CREATE TRIGGER IF NOT EXISTS batch_decisions_immutable_delete
BEFORE DELETE ON batch_decisions
BEGIN SELECT RAISE(ABORT, 'batch decisions are immutable'); END
"""


def create_batch_decision_table(connection: sqlite3.Connection) -> None:
    """Install immutable batch-decision storage in a new ledger."""
    connection.execute(_CREATE_BATCH_DECISIONS_SQL)
    connection.execute(_CREATE_BATCH_UPDATE_TRIGGER_SQL)
    connection.execute(_CREATE_BATCH_DELETE_TRIGGER_SQL)


def migrate_schema_two_ledger(connection: sqlite3.Connection) -> None:
    """Add batch decisions to a schema-2 ledger without rewriting decisions or learning snapshots."""
    try:
        connection.execute("BEGIN IMMEDIATE")
        create_batch_decision_table(connection)
        connection.execute(f"PRAGMA user_version = {CURRENT_LEDGER_SCHEMA_VERSION}")
        connection.execute("COMMIT")
    except sqlite3.Error:
        if connection.in_transaction:
            connection.execute("ROLLBACK")
        raise


def _valid_task_id(value: object) -> bool:
    return isinstance(value, str) and 0 < len(value) <= 128


def _decode_batch_plan(payload: str, expected_sha256: object) -> BatchPlan:
    try:
        if (not isinstance(payload, str) or len(payload.encode("utf-8", errors="strict")) > MAX_BATCH_RECORD_BYTES or
                not isinstance(expected_sha256, str) or not _SHA256.fullmatch(expected_sha256)):
            raise ValueError("batch payload bounds")
        raw = json.loads(payload)
        if not isinstance(raw, dict) or set(raw) not in (_LEGACY_BATCH_PLAN_FIELDS, _BATCH_PLAN_FIELDS) or \
                raw["batch_policy_version"] not in {
                    _LEGACY_BATCH_POLICY_VERSION, BATCH_POLICY_VERSION,
                } or \
                raw["schema_version"] != (API_VERSION if raw["batch_policy_version"] == _LEGACY_BATCH_POLICY_VERSION
                                          else BATCH_PLAN_SCHEMA_VERSION) or \
                (raw["batch_policy_version"] == BATCH_POLICY_VERSION) != ("quota_evidence" in raw) or \
                raw["route_policy_version"] != ROUTE_POLICY_VERSION or \
                not isinstance(raw["batch_id"], str) or not _SHA256.fullmatch(raw["batch_id"]) or \
                not isinstance(raw["input_sha256"], str) or not _SHA256.fullmatch(raw["input_sha256"]) or \
                not isinstance(raw["free_slots"], int) or isinstance(raw["free_slots"], bool) or \
                raw["free_slots"] < 1 or not isinstance(raw["considered_task_count"], int) or \
                isinstance(raw["considered_task_count"], bool) or \
                not 1 <= raw["considered_task_count"] <= MAX_BATCH_TASKS or \
                not isinstance(raw["assignments"], list) or len(raw["assignments"]) > MAX_BATCH_TASKS or \
                not isinstance(raw["unassigned"], list) or len(raw["unassigned"]) > MAX_BATCH_TASKS or \
                not isinstance(raw["route_exclusions"], list) or len(raw["route_exclusions"]) > MAX_BATCH_CANDIDATES:
            raise ValueError("batch payload fields")

        assignments = tuple(_decode_assignment(row) for row in raw["assignments"])
        unassigned = tuple(_decode_unassignment(row) for row in raw["unassigned"])
        exclusions = tuple(_decode_route_exclusion(row) for row in raw["route_exclusions"])
        assigned_ids = tuple(row.task_id for row in assignments)
        unassigned_ids = tuple(row.task_id for row in unassigned)
        if (assigned_ids != tuple(sorted(assigned_ids)) or unassigned_ids != tuple(sorted(unassigned_ids)) or
                len(set(assigned_ids)) != len(assigned_ids) or len(set(unassigned_ids)) != len(unassigned_ids) or
                set(assigned_ids) & set(unassigned_ids) or
                len(assigned_ids) + len(unassigned_ids) != raw["considered_task_count"] or
                len(assigned_ids) > raw["free_slots"]):
            raise ValueError("batch task assignments invalid")
        known_tasks = set(assigned_ids) | set(unassigned_ids)
        exclusion_keys = tuple((row.task_id, row.route_id) for row in exclusions)
        if (exclusion_keys != tuple(sorted(exclusion_keys)) or len(set(exclusion_keys)) != len(exclusion_keys) or
                any(task_id not in known_tasks for task_id, _ in exclusion_keys) or
                any((row.task_id, row.route_id) in set(exclusion_keys) for row in assignments)):
            raise ValueError("batch route exclusions invalid")
        quota_evidence = tuple(_decode_quota_evidence(row) for row in raw.get("quota_evidence", []))
        evidence_keys = tuple((row.task_id, row.route_id) for row in quota_evidence)
        if evidence_keys != tuple(sorted(evidence_keys)) or len(set(evidence_keys)) != len(evidence_keys) or \
                any(task_id not in known_tasks for task_id, _ in evidence_keys):
            raise ValueError("batch quota evidence invalid")
        plan = BatchPlan(
            raw["schema_version"], raw["batch_policy_version"], raw["route_policy_version"], raw["batch_id"],
            raw["input_sha256"], raw["free_slots"], raw["considered_task_count"], assignments, unassigned,
            exclusions, quota_evidence,
        )
        if (canonical_json(raw) != payload or sha256_json(raw) != expected_sha256 or
                plan.batch_id != sha256_json({"batch_policy_version": raw["batch_policy_version"],
                                               "input_sha256": plan.input_sha256})):
            raise ValueError("batch payload integrity")
        return plan
    except DecisionLedgerError:
        raise
    except (KeyError, TypeError, ValueError, UnicodeEncodeError) as exc:
        raise DecisionLedgerError("batch_decision_corrupt") from exc


def _decode_assignment(value: object) -> BatchAssignment:
    if not isinstance(value, dict) or set(value) != {"task_id", "route_id", "account_ref", "route_policy_rank",
                                                   "reason_code"} or \
            not _valid_task_id(value["task_id"]) or not isinstance(value["route_id"], str) or \
            not _SHA256.fullmatch(value["route_id"]) or not isinstance(value["account_ref"], str) or \
            not _ACCOUNT_REF.fullmatch(value["account_ref"]) or \
            not isinstance(value["route_policy_rank"], int) or isinstance(value["route_policy_rank"], bool) or \
            not 1 <= value["route_policy_rank"] <= 256 or \
            value["reason_code"] not in _BATCH_ASSIGNMENT_REASONS or \
            (value["route_policy_rank"] == 1) != (value["reason_code"] == "route_policy_preferred"):
        raise DecisionLedgerError("batch_decision_corrupt")
    return BatchAssignment(value["task_id"], value["route_id"], value["account_ref"],
                           value["route_policy_rank"], value["reason_code"])


def _decode_unassignment(value: object) -> BatchUnassignment:
    if not isinstance(value, dict) or set(value) != {"task_id", "reason_code"} or \
            not _valid_task_id(value["task_id"]) or value["reason_code"] not in _BATCH_UNASSIGNMENT_REASONS:
        raise DecisionLedgerError("batch_decision_corrupt")
    return BatchUnassignment(value["task_id"], value["reason_code"])


def _decode_route_exclusion(value: object) -> BatchRouteExclusion:
    if not isinstance(value, dict) or set(value) != {"task_id", "route_id", "reason_codes"} or \
            not _valid_task_id(value["task_id"]) or not isinstance(value["route_id"], str) or \
            not _SHA256.fullmatch(value["route_id"]) or not isinstance(value["reason_codes"], list) or \
            not 1 <= len(value["reason_codes"]) <= 16 or \
            any(not isinstance(reason, str) or reason not in _BATCH_EXCLUSION_REASONS
                for reason in value["reason_codes"]) or \
            value["reason_codes"] != sorted(set(value["reason_codes"])):
        raise DecisionLedgerError("batch_decision_corrupt")
    return BatchRouteExclusion(value["task_id"], value["route_id"], tuple(value["reason_codes"]))


def _decode_quota_evidence(value: object) -> BatchQuotaEvidence:
    fields = {"schema_version", "task_id", "route_id", "profile", "account_ref", "state", "observed_at", "valid_until",
              "used_percent", "reason_code"}
    if not isinstance(value, dict) or set(value) != fields or value["schema_version"] != BATCH_EVIDENCE_VERSION or \
            not _valid_task_id(value["task_id"]) or \
            not isinstance(value["route_id"], str) or not _SHA256.fullmatch(value["route_id"]) or \
            not isinstance(value["account_ref"], str) or not _ACCOUNT_REF.fullmatch(value["account_ref"]) or \
            value["state"] not in {"fresh", "stale", "missing", "malformed", "refresh_failed", "exhausted"} or \
            not isinstance(value["profile"], str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}",
                                                                      value["profile"]) or \
            value["reason_code"] not in {
                "quota_fresh", "quota_observation_stale", "quota_observation_missing", "quota_data_malformed",
                "quota_refresh_failed", "quota_exhausted", "preflight_account_limit_exceeded",
            }:
        raise DecisionLedgerError("batch_decision_corrupt")
    for field in ("observed_at", "valid_until", "used_percent"):
        number = value[field]
        if number is not None and (not isinstance(number, (int, float)) or isinstance(number, bool) or
                                   not math.isfinite(number)):
            raise DecisionLedgerError("batch_decision_corrupt")
    if (value["observed_at"] is not None and value["observed_at"] < 0 or
            value["valid_until"] is not None and value["valid_until"] < 0 or
            value["used_percent"] is not None and not 0 <= value["used_percent"] <= 100 or
            value["state"] == "fresh" and (value["observed_at"] is None or value["valid_until"] is None or
                                             value["valid_until"] <= value["observed_at"] or
                                             value["used_percent"] is None or value["used_percent"] >= 100) or
            value["state"] == "exhausted" and value["used_percent"] != 100):
        raise DecisionLedgerError("batch_decision_corrupt")
    return BatchQuotaEvidence(value["schema_version"], value["task_id"], value["route_id"], value["profile"],
                              value["account_ref"], value["state"],
                              value["observed_at"], value["valid_until"], value["used_percent"],
                              value["reason_code"])


class BatchDecisionStore:
    """Idempotent, append-only persistence sharing the M2 decision ledger's SQLite file."""

    def __init__(self, connection_factory: Callable[[bool], sqlite3.Connection], *, writable: bool,
                 schema_version: int):
        self._connection_factory = connection_factory
        self._writable = writable
        self._schema_version = schema_version

    def persist(self, requests: Sequence[DecisionRequest], *,
                account_concurrency: Sequence[AccountConcurrency] = (),
                route_evidence_by_task: Mapping[str, Mapping[str, RoutePolicyEvidence]] | None = None,
                preserve_baseline_by_task: Mapping[str, bool] | None = None,
                quota_evidence_by_task: Mapping[str, Mapping[str, BatchQuotaEvidence]] | None = None,
                policy: RoutePolicyConfig = DEFAULT_ROUTE_POLICY) -> BatchPlan:
        """Plan and insert once; exact replay returns the first immutable stored result."""
        if not self._writable:
            raise DecisionLedgerError("read_only")
        if self._schema_version != CURRENT_LEDGER_SCHEMA_VERSION:
            raise DecisionLedgerError("batch_decision_schema_unavailable")
        plan = plan_ready_batch(
            requests, account_concurrency=account_concurrency,
            route_evidence_by_task=route_evidence_by_task,
            preserve_baseline_by_task=preserve_baseline_by_task,
            quota_evidence_by_task=quota_evidence_by_task, policy=policy,
        )
        try:
            payload = canonical_json(plan)
            if len(payload.encode("utf-8")) > MAX_BATCH_RECORD_BYTES:
                raise DecisionLedgerError("batch_decision_too_large")
            payload_sha256 = sha256_json(json.loads(payload))
        except DecisionLedgerError:
            raise
        except (TypeError, ValueError) as exc:
            raise DecisionLedgerError("batch_decision_invalid") from exc

        try:
            connection = self._connection_factory(False)
        except sqlite3.Error as exc:
            raise DecisionLedgerError("ledger_unavailable") from exc
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT batch_id, plan_sha256, plan_json FROM batch_decisions WHERE input_sha256 = ?",
                (plan.input_sha256,),
            ).fetchone()
            if row:
                stored = _decode_batch_plan(row[2], row[1])
                if row[0] != stored.batch_id or stored != plan or row[2] != payload:
                    raise DecisionLedgerError("batch_decision_fingerprint_conflict")
                connection.execute("COMMIT")
                return stored
            row = connection.execute("SELECT input_sha256 FROM batch_decisions WHERE batch_id = ?",
                                     (plan.batch_id,)).fetchone()
            if row:
                raise DecisionLedgerError("batch_decision_id_conflict")
            count = connection.execute("SELECT COUNT(*) FROM batch_decisions").fetchone()[0]
            if count >= MAX_BATCH_RECORDS:
                raise DecisionLedgerError("batch_decision_store_full")
            connection.execute(
                "INSERT INTO batch_decisions(batch_id,input_sha256,plan_sha256,plan_json) VALUES(?,?,?,?)",
                (plan.batch_id, plan.input_sha256, payload_sha256, payload),
            )
            connection.execute("COMMIT")
            return plan
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

    def get(self, input_sha256: str) -> BatchPlan | None:
        """Read one exact batch replay by its canonical input fingerprint."""
        if not isinstance(input_sha256, str) or not _SHA256.fullmatch(input_sha256):
            raise DecisionLedgerError("batch_decision_invalid")
        if self._schema_version < CURRENT_LEDGER_SCHEMA_VERSION:
            return None
        try:
            connection = self._connection_factory(True)
        except sqlite3.Error as exc:
            raise DecisionLedgerError("ledger_unavailable") from exc
        try:
            row = connection.execute(
                "SELECT batch_id, plan_sha256, plan_json FROM batch_decisions WHERE input_sha256 = ?",
                (input_sha256,),
            ).fetchone()
        except sqlite3.Error as exc:
            raise DecisionLedgerError("ledger_unavailable") from exc
        finally:
            connection.close()
        if row is None:
            return None
        plan = _decode_batch_plan(row[2], row[1])
        if row[0] != plan.batch_id or plan.input_sha256 != input_sha256:
            raise DecisionLedgerError("batch_decision_corrupt")
        return plan
