from __future__ import annotations

import dataclasses
import json
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from bt_scheduler_decision import DecisionLedger, DecisionLedgerError
from bt_scheduler_decision.batch_ledger import _decode_batch_plan
from bt_scheduler_decision.batch_quota_evidence import (
    BATCH_EVIDENCE_VERSION,
    BatchQuotaEvidence,
)
from bt_scheduler_decision.contracts import API_VERSION
from bt_scheduler_decision.identity import canonical_json, sha256_json
from bt_scheduler_decision.policy import ROUTE_POLICY_VERSION
from bt_scheduler_decision.tests.support import candidate, request, task_facts


class BatchDecisionLedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "state" / "m2.sqlite3"
        self.ledger = DecisionLedger(self.path)

    def tearDown(self):
        self.temp.cleanup()

    def test_batch_replay_persists_selection_exclusions_and_no_assignment_reasons(self):
        unavailable = dataclasses.replace(candidate(profile="unavailable"), runtime_status="unavailable")
        requests = (
            request(task=task_facts(task_id="T1"), candidates=(candidate(profile="eligible"),)),
            request(task=task_facts(task_id="T2"), candidates=(unavailable,)),
        )

        plan = self.ledger.batch_decisions.persist(requests)
        replay = self.ledger.batch_decisions.get(plan.input_sha256)

        self.assertEqual(replay, plan)
        self.assertEqual(plan.assignments[0].task_id, "T1")
        self.assertEqual(plan.assignments[0].reason_code, "route_policy_preferred")
        self.assertEqual(plan.unassigned[0].task_id, "T2")
        self.assertEqual(plan.unassigned[0].reason_code, "no_eligible_route")
        self.assertEqual(plan.route_exclusions[0].task_id, "T2")
        self.assertEqual(plan.route_exclusions[0].reason_codes, ("runtime_unavailable",))
        serialized = json.dumps(dataclasses.asdict(plan), sort_keys=True)
        self.assertNotIn("Update the validated scheduler route safely.", serialized)

    def test_batch_replay_persists_allowlisted_quota_evidence_for_selected_and_excluded_routes(self):
        selected = candidate(profile="selected", rank=0, observed_at=99.0, valid_until=120.0)
        excluded = dataclasses.replace(candidate(profile="stale"), quota_status="stale",
                                       quota_observed_at=80.0, quota_valid_until=90.0,
                                       quota_used_percent=72.0)
        request_value = request(task=task_facts(task_id="T1"), candidates=(selected, excluded))
        evidence = {
            selected.route_id: BatchQuotaEvidence(BATCH_EVIDENCE_VERSION, "T1", selected.route_id,
                selected.profile, selected.account_ref, "fresh", 99.0, 120.0, 12.0, "quota_fresh"),
            excluded.route_id: BatchQuotaEvidence(BATCH_EVIDENCE_VERSION, "T1", excluded.route_id,
                excluded.profile, excluded.account_ref, "stale", 80.0, 90.0, 72.0, "quota_observation_stale"),
        }
        plan = self.ledger.batch_decisions.persist((request_value,), quota_evidence_by_task={"T1": evidence})
        replay = self.ledger.batch_decisions.get(plan.input_sha256)
        self.assertEqual(replay, plan)
        self.assertEqual(plan.schema_version, "1.3.0")
        self.assertEqual([row.state for row in plan.quota_evidence], ["fresh", "stale"])
        encoded = json.dumps(dataclasses.asdict(plan), sort_keys=True)
        self.assertNotIn("Update the validated scheduler route safely.", encoded)
        self.assertNotIn("credential", encoded.lower())

    def test_legacy_v12_batch_payload_remains_readable(self):
        policy_version = "m2-bounded-batch-v1"
        input_sha256 = "a" * 64
        batch_id = sha256_json({"batch_policy_version": policy_version, "input_sha256": input_sha256})
        payload = {
            "schema_version": API_VERSION, "batch_policy_version": policy_version,
            "route_policy_version": ROUTE_POLICY_VERSION, "batch_id": batch_id,
            "input_sha256": input_sha256, "free_slots": 1, "considered_task_count": 1,
            "assignments": [], "unassigned": [{"task_id": "T1", "reason_code": "no_eligible_route"}],
            "route_exclusions": [],
        }
        serialized = canonical_json(payload)
        plan = _decode_batch_plan(serialized, sha256_json(payload))
        self.assertEqual(plan.batch_policy_version, policy_version)
        self.assertEqual(plan.quota_evidence, ())

    def test_batch_replay_is_order_independent_and_concurrent_writes_are_idempotent(self):
        requests = (
            request(task=task_facts(task_id="T1"), candidates=(candidate(profile="first"),)),
            request(task=task_facts(task_id="T2"), candidates=(candidate(profile="second"),)),
        )

        def persist(index):
            order = requests if index % 2 == 0 else tuple(reversed(requests))
            return self.ledger.batch_decisions.persist(order)

        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(persist, range(16)))

        self.assertEqual(len({item.batch_id for item in results}), 1)
        self.assertEqual(len({item.input_sha256 for item in results}), 1)
        self.assertEqual(len({item.assignments for item in results}), 1)
        connection = sqlite3.connect(self.path)
        try:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM batch_decisions").fetchone()[0], 1)
        finally:
            connection.close()

    def test_changed_batch_snapshot_creates_a_new_content_addressed_decision(self):
        original_request = request()
        first = self.ledger.batch_decisions.persist((original_request,))
        changed_candidate = dataclasses.replace(candidate(), quota_used_percent=31.0)
        changed_request = request(candidates=(changed_candidate,))
        second = self.ledger.batch_decisions.persist((changed_request,))

        self.assertNotEqual(first.input_sha256, second.input_sha256)
        self.assertNotEqual(first.batch_id, second.batch_id)
        self.assertEqual(self.ledger.batch_decisions.get(first.input_sha256), first)
        self.assertEqual(self.ledger.batch_decisions.get(second.input_sha256), second)
        connection = sqlite3.connect(self.path)
        try:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM batch_decisions").fetchone()[0], 2)
        finally:
            connection.close()

    def test_corrupt_batch_decision_fails_closed(self):
        plan = self.ledger.batch_decisions.persist((request(),))
        connection = sqlite3.connect(self.path)
        try:
            connection.execute("DROP TRIGGER batch_decisions_immutable_update")
            connection.execute("UPDATE batch_decisions SET plan_json = '{}' WHERE input_sha256 = ?",
                               (plan.input_sha256,))
            connection.commit()
        finally:
            connection.close()

        with self.assertRaisesRegex(DecisionLedgerError, "batch_decision_corrupt"):
            self.ledger.batch_decisions.get(plan.input_sha256)

    def test_batch_decisions_are_immutable_and_payload_size_is_bounded_before_write(self):
        requests = (request(),)
        with patch("bt_scheduler_decision.batch_ledger.MAX_BATCH_RECORD_BYTES", 1), \
                self.assertRaisesRegex(DecisionLedgerError, "batch_decision_too_large"):
            self.ledger.batch_decisions.persist(requests)
        connection = sqlite3.connect(self.path)
        try:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM batch_decisions").fetchone()[0], 0)
        finally:
            connection.close()

        with patch("bt_scheduler_decision.batch_ledger.MAX_BATCH_RECORDS", 0), \
                self.assertRaisesRegex(DecisionLedgerError, "batch_decision_store_full"):
            self.ledger.batch_decisions.persist(requests)
        connection = sqlite3.connect(self.path)
        try:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM batch_decisions").fetchone()[0], 0)
        finally:
            connection.close()

        plan = self.ledger.batch_decisions.persist(requests)
        connection = sqlite3.connect(self.path)
        try:
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("UPDATE batch_decisions SET plan_json = '{}' WHERE batch_id = ?",
                                   (plan.batch_id,))
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("DELETE FROM batch_decisions WHERE batch_id = ?", (plan.batch_id,))
        finally:
            connection.close()
