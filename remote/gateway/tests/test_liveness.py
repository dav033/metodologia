import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app import GatewayRuntime, create_runtime
from config import ConfigurationError, GatewayConfig
from liveness import LaptopStatus, LivenessMonitor
from main import main
from upstream import UpstreamError


class FakeLaptop:
    def __init__(self):
        self.healthy = True
        self.health_results = []
        self.feed = []

    def health(self):
        healthy = self.health_results.pop(0) if self.health_results else self.healthy
        if not healthy:
            raise UpstreamError("offline")
        return {"status": "ok"}

    def events(self, after):
        result = {"events": self.feed, "nextCursor": "cursor-1"}
        self.feed = []
        return result

    def snapshot(self):
        return {"runs": [{"status": "running"}]}


class LivenessTests(unittest.TestCase):
    def test_three_failed_probes_mark_laptop_offline_and_success_recovers(self):
        monitor = LivenessMonitor()
        self.assertIsNone(monitor.record_failure())
        self.assertIsNone(monitor.record_failure())
        transition = monitor.record_failure()
        self.assertEqual(transition.current, LaptopStatus.OFFLINE)
        self.assertEqual(monitor.status, LaptopStatus.OFFLINE)

        transition = monitor.record_success()
        self.assertEqual(transition.current, LaptopStatus.ONLINE)
        self.assertEqual(monitor.status, LaptopStatus.ONLINE)
        self.assertEqual(monitor.consecutive_failures, 0)

    def test_missing_configuration_refuses_production_entrypoint(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ConfigurationError):
                GatewayConfig.from_env()
            self.assertEqual(main(), 2)

    def test_production_composition_persists_liveness_and_event_delivery(self):
        with tempfile.TemporaryDirectory() as directory:
            laptop = FakeLaptop()
            sent = []
            laptop.health_results = [False, False, False, True]
            config = GatewayConfig(
                laptop_origin="http://127.0.0.1:18765",
                gateway_key="test-key",
                telegram_bot_token="test-token",
                telegram_chat_id="test-chat",
                database_path=Path(directory) / "gateway.sqlite",
            )
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
            built = []

            def one_production_cycle(runtime):
                built.append(runtime)
                for _ in range(4):
                    runtime.poll_once()

            with patch.dict(os.environ, {
                "LAPTOP_ORIGIN": "http://127.0.0.1:18765",
                "FLOW_GATEWAY_KEY": "test-key",
                "TELEGRAM_BOT_TOKEN": "test-token",
                "TELEGRAM_CHAT_ID": "test-chat",
                "GATEWAY_DATABASE": str(config.database_path),
            }, clear=True), patch("app.LaptopClient", return_value=laptop), \
                    patch("app.TelegramSender", return_value=sent.append), \
                    patch("app.OFFLINE_ALERT_DELAY_SECONDS", 0), \
                    patch.object(GatewayRuntime, "run_forever", one_production_cycle):
                self.assertEqual(main(), 0)

            runtime = built[0]
            self.assertEqual(runtime.liveness.status, LaptopStatus.ONLINE)
            self.assertEqual(len(sent), 2)
            self.assertTrue(any("más de 15 minutos" in message for message in sent))
            self.assertTrue(any("Una tarea falló" in message for message in sent))

            restarted = create_runtime(config, laptop=laptop, sender=sent.append)
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
            restarted.poll_once()
            self.assertEqual(len(sent), 2)


if __name__ == "__main__":
    unittest.main()
