import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import GatewayRuntime
from config import GatewayConfig
from upstream import UpstreamError


class FakeLaptop:
    def __init__(self):
        self.healthy = True
        self.snapshot_calls = 0
        self.feed = []

    def health(self):
        if not self.healthy:
            raise UpstreamError("offline")
        return {"status": "ok"}

    def snapshot(self):
        self.snapshot_calls += 1
        if not self.healthy:
            raise UpstreamError("offline")
        return {"runs": [{"status": "running"}]}

    def events(self, after):
        return {"events": self.feed, "nextCursor": "cursor-1"}


class FakeServer:
    def serve_forever(self):
        return None

    def shutdown(self):
        return None

    def server_close(self):
        return None


class NotificationTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.config = GatewayConfig(
            laptop_origin="http://127.0.0.1:18765",
            gateway_key="test-key",
            telegram_bot_token="test-token",
            telegram_chat_id="test-chat",
            database_path=Path(self.temporary_directory.name) / "gateway.sqlite",
        )

    def test_duplicate_feed_event_and_restart_replay_deliver_once(self):
        laptop = FakeLaptop()
        sent = []
        laptop.feed = [{
            "schemaVersion": 1,
            "id": "event-1",
            "cursor": "1",
            "type": "attempt.failed",
            "occurredAt": "2026-10-19T00:00:00Z",
            "target": {"kind": "task", "project": "demo", "req": "REQ-027"},
            "data": {},
            "dedupeKey": "attempt-1-failed",
        }]

        first_runtime = GatewayRuntime(self.config, laptop=laptop, sender=sent.append)
        self.addCleanup(first_runtime.outbox._db.close)
        first_runtime.poll_once()
        first_runtime.poll_once()

        restarted_runtime = GatewayRuntime(self.config, laptop=laptop, sender=sent.append)
        self.addCleanup(restarted_runtime.outbox._db.close)
        restarted_runtime.poll_once()

        self.assertEqual(len(sent), 1)
        self.assertIn("Una tarea falló", sent[0])

    def test_production_entrypoint_notifies_once_from_cached_active_run_after_offline_delay(self):
        from main import main

        laptop = FakeLaptop()
        sent = []
        current_time = [100.0]
        runtimes = []

        def run_production_cycles(runtime):
            runtimes.append(runtime)
            runtime.poll_once()
            laptop.healthy = False
            for _ in range(3):
                runtime.poll_once()
            current_time[0] += 901
            runtime.poll_once()
            runtime.poll_once()

        environment = {
            "LAPTOP_ORIGIN": self.config.laptop_origin,
            "FLOW_GATEWAY_KEY": self.config.gateway_key,
            "TELEGRAM_BOT_TOKEN": self.config.telegram_bot_token,
            "TELEGRAM_CHAT_ID": self.config.telegram_chat_id,
            "GATEWAY_DATABASE": str(self.config.database_path),
            "GITHUB_CLIENT_ID": "test-client-id",
            "GITHUB_CLIENT_SECRET": "test-client-secret",
            "SESSION_SECRET": "test-session-secret-with-more-than-32-bytes",
            "FLOW_FRONTEND_ORIGIN": "https://flow.example.test",
        }

        with patch.dict(os.environ, environment, clear=True), \
                patch("app.LaptopClient", return_value=laptop), \
                patch("app.TelegramSender", return_value=sent.append), \
                patch("main.create_server", return_value=FakeServer()), \
                patch("main.TelegramBot"), \
                patch("app.time.monotonic", side_effect=lambda: current_time[0]), \
                patch.object(GatewayRuntime, "run_forever", run_production_cycles):
            self.assertEqual(main(), 0)

        self.addCleanup(runtimes[0].outbox._db.close)
        offline_alerts = [message for message in sent if "más de 15 minutos" in message]
        self.assertEqual(len(offline_alerts), 1)
        self.assertEqual(laptop.snapshot_calls, 1)


if __name__ == "__main__":
    unittest.main()
