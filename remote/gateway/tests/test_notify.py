import json
import os
import socket
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import GatewayRuntime, create_runtime
from config import GatewayConfig
from main import main
from notifications import NotificationOutbox, notification_for_event
from upstream import UpstreamError


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def failed_event(event_id="event-1", key="attempt-1-failed"):
    return {"schemaVersion": 1, "id": event_id, "cursor": event_id, "type": "attempt.failed",
            "occurredAt": "2026-10-19T00:00:00Z",
            "target": {"kind": "task", "project": "demo", "req": "REQ-027"}, "data": {}, "dedupeKey": key}


class FakeLaptop:
    def __init__(self):
        self.health_results = []
        self.feed = []

    def health(self):
        if self.health_results and not self.health_results.pop(0):
            raise UpstreamError("offline")
        return {"status": "ok"}

    def events(self, after):
        feed, self.feed = self.feed, []
        return {"events": feed, "nextCursor": "c"}

    def snapshot(self):
        return {"runs": [{"status": "running"}]}


class FakeResponse:
    def __init__(self, body=b'{"ok": true}'):
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self._body


class NotifyTests(unittest.TestCase):
    def env(self, directory):
        return {"LAPTOP_ORIGIN": "http://127.0.0.1:18765", "FLOW_GATEWAY_KEY": "k",
                "TELEGRAM_BOT_TOKEN": "tok", "TELEGRAM_CHAT_ID": "chat",
                "GATEWAY_DATABASE": str(Path(directory) / "g.sqlite"),
                "GITHUB_CLIENT_ID": "id", "GITHUB_CLIENT_SECRET": "secret",
                "SESSION_SECRET": "test-session-secret-with-more-than-32-bytes",
                "FLOW_FRONTEND_ORIGIN": "https://flow.example.test",
                "GATEWAY_BIND": "127.0.0.1", "GATEWAY_PORT": str(free_port())}

    def run_main(self, directory, laptop, cycles, offline_delay=15 * 60):
        """Run the production `main()` with real TelegramSender; capture Telegram HTTP posts."""
        posts = []

        def fake_urlopen(request, timeout=None):
            posts.append(json.loads(request.data.decode("utf-8")))
            return FakeResponse()

        def cycle(runtime):
            for _ in range(cycles):
                runtime.poll_once()

        with patch.dict(os.environ, self.env(directory), clear=True), \
                patch("app.LaptopClient", return_value=laptop), \
                patch("notifications.urlopen", fake_urlopen), \
                patch("app.OFFLINE_ALERT_DELAY_SECONDS", offline_delay), \
                patch.object(GatewayRuntime, "run_forever", cycle):
            self.assertEqual(main(), 0)
        return posts

    def test_main_delivers_event_to_telegram_with_review_button_once(self):
        with tempfile.TemporaryDirectory() as directory:
            laptop = FakeLaptop()
            laptop.feed = [failed_event(), failed_event("event-2")]  # same dedupe key
            posts = self.run_main(directory, laptop, 2)
            self.assertEqual(len(posts), 1)
            self.assertIn("Una tarea falló", posts[0]["text"])
            button = posts[0]["reply_markup"]["inline_keyboard"][0][0]
            self.assertEqual(button["url"], "https://flow.example.test/runs/demo/REQ-027")

    def test_restart_rereading_feed_sends_nothing_new(self):
        with tempfile.TemporaryDirectory() as directory:
            laptop = FakeLaptop()
            laptop.feed = [failed_event()]
            self.assertEqual(len(self.run_main(directory, laptop, 1)), 1)
            laptop.feed = [failed_event()]
            self.assertEqual(self.run_main(directory, laptop, 1), [])

    def test_offline_over_15_minutes_with_active_run_notifies_once_with_link(self):
        with tempfile.TemporaryDirectory() as directory:
            laptop = FakeLaptop()
            laptop.health_results = [True, False, False, False, False, False, False]
            clock = [1000.0]
            with patch("app.time.monotonic", lambda: clock[0]), patch("liveness.time.monotonic", lambda: clock[0]):
                posts = []

                def fake_urlopen(request, timeout=None):
                    posts.append(json.loads(request.data.decode("utf-8")))
                    return FakeResponse()

                def cycle(runtime):
                    runtime.poll_once()
                    for _ in range(3):
                        runtime.poll_once()
                    self.assertEqual(posts, [])  # offline, but under 15 minutes
                    clock[0] += 16 * 60
                    runtime.poll_once()
                    runtime.poll_once()

                with patch.dict(os.environ, self.env(directory), clear=True), \
                        patch("app.LaptopClient", return_value=laptop), \
                        patch("notifications.urlopen", fake_urlopen), \
                        patch.object(GatewayRuntime, "run_forever", cycle):
                    self.assertEqual(main(), 0)
            self.assertEqual(len(posts), 1)
            self.assertIn("más de 15 minutos", posts[0]["text"])
            self.assertEqual(posts[0]["reply_markup"]["inline_keyboard"][0][0]["url"],
                             "https://flow.example.test")

    def test_rules_are_deterministic_and_outbox_dedupes(self):
        first = notification_for_event(failed_event(), "https://f.test")
        self.assertEqual(first, notification_for_event(failed_event("other"), "https://f.test"))
        self.assertIsNone(notification_for_event({"type": "noise", "id": "x", "dedupeKey": "k"}))
        outbox = NotificationOutbox(":memory:")
        self.assertTrue(outbox.enqueue(*first))
        self.assertFalse(outbox.enqueue(*first))


if __name__ == "__main__":
    unittest.main()
