"""HTTP-level coverage for the authenticated remote API entry point."""
from __future__ import annotations

import http.client
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
REPO = SCRIPTS.parents[1]
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(REPO / "tests" / "migration"))
import bt_remote_api
import installed_wheel
KEY = "test-gateway-key-0123456789"


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


class Handler:
    path = "/api/remote/v1/snapshot"
    headers = {"Authorization": "Bearer test-key"}

    def send(self, body, status, content_type):
        self.body, self.status, self.content_type = body, status, content_type


class MobileDialectTests(unittest.TestCase):
    """The production projections must carry every key the mobile `parseSnapshot` requires, plus round/decision detail."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.rdir = self.root / "demo" / "requirements" / "REQ-001-thing"
        (self.rdir / "rounds").mkdir(parents=True)
        (self.rdir / "PLAN.md").write_text(
            "---\nstatus: approved\n---\n# Thing\n\n## M1 — First\n- [ ] **T1** Build it\n", encoding="utf-8")
        (self.rdir / "rounds" / "round-01.json").write_text(json.dumps({
            "round": 1, "title": "Scope", "status": "open", "answers": {},
            "questions": [{"id": "q1", "text": "Which?", "type": "choice", "options": [{"key": "a", "label": "A"}]}]}),
            encoding="utf-8")
        self.decision = {"id": "T1:1", "task": "T1", "title": "T1 bloqueada", "what": "Bloqueada.", "evidence": [],
                         "options": [{"id": "retry", "label": "Reintentar", "consequence": "Gasta un intento."}],
                         "recommended": "retry", "unskippable": False}

    def test_snapshot_keeps_failed_attempt_reviewable_without_marking_it_active(self):
        runs = [{"run": "demo/REQ-001", "status": "running", "tasks": [
            {"id": "T1", "state": "rejected", "attempt": {"id": "att-9", "state": "failed", "live": False,
                                                          "ended_at": "2026-10-20T10:00:00Z"}},
            {"id": "T2", "state": "running", "attempt": {"id": "att-10", "state": "running", "live": True}}]}]
        with patch.object(bt_remote_api, "_runs", return_value=runs), \
                patch.object(bt_remote_api, "_shared_now_items", return_value=[]):
            rows = bt_remote_api._snapshot_runs()
        failed, running = rows[0]["tasks"]
        self.assertIsNone(failed["activeAttempt"])
        self.assertEqual(failed["reviewAttempt"]["id"], "att-9")
        self.assertEqual(running["activeAttempt"]["id"], "att-10")
        self.assertIsNone(running["reviewAttempt"])
        self.assertEqual(rows[0]["activeAttempt"]["id"], "att-10")

    def snapshot(self):
        status = {"project": "demo", "req_id": "REQ-001", "title": "Thing",
                  "plan": {"plan_id": "p1", "revision": 2, "status": "approved"},
                  "run": {"status": "running", "active": True, "updated_at": "2026-10-20T10:00:00Z"},
                  "summary": {"tasks_total": 1, "tasks_done": 0, "difficulty": "low"},
                  "milestones": [{"id": "M1", "tasks": [{
                      "id": "T1", "title": "Build it", "milestone_id": "M1", "state": "running", "attempts": 1,
                      "attempt": {"id": "att-1", "state": "running", "live": True, "last_activity_at": "2026-10-20T10:00:00Z"},
                      "history": []}]}]}
        handler = Handler()
        with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": "test-key"}), \
                patch("bt_core.ROOT", self.root), \
                patch("bt_live_api.runs_in_scope", return_value=[("demo", self.rdir)]), \
                patch("bt_planstatus.plan_status", return_value=status), \
                patch("bt_scheduler_decisions.open_requests", return_value=[self.decision]), \
                patch.object(bt_remote_api, "_shared_now_items", return_value=[]):
            bt_remote_api.route_get(handler)
        self.assertEqual(handler.status, 200, handler.body)
        return json.loads(handler.body)

    def test_snapshot_runs_use_the_mobile_dialect(self):
        run = self.snapshot()["runs"][0]
        self.assertEqual((run["project"], run["req"], run["state"]), ("demo", "REQ-001", "running"))
        self.assertEqual(run["activeAttempt"]["id"], "att-1")
        task = run["tasks"][0]
        self.assertEqual((task["id"], task["state"], task["activeAttempt"]["id"]), ("T1", "running", "att-1"))

    def test_snapshot_plans_carry_state_tasks_decisions_and_rounds(self):
        snapshot = self.snapshot()
        plan = snapshot["plans"][0]
        self.assertEqual((plan["project"], plan["req"], plan["state"], plan["revision"]), ("demo", "REQ-001", "approved", 2))
        self.assertEqual([task["id"] for task in plan["tasks"]], ["T1"])
        self.assertEqual(snapshot["rounds"][0]["questions"][0]["options"], [{"key": "a", "label": "A"}])
        self.assertEqual((snapshot["rounds"][0]["project"], snapshot["rounds"][0]["req"], snapshot["rounds"][0]["round"]),
                         ("demo", "REQ-001", 1))
        decision = snapshot["decisionRequests"][0]
        self.assertEqual((decision["project"], decision["req"], decision["id"]), ("demo", "REQ-001", "T1:1"))
        self.assertEqual(decision["options"][0]["consequence"], "Gasta un intento.")


class RemoteApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.port = free_port()
        self.process = subprocess.Popen(
            [sys.executable, str(SCRIPTS / "bitacora.py"), "serve-remote", "--port", str(self.port)],
            cwd=SCRIPTS,
            env={**os.environ, "BITACORA_ROOT": self.temp.name, "HOME": self.temp.name, "FLOW_GATEWAY_KEY": KEY},
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                self.fail("serve-remote exited before accepting requests")
            try:
                with socket.create_connection(("127.0.0.1", self.port), timeout=0.2):
                    break
            except OSError:
                time.sleep(0.05)
        else:
            self.fail("serve-remote did not start listening")

    def tearDown(self):
        self.process.terminate()
        try:
            self.process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=3)
        self.temp.cleanup()

    def test_remote_entry_point_runs_from_installed_wheel(self):
        installed = installed_wheel.get()
        probe = subprocess.run(
            [str(installed.python), "-I", "-c",
             "import bt_remote_api, bt_remote_commands, bt_remote_events, bt_remote_recovery, bt_remote_views"],
            cwd=installed.work,
            env={"PATH": "/usr/bin:/bin", "HOME": str(installed.work / "home"),
                 "PYTHONDONTWRITEBYTECODE": "1"},
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(probe.returncode, 0, probe.stderr)

        port = free_port()
        env = {"PATH": "/usr/bin:/bin", "HOME": str(installed.work / "home"),
               "BITACORA_ROOT": str(installed.work / "remote-root"), "FLOW_GATEWAY_KEY": KEY,
               "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"}
        process = subprocess.Popen(
            [str(installed.python), "-I", "-c",
             "import sys, bt_server; bt_server.serve_remote(int(sys.argv[1]))", str(port)],
            cwd=installed.work, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        try:
            deadline = time.monotonic() + 8
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    self.fail("installed serve-remote exited before accepting requests")
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                        break
                except OSError:
                    time.sleep(0.05)
            else:
                self.fail("installed serve-remote did not start listening")

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

    def request(self, method: str, path: str, *, key: str | None = KEY, body: str | None = None):
        headers = {"Content-Type": "application/json"}
        if key is not None:
            headers["Authorization"] = f"Bearer {key}"
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=3)
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        payload = response.read()
        result = response.status, response.getheader("Content-Type", ""), payload
        connection.close()
        return result

    def test_gateway_key_is_required_and_health_has_version_and_timestamp(self):
        status, content_type, body = self.request("GET", "/api/remote/v1/health", key=None)
        self.assertEqual(status, 401)
        self.assertIn("application/problem+json", content_type)
        self.assertEqual(json.loads(body)["code"], "UNAUTHORIZED")

        status, _, body = self.request("GET", "/api/remote/v1/health")
        health = json.loads(body)
        self.assertEqual(status, 200)
        self.assertEqual(health["schemaVersion"], 1)
        self.assertTrue(health["version"])
        self.assertTrue(health["checkedAt"])

    def test_contract_routes_are_dispatched_by_the_real_listener(self):
        routes = (
            ("GET", "/api/remote/v1/snapshot", 200),
            ("GET", "/api/remote/v1/events", 200),
            ("GET", "/api/remote/v1/attempts/attempt-1/review", 404),
            ("GET", "/api/remote/v1/quotas", 200),
            ("GET", "/api/remote/v1/commands", 200),
            ("POST", "/api/remote/v1/commands", 400),
            ("GET", "/api/remote/v1/runs", 200),
            ("GET", "/api/remote/v1/plans", 200),
            ("GET", "/api/remote/v1/history", 200),
            ("GET", "/api/remote/v1/challenges", 503),
            ("POST", "/api/remote/v1/challenges", 400),
        )
        for method, path, expected_status in routes:
            with self.subTest(method=method, path=path):
                status, _, body = self.request(method, path, body="{}" if method == "POST" else None)
                self.assertEqual(status, expected_status, body.decode("utf-8"))

    def test_quotas_and_history_are_real_read_models_not_placeholders(self):
        status, _, body = self.request("GET", "/api/remote/v1/quotas")
        self.assertEqual(status, 200)
        quotas = json.loads(body)
        self.assertIsInstance(quotas["accounts"], list)
        self.assertTrue(quotas["checkedAt"])
        status, _, body = self.request("GET", "/api/remote/v1/history")
        self.assertEqual((status, json.loads(body)["commands"]), (200, []))

    def test_snapshot_includes_live_task_and_latest_sign_of_life_from_shared_now_frame(self):
        runs = [{"run": "demo/REQ-001", "updated_at": "2026-10-19T10:00:00Z", "tasks": [
            {"id": "T1", "title": "Prepare", "attempt": {"last_activity_at": "2026-10-19T10:01:00Z"}},
            {"id": "T2", "title": "Build", "attempt": {"last_activity_at": "2026-10-19T10:03:00Z"}},
        ]}]
        shared_frame = (b'event: now\ndata: {"items":[{"project":"demo","req_id":"REQ-001",'
                        b'"task":"T2"}],"sessions":[]}\n\n')
        with patch.object(bt_remote_api, "_runs", return_value=runs), \
                patch("bt_live_api._now_frame", return_value=shared_frame) as now_frame:
            snapshot = bt_remote_api._snapshot_runs()

        now_frame.assert_called_once_with(None)
        self.assertEqual(snapshot[0]["active_task"], {"id": "T2", "title": "Build"})
        self.assertEqual(snapshot[0]["last_sign_of_life"], "2026-10-19T10:03:00Z")

    def test_snapshot_handles_large_fixture_within_one_second(self):
        fixture_runs = [{"run": f"demo/REQ-{index:04d}", "updated_at": None, "tasks": []}
                        for index in range(3000)]
        with patch.object(bt_remote_api, "_runs", return_value=fixture_runs), \
                patch.object(bt_remote_api, "_shared_now_items", return_value=[]):
            started = time.monotonic()
            snapshot = bt_remote_api._snapshot_runs()
            elapsed = time.monotonic() - started

        self.assertEqual(len(snapshot), len(fixture_runs))
        self.assertLess(elapsed, 1.0)

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
