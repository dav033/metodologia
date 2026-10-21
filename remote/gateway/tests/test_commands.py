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
from upstream import UpstreamTimeout


class FakeLaptop:
    def __init__(self) -> None:
        self.command_calls: list[dict[str, object]] = []
        self.command_error: Exception | None = None

    def health(self):
        return {"status": "ok"}

    def snapshot(self):
        return {"runs": []}

    def events(self, after):
        return {"events": [], "nextCursor": after}

    def command(self, command):
        self.command_calls.append(command)
        if self.command_error:
            raise self.command_error
        key = command.get("idempotencyKey", command.get("idempotency_key"))
        return 202, {"commandId": "command-1", "status": "accepted", "idempotencyKey": key}


class CommandRelayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        database = Path(self.temp_dir.name) / "gateway.sqlite"
        self.oauth = OAuthConfig(
            client_id="test-client",
            client_secret="test-secret",
            session_secret="test-session-secret-with-more-than-32-bytes",
            frontend_origin="https://flow.example.test",
            database_path=str(database),
        )
        self.session = SessionStore(str(database), self.oauth.session_secret).create_session("dav033")
        self.laptop = FakeLaptop()
        self.config = GatewayConfig(
            laptop_origin="http://127.0.0.1:18765",
            gateway_key="test-key",
            telegram_bot_token="test-token",
            telegram_chat_id="test-chat",
            database_path=database,
        )
        self.runtime = create_runtime(self.config, laptop=self.laptop, sender=lambda _message: None)
        self.server = create_server(self.oauth, ("127.0.0.1", 0), runtime=self.runtime)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port)
        self.headers = {
            "Origin": "https://flow.example.test",
            "X-Flow-Request": "1",
            "Cookie": f"flow_session={self.session}",
            "Content-Type": "application/json",
        }

    def tearDown(self) -> None:
        self.connection.close()
        self.server.shutdown()
        self.server.server_close()
        self.runtime.outbox._db.close()
        self.temp_dir.cleanup()

    def post(self, command: dict[str, object]):
        self.connection.request("POST", "/api/remote/v1/commands", json.dumps(command), self.headers)
        response = self.connection.getresponse()
        body = response.read()
        return response.status, response.getheader("Content-Type"), json.loads(body)

    @staticmethod
    def command(command_type: str = "pause") -> dict[str, object]:
        return {
            "schemaVersion": 1,
            "idempotencyKey": "command-key-000001",
            "type": command_type,
            "target": {"kind": "run", "project": "demo", "req": "REQ-027"},
            "precondition": {"state": "running"},
        }

    def test_destructive_command_without_challenge_is_refused(self) -> None:
        status, content_type, body = self.post(self.command("approve"))

        self.assertEqual(status, 409)
        self.assertTrue(content_type.startswith("application/problem+json"))
        self.assertEqual(body["code"], "CONFIRMATION_REQUIRED")
        self.assertEqual(self.laptop.command_calls, [])

    def test_destructive_command_with_matching_challenge_reaches_laptop(self) -> None:
        command = self.command("approve")
        command["confirmation"] = {"challengeId": "challenge-token-1234", "typedReq": "REQ-027"}

        status, _content_type, body = self.post(command)

        self.assertEqual(status, 202)
        self.assertEqual(body["status"], "accepted")
        self.assertEqual(self.laptop.command_calls, [{
            "idempotency_key": command["idempotencyKey"],
            "command": "approve",
            "target": "demo/REQ-027",
            "origin": "web",
            "params": {"confirmation": {"challenge_id": "challenge-token-1234", "typed_req": "REQ-027"}},
            "precondition": {"state": "running"},
        }])

    def test_offline_laptop_refuses_command_without_queueing(self) -> None:
        for _ in range(3):
            self.runtime.liveness.record_failure()

        status, _content_type, body = self.post(self.command())

        self.assertEqual(status, 410)
        self.assertEqual(body["code"], "LAPTOP_OFFLINE")
        self.assertEqual(self.laptop.command_calls, [])

    def test_timeout_reports_unknown_outcome_with_idempotency_key(self) -> None:
        self.laptop.command_error = UpstreamTimeout("timeout")

        status, _content_type, body = self.post(self.command())

        self.assertEqual(status, 503)
        self.assertEqual(body["code"], "UNKNOWN_OUTCOME")
        self.assertEqual(body["idempotencyKey"], "command-key-000001")


if __name__ == "__main__":
    unittest.main()
