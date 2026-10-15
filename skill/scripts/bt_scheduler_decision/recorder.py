"""Bounded SQLite ledger for immutable M2 recommendations."""
from __future__ import annotations

import dataclasses
import json
import math
import os
import re
import sqlite3
from pathlib import Path

from .contracts import (
    API_VERSION,
    DECISION_FACTOR_CODES,
    DECISION_METHODS,
    DECISION_STATUSES,
    EXCLUSION_REASON_CODES,
    FALLBACK_REASONS,
    Candidate,
    Confidence,
    DecisionRecord,
    Exclusion,
    RouteSummary,
    ValidatedRequest,
)
from .identity import (
    canonical_json,
    parse_executor_reference,
    sha256_json,
)
from .policy import rank_candidates
from .validation import validate_request

APPLICATION_ID = 0x4D324445  # "M2DE"
LEDGER_SCHEMA_VERSION = 1
MAX_RECORD_BYTES = 131_072
MAX_LEDGER_RECORDS = 100_000
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_ACCOUNT_REF = re.compile(r"acct:[0-9a-f]{64}\Z")
_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS decision_records (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id TEXT NOT NULL UNIQUE CHECK(length(decision_id) = 64),
    idempotency_key TEXT NOT NULL UNIQUE CHECK(length(idempotency_key) = 64),
    plan_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    record_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS decision_records_task_latest
    ON decision_records(plan_id, task_id, seq DESC);
"""


class DecisionLedgerError(RuntimeError):
    """Stable local-persistence error without filesystem or SQLite details."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(f"decision_ledger_{code}")


def _idempotency_key_for_validated(validated: ValidatedRequest) -> str:
    """Hash validated decision sources while excluding request wall-clock time."""
    item = validated.request
    return sha256_json({
        "contract_version": API_VERSION,
        "plan_id": item.plan_id,
        "revision": item.revision,
        "plan_sha256": item.plan_sha256,
        "validated_task_input_digest": validated.task_input_sha256,
        "candidate_quota_telemetry_snapshot": {
            "candidate_snapshot_sha256": validated.candidate_snapshot_sha256,
            "quota_snapshot_sha256": validated.quota_snapshot_sha256,
        },
        "policy_version": item.policy_version,
        "checkpoint_revision": item.checkpoint_revision,
    })


def idempotency_key(request: object) -> str:
    """Validate the original request and hash its sources, excluding request wall-clock time."""
    if isinstance(request, ValidatedRequest):
        raise DecisionLedgerError("raw_request_required")
    return _idempotency_key_for_validated(validate_request(request))


def decision_id_for(key: str) -> str:
    if not isinstance(key, str) or not _SHA256.fullmatch(key):
        raise ValueError("idempotency key must be lowercase SHA-256 hex")
    return sha256_json({"m2_decision_id": key})


def _route_summary_matches(summary: RouteSummary, candidate: Candidate) -> bool:
    return (summary.route_id, summary.provider, summary.model, summary.profile, summary.account_ref, summary.effort,
            summary.baseline_rank) == (candidate.route_id, candidate.provider, candidate.model, candidate.profile,
                                       candidate.account_ref, candidate.effort, candidate.baseline_rank)


def _validate_route_summary(value: object) -> None:
    if not isinstance(value, RouteSummary) or not _SHA256.fullmatch(value.route_id or "") or \
            not _ACCOUNT_REF.fullmatch(value.account_ref or ""):
        raise DecisionLedgerError("invalid_record")
    for text, maximum in ((value.provider, 64), (value.model, 128), (value.profile, 64)):
        if not isinstance(text, str) or not text or len(text) > maximum:
            raise DecisionLedgerError("invalid_record")
    if value.effort is not None and (not isinstance(value.effort, str) or len(value.effort) > 32):
        raise DecisionLedgerError("invalid_record")
    if value.baseline_rank is not None and (not isinstance(value.baseline_rank, int) or
                                             isinstance(value.baseline_rank, bool) or
                                             not 0 <= value.baseline_rank <= 255):
        raise DecisionLedgerError("invalid_record")
    if not isinstance(value.factor_codes, tuple) or len(value.factor_codes) > 64 or \
            any(not isinstance(code, str) or code not in DECISION_FACTOR_CODES for code in value.factor_codes):
        raise DecisionLedgerError("invalid_record")


def _validate_exclusion(value: object) -> None:
    if not isinstance(value, Exclusion):
        raise DecisionLedgerError("invalid_record")
    _validate_route_summary(RouteSummary(value.route_id, value.provider, value.model, value.profile, value.account_ref,
                                         value.effort))
    if not isinstance(value.reason_codes, tuple) or not value.reason_codes or len(value.reason_codes) > 64 or \
            any(not isinstance(code, str) or code not in EXCLUSION_REASON_CODES for code in value.reason_codes):
        raise DecisionLedgerError("invalid_record")


def _validate_record(record: object, request: ValidatedRequest | None = None) -> None:
    if not isinstance(record, DecisionRecord) or record.schema_version != API_VERSION or \
            not _SHA256.fullmatch(record.decision_id or "") or not _SHA256.fullmatch(record.idempotency_key or ""):
        raise DecisionLedgerError("invalid_record")
    if record.decision_id != decision_id_for(record.idempotency_key):
        raise DecisionLedgerError("invalid_record")
    if record.previous_decision_id is not None and not _SHA256.fullmatch(record.previous_decision_id):
        raise DecisionLedgerError("invalid_record")
    if not isinstance(record.plan_id, str) or not record.plan_id or not isinstance(record.task_id, str) or \
            not record.task_id or not isinstance(record.revision, int) or isinstance(record.revision, bool) or \
            record.revision < 1 or not _SHA256.fullmatch(record.plan_sha256 or ""):
        raise DecisionLedgerError("invalid_record")
    if not isinstance(record.created_at, (int, float)) or isinstance(record.created_at, bool) or \
            not math.isfinite(record.created_at) or record.created_at < 0:
        raise DecisionLedgerError("invalid_record")
    if record.status not in DECISION_STATUSES or record.method not in DECISION_METHODS:
        raise DecisionLedgerError("invalid_record")
    if not isinstance(record.policy_version, str) or not record.policy_version or \
            record.checkpoint_revision is not None and not isinstance(record.checkpoint_revision, str):
        raise DecisionLedgerError("invalid_record")
    if not _SHA256.fullmatch(record.candidate_snapshot_sha256 or "") or \
            not _SHA256.fullmatch(record.quota_snapshot_sha256 or ""):
        raise DecisionLedgerError("invalid_record")
    if record.baseline_route_id is not None and not _SHA256.fullmatch(record.baseline_route_id):
        raise DecisionLedgerError("invalid_record")
    if record.fallback_reason is not None and (not isinstance(record.fallback_reason, str) or
                                                record.fallback_reason not in FALLBACK_REASONS):
        raise DecisionLedgerError("invalid_record")
    if not isinstance(record.confidence, Confidence):
        raise DecisionLedgerError("invalid_record")
    if not isinstance(record.factor_codes, tuple) or len(record.factor_codes) > 64 or \
            any(not isinstance(code, str) or code not in DECISION_FACTOR_CODES for code in record.factor_codes):
        raise DecisionLedgerError("invalid_record")
    if not isinstance(record.rationale, str) or len(record.rationale) > 4096 or \
            record.rationale != ";".join(record.factor_codes):
        raise DecisionLedgerError("free_text_rationale_forbidden")
    if not isinstance(record.alternatives, tuple) or len(record.alternatives) > 256 or \
            not isinstance(record.exclusions, tuple) or len(record.exclusions) > 256:
        raise DecisionLedgerError("invalid_record")
    for route in record.alternatives:
        _validate_route_summary(route)
    for exclusion in record.exclusions:
        _validate_exclusion(exclusion)
    if record.selected is not None:
        _validate_route_summary(record.selected)
    if (record.status == "recommended") != (record.selected is not None):
        raise DecisionLedgerError("invalid_record")
    if record.method == "laya" and (record.checkpoint_revision is None or
                                     record.confidence.source != "laya_answer_confidence" or
                                     record.fallback_reason is not None or
                                     "laya_choice_accepted" not in record.factor_codes):
        raise DecisionLedgerError("invalid_record")
    if record.method != "laya" and (record.confidence.source == "laya_answer_confidence" or
                                     record.method == "deterministic" and record.fallback_reason is not None or
                                     record.method == "deterministic_fallback" and record.fallback_reason is None):
        raise DecisionLedgerError("invalid_record")
    route_ids = [route.route_id for route in record.alternatives]
    excluded_ids = [item.route_id for item in record.exclusions]
    if len(route_ids) != len(set(route_ids)) or len(excluded_ids) != len(set(excluded_ids)) or \
            set(route_ids) & set(excluded_ids) or record.selected and \
            record.selected.route_id in {*route_ids, *excluded_ids}:
        raise DecisionLedgerError("invalid_record")
    if request is None:
        return
    item = request.request
    expected_key = _idempotency_key_for_validated(request)
    if record.idempotency_key != expected_key or record.decision_id != decision_id_for(expected_key) or \
            (record.plan_id, record.revision, record.plan_sha256, record.task_id, record.policy_version,
             record.checkpoint_revision, record.candidate_snapshot_sha256, record.quota_snapshot_sha256) != \
            (item.plan_id, item.revision, item.plan_sha256, item.task.task_id, item.policy_version,
             item.checkpoint_revision, request.candidate_snapshot_sha256, request.quota_snapshot_sha256):
        raise DecisionLedgerError("record_request_mismatch")
    ranking = rank_candidates(request)
    eligible = {candidate.route_id: candidate for candidate in ranking.eligible}
    all_candidates = {candidate.route_id: candidate for candidate in item.candidates}
    if record.baseline_route_id != (ranking.selected.route_id if ranking.selected else None):
        raise DecisionLedgerError("record_request_mismatch")
    if record.status == "recommended":
        candidate = eligible.get(record.selected.route_id)
        if candidate is None or not _route_summary_matches(record.selected, candidate):
            raise DecisionLedgerError("record_selected_route_invalid")
    elif ranking.eligible:
        raise DecisionLedgerError("record_selected_route_invalid")
    for route in record.alternatives:
        candidate = eligible.get(route.route_id)
        if candidate is None or record.selected and route.route_id == record.selected.route_id or \
                not _route_summary_matches(route, candidate):
            raise DecisionLedgerError("record_alternative_route_invalid")
    expected_exclusions = {item.route_id: item for item in ranking.exclusions}
    if set(excluded_ids) != set(expected_exclusions):
        raise DecisionLedgerError("record_exclusions_mismatch")
    for exclusion in record.exclusions:
        candidate = all_candidates.get(exclusion.route_id)
        expected = expected_exclusions[exclusion.route_id]
        if candidate is None or (exclusion.provider, exclusion.model, exclusion.profile, exclusion.account_ref,
                                 exclusion.effort, exclusion.reason_codes) != \
                (expected.provider, expected.model, expected.profile, expected.account_ref, expected.effort,
                 expected.reason_codes):
            raise DecisionLedgerError("record_exclusions_mismatch")


def _record_payload(record: DecisionRecord) -> str:
    payload = canonical_json(record)
    if len(payload.encode("utf-8")) > MAX_RECORD_BYTES:
        raise DecisionLedgerError("record_too_large")
    return payload


def _decode_record(payload: str) -> DecisionRecord:
    try:
        if len(payload.encode("utf-8", errors="strict")) > MAX_RECORD_BYTES:
            raise DecisionLedgerError("record_too_large")
        raw = json.loads(payload)
        if not isinstance(raw, dict):
            raise TypeError("not an object")
        expected = {field.name for field in dataclasses.fields(DecisionRecord)}
        if set(raw) != expected:
            raise ValueError("record fields mismatch")
        selected = None if raw["selected"] is None else RouteSummary(
            **{**raw["selected"], "factor_codes": tuple(raw["selected"].get("factor_codes", ()))})
        alternatives = tuple(RouteSummary(**{**item, "factor_codes": tuple(item.get("factor_codes", ()))})
                             for item in raw["alternatives"])
        exclusions = tuple(Exclusion(**{**item, "reason_codes": tuple(item["reason_codes"])})
                           for item in raw["exclusions"])
        confidence = Confidence(**raw["confidence"])
        record = DecisionRecord(**{**raw, "selected": selected, "alternatives": alternatives,
                                   "exclusions": exclusions, "confidence": confidence,
                                   "factor_codes": tuple(raw["factor_codes"])})
        _validate_record(record)
        return record
    except DecisionLedgerError:
        raise
    except (KeyError, TypeError, ValueError, UnicodeEncodeError) as exc:
        raise DecisionLedgerError("record_corrupt") from exc


class DecisionLedger:
    """A private M2-only SQLite file. Every operation uses its own bounded connection/transaction."""

    def __init__(self, path: str | Path, *, busy_timeout: float = 10.0, create: bool = True):
        self.path = Path(path)
        if str(path) == ":memory:" or self.path.is_symlink() or not isinstance(busy_timeout, (int, float)) or \
                isinstance(busy_timeout, bool) or not math.isfinite(busy_timeout) or not 0 < busy_timeout <= 60:
            raise DecisionLedgerError("invalid_configuration")
        if self.path.exists() and not self.path.is_file() or not create and not self.path.is_file():
            raise DecisionLedgerError("ledger_missing_or_invalid")
        existed = self.path.exists()
        self._busy_timeout = float(busy_timeout)
        self._writable = create
        try:
            if create:
                self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            self._initialize(create, existed=existed)
            if create:
                os.chmod(self.path, 0o600)
        except DecisionLedgerError:
            raise
        except (OSError, sqlite3.Error) as exc:
            raise DecisionLedgerError("ledger_unavailable") from exc

    def _connect(self, *, readonly: bool = False) -> sqlite3.Connection:
        if readonly:
            connection = sqlite3.connect(self.path.as_uri() + "?mode=ro", uri=True,
                                         timeout=float(self._busy_timeout), isolation_level=None)
        else:
            connection = sqlite3.connect(str(self.path), timeout=float(self._busy_timeout), isolation_level=None)
        connection.execute(f"PRAGMA busy_timeout = {int(float(self._busy_timeout) * 1000)}")
        connection.execute("PRAGMA synchronous = FULL")
        return connection

    def _initialize(self, create: bool, *, existed: bool) -> None:
        if not create and not self.path.is_file():
            raise DecisionLedgerError("ledger_missing_or_invalid")
        connection = self._connect(readonly=not create)
        try:
            tables = {row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
            app_id = connection.execute("PRAGMA application_id").fetchone()[0]
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if existed and (app_id != APPLICATION_ID or tables != {"decision_records"} or
                            version != LEDGER_SCHEMA_VERSION):
                raise DecisionLedgerError("ledger_incompatible")
            if not existed and (tables or app_id != 0 or version != 0):
                raise DecisionLedgerError("ledger_incompatible")
            if not create and not tables:
                raise DecisionLedgerError("ledger_incompatible")
            if create:
                connection.execute("PRAGMA journal_mode = WAL")
                connection.executescript(_SCHEMA_SQL)
                connection.execute(f"PRAGMA application_id = {APPLICATION_ID}")
                connection.execute(f"PRAGMA user_version = {LEDGER_SCHEMA_VERSION}")
        finally:
            connection.close()

    def lookup(self, request: object) -> DecisionRecord | None:
        """Read an exact replay before inference without changing the ledger."""
        if isinstance(request, ValidatedRequest):
            raise DecisionLedgerError("raw_request_required")
        validated = validate_request(request)
        key = _idempotency_key_for_validated(validated)
        try:
            connection = self._connect(readonly=True)
        except sqlite3.Error as exc:
            raise DecisionLedgerError("ledger_unavailable") from exc
        try:
            row = connection.execute("SELECT record_json FROM decision_records WHERE idempotency_key = ?", (key,)).fetchone()
        except sqlite3.Error as exc:
            raise DecisionLedgerError("ledger_unavailable") from exc
        finally:
            connection.close()
        return _decode_record(row[0]) if row else None

    def persist(self, request: object, record: DecisionRecord) -> DecisionRecord:
        """Insert once; exact replay returns stored bytes; changed snapshots link to the preceding task record."""
        if not self._writable:
            raise DecisionLedgerError("read_only")
        if isinstance(request, ValidatedRequest):
            raise DecisionLedgerError("raw_request_required")
        validated = validate_request(request)
        _validate_record(record, validated)
        if record.previous_decision_id is not None:
            raise DecisionLedgerError("caller_previous_decision_forbidden")
        _record_payload(record)
        try:
            connection = self._connect()
        except sqlite3.Error as exc:
            raise DecisionLedgerError("ledger_unavailable") from exc
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT record_json FROM decision_records WHERE idempotency_key = ?",
                                     (record.idempotency_key,)).fetchone()
            if row:
                connection.execute("COMMIT")
                return _decode_record(row[0])
            previous = connection.execute(
                "SELECT decision_id FROM decision_records WHERE plan_id = ? AND task_id = ? ORDER BY seq DESC LIMIT 1",
                (record.plan_id, record.task_id),
            ).fetchone()
            count = connection.execute("SELECT COUNT(*) FROM decision_records").fetchone()[0]
            if count >= MAX_LEDGER_RECORDS:
                raise DecisionLedgerError("ledger_full")
            persisted = dataclasses.replace(record, previous_decision_id=previous[0] if previous else None)
            persisted_payload = _record_payload(persisted)
            connection.execute(
                "INSERT INTO decision_records(decision_id,idempotency_key,plan_id,task_id,record_json) "
                "VALUES(?,?,?,?,?)",
                (persisted.decision_id, persisted.idempotency_key, persisted.plan_id, persisted.task_id,
                 persisted_payload),
            )
            connection.execute("COMMIT")
            return persisted
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

    def resolve_executor_reference(self, reference: str) -> RouteSummary | None:
        """Resolve only the selected route; unknown, malformed, excluded and alternative refs return `None`."""
        parsed = parse_executor_reference(reference)
        if parsed is None:
            return None
        decision_id, route_id = parsed
        try:
            connection = self._connect(readonly=True)
        except sqlite3.Error as exc:
            raise DecisionLedgerError("ledger_unavailable") from exc
        try:
            row = connection.execute("SELECT record_json FROM decision_records WHERE decision_id = ?",
                                     (decision_id,)).fetchone()
        except sqlite3.Error as exc:
            raise DecisionLedgerError("ledger_unavailable") from exc
        finally:
            connection.close()
        if row is None:
            return None
        record = _decode_record(row[0])
        if record.selected is None or record.selected.route_id != route_id:
            return None
        return record.selected


def resolve_executor_reference(path: str | Path, reference: str) -> RouteSummary | None:
    """Resolve a selected route through an existing ledger without creating or changing the database."""
    return DecisionLedger(path, create=False).resolve_executor_reference(reference)
