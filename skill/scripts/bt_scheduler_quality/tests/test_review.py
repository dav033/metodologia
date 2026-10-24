from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from bt_scheduler_quality.engine import QualityEngine
from bt_scheduler_quality.policy import QualityPolicy
from bt_scheduler_quality.review import ReviewerEvidence
from bt_scheduler_quality.runner import CommandOutcome
from bt_scheduler_quality.store import QualityStore
from test_snapshot import _make_snapshot

ORDER_FIXTURE = Path(__file__).parent / "fixtures" / "verify-order-pass.json"


class FixedRunner:
    def run(self, check, snapshot_root, *, timeout_seconds=None, mounts=()):
        return CommandOutcome("pass", 0, 1, b"ok\n", b"", None, True)


class FixedReviewer:
    def __init__(
        self,
        *,
        identity="quality-reviewer",
        approved=True,
        subject="",
        evidence="reviewed m6 result",
    ):
        self.identity, self.approved, self.subject, self.evidence = (
            identity,
            approved,
            subject,
            evidence,
        )

    def review(self, order, result):
        subject_hash = self.subject or order.input_hash
        return ReviewerEvidence(
            self.identity, self.approved, self.evidence, subject_hash
        )


class IndependentReviewTests(unittest.TestCase):
    def _verify(self, *, reviewer=None, required=True, author="", secrets=()):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        _, source, _, _ = _make_snapshot(root)
        order = json.loads(ORDER_FIXTURE.read_text(encoding="utf-8"))
        if author:
            order["verification"][0]["created_by"] = author
        store = QualityStore(":memory:")
        self.addCleanup(store.close)
        engine = QualityEngine(
            QualityPolicy(require_independent_review=required, secret_values=secrets),
            store,
            runner=FixedRunner(),
            reviewer=reviewer,
        )
        result = engine.verify(order, source)
        manifest = store.get_result_manifest(result["evidence_manifest"])
        return result, json.loads(manifest)

    def test_review_is_disabled_by_default(self):
        result, manifest = self._verify(required=False)

        self.assertEqual(result["status"], "PASS")
        self.assertNotIn("independent_review", manifest["context"])

    def test_missing_required_reviewer_means_needs_review(self):
        result, _ = self._verify()

        self.assertEqual(result["status"], "NEEDS_REVIEW")
        self.assertEqual(result["reason_code"], "BLOCKED_EXTERNAL")
        self.assertIn("REVIEW_REQUIRED", {item["code"] for item in result["issues"]})

    def test_independent_evidence_is_bound_to_order_and_persisted(self):
        result, manifest = self._verify(reviewer=FixedReviewer())

        self.assertEqual(result["status"], "PASS")
        evidence = manifest["context"]["independent_review"]
        self.assertEqual(evidence["reviewer_identity"], "quality-reviewer")
        self.assertEqual(evidence["subject_hash"], result["input"]["order_sha256"])

    def test_same_as_author_identity_is_not_an_independent_review(self):
        result, _ = self._verify(
            reviewer=FixedReviewer(identity="builder-7"), author="builder-7"
        )

        self.assertEqual(result["status"], "NEEDS_REVIEW")
        self.assertEqual(result["reason_code"], "BLOCKED_EXTERNAL")
        self.assertIn(
            "REVIEW_NOT_INDEPENDENT", {item["code"] for item in result["issues"]}
        )

    def test_reviewer_decision_for_another_order_is_not_accepted(self):
        result, _ = self._verify(reviewer=FixedReviewer(subject="0" * 64))

        self.assertEqual(result["status"], "NEEDS_REVIEW")
        self.assertEqual(result["reason_code"], "BLOCKED_EXTERNAL")
        self.assertIn("REVIEW_INVALID", {item["code"] for item in result["issues"]})

    def test_reviewer_rejection_produces_fail(self):
        result, _ = self._verify(reviewer=FixedReviewer(approved=False))

        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["reason_code"], "FAIL_CODE")
        self.assertIn("REVIEW_REJECTED", {item["code"] for item in result["issues"]})

    def test_reviewer_evidence_cannot_persist_configured_secrets(self):
        secret = "m6-review-test-secret"
        result, _ = self._verify(
            reviewer=FixedReviewer(evidence=f"review included {secret}"),
            secrets=(secret,),
        )

        self.assertEqual(result["status"], "NEEDS_REVIEW")
        self.assertEqual(result["reason_code"], "BLOCKED_EXTERNAL")
        self.assertIn("REVIEW_INVALID", {item["code"] for item in result["issues"]})


if __name__ == "__main__":
    unittest.main()
