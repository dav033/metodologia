import http.client
import json
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path
<<<<<<< 4afe24b9701478e708836c2a834fe7e817773f1d
from unittest.mock import Mock
||||||| c04d03849ef5c7dc6c4e925a2221829c531ea8d3
=======
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch
>>>>>>> 8a050424a13d0335b6f496bee2e6edb1152be935

from app import GatewayRuntime, _ledger_command
from auth import OAuthConfig, SessionStore
from config import GatewayConfig
from liveness import LaptopStatus
from server import create_server
<<<<<<< 4afe24b9701478e708836c2a834fe7e817773f1d
from upstream import UpstreamTimeout
||||||| c04d03849ef5c7dc6c4e925a2221829c531ea8d3
from stream import SnapshotEventStream
from upstream import UpstreamTimeout
=======
from stream import SnapshotEventStream
from upstream import LaptopClient, UpstreamTimeout

SCRIPTS = Path(__file__).resolve().parents[3] / "skill" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import bt_remote_api


class LaptopLedgerHandler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def do_POST(self):
        bt_remote_api.route_post(self)

    def send(self, payload, status=200, content_type="application/json; charset=utf-8"):
        if isinstance(payload, str):
            payload = payload.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)
>>>>>>> 8a050424a13d0335b6f496bee2e6edb1152be935


<<<<<<< 4afe24b9701478e708836c2a834fe7e817773f1d
def config(path: Path) -> GatewayConfig:
    return GatewayConfig("http://127.0.0.1:18765", "test-key", "test-token", "test-chat", path)
||||||| c04d03849ef5c7dc6c4e925a2221829c531ea8d3
class FakeLaptop:
    def __init__(self) -> None:
        self.command_calls: list[dict[str, object]] = []
        self.command_error: Exception | None = None
=======
class FakeLaptop:
    def __init__(self) -> None:
        self.command_calls: list[dict[str, object]] = []
        self.challenge_calls: list[dict[str, object]] = []
        self.command_error: Exception | None = None
>>>>>>> 8a050424a13d0335b6f496bee2e6edb1152be935


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

    def challenge(self, challenge):
        self.challenge_calls.append(challenge)
        return {"challengeId": "laptop-challenge-000001", **challenge, "expiresIn": 120}


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

<<<<<<< 4afe24b9701478e708836c2a834fe7e817773f1d
    def post(self, body):
        self.connection.request("POST", "/api/remote/v1/commands", json.dumps(body), {
            "Origin": "https://flow.example.test", "X-Flow-Request": "1",
            "Cookie": f"flow_session={self.session}", "Content-Type": "application/json",
        })
||||||| c04d03849ef5c7dc6c4e925a2221829c531ea8d3
    def post(self, command: dict[str, object]):
        self.connection.request("POST", "/api/remote/v1/commands", json.dumps(command), self.headers)
=======
    def post(self, command: dict[str, object]):
        return self.post_path("/api/remote/v1/commands", command, self.headers)

    def post_path(self, path: str, value: dict[str, object], headers: dict[str, str]):
        self.connection.request("POST", path, json.dumps(value), headers)
>>>>>>> 8a050424a13d0335b6f496bee2e6edb1152be935
        response = self.connection.getresponse()
        result = response.status, json.loads(response.read())
        return result

    def get(self, path: str):
        self.connection.request("GET", path)
        response = self.connection.getresponse()
        body = response.read()
        return response.status, response.getheader("Location"), response.getheader("Set-Cookie"), body

    def test_displayed_github_and_logout_routes_are_real_http_entrypoints(self) -> None:
        status, location, _cookie, _body = self.get("/api/auth/github")
        self.assertEqual(status, 302)
        self.assertIn("github.com", location)

        status, location, cookie, _body = self.get("/api/auth/logout")
        self.assertEqual(status, 302)
        self.assertEqual(location, "https://flow.example.test/")
        self.assertIn("flow_session=", cookie)
        self.assertIn("Max-Age=0", cookie)

    def test_public_pause_command_is_translated_to_laptop_ledger_schema(self) -> None:
        status, _content_type, body = self.post(self.command())

        self.assertEqual(status, 202)
        self.assertEqual(body["status"], "accepted")
        self.assertEqual(self.laptop.command_calls, [{
            "idempotency_key": "command-key-000001",
            "command": "pause",
            "target": "demo/REQ-027",
            "origin": "web",
            "params": {},
            "precondition": {"state": "running"},
        }])

    def test_authenticated_challenge_request_is_relayed_to_laptop(self) -> None:
        status, content_type, body = self.post_path(
            "/api/remote/v1/challenges",
            {"target": "demo/REQ-027", "typedReq": "REQ-027"},
            self.headers,
        )

        self.assertEqual(status, 201)
        self.assertTrue(content_type.startswith("application/json"))
        self.assertEqual(body["challengeId"], "laptop-challenge-000001")
        self.assertEqual(self.laptop.challenge_calls, [{"target": "demo/REQ-027", "typedReq": "REQ-027"}])

    def test_command_and_challenge_pass_through_both_production_http_handlers(self) -> None:
        laptop_server = ThreadingHTTPServer(("127.0.0.1", 0), LaptopLedgerHandler)
        laptop_thread = threading.Thread(target=laptop_server.serve_forever, daemon=True)
        laptop_thread.start()
        self.addCleanup(laptop_server.server_close)
        self.addCleanup(laptop_server.shutdown)
        self.runtime.laptop = LaptopClient(f"http://127.0.0.1:{laptop_server.server_port}", "test-key")
        handlers = {"pause": lambda _target, _params: {"paused": True},
                    "approve": lambda _target, _params: {"approved": True}}
        with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": "test-key", "BITACORA_ROOT": self.temp_dir.name}), \
                patch.object(bt_remote_api, "_target_state", lambda *_args: {"state": "running"}), \
                patch.dict(bt_remote_api.HANDLERS, handlers, clear=True):
            command_status, _content_type, command_body = self.post(self.command())
            self.assertEqual(command_status, 200)
            self.assertEqual(command_body["status"], "OK")
            self.assertEqual(command_body["outcome"], {"paused": True})

            challenge_status, _content_type, challenge_body = self.post_path(
                "/api/remote/v1/challenges",
                {"target": "demo/REQ-027", "typedReq": "REQ-027"},
                self.headers,
            )
            self.assertEqual(challenge_status, 201)
            approve = self.command("approve")
            approve["idempotencyKey"] = "challenge-command-key-0002"
            approve["confirmation"] = {"challengeId": challenge_body["challengeId"], "typedReq": "REQ-027"}
            approve_status, _content_type, approve_body = self.post(approve)
            self.assertEqual(approve_status, 200, approve_body)
            self.assertEqual(approve_body["status"], "OK")
            self.assertEqual(approve_body["outcome"], {"approved": True})

    def test_challenge_request_requires_valid_session_and_request_marker(self) -> None:
        value = {"target": "demo/REQ-027", "typedReq": "REQ-027"}
        no_session = {key: val for key, val in self.headers.items() if key != "Cookie"}
        status, _content_type, _body = self.post_path("/api/remote/v1/challenges", value, no_session)
        self.assertEqual(status, 401)

        no_marker = {key: val for key, val in self.headers.items() if key != "X-Flow-Request"}
        status, _content_type, _body = self.post_path("/api/remote/v1/challenges", value, no_marker)
        self.assertEqual(status, 403)
        self.assertEqual(self.laptop.challenge_calls, [])

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

<<<<<<< 4afe24b9701478e708836c2a834fe7e817773f1d
    def test_offline_command_is_refused_without_forwarding(self):
        for _ in range(self.runtime.liveness.failures_before_offline):
||||||| c04d03849ef5c7dc6c4e925a2221829c531ea8d3
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
=======
        status, _content_type, body = self.post(command)

        self.assertEqual(status, 202)
        self.assertEqual(body["status"], "accepted")
        self.assertEqual(self.laptop.command_calls, [{
            "idempotency_key": command["idempotencyKey"],
            "command": "approve",
            "target": "demo/REQ-027",
            "origin": "web",
            "params": {},
            "precondition": {"state": "running"},
            "confirmation": {"challenge_id": "challenge-token-1234", "typed_req": "REQ-027"},
        }])

    def test_offline_laptop_refuses_command_without_queueing(self) -> None:
        for _ in range(3):
>>>>>>> 8a050424a13d0335b6f496bee2e6edb1152be935
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
