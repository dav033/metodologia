import json
import http.client
import threading
import tempfile
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
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
        self.laptop.command.return_value = (200, {"status": "OK", "code": None})
        self.laptop.challenge.return_value = (200, {"challengeId": "challenge-token", "expiresIn": 120})
        self.runtime = GatewayRuntime(config(Path(self.temp.name) / "gateway.sqlite"), laptop=self.laptop,
                                      sender=lambda _: None)

    def test_destructive_command_without_challenge_is_refused_without_forwarding(self):
        result = self.runtime.submit_command(command(type="launch", route=None))
        self.assertEqual(result["code"], "CONFIRMATION_REQUIRED")
        self.laptop.command.assert_not_called()

    def test_destructive_command_with_empty_or_mismatched_challenge_is_refused(self):
        for confirmation in ({}, {"challengeId": "challenge-token", "typedReq": "REQ-999"}):
            with self.subTest(confirmation=confirmation):
                result = self.runtime.submit_command(command(type="launch", route=None, confirmation=confirmation))
                self.assertEqual(result["code"], "CONFIRMATION_REQUIRED")
        self.laptop.command.assert_not_called()

    def test_offline_laptop_returns_laptop_offline_without_forwarding(self):
        self.runtime.liveness.status = LaptopStatus.OFFLINE
        result = self.runtime.submit_command(command())
        self.assertEqual(result["code"], "LAPTOP_OFFLINE")
        self.laptop.command.assert_not_called()

    def test_timeout_returns_unknown_outcome_with_idempotency_key(self):
        self.laptop.command.side_effect = UpstreamTimeout("late response")
        result = self.runtime.submit_command(command())
        self.assertEqual(result["code"], "UNKNOWN_OUTCOME")
        self.assertEqual(result["idempotency_key"], "retry-key-00000001")

    def test_confirmation_challenge_is_relayed_with_string_target(self):
        result = self.runtime.issue_challenge({
            "target": {"kind": "run", "project": "demo", "req": "REQ-027"},
            "typedReq": "REQ-027",
        })
        self.assertEqual(result["challengeId"], "challenge-token")
        self.laptop.challenge.assert_called_once_with({"target": "demo/REQ-027", "typedReq": "REQ-027"})

    def test_route_object_is_translated_to_string_selectors_for_laptop_ledger(self):
        translated = _ledger_command(command())
        self.assertEqual(translated["target"], "demo/REQ-027")
        self.assertEqual(translated["params"], {
            "task": "T4", "route": "route:abc", "model": "sonnet", "account": "work"})
        self.runtime.submit_command(command())
        forwarded = self.laptop.command.call_args.args[0]
        self.assertEqual(forwarded["params"]["route"], "route:abc")
        self.assertEqual(forwarded["params"]["model"], "sonnet")
        self.assertEqual(forwarded["params"]["account"], "work")

    def test_phone_payloads_reach_laptop_http_with_route_round_and_edit_fields(self):
        received = []

        class LaptopEndpoint(BaseHTTPRequestHandler):
            def do_POST(self):
                payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                self.server.received.append((self.path, self.headers.get("Authorization"), payload))
                body = json.dumps({"status": "OK"}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, _format, *_args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), LaptopEndpoint)
        server.received = received
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join, 2)
        self.addCleanup(server.shutdown)
        runtime = GatewayRuntime(
            GatewayConfig(f"http://127.0.0.1:{server.server_port}", "test-key", "test-token",
                          "test-chat", Path(self.temp.name) / "http-gateway.sqlite"),
            sender=lambda _: None,
        )

        route_request = command(route={"route_id": "route:phone", "model": "sonnet", "account": "work"})
        round_request = command(
            type="answer-round",
            target={"kind": "round", "project": "demo", "req": "REQ-027", "roundId": "2"},
            round=2, answer={"Q1": "yes"},
        )
        edit_request = command(
            type="edit-brief",
            target={"kind": "task", "project": "demo", "req": "REQ-027", "taskId": "T1"},
            field="acceptance_criteria", value="Keep the chosen route.",
            confirmation={"challengeId": "challenge-token", "typedReq": "REQ-027"},
        )
        round_request.pop("route")
        edit_request.pop("route")

        for request in (route_request, round_request, edit_request):
            self.assertEqual(runtime.submit_command(request)["status"], "OK")

        self.assertEqual([item[0] for item in received], ["/api/remote/v1/commands"] * 3)
        self.assertEqual([item[1] for item in received], ["Bearer test-key"] * 3)
        sent = [item[2] for item in received]
        self.assertEqual(sent[0]["params"], {
            "task": "T4", "route": "route:phone", "model": "sonnet", "account": "work"})
        self.assertEqual(sent[1]["params"], {"round": 2, "answers": {"Q1": "yes"}})
        self.assertEqual(sent[2]["params"], {
            "task": "T1", "field": "acceptance_criteria", "value": "Keep the chosen route."})
        self.assertEqual(sent[2]["confirmation"], {
            "challenge_id": "challenge-token", "typed_req": "REQ-027"})

    def test_authenticated_http_routes_forward_commands_and_challenges(self):
        database = Path(self.temp.name) / "gateway-http.sqlite"
        runtime = GatewayRuntime(config(database), laptop=self.laptop, sender=lambda _: None)
        auth = OAuthConfig("client", "secret", "test-session-secret-with-more-than-32-bytes",
                           "https://flow.example.test", str(database))
        token = SessionStore(str(database), auth.session_secret).create_session("owner")
        server = create_server(auth, ("127.0.0.1", 0), runtime=runtime)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        connection = http.client.HTTPConnection("127.0.0.1", server.server_port)
        headers = {"Origin": auth.frontend_origin, "X-Flow-Request": "1",
                   "Cookie": f"flow_session={token}", "Content-Type": "application/json"}
        self.addCleanup(connection.close)
        self.addCleanup(server.shutdown)
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join, 2)

        challenge = {"target": "demo/REQ-027", "typedReq": "REQ-027"}
        self.laptop.challenge.return_value = (201, {"challengeId": "challenge-token", "expiresIn": 120})
        connection.request("POST", "/api/remote/v1/challenges", json.dumps(challenge), headers)
        challenge_response = connection.getresponse()
        self.assertEqual(challenge_response.status, 201)
        self.assertEqual(json.loads(challenge_response.read())["challengeId"], "challenge-token")

        self.laptop.command.return_value = (200, {"status": "OK", "code": None})
        connection.request("POST", "/api/remote/v1/commands", json.dumps(command()), headers)
        command_response = connection.getresponse()
        self.assertEqual(command_response.status, 200)
        self.assertEqual(json.loads(command_response.read())["status"], "OK")
        self.assertEqual(self.laptop.challenge.call_count, 1)
        self.assertEqual(self.laptop.command.call_count, 1)

        self.laptop.command.side_effect = UpstreamTimeout("late response")
        connection.request("POST", "/api/remote/v1/commands", json.dumps(command()), headers)
        timeout_response = connection.getresponse()
        timeout_body = json.loads(timeout_response.read())
        self.assertEqual(timeout_response.status, 503)
        self.assertEqual(timeout_body["code"], "UNKNOWN_OUTCOME")
        self.assertEqual(timeout_body["idempotencyKey"], "retry-key-00000001")

        runtime.liveness.status = LaptopStatus.OFFLINE
        connection.request("POST", "/api/remote/v1/commands", json.dumps(command()), headers)
        offline_response = connection.getresponse()
        self.assertEqual(offline_response.status, 410)
        self.assertEqual(json.loads(offline_response.read())["code"], "LAPTOP_OFFLINE")


if __name__ == "__main__":
    unittest.main()
