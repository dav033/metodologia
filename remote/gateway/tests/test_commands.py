from __future__ import annotations

import http.client
import json
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

from app import create_runtime
from auth import OAuthConfig, SessionStore
from config import GatewayConfig
from server import create_server
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

    def challenge(self, challenge):
        self.challenge_calls.append(challenge)
        return {"challengeId": "laptop-challenge-000001", **challenge, "expiresIn": 120}


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
        return self.post_path("/api/remote/v1/commands", command, self.headers)

    def post_path(self, path: str, value: dict[str, object], headers: dict[str, str]):
        self.connection.request("POST", path, json.dumps(value), headers)
        response = self.connection.getresponse()
        body = response.read()
        return response.status, response.getheader("Content-Type"), json.loads(body)

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
            "params": {},
            "precondition": {"state": "running"},
            "confirmation": {"challenge_id": "challenge-token-1234", "typed_req": "REQ-027"},
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
