import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import GatewayRuntime
from config import GatewayConfig
from upstream import UpstreamError


class FakeLaptop:
    def __init__(self):
        self.online = True
        self.feed = []
        self.snapshot_data = {"runs": []}

    def health(self):
        if not self.online:
            raise UpstreamError("offline")
        return {"status": "ok"}

    def snapshot(self):
        if not self.online:
            raise UpstreamError("offline")
        return self.snapshot_data

    def events(self, _after):
        return {"events": self.feed, "nextCursor": str(len(self.feed))}


def make_config(database_path):
    return GatewayConfig("http://127.0.0.1:18765", "key", "token", "chat", database_path)


def feed_event(event_id, event_type="attempt.failed"):
    return {
        "id": event_id,
        "dedupeKey": event_id,
        "type": event_type,
        "target": {"project": "demo", "req": "REQ-027", "taskId": "T1", "attemptId": "att-0001"},
        "data": {},
    }


class NotificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.database_path = Path(self.temp.name) / "gateway.sqlite"
        self.config = make_config(self.database_path)
        self.laptop = FakeLaptop()
        self.sent = []

    def runtime(self):
        return GatewayRuntime(self.config, laptop=self.laptop, sender=self.sent.append)

    def test_duplicate_event_yields_no_second_notification(self):
        runtime = self.runtime()
        self.laptop.feed = [feed_event("event-1"), feed_event("event-1")]

        runtime.poll_once()

        self.assertEqual(len(self.sent), 1)
        self.assertIn("Una tarea falló", self.sent[0])
        self.assertIn("/review?project=demo&req=REQ-027&taskId=T1#attempt-att-0001", self.sent[0])

    def test_duplicate_failure_sources_yield_one_notification_per_attempt(self):
        runtime = self.runtime()
        projection_event = feed_event("projection-event")
        projection_event["target"].update({"project": "demo", "taskId": "T1", "attemptId": "att-0001"})
        bus_event = feed_event("bus-event")
        bus_event["target"].update({"project": "demo", "taskId": "T1", "attemptId": "att-0001"})
        self.laptop.feed = [projection_event, bus_event]

        runtime.poll_once()

        self.assertEqual(len(self.sent), 1)

    def test_restart_rereading_feed_sends_nothing_new(self):
        self.laptop.feed = [feed_event("event-1"), feed_event("decision-2", "decision.requested")]
        self.runtime().poll_once()
        self.assertEqual(len(self.sent), 2)

        # The same feed page is replayed after a process restart; SQLite owns deduplication.
        self.runtime().poll_once()

        self.assertEqual(len(self.sent), 2)

    def test_offline_over_15_minutes_with_active_run_notifies_once(self):
        self.laptop.snapshot_data = {"runs": [{"id": "run-1", "status": "running"}]}
        runtime = self.runtime()
        runtime.poll_once()  # Cache the last known active run while the laptop is reachable.
        clock = [1000.0]
        self.laptop.online = False
        with patch("time.monotonic", side_effect=lambda: clock[0]), \
                patch("time.time", side_effect=lambda: 1_800_000_000 + clock[0]), \
                patch("app.OFFLINE_ALERT_DELAY_SECONDS", 15 * 60):
            for _ in range(3):
                runtime.poll_once()
            clock[0] += 901
            runtime.poll_once()
            self.assertEqual(len(self.sent), 1)

            # A restart during the same outage restores both its start time and dedupe state.
            restarted = self.runtime()
            clock[0] += 10
            restarted.poll_once()
            self.assertEqual(len(self.sent), 1)


if __name__ == "__main__":
    unittest.main()
