import json
import threading
import tempfile
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import Mock

from app import GatewayRuntime, _ledger_command
from config import GatewayConfig
from liveness import LaptopStatus
<<<<<<< 8ecfc9b9879654152f440aae4e87866fc2b072d9
||||||| e056936f8c038f6578c8925eecc5a2ea7eb5ad90
<<<<<<< 6e14d8818318957c2a22229173f0d8756cc62fbb
||||||| cef6803a8bb00ff874d51bb725bd35592ac54d1b
<<<<<<< 95117308c8f8cb3d2df1d6fc5995a46c9c874bd5
from upstream import UpstreamTimeout
||||||| a9d34cf7541f716c9f34151d11e37355821f1f52
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
=======
from server import create_server
from upstream import LaptopClient, UpstreamTimeout

SCRIPTS = Path(__file__).resolve().parents[3] / "skill" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import bt_remote_api
>>>>>>> c0a5e47ed090adf0bb7ad5ad7bdf2c67e37ce775
=======
from server import create_server
>>>>>>> 725ff33443950b7b5e0842d1366bc81f05c1a57c
=======
from server import create_server
>>>>>>> b21af576095cc9c033b3326647f1e1a84fb3152f
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

<<<<<<< 8ecfc9b9879654152f440aae4e87866fc2b072d9
||||||| e056936f8c038f6578c8925eecc5a2ea7eb5ad90
<<<<<<< 6e14d8818318957c2a22229173f0d8756cc62fbb
||||||| cef6803a8bb00ff874d51bb725bd35592ac54d1b
||||||| a9d34cf7541f716c9f34151d11e37355821f1f52
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
=======
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
>>>>>>> c0a5e47ed090adf0bb7ad5ad7bdf2c67e37ce775

=======

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

>>>>>>> 725ff33443950b7b5e0842d1366bc81f05c1a57c
=======

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
        self.addCleanup(self.connection.close)
        self.addCleanup(self.server.shutdown)
        self.addCleanup(self.server.server_close)

    def post_path(self, path, body, headers=None):
        self.connection.request("POST", path, json.dumps(body), headers or self.headers)
        response = self.connection.getresponse()
        return response.status, json.loads(response.read())

    def test_displayed_github_and_logout_routes_are_real_http_entrypoints(self):
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
        self.assertIn("Max-Age=0", logout.getheader("Set-Cookie"))
        logout.read()

    def test_public_pause_command_is_translated_at_the_http_entrypoint(self):
        public_command = {
            "schemaVersion": 1,
            "idempotencyKey": "command-key-000001",
            "type": "pause",
            "target": {"kind": "run", "project": "demo", "req": "REQ-027"},
            "precondition": {"state": "running"},
        }
        status, body = self.post_path("/api/remote/v1/commands", public_command)

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

    def test_authenticated_challenge_relay_supports_confirmed_command(self):
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

    def test_mutations_require_a_session_and_the_web_request_marker(self):
        challenge = {"target": "demo/REQ-027", "typedReq": "REQ-027"}
        without_session = {key: value for key, value in self.headers.items() if key != "Cookie"}
        self.assertEqual(self.post_path("/api/remote/v1/challenges", challenge, without_session)[0], 401)
        self.assertEqual(self.post_path("/api/remote/v1/commands", {}, without_session)[0], 401)

        without_marker = {key: value for key, value in self.headers.items() if key != "X-Flow-Request"}
        self.assertEqual(self.post_path("/api/remote/v1/challenges", challenge, without_marker)[0], 403)
        self.assertEqual(self.post_path("/api/remote/v1/commands", {}, without_marker)[0], 403)
        self.laptop.post_json.assert_not_called()

>>>>>>> b21af576095cc9c033b3326647f1e1a84fb3152f

if __name__ == "__main__":
    unittest.main()
