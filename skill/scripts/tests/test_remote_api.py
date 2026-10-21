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
import tarfile
import zipfile
import threading
import time
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tests" / "migration"))
import installed_wheel  # noqa: E402
TEST_KEY = "test-only-gateway-key"


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

    def test_snapshot_uses_shared_now_frame_and_exposes_rejected_review_attempt(self):
        import bt_core
        import bt_live_api as live
        import bt_server

        with tempfile.TemporaryDirectory() as root, patch.dict(os.environ, {"FLOW_GATEWAY_KEY": TEST_KEY}), \
                patch.object(bt_core, "ROOT", Path(root)), \
                patch.object(live, "now_items", wraps=live.now_items) as read_now:
            base = Path(root).resolve()
            rdir = base / "demo" / "requirements" / "REQ-001-fixture"
            rdir.mkdir(parents=True)
            tasks = [{"id": "T1", "milestone_id": "M1", "title": "Active task", "after": [], "complexity": "low",
                      "acceptance_criteria": ["Active work is visible"]},
                     {"id": "T2", "milestone_id": "M1", "title": "Rejected task", "after": [], "complexity": "low"},
                     {"id": "T3", "milestone_id": "M1", "title": "Failed task", "after": [], "complexity": "low"}]
            plan = {"schema_version": "1.0.0", "plan_id": "REQ-001", "revision": 1,
                    "milestones": [{"id": "M1", "title": "First"}], "tasks": tasks}
            (rdir / "PLAN.json").write_text(json.dumps(plan), encoding="utf-8")
            (rdir / "PLAN.md").write_text("---\nstatus: approved\n---\n# Plan — REQ-001 — Fixture\n", encoding="utf-8")
            (rdir / "SPEC.md").write_text("# Spec — REQ-001 — Fixture\n", encoding="utf-8")
            timestamp = dt.datetime(2026, 10, 20, 10, 1, tzinfo=dt.timezone.utc).timestamp()
            import bt_scheduler_adapter as scheduler_adapter
            db = scheduler_adapter.run_db_path(rdir)
            db.parent.mkdir(parents=True)
            doc = {"tasks": {"T1": {"state": "active", "attempts": ["A-live"]},
                             "T2": {"state": "recovering", "attempts": ["A-rejected"]},
                             "T3": {"state": "failed", "attempts": ["A-failed"]}},
                   "attempts": {"A-live": {"id": "A-live", "task_id": "T1", "number": 1, "state": "running",
                                            "created_at": timestamp - 60, "updated_at": timestamp,
                                            "last_event_at": timestamp},
                                "A-rejected": {"id": "A-rejected", "task_id": "T2", "number": 1,
                                               "state": "rejected", "created_at": timestamp - 120,
                                               "updated_at": timestamp - 30, "failure": "review required"},
                                "A-failed": {"id": "A-failed", "task_id": "T3", "number": 1,
                                             "state": "failed", "created_at": timestamp - 120,
                                             "updated_at": timestamp - 30, "failure": "tests failed"}}}
            with sqlite3.connect(db) as connection:
                connection.execute("CREATE TABLE state (id INTEGER PRIMARY KEY, version INTEGER NOT NULL, doc TEXT NOT NULL)")
                connection.execute("INSERT INTO state VALUES (1, 1, ?)", (json.dumps(doc),))
            projection = {"authority": "scheduler", "projection": True, "req": "REQ-001", "status": "running",
                          "heartbeat_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                          "plan_ref": {"plan_id": "REQ-001", "revision": 1, "sha256": "a" * 64},
                          "tasks": [{"id": "T1", "title": "Active task", "status": "in_progress",
                                     "scheduler_state": "active", "attempts": 1},
                                    {"id": "T2", "title": "Rejected task", "status": "in_progress",
                                     "scheduler_state": "recovering", "attempts": 1},
                                    {"id": "T3", "title": "Failed task", "status": "in_progress",
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
            self.assertEqual(snapshot["runs"][0]["req"], "REQ-001")
            self.assertEqual(snapshot["runs"][0]["state"], "running")
            self.assertIn("activeAttempt", snapshot["runs"][0])
            self.assertEqual(snapshot["plans"][0]["req"], "REQ-001")
            self.assertEqual(snapshot["plans"][0]["tasks"][0]["acceptanceCriteria"],
                             ["Active work is visible"])
            self.assertEqual(snapshot["plans"][0]["acceptanceCriteria"], ["Active work is visible"])
            last_activity = dt.datetime.fromisoformat(snapshot["runs"][0]["lastActivityAt"].replace("Z", "+00:00"))
            self.assertEqual(last_activity, dt.datetime(2026, 10, 20, 10, 1, tzinfo=dt.timezone.utc))
            rejected_task = snapshot["runs"][0]["tasks"][1]
            self.assertEqual(rejected_task["state"], "rejected")
            self.assertIsNone(rejected_task["activeAttempt"])
            self.assertEqual(rejected_task["reviewAttempt"]["id"], "A-rejected")
            self.assertFalse(rejected_task["reviewAttempt"]["live"])
            self.assertEqual(rejected_task["history"][0]["id"], "A-rejected")
            failed_task = snapshot["runs"][0]["tasks"][2]
            self.assertEqual(failed_task["state"], "rejected")
            self.assertIsNone(failed_task["activeAttempt"])
            self.assertEqual(failed_task["reviewAttempt"]["id"], "A-failed")
            self.assertFalse(failed_task["reviewAttempt"]["live"])
            self.assertEqual(failed_task["history"][0]["id"], "A-failed")

            self.request(server.server_address[1], "/api/remote/v1/snapshot", TEST_KEY)
            self.assertEqual(read_now.call_count, 1)
            self.assertIn(b"A-live", live._now_frame(base))
            self.assertEqual(read_now.call_count, 1)

    def test_snapshot_route_keeps_failed_attempt_identity_out_of_active_attempt(self):
        import bt_core
        import bt_live_api
        import bt_plans_api
        import bt_remote_api

        attempt = {"id": "A-failed", "state": "failed", "live": False, "failure": "checks failed"}
        summary = {"run": "demo/REQ-001", "project": "demo", "req_id": "REQ-001", "title": "Demo",
                   "status": "failed", "active": False, "updated_at": None,
                   "tasks": [{"id": "T1", "title": "Build", "state": "failed", "attempt": attempt,
                              "history": [attempt]}]}

        class Handler:
            path = "/api/remote/v1/snapshot"
            headers = {"Authorization": f"Bearer {TEST_KEY}"}

            def send(self, body, status, content_type):
                self.body, self.status, self.content_type = body, status, content_type

        handler = Handler()
        with tempfile.TemporaryDirectory() as root, patch.dict(os.environ, {"FLOW_GATEWAY_KEY": TEST_KEY}), \
                patch.object(bt_core, "ROOT", Path(root)), \
                patch.object(bt_live_api, "run_summaries", return_value=[summary]), \
                patch.object(bt_live_api, "now_frame_data", return_value={"items": []}), \
                patch.object(bt_plans_api, "plans_payload", return_value=[]):
            bt_remote_api.route_get(handler)

        self.assertEqual(handler.status, 200)
        task = json.loads(handler.body)["runs"][0]["tasks"][0]
        self.assertIsNone(task["activeAttempt"])
        self.assertEqual(task["reviewAttempt"]["id"], "A-failed")

    def test_keyed_read_models_are_served_by_the_real_http_listener(self):
        with tempfile.TemporaryDirectory() as root:
            import bt_remote_commands as commands

            req_dir = Path(root) / "demo" / "requirements" / "REQ-001-fixture"
            req_dir.mkdir(parents=True)
            plan = {"schema_version": "1.0.0", "plan_id": "REQ-001", "revision": 1,
                    "milestones": [{"id": "M1", "title": "First"}],
                    "tasks": [{"id": "T1", "milestone_id": "M1", "title": "Task", "objective": "x",
                               "after": [], "complexity": "low"}]}
            (req_dir / "PLAN.json").write_text(json.dumps(plan), encoding="utf-8")
            (req_dir / "PLAN.md").write_text("---\nstatus: approved\n---\n# Plan\n", encoding="utf-8")
            ledger = commands.Ledger(Path(root) / ".state" / "remote" / "commands.db")
            outcome = ledger.submit({"idempotency_key": "fixture-command-1", "command": "note",
                                     "target": "demo/REQ-001", "origin": "web", "params": {"task": "T1", "note": "fixture"},
                                     "precondition": {"state": "running"}},
                                    {"note": lambda target, params: {"saved": True}},
                                    lambda target: {"state": "running"})
            self.assertEqual(outcome["status"], "OK")
            quota_cache = Path(root) / ".state" / "globalusage-cache.json"
            quota_cache.parent.mkdir(parents=True, exist_ok=True)
            quota_cache.write_text(json.dumps({"at": time.time(), "rows": []}), encoding="utf-8")
            port = free_port()
            env = {**os.environ, "BITACORA_ROOT": root, "FLOW_GATEWAY_KEY": TEST_KEY}
            process = self.start_server("serve-remote", port, env)
            try:
                for path in ("/api/remote/v1/commands", "/api/remote/v1/history"):
                    with self.subTest(path=path):
                        status, content_type, body = self.request(port, path, TEST_KEY)
                        self.assertEqual(status, 200, body.decode("utf-8"))
                        self.assertTrue(content_type.startswith("application/json"))
                        response = json.loads(body)
                        self.assertEqual(len(response["commands"]), 1)
                        self.assertEqual(response["commands"][0]["command"], "note")
                        self.assertTrue(response["nextCursor"].startswith("cmd_"))
                        self.assertNotIn('"note":"fixture"', body.decode("utf-8"))

                status, _, body = self.request(port, "/api/remote/v1/commands?after=invalid", TEST_KEY)
                self.assertEqual(status, 400)
                self.assertEqual(json.loads(body)["code"], "INVALID_CURSOR")

                status, _, body = self.request(port, "/api/remote/v1/quotas", TEST_KEY)
                self.assertIn(status, (200, 503), body.decode("utf-8"))
                if status == 200:
                    self.assertIn("accounts", json.loads(body))
                else:
                    self.assertEqual(json.loads(body)["code"], "QUOTAS_UNAVAILABLE")

                status, _, body = self.request(port, "/api/remote/v1/routes", TEST_KEY)
                self.assertEqual(status, 400)
                self.assertEqual(json.loads(body)["code"], "INVALID_ROUTE_QUERY")

                status, _, body = self.request(
                    port, "/api/remote/v1/routes?target=demo%2FREQ-001&task=T1", TEST_KEY)
                self.assertEqual(status, 404, body.decode("utf-8"))
                self.assertEqual(json.loads(body)["code"], "ROUTES_UNAVAILABLE")
            finally:
                self.stop_server(process)


    def test_installed_distribution_serves_remote_api_from_packaged_modules(self):
        installed = installed_wheel.get()
        remote_modules = {
            "bt_remote_api.py",
            "bt_remote_commands.py",
            "bt_remote_events.py",
            "bt_remote_recovery.py",
            "bt_remote_views.py",
        }
        with zipfile.ZipFile(installed.wheel) as wheel:
            wheel_files = {Path(name).name for name in wheel.namelist()}
        self.assertTrue(remote_modules.issubset(wheel_files), remote_modules - wheel_files)
        with tarfile.open(installed.sdist, "r:*") as archive:
            sdist_files = {Path(member.name).name for member in archive.getmembers()}
        self.assertTrue(remote_modules.issubset(sdist_files), remote_modules - sdist_files)

        port = free_port()
        env = {
            "PATH": "/usr/bin:/bin",
            "HOME": str(installed.work / "home"),
            "BITACORA_ROOT": str(installed.work / "bitacora"),
            "FLOW_GATEWAY_KEY": TEST_KEY,
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONIOENCODING": "utf-8",
        }
        command = (
            "import sys; sys.path.insert(0, sys.argv[1]); "
            "import bt_remote_api, bt_remote_commands, bt_remote_events, "
            "bt_remote_recovery, bt_remote_views; "
            "sys.argv = ['bitacora', 'serve-remote', '--port', sys.argv[2]]; "
            "import bitacora; bitacora.main()"
        )
        process = subprocess.Popen(
            [str(installed.python), "-I", "-c", command, str(installed.site), str(port)],
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
                    self.fail(f"installed bitacora serve-remote exited: {process.stderr.read()}")
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                        break
                except OSError:
                    time.sleep(0.05)
            else:
                self.fail("installed bitacora serve-remote did not start listening")

            status, content_type, body = self.request(port, "/api/remote/v1/health", TEST_KEY)
            self.assertEqual(status, 200, body.decode("utf-8"))
            self.assertTrue(content_type.startswith("application/json"))
            self.assertEqual(json.loads(body)["schemaVersion"], 1)
        finally:
            self.stop_server(process)
            process.stderr.close()


if __name__ == "__main__":
    unittest.main()
