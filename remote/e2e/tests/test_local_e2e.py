from __future__ import annotations

import http.client
import hashlib
import json
import os
import socket
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import shutil
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import ClassVar
from unittest.mock import patch
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import Request, urlopen as real_urlopen


REPO = Path(__file__).resolve().parents[3]
SCRIPTS = REPO / "skill" / "scripts"
WEB = REPO / "remote" / "web"
GATEWAY = REPO / "remote" / "gateway"
GATEWAY_KEY = "e2e-gateway-key-for-local-tests-only"
SESSION_SECRET = "e2e-session-secret-with-more-than-32-bytes"


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


class FakeProviderHandler(BaseHTTPRequestHandler):
    telegram_messages: ClassVar[list[dict]] = []

    def log_message(self, *_args):
        pass

    def _reply(self, status: int, body: bytes = b"", headers: tuple[tuple[str, str], ...] = ()) -> None:
        self.send_response(status)
        self.send_header("Content-Length", str(len(body)))
        for name, value in headers:
            self.send_header(name, value)
        self.end_headers()
        if body:
            self.wfile.write(body)

    def do_GET(self):
        route = urlsplit(self.path)
        query = parse_qs(route.query)
        if route.path == "/login/oauth/authorize":
            login = query.get("login", ["dav033"])[0]
            callback = query["redirect_uri"][0] + "?" + urlencode({"code": login, "state": query["state"][0]})
            return self._reply(302, headers=(("Location", callback),))
        if route.path == "/user":
            login = self.headers.get("Authorization", "").removeprefix("Bearer ")
            body = json.dumps({"login": login}).encode()
            return self._reply(200, body, (("Content-Type", "application/json"),))
        if route.path == "/telegram/sendMessage":
            return self._reply(404)
        self._reply(404)

    def do_POST(self):
        route = urlsplit(self.path)
        if route.path == "/login/oauth/access_token":
            form = parse_qs(self.rfile.read(int(self.headers.get("Content-Length", "0"))).decode())
            body = json.dumps({"access_token": form.get("code", [""])[0]}).encode()
            return self._reply(200, body, (("Content-Type", "application/json"),))
        if route.path == "/telegram/sendMessage":
            payload = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
            type(self).telegram_messages.append(payload)
            return self._reply(200, b'{"ok":true}', (("Content-Type", "application/json"),))
        self._reply(404)


class LocalEndToEndTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="flow-remote-e2e-")
        cls.root = Path(cls.temp.name) / "bitacora"
        cls.root.mkdir()
        cls.gateway_port = free_port()
        cls.laptop_port = free_port()
        cls.web_port = free_port()
        cls.provider = ThreadingHTTPServer(("127.0.0.1", 0), FakeProviderHandler)
        cls.provider_port = cls.provider.server_address[1]
        cls.provider_thread = threading.Thread(target=cls.provider.serve_forever, daemon=True)
        cls.provider_thread.start()
        FakeProviderHandler.telegram_messages.clear()
        cls._seed_retry_event_fixture()
        cls._seed_cancel_run_fixture()
        cls._build_web()
        cls._start_laptop_api()
        cls._start_gateway()
        cls._start_web()

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "web_process"):
            cls._stop_process(cls.web_process)
        if hasattr(cls, "gateway_stop"):
            cls.gateway_stop.set()
            cls.gateway_thread.join(timeout=5)
        if hasattr(cls, "laptop_process"):
            cls._stop_process(cls.laptop_process)
        if hasattr(cls, "provider"):
            cls.provider.shutdown()
            cls.provider.server_close()
            cls.provider_thread.join(timeout=3)
        if hasattr(cls, "temporary_gateway_db"):
            cls.temporary_gateway_db.cleanup()
        cls.temp.cleanup()

    @classmethod
    def _seed_retry_event_fixture(cls):
        """Create a failed attempt through M1 so the real remote event feed can observe it."""
        req = cls.root / "demo" / "requirements" / "REQ-001-forced-failure"
        req.mkdir(parents=True)
        (req / "PLAN.md").write_text("---\nstatus: approved\n---\n# Plan — Forced failure fixture\n", encoding="utf-8")

        plan = {
            "schema_version": "1.0.0", "plan_id": "REQ-001", "revision": 1,
            "tasks": [{
                "id": "T1", "milestone_id": "M1", "after": [], "shared_resources": [],
                "expected_paths": ["fixture/**"], "acceptance_criteria": ["forced failure is reported"],
                "verification": [{"type": "command", "value": "true"}], "repository": "demo",
            }],
        }
        plan_text = json.dumps(plan, separators=(",", ":"))
        plan_path = req / "plan-revisions" / "PLAN.r1.json"
        plan_path.parent.mkdir(parents=True)
        plan_path.write_text(plan_text, encoding="utf-8")
        plan_hash = hashlib.sha256(plan_text.encode()).hexdigest()
        (plan_path.parent / "MANIFEST.json").write_text(json.dumps({
            "schema": 1, "revisions": [{
                "revision": 1, "sha256": plan_hash, "frozen_at": "2026-10-20T00:00:00Z",
            }],
        }), encoding="utf-8")
        (req / "PLAN.json").write_text(plan_text, encoding="utf-8")

        seed_script = """
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import bt_scheduler_adapter as adapter
import bt_scheduler_core as core
rdir = Path(sys.argv[2])
scheduler = adapter.open_scheduler(
    rdir, ports=core.Ports(execution=core.FakeExecutor()),
    config=core.Config(max_parallel_tasks=1, max_attempts=3),
)
scheduler.step()
scheduler.step()
for attempt_number in range(3):
    attempt_id = scheduler.snapshot().tasks["T1"]["attempt"]
    token = scheduler.read(lambda ctx: ctx.state.attempts[attempt_id].token)
    started = scheduler.ingest(core.Event(
        f"fixture-execution-started-{attempt_number}", "REQ-001", 1, "T1", attempt_id, "executor",
        "execution_started", token=token,
    ))
    assert started.status == "applied", started
    result = scheduler.ingest(core.Event(
        f"fixture-forced-failure-{attempt_number}", "REQ-001", 1, "T1", attempt_id, "executor",
        "execution_failed", payload={"reason": "fixture failure"}, token=token,
    ))
    assert result.status == "applied", result
    if attempt_number < 2:
        scheduler.step()
adapter.write_projection(rdir, scheduler)
"""
        subprocess.run([sys.executable, "-c", seed_script, str(SCRIPTS), str(req)],
                       env={**os.environ, "BITACORA_ROOT": str(cls.root)}, check=True, timeout=30)

        state = cls.root / ".state" / "scheduler"
        m1 = state / "demo-REQ-001.db"
        runtime_id = "a" * 32
        m1.with_name(m1.stem + "-runtime.json").write_text(json.dumps({"runtime_id": runtime_id}), encoding="utf-8")
        modules = m1.parent / f"{m1.stem}-{runtime_id}-modules"
        modules.mkdir()
        m5 = sqlite3.connect(modules / "m5-recovery.sqlite3")
        m5.execute("CREATE TABLE decisions (seq INTEGER PRIMARY KEY, task_id TEXT, attempt_id TEXT, cause TEXT, action TEXT)")
        m5.execute("INSERT INTO decisions VALUES (1, 'T1', 'attempt-forced-failure', 'fixture failure', 'retry')")
        m5.commit()
        m5.close()

    @classmethod
    def _seed_cancel_run_fixture(cls):
        """Create a second run through M1's SQLite repository for command-path cancel coverage."""
        req = cls.root / "demo" / "requirements" / "REQ-002-cancel-fixture"
        req.mkdir(parents=True)
        plan = {
            "schema_version": "1.0.0", "plan_id": "REQ-002", "revision": 1,
            "tasks": [{
                "id": "T1", "milestone_id": "M1", "after": [], "shared_resources": [],
                "expected_paths": ["fixture/**"], "acceptance_criteria": ["cancel fixture"],
                "verification": [{"type": "command", "value": "true"}], "repository": "demo",
            }],
        }
        plan_text = json.dumps(plan, separators=(",", ":"))
        plan_path = req / "plan-revisions" / "PLAN.r1.json"
        plan_path.parent.mkdir()
        plan_path.write_text(plan_text, encoding="utf-8")
        plan_hash = hashlib.sha256(plan_text.encode()).hexdigest()
        (plan_path.parent / "MANIFEST.json").write_text(json.dumps({
            "schema": 1, "revisions": [{
                "revision": 1, "sha256": plan_hash, "frozen_at": "2026-10-20T00:00:00Z",
            }],
        }), encoding="utf-8")
        (req / "PLAN.md").write_text(
            "---\nstatus: approved\n---\n# Plan — Cancel fixture\n", encoding="utf-8")
        (req / "PLAN.json").write_text(plan_text, encoding="utf-8")

        seed_script = """
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import bt_scheduler_adapter as adapter
import bt_scheduler_core as core
rdir = Path(sys.argv[2])
scheduler = adapter.open_scheduler(
    rdir, ports=core.Ports(execution=core.FakeExecutor()),
    config=core.Config(max_parallel_tasks=1),
)
scheduler.step()
scheduler.step()
snapshot = scheduler.snapshot()
attempt_id = snapshot.tasks["T1"]["attempt"]
token = scheduler.read(lambda ctx: ctx.state.attempts[attempt_id].token)
started = scheduler.ingest(core.Event(
    "fixture-execution-started", "REQ-002", 1, "T1", attempt_id, "executor",
    "execution_started", token=token,
))
assert started.status == "applied", started
adapter.write_projection(rdir, scheduler)
"""
        subprocess.run([sys.executable, "-c", seed_script, str(SCRIPTS), str(req)],
                       env={**os.environ, "BITACORA_ROOT": str(cls.root)}, check=True, timeout=30)

    @classmethod
    def _build_web(cls):
        if not (WEB / "node_modules" / ".bin" / "next").exists():
            subprocess.run([shutil.which("npm") or "npm", "ci", "--offline"], cwd=WEB, check=True, timeout=180)
        environment = {**os.environ, "FLOW_GATEWAY_ORIGIN": f"http://127.0.0.1:{cls.gateway_port}"}
        subprocess.run(["npm", "run", "build"], cwd=WEB, env=environment, check=True, timeout=240)

    @classmethod
    def _start_laptop_api(cls):
        environment = {**os.environ, "BITACORA_ROOT": str(cls.root), "FLOW_GATEWAY_KEY": GATEWAY_KEY}
        cls.laptop_process = subprocess.Popen(
            [sys.executable, str(SCRIPTS / "bitacora.py"), "serve-remote", "--port", str(cls.laptop_port)],
            cwd=SCRIPTS, env=environment, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        cls._wait_port(cls.laptop_port, cls.laptop_process, "laptop API")

    @classmethod
    def _start_gateway(cls):
        provider_origin = f"http://127.0.0.1:{cls.provider_port}"
        cls.gateway_environment = {
            "LAPTOP_ORIGIN": f"http://127.0.0.1:{cls.laptop_port}",
            "FLOW_GATEWAY_KEY": GATEWAY_KEY,
            "TELEGRAM_BOT_TOKEN": "fake-token",
            "TELEGRAM_CHAT_ID": "fake-chat",
            "GATEWAY_DATABASE": str(Path(cls.temp.name) / "gateway.sqlite"),
            "GATEWAY_BIND": "127.0.0.1",
            "GATEWAY_PORT": str(cls.gateway_port),
            "UPSTREAM_TIMEOUT": "0.5",
            "PROBE_INTERVAL": "0.2",
            "GITHUB_CLIENT_ID": "fake-client",
            "GITHUB_CLIENT_SECRET": "fake-secret",
            "SESSION_SECRET": SESSION_SECRET,
            "FLOW_FRONTEND_ORIGIN": f"http://127.0.0.1:{cls.web_port}",
            "GITHUB_AUTHORIZE_URL": provider_origin + "/login/oauth/authorize",
            "GITHUB_TOKEN_URL": provider_origin + "/login/oauth/access_token",
            "GITHUB_USER_URL": provider_origin + "/user",
        }
        cls.gateway_stop = threading.Event()
        cls.gateway_runtimes = []
        def poll_until_stopped(runtime):
            cls.gateway_runtimes.append(runtime)
            while not cls.gateway_stop.is_set():
                runtime.poll_once()
                cls.gateway_stop.wait(0.2)

        def fake_telegram_open(request, timeout):
            target = Request(
                provider_origin + "/telegram/sendMessage", data=request.data,
                headers={"Content-Type": "application/json"}, method="POST",
            )
            return real_urlopen(target, timeout=timeout)

        def run_gateway():
            sys.path.insert(0, str(GATEWAY))
            import app as gateway_app
            import main as gateway_main
            import notifications
            with patch.object(gateway_app.GatewayRuntime, "run_forever", poll_until_stopped), \
                    patch.object(notifications, "urlopen", fake_telegram_open), \
                    patch.object(gateway_main.TelegramBot, "run_forever", lambda _bot: None):
                gateway_main.main()

        cls.gateway_thread = threading.Thread(target=run_gateway, daemon=True)
        with patch.dict(os.environ, cls.gateway_environment, clear=True):
            cls.gateway_thread.start()
            cls._wait_port(cls.gateway_port, None, "gateway")

    @classmethod
    def _start_web(cls):
        environment = {**os.environ, "FLOW_GATEWAY_ORIGIN": f"http://127.0.0.1:{cls.gateway_port}"}
        cls.web_process = subprocess.Popen(
            [shutil.which("npm") or "npm", "start", "--", "--hostname", "127.0.0.1", "--port", str(cls.web_port)],
            cwd=WEB, env=environment, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        cls._wait_port(cls.web_port, cls.web_process, "built web")

    @staticmethod
    def _wait_port(port: int, process: subprocess.Popen | None, name: str):
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            if process is not None and process.poll() is not None:
                raise AssertionError(f"{name} exited before listening ({process.returncode})")
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                    return
            except OSError:
                time.sleep(0.05)
        raise AssertionError(f"{name} did not start listening on loopback")

    @staticmethod
    def _stop_process(process: subprocess.Popen):
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)

    def _request(self, path: str, *, cookie: str = ""):
        connection = http.client.HTTPConnection("127.0.0.1", self.web_port, timeout=4)
        headers = {"Cookie": cookie} if cookie else {}
        connection.request("GET", path, headers=headers)
        response = connection.getresponse()
        body = response.read()
        result = response.status, response.getheaders(), body
        connection.close()
        return result

    def _post_command(self, command: dict, *, cookie: str):
        connection = http.client.HTTPConnection("127.0.0.1", self.gateway_port, timeout=4)
        body = json.dumps(command).encode()
        connection.request("POST", "/api/remote/v1/commands", body=body, headers={
            "Cookie": cookie,
            "Content-Type": "application/json",
            "Origin": f"http://127.0.0.1:{self.web_port}",
            "X-Flow-Request": "1",
        })
        response = connection.getresponse()
        result = response.status, json.loads(response.read())
        connection.close()
        return result

    def _sign_in(self, login: str) -> tuple[int, str]:
        status, headers, _ = self._request("/api/auth/login")
        self.assertEqual(status, 302)
        state_cookie = next(value.split(";", 1)[0] for name, value in headers if name.lower() == "set-cookie"
                            and value.startswith("flow_oauth_state="))
        authorize_url = next(value for name, value in headers if name.lower() == "location")
        parsed = urlsplit(authorize_url)
        query = parse_qs(parsed.query)
        provider_path = parsed.path + "?" + urlencode({
            "client_id": query["client_id"][0], "redirect_uri": query["redirect_uri"][0],
            "state": query["state"][0], "login": login,
        })
        provider = http.client.HTTPConnection("127.0.0.1", self.provider.server_address[1], timeout=3)
        provider.request("GET", provider_path)
        authorized = provider.getresponse()
        redirect = authorized.getheader("Location")
        authorized.read()
        provider.close()
        callback = urlsplit(redirect)
        callback_path = callback.path + "?" + callback.query
        status, headers, _ = self._request(callback_path, cookie=state_cookie)
        session = next((value.split(";", 1)[0] for name, value in headers if name.lower() == "set-cookie"
                        and value.startswith("flow_session=")), "")
        return status, session

    def test_local_e2e_oauth_offline_and_failure_notification(self):
        status, _, body = self._request("/")
        self.assertEqual(status, 200)
        self.assertIn(b"Flow", body)

        laptop = http.client.HTTPConnection("127.0.0.1", self.laptop_port, timeout=4)
        laptop.request("GET", "/api/remote/v1/events?limit=100", headers={"Authorization": f"Bearer {GATEWAY_KEY}"})
        response = laptop.getresponse()
        self.assertEqual(response.status, 200)
        event_page = json.loads(response.read())
        laptop.close()
        feed = event_page["events"]
        self.assertTrue(event_page["nextCursor"], event_page)
        failures = [event for event in feed if event["type"] == "attempt.failed"
                    and event["data"].get("failure") == "fixture failure"]
        self.assertEqual(len(failures), 3, feed)
        for failure in failures:
            self.assertEqual(failure["target"]["taskId"], "T1")
            self.assertEqual(failure["target"]["req"], "REQ-001")
            self.assertEqual(failure["data"]["failure"], "fixture failure")

        status, session = self._sign_in("dav033")
        self.assertEqual(status, 302)
        self.assertTrue(session)
        status, _, body = self._request("/api/auth/session", cookie=session)
        self.assertEqual((status, json.loads(body)["login"]), (200, "dav033"))

        cancel_command = {
            "schemaVersion": 1,
            "idempotencyKey": "e2e-cancel-attempt-0001",
            "type": "cancel-attempt",
            "target": {"kind": "attempt", "project": "demo", "req": "REQ-002", "attemptId": "att-0001"},
            "precondition": {"state": "running"},
            "reason": "E2E cancellation",
        }
        stale = {**cancel_command, "idempotencyKey": "e2e-cancel-stale-0001",
                 "precondition": {"state": "reserved"}}
        status, body = self._post_command(stale, cookie=session)
        self.assertEqual((status, body.get("code")), (409, "STALE_PRECONDITION"), body)

        status, body = self._post_command(cancel_command, cookie=session)
        self.assertEqual((status, body.get("status")), (200, "OK"), body)
        scheduler_db = self.root / ".state" / "scheduler" / "demo-REQ-002.db"
        db = sqlite3.connect(scheduler_db)
        try:
            cancelled = db.execute(
                "SELECT COUNT(*) FROM audit WHERE kind = 'attempt_transition' AND attempt_id = 'att-0001' "
                "AND detail LIKE '%cancelled%'"
            ).fetchone()[0]
        finally:
            db.close()
        self.assertEqual(cancelled, 1, "cancel command did not commit a cancellation transition to M1")

        status, foreign_session = self._sign_in("foreign-user")
        self.assertEqual(status, 403)
        self.assertFalse(foreign_session)
        status, _, body = self._request("/api/auth/session")
        self.assertEqual(status, 401)

        deadline = time.monotonic() + 8
        while time.monotonic() < deadline and len(FakeProviderHandler.telegram_messages) < len(failures):
            time.sleep(0.05)
        messages = FakeProviderHandler.telegram_messages
        self.assertEqual(len(messages), len(failures), messages)
        for message in messages:
            self.assertIn("Una tarea falló", message["text"])

        self._stop_process(self.laptop_process)
        deadline = time.monotonic() + 20
        offline = False
        while time.monotonic() < deadline:
            if self.gateway_runtimes and self.gateway_runtimes[0].liveness.status.value == "offline":
                offline = True
                break
            time.sleep(0.1)
        self.assertTrue(offline, "gateway did not detect laptop offline within 20 seconds")
        self.assertEqual(len(FakeProviderHandler.telegram_messages), len(failures))


if __name__ == "__main__":
    unittest.main()
