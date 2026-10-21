import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock

from app import GatewayRuntime, _ledger_command
from auth import OAuthConfig, SessionStore
from config import GatewayConfig
from liveness import LaptopStatus
from server import create_server
from upstream import UpstreamTimeout


def config(path: Path) -> GatewayConfig:
    return GatewayConfig("http://127.0.0.1:18765", "test-key", "test-token", "test-chat", path)


def command(**changes):
    request = {
        "schemaVersion": 1,
        "idempotencyKey": "retry-key-00000001",
        "type": "retry",
        "target": {"kind": "task", "project": "demo", "req": "REQ-027", "taskId": "T4"},
        "precondition": {"state": "rejected", "revision": 3},
        "route": {"id": "route:abc", "model": "sonnet", "account": "work"},
    }
    return {**request, **changes}


class CommandRelayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.laptop = Mock()
        self.laptop.post_json.return_value = {"status": "OK", "code": None}
        self.runtime = GatewayRuntime(config(Path(self.temp.name) / "gateway.sqlite"), laptop=self.laptop,
                                      sender=lambda _: None)

    def test_destructive_command_without_challenge_is_refused_without_forwarding(self):
        result = self.runtime.submit_command(command(type="launch", route=None))
        self.assertEqual(result["code"], "CONFIRMATION_REQUIRED")
        self.laptop.post_json.assert_not_called()

    def test_offline_laptop_returns_laptop_offline_without_forwarding(self):
        self.runtime.liveness.status = LaptopStatus.OFFLINE
        result = self.runtime.submit_command(command())
        self.assertEqual(result["code"], "LAPTOP_OFFLINE")
        self.laptop.post_json.assert_not_called()

    def test_timeout_returns_unknown_outcome_with_idempotency_key(self):
        self.laptop.post_json.side_effect = UpstreamTimeout("late response")
        result = self.runtime.submit_command(command())
        self.assertEqual(result["code"], "UNKNOWN_OUTCOME")
        self.assertEqual(result["idempotency_key"], "retry-key-00000001")

    def test_confirmation_challenge_is_relayed_with_string_target(self):
        self.laptop.post_json.return_value = {"challengeId": "challenge-token", "expiresIn": 120}
        result = self.runtime.issue_challenge({
            "target": {"kind": "run", "project": "demo", "req": "REQ-027"},
            "typedReq": "REQ-027",
        })
        self.assertEqual(result["challengeId"], "challenge-token")
        self.laptop.post_json.assert_called_once_with("/api/remote/v1/challenges", {
            "target": "demo/REQ-027", "typedReq": "REQ-027"})

    def test_route_object_is_translated_to_string_selectors_for_laptop_ledger(self):
        translated = _ledger_command(command())
        self.assertEqual(translated["target"], "demo/REQ-027")
        self.assertEqual(translated["params"], {
            "task": "T4", "route": "route:abc", "model": "sonnet", "account": "work"})
        self.runtime.submit_command(command())
        forwarded = self.laptop.post_json.call_args.args[1]
        self.assertEqual(forwarded["params"]["route"], "route:abc")
        self.assertEqual(forwarded["params"]["model"], "sonnet")
        self.assertEqual(forwarded["params"]["account"], "work")


class CommandRelayHttpTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        database = Path(self.temp.name) / "gateway.sqlite"
        oauth = OAuthConfig(
            client_id="test-client", client_secret="test-secret",
            session_secret="test-session-secret-with-more-than-32-bytes",
            frontend_origin="https://flow.example.test", database_path=str(database),
        )
        store = SessionStore(str(database), oauth.session_secret)
        self.session = store.create_session("dav033")
        self.laptop = Mock()
        self.laptop.post_json.return_value = {"status": "OK", "code": None}
        self.runtime = GatewayRuntime(config(database), laptop=self.laptop, sender=lambda _: None)
        self.server = create_server(oauth, ("127.0.0.1", 0), runtime=self.runtime)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port)

    def tearDown(self):
        self.connection.close()
        self.server.shutdown()
        self.server.server_close()
        self.runtime.outbox._db.close()

    def post(self, body):
        self.connection.request("POST", "/api/remote/v1/commands", json.dumps(body), {
            "Origin": "https://flow.example.test", "X-Flow-Request": "1",
            "Cookie": f"flow_session={self.session}", "Content-Type": "application/json",
        })
        response = self.connection.getresponse()
        result = response.status, json.loads(response.read())
        return result

    @staticmethod
    def run_command(command_type="pause"):
        return {
            "schemaVersion": 1, "idempotencyKey": "command-key-000001", "type": command_type,
            "target": {"kind": "run", "project": "demo", "req": "REQ-027"},
            "precondition": {"state": "running"},
        }

    def test_destructive_command_requires_confirmation(self):
        status, body = self.post(self.run_command("approve"))
        self.assertEqual((status, body["code"]), (409, "CONFIRMATION_REQUIRED"))
        self.laptop.post_json.assert_not_called()

    def test_confirmed_destructive_command_reaches_laptop_ledger(self):
        command = self.run_command("approve")
        command["confirmation"] = {"challengeId": "challenge-token-1234", "typedReq": "REQ-027"}
        status, body = self.post(command)
        self.assertEqual((status, body["status"]), (200, "OK"))
        self.laptop.post_json.assert_called_once_with("/api/remote/v1/commands", {
            "idempotency_key": command["idempotencyKey"], "command": "approve", "target": "demo/REQ-027",
            "origin": "web", "params": {}, "precondition": {"state": "running"},
            "confirmation": {"challenge_id": "challenge-token-1234", "typed_req": "REQ-027"},
        })

    def test_offline_command_is_refused_without_forwarding(self):
        for _ in range(self.runtime.liveness.failures_before_offline):
            self.runtime.liveness.record_failure()
        status, body = self.post(self.run_command())
        self.assertEqual((status, body["code"]), (410, "LAPTOP_OFFLINE"))
        self.laptop.post_json.assert_not_called()

    def test_timeout_returns_unknown_outcome_with_idempotency_key(self):
        self.laptop.post_json.side_effect = UpstreamTimeout("late response")
        status, body = self.post(self.run_command())
        self.assertEqual((status, body["code"]), (503, "UNKNOWN_OUTCOME"))
        self.assertEqual(body["idempotency_key"], "command-key-000001")


if __name__ == "__main__":
    unittest.main()
