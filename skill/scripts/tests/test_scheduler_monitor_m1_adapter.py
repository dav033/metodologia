from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bt_scheduler_monitor.contracts import Incident
from bt_scheduler_monitor.store import MonitorStore
from bt_scheduler_monitor_adapter import deliver_incident_outbox

NOW = "2026-10-15T16:00:00Z"


def make_incident(attempt_id: str) -> Incident:
    return Incident("1.0.0", "sha256:" + "b" * 64, "runtime-run-1", "T1", attempt_id, "exec-1",
                    "missed_heartbeat", "missed_heartbeat", "medium", "high", NOW, NOW, 1, (), (), "open")


class FakeScheduler:
    contract_version = "1.2.0"

    def __init__(self, statuses: tuple[str, ...] = ("applied",)) -> None:
        self.plan = type("Plan", (), {"plan_id": "REQ-T", "revision": 1})()
        self.statuses = list(statuses)
        self.events: list[dict[str, object]] = []

    def ingest(self, event: dict[str, object]):
        self.events.append(event)
        status = self.statuses.pop(0)
        return type("Result", (), {"status": status})()


class MonitorM1AdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.store = MonitorStore(Path(self.temp.name) / "monitor.sqlite3")
        self.scheduler = FakeScheduler()
        incident = make_incident("attempt-1")
        self.key = "sha256:" + "a" * 64
        self.store.enqueue_incident(incident, self.key)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_outbox_delivers_versioned_audit_event_and_acknowledges_applied(self):
        report = deliver_incident_outbox(self.store, self.scheduler, "worker", now=1)
        self.assertEqual((report.status, report.claimed, report.applied, report.pending), ("complete", 1, 1, 0))
        event = self.scheduler.events[0]
        self.assertEqual((event["kind"], event["source"], event["contract_version"]),
                         ("incident_observed", "m4", "1.2.0"))
        self.assertEqual(event["payload"]["run_id"], "runtime-run-1")
        self.assertEqual(self.store.claim_outbox("worker-2", now=2, lease_seconds=5), ())

    def test_unsupported_m1_capability_leaves_outbox_unclaimed(self):
        class OldScheduler:
            contract_version = "1.1.0"

        report = deliver_incident_outbox(self.store, OldScheduler(), "worker", now=1)
        self.assertEqual(report.status, "unsupported_contract")
        claim, = self.store.claim_outbox("worker-2", now=1, lease_seconds=5)
        self.assertEqual(claim.idempotency_key, self.key)

    def test_scheduler_without_a_declared_capability_leaves_outbox_unclaimed(self):
        class UnversionedScheduler:
            pass

        report = deliver_incident_outbox(self.store, UnversionedScheduler(), "worker", now=1)
        self.assertEqual(report.status, "unsupported_contract")
        claim, = self.store.claim_outbox("worker-2", now=1, lease_seconds=5)
        self.assertEqual(claim.idempotency_key, self.key)

    def test_duplicate_is_acknowledged_after_a_crash_between_apply_and_ack(self):
        scheduler = FakeScheduler(("applied", "duplicate"))
        acknowledge = self.store.ack_outbox
        self.store.ack_outbox = lambda *_args: False
        report = deliver_incident_outbox(self.store, scheduler, "worker", now=1, lease_seconds=1)
        self.store.ack_outbox = acknowledge
        self.assertEqual(report.pending, 1)
        report = deliver_incident_outbox(self.store, scheduler, "worker-2", now=3)
        self.assertEqual((report.duplicate, report.pending), (1, 0))

    def test_non_applied_result_is_retried_with_safe_code_only(self):
        class RejectingScheduler:
            plan = FakeScheduler().plan
            contract_version = "1.2.0"

            @staticmethod
            def ingest(_event):
                return type("Result", (), {"status": "invalid"})()

        report = deliver_incident_outbox(self.store, RejectingScheduler(), "worker", now=1)
        self.assertEqual(report.pending, 1)
        claim, = self.store.claim_outbox("worker-2", now=2, lease_seconds=5)
        self.assertEqual(claim.idempotency_key, self.key)

    def test_known_boundary_failures_are_retried_without_acknowledging(self):
        class UnavailableScheduler:
            plan = FakeScheduler().plan
            contract_version = "1.2.0"

            @staticmethod
            def ingest(_event):
                raise OSError("M1 storage unavailable")

        report = deliver_incident_outbox(self.store, UnavailableScheduler(), "worker", now=1)
        self.assertEqual((report.claimed, report.pending, report.applied), (1, 1, 0))
        claim, = self.store.claim_outbox("worker-2", now=32, lease_seconds=5)
        self.assertEqual(claim.idempotency_key, self.key)

    def test_unexpected_programming_errors_are_not_swallowed(self):
        class BrokenScheduler:
            plan = FakeScheduler().plan
            contract_version = "1.2.0"

            @staticmethod
            def ingest(_event):
                raise TypeError("unexpected adapter bug")

        with self.assertRaisesRegex(TypeError, "unexpected adapter bug"):
            deliver_incident_outbox(self.store, BrokenScheduler(), "worker", now=1)
        claim, = self.store.claim_outbox("worker-2", now=32, lease_seconds=5)
        self.assertEqual(claim.idempotency_key, self.key)


if __name__ == "__main__":
    unittest.main()
