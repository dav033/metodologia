"""Plain post-verification guards reject a candidate instead of stranding its verdict."""
import unittest
from types import SimpleNamespace

from bitacora_platform import conflict_publisher
from bt_scheduler_recovery.conflict_delivery import EvidenceUnavailable, publish_or_raise


class ConflictPublisherTests(unittest.TestCase):
    def setUp(self):
        self.order = SimpleNamespace(plan_id="REQ-1", revision=4, task_id="T13", attempt_id="att-70")
        self.plan = SimpleNamespace(sha256="a" * 64)

    def publish(self, clash):
        return publish_or_raise(lambda *args: conflict_publisher.publish(object(), self.plan, *args),
                                self.order, clash, "ordinary_rework_refused", "not an accepted task")

    def test_foreign_file_deletion_is_delivered_as_a_plain_rejection(self):
        clash = "INTEGRATION_FILES_LOST T13 deletes files of accepted tasks it does not declare (T14: src/app/components/[id]/page.tsx)"
        self.assertIsNone(self.publish(clash))

    def test_marker_and_revert_guards_do_not_require_nonexistent_merge_observations(self):
        for clash in ["merge conflict markers left in: src/a.ts", "files changed back to an older version than the base they started from: src/a.ts"]:
            with self.subTest(clash=clash):
                self.assertIsNone(self.publish(clash))

    def test_unknown_or_missing_structural_evidence_still_refuses_delivery(self):
        with self.assertRaises(EvidenceUnavailable):
            self.publish("T13 vs T14 for T15: src/a.ts")
        with self.assertRaises(EvidenceUnavailable):
            self.publish("T13 vs T14 for T15: src/a.ts | conflict evidence: conflict:" + "a" * 64)
