"""HTTP-level tests for the remote health endpoint and unchanged local panel."""
from __future__ import annotations

import datetime as dt
import http.client
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
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
<<<<<<< e5f3b15ac8278a1920c8feef414f89bd689013ca
TEST_KEY = "test-only-gateway-key"
||||||| d5483831b29a60a51a2e6b909a8d98b8dba66d59
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS.parents[1] / "remote" / "gateway"))
<<<<<<< 27ef4b35c0fcf26f0b68058d0e95deb7ed5fe25f
||||||| 8f79667cf84ec0090fd3b66913d431e3da8f60e3
||||||| 21ed855e0526bd6f970e6e6d9769919c0dcbf0b3
=======
sys.path.insert(0, str(REPO / "tests" / "migration"))
>>>>>>> 0ba9b657011be079d160ed12134f1130cf08a4e9
=======
sys.path.insert(0, str(REPO / "tests" / "migration"))
>>>>>>> 4f158bc298d1217d991378eb8f09a3fb378e3af2
import bt_remote_api
KEY = "test-gateway-key-0123456789"
=======
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS.parents[1] / "remote" / "gateway"))
sys.path.insert(0, str(REPO / "tests" / "migration"))
import bt_remote_api
import installed_wheel
KEY = "test-gateway-key-0123456789"
>>>>>>> 066590a282689183fac2726efbf57cbf4d8bce1a


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


class RemoteApiTests(unittest.TestCase):
    def start_server(self, command: str, port: int, env: dict[str, str]) -> subprocess.Popen:
        process = subprocess.Popen(
            [sys.executable, str(SCRIPTS / "bitacora.py"), command, "--port", str(port)],
            cwd=SCRIPTS,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            if process.poll() is not None:
                self.fail(f"{command} exited before accepting requests")
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                    return process
            except OSError:
                time.sleep(0.05)
        process.terminate()
        process.wait(timeout=3)
        self.fail(f"{command} did not start listening")

    def request(self, port: int, path: str, key: str | None = None):
        headers = {}
        if key is not None:
            headers["Authorization"] = f"Bearer {key}"
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
        connection.request("GET", path, headers=headers)
        response = connection.getresponse()
        result = response.status, response.getheader("Content-Type", ""), response.read()
        connection.close()
        return result

    def stop_server(self, process: subprocess.Popen) -> None:
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)

    def test_health_requires_gateway_key_and_returns_version_and_timestamp(self):
        with tempfile.TemporaryDirectory() as root:
            port = free_port()
            env = {**os.environ, "BITACORA_ROOT": root, "FLOW_GATEWAY_KEY": TEST_KEY}
            process = self.start_server("serve-remote", port, env)
            try:
                status, content_type, body = self.request(port, "/api/remote/v1/health")
                self.assertEqual(status, 401)
                self.assertTrue(content_type.startswith("application/problem+json"))
                self.assertEqual(json.loads(body)["code"], "UNAUTHORIZED")

                status, content_type, body = self.request(port, "/api/remote/v1/health", TEST_KEY)
                health = json.loads(body)
                self.assertEqual(status, 200)
                self.assertTrue(content_type.startswith("application/json"))
                self.assertEqual(health["schemaVersion"], 1)
                self.assertEqual(health["status"], "ok")
                self.assertTrue(health["version"])
                checked_at = dt.datetime.fromisoformat(health["checkedAt"].replace("Z", "+00:00"))
                self.assertIsNotNone(checked_at.tzinfo)

                status, _, body = self.request(port, "/api/remote/v1/health", "wrong-key")
                self.assertEqual(status, 401)
                self.assertEqual(json.loads(body)["code"], "UNAUTHORIZED")
            finally:
                self.stop_server(process)

    def test_local_panel_routes_still_work(self):
        with tempfile.TemporaryDirectory() as root:
            port = free_port()
            env = {**os.environ, "BITACORA_ROOT": root}
            env.pop("FLOW_GATEWAY_KEY", None)
            process = self.start_server("serve", port, env)
            try:
                for path in ("/", "/api/now"):
                    with self.subTest(path=path):
                        status, _, _ = self.request(port, path)
                        self.assertEqual(status, 200)
            finally:
                self.stop_server(process)

    def test_read_models_route_to_command_ledger_quotas_and_eligible_routes(self):
        import bt_remote_api
        import bt_core
        import bt_plans_api
        import bt_remote_commands
        import bt_route_pins
        import bt_subscriptions

        class Handler:
            headers = {"Authorization": f"Bearer {TEST_KEY}"}
            path = ""

            def send(self, body, status, content_type):
                self.body, self.status, self.content_type = body, status, content_type

        class Candidate:
            route_id = "claude-sonnet"
            provider = "claude"
            model = "sonnet"
            profile = "work"

        calls = []
        ledger_row = {"idempotency_key": "command-1", "command": "retry", "target": "demo/REQ-001",
                      "origin": "web", "status": "OK", "outcome": '{"status":"accepted"}',
                      "code": None, "received_at": "2026-10-20T10:00:00Z"}
        with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": TEST_KEY}), \
                patch("bt_remote_commands.Ledger", return_value=type("LedgerStub", (), {
                    "rows": lambda self: [ledger_row]})()), \
                patch.object(bt_subscriptions, "summary", return_value=[{"profile": "work", "provider": "claude",
                    "status": "ok", "observed_at": 1792490400, "windows": {}}]), \
                patch.object(bt_core, "ROOT", Path("/tmp")), \
                patch.object(bt_plans_api, "req_dir", return_value=Path("/tmp/demo/REQ-001")), \
                patch.object(bt_route_pins, "available", side_effect=lambda project, rdir, task, _pin: (
                    calls.append((project, task)) or (Candidate(),))):
            handler = Handler()
            handler.path = "/api/remote/v1/commands?after=&limit=100"
            bt_remote_api.route_get(handler)
            commands = json.loads(handler.body)
            self.assertEqual(handler.status, 200)
            self.assertEqual(commands["commands"][0]["id"], "command-1")

            handler = Handler()
            handler.path = "/api/remote/v1/quotas"
            bt_remote_api.route_get(handler)
            self.assertEqual(json.loads(handler.body)["accounts"][0]["profile"], "work")

            handler = Handler()
            handler.path = "/api/remote/v1/routes?target=demo%2FREQ-001&task=T1"
            bt_remote_api.route_get(handler)
            routes = json.loads(handler.body)
            self.assertEqual(routes["routes"][0]["routeId"], "claude-sonnet")
            self.assertTrue(routes["routes"][0]["available"])
            self.assertEqual(calls, [("demo", "T1")])

    def test_snapshot_uses_shared_now_frame_and_exposes_rejected_review_attempt(self):
        import bt_core
        import bt_live_api as live
        import bt_server
        import bt_plans_api as plans_api
        import bt_rounds

        with tempfile.TemporaryDirectory() as root, patch.dict(os.environ, {"FLOW_GATEWAY_KEY": TEST_KEY}), \
                patch.object(bt_core, "ROOT", Path(root)), \
                patch.object(live, "now_items", wraps=live.now_items) as read_now, \
                patch.object(plans_api, "plans_payload", return_value=[{"project": "demo", "req_id": "REQ-001",
                              "plan_status": "approved", "run_status": "running", "updated_at": "2026-10-20T10:01:00Z"}]), \
                patch.object(bt_rounds, "load", return_value={"round": 2, "title": "Coverage", "intro": "Context",
                              "coverage": "2/5", "status": "open", "questions": [{"id": "q1", "text": "Scope?",
                              "type": "choice", "options": [{"key": "a", "label": "Option A"}]}]}), \
                patch.object(bt_rounds, "list_rounds", return_value=[Path("/tmp/round-02.json")]), \
                patch.object(plans_api, "open_decisions", return_value=[{"id": "decision-1", "title": "Choose",
                              "what": "Select", "options": [{"id": "continue", "label": "Continue",
                              "consequence": "Run continues"}]}]), \
                patch.object(plans_api, "req_dir", return_value=Path("/tmp/REQ-001")):
            base = Path(root).resolve()
            rdir = base / "demo" / "requirements" / "REQ-001-fixture"
            rdir.mkdir(parents=True)
            tasks = [{"id": "T1", "milestone_id": "M1", "title": "Active task", "after": [], "complexity": "low"},
                     {"id": "T2", "milestone_id": "M1", "title": "Rejected task", "after": [], "complexity": "low"}]
            plan = {"schema_version": "1.0.0", "plan_id": "REQ-001", "revision": 1,
                    "milestones": [{"id": "M1", "title": "First"}], "tasks": tasks}
            (rdir / "PLAN.json").write_text(json.dumps(plan), encoding="utf-8")
            (rdir / "PLAN.md").write_text("---\nstatus: approved\n---\n# Plan — REQ-001 — Fixture\n", encoding="utf-8")
            (rdir / "SPEC.md").write_text("# Spec — REQ-001 — Fixture\n", encoding="utf-8")
            timestamp = dt.datetime(2026, 10, 20, 10, 1, tzinfo=dt.timezone.utc).timestamp()
            db = base / ".state" / "scheduler" / "demo-REQ-001.db"
            db.parent.mkdir(parents=True)
            doc = {"tasks": {"T1": {"state": "active", "attempts": ["A-live"]},
                             "T2": {"state": "recovering", "attempts": ["A-rejected"]}},
                   "attempts": {"A-live": {"id": "A-live", "task_id": "T1", "number": 1, "state": "running",
                                            "created_at": timestamp - 60, "updated_at": timestamp,
                                            "last_event_at": timestamp},
                                "A-rejected": {"id": "A-rejected", "task_id": "T2", "number": 1,
                                               "state": "rejected", "created_at": timestamp - 120,
                                               "updated_at": timestamp - 30, "failure": "review required"}}}
            with sqlite3.connect(db) as connection:
                connection.execute("CREATE TABLE state (id INTEGER PRIMARY KEY, version INTEGER NOT NULL, doc TEXT NOT NULL)")
                connection.execute("INSERT INTO state VALUES (1, 1, ?)", (json.dumps(doc),))
            projection = {"authority": "scheduler", "projection": True, "req": "REQ-001", "status": "running",
                          "heartbeat_at": "2026-10-20T10:01:00+00:00",
                          "plan_ref": {"plan_id": "REQ-001", "revision": 1, "sha256": "a" * 64},
                          "tasks": [{"id": "T1", "title": "Active task", "status": "in_progress",
                                     "scheduler_state": "active", "attempts": 1},
                                    {"id": "T2", "title": "Rejected task", "status": "in_progress",
                                     "scheduler_state": "recovering", "attempts": 1}]}
            (rdir / "RUN.projection.json").write_text(json.dumps(projection), encoding="utf-8")
            live._now_data_cache.pop(base, None)
            live._now_cache.pop(base, None)
            server = ThreadingHTTPServer(("127.0.0.1", 0), bt_server.RemoteHandler)
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            self.addCleanup(server.server_close)
            self.addCleanup(server.shutdown)
            started = time.monotonic()
            status, content_type, body = self.request(server.server_address[1], "/api/remote/v1/snapshot", TEST_KEY)
            elapsed = time.monotonic() - started
            snapshot = json.loads(body)

            self.assertEqual(status, 200)
            self.assertTrue(content_type.startswith("application/json"))
            self.assertLess(elapsed, 1.0)
            self.assertEqual(snapshot["runs"][0]["activeTask"]["id"], "T1")
            self.assertEqual((snapshot["runs"][0]["req"], snapshot["runs"][0]["state"]), ("REQ-001", "running"))
            self.assertEqual((snapshot["plans"][0]["req"], snapshot["plans"][0]["state"]), ("REQ-001", "approved"))
            self.assertEqual(snapshot["rounds"][0]["round"], 2)
            self.assertEqual(snapshot["rounds"][0]["questions"][0]["options"][0]["label"], "Option A")
            self.assertEqual(snapshot["decisionRequests"][0]["id"], "decision-1")
            last_activity = dt.datetime.fromisoformat(snapshot["runs"][0]["lastActivityAt"].replace("Z", "+00:00"))
            self.assertEqual(last_activity, dt.datetime(2026, 10, 20, 10, 1, tzinfo=dt.timezone.utc))
            rejected_task = snapshot["runs"][0]["tasks"][1]
            self.assertEqual(rejected_task["state"], "rejected")
            self.assertIsNone(rejected_task["activeAttempt"])
            self.assertEqual(rejected_task["reviewAttempt"]["id"], "A-rejected")
            self.assertFalse(rejected_task["reviewAttempt"]["live"])
            self.assertEqual(rejected_task["history"][0]["id"], "A-rejected")

<<<<<<< e5f3b15ac8278a1920c8feef414f89bd689013ca
            self.request(server.server_address[1], "/api/remote/v1/snapshot", TEST_KEY)
            self.assertEqual(read_now.call_count, 1)
            self.assertIn(b"A-live", live._now_frame(base))
            self.assertEqual(read_now.call_count, 1)

    def test_snapshot_route_preserves_non_live_failed_attempt_for_review(self):
        import bt_remote_api
        import bt_plans_api

        class SnapshotHandler:
            path = "/api/remote/v1/snapshot"
            headers = {"Authorization": f"Bearer {TEST_KEY}"}

            def send(self, body, status, content_type):
                self.body, self.status, self.content_type = body, status, content_type

        failed_attempt = {"id": "A-failed", "state": "failed", "live": False,
                          "last_activity_at": "2026-10-20T10:00:00Z", "failure": "tests failed"}
        failed_run = {
            "run": "demo/REQ-001", "project": "demo", "req_id": "REQ-001", "title": "Demo",
            "updated_at": "2026-10-20T10:00:00Z", "max_attempts": 2, "active": False,
            "status": "failed", "tasks": [{"id": "T1", "title": "Failed task", "state": "failed",
                                               "attempt": failed_attempt, "history": [failed_attempt]}],
        }
        handler = SnapshotHandler()
        with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": TEST_KEY}), \
                patch("bt_live_api.run_summaries", return_value=[failed_run]), \
                patch("bt_live_api.now_frame_data", return_value={"items": []}), \
                patch.object(bt_plans_api, "plans_payload", return_value=[]):
            bt_remote_api.route_get(handler)

        payload = json.loads(handler.body)
        task = payload["runs"][0]["tasks"][0]
        self.assertEqual(handler.status, 200)
        self.assertIsNone(task["activeAttempt"])
        self.assertEqual(task["reviewAttempt"]["id"], "A-failed")
        self.assertFalse(task["reviewAttempt"]["live"])


if __name__ == "__main__":
    unittest.main()
||||||| d5483831b29a60a51a2e6b909a8d98b8dba66d59
    def test_local_panel_entry_point_still_serves_existing_routes(self):
        port = free_port()
        process = subprocess.Popen(
            [sys.executable, str(SCRIPTS / "bitacora.py"), "serve", "--port", str(port)],
            cwd=SCRIPTS,
            env={**os.environ, "BITACORA_ROOT": self.temp.name},
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            deadline = time.monotonic() + 8
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    self.fail("serve exited before accepting requests")
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                        break
                except OSError:
                    time.sleep(0.05)
            else:
                self.fail("serve did not start listening")
            for path in ("/", "/api/now"):
                connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
                connection.request("GET", path)
                response = connection.getresponse()
                response.read()
                connection.close()
                self.assertEqual(response.status, 200, path)
        finally:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)
=======
    def test_local_panel_entry_point_still_serves_existing_routes(self):
        port = free_port()
        process = subprocess.Popen(
            [sys.executable, str(SCRIPTS / "bitacora.py"), "serve", "--port", str(port)],
            cwd=SCRIPTS,
            env={**os.environ, "BITACORA_ROOT": self.temp.name},
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            deadline = time.monotonic() + 8
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    self.fail("serve exited before accepting requests")
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                        break
                except OSError:
                    time.sleep(0.05)
            else:
                self.fail("serve did not start listening")
            for path in ("/", "/api/now"):
                connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
                connection.request("GET", path)
                response = connection.getresponse()
                response.read()
                connection.close()
                self.assertEqual(response.status, 200, path)
        finally:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)

    def test_installed_wheel_serves_remote_api_from_packaged_modules(self):
        installed = installed_wheel.get()
        port = free_port()
        env = {"PATH": "/usr/bin:/bin", "HOME": str(installed.work / "home"),
               "BITACORA_ROOT": str(installed.work / "bitacora"), "FLOW_GATEWAY_KEY": KEY,
               "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"}
        process = subprocess.Popen(
            [str(installed.python), "-I", "-c",
             "import sys; sys.path.insert(0, sys.argv[1]); "
             "import bt_remote_api, bt_remote_commands, bt_remote_events, bt_remote_recovery, bt_remote_views; "
             "from bt_server import serve_remote; serve_remote(int(sys.argv[2]))",
             str(installed.site), str(port)],
            cwd=installed.work,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            deadline = time.monotonic() + 8
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    self.fail(f"installed serve_remote exited: {process.stderr.read()}")
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                        break
                except OSError:
                    time.sleep(0.05)
            else:
                self.fail("installed serve_remote did not start listening")

            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
            connection.request("GET", "/api/remote/v1/health",
                               headers={"Authorization": f"Bearer {KEY}"})
            response = connection.getresponse()
            body = response.read()
            connection.close()
            self.assertEqual(response.status, 200, body.decode("utf-8"))
            self.assertEqual(json.loads(body)["schemaVersion"], 1)
        finally:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)
            process.stderr.close()
>>>>>>> 066590a282689183fac2726efbf57cbf4d8bce1a
