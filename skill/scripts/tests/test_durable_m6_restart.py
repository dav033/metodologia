"""A verification cut short by an engine restart runs again once (D-171). pictures REQ-021 T95, 2026-10-29 18:44: the
restart killed the verifier, the re-run DBOS step met its own orphaned M6 request (REQUEST_IN_PROGRESS) and the task
waited for the owner as a runtime defect."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bt_contracts.failure import Budget, FailureClass, RecoveryAction, Spent
from bt_durable.adapters.m6 import M6Verifier, outcome_of
from bt_durable.control import classify, policy
from bt_scheduler_quality.contracts import QualityError, VerifyRequest
from bt_scheduler_quality.engine import QualityEngine
from bt_scheduler_quality.policy import QualityPolicy

ORDER = {"idempotency_key": "bt:p-REQ-1-r1-T1-a1-x:verify", "plan_id": "REQ-1", "revision": 1, "task_id": "T1",
         "attempt_id": "att-1", "token": 1, "acceptance_criteria": ["ok"],
         "verification": [{"type": "command", "value": "true", "purpose": "ok"}]}


class RestartedVerification(unittest.TestCase):
    def setUp(self):
        self.verifier = M6Verifier(store_path=Path(tempfile.mkdtemp(prefix="bt-m6-restart-")) / "m6" / "m6.sqlite3")
        self.store = self.verifier.store
        self.order = VerifyRequest.from_mapping(ORDER)
        self.engine = QualityEngine(QualityPolicy(), self.store)

    def tearDown(self):
        self.verifier.close()

    def interrupted(self):                       # a verifier claimed the request, then its engine stopped
        self.store.reserve(self.order)
        self.assertTrue(self.store.claim_work(self.order.idempotency_key))

    def test_without_recovery_the_rerun_step_meets_its_orphaned_request(self):
        self.interrupted()
        with self.assertRaisesRegex(QualityError, "active verifier"):
            self.engine.verify(self.order, None)

    def test_after_a_restart_the_same_request_is_verified_again(self):
        self.interrupted()
        self.assertEqual(self.verifier.recover_interrupted(), (self.order.idempotency_key,))
        self.assertEqual(self.store.reserve(self.order)[0], "queued")
        with mock.patch.object(QualityEngine, "process_reserved", return_value={"status": "PASS"}) as ran:
            self.assertEqual(self.engine.verify(self.order, None), {"status": "PASS"})
        ran.assert_called_once()
        self.assertEqual(self.store.reserve(self.order)[0], "running")

    def test_a_second_interruption_stays_for_review(self):
        self.interrupted()
        self.verifier.recover_interrupted()
        self.assertTrue(self.store.claim_work(self.order.idempotency_key))
        self.assertEqual(self.verifier.recover_interrupted(), ())
        state, result = self.store.reserve(self.order)
        self.assertEqual((state, result["status"]), ("existing", "NEEDS_REVIEW"))

    def test_exhausted_restart_recovery_uses_bounded_snapshot_reverification(self):
        self.interrupted()
        self.verifier.recover_interrupted()
        self.assertTrue(self.store.claim_work(self.order.idempotency_key))
        self.assertEqual(self.verifier.recover_interrupted(), ())
        _, result = self.store.reserve(self.order)
        self.assertEqual(result["reason_code"], "BLOCKED_ENV")
        verdict = outcome_of(result, self.store)
        failure = classify.classify(classify.AttemptFacts(verify=verdict))
        self.assertEqual((failure.failure_class, failure.code),
                         (FailureClass.VERIFICATION, "ENGINE_INTERRUPTED"))
        self.assertIn("interrupted", failure.summary.lower())
        self.assertIn("ENGINE_INTERRUPTED", [item.excerpt for item in failure.evidence])
        first = policy.decide(failure, Spent(attempts=1), Budget(), now=0, other_route=False)
        self.assertEqual(first.action, RecoveryAction.REPAIR_ENVIRONMENT)
        self.assertIn(failure.code, policy.REVERIFY)
        exhausted = policy.decide(failure, Spent(attempts=1, environment_repairs=1), Budget(),
                                  now=0, other_route=False)
        self.assertEqual((exhausted.action, exhausted.limit_hit),
                         (RecoveryAction.ESCALATE, "max_environment_repairs"))
        historical = policy.decide(failure, Spent(attempts=1), Budget(), now=0, other_route=False,
                                   interrupted_reverify=False)
        self.assertEqual(historical.action, RecoveryAction.ESCALATE)

    def test_interruption_never_hides_other_review_issues(self):
        from bt_contracts.execution import VerifyOutcome

        for reason, issues, expected in (
            ("BLOCKED_ENV", ("ENGINE_INTERRUPTED", "CHECK_UNAVAILABLE"), FailureClass.ENVIRONMENT),
            ("BLOCKED_ENV", (), FailureClass.ENVIRONMENT),
            ("AUTHORIZATION_DENIED", ("ENGINE_INTERRUPTED",), FailureClass.PERMISSION),
            ("CHECK_MANUAL", ("ENGINE_INTERRUPTED", "CRITERION_MANUAL"), FailureClass.PRODUCT_DECISION),
        ):
            with self.subTest(reason=reason, issues=issues):
                verdict = VerifyOutcome(status="NEEDS_REVIEW", reason_code=reason, issue_codes=issues)
                failure = classify.classify(classify.AttemptFacts(verify=verdict))
                self.assertEqual(failure.failure_class, expected)
                self.assertNotIn(failure.code, policy.REVERIFY)

    def test_workflow_patch_keeps_historical_escalation_and_enables_new_reverification(self):
        from bt_contracts.execution import VerifyOutcome
        from bt_durable.execution import recovery_policy

        failure = classify.classify(classify.AttemptFacts(verify=VerifyOutcome(
            status="NEEDS_REVIEW", reason_code="BLOCKED_ENV", issue_codes=("ENGINE_INTERRUPTED",))))
        for patched, expected in ((False, RecoveryAction.ESCALATE), (True, RecoveryAction.REPAIR_ENVIRONMENT)):
            with self.subTest(patched=patched), mock.patch.object(recovery_policy.DBOS, "patch",
                                                                 return_value=patched) as patch:
                decision = recovery_policy.decide(failure, Spent(attempts=1), Budget(), now=0, other_route=False)
                self.assertEqual(decision.action, expected)
                patch.assert_called_once_with(recovery_policy.PATCH_INTERRUPTED_REVERIFY)

        missing = classify.classify(classify.AttemptFacts(verify=VerifyOutcome(
            status="NEEDS_REVIEW", reason_code="BLOCKED_ENV", issue_codes=("CHECK_UNAVAILABLE",))))
        with mock.patch.object(recovery_policy.DBOS, "patch") as patch:
            decision = recovery_policy.decide(missing, Spent(), Budget(), now=0, other_route=False)
            self.assertEqual(decision.action, RecoveryAction.ESCALATE)
            patch.assert_not_called()

    def test_nothing_to_recover_changes_nothing(self):
        self.assertEqual(self.verifier.recover_interrupted(), ())


if __name__ == "__main__":
    unittest.main()
