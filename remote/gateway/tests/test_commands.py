import http.client
import json
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
        self.laptop.post_json.return_value = {"status": "OK", "code": None}
        self.runtime = GatewayRuntime(config(Path(self.temp.name) / "gateway.sqlite"), laptop=self.laptop,
                                      sender=lambda _: None)

    def test_destructive_command_without_challenge_is_refused_without_forwarding(self):
        result = self.runtime.submit_command(command(type="launch", route=None))
        self.assertEqual(result["code"], "CONFIRMATION_REQUIRED")
        self.laptop.post_json.assert_not_called()

    def test_destructive_command_with_empty_or_mismatched_challenge_is_refused(self):
        for confirmation in ({}, {"challengeId": "challenge-token", "typedReq": "REQ-999"}):
            with self.subTest(confirmation=confirmation):
                result = self.runtime.submit_command(command(type="launch", route=None, confirmation=confirmation))
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
        self.session_store = SessionStore(str(database), self.oauth.session_secret)
        self.session = self.session_store.create_session("dav033")
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
        self.addCleanup(self.connection.close)
        self.addCleanup(self.server.shutdown)
        self.addCleanup(self.server.server_close)

    def post(self, path, body, headers=None):
        self.connection.request("POST", path, json.dumps(body), headers or self.headers)
        response = self.connection.getresponse()
        return response.status, json.loads(response.read())

    def test_displayed_sign_in_and_logout_routes_work_and_revoke_session(self):
        self.connection.request("GET", "/api/auth/github")
        login = self.connection.getresponse()
        self.assertEqual(login.status, 302)
        self.assertIn("github.com/login/oauth/authorize", login.getheader("Location"))
        self.assertIn("flow_oauth_state=", login.getheader("Set-Cookie"))
        login.read()

        self.connection.request("GET", "/api/auth/logout", headers={"Cookie": f"flow_session={self.session}"})
        logout = self.connection.getresponse()
        self.assertEqual(logout.status, 302)
        self.assertEqual(logout.getheader("Location"), "https://flow.example.test/")
        self.assertIn("flow_session=;", logout.getheader("Set-Cookie"))
        logout.read()
        self.assertIsNone(self.session_store.get_session(self.session))

    def test_authenticated_public_command_is_translated_at_http_entrypoint(self):
        public_command = {
            "schemaVersion": 1,
            "idempotencyKey": "command-key-000001",
            "type": "pause",
            "target": {"kind": "run", "project": "demo", "req": "REQ-027"},
            "precondition": {"state": "running"},
        }
        status, body = self.post("/api/remote/v1/commands", public_command)

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

<<<<<<< fdc224e41c20baaf18251239055e505699e9db6a
    def test_authenticated_challenge_http_relay_supports_confirmed_command(self):
||||||| abc942f14b9a0fa0d84e36f8efa479328584534c
<<<<<<< f05f8fd659ac343b89d326952a27e078aab647c1
||||||| bb8d45c1c426152ebc0ce48c79c6b29d739fa631
<<<<<<< e6088af660026d2e861b496d907f514eef10722f
    def test_authenticated_challenge_relay_supports_confirmed_command(self):
||||||| 9c190842d7f30c6178e9794e196264c85b92bba2
<<<<<<< 6048a7cab2664fbc1ed484e52a4a784570976dce
    def test_authenticated_challenge_relay_supports_confirmed_command(self):
||||||| a86df111448409a7063f992bae2d9ccdfe498fa4
    def test_authenticated_challenge_http_relay_enables_confirmed_command(self):
=======
    def test_web_decision_answer_passes_gateway_allowlist_and_translates_request_id(self):
        body = {
            "schemaVersion": 1,
            "idempotencyKey": "decision-command-key-0001",
            "type": "answer-decision",
            "target": {"kind": "run", "project": "demo", "req": "REQ-027"},
            "precondition": {"state": "open"},
            "requestId": "T2:1", "option": "retry", "reason": "Retry",
        }

        status, response = self.post_path("/api/remote/v1/commands", body)

        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "OK")
        self.assertEqual(self.laptop.post_json.call_args.args[1]["params"], {
            "request_id": "T2:1", "option": "retry", "reason": "Retry"})

    def test_round_answer_http_command_sends_answers_with_open_round_precondition(self):
        body = {
            "schemaVersion": 1,
            "idempotencyKey": "round-command-key-0001",
            "type": "answer-round",
            "target": {"kind": "round", "project": "demo", "req": "REQ-027", "roundId": "2"},
            "precondition": {"state": "open"},
            "round": 2, "answers": {"q1": {"text": "Keep scope"}},
        }

        status, response = self.post_path("/api/remote/v1/commands", body)

        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "OK")
        self.assertEqual(self.laptop.post_json.call_args.args[1]["params"], {
            "round": 2, "answers": {"q1": {"text": "Keep scope"}}})
        self.assertEqual(self.laptop.post_json.call_args.args[1]["precondition"], {"state": "open"})

    def test_public_command_and_challenge_reach_the_real_laptop_ledger(self):
        laptop_server = ThreadingHTTPServer(("127.0.0.1", 0), LaptopLedgerHandler)
        laptop_thread = threading.Thread(target=laptop_server.serve_forever, daemon=True)
        laptop_thread.start()
        self.addCleanup(laptop_server.server_close)
        self.addCleanup(laptop_server.shutdown)
        self.runtime.laptop = LaptopClient(f"http://127.0.0.1:{laptop_server.server_port}", "test-key")
        with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": "test-key", "BITACORA_ROOT": self.temp.name}), \
                patch.object(bt_remote_api, "_target_state", lambda *_args: {"state": "running"}), \
                patch.dict(bt_remote_api.HANDLERS, {"pause": lambda *_args: {"paused": True}}, clear=True):
            status, _body = self.post_path("/api/remote/v1/commands", {
                "schemaVersion": 1, "idempotencyKey": "command-key-000001", "type": "pause",
                "target": {"kind": "run", "project": "demo", "req": "REQ-027"},
                "precondition": {"state": "running"},
            })
            self.assertEqual(status, 200)

            challenge_status, challenge = self.post_path("/api/remote/v1/challenges", {
                "target": "demo/REQ-027", "typedReq": "REQ-027",
            })

        self.assertEqual(challenge_status, 200)
        self.assertTrue(challenge.get("challengeId"))

    def test_authenticated_challenge_http_relay_enables_confirmed_command(self):
>>>>>>> 4273ff48ab3b1b2c2ef13b15ffc7e756d2fef067
=======
    def test_web_decision_answer_passes_gateway_allowlist_and_translates_request_id(self):
        body = {
            "schemaVersion": 1,
            "idempotencyKey": "decision-command-key-0001",
            "type": "answer-decision",
            "target": {"kind": "run", "project": "demo", "req": "REQ-027"},
            "precondition": {"state": "open"},
            "requestId": "T2:1", "option": "retry", "reason": "Retry",
        }

        status, response = self.post_path("/api/remote/v1/commands", body)

        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "OK")
        self.assertEqual(self.laptop.post_json.call_args.args[1]["params"], {
            "request_id": "T2:1", "option": "retry", "reason": "Retry"})

    def test_round_answer_http_command_sends_answers_with_open_round_precondition(self):
        body = {
            "schemaVersion": 1,
            "idempotencyKey": "round-command-key-0001",
            "type": "answer-round",
            "target": {"kind": "round", "project": "demo", "req": "REQ-027", "roundId": "2"},
            "precondition": {"state": "open"},
            "round": 2, "answers": {"q1": {"text": "Keep scope"}},
        }

        status, response = self.post_path("/api/remote/v1/commands", body)

        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "OK")
        self.assertEqual(self.laptop.post_json.call_args.args[1]["params"], {
            "round": 2, "answers": {"q1": {"text": "Keep scope"}}})
        self.assertEqual(self.laptop.post_json.call_args.args[1]["precondition"], {"state": "open"})

    def test_public_command_and_challenge_reach_the_real_laptop_ledger(self):
        laptop_server = ThreadingHTTPServer(("127.0.0.1", 0), LaptopLedgerHandler)
        laptop_thread = threading.Thread(target=laptop_server.serve_forever, daemon=True)
        laptop_thread.start()
        self.addCleanup(laptop_server.server_close)
        self.addCleanup(laptop_server.shutdown)
        self.runtime.laptop = LaptopClient(f"http://127.0.0.1:{laptop_server.server_port}", "test-key")
        with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": "test-key", "BITACORA_ROOT": self.temp.name}), \
                patch.object(bt_remote_api, "_target_state", lambda *_args: {"state": "running"}), \
                patch.dict(bt_remote_api.HANDLERS, {"pause": lambda *_args: {"paused": True}}, clear=True):
            status, _body = self.post_path("/api/remote/v1/commands", {
                "schemaVersion": 1, "idempotencyKey": "command-key-000001", "type": "pause",
                "target": {"kind": "run", "project": "demo", "req": "REQ-027"},
                "precondition": {"state": "running"},
            })
            self.assertEqual(status, 200)

            challenge_status, challenge = self.post_path("/api/remote/v1/challenges", {
                "target": "demo/REQ-027", "typedReq": "REQ-027",
            })

        self.assertEqual(challenge_status, 200)
        self.assertTrue(challenge.get("challengeId"))

    def test_authenticated_challenge_http_relay_enables_confirmed_command(self):
>>>>>>> 70de5f62178587b71e15d40677732fb4dc3cae8c
=======
    def test_web_decision_and_round_answers_translate_at_the_http_entrypoint(self):
        decision_status, decision_response = self.post_path("/api/remote/v1/commands", {
            "schemaVersion": 1,
            "idempotencyKey": "decision-command-key-0001",
            "type": "answer-decision",
            "target": {"kind": "run", "project": "demo", "req": "REQ-027", "taskId": "T2"},
            "precondition": {"state": "open"},
            "requestId": "T2:1", "option": "retry", "reason": "Retry",
        })
        round_status, round_response = self.post_path("/api/remote/v1/commands", {
            "schemaVersion": 1,
            "idempotencyKey": "round-command-key-0001",
            "type": "answer-round",
            "target": {"kind": "round", "project": "demo", "req": "REQ-027", "roundId": "2"},
            "precondition": {"state": "open"},
            "round": 2, "answer": {"q1": {"text": "Keep scope"}},
        })

        self.assertEqual((decision_status, decision_response["status"]), (200, "OK"))
        self.assertEqual((round_status, round_response["status"]), (200, "OK"))
        decision, round_command = [call.args[1] for call in self.laptop.post_json.call_args_list]
        self.assertEqual(decision["params"], {"request_id": "T2:1", "option": "retry",
                                              "reason": "Retry", "task": "T2"})
        self.assertEqual(round_command["params"], {"round": 2, "answers": {"q1": {"text": "Keep scope"}}})

>>>>>>> 7d0156fc3acf8afdbcdf78e19160f8fd15f17368
    def test_authenticated_challenge_relay_supports_confirmed_command(self):
=======
    def test_web_decision_and_round_answers_translate_at_the_http_entrypoint(self):
        decision_status, decision_response = self.post_path("/api/remote/v1/commands", {
            "schemaVersion": 1,
            "idempotencyKey": "decision-command-key-0001",
            "type": "answer-decision",
            "target": {"kind": "run", "project": "demo", "req": "REQ-027", "taskId": "T2"},
            "precondition": {"state": "open"},
            "requestId": "T2:1", "option": "retry", "reason": "Retry",
        })
        round_status, round_response = self.post_path("/api/remote/v1/commands", {
            "schemaVersion": 1,
            "idempotencyKey": "round-command-key-0001",
            "type": "answer-round",
            "target": {"kind": "round", "project": "demo", "req": "REQ-027", "roundId": "2"},
            "precondition": {"state": "open"},
            "round": 2, "answer": {"q1": {"text": "Keep scope"}},
        })

        self.assertEqual((decision_status, decision_response["status"]), (200, "OK"))
        self.assertEqual((round_status, round_response["status"]), (200, "OK"))
        decision, round_command = [call.args[1] for call in self.laptop.post_json.call_args_list]
        self.assertEqual(decision["params"], {"request_id": "T2:1", "option": "retry",
                                              "reason": "Retry", "task": "T2"})
        self.assertEqual(round_command["params"], {"round": 2, "answers": {"q1": {"text": "Keep scope"}}})

    def test_authenticated_challenge_relay_supports_confirmed_command(self):
>>>>>>> d58d5211dfbc3de3567c96dfad21cbe074ff5303
        self.laptop.post_json.side_effect = [
            {"challengeId": "laptop-challenge-000001", "expiresIn": 120},
            {"status": "OK", "code": None},
        ]
        challenge_status, challenge = self.post("/api/remote/v1/challenges", {
            "target": "demo/REQ-027", "typedReq": "REQ-027",
        })
        self.assertEqual(challenge_status, 200)
        self.assertEqual(challenge["challengeId"], "laptop-challenge-000001")

        command_status, command_body = self.post("/api/remote/v1/commands", {
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

    def test_mutations_require_authenticated_session_and_request_marker(self):
        challenge = {"target": "demo/REQ-027", "typedReq": "REQ-027"}
        without_session = {key: value for key, value in self.headers.items() if key != "Cookie"}
        self.assertEqual(self.post("/api/remote/v1/challenges", challenge, without_session)[0], 401)
        self.assertEqual(self.post("/api/remote/v1/commands", {}, without_session)[0], 401)

        without_marker = {key: value for key, value in self.headers.items() if key != "X-Flow-Request"}
        self.assertEqual(self.post("/api/remote/v1/challenges", challenge, without_marker)[0], 403)
        self.assertEqual(self.post("/api/remote/v1/commands", {}, without_marker)[0], 403)
        self.laptop.post_json.assert_not_called()


if __name__ == "__main__":
    unittest.main()
