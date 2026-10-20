from __future__ import annotations

import http.client
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
WEB = ROOT / "remote" / "web"
sys.path.insert(0, str(ROOT / "skill" / "scripts"))
sys.path.insert(0, str(ROOT / "remote" / "gateway"))

import bt_live_api
import bt_flow_bus
import bt_server
import notifications
from app import create_runtime
from auth import OAuthConfig
from config import GatewayConfig
from server import create_server as create_gateway_server


def free_port() -> int:
    with closing(socket.socket()) as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


class FakeGitHubHandler(BaseHTTPRequestHandler):
    login = "dav033"
    frontend_origin = ""

    def log_message(self, *_args) -> None:
        pass

    def do_GET(self) -> None:
        if self.path.startswith("/login/oauth/authorize"):
            query = parse_qs(urlsplit(self.path).query)
            callback = query["redirect_uri"][0] + "?" + urlencode({"code": "fixture-code", "state": query["state"][0]})
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

    def do_POST(self) -> None:
        body = b'{"access_token":"fixture-token","token_type":"bearer"}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class FakeTelegramHandler(BaseHTTPRequestHandler):
    messages: list[dict[str, object]] = []

    def log_message(self, *_args) -> None:
        pass

    def do_POST(self) -> None:
        payload = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
        type(self).messages.append(payload)
        body = b'{"ok":true,"result":{}}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class LocalRemoteEndToEndTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.gateway_port = free_port()
        install = subprocess.run(["npm", "ci", "--offline"], cwd=WEB, capture_output=True, text=True, timeout=180)
        if install.returncode:
            raise RuntimeError(f"offline web dependency install failed: {install.stderr[-2000:]}")
        build_env = {**os.environ, "FLOW_GATEWAY_ORIGIN": f"http://127.0.0.1:{cls.gateway_port}"}
        build = subprocess.run(["npm", "run", "build"], cwd=WEB, env=build_env,
                               capture_output=True, text=True, timeout=240)
        if build.returncode:
            raise RuntimeError(f"built web failed: {build.stdout[-3000:]}\n{build.stderr[-3000:]}")

    @classmethod
    def tearDownClass(cls) -> None:
        browser = subprocess.run(["node", "--test", "tests/panel-browser.test.mjs"], cwd=WEB,
                                 capture_output=True, text=True, timeout=180)
        if browser.returncode:
            raise RuntimeError(f"open-panel browser test failed: {browser.stdout[-3000:]}\n{browser.stderr[-3000:]}")

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self._cleanup)
        self.database = Path(self.temporary.name) / "gateway.sqlite"
        self.web_port = free_port()
        self.frontend_origin = f"http://127.0.0.1:{self.web_port}"
        self.github = ThreadingHTTPServer(("127.0.0.1", 0), FakeGitHubHandler)
        self.github_thread = threading.Thread(target=self.github.serve_forever, daemon=True)
        self.github_thread.start()
        self.telegram = ThreadingHTTPServer(("127.0.0.1", 0), FakeTelegramHandler)
        self.telegram_thread = threading.Thread(target=self.telegram.serve_forever, daemon=True)
        self.telegram_thread.start()
        github_origin = f"http://127.0.0.1:{self.github.server_port}"
        FakeGitHubHandler.login = "dav033"
        FakeTelegramHandler.messages = []
        self.config = GatewayConfig(
            laptop_origin=f"http://127.0.0.1:{free_port()}", gateway_key="fixture-gateway-key",
            telegram_bot_token="fixture-bot-token", telegram_chat_id="fixture-chat",
            database_path=self.database, bind_port=self.gateway_port, request_timeout=1, probe_interval=0.1,
        )
        self.oauth = OAuthConfig(
            client_id="fixture-client", client_secret="fixture-client-secret",
            session_secret="fixture-session-secret-longer-than-32-bytes", frontend_origin=self.frontend_origin,
            database_path=str(self.database), authorize_url=github_origin + "/login/oauth/authorize",
            token_url=github_origin + "/login/oauth/access_token", user_url=github_origin + "/user",
        )
        self.runs = [{"project": "demo", "req": "REQ-001", "state": "running",
                      "tasks": [{"id": "T1", "state": "running"}], "updatedAt": "v1"}]
        self.flow_rows = bt_flow_bus.audit_events("demo/REQ-001", [{
            "seq": 1, "at": 1792497600.0, "kind": "attempt_transition", "task_id": "T1",
            "attempt_id": "attempt-1", "detail": json.dumps({"from": "dispatched", "to": "running", "source": "executor"}),
        }], bt_flow_bus.Ctx(None, "demo/REQ-001"))
        self.patches = [
            patch.dict(os.environ, {"FLOW_GATEWAY_KEY": "fixture-gateway-key"}),
            patch("bt_remote_api._snapshot_runs", side_effect=lambda: json.loads(json.dumps(self.runs))),
            patch("bt_remote_api._plans", return_value=[]),
            patch("bt_live_api.flow_events", side_effect=lambda *_args, **_kwargs: (self.flow_rows, [], {})),
        ]
        for active_patch in self.patches:
            active_patch.start()
        self.laptop_server = ThreadingHTTPServer(("127.0.0.1", 0), bt_server.RemoteHandler)
        self.config = GatewayConfig(
            laptop_origin=f"http://127.0.0.1:{self.laptop_server.server_port}", gateway_key="fixture-gateway-key",
            telegram_bot_token="fixture-bot-token", telegram_chat_id="fixture-chat",
            database_path=self.database, bind_port=self.gateway_port, request_timeout=1, probe_interval=0.1,
        )
        self.laptop_thread = threading.Thread(target=self.laptop_server.serve_forever, daemon=True)
        self.laptop_thread.start()
        self.runtime = create_runtime(self.config)
        self.gateway_server = create_gateway_server(self.oauth, ("127.0.0.1", self.gateway_port), runtime=self.runtime)
        self.gateway_thread = threading.Thread(target=self.gateway_server.serve_forever, daemon=True)
        self.gateway_thread.start()
        self.poll_stop = threading.Event()
        self.poll_thread = threading.Thread(target=self._poll, daemon=True)
        self.poll_thread.start()
        web_env = {**os.environ, "PORT": str(self.web_port), "HOSTNAME": "127.0.0.1",
                   "FLOW_GATEWAY_ORIGIN": f"http://127.0.0.1:{self.gateway_port}"}
        self.web_process = subprocess.Popen(["npm", "run", "start", "--", "--hostname", "127.0.0.1", "--port", str(self.web_port)],
                                            cwd=WEB, env=web_env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self._wait_http(self.frontend_origin + "/", timeout=20)

    def _poll(self) -> None:
        while not self.poll_stop.is_set():
            self.runtime.poll_once()
            self.poll_stop.wait(self.config.probe_interval)

    def _cleanup(self) -> None:
        self.poll_stop.set()
        if hasattr(self, "poll_thread"):
            self.poll_thread.join(timeout=2)
        for server in (getattr(self, "gateway_server", None), getattr(self, "laptop_server", None),
                       getattr(self, "github", None), getattr(self, "telegram", None)):
            if server is not None:
                server.shutdown()
                server.server_close()
        process = getattr(self, "web_process", None)
        if process is not None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        if hasattr(self, "runtime"):
            self.runtime.outbox._db.close()
        for active_patch in reversed(getattr(self, "patches", [])):
            active_patch.stop()
        self.temporary.cleanup()

    @staticmethod
    def _wait_http(url: str, timeout: float) -> None:
        deadline = time.monotonic() + timeout
        last_error = None
        while time.monotonic() < deadline:
            try:
                response = http_get(url)
                if response[0] < 500:
                    return
            except OSError as exc:
                last_error = exc
            time.sleep(0.1)
        raise AssertionError(f"HTTP endpoint did not become ready: {url} ({last_error})")

    def _request(self, origin: str, path: str, *, cookie: str | None = None) -> tuple[int, dict[str, str], bytes]:
        parsed = urlsplit(origin)
        connection = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=5)
        headers = {"Host": parsed.netloc}
        if cookie:
            headers["Cookie"] = cookie
        connection.request("GET", path, headers=headers)
        response = connection.getresponse()
        response_headers: dict[str, str] = {}
        for name, value in response.getheaders():
            key = name.lower()
            response_headers[key] = response_headers[key] + "\n" + value if key == "set-cookie" and key in response_headers else value
        result = (response.status, response_headers, response.read())
        connection.close()
        return result

    def _sign_in(self) -> str:
        status, headers, _ = self._request(self.frontend_origin, "/api/auth/login")
        self.assertEqual(status, 302)
        state_cookie = headers["set-cookie"].split(";", 1)[0]
        authorize = urlsplit(headers["location"])
        status, gh_headers, _ = self._request(f"{authorize.scheme}://{authorize.netloc}", authorize.path + "?" + authorize.query)
        self.assertEqual(status, 302)
        callback = urlsplit(gh_headers["location"])
        status, callback_headers, _ = self._request(self.frontend_origin, callback.path + "?" + callback.query,
                                                     cookie=state_cookie)
        return callback_headers.get("set-cookie", "") if status == 302 else ""

    def test_local_stack_auth_live_state_offline_and_telegram(self) -> None:
        page_status, _, page = self._request(self.frontend_origin, "/")
        self.assertEqual(page_status, 200)
        self.assertIn(b"Flow Remote", page)

        session_cookie = self._sign_in().split(";", 1)[0]
        self.assertTrue(session_cookie.startswith("flow_session="))
        session_status, _, session_body = self._request(self.frontend_origin, "/api/auth/session", cookie=session_cookie)
        self.assertEqual(session_status, 200)
        self.assertTrue(json.loads(session_body)["authenticated"])

        snapshot_status, _, snapshot_body = self._request(self.frontend_origin, "/api/remote/v1/snapshot", cookie=session_cookie)
        self.assertEqual(snapshot_status, 200)
        first_snapshot = json.loads(snapshot_body)
        self.assertTrue(first_snapshot["laptop"]["online"])
        self.assertEqual(first_snapshot["runs"][0]["state"], "running")

        self.runs[0] = {**self.runs[0], "state": "running", "tasks": [{"id": "T1", "state": "failed"}], "updatedAt": "v2"}
        changed = self._wait_snapshot(session_cookie, lambda value: value["runs"][0]["tasks"][0]["state"] == "failed", 5)
        self.assertEqual(changed["runs"][0]["updatedAt"], "v2")
        projected = self._wait_for_event("task.progress", timeout=5)
        self.assertEqual(projected["target"], {"project": "demo", "req": "REQ-001", "taskId": "T1", "attemptId": "attempt-1"})

        FakeGitHubHandler.login = "foreign-user"
        foreign_state, foreign_headers, _ = self._request(self.frontend_origin, "/api/auth/login")
        self.assertEqual(foreign_state, 302)
        foreign_cookie = foreign_headers["set-cookie"].split(";", 1)[0]
        authorize = urlsplit(foreign_headers["location"])
        _, gh_headers, _ = self._request(f"{authorize.scheme}://{authorize.netloc}", authorize.path + "?" + authorize.query)
        callback = urlsplit(gh_headers["location"])
        foreign_status, _, _ = self._request(self.frontend_origin, callback.path + "?" + callback.query, cookie=foreign_cookie)
        self.assertEqual(foreign_status, 403)
        FakeGitHubHandler.login = "dav033"

        failure = bt_flow_bus.audit_events("demo/REQ-001", [{
            "seq": 2, "at": 1792497601.0, "kind": "attempt_transition", "task_id": "T1",
            "attempt_id": "attempt-1", "detail": json.dumps({"from": "running", "to": "failed", "source": "executor"}),
        }], bt_flow_bus.Ctx(None, "demo/REQ-001"))[0]
        original_urlopen = notifications.urlopen

        def route_telegram(request, timeout=5):
            local = f"http://127.0.0.1:{self.telegram.server_port}/sendMessage"
            rewritten = __import__("urllib.request", fromlist=["Request"]).Request(
                local, data=request.data, headers=dict(request.header_items()), method=request.method,
            )
            return original_urlopen(rewritten, timeout=timeout)

        with patch.object(notifications, "urlopen", side_effect=route_telegram):
            self.flow_rows.append(failure)
            self._wait_for_telegram(1, timeout=5)
            time.sleep(0.3)
        self.assertEqual(len(FakeTelegramHandler.messages), 1)
        self.assertEqual(FakeTelegramHandler.messages[0]["chat_id"], "fixture-chat")
        failed_event = self._wait_for_event("attempt.failed", timeout=5)
        self.assertEqual(failed_event["target"]["taskId"], "T1")

        self.runs[0] = {**self.runs[0], "state": "finished", "tasks": [{"id": "T1", "state": "completed"}], "updatedAt": "v3"}
        completed = self._wait_snapshot(session_cookie, lambda value: value["runs"][0]["state"] == "finished", 5)
        self.assertEqual(completed["runs"][0]["tasks"][0]["state"], "completed")

        self.laptop_server.shutdown()
        self.laptop_server.server_close()
        self._wait_snapshot(session_cookie, lambda value: value.get("laptop", {}).get("online") is False, 20)

    def _wait_snapshot(self, cookie: str, predicate, timeout: float) -> dict[str, object]:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            status, _, body = self._request(self.frontend_origin, "/api/remote/v1/snapshot", cookie=cookie)
            if status == 200:
                snapshot = json.loads(body)
                if predicate(snapshot):
                    return snapshot
            time.sleep(0.1)
        self.fail("snapshot did not reach the requested state before its deadline")

    def _wait_for_event(self, event_type: str, timeout: float) -> dict[str, object]:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            events = self.runtime.stream.after("0")
            matching = [event for _, event in events if event.get("type") == event_type]
            if matching:
                return matching[-1]
            time.sleep(0.1)
        self.fail(f"gateway did not publish {event_type} from the laptop API")

    def _wait_for_telegram(self, count: int, timeout: float) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if len(FakeTelegramHandler.messages) >= count:
                return
            time.sleep(0.1)
        self.fail("forced failure did not reach the fake Telegram before its deadline")


def http_get(url: str) -> tuple[int, bytes]:
    parsed = urlsplit(url)
    connection = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=1)
    connection.request("GET", parsed.path or "/")
    response = connection.getresponse()
    result = (response.status, response.read())
    connection.close()
    return result


if __name__ == "__main__":
    unittest.main()
