from __future__ import annotations

import dataclasses
import hashlib
import json
import sqlite3
import stat
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from bt_scheduler_decision import (
    API_VERSION,
    Confidence,
    DecisionLedger,
    DecisionLedgerError,
    DecisionRecord,
    PerformanceContext,
    RouteSummary,
    decision_id_for,
    executor_reference,
    idempotency_key,
    normalize_performance_event,
    rank_candidates,
    resolve_executor_binding,
    resolve_executor_reference,
    validate_request,
)
from bt_scheduler_decision.recorder import _decode_record
from bt_scheduler_decision.tests.support import candidate, request


def _summary(item):
    return RouteSummary(item.route_id, item.provider, item.model, item.profile, item.account_ref, item.effort,
                        item.baseline_rank, ("baseline_route",), item.quota_observed_at,
                        item.quota_used_percent, item.quota_valid_until)


def _record(request_value, *, created_at=100.0, rationale_override=None):
    validated = validate_request(request_value)
    ranking = rank_candidates(validated)
    item = validated.request
    key = idempotency_key(request_value)
    factors = ("baseline_route",) if ranking.selected else ("no_eligible_candidate",)
    selected = _summary(ranking.selected) if ranking.selected else None
    alternatives = tuple(_summary(route) for route in ranking.eligible[1:])
    return DecisionRecord(
        API_VERSION,
        decision_id_for(key),
        key,
        None,
        item.plan_id,
        item.revision,
        item.plan_sha256,
        item.task.task_id,
        created_at,
        "recommended" if selected else "no_eligible_candidate",
        selected,
        alternatives,
        ranking.exclusions,
        ranking.selected.route_id if ranking.selected else None,
        "deterministic",
        None,
        item.policy_version,
        item.checkpoint_revision,
        validated.candidate_snapshot_sha256,
        validated.quota_snapshot_sha256,
        Confidence(None, "none", "none"),
        factors,
        rationale_override if rationale_override is not None else ";".join(factors),
    )


def _learning_sources():
    route_id = "b" * 64
    target = PerformanceContext(task_family="implementation", complexity="medium", scope="small_change",
                                risk="low", coupling="low")
    events = []
    contexts = {}
    for index in range(5):
        task_id = f"private-task-{index}"
        attempt_id = f"private-attempt-{index}"
        decision_id = hashlib.sha256(f"decision:{task_id}".encode()).hexdigest()
        attempt = {
            "plan_id": "REQ-020",
            "revision": 3,
            "task_id": task_id,
            "attempt_id": attempt_id,
            "executor_ref": f"route:m2:v1:{decision_id}:{route_id}",
            "state": "accepted",
            "synthetic": False,
        }
        decision = {
            "schema_version": API_VERSION,
            "decision_id": decision_id,
            "plan_id": "REQ-020",
            "revision": 3,
            "task_id": task_id,
            "selected_route_id": route_id,
        }
        verdict = {
            "verdict_id": f"private-verdict-{index}",
            "plan_id": "REQ-020",
            "revision": 3,
            "task_id": task_id,
            "attempt_id": attempt_id,
            "accepted": True,
            "verifier": "private-independent-reviewer",
            "evidence_present": True,
            "application_status": "applied",
            "synthetic": False,
            "applied_at": "2026-10-15T20:30:00Z",
        }
        events.append(normalize_performance_event(attempt, decision, verdict))
        contexts[("REQ-020", 3, task_id)] = target
    return events, contexts, route_id, target


class DecisionLedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "state" / "m2.sqlite3"
        self.ledger = DecisionLedger(self.path)

    def tearDown(self):
        self.temp.cleanup()

    def _persist_learning_snapshot(self, events, contexts, route_id, target, *, created_at=1_800_000_001.0,
                                   policy_version="contextual-history-v1", learning_cutoff=1_800_000_000.0):
        return self.ledger.learning_snapshots.persist(
            events, contexts, route_id=route_id, target_context=target, policy_version=policy_version,
            learning_cutoff=learning_cutoff, created_at=created_at,
        )

    def test_decoder_keeps_legacy_record_versions_readable(self):
        current = _record(request())
        current_data = dataclasses.asdict(current)
        legacy = None
        for version in ("1.0.0", "1.1.0"):
            payload_data = json.loads(json.dumps(current_data))
            payload_data["schema_version"] = version
            if version == "1.0.0":
                for route in (payload_data["selected"], *payload_data["alternatives"]):
                    if route is not None:
                        route.pop("quota_observed_at", None)
                        route.pop("quota_used_percent", None)
                        route.pop("quota_valid_until", None)
            record = _decode_record(json.dumps(payload_data, sort_keys=True, separators=(",", ":")))
            self.assertEqual(record.schema_version, version)
            if version == "1.0.0":
                legacy = record
        self.assertIsNotNone(legacy)
        self.assertIsNone(legacy.selected.quota_valid_until)

    def test_exact_replay_ignores_request_time_and_preserves_first_timestamp(self):
        first_request = request(requested_at=100.0)
        later_request = dataclasses.replace(first_request, requested_at=110.0)
        first = self.ledger.persist(first_request, _record(first_request, created_at=101.0))
        replay = self.ledger.persist(later_request, _record(later_request, created_at=111.0))
        self.assertEqual(replay, first)
        self.assertEqual(replay.created_at, 101.0)
        self.assertIsNone(replay.previous_decision_id)

    def test_changed_quota_snapshot_creates_a_new_linked_record(self):
        first_request = request()
        first = self.ledger.persist(first_request, _record(first_request))
        changed = dataclasses.replace(candidate(), quota_used_percent=31.0)
        second_request = request(candidates=(changed,))
        second = self.ledger.persist(second_request, _record(second_request, created_at=120.0))
        self.assertNotEqual(first.idempotency_key, second.idempotency_key)
        self.assertNotEqual(first.decision_id, second.decision_id)
        self.assertEqual(second.previous_decision_id, first.decision_id)

    def test_concurrent_identical_writes_create_exactly_one_record(self):
        request_value = request()

        def persist(index):
            return self.ledger.persist(request_value, _record(request_value, created_at=100.0 + index))

        with ThreadPoolExecutor(max_workers=12) as pool:
            results = list(pool.map(persist, range(24)))
        self.assertEqual(len({record.decision_id for record in results}), 1)
        self.assertEqual(len({record.created_at for record in results}), 1)
        connection = sqlite3.connect(self.path)
        try:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM decision_records").fetchone()[0], 1)
        finally:
            connection.close()

    def test_executor_reference_resolves_only_the_persisted_selected_route(self):
        selected = candidate(profile="selected", rank=0)
        alternative = candidate(provider="codex", model="sol", profile="alternative", rank=1)
        excluded = dataclasses.replace(candidate(profile="excluded", rank=2), profile_authorized=False)
        request_value = request(candidates=(selected, alternative, excluded))
        saved = self.ledger.persist(request_value, _record(request_value))
        selected_ref = executor_reference(saved.decision_id, selected.route_id)
        alternative_ref = executor_reference(saved.decision_id, alternative.route_id)
        excluded_ref = executor_reference(saved.decision_id, excluded.route_id)
        self.assertEqual(self.ledger.resolve_executor_reference(selected_ref).route_id, selected.route_id)
        self.assertIsNone(self.ledger.resolve_executor_reference(alternative_ref))
        self.assertIsNone(self.ledger.resolve_executor_reference(excluded_ref))
        self.assertIsNone(self.ledger.resolve_executor_reference("not-an-m2-reference"))
        self.assertIsNone(self.ledger.resolve_executor_reference(executor_reference("f" * 64, selected.route_id)))

    def test_public_executor_lookup_opens_existing_ledger_read_only(self):
        request_value = request()
        saved = self.ledger.persist(request_value, _record(request_value))
        reference = executor_reference(saved.decision_id, saved.selected.route_id)
        before = self.path.read_bytes()
        resolved = resolve_executor_reference(self.path, reference)
        self.assertEqual(resolved, saved.selected)
        self.assertEqual(self.path.read_bytes(), before)

    def test_binding_names_the_plan_task_and_the_decision_that_replaced_it(self):
        first_candidate = candidate(profile="one", rank=0)
        second_candidate = candidate(provider="codex", model="sol", profile="two", rank=0)
        first_request = request(candidates=(first_candidate,))
        first = self.ledger.persist(first_request, _record(first_request))
        first_ref = executor_reference(first.decision_id, first.selected.route_id)
        live = resolve_executor_binding(self.path, first_ref)
        self.assertEqual((live.plan_id, live.revision, live.task_id, live.decision_id, live.superseded_by),
                         (first.plan_id, first.revision, first.task_id, first.decision_id, None))
        self.assertEqual(live.route, first.selected)
        second_request = request(candidates=(second_candidate,))
        second = self.ledger.persist(second_request, _record(second_request))
        self.assertNotEqual(first.decision_id, second.decision_id)
        self.assertEqual(resolve_executor_binding(self.path, first_ref).superseded_by, second.decision_id)
        second_ref = executor_reference(second.decision_id, second.selected.route_id)
        self.assertIsNone(resolve_executor_binding(self.path, second_ref).superseded_by)
        self.assertIsNone(resolve_executor_binding(self.path, executor_reference("f" * 64, first.selected.route_id)))
        self.assertIsNone(resolve_executor_binding(self.path, "not-an-m2-reference"))

    def test_record_decision_id_must_be_derived_from_its_idempotency_key(self):
        request_value = request()
        record = dataclasses.replace(_record(request_value), decision_id="f" * 64)
        with self.assertRaisesRegex(DecisionLedgerError, "invalid_record"):
            self.ledger.persist(request_value, record)

    def test_persistence_revalidates_raw_request_and_rejects_forged_validated_digest(self):
        request_value = request()
        validated = validate_request(request_value)
        forged = dataclasses.replace(validated, task_input_sha256="f" * 64)
        with self.assertRaisesRegex(DecisionLedgerError, "raw_request_required"):
            self.ledger.persist(forged, _record(request_value))
        with self.assertRaisesRegex(DecisionLedgerError, "raw_request_required"):
            idempotency_key(forged)

    def test_unrelated_database_is_refused_without_modification(self):
        other = Path(self.temp.name) / "other.sqlite3"
        connection = sqlite3.connect(other)
        try:
            connection.execute("CREATE TABLE precious (value TEXT)")
            connection.execute("INSERT INTO precious VALUES ('preserve')")
        finally:
            connection.close()
        before = other.read_bytes()
        with self.assertRaisesRegex(DecisionLedgerError, "ledger_incompatible"):
            DecisionLedger(other)
        self.assertEqual(other.read_bytes(), before)

    def test_existing_empty_database_is_refused_without_modification(self):
        empty = Path(self.temp.name) / "empty.sqlite3"
        empty.touch(mode=0o600)
        before = empty.read_bytes()
        with self.assertRaisesRegex(DecisionLedgerError, "ledger_incompatible"):
            DecisionLedger(empty)
        self.assertEqual(empty.read_bytes(), before)

    def test_free_text_rationale_is_rejected_and_database_permissions_are_private(self):
        request_value = request()
        with self.assertRaisesRegex(DecisionLedgerError, "free_text_rationale_forbidden"):
            self.ledger.persist(request_value, _record(request_value, rationale_override="raw task text"))
        self.assertEqual(stat.S_IMODE(self.path.stat().st_mode), 0o600)

    def test_missing_read_only_ledger_is_not_created(self):
        absent = Path(self.temp.name) / "absent.sqlite3"
        with self.assertRaisesRegex(DecisionLedgerError, "ledger_missing_or_invalid"):
            DecisionLedger(absent, create=False)
        self.assertFalse(absent.exists())

    def test_learning_snapshot_is_idempotent_redacted_and_readable_after_replay(self):
        events, contexts, route_id, target = _learning_sources()
        first = self._persist_learning_snapshot(events, contexts, route_id, target)
        replay = self._persist_learning_snapshot(
            [*reversed(events), events[0]], contexts, route_id, target, created_at=1_800_000_100.0,
        )
        self.assertEqual(replay, first)
        self.assertEqual(replay.to_dict()["assessment"]["selected_level"], "exact_context")
        self.assertEqual(self.ledger.learning_snapshots.get(first.source_fingerprint), first)
        reopened = DecisionLedger(self.path, create=False)
        self.assertEqual(reopened.learning_snapshots.get(first.source_fingerprint), first)
        serialized = json.dumps(first.to_dict(), sort_keys=True)
        self.assertNotIn("private-task", serialized)
        self.assertNotIn("private-attempt", serialized)
        self.assertNotIn("private-verdict", serialized)
        self.assertNotIn("private-independent-reviewer", serialized)
        connection = sqlite3.connect(self.path)
        try:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM learning_snapshots").fetchone()[0], 1)
            stored = connection.execute("SELECT snapshot_json FROM learning_snapshots").fetchone()[0]
            self.assertNotIn("private-task", stored)
        finally:
            connection.close()

    def test_learning_snapshots_reject_updates_and_deletes(self):
        events, contexts, route_id, target = _learning_sources()
        snapshot = self._persist_learning_snapshot(events, contexts, route_id, target)
        connection = sqlite3.connect(self.path)
        try:
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("UPDATE learning_snapshots SET snapshot_json = '{}' WHERE source_fingerprint = ?",
                                   (snapshot.source_fingerprint,))
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("DELETE FROM learning_snapshots WHERE source_fingerprint = ?",
                                   (snapshot.source_fingerprint,))
        finally:
            connection.close()
        self.assertEqual(self.ledger.learning_snapshots.get(snapshot.source_fingerprint), snapshot)

    def test_corrupt_learning_snapshot_is_rejected_without_exposing_stored_data(self):
        events, contexts, route_id, target = _learning_sources()
        snapshot = self._persist_learning_snapshot(events, contexts, route_id, target)
        connection = sqlite3.connect(self.path)
        try:
            connection.execute("DROP TRIGGER learning_snapshots_immutable_update")
            connection.execute("UPDATE learning_snapshots SET snapshot_json = '{}' WHERE source_fingerprint = ?",
                               (snapshot.source_fingerprint,))
            connection.commit()
        finally:
            connection.close()
        with self.assertRaisesRegex(DecisionLedgerError, "learning_snapshot_corrupt"):
            self.ledger.learning_snapshots.get(snapshot.source_fingerprint)

    def test_learning_snapshot_capacity_is_bounded_without_pruning(self):
        events, contexts, route_id, target = _learning_sources()
        with patch("bt_scheduler_decision.learning_snapshots.MAX_LEARNING_SNAPSHOTS", 1):
            first = self._persist_learning_snapshot(events, contexts, route_id, target)
            with self.assertRaisesRegex(DecisionLedgerError, "learning_snapshot_store_full"):
                self._persist_learning_snapshot(
                    events, contexts, route_id, target, policy_version="contextual-history-v2",
                )
        self.assertEqual(self.ledger.learning_snapshots.get(first.source_fingerprint), first)
        connection = sqlite3.connect(self.path)
        try:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM learning_snapshots").fetchone()[0], 1)
        finally:
            connection.close()

    def test_learning_snapshot_payload_size_is_bounded_before_any_write(self):
        events, contexts, route_id, target = _learning_sources()
        with patch("bt_scheduler_decision.learning_snapshots.MAX_LEARNING_SNAPSHOT_BYTES", 1), \
                self.assertRaisesRegex(DecisionLedgerError, "learning_snapshot_too_large"):
            self._persist_learning_snapshot(events, contexts, route_id, target)
        connection = sqlite3.connect(self.path)
        try:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM learning_snapshots").fetchone()[0], 0)
        finally:
            connection.close()

    def test_concurrent_learning_snapshot_replays_store_one_immutable_row(self):
        events, contexts, route_id, target = _learning_sources()

        def persist(index):
            return self._persist_learning_snapshot(events, contexts, route_id, target,
                                                   created_at=1_800_000_001.0 + index)

        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(persist, range(16)))
        self.assertEqual(len({item.source_fingerprint for item in results}), 1)
        self.assertEqual(len({item.created_at for item in results}), 1)
        connection = sqlite3.connect(self.path)
        try:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM learning_snapshots").fetchone()[0], 1)
        finally:
            connection.close()

    def test_writable_schema_one_ledger_migrates_additively_and_read_only_schema_one_remains_valid(self):
        request_value = request()
        saved = self.ledger.persist(request_value, _record(request_value))
        connection = sqlite3.connect(self.path)
        try:
            connection.execute("DROP TABLE batch_decisions")
            connection.execute("DROP TABLE learning_snapshots")
            connection.execute("PRAGMA user_version = 1")
        finally:
            connection.close()
        legacy = DecisionLedger(self.path, create=False)
        self.assertEqual(legacy.lookup(request_value), saved)
        self.assertIsNone(legacy.learning_snapshots.get("a" * 64))
        self.assertIsNone(legacy.batch_decisions.get("a" * 64))
        migrated = DecisionLedger(self.path)
        self.assertEqual(migrated.lookup(request_value), saved)
        self.assertEqual(migrated.learning_snapshots.get("a" * 64), None)
        connection = sqlite3.connect(self.path)
        try:
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 3)
            tables = {row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
            self.assertEqual(tables, {"decision_records", "learning_snapshots", "batch_decisions"})
        finally:
            connection.close()

    def test_writable_schema_two_ledger_migrates_additively_and_read_only_schema_two_remains_valid(self):
        request_value = request()
        saved_decision = self.ledger.persist(request_value, _record(request_value))
        events, contexts, route_id, target = _learning_sources()
        saved_snapshot = self._persist_learning_snapshot(events, contexts, route_id, target)
        connection = sqlite3.connect(self.path)
        try:
            connection.execute("DROP TABLE batch_decisions")
            connection.execute("PRAGMA user_version = 2")
        finally:
            connection.close()

        legacy = DecisionLedger(self.path, create=False)
        self.assertEqual(legacy.lookup(request_value), saved_decision)
        self.assertEqual(legacy.learning_snapshots.get(saved_snapshot.source_fingerprint), saved_snapshot)
        self.assertIsNone(legacy.batch_decisions.get("a" * 64))

        migrated = DecisionLedger(self.path)
        self.assertEqual(migrated.lookup(request_value), saved_decision)
        self.assertEqual(migrated.learning_snapshots.get(saved_snapshot.source_fingerprint), saved_snapshot)
        self.assertIsNone(migrated.batch_decisions.get("a" * 64))
        connection = sqlite3.connect(self.path)
        try:
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 3)
            tables = {row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
            self.assertEqual(tables, {"decision_records", "learning_snapshots", "batch_decisions"})
        finally:
            connection.close()


if __name__ == "__main__":
    unittest.main()
