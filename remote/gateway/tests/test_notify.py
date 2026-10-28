import copy
import json
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


# Real feed events, validated against the contract by test_remote_contracts.
EVENTS = json.loads((Path(__file__).resolve().parents[2] / "contract" / "fixtures" / "events.json")
                    .read_text(encoding="utf-8"))


def fresh(event):
    """A fixture event that just happened: the outbox drops messages older than an hour."""
    from datetime import datetime, timezone
    return {**copy.deepcopy(event), "occurredAt": datetime.now(timezone.utc).isoformat(timespec="seconds")}


def make_config(database_path):
    return GatewayConfig("http://127.0.0.1:18765", "key", "token", "chat", database_path)


def feed_event(event_id, event_type="attempt.failed"):
    return {
        "id": event_id,
        "dedupeKey": event_id,
        "type": event_type,
        "target": {"project": "demo", "req": "REQ-027"},
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

    def env_runtime(self, origin):
        env = {"LAPTOP_ORIGIN": "http://127.0.0.1:18765", "FLOW_GATEWAY_KEY": "key", "TELEGRAM_BOT_TOKEN": "token",
               "TELEGRAM_CHAT_ID": "chat", "GATEWAY_DATABASE": str(self.database_path)}
        if origin is not None:
            env["FLOW_FRONTEND_ORIGIN"] = origin
        return GatewayRuntime(GatewayConfig.from_env(env), laptop=self.laptop, sender=self.sent.append)

    def test_f10_failure_notification_carries_cause_and_review_link_without_secrets(self):
        event = fresh(EVENTS[0])
        event["data"]["failure"] = "tests failed: GITHUB_TOKEN=ghp_abcdefghijklmnopqrstuvwxyz123456 " + "x" * 600
        self.laptop.feed = [event]
        self.env_runtime("https://flow.example.test/").poll_once()

        message = self.sent[0]
        self.assertIn("Una tarea falló", message)
        self.assertIn("lotm/REQ-027 · T15a", message)
        self.assertIn("Causa: tests failed", message)
        self.assertIn("https://flow.example.test/review?project=lotm&req=REQ-027&taskId=T15a#attempt-att-0008", message)
        self.assertNotIn("ghp_", message)
        self.assertLess(len(message), 600)

    def test_f10_notification_without_frontend_origin_or_task_has_no_link(self):
        quota = fresh(EVENTS[2])
        quota["type"] = "attempt.blocked"
        failure = fresh(EVENTS[0])
        self.laptop.feed = [failure, quota]
        self.env_runtime(None).poll_once()
        self.assertIn("Causa: La verificación terminó", self.sent[0])
        self.assertNotIn("http", self.sent[0])
        self.assertEqual(self.sent[1], "Una tarea quedó bloqueada.")


if __name__ == "__main__":
    unittest.main()
