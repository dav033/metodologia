from __future__ import annotations

import http.client
import io
import json
import tempfile
import threading
import unittest
from email.message import Message
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace

import panel_proxy
from auth import OAuthConfig, SESSION_COOKIE, SessionStore
from server import create_server
from upstream import LaptopClient, UpstreamError

ORIGIN = "https://flow.example.test"


class FakeResponse:
    def __init__(self, status: int, body: bytes = b"", **headers: str) -> None:
        self.status = status
        self.headers = Message()
        for name, value in headers.items():
            self.headers[name.replace("_", "-")] = value
        self._body = io.BytesIO(body)
        self.closed = False

    def read(self, size: int = -1) -> bytes:
        return self._body.read(size)

    def readline(self) -> bytes:
        return self._body.readline()

    def close(self) -> None:
        self.closed = True


class FakeLaptop:
    def __init__(self) -> None:
        self.calls: list[tuple] = []
        self.responses: list = []
        self.error: Exception | None = None

    def open_panel(self, method, path, body=None, content_type=None, timeout=30.0):
        self.calls.append((method, path, body, content_type))
        if self.error:
            raise self.error
        return self.responses.pop(0)


class PanelProxyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        database = str(Path(self.temp.name) / "gateway.sqlite")
        secret = "test-session-secret-with-more-than-32-bytes"
        self.laptop = FakeLaptop()
        runtime = SimpleNamespace(laptop=self.laptop)
        self.server = create_server(OAuthConfig(client_id="c", client_secret="s", session_secret=secret,
                                                frontend_origin=ORIGIN, database_path=database),
                                    ("127.0.0.1", 0), runtime=runtime)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.store = SessionStore(database, secret)
        self.cookie = {"Cookie": f"{SESSION_COOKIE}={self.store.create_session('dav033')}"}

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.temp.cleanup()

    def call(self, method: str, path: str, headers: dict | None = None, body: bytes | None = None):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        conn.request(method, path, body=body, headers=headers or {})
        resp = conn.getresponse()
        data = resp.read()
        result = resp.status, resp, data
        conn.close()
        return result

    def post_headers(self, **extra: str) -> dict:
        return {**self.cookie, "Origin": ORIGIN, "X-Flow-Request": "1",
                "Content-Type": "application/x-www-form-urlencoded", **extra}

    # ------------------------------------------------------------------ reads
    def test_anonymous_readers_are_sent_to_login_or_refused(self) -> None:
        status, resp, _ = self.call("GET", "/p/demo", {"Accept": "text/html"})
        self.assertEqual((status, resp.getheader("Location")), (302, "/api/auth/login"))
        status, _, body = self.call("GET", "/api/flow")
        self.assertEqual((status, json.loads(body)), (401, {"error": "unauthorized"}))
        self.assertEqual(self.laptop.calls, [])

    def test_unrelated_paths_stay_404_even_with_a_session(self) -> None:
        for path in ("/admin", "/api/other", "/.env", "/api/remote/v1/unknown"):
            with self.subTest(path=path):
                self.assertEqual(self.call("GET", path, self.cookie)[0], 404)
        self.assertEqual(self.call("GET", "/api/auth/session", self.cookie)[0], 200)

    def test_page_is_relayed_with_shim_redaction_and_safe_headers(self) -> None:
        token = "123456789:" + "A" * 35
        html = (f"<html><head><title>x</title></head><body>token {token} "
                "TELEGRAM_BOT_TOKEN=abc123 <input name=token value=keepme></body></html>").encode()
        self.laptop.responses.append(FakeResponse(200, html, Content_Type="text/html; charset=utf-8"))
        status, resp, body = self.call("GET", "/p/demo?tab=docs", self.cookie)
        text = body.decode()
        self.assertEqual(status, 200)
        self.assertEqual(self.laptop.calls[0][:2], ("GET", "/p/demo?tab=docs"))
        self.assertIn(panel_proxy.SHIM_PATH, text)
        self.assertNotIn(token, text)
        self.assertNotIn("abc123", text)
        self.assertIn("value=keepme", text)
        self.assertEqual(resp.getheader("X-Content-Type-Options"), "nosniff")
        self.assertEqual(resp.getheader("Cache-Control"), "no-store")
        self.assertEqual(resp.getheader("X-Frame-Options"), "SAMEORIGIN")

    def test_root_alias_maps_to_the_panel_dashboard(self) -> None:
        self.laptop.responses.append(FakeResponse(200, b"<head></head>", Content_Type="text/html"))
        self.assertEqual(self.call("GET", "/__panel_root", self.cookie)[0], 200)
        self.assertEqual(self.laptop.calls[0][1], "/")

    def test_artifact_with_its_own_csp_gets_no_shim(self) -> None:
        csp = "sandbox allow-scripts; default-src 'none'"
        self.laptop.responses.append(FakeResponse(200, b"<html><head></head></html>", Content_Type="text/html",
                                                  Content_Security_Policy=csp))
        status, resp, body = self.call("GET", "/p/demo/view/a.html", self.cookie)
        self.assertEqual(status, 200)
        self.assertEqual(resp.getheader("Content-Security-Policy"), csp)
        self.assertNotIn(panel_proxy.SHIM_PATH.encode(), body)

    def test_laptop_offline_is_reported_without_a_stack(self) -> None:
        self.laptop.error = UpstreamError("down")
        status, _, body = self.call("GET", "/now", self.cookie)
        self.assertEqual((status, json.loads(body)), (503, {"code": "LAPTOP_OFFLINE"}))

    def test_event_stream_is_passed_through(self) -> None:
        stream = b"event: tick\ndata: {\"n\":1}\n\n: keepalive\n\n"
        self.laptop.responses.append(FakeResponse(200, stream, Content_Type="text/event-stream"))
        status, resp, body = self.call("GET", "/live?scope=global", self.cookie)
        self.assertEqual(status, 200)
        self.assertEqual(body, stream)
        self.assertTrue(resp.getheader("Content-Type").startswith("text/event-stream"))

    def test_shim_is_public_static_javascript(self) -> None:
        status, resp, body = self.call("GET", panel_proxy.SHIM_PATH)
        self.assertEqual(status, 200)
        self.assertIn("javascript", resp.getheader("Content-Type"))
        self.assertIn(b"X-Flow-Challenge", body)

    # ------------------------------------------------------------------ writes
    def test_post_needs_header_origin_and_session(self) -> None:
        path = "/p/demo/req/REQ-001/run"
        self.assertEqual(self.call("POST", path, {**self.cookie, "Origin": ORIGIN}, b"a=1")[0], 403)
        self.assertEqual(self.call("POST", path, {**self.post_headers(), "Origin": "https://evil.example"}, b"a=1")[0],
                         403)
        headers = self.post_headers()
        headers.pop("Cookie")
        self.assertEqual(self.call("POST", path, headers, b"a=1")[0], 401)
        self.assertEqual(self.laptop.calls, [])

    def test_post_needs_a_typed_confirmation_bound_to_the_exact_request(self) -> None:
        path, body = "/p/demo/req/REQ-001/run", b"action=stop&token=t"
        status, _, raw = self.call("POST", path, self.post_headers(), body)
        challenge = json.loads(raw)
        self.assertEqual((status, challenge["code"], challenge["action"]), (428, "CONFIRMATION_REQUIRED", path))
        self.assertEqual(self.laptop.calls, [])
        # wrong typed text, a different body or another URL do not pass and burn nothing they should not
        wrong = self.post_headers(**{"X-Flow-Challenge": challenge["challenge"], "X-Flow-Typed": "si"})
        self.assertEqual(self.call("POST", path, wrong, body)[0], 428)
        again = json.loads(self.call("POST", path, self.post_headers(), body)[2])["challenge"]
        ok_headers = self.post_headers(**{"X-Flow-Challenge": again, "X-Flow-Typed": panel_proxy.CONFIRM_TEXT})
        self.assertEqual(self.call("POST", path, ok_headers, b"action=resume&token=t")[0], 428)
        again = json.loads(self.call("POST", path, self.post_headers(), body)[2])["challenge"]
        ok_headers = self.post_headers(**{"X-Flow-Challenge": again, "X-Flow-Typed": panel_proxy.CONFIRM_TEXT})
        self.laptop.responses.append(FakeResponse(303, b"", Location="/p/demo/req/REQ-001?tab=run&msg=ok"))
        status, resp, _ = self.call("POST", path, ok_headers, body)
        self.assertEqual((status, resp.getheader("Location")), (303, "/p/demo/req/REQ-001?tab=run&msg=ok"))
        self.assertEqual(self.laptop.calls, [("POST", path, body, "application/x-www-form-urlencoded")])
        # single use
        self.assertEqual(self.call("POST", path, ok_headers, body)[0], 428)
        self.assertEqual(len(self.laptop.calls), 1)

    def test_challenges_are_bound_to_the_session(self) -> None:
        path, body = "/api/flow/decision", b"x=1"
        ident = json.loads(self.call("POST", path, self.post_headers(), body)[2])["challenge"]
        other = {"Cookie": f"{SESSION_COOKIE}={self.store.create_session('dav033')}", "Origin": ORIGIN,
                 "X-Flow-Request": "1", "X-Flow-Challenge": ident, "X-Flow-Typed": panel_proxy.CONFIRM_TEXT}
        self.assertEqual(self.call("POST", path, other, body)[0], 428)

    def test_post_to_an_unlisted_path_is_404_and_oversized_body_is_refused(self) -> None:
        self.assertEqual(self.call("POST", "/admin", self.post_headers(), b"a=1")[0], 404)
        big = self.post_headers()
        self.assertEqual(self.call("POST", "/api/flow/decision", big, b"x" * (panel_proxy.MAX_REQUEST_BODY + 1))[0], 413)


class RedactionTests(unittest.TestCase):
    def test_known_secret_shapes_are_removed_and_ordinary_text_is_kept(self) -> None:
        aws_key = "AKIA" + "ABCDEFGHIJKLMNOP"
        text = ("bot 123456789:" + "A" * 35 + " gh " + "ghp_" + "a" * 36 + " key " + aws_key + "\n"
                "-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----\nSESSION_SECRET=deadbeef FOO=bar total_tokens 12")
        result = panel_proxy.redact(text)
        for leaked in ("AAAAAAAA", "ghp_", aws_key, "abc\n", "deadbeef"):
            self.assertNotIn(leaked, result)
        self.assertIn("FOO=bar", result)
        self.assertIn("total_tokens 12", result)

    def test_upstream_path_covers_panel_urls_only(self) -> None:
        for path in ("/", "/__panel_root", "/p/x", "/flow", "/api/now", "/api/flow/agent", "/static/a.js", "/live"):
            self.assertIsNotNone(panel_proxy.upstream_path(path), path)
        for path in ("/api/auth/login", "/api/remote/v1/snapshot", "/healthz", "/admin", "/api"):
            self.assertIsNone(panel_proxy.upstream_path(path), path)


class NoRedirectTests(unittest.TestCase):
    def test_laptop_client_hands_redirects_to_the_browser(self) -> None:
        seen = {}

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                seen["auth"] = self.headers.get("Authorization")
                seen["body"] = self.rfile.read(int(self.headers["Content-Length"]))
                self.send_response(303)
                self.send_header("Location", "/p/x?msg=1")
                self.end_headers()

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            client = LaptopClient(f"http://127.0.0.1:{server.server_port}", "k")
            response = client.open_panel("POST", "/p/x/req/R/run", b"a=1", "application/x-www-form-urlencoded")
            self.assertEqual((response.code, response.headers["Location"]), (303, "/p/x?msg=1"))
            self.assertEqual((seen["auth"], seen["body"]), ("Bearer k", b"a=1"))
            with self.assertRaises(ValueError):
                client.open_panel("DELETE", "/p/x")
            with self.assertRaises(UpstreamError):
                LaptopClient("http://127.0.0.1:9", "k").open_panel("GET", "/p/x", timeout=1)
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
