from __future__ import annotations

import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path

from app import create_runtime
from auth import OAuthConfig, SESSION_COOKIE, SessionStore
from config import GatewayConfig
from server import create_server
from upstream import UpstreamError


class FakeLaptop:
    def __init__(self):
        self.health_results = [True]
        self.snapshot_calls = 0
        self.events_calls = 0
        self.feed: list[dict] = []
        self.commands: list[dict] = []

    def health(self):
        success = self.health_results.pop(0) if self.health_results else True
        if not success:
            raise UpstreamError("offline")
        return {"schemaVersion": 1, "status": "ok"}

    def snapshot(self):
        self.snapshot_calls += 1
        return {"schemaVersion": 1, "runs": [{"run": "demo/REQ-001", "tasks": []}],
                "plans": [{"req": "REQ-002", "status": "review"}],
                "generatedAt": "2026-10-19T12:00:00Z", "cursor": "c-1"}

    def events(self, after):
        self.events_calls += 1
        feed, self.feed = self.feed, []
        return {"events": feed, "nextCursor": "1" if feed else after, "hasMore": False}

    def command(self, payload):
        self.commands.append(payload)
        return 202, {"commandId": "cmd-1", "status": "accepted", "idempotencyKey": payload["idempotencyKey"]}


class StreamEntryPointTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        database = Path(self.temp.name) / "gateway.sqlite"
        self.laptop = FakeLaptop()
        self.runtime = create_runtime(GatewayConfig(
            laptop_origin="http://127.0.0.1:18765", gateway_key="test-key",
            telegram_bot_token="test-token", telegram_chat_id="test-chat", database_path=database,
        ), laptop=self.laptop, sender=lambda _message: None)
        self.server = create_server(OAuthConfig(
            client_id="test-client", client_secret="test-secret",
            session_secret="test-session-secret-with-more-than-32-bytes",
            frontend_origin="https://flow.example.test", database_path=str(database),
        ), ("127.0.0.1", 0), runtime=self.runtime)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        token = SessionStore(str(database), "test-session-secret-with-more-than-32-bytes").create_session("dav033")
        self.cookie = f"{SESSION_COOKIE}={token}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.temp.cleanup()

    def request_json(self, path: str):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        connection.request("GET", path, headers={"Cookie": self.cookie})
        response = connection.getresponse()
        payload = json.loads(response.read())
        status = response.status
        connection.close()
        return status, payload

    def request_command(self, payload: dict):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        connection.request("POST", "/api/remote/v1/commands", body=json.dumps(payload), headers={
            "Cookie": self.cookie, "Origin": "https://flow.example.test", "X-Flow-Request": "1",
            "Content-Type": "application/json",
        })
        response = connection.getresponse()
        result = response.status, json.loads(response.read())
        connection.close()
        return result

    def read_event(self, last_event_id: str):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        connection.request("GET", "/api/remote/v1/events", headers={
            "Cookie": self.cookie, "Last-Event-ID": last_event_id,
        })
        response = connection.getresponse()
        self.assertEqual(response.status, 200)
        self.assertIn("text/event-stream", response.getheader("Content-Type", ""))
        lines = []
        while True:
            line = response.fp.readline().decode("utf-8")
            if not line:
                break
            lines.append(line)
            if line == "\n" and any(value.startswith("data: ") for value in lines):
                break
        connection.close()
        return "".join(lines)

    def test_last_event_id_replays_laptop_event_at_real_http_entrypoint(self):
        self.laptop.feed = [{
            "ord": "7", "kind": "attempt.failed", "run": "demo/REQ-001", "task": "T1",
            "text": "verification failed", "occurred_at": "2026-10-19T12:01:00Z",
        }]
        self.runtime.poll_once()

        replay = self.read_event("0")
        self.assertIn("id: 1\n", replay)
        self.assertIn("event: flow\n", replay)
        self.assertIn('"ord":"7"', replay)
        self.assertIn('"text":"verification failed"', replay)
        self.assertEqual(self.laptop.events_calls, 1)

    def test_offline_snapshot_keeps_laptop_generated_time_and_routes_match_laptop_shape(self):
        self.runtime.poll_once()
        self.laptop.health_results = [False, False, False]
        for _ in range(3):
            self.runtime.poll_once()

        status, snapshot = self.request_json("/api/remote/v1/snapshot")
        self.assertEqual(status, 200)
        self.assertEqual(snapshot["generatedAt"], "2026-10-19T12:00:00Z")
        self.assertEqual(snapshot["laptopStatus"], "offline")
        self.assertEqual(snapshot["runs"][0]["run"], "demo/REQ-001")

        status, runs = self.request_json("/api/remote/v1/runs")
        self.assertEqual(status, 200)
        self.assertEqual(runs["runs"], snapshot["runs"])
        status, plans = self.request_json("/api/remote/v1/plans")
        self.assertEqual(status, 200)
        self.assertEqual(plans["plans"], snapshot["plans"])
        self.assertEqual(self.laptop.snapshot_calls, 1)

    def test_many_http_clients_read_one_shared_runtime_snapshot(self):
        self.runtime.poll_once()
        for _ in range(8):
            status, payload = self.request_json("/api/remote/v1/snapshot")
            self.assertEqual(status, 200)
            self.assertIn("generatedAt", payload)
        self.assertEqual(self.laptop.snapshot_calls, 1)
        self.assertEqual(self.laptop.events_calls, 1)

    def test_panel_command_route_relays_the_laptop_command_shape(self):
        command = {"schemaVersion": 1, "idempotencyKey": "client-key-1", "command": "pause",
                   "target": {"kind": "run", "project": "demo", "req": "REQ-001"},
                   "precondition": {"status": "running"}}
        status, result = self.request_command(command)
        self.assertEqual(status, 202)
        self.assertEqual(result["commandId"], "cmd-1")
        self.assertEqual(self.laptop.commands, [command])


if __name__ == "__main__":
    unittest.main()
