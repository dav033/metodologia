"""Only the live M1 attempt may receive receipts, and reading reviews never claims M6."""
import hashlib
import json
import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import bt_attestation
import bt_run_stores
import bt_scheduler_adapter as adapter
import bt_scheduler_ops as ops
from bt_scheduler_quality.contracts import VerifyRequest
from bt_scheduler_quality.evidence import canonical_json
from bt_scheduler_quality.store import QualityStore


class ReviewAttemptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.rdir = Path(self.temp.name) / "REQ-001-x"
        self.rdir.mkdir()
        db = adapter.run_db_path(self.rdir)
        with closing(sqlite3.connect(db)) as connection:
            connection.execute("CREATE TABLE state (id INTEGER, doc TEXT)")
            connection.execute("INSERT INTO state VALUES (1, ?)", (json.dumps({"revision": 17,
                "tasks": {"T14a": {"state": "active", "attempts": ["att-old", "att-current"]}},
                "attempts": {"att-old": {"state": "cancelled"}, "att-current": {"state": "verifying"}}}),))
            connection.commit()
        bt_run_stores.runtime_marker(db).write_text(json.dumps({"runtime_id": "a" * 32}))
        self.path = bt_run_stores.paths(self.rdir)["m6"]
        with QualityStore(self.path) as store:
            for attempt, revision in [("att-old", 7), ("att-current", 17)]:
                order = VerifyRequest.from_mapping({"idempotency_key": attempt, "plan_id": "REQ-001", "revision": revision,
                    "task_id": "T14a", "attempt_id": attempt, "token": revision, "acceptance_criteria": ["works"],
                    "verification": [{"type": "manual", "value": "observe", "purpose": "works", "expected": "evidence"}]})
                store.reserve(order)
                store.claim_work(order.idempotency_key)
                result = {"status": "NEEDS_REVIEW", "issues": [{"code": "CRITERION_MANUAL"}],
                          "evidence_manifest": "m6://result/" + hashlib.sha256(b"{}").hexdigest()}
                store.finish(order, result, canonical_json(result), b"{}", {})

    def test_stale_reviews_are_excluded_even_when_the_owner_is_stopped(self):
        self.assertEqual(ops.review_attempts(self.rdir, "T14a"), ("att-current",))

    def test_reading_review_attempts_does_not_change_store_permissions(self):
        self.path.chmod(0o400)
        ops.review_attempts(self.rdir, "T14a")
        self.assertEqual(os.stat(self.path).st_mode & 0o777, 0o400)

    def test_attesting_current_attempt_leaves_historical_reviews_untouched(self):
        check = {"type": "manual", "value": "observe", "purpose": "works", "expected": "evidence"}
        plan = SimpleNamespace(task=lambda _: SimpleNamespace(verification=[check]))
        with patch.object(ops, "bound_plan", return_value=plan), \
                patch.object(bt_attestation, "key_path", return_value=Path(self.temp.name) / "receipt.key"):
            lines = ops.attest("fixture-reviews", "REQ-001", self.rdir, "T14a", "", "Observed the live flow and recorded all required checks.",
                               expected_attempt="att-current")
        self.assertTrue(any("requeued" in line for line in lines))
        with QualityStore(self.path) as store:
            self.assertEqual(store.open_review_attempts("T14a"), ("att-old",))
            self.assertEqual(store.get_result("att-old")["status"], "NEEDS_REVIEW")
