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
<<<<<<< 7d0156fc3acf8afdbcdf78e19160f8fd15f17368
||||||| db6edf954e129b7cd051a3c578550f3b2f481e80
<<<<<<< 70de5f62178587b71e15d40677732fb4dc3cae8c
||||||| c811dba709f0c3894932292dca3aa9fddaea0ccd
<<<<<<< 4273ff48ab3b1b2c2ef13b15ffc7e756d2fef067
||||||| 2aea77d9f6987b6a86600183103b4f4b8ef75bfc
<<<<<<< d5722a644747de28545fa30eb743fa0997f37253
||||||| c0969389257f369ac7e60b2afc11ee15262aef0e
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
=======
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS.parents[1] / "remote" / "gateway"))
sys.path.insert(0, str(REPO / "tests" / "migration"))
import installed_wheel

>>>>>>> 8c18ec6092cb5c79129fab705964d0f2b775527a
=======
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS.parents[1] / "remote" / "gateway"))
sys.path.insert(0, str(REPO / "tests" / "migration"))
import bt_remote_api
import installed_wheel
>>>>>>> 6ca40753a3fa92b259d7156226575fb60558f6e0
=======
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS.parents[1] / "remote" / "gateway"))
sys.path.insert(0, str(REPO / "tests" / "migration"))
import bt_remote_api
import installed_wheel
>>>>>>> 2379a2a93808a923d50b6b1f2f82714d0e07f691
=======
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS.parents[1] / "remote" / "gateway"))
sys.path.insert(0, str(REPO / "tests" / "migration"))
import bt_remote_api
import installed_wheel
>>>>>>> 67cedce0c942471ce724ebeb8762af53c336f590
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
            tasks = [{"id": "T1", "milestone_id": "M1", "title": "Active task", "after": [], "complexity": "low"},
                     {"id": "T2", "milestone_id": "M1", "title": "Rejected task", "after": [], "complexity": "low"}]
            plan = {"schema_version": "1.0.0", "plan_id": "REQ-001", "revision": 1,
                    "milestones": [{"id": "M1", "title": "First"}], "tasks": tasks}
            (rdir / "PLAN.json").write_text(json.dumps(plan), encoding="utf-8")
            (rdir / "PLAN.md").write_text("---\nstatus: approved\n---\n# Plan — REQ-001 — Fixture\n", encoding="utf-8")
            (rdir / "SPEC.md").write_text("# Spec — REQ-001 — Fixture\n", encoding="utf-8")
            rounds_dir = rdir / "rounds"
            rounds_dir.mkdir()
            (rounds_dir / "round-02.json").write_text(json.dumps({
                "round": 2, "status": "open", "title": "Scope", "intro": "Confirm scope",
                "coverage": "edge cases", "revision": 3,
                "questions": [{"id": "q1", "text": "Continue?", "type": "choice",
                               "options": [{"key": "yes", "label": "Yes"}]}]}), encoding="utf-8")
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
            decision = {"id": "decision-1", "task": "T2", "title": "Choose", "what": "Pick an option",
                        "evidence": ["attempts exhausted"],
                        "options": [{"id": "stop", "label": "Stop", "consequence": "Ends the run"}],
                        "recommended": "stop", "unskippable": True}
            with patch("bt_plans_api.open_decisions", return_value=[decision]):
                status, content_type, body = self.request(server.server_address[1], "/api/remote/v1/snapshot", TEST_KEY)
            elapsed = time.monotonic() - started
            snapshot = json.loads(body)

            self.assertEqual(status, 200)
            self.assertTrue(content_type.startswith("application/json"))
            self.assertLess(elapsed, 1.0)
            self.assertEqual(snapshot["runs"][0]["activeTask"]["id"], "T1")
            self.assertEqual(snapshot["runs"][0]["req"], "REQ-001")
            self.assertEqual(snapshot["runs"][0]["state"], "running")
            self.assertEqual(snapshot["runs"][0]["activeAttempt"]["id"], "A-live")
            last_activity = dt.datetime.fromisoformat(snapshot["runs"][0]["lastActivityAt"].replace("Z", "+00:00"))
            self.assertEqual(last_activity, dt.datetime(2026, 10, 20, 10, 1, tzinfo=dt.timezone.utc))
            rejected_task = snapshot["runs"][0]["tasks"][1]
            self.assertEqual(rejected_task["state"], "rejected")
            self.assertIsNone(rejected_task["activeAttempt"])
            self.assertEqual(rejected_task["reviewAttempt"]["id"], "A-rejected")
            self.assertFalse(rejected_task["reviewAttempt"]["live"])
            self.assertEqual(rejected_task["history"][0]["id"], "A-rejected")
            self.assertEqual(snapshot["plans"][0]["req"], "REQ-001")
            self.assertEqual(snapshot["plans"][0]["state"], "approved")
            self.assertEqual(snapshot["plans"][0]["tasks"][1]["id"], "T2")
            self.assertEqual(snapshot["rounds"][0]["round"], 2)
            self.assertEqual(snapshot["rounds"][0]["questions"][0]["id"], "q1")
            self.assertEqual(snapshot["decisionRequests"][0]["options"][0]["consequence"], "Ends the run")

            self.request(server.server_address[1], "/api/remote/v1/snapshot", TEST_KEY)
            self.assertEqual(read_now.call_count, 1)
            self.assertIn(b"A-live", live._now_frame(base))
            self.assertEqual(read_now.call_count, 1)

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

<<<<<<< 7d0156fc3acf8afdbcdf78e19160f8fd15f17368
||||||| db6edf954e129b7cd051a3c578550f3b2f481e80

<<<<<<< 70de5f62178587b71e15d40677732fb4dc3cae8c
||||||| c811dba709f0c3894932292dca3aa9fddaea0ccd
<<<<<<< 4273ff48ab3b1b2c2ef13b15ffc7e756d2fef067
||||||| 2aea77d9f6987b6a86600183103b4f4b8ef75bfc
<<<<<<< d5722a644747de28545fa30eb743fa0997f37253
||||||| c0969389257f369ac7e60b2afc11ee15262aef0e
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
=======
    def test_installed_wheel_serves_remote_api_and_resolves_round_and_decision_preconditions(self):
        installed = installed_wheel.get()
        remote_modules = {"bt_remote_api.py", "bt_remote_commands.py", "bt_remote_events.py",
                          "bt_remote_preconditions.py", "bt_remote_recovery.py", "bt_remote_views.py"}
        with zipfile.ZipFile(installed.wheel) as wheel:
            self.assertTrue(remote_modules.issubset({Path(name).name for name in wheel.namelist()}))
        with tarfile.open(installed.sdist, "r:*") as archive:
            self.assertTrue(remote_modules.issubset({Path(member.name).name for member in archive.getmembers()}))
        check = r"""
import json, pathlib, sys, tempfile
from unittest.mock import patch
sys.path.insert(0, sys.argv[1])
import bt_remote_api, bt_remote_commands, bt_remote_events, bt_remote_preconditions
import bt_remote_recovery, bt_remote_views
import bt_core, bt_plans_api, bt_scheduler_decisions
root = pathlib.Path(tempfile.mkdtemp())
rdir = root / "demo" / "REQ-001"
(rdir / "rounds").mkdir(parents=True)
(rdir / "rounds" / "round-01.json").write_text(json.dumps({"round": 1, "status": "open", "revision": 3}))
status = {"run": {"authority": "scheduler", "status": "running", "plan_ref": {"revision": 1}}, "plan": {}}
with patch.object(bt_core, "ROOT", root), \
     patch.object(bt_remote_commands, "_run_target", return_value=("demo", "REQ-001", rdir)), \
     patch.object(bt_plans_api, "status_of", return_value=status), \
     patch.object(bt_scheduler_decisions, "open_requests", return_value=[{"id": "decision-1", "state": "waiting"}]):
    assert bt_remote_commands.target_state("demo/REQ-001", "answer-round", {"round": 1}) == {"state": "open", "revision": 3}
    assert bt_remote_commands.target_state("demo/REQ-001", "answer-decision", {"request_id": "decision-1"}) == {"state": "waiting"}
"""
        subprocess.run([str(installed.python), "-I", "-c", check, str(installed.site)],
                       cwd=installed.work, check=True, timeout=30,
                       env={"PATH": "/usr/bin:/bin", "HOME": str(installed.work / "home"),
                            "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"})

        port = free_port()
        env = {"PATH": "/usr/bin:/bin", "HOME": str(installed.work / "home"),
               "BITACORA_ROOT": str(installed.work / "bitacora"), "FLOW_GATEWAY_KEY": TEST_KEY,
               "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"}
        process = subprocess.Popen(
            [str(installed.python), "-I", "-c",
             "import sys; sys.path.insert(0, sys.argv[1]); "
             "import bt_remote_api, bt_remote_commands, bt_remote_events, bt_remote_preconditions, "
             "bt_remote_recovery, bt_remote_views; "
             "from bt_server import serve_remote; serve_remote(int(sys.argv[2]))",
             str(installed.site), str(port)],
            cwd=installed.work, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
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
            status, _, body = self.request(port, "/api/remote/v1/health", TEST_KEY)
            self.assertEqual(status, 200, body.decode("utf-8"))
            self.assertEqual(json.loads(body)["schemaVersion"], 1)
        finally:
            self.stop_server(process)
            process.stderr.close()


>>>>>>> 8c18ec6092cb5c79129fab705964d0f2b775527a
=======
    def test_installed_wheel_serves_remote_api_and_resolves_round_and_decision_preconditions(self):
        installed = installed_wheel.get()
        remote_modules = {"bt_remote_api.py", "bt_remote_commands.py", "bt_remote_events.py",
                          "bt_remote_preconditions.py", "bt_remote_recovery.py", "bt_remote_views.py"}
        with zipfile.ZipFile(installed.wheel) as wheel:
            self.assertTrue(remote_modules.issubset({Path(name).name for name in wheel.namelist()}))
        with tarfile.open(installed.sdist, "r:*") as archive:
            self.assertTrue(remote_modules.issubset({Path(member.name).name for member in archive.getmembers()}))
        check = r"""
import json, pathlib, sys, tempfile
from unittest.mock import patch
sys.path.insert(0, sys.argv[1])
import bt_remote_api, bt_remote_commands, bt_remote_events, bt_remote_preconditions
import bt_remote_recovery, bt_remote_views
import bt_core, bt_plans_api, bt_scheduler_decisions
root = pathlib.Path(tempfile.mkdtemp())
rdir = root / "demo" / "REQ-001"
(rdir / "rounds").mkdir(parents=True)
(rdir / "rounds" / "round-01.json").write_text(json.dumps({"round": 1, "status": "open", "revision": 3}))
status = {"run": {"authority": "scheduler", "status": "running", "plan_ref": {"revision": 1}}, "plan": {}}
with patch.object(bt_core, "ROOT", root), \
     patch.object(bt_remote_commands, "_run_target", return_value=("demo", "REQ-001", rdir)), \
     patch.object(bt_plans_api, "status_of", return_value=status), \
     patch.object(bt_scheduler_decisions, "open_requests", return_value=[{"id": "decision-1", "state": "waiting"}]):
    assert bt_remote_commands.target_state("demo/REQ-001", "answer-round", {"round": 1}) == {"state": "open", "revision": 3}
    assert bt_remote_commands.target_state("demo/REQ-001", "answer-decision", {"request_id": "decision-1"}) == {"state": "waiting"}
"""
        subprocess.run([str(installed.python), "-I", "-c", check, str(installed.site)],
                       cwd=installed.work, check=True, timeout=30,
                       env={"PATH": "/usr/bin:/bin", "HOME": str(installed.work / "home"),
                            "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"})

        port = free_port()
        env = {"PATH": "/usr/bin:/bin", "HOME": str(installed.work / "home"),
               "BITACORA_ROOT": str(installed.work / "bitacora"), "FLOW_GATEWAY_KEY": TEST_KEY,
               "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"}
        process = subprocess.Popen(
            [str(installed.python), "-I", "-c",
             "import sys; sys.path.insert(0, sys.argv[1]); "
             "import bt_remote_api, bt_remote_commands, bt_remote_events, bt_remote_preconditions, "
             "bt_remote_recovery, bt_remote_views; "
             "from bt_server import serve_remote; serve_remote(int(sys.argv[2]))",
             str(installed.site), str(port)],
            cwd=installed.work, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
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
            status, _, body = self.request(port, "/api/remote/v1/health", TEST_KEY)
            self.assertEqual(status, 200, body.decode("utf-8"))
            self.assertEqual(json.loads(body)["schemaVersion"], 1)
        finally:
            self.stop_server(process)
            process.stderr.close()


>>>>>>> 6ca40753a3fa92b259d7156226575fb60558f6e0
=======
    def test_installed_wheel_and_sdist_serve_remote_api(self):
        installed = installed_wheel.get()
        remote_modules = {
            "bt_remote_api.py",
            "bt_remote_commands.py",
            "bt_remote_events.py",
            "bt_remote_preconditions.py",
            "bt_remote_recovery.py",
            "bt_remote_views.py",
        }
        with zipfile.ZipFile(installed.wheel) as wheel:
            wheel_files = {Path(name).name for name in wheel.namelist()}
        self.assertTrue(remote_modules.issubset(wheel_files))
        with tarfile.open(installed.sdist, "r:*") as archive:
            sdist_files = {Path(member.name).name for member in archive.getmembers()}
        self.assertTrue(remote_modules.issubset(sdist_files))

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
            "import sys; site, port = sys.argv[1:]; sys.path.insert(0, site); "
            "import bt_remote_api, bt_remote_commands, bt_remote_events, bt_remote_preconditions, "
            "bt_remote_recovery, bt_remote_views; "
            "sys.argv = ['bitacora', 'serve-remote', '--port', port]; "
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
                    self.fail(f"installed serve-remote exited: {process.stderr.read()}")
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                        break
                except OSError:
                    time.sleep(0.05)
            else:
                self.fail("installed serve-remote did not start listening")

            status, content_type, body = self.request(port, "/api/remote/v1/health", TEST_KEY)
            self.assertEqual(status, 200, body.decode("utf-8"))
            self.assertTrue(content_type.startswith("application/json"))
            self.assertEqual(json.loads(body)["schemaVersion"], 1)
        finally:
            self.stop_server(process)
            process.stderr.close()


>>>>>>> 2379a2a93808a923d50b6b1f2f82714d0e07f691
=======
    def test_installed_distribution_includes_remote_modules_and_dispatches_remote_commands(self):
        installed = installed_wheel.get()
        remote_modules = {
            "bt_remote_api.py",
            "bt_remote_commands.py",
            "bt_remote_edit.py",
            "bt_remote_events.py",
            "bt_remote_preconditions.py",
            "bt_remote_recovery.py",
            "bt_remote_views.py",
            "bt_route_pins.py",
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
        command = r"""
import sys
site, port = sys.argv[1:]
sys.path.insert(0, site)
import bt_remote_api, bt_remote_commands, bt_remote_events, bt_remote_recovery, bt_remote_views
import bt_remote_preconditions, bt_remote_edit, bt_route_pins
import bt_plans_api

# Exercise the real command dispatchers. The fixture has no project, so each dispatch
# reaches its installed implementation and fails on the expected project lookup guard.
try:
    bt_remote_commands.dispatch_run_command("retry", "demo/REQ-001", {"task": "T1"})
except bt_plans_api.PlanError as error:
    assert str(error) == "Proyecto no encontrado."
else:
    raise AssertionError("retry unexpectedly succeeded without a project")
assert "bt_route_pins" in sys.modules
try:
    bt_remote_commands.dispatch_edit_brief(
        "demo/REQ-001", {"typed_req": "REQ-001", "task": "T1", "brief": "updated"})
except bt_plans_api.PlanError as error:
    assert str(error) == "Proyecto no encontrado."
else:
    raise AssertionError("edit-brief unexpectedly succeeded without a project")
assert "bt_remote_edit" in sys.modules

sys.argv = ["bitacora", "serve-remote", "--port", port]
import bitacora
bitacora.main()
"""
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
                    self.fail(f"installed serve-remote exited: {process.stderr.read()}")
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                        break
                except OSError:
                    time.sleep(0.05)
            else:
                self.fail("installed serve-remote did not start listening")

            status, content_type, body = self.request(port, "/api/remote/v1/health", TEST_KEY)
            self.assertEqual(status, 200, body.decode("utf-8"))
            self.assertTrue(content_type.startswith("application/json"))
            self.assertEqual(json.loads(body)["schemaVersion"], 1)
        finally:
            self.stop_server(process)
            process.stderr.close()

>>>>>>> 67cedce0c942471ce724ebeb8762af53c336f590

if __name__ == "__main__":
    unittest.main()
