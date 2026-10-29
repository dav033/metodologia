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

from bt_durable.adapters.m6 import M6Verifier
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

    def test_nothing_to_recover_changes_nothing(self):
        self.assertEqual(self.verifier.recover_interrupted(), ())


if __name__ == "__main__":
    unittest.main()
