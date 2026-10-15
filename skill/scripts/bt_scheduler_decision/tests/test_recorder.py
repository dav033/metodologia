from __future__ import annotations

import dataclasses
import sqlite3
import stat
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from bt_scheduler_decision import (
    API_VERSION,
    Confidence,
    DecisionLedger,
    DecisionLedgerError,
    DecisionRecord,
    RouteSummary,
    decision_id_for,
    executor_reference,
    idempotency_key,
    rank_candidates,
    resolve_executor_reference,
    validate_request,
)
from bt_scheduler_decision.tests.support import candidate, request


def _summary(item):
    return RouteSummary(item.route_id, item.provider, item.model, item.profile, item.account_ref, item.effort,
                        item.baseline_rank, ("baseline_route",))


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


class DecisionLedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "state" / "m2.sqlite3"
        self.ledger = DecisionLedger(self.path)

    def tearDown(self):
        self.temp.cleanup()

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


if __name__ == "__main__":
    unittest.main()
