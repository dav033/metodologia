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
<<<<<<< 0d0dd48d35237123898d202a25bcd85838d7ff3f
        headers = {"Origin": "https://flow.example.test", "X-Flow-Request": "1"}
        statuses = [self.request("POST", "/api/remote/v1/commands", headers)[0] for _ in range(31)]
        self.assertEqual(statuses[:30], [404] * 30)
        self.assertEqual(statuses[30], 429)
||||||| 27eddbf4d46527a94f9c3d70f4f01c34f744c5ca
<<<<<<< 149640c82b5f108f4c5a7eac70fb7f073cffb6ab
        headers = {"Origin": "https://flow.example.test", "X-Flow-Request": "1"}
        statuses = [self.request("POST", "/api/remote/v1/commands", headers)[0] for _ in range(31)]
        self.assertEqual(statuses[:30], [404] * 30)
        self.assertEqual(statuses[30], 429)
||||||| 7beb8fe6bae2ba79076c3e6f50fb2a34c263eba7
<<<<<<< 73c6de87b56d1741871566254ce0446c8ae6ecf0
        headers = {"Origin": "https://flow.example.test", "X-Flow-Request": "1"}
||||||| eabe6586ac38bb6594ad8a958a47403c0d734a82
        headers = {"Origin": "https://flow.example.test", "X-Flow-Request": "1"}
<<<<<<< ff6d46bc29f4b6a862628af4bad381b77e5a9d7a
=======
        headers = {"Origin": "https://flow.example.test", "X-Flow-Request": "1", **self.owner_cookie()}
>>>>>>> c84c8fbab2d22c2e569017ae577c884a2ce38dac
        statuses = [self.request("POST", "/api/remote/v1/commands", headers)[0] for _ in range(31)]
        self.assertEqual(statuses[:30], [200] * 30)
        self.assertEqual(statuses[30], 429)

<<<<<<< 73c6de87b56d1741871566254ce0446c8ae6ecf0
||||||| eabe6586ac38bb6594ad8a958a47403c0d734a82
||||||| 0ff0939d5307dbf48978d18f532532ca5102158c
<<<<<<< 7bab8d3fc65eb4681168829156ff0d7510a656a6
        statuses = [self.request("POST", "/api/remote/v1/commands", headers)[0] for _ in range(31)]
        self.assertEqual(statuses[:30], [404] * 30)
        self.assertEqual(statuses[30], 429)

||||||| 194da776c0e1544e07a5ba6f7ad2b3a8a215b287
        statuses = [self.request("POST", "/api/remote/v1/commands", headers)[0] for _ in range(31)]
        self.assertEqual(statuses[:30], [404] * 30)
        self.assertEqual(statuses[30], 429)

<<<<<<< ede87253b5f40c74d13b25da89f0c8ea70ac0e63
||||||| c0af0bd65e6b3d72daaee036a0c60fb962d41ec6
    def test_anonymous_commands_do_not_consume_authenticated_command_quota(self) -> None:
        headers = {"Origin": "https://flow.example.test", "X-Flow-Request": "1"}
        anonymous = [self.request("POST", "/api/remote/v1/commands", headers)[0] for _ in range(30)]
        self.assertEqual(anonymous, [401] * 30)

        token = SessionStore(str(Path(self.temp_dir.name) / "gateway.sqlite"),
                             "test-session-secret-with-more-than-32-bytes").create_session("dav033")
        authenticated = {**headers, "Cookie": f"{SESSION_COOKIE}={token}"}
        status, _ = self.request("POST", "/api/remote/v1/commands", authenticated)
        self.assertEqual(status, 404)

=======
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

>>>>>>> cb44d05b7dd50284f6561c3aa1724df1536dd260
=======
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

    def test_oauth_login_starts_are_throttled(self) -> None:
        statuses = [self.request("GET", "/api/auth/login")[0] for _ in range(6)]
        self.assertEqual(statuses, [302, 302, 302, 302, 302, 429])
>>>>>>> 7f1c20f62aa58583d40c3157b63a1f7f05b22ad3
=======
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
        self.assertEqual(self.request("POST", "/api/remote/v1/commands", authenticated)[0], 404)

    def test_command_quota_is_shared_by_owner_across_sessions(self) -> None:
        headers = {"Origin": "https://flow.example.test", "X-Flow-Request": "1"}
        store = SessionStore(str(Path(self.temp_dir.name) / "gateway.sqlite"),
                             "test-session-secret-with-more-than-32-bytes")
        owner_session = store.create_session("dav033")
        same_owner_session = store.create_session("dav033")
        another_owner_session = store.create_session("another-owner")
        owner_headers = {**headers, "Cookie": f"{SESSION_COOKIE}={owner_session}"}
        same_owner_headers = {**headers, "Cookie": f"{SESSION_COOKIE}={same_owner_session}"}
        another_owner_headers = {**headers, "Cookie": f"{SESSION_COOKIE}={another_owner_session}"}

        statuses = [self.request("POST", "/api/remote/v1/commands", owner_headers)[0] for _ in range(30)]
        self.assertEqual(statuses, [404] * 30)
        self.assertEqual(self.request("POST", "/api/remote/v1/commands", same_owner_headers)[0], 429)
        self.assertEqual(self.request("POST", "/api/remote/v1/commands", another_owner_headers)[0], 404)

    def test_oauth_login_starts_are_throttled(self) -> None:
        statuses = [self.request("GET", "/api/auth/login")[0] for _ in range(6)]
        self.assertEqual(statuses, [302, 302, 302, 302, 302, 429])
>>>>>>> f8f178bc31b43c696b1f798fad010e9d92350e6f
=======
    def test_anonymous_commands_do_not_consume_owner_command_quota(self) -> None:
        headers = {"Origin": "https://flow.example.test", "X-Flow-Request": "1"}
        anonymous = [self.request("POST", "/api/remote/v1/commands", headers)[0] for _ in range(30)]
        self.assertEqual(anonymous, [401] * 30)
        self.assertEqual(self.request("POST", "/api/remote/v1/commands", {**headers, **self.owner_cookie()})[0], 200)

    def test_command_quota_is_shared_by_owner_across_sessions(self) -> None:
        headers = {"Origin": "https://flow.example.test", "X-Flow-Request": "1"}
        owner = self.owner_cookie()
        same_owner = self.owner_cookie()
        another_owner = self.owner_cookie("another-owner")
        statuses = [self.request("POST", "/api/remote/v1/commands", {**headers, **owner})[0] for _ in range(30)]
        self.assertEqual(statuses, [200] * 30)
        self.assertEqual(self.request("POST", "/api/remote/v1/commands", {**headers, **same_owner})[0], 429)
        self.assertEqual(self.request("POST", "/api/remote/v1/commands", {**headers, **another_owner})[0], 200)

    def test_oauth_login_starts_are_throttled_across_login_aliases(self) -> None:
        paths = ["/api/auth/login", "/api/auth/github"] * 3
        statuses = [self.request("GET", path)[0] for path in paths]
        self.assertEqual(statuses, [302, 302, 302, 302, 302, 429])

>>>>>>> c84c8fbab2d22c2e569017ae577c884a2ce38dac
=======
        headers = {"Origin": "https://flow.example.test", "X-Flow-Request": "1", **self.owner_cookie()}
        statuses = [self.request("POST", "/api/remote/v1/commands", headers)[0] for _ in range(31)]
        self.assertEqual(statuses[:30], [200] * 30)
        self.assertEqual(statuses[30], 429)

    def test_anonymous_commands_do_not_consume_owner_command_quota(self) -> None:
        headers = {"Origin": "https://flow.example.test", "X-Flow-Request": "1"}
        anonymous = [self.request("POST", "/api/remote/v1/commands", headers)[0] for _ in range(30)]
        self.assertEqual(anonymous, [401] * 30)
        self.assertEqual(self.request("POST", "/api/remote/v1/commands", {**headers, **self.owner_cookie()})[0], 200)

    def test_command_quota_is_shared_by_owner_across_sessions(self) -> None:
        headers = {"Origin": "https://flow.example.test", "X-Flow-Request": "1"}
        owner = self.owner_cookie()
        same_owner = self.owner_cookie()
        another_owner = self.owner_cookie("another-owner")
        statuses = [self.request("POST", "/api/remote/v1/commands", {**headers, **owner})[0] for _ in range(30)]
        self.assertEqual(statuses, [200] * 30)
        self.assertEqual(self.request("POST", "/api/remote/v1/commands", {**headers, **same_owner})[0], 429)
        self.assertEqual(self.request("POST", "/api/remote/v1/commands", {**headers, **another_owner})[0], 200)

    def test_oauth_login_starts_are_throttled_across_login_aliases(self) -> None:
        paths = ["/api/auth/login", "/api/auth/github"] * 3
        statuses = [self.request("GET", path)[0] for path in paths]
        self.assertEqual(statuses, [302, 302, 302, 302, 302, 429])
>>>>>>> 62324990f833b9b1a3d421375cb5438383f2e25c
=======
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
>>>>>>> 5a5761a021f0c8d1a035ba4a2695e335afaa258b


if __name__ == "__main__":
    unittest.main()
