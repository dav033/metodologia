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
<<<<<<< a474fe7810a1d2a36f9a5f0474a49e4d4dadd236
from upstream import UpstreamTimeout
||||||| 6d69194de8a49c55d12c9d73b42d9cda2631c1dd
from upstream import LaptopClient, UpstreamTimeout

SCRIPTS = Path(__file__).resolve().parents[3] / "skill" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import bt_remote_api
=======
from upstream import LaptopClient, UpstreamResponseError, UpstreamTimeout

SCRIPTS = Path(__file__).resolve().parents[3] / "skill" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import bt_remote_api
>>>>>>> d5722a644747de28545fa30eb743fa0997f37253


<<<<<<< a474fe7810a1d2a36f9a5f0474a49e4d4dadd236
||||||| 6d69194de8a49c55d12c9d73b42d9cda2631c1dd
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
=======
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


>>>>>>> d5722a644747de28545fa30eb743fa0997f37253
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


class CommandRelayHttpTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        database = Path(self.temp.name) / "gateway.sqlite"
        self.oauth = OAuthConfig(
            client_id="test-client", client_secret="test-secret",
            session_secret="test-session-secret-with-more-than-32-bytes",
            frontend_origin="https://flow.example.test", database_path=str(database),
        )
        self.session = SessionStore(str(database), self.oauth.session_secret).create_session("dav033")
        self.laptop = Mock()
        self.laptop.post_json.return_value = {"status": "OK", "code": None}
        self.runtime = GatewayRuntime(config(database), laptop=self.laptop, sender=lambda _: None)
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
        self.addCleanup(self.runtime.outbox._db.close)
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.addCleanup(self.connection.close)

    def post_path(self, path, body, headers=None):
        self.connection.request("POST", path, json.dumps(body), headers or self.headers)
        response = self.connection.getresponse()
        payload = json.loads(response.read())
        return response.status, payload

    def test_displayed_github_and_logout_routes_are_real_http_entrypoints(self):
        self.connection.request("GET", "/api/auth/github")
        response = self.connection.getresponse()
        self.assertEqual(response.status, 302)
        self.assertIn("github.com", response.getheader("Location"))

        self.connection.request("GET", "/api/auth/logout")
        response = self.connection.getresponse()
        self.assertEqual(response.status, 302)
        self.assertEqual(response.getheader("Location"), "https://flow.example.test/")
        self.assertIn("Max-Age=0", response.getheader("Set-Cookie"))

    def test_public_pause_http_command_is_translated_to_laptop_ledger_schema(self):
        public_command = {
            "schemaVersion": 1,
            "idempotencyKey": "command-key-000001",
            "type": "pause",
            "target": {"kind": "run", "project": "demo", "req": "REQ-027"},
            "precondition": {"state": "running"},
        }
        status, body = self.post_path("/api/remote/v1/commands", public_command)

<<<<<<< a474fe7810a1d2a36f9a5f0474a49e4d4dadd236
||||||| 6d69194de8a49c55d12c9d73b42d9cda2631c1dd
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
=======
    def test_expired_feed_cursor_is_reset_and_later_events_reach_telegram(self):
        event = {"id": "evt-decision", "type": "plan.waiting", "dedupeKey": "evt-decision",
                 "target": {"req": "REQ-027"}}
        self.runtime.event_cursor = "expired-cursor"
        self.laptop.events.side_effect = [
            UpstreamResponseError(400, {"code": "INVALID_CURSOR"}),
            {"events": [event], "nextCursor": "fresh-cursor"},
        ]

        self.runtime._poll_events()
        self.assertEqual(self.runtime.event_cursor, "")
        delivered = []
        self.runtime.outbox.deliver_due(delivered.append)
        self.assertEqual(delivered, [])

        self.runtime._poll_events()
        self.runtime.outbox.deliver_due(delivered.append)

        self.assertEqual(self.laptop.events.call_args_list[0].args, ("expired-cursor",))
        self.assertEqual(self.laptop.events.call_args_list[1].args, ("",))
        self.assertEqual(self.runtime.event_cursor, "fresh-cursor")
        self.assertEqual(len(delivered), 1)

    def test_web_decision_answer_passes_gateway_allowlist_and_translates_request_id(self):
        request = command(type="answer-decision", requestId="T2:1", option="retry", reason="Retry")
        request["target"] = {"kind": "run", "project": "demo", "req": "REQ-027"}
        request.pop("route")
        request["precondition"] = {"state": "open", "revision": 2}

        result = self.runtime.submit_command(request)

        self.assertEqual(result["status"], "OK")
        self.assertEqual(self.laptop.post_json.call_args.args[1]["params"], {
            "request_id": "T2:1", "option": "retry", "reason": "Retry"})
        self.assertEqual(self.runtime.submit_command(command(type="unknown"))["code"], "INVALID_COMMAND")

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

    def test_authenticated_challenge_http_entrypoint_relays_to_laptop(self):
        self.laptop.post_json.return_value = {"challengeId": "challenge-token-1234", "expiresIn": 120}
        status, body = self.post_path("/api/remote/v1/challenges", {
            "target": "demo/REQ-027", "typedReq": "REQ-027",
        }, {
            "Origin": "https://flow.example.test", "X-Flow-Request": "1",
            "Cookie": f"flow_session={self.session}", "Content-Type": "application/json",
        })
>>>>>>> d5722a644747de28545fa30eb743fa0997f37253
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "OK")
        self.laptop.post_json.assert_called_once_with("/api/remote/v1/commands", {
            "idempotency_key": "command-key-000001",
            "command": "pause",
            "target": "demo/REQ-027",
            "origin": "web",
            "params": {},
            "precondition": {"state": "running"},
        })

    def test_authenticated_challenge_http_relay_enables_confirmed_command(self):
        self.laptop.post_json.side_effect = [
            {"challengeId": "laptop-challenge-000001", "expiresIn": 120},
            {"status": "OK", "code": None},
        ]
        challenge_status, challenge = self.post_path("/api/remote/v1/challenges", {
            "target": "demo/REQ-027", "typedReq": "REQ-027",
        })
        self.assertEqual(challenge_status, 200)
        self.assertEqual(challenge["challengeId"], "laptop-challenge-000001")

        command_status, command_body = self.post_path("/api/remote/v1/commands", {
            "schemaVersion": 1,
            "idempotencyKey": "approve-command-key-0001",
            "type": "approve",
            "target": {"kind": "run", "project": "demo", "req": "REQ-027"},
            "precondition": {"state": "running"},
            "confirmation": {"challengeId": challenge["challengeId"], "typedReq": "REQ-027"},
        })

        self.assertEqual(command_status, 200)
        self.assertEqual(command_body["status"], "OK")
        self.assertEqual(self.laptop.post_json.call_args_list[0].args, (
            "/api/remote/v1/challenges", {"target": "demo/REQ-027", "typedReq": "REQ-027"}))
        self.assertEqual(self.laptop.post_json.call_args_list[1].args[1]["confirmation"], {
            "challenge_id": "laptop-challenge-000001", "typed_req": "REQ-027"})

    def test_challenge_and_command_mutations_require_session_and_request_marker(self):
        body = {"target": "demo/REQ-027", "typedReq": "REQ-027"}
        no_session = {key: value for key, value in self.headers.items() if key != "Cookie"}
        self.assertEqual(self.post_path("/api/remote/v1/challenges", body, no_session)[0], 401)
        self.assertEqual(self.post_path("/api/remote/v1/commands", {}, no_session)[0], 401)

        no_marker = {key: value for key, value in self.headers.items() if key != "X-Flow-Request"}
        self.assertEqual(self.post_path("/api/remote/v1/challenges", body, no_marker)[0], 403)
        self.assertEqual(self.post_path("/api/remote/v1/commands", {}, no_marker)[0], 403)
        self.laptop.post_json.assert_not_called()


if __name__ == "__main__":
    unittest.main()
