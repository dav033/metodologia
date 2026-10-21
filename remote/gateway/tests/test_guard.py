from __future__ import annotations

import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.parse import urlencode

from auth import OAuthConfig, SESSION_COOKIE, SessionStore
from server import create_server


class RequestGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.server = create_server(
            OAuthConfig(
                client_id="test-client",
                client_secret="test-secret",
                session_secret="test-session-secret-with-more-than-32-bytes",
                frontend_origin="https://flow.example.test",
                database_path=str(Path(self.temp_dir.name) / "gateway.sqlite"),
            ),
            ("127.0.0.1", 0),
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port)

    def tearDown(self) -> None:
        self.connection.close()
        self.server.shutdown()
        self.server.server_close()
        self.temp_dir.cleanup()

    def request(self, method: str, path: str, headers: dict[str, str] | None = None):
        self.connection.request(method, path, headers=headers or {})
        response = self.connection.getresponse()
        body = response.read()
        return response.status, body

    def test_post_without_flow_request_header_is_refused(self) -> None:
        status, body = self.request("POST", "/api/remote/v1/commands", {"Origin": "https://flow.example.test"})
        self.assertEqual(status, 403)
        self.assertEqual(json.loads(body), {"error": "forbidden"})

    def test_post_from_foreign_origin_is_refused(self) -> None:
        status, body = self.request("POST", "/api/remote/v1/commands", {
            "Origin": "https://attacker.example",
            "X-Flow-Request": "1",
        })
        self.assertEqual(status, 403)
        self.assertEqual(json.loads(body), {"error": "forbidden"})

    def test_sixth_failed_login_in_a_minute_is_throttled(self) -> None:
        statuses = []
        for _ in range(6):
            status, _ = self.request("GET", "/api/auth/callback?" + urlencode({"state": "invalid", "code": "invalid"}))
            statuses.append(status)
        self.assertEqual(statuses, [400, 400, 400, 400, 400, 429])

    def test_oauth_login_starts_are_throttled(self) -> None:
        statuses = [self.request("GET", "/api/auth/login")[0] for _ in range(6)]
        self.assertEqual(statuses, [302, 302, 302, 302, 302, 429])

    def test_command_rate_limit_rejects_the_thirty_first_request(self) -> None:
        headers = {"Origin": "https://flow.example.test", "X-Flow-Request": "1"}
        token = SessionStore(str(Path(self.temp_dir.name) / "gateway.sqlite"),
                             "test-session-secret-with-more-than-32-bytes").create_session("dav033")
        authenticated = {**headers, "Cookie": f"{SESSION_COOKIE}={token}"}
        statuses = [self.request("POST", "/api/remote/v1/commands", authenticated)[0] for _ in range(31)]
        self.assertEqual(statuses[:30], [404] * 30)
        self.assertEqual(statuses[30], 429)

    def test_anonymous_commands_do_not_consume_authenticated_command_quota(self) -> None:
        headers = {"Origin": "https://flow.example.test", "X-Flow-Request": "1"}
        anonymous = [self.request("POST", "/api/remote/v1/commands", headers)[0] for _ in range(30)]
        self.assertEqual(anonymous, [401] * 30)

        token = SessionStore(str(Path(self.temp_dir.name) / "gateway.sqlite"),
                             "test-session-secret-with-more-than-32-bytes").create_session("dav033")
        authenticated = {**headers, "Cookie": f"{SESSION_COOKIE}={token}"}
        status, _ = self.request("POST", "/api/remote/v1/commands", authenticated)
        self.assertEqual(status, 404)

    def test_command_quota_is_shared_by_owner_across_sessions(self) -> None:
        headers = {"Origin": "https://flow.example.test", "X-Flow-Request": "1"}
        store = SessionStore(str(Path(self.temp_dir.name) / "gateway.sqlite"),
                             "test-session-secret-with-more-than-32-bytes")
        owner_session = store.create_session("dav033")
        another_owner_session = store.create_session("another-owner")
        owner_headers = {**headers, "Cookie": f"{SESSION_COOKIE}={owner_session}"}
        same_owner_headers = {**headers, "Cookie": f"{SESSION_COOKIE}={store.create_session('dav033')}"}
        another_owner_headers = {**headers, "Cookie": f"{SESSION_COOKIE}={another_owner_session}"}

        statuses = [self.request("POST", "/api/remote/v1/commands", owner_headers)[0] for _ in range(30)]
        self.assertEqual(statuses, [404] * 30)
        self.assertEqual(self.request("POST", "/api/remote/v1/commands", same_owner_headers)[0], 429)
        self.assertEqual(self.request("POST", "/api/remote/v1/commands", another_owner_headers)[0], 404)


if __name__ == "__main__":
    unittest.main()
