import http.client
import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import Mock, patch

from app import GatewayRuntime, _ledger_command
from auth import OAuthConfig, SessionStore
from config import GatewayConfig
from liveness import LaptopStatus
from server import create_server
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


<<<<<<< 9e2b4a7ef27c0360273e4d2c110f31839133069d
def config(path: Path) -> GatewayConfig:
    return GatewayConfig("http://127.0.0.1:18765", "test-key", "test-token", "test-chat", path)
||||||| f5aa1d3190788a2f58e4928c44fd96a9b9a3e1c7
class FakeLaptop:
    def __init__(self) -> None:
        self.command_calls: list[dict[str, object]] = []
        self.challenge_calls: list[dict[str, object]] = []
        self.command_error: Exception | None = None
=======
class LaptopEventsHandler(BaseHTTPRequestHandler):
    requested_cursors: list[str] = []
    event = {"id": "evt-decision", "type": "plan.waiting", "dedupeKey": "evt-decision",
             "target": {"req": "REQ-027"}}

    def log_message(self, *_args):
        pass

    def do_GET(self):
        from urllib.parse import parse_qs, urlsplit

        after = parse_qs(urlsplit(self.path).query).get("after", [""])[0]
        self.requested_cursors.append(after)
        if after == "expired-cursor":
            status, body = 400, {"code": "INVALID_CURSOR"}
        else:
            status, body = 200, {"events": [self.event], "nextCursor": "fresh-cursor"}
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


class FakeLaptop:
    def __init__(self) -> None:
        self.command_calls: list[dict[str, object]] = []
        self.challenge_calls: list[dict[str, object]] = []
        self.command_error: Exception | None = None
>>>>>>> e5f3b15ac8278a1920c8feef414f89bd689013ca


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
        return self.post_path("/api/remote/v1/commands", body, {
            "Origin": "https://flow.example.test", "X-Flow-Request": "1",
            "Cookie": f"flow_session={self.session}", "Content-Type": "application/json",
        })

    def post_path(self, path, body, headers=None):
        self.connection.request("POST", path, json.dumps(body), headers or {})
        response = self.connection.getresponse()
        return response.status, json.loads(response.read())

    def test_displayed_github_login_and_logout_routes_reach_gateway(self):
        self.connection.request("GET", "/api/auth/github")
        login = self.connection.getresponse()
        self.assertEqual(login.status, 302)
        self.assertIn("github.com/login/oauth/authorize", login.getheader("Location"))
        self.assertIn("flow_oauth_state=", login.getheader("Set-Cookie"))
        login.read()

        self.connection.request("GET", "/api/auth/logout")
        logout = self.connection.getresponse()
        self.assertEqual(logout.status, 302)
        self.assertEqual(logout.getheader("Location"), "https://flow.example.test/")
        self.assertIn("flow_session=;", logout.getheader("Set-Cookie"))
        logout.read()

    @staticmethod
    def run_command(command_type="pause"):
        return {
            "schemaVersion": 1, "idempotencyKey": "command-key-000001", "type": command_type,
            "target": {"kind": "run", "project": "demo", "req": "REQ-027"},
            "precondition": {"state": "running"},
        }

<<<<<<< 9e2b4a7ef27c0360273e4d2c110f31839133069d
    def test_destructive_command_requires_confirmation(self):
        status, body = self.post(self.run_command("approve"))
        self.assertEqual((status, body["code"]), (409, "CONFIRMATION_REQUIRED"))
        self.laptop.post_json.assert_not_called()
||||||| f5aa1d3190788a2f58e4928c44fd96a9b9a3e1c7
    def test_authenticated_challenge_request_is_relayed_to_laptop(self) -> None:
        status, content_type, body = self.post_path(
            "/api/remote/v1/challenges",
            {"target": "demo/REQ-027", "typedReq": "REQ-027"},
            self.headers,
        )
=======
    def test_web_decision_answer_is_validated_and_translated_for_laptop(self) -> None:
        command = self.command("answer-decision")
        command.update({"idempotencyKey": "decision-command-key-0001", "requestId": "T2:1",
                       "option": "retry", "reason": "Reintentar"})
        command["precondition"] = {"state": "open"}

        status, _content_type, body = self.post(command)

        self.assertEqual((status, body["status"]), (202, "accepted"))
        self.assertEqual(self.laptop.command_calls[-1]["params"], {
            "request_id": "T2:1", "option": "retry", "reason": "Reintentar",
        })

    def test_round_answer_envelope_relays_answers_to_laptop(self) -> None:
        command = self.command("answer-round")
        command.update({"idempotencyKey": "round-command-key-0001",
                       "target": {"kind": "round", "project": "demo", "req": "REQ-027", "roundId": "2"},
                       "round": 2, "answers": {"q1": {"text": "Keep scope"}}})
        command["precondition"] = {"state": "open"}

        status, _content_type, body = self.post(command)

        self.assertEqual((status, body["status"]), (202, "accepted"))
        self.assertEqual(self.laptop.command_calls[-1]["params"], {
            "round": 2, "answers": {"q1": {"text": "Keep scope"}},
        })

    def test_expired_event_cursor_resets_then_sse_and_telegram_delivery_resume(self) -> None:
        LaptopEventsHandler.requested_cursors = []
        laptop_server = ThreadingHTTPServer(("127.0.0.1", 0), LaptopEventsHandler)
        laptop_thread = threading.Thread(target=laptop_server.serve_forever, daemon=True)
        laptop_thread.start()
        self.addCleanup(laptop_server.server_close)
        self.addCleanup(laptop_server.shutdown)
        self.runtime.laptop = LaptopClient(f"http://127.0.0.1:{laptop_server.server_port}", "test-key")
        self.runtime.event_cursor = "expired-cursor"
        self.runtime._poll_events()
        self.assertEqual(self.runtime.event_cursor, "")

        self.runtime._poll_events()

        self.assertEqual(LaptopEventsHandler.requested_cursors, ["expired-cursor", ""])
        self.assertEqual(self.runtime.event_cursor, "fresh-cursor")
        self.assertEqual(self.runtime.stream.after(None)[0][1], LaptopEventsHandler.event)
        delivered = []
        self.runtime.outbox.deliver_due(delivered.append)
        self.assertEqual(len(delivered), 1)

    def test_authenticated_challenge_request_is_relayed_to_laptop(self) -> None:
        status, content_type, body = self.post_path(
            "/api/remote/v1/challenges",
            {"target": "demo/REQ-027", "typedReq": "REQ-027"},
            self.headers,
        )
>>>>>>> e5f3b15ac8278a1920c8feef414f89bd689013ca

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

    def test_authenticated_challenge_http_entrypoint_relays_to_laptop(self):
        self.laptop.post_json.return_value = {"challengeId": "challenge-token-1234", "expiresIn": 120}
        status, body = self.post_path("/api/remote/v1/challenges", {
            "target": "demo/REQ-027", "typedReq": "REQ-027",
        }, {
            "Origin": "https://flow.example.test", "X-Flow-Request": "1",
            "Cookie": f"flow_session={self.session}", "Content-Type": "application/json",
        })
        self.assertEqual(status, 200)
        self.assertEqual(body["challengeId"], "challenge-token-1234")
        self.laptop.post_json.assert_called_once_with("/api/remote/v1/challenges", {
            "target": "demo/REQ-027", "typedReq": "REQ-027",
        })

    def test_public_command_and_challenge_work_through_the_real_laptop_ledger(self):
        laptop_server = ThreadingHTTPServer(("127.0.0.1", 0), LaptopLedgerHandler)
        laptop_thread = threading.Thread(target=laptop_server.serve_forever, daemon=True)
        laptop_thread.start()
        self.addCleanup(laptop_server.server_close)
        self.addCleanup(laptop_server.shutdown)
        self.runtime.laptop = LaptopClient(f"http://127.0.0.1:{laptop_server.server_port}", "test-key")
        with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": "test-key", "BITACORA_ROOT": self.temp.name}), \
                patch.object(bt_remote_api, "_target_state", lambda *_args: {"state": "running"}), \
                patch.dict(bt_remote_api.HANDLERS, {"pause": lambda *_args: {"paused": True}}, clear=True):
            status, _body = self.post(self.run_command())
            self.assertEqual(status, 200)

            challenge_status, challenge = self.post_path("/api/remote/v1/challenges", {
                "target": "demo/REQ-027", "typedReq": "REQ-027",
            }, {
                "Origin": "https://flow.example.test", "X-Flow-Request": "1",
                "Cookie": f"flow_session={self.session}", "Content-Type": "application/json",
            })
            self.assertEqual(challenge_status, 200)
            self.assertTrue(challenge.get("challengeId"))

    def test_challenge_http_entrypoint_requires_authenticated_session(self):
        status, body = self.post_path("/api/remote/v1/challenges", {
            "target": "demo/REQ-027", "typedReq": "REQ-027",
        }, {
            "Origin": "https://flow.example.test", "X-Flow-Request": "1",
            "Content-Type": "application/json",
        })
        self.assertEqual((status, body["error"]), (401, "unauthorized"))
        self.laptop.post_json.assert_not_called()

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
