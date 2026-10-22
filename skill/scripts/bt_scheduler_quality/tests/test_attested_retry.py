"""REQ-030 step 4: a review that only waited for manual evidence is verified again once the evidence is attested."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from bt_scheduler_quality.contracts import QualityError, VerifyRequest
from bt_scheduler_quality.engine import QualityEngine
from bt_scheduler_quality.policy import QualityPolicy
from bt_scheduler_quality.store import QualityStore
from test_reuse import Runner, order
from test_snapshot import _make_snapshot


def manual_order(attempt="att-1"):
    raw = order(attempt, "python3 -m unittest -q")
    raw["verification"].append({"type": "manual", "value": "open it on a phone", "purpose": raw["acceptance_criteria"][0],
                                "expected": "it renders"})
    return raw


class AttestedRetry(unittest.TestCase):
    def test_a_review_that_waited_for_manual_evidence_is_requeued_once_and_then_passes(self):
        receipts = {}
        with tempfile.TemporaryDirectory() as tmp, QualityStore(":memory:") as store:
            _, source, _, _ = _make_snapshot(Path(tmp))
            engine = QualityEngine(QualityPolicy(), store, runner=Runner(),
                                   attestations=lambda order_, spec: receipts.get(spec.purpose))
            first = engine.verify(manual_order(), source)
            self.assertEqual(first["status"], "NEEDS_REVIEW")
            self.assertEqual(store.open_reviews_of("T-001"), ("verify:T-001:att-1",))
            self.assertEqual(store.open_reviews_of("T-999"), ())
            self.assertEqual(store.open_review_attempts("T-001"), ("att-1",))               # what a receipt binds to (REQ-029 A11)
            self.assertEqual(store.open_review_attempts("T-999"), ())
            receipts["check 1 holds"] = "sha256:abc"
            store.retry_attested("verify:T-001:att-1", "david", "attested: opened it on a phone and saw it render")
            self.assertEqual(store.open_reviews_of("T-001"), ())
            self.assertTrue(store.claim_work("verify:T-001:att-1"))
            request = VerifyRequest.from_mapping(manual_order())
            second = engine.process_reserved(request, source)
            self.assertEqual(second["status"], "PASS")
            with self.assertRaises(QualityError) as caught:                                  # one retry per request
                store.retry_attested("verify:T-001:att-1", "david", "again")
            self.assertIn(caught.exception.code, {"RETRY_INVALID", "RETRY_EXHAUSTED"})

    def test_a_review_about_more_than_manual_evidence_is_not_requeued(self):
        with tempfile.TemporaryDirectory() as tmp, QualityStore(":memory:") as store:
            _, source, _, _ = _make_snapshot(Path(tmp))
            raw = order("att-1", "python3 -m unittest -q")
            raw["acceptance_criteria"].append("nobody checks this")                          # CRITERION_UNVERIFIABLE
            QualityEngine(QualityPolicy(), store, runner=Runner()).verify(raw, source)
            with self.assertRaises(QualityError) as caught:
                store.retry_attested("verify:T-001:att-1", "david", "attested")
            self.assertEqual(caught.exception.code, "RETRY_INVALID")


if __name__ == "__main__":
    unittest.main()
