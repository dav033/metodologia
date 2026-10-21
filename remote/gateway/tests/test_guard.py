from __future__ import annotations

import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.parse import urlencode

from auth import OAuthConfig
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

    def owner_cookie(self, login: str = "dav033") -> dict[str, str]:
        from auth import SESSION_COOKIE, SessionStore

        token = SessionStore(str(Path(self.temp_dir.name) / "gateway.sqlite"),
                             "test-session-secret-with-more-than-32-bytes").create_session(login)
        return {"Cookie": f"{SESSION_COOKIE}={token}"}

    def test_command_rate_limit_rejects_the_thirty_first_request(self) -> None:
        headers = {"Origin": "https://flow.example.test", "X-Flow-Request": "1", **self.owner_cookie()}
        statuses = [self.request("POST", "/api/remote/v1/commands", headers)[0] for _ in range(31)]
        self.assertEqual(statuses[:30], [404] * 30)
        self.assertEqual(statuses[30], 429)

    def test_anonymous_commands_do_not_consume_owner_command_quota(self) -> None:
        headers = {"Origin": "https://flow.example.test", "X-Flow-Request": "1"}
        anonymous = [self.request("POST", "/api/remote/v1/commands", headers)[0] for _ in range(30)]
        self.assertEqual(anonymous, [401] * 30)
        self.assertEqual(self.request("POST", "/api/remote/v1/commands",
                                      {**headers, **self.owner_cookie()})[0], 404)

    def test_command_quota_is_shared_by_owner_across_sessions(self) -> None:
        headers = {"Origin": "https://flow.example.test", "X-Flow-Request": "1"}
        owner = self.owner_cookie()
        same_owner = self.owner_cookie()
        another_owner = self.owner_cookie("another-owner")
        statuses = [self.request("POST", "/api/remote/v1/commands", {**headers, **owner})[0]
                    for _ in range(30)]
        self.assertEqual(statuses, [404] * 30)
        self.assertEqual(self.request("POST", "/api/remote/v1/commands", {**headers, **same_owner})[0], 429)
        self.assertEqual(self.request("POST", "/api/remote/v1/commands", {**headers, **another_owner})[0], 404)

    def test_oauth_login_starts_are_throttled_across_login_aliases(self) -> None:
        paths = ["/api/auth/login", "/api/auth/github"] * 3
        statuses = [self.request("GET", path)[0] for path in paths]
        self.assertEqual(statuses, [302, 302, 302, 302, 302, 429])


if __name__ == "__main__":
    unittest.main()
