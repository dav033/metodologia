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
        self.health_failures = 0
        self.command_payloads: list[dict] = []
        self.challenge_payloads: list[dict] = []
        self.raise_command_timeout = False

    def health(self):
        if self.health_failures:
            self.health_failures -= 1
            raise UpstreamError("health timeout")
        return {"status": "ok"}

    def snapshot(self):
        return {"runs": [], "plans": [], "generatedAt": "2026-10-19T12:00:00Z"}

    def events(self, after):
        return {"events": [], "nextCursor": after}

    def command(self, payload):
        self.command_payloads.append(payload)
        if self.raise_command_timeout:
            raise UpstreamError("command timed out")
        if payload["command"] in {"revise", "approve", "launch", "cancel-plan", "delete-plan"} \
                and "confirmation" not in payload:
            return 409, {"status": "REJECTED", "code": "CONFIRMATION_REQUIRED"}
        return 202, {"status": "OK", "idempotency_key": payload["idempotency_key"]}

    def challenge(self, payload):
        self.challenge_payloads.append(payload)
        return 201, {"challengeId": "challenge-token-0123456789", "target": payload["target"], "expiresIn": 120}


class CommandEntryPointTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        database = Path(self.temp.name) / "gateway.sqlite"
        self.laptop = FakeLaptop()
        config = GatewayConfig(laptop_origin="http://127.0.0.1:18765", gateway_key="test-key",
                               telegram_bot_token="test-token", telegram_chat_id="test-chat",
                               database_path=database)
        self.runtime = create_runtime(config, laptop=self.laptop, sender=lambda _message: None)
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

    def post(self, path: str, payload: dict):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        connection.request("POST", path, body=json.dumps(payload), headers={
            "Cookie": self.cookie, "Origin": "https://flow.example.test", "X-Flow-Request": "1",
            "Content-Type": "application/json",
        })
        response = connection.getresponse()
        result = response.status, json.loads(response.read())
        connection.close()
        return result

    @staticmethod
    def destructive_command():
        return {"schemaVersion": 1, "idempotencyKey": "command-key-000001", "type": "launch",
                "target": {"kind": "plan", "project": "demo", "req": "REQ-027"},
                "precondition": {"state": "approved", "revision": 4}}

    def test_destructive_command_without_challenge_is_refused_at_gateway_http_entrypoint(self):
        status, body = self.post("/api/remote/v1/commands", self.destructive_command())
        self.assertEqual((status, body["code"]), (409, "CONFIRMATION_REQUIRED"))
        self.assertEqual(self.laptop.command_payloads, [{
            "idempotency_key": "command-key-000001", "command": "launch", "target": "demo/REQ-027",
            "origin": "web", "params": {}, "precondition": {"state": "approved", "revision": 4},
        }])

    def test_confirmation_challenge_and_command_use_laptop_ledger_contract(self):
        challenge_status, challenge = self.post("/api/remote/v1/challenges", {
            "target": {"kind": "plan", "project": "demo", "req": "REQ-027"}, "typedReq": "REQ-027",
        })
        self.assertEqual(challenge_status, 201)
        self.assertEqual(self.laptop.challenge_payloads, [{"target": "demo/REQ-027", "typedReq": "REQ-027"}])
        command = self.destructive_command()
        command["confirmation"] = {"challengeId": challenge["challengeId"], "typedReq": "REQ-027"}
        status, result = self.post("/api/remote/v1/commands", command)
        self.assertEqual((status, result["status"], result["idempotencyKey"]), (202, "OK", "command-key-000001"))
        self.assertEqual(self.laptop.command_payloads[-1]["confirmation"], command["confirmation"])

    def test_offline_laptop_returns_laptop_offline_at_gateway_http_entrypoint(self):
        self.laptop.health_failures = 3
        for _ in range(3):
            self.runtime.poll_once()
        status, result = self.post("/api/remote/v1/commands", self.destructive_command())
        self.assertEqual((status, result["code"], result["idempotencyKey"]),
                         (410, "LAPTOP_OFFLINE", "command-key-000001"))
        self.assertEqual(self.laptop.command_payloads, [])

    def test_timeout_returns_unknown_outcome_with_idempotency_key(self):
        self.laptop.raise_command_timeout = True
        status, result = self.post("/api/remote/v1/commands", self.destructive_command())
        self.assertEqual((status, result["code"], result["idempotencyKey"]),
                         (503, "UNKNOWN_OUTCOME", "command-key-000001"))


if __name__ == "__main__":
    unittest.main()
