from __future__ import annotations

import http.client
import json
import shutil
import sqlite3
import subprocess
import tempfile
import threading
import unittest
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import ClassVar
from urllib.parse import parse_qs, urlencode, urlsplit

from auth import OAuthConfig, SessionStore
from server import create_server


class FakeGitHubHandler(BaseHTTPRequestHandler):
    login = "dav033"
    last_authorize: ClassVar[dict[str, list[str]]] = {}

    def log_message(self, *_args):
        pass

    def do_GET(self):
        if self.path.startswith("/login/oauth/authorize"):
            query = parse_qs(urlsplit(self.path).query)
            type(self).last_authorize = query
            callback = query["redirect_uri"][0] + "?" + urlencode({"code": "test-code", "state": query["state"][0]})
            self.send_response(302)
            self.send_header("Location", callback)
            self.end_headers()
            return
        if self.path == "/user":
            body = json.dumps({"login": type(self).login}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_error(404)

    def do_POST(self):
        body = json.dumps({"access_token": "fake-token", "token_type": "bearer"}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class FrontendRewriteHandler(BaseHTTPRequestHandler):
    """Model Vercel's same-origin /api rewrite while preserving the browser Host."""

    backend: tuple[str, int] = ("127.0.0.1", 0)
    callback_cookie: str | None = None
    state_cookie_response: str | None = None
    callback_query: str | None = None
    callback_requests: ClassVar[list[tuple[str | None, str]]] = []
    set_cookies: ClassVar[list[str]] = []
    github_browser_origin = ""

    def log_message(self, *_args):
        pass

    def do_GET(self):
        if self.path == "/api/auth/login":
            type(self).state_cookie_response = None
        if self.path.startswith("/api/auth/callback"):
            type(self).callback_cookie = self.headers.get("Cookie")
            type(self).callback_query = self.path.split("?", 1)[-1]
            type(self).callback_requests.append((type(self).callback_cookie, type(self).callback_query))
        if self.path == "/":
            body = b"<html><body><script>fetch('/api/auth/session').then(r=>r.json()).then(v=>document.body.textContent='login='+v.login)</script></body></html>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        connection = http.client.HTTPConnection(*type(self).backend, timeout=5)
        headers = {"Host": f"{type(self).backend[0]}:{type(self).backend[1]}"}
        if self.headers.get("Cookie"):
            headers["Cookie"] = self.headers["Cookie"]
        connection.request("GET", self.path, headers=headers)
        response = connection.getresponse()
        body = response.read()
        self.send_response(response.status)
        for name, value in response.getheaders():
            if name.casefold() == "set-cookie":
                type(self).set_cookies.append(value)
            if name.casefold() == "set-cookie" and value.startswith("flow_oauth_state=") and "Max-Age=600" in value:
                type(self).state_cookie_response = value
            if name.casefold() not in {"connection", "transfer-encoding", "content-length", "server", "date"}:
                self.send_header(name, value)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)
        connection.close()


class AuthEntryPointTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = str(Path(self.temp_dir.name) / "gateway.sqlite")
        self.github = ThreadingHTTPServer(("127.0.0.1", 0), FakeGitHubHandler)
        self.github_thread = threading.Thread(target=self.github.serve_forever, daemon=True)
        self.github_thread.start()
        self.github_origin = f"http://127.0.0.1:{self.github.server_port}"
        self.backend = None
        self.frontend = None

    def tearDown(self):
        for server in (self.frontend, self.backend, self.github):
            if server is not None:
                server.shutdown()
                server.server_close()
        self.temp_dir.cleanup()

    def make_config(self, frontend_origin: str, authorize_url: str | None = None) -> OAuthConfig:
        base = self.github_origin
        return OAuthConfig(
            client_id="test-client-id", client_secret="test-client-secret",
            session_secret="test-session-secret-with-more-than-32-bytes", frontend_origin=frontend_origin,
            database_path=self.database,
            authorize_url=authorize_url or base + "/login/oauth/authorize",
            token_url=base + "/login/oauth/access_token", user_url=base + "/user",
        )

    def test_state_is_single_use_and_mismatch_is_refused_at_http_entrypoint(self):
        server = create_server(self.make_config("https://flow.example.test"), ("127.0.0.1", 0))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            connection = http.client.HTTPConnection("127.0.0.1", server.server_port)
            connection.request("GET", "/api/auth/login", headers={"Host": "flow.example.test"})
            response = connection.getresponse()
            location = response.getheader("Location")
            state_cookie = response.getheader("Set-Cookie").split(";", 1)[0]
            self.assertEqual(response.status, 302)
            self.assertIn("SameSite=Lax", response.getheader("Set-Cookie"))
            query = parse_qs(urlsplit(location).query)
            self.assertEqual(query["redirect_uri"], ["https://flow.example.test/api/auth/callback"])

            connection.request("GET", "/api/auth/callback?" + urlencode({"state": "attacker", "code": "test-code"}),
                               headers={"Host": "flow.example.test", "Cookie": state_cookie})
            mismatch = connection.getresponse()
            self.assertEqual(mismatch.status, 400)
            self.assertEqual(json.loads(mismatch.read()), {"error": "invalid OAuth state"})

            real_state = query["state"][0]
            connection.request("GET", "/api/auth/callback?" + urlencode({"state": real_state, "code": "test-code"}),
                               headers={"Host": "flow.example.test", "Cookie": state_cookie})
            replay = connection.getresponse()
            self.assertEqual(replay.status, 302)
            replay.read()
            connection.request("GET", "/api/auth/callback?" + urlencode({"state": real_state, "code": "test-code"}),
                               headers={"Host": "flow.example.test", "Cookie": state_cookie})
            replayed = connection.getresponse()
            self.assertEqual(replayed.status, 400)
            replayed.read()
            connection.close()
        finally:
            server.shutdown()
            server.server_close()

    def test_foreign_github_user_is_refused_at_http_entrypoint(self):
        FakeGitHubHandler.login = "someone-else"
        server = create_server(self.make_config("https://flow.example.test"), ("127.0.0.1", 0))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            state = SessionStore(self.database, "test-session-secret-with-more-than-32-bytes").create_state()
            connection = http.client.HTTPConnection("127.0.0.1", server.server_port)
            cookie = f"flow_oauth_state={state}"
            connection.request("GET", "/api/auth/callback?" + urlencode({"state": state, "code": "test-code"}),
                               headers={"Host": "flow.example.test", "Cookie": cookie})
            response = connection.getresponse()
            self.assertEqual(response.status, 403)
            self.assertEqual(json.loads(response.read()), {"error": "GitHub sign-in refused"})
            with closing(sqlite3.connect(self.database)) as db:
                self.assertEqual(db.execute("SELECT COUNT(*) FROM sessions").fetchone(), (0,))
            connection.close()
        finally:
            server.shutdown()
            server.server_close()
            FakeGitHubHandler.login = "dav033"

    def test_browser_returns_through_frontend_rewrite_with_lax_state_and_strict_session(self):
        chromium = shutil.which("chromium")
        self.assertIsNotNone(chromium, "Chromium is required to verify browser SameSite behavior")
        frontend = ThreadingHTTPServer(("127.0.0.1", 0), FrontendRewriteHandler)
        frontend_thread = threading.Thread(target=frontend.serve_forever, daemon=True)
        frontend_thread.start()
        self.frontend = frontend
        frontend_port = frontend.server_port
        # Port is part of the frontend origin and is preserved by the same-origin rewrite.
        frontend_origin = f"http://app.test:{frontend_port}"
        github_browser_origin = f"http://github.test:{self.github.server_port}"
        FrontendRewriteHandler.github_browser_origin = github_browser_origin
        self.backend = create_server(self.make_config(frontend_origin, github_browser_origin + "/login/oauth/authorize"), ("127.0.0.1", 0))
        FrontendRewriteHandler.callback_requests = []
        FrontendRewriteHandler.set_cookies = []
        FrontendRewriteHandler.backend = ("127.0.0.1", self.backend.server_port)
        backend_thread = threading.Thread(target=self.backend.serve_forever, daemon=True)
        backend_thread.start()

        profile = Path(self.temp_dir.name) / "chromium-profile"
        result = subprocess.run([
            chromium, "--headless", "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
            "--disable-background-networking", "--no-first-run", "--no-default-browser-check",
            "--host-resolver-rules=MAP app.test 127.0.0.1,MAP github.test 127.0.0.1", "--unsafely-treat-insecure-origin-as-secure=" + frontend_origin,
            f"--user-data-dir={profile}", "--virtual-time-budget=2000", "--dump-dom",
            f"{frontend_origin}/api/auth/login",
        ], capture_output=True, text=True, timeout=30, check=False)
        self.assertEqual(result.returncode, 0, result.stderr[-2000:])
        self.assertIn("login=dav033", result.stdout,
                      f"callback requests={FrontendRewriteHandler.callback_requests!r}; state Set-Cookie={FrontendRewriteHandler.state_cookie_response!r}")
        callback_cookie = dict(item.split("=", 1) for item in (FrontendRewriteHandler.callback_cookie or "").split("; "))
        callback_state = parse_qs(FrontendRewriteHandler.callback_query or "")["state"][0]
        self.assertEqual(callback_cookie.get("flow_oauth_state"), callback_state)
        self.assertEqual(FakeGitHubHandler.last_authorize["redirect_uri"], [frontend_origin + "/api/auth/callback"])
        self.assertEqual(FakeGitHubHandler.last_authorize["scope"], ["read:user"])
        state_cookie = next(value for value in FrontendRewriteHandler.set_cookies if value.startswith("flow_oauth_state=") and "Max-Age=600" in value)
        session_cookie = next(value for value in FrontendRewriteHandler.set_cookies if value.startswith("flow_session="))
        self.assertIn("HttpOnly", state_cookie)
        self.assertIn("Secure", state_cookie)
        self.assertIn("SameSite=Lax", state_cookie)
        self.assertIn("HttpOnly", session_cookie)
        self.assertIn("Secure", session_cookie)
        self.assertIn("SameSite=Strict", session_cookie)

        # Browser storage must reflect a Strict session and the cross-site OAuth state must be sent on callback.
        session = SessionStore(self.database, "test-session-secret-with-more-than-32-bytes")
        with session._connect() as db:
            self.assertEqual(db.execute("SELECT login FROM sessions").fetchone(), ("dav033",))
            self.assertEqual(db.execute("SELECT COUNT(*) FROM oauth_states").fetchone(), (0,))


if __name__ == "__main__":
    unittest.main()
