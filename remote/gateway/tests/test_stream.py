from __future__ import annotations

import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path

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
        self.read_paths: list[str] = []

    def health(self):
        if not self.online:
            raise UpstreamError("offline")
        return {"status": "ok"}

    def snapshot(self):
        self.snapshot_calls += 1
        return {"runs": [], "generatedAt": "2026-10-20T12:00:00Z", "cursor": "upstream-1"}

    def read(self, path):
        self.read_paths.append(path)
        if not self.online:
            raise UpstreamError("offline")
        if "/attempts/missing/review" in path:
            return 404, {"code": "ATTEMPT_NOT_FOUND", "message": "secret /home/path detail"}
        return 200, {"path": path.split("?")[0], "accounts": [], "commands": [], "routes": [], "attemptId": "att-1"}

    def events(self, after):
        self.event_calls += 1
        return {
            "events": [
                {"id": "event-a", "cursor": "upstream-1", "type": "run.finished"},
                {"id": "event-b", "cursor": "upstream-2", "type": "attempt.failed"},
            ],
            "nextCursor": "upstream-2",
        }


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

        self.runtime.poll_once()
        cached = self.runtime.stream.snapshot()

        self.assertEqual(cached["generatedAt"], "2026-10-20T12:00:00Z")
        self.assertTrue(cached["cachedAt"].endswith("Z"))
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


class ReadRelayTests(unittest.TestCase):
    """Review, quotas, history/commands and routes reach the browser through the authenticated gateway."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        database = Path(self.temp_dir.name) / "gateway.sqlite"
        oauth = OAuthConfig(client_id="id", client_secret="secret",
                            session_secret="test-session-secret-with-more-than-32-bytes",
                            frontend_origin="https://flow.example.test", database_path=str(database))
        self.cookie = f"flow_session={SessionStore(str(database), oauth.session_secret).create_session('dav033')}"
        self.laptop = FakeLaptop()
        config = GatewayConfig(laptop_origin="http://127.0.0.1:18765", gateway_key="k", telegram_bot_token="t",
                               telegram_chat_id="c", database_path=database)
        self.runtime = create_runtime(config, laptop=self.laptop, sender=lambda message: None)
        self.addCleanup(self.runtime.outbox._db.close)
        self.server = create_server(oauth, ("127.0.0.1", 0), runtime=self.runtime)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def get(self, path: str, cookie: str | None = None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        connection.request("GET", path, headers={"Cookie": cookie if cookie is not None else self.cookie})
        response = connection.getresponse()
        body = json.loads(response.read())
        connection.close()
        return response.status, body

    def test_read_routes_require_a_session_and_relay_validated_queries(self) -> None:
        for path in ("/api/remote/v1/quotas", "/api/remote/v1/history", "/api/remote/v1/commands",
                     "/api/remote/v1/attempts/att-1/review",
                     "/api/remote/v1/routes?target=demo/REQ-027&task=T3"):
            with self.subTest(path=path):
                self.assertEqual(self.get(path, cookie="")[0], 401)
                status, body = self.get(path)
                self.assertEqual(status, 200, body)
        self.assertEqual(self.laptop.read_paths[-1], "/api/remote/v1/routes?target=demo%2FREQ-027&task=T3")
        self.assertEqual(self.get("/api/remote/v1/routes?target=bad&task=T3")[1]["code"], "INVALID_ROUTE_QUERY")
        self.assertEqual(self.get("/api/remote/v1/history?limit=0")[1]["code"], "INVALID_LIMIT")
        self.assertEqual(len(self.laptop.read_paths), 5)

    def test_laptop_errors_are_mapped_without_leaking_details(self) -> None:
        status, body = self.get("/api/remote/v1/attempts/missing/review")
        self.assertEqual((status, body["code"]), (404, "ATTEMPT_NOT_FOUND"))
        self.assertNotIn("/home", json.dumps(body))

    def test_offline_laptop_serves_cached_quotas_and_refuses_uncached_reads(self) -> None:
        self.assertEqual(self.get("/api/remote/v1/quotas")[0], 200)
        self.laptop.online = False
        for _ in range(3):
            self.runtime.liveness.record_failure()
        status, body = self.get("/api/remote/v1/quotas")
        self.assertEqual(status, 200)
        self.assertTrue(body["cachedAt"].endswith("Z"))
        status, body = self.get("/api/remote/v1/attempts/att-1/review")
        self.assertEqual((status, body["code"]), (503, "LAPTOP_OFFLINE"))


if __name__ == "__main__":
    unittest.main()
