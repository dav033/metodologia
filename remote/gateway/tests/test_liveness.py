import os
import socket
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from app import GatewayRuntime, create_runtime
from config import ConfigurationError, GatewayConfig
from liveness import LaptopStatus, LivenessMonitor
from main import main
from upstream import LaptopClient, UpstreamError


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class FakeLaptop:
    def __init__(self):
        self.healthy = True
        self.health_results = []
        self.feed = []
        self.snapshot_calls = 0
        self.snapshot_unavailable = False

    def health(self):
        healthy = self.health_results.pop(0) if self.health_results else self.healthy
        if not healthy:
            self.snapshot_unavailable = True
            raise UpstreamError("offline")
        self.snapshot_unavailable = False
        return {"status": "ok"}

    def events(self, after):
        result = {"events": self.feed, "nextCursor": "cursor-1"}
        self.feed = []
        return result

    def snapshot(self):
        self.snapshot_calls += 1
        if self.snapshot_unavailable:
            raise UpstreamError("offline")
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

    def test_upstream_client_uses_configured_timeout(self):
        config = GatewayConfig.from_env({
            "LAPTOP_ORIGIN": "http://127.0.0.1:18765",
            "FLOW_GATEWAY_KEY": "test-key",
            "TELEGRAM_BOT_TOKEN": "test-token",
            "TELEGRAM_CHAT_ID": "test-chat",
            "GATEWAY_DATABASE": "/tmp/gateway.sqlite",
            "UPSTREAM_TIMEOUT": "2.5",
        })
        client = LaptopClient(config.laptop_origin, config.gateway_key, config.request_timeout)
        with patch("upstream.urlopen") as urlopen:
            urlopen.return_value.__enter__.return_value.read.return_value = b'{"status":"ok"}'

            self.assertEqual(client.health(), {"status": "ok"})
            urlopen.assert_called_once()
            self.assertEqual(urlopen.call_args.kwargs["timeout"], 2.5)

    def test_production_composition_persists_liveness_and_event_delivery(self):
        with tempfile.TemporaryDirectory() as directory:
            laptop = FakeLaptop()
            sent = []
            laptop.health_results = [True, False, False, False, True]
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
                "occurredAt": datetime.now(timezone.utc).isoformat(),
                "target": {"kind": "task", "project": "demo", "req": "REQ-027"},
                "data": {},
                "dedupeKey": "attempt-1-failed",
            }]
            built = []

            def one_production_cycle(runtime):
                built.append(runtime)
                for _ in range(5):
                    runtime.poll_once()

            with patch.dict(os.environ, {
                "LAPTOP_ORIGIN": "http://127.0.0.1:18765",
                "FLOW_GATEWAY_KEY": "test-key",
                "TELEGRAM_BOT_TOKEN": "test-token",
                "TELEGRAM_CHAT_ID": "test-chat",
                "GATEWAY_DATABASE": str(config.database_path),
                "GITHUB_CLIENT_ID": "test-client-id",
                "GITHUB_CLIENT_SECRET": "test-client-secret",
                "SESSION_SECRET": "test-session-secret-with-more-than-32-bytes",
                "FLOW_FRONTEND_ORIGIN": "https://flow.example.test",
                "GATEWAY_BIND": "127.0.0.1",
                "GATEWAY_PORT": str(free_port()),
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

    def test_production_entrypoint_alerts_from_cached_active_run_when_laptop_is_offline(self):
        with tempfile.TemporaryDirectory() as directory:
            laptop = FakeLaptop()
            laptop.health_results = [True, False, False, False]
            sent = []
            config = GatewayConfig(
                laptop_origin="http://127.0.0.1:18765",
                gateway_key="test-key",
                telegram_bot_token="test-token",
                telegram_chat_id="test-chat",
                database_path=Path(directory) / "gateway.sqlite",
            )

            def four_production_cycles(runtime):
                for _ in range(4):
                    runtime.poll_once()

            env = {
                "LAPTOP_ORIGIN": config.laptop_origin,
                "FLOW_GATEWAY_KEY": config.gateway_key,
                "TELEGRAM_BOT_TOKEN": config.telegram_bot_token,
                "TELEGRAM_CHAT_ID": config.telegram_chat_id,
                "GATEWAY_DATABASE": str(config.database_path),
<<<<<<< 6325aad3bf697b5532e04cadff1faaf103f99745
                "GITHUB_CLIENT_ID": "test-client",
                "GITHUB_CLIENT_SECRET": "test-secret",
                "SESSION_SECRET": "test-session-secret-with-more-than-32-bytes",
                "FLOW_FRONTEND_ORIGIN": "https://flow.example.test",
                "GATEWAY_PORT": str(free_port()),
||||||| d50e31c90b0e67af0ef0f7d068ae134a8c2c23a0
=======
                "GITHUB_CLIENT_ID": "test-client-id",
                "GITHUB_CLIENT_SECRET": "test-client-secret",
                "SESSION_SECRET": "test-session-secret-with-more-than-32-bytes",
                "FLOW_FRONTEND_ORIGIN": "https://flow.example.test",
>>>>>>> d88a6a63b45058501d9bd5ba9116859d7bfce2c5
            }
            with patch.dict(os.environ, env, clear=True), patch("app.LaptopClient", return_value=laptop), \
                    patch("app.TelegramSender", return_value=sent.append), \
                    patch("app.OFFLINE_ALERT_DELAY_SECONDS", 0), \
                    patch.object(GatewayRuntime, "run_forever", four_production_cycles):
                self.assertEqual(main(), 0)

            self.assertEqual(laptop.snapshot_calls, 1)
            self.assertTrue(any("más de 15 minutos" in message for message in sent))


if __name__ == "__main__":
    unittest.main()
