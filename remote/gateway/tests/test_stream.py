from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path
import http.client
import json

from app import create_runtime
from auth import OAuthConfig, SessionStore
from config import GatewayConfig
from server import create_server
from stream import SnapshotEventStream
from upstream import UpstreamError


class FakeLaptop:
    def __init__(self) -> None:
        self.online = True
        self.snapshot_calls = 0
        self.event_calls = 0
        self.read_calls = []

    def health(self):
        if not self.online:
            raise UpstreamError("offline")
        return {"status": "ok"}

    def snapshot(self):
        self.snapshot_calls += 1
        return {"runs": [], "generatedAt": "2026-10-20T12:00:00Z", "cursor": "upstream-1"}

    def events(self, after):
        self.event_calls += 1
        return {
            "events": [
                {"id": "event-a", "cursor": "upstream-1", "type": "run.finished"},
                {"id": "event-b", "cursor": "upstream-2", "type": "attempt.failed"},
            ],
            "nextCursor": "upstream-2",
        }

    def read_model(self, path):
        self.read_calls.append(path)
        return {"source": path}


class SnapshotStreamTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.laptop = FakeLaptop()
        self.config = GatewayConfig(
            laptop_origin="http://127.0.0.1:18765",
            gateway_key="test-key",
            telegram_bot_token="test-token",
            telegram_chat_id="test-chat",
            database_path=Path(self.temp_dir.name) / "gateway.sqlite",
        )
        self.runtime = create_runtime(self.config, laptop=self.laptop, sender=lambda message: None)

    def tearDown(self) -> None:
        self.runtime.outbox._db.close()
        self.temp_dir.cleanup()

    def test_last_event_id_replays_only_events_after_cursor(self) -> None:
        self.runtime.poll_once()

        resumed = self.runtime.stream.after("1")

        self.assertEqual([event_id for event_id, _ in resumed], [2])
        self.assertEqual(resumed[0][1]["id"], "event-b")
        self.assertEqual(self.runtime.stream.after("0"), [
            (1, {"id": "event-a", "cursor": "upstream-1", "type": "run.finished"}),
            (2, {"id": "event-b", "cursor": "upstream-2", "type": "attempt.failed"}),
        ])

    def test_offline_laptop_keeps_cached_snapshot_and_capture_time(self) -> None:
        self.runtime.poll_once()
        self.laptop.online = False

        for _ in range(3):
            self.runtime.poll_once()
        cached = self.runtime.stream.snapshot()

        self.assertEqual(cached["generatedAt"], "2026-10-20T12:00:00Z")
        self.assertTrue(cached["cachedAt"].endswith("Z"))
        self.assertFalse(cached["laptop"]["online"])
        self.assertTrue(cached["laptop"]["checkedAt"].endswith("Z"))
        self.assertEqual(self.laptop.snapshot_calls, 1)

    def test_multiple_clients_share_the_single_runtime_poll(self) -> None:
        self.runtime.poll_once()

        first_client = self.runtime.stream.after(None)
        second_client = self.runtime.stream.after(None)

        self.assertEqual(first_client, second_client)
        self.assertEqual(self.laptop.snapshot_calls, 1)
        self.assertEqual(self.laptop.event_calls, 1)

    def test_reconnect_wait_receives_events_published_after_it_starts(self) -> None:
        stream = SnapshotEventStream()
        waiting = threading.Event()
        received = []

        def reconnect() -> None:
            waiting.set()
            received.extend(stream.wait_after(0, timeout=1))

        client = threading.Thread(target=reconnect)
        client.start()
        self.assertTrue(waiting.wait(timeout=1))
        stream.publish([{"id": "event-a", "type": "run.finished"}])
        client.join(timeout=1)

        self.assertFalse(client.is_alive())
        self.assertEqual(received, [(1, {"id": "event-a", "type": "run.finished"})])

    def test_authenticated_http_entrypoint_relays_required_read_models(self) -> None:
        database = Path(self.temp_dir.name) / "auth.sqlite"
        oauth = OAuthConfig("client", "client-secret", "test-session-secret-with-more-than-32-bytes",
                           "https://flow.example.test", str(database))
        session = SessionStore(str(database), oauth.session_secret).create_session("dav033")
        server = create_server(oauth, ("127.0.0.1", 0), runtime=self.runtime)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        connection = http.client.HTTPConnection("127.0.0.1", server.server_port)
        paths = ["/api/remote/v1/attempts/a1/review", "/api/remote/v1/quotas",
                 "/api/remote/v1/history", "/api/remote/v1/routes?target=demo%2FREQ-001&task=T1"]
        try:
            for path in paths:
                connection.request("GET", path, headers={"Cookie": f"flow_session={session}"})
                response = connection.getresponse()
                payload = json.loads(response.read())
                self.assertEqual(response.status, 200)
                self.assertEqual(payload["source"], path.split("?", 1)[0] + ("?" + path.split("?", 1)[1] if "?" in path else ""))
            self.assertEqual(self.laptop.read_calls, paths)
        finally:
            connection.close()
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
