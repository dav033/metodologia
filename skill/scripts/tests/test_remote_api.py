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
sys.path.insert(0, str(SCRIPTS))
import bt_remote_api
KEY = "test-gateway-key-0123456789"


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


class RemoteApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.port = free_port()
        self.process = subprocess.Popen(
            [sys.executable, str(SCRIPTS / "bitacora.py"), "serve-remote", "--port", str(self.port)],
            cwd=SCRIPTS,
            env={**os.environ, "BITACORA_ROOT": self.temp.name, "FLOW_GATEWAY_KEY": KEY},
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
            ("GET", "/api/remote/v1/attempts/attempt-1/review", 503),
            ("GET", "/api/remote/v1/commands", 503),
            ("POST", "/api/remote/v1/commands", 400),
            ("GET", "/api/remote/v1/runs", 200),
            ("GET", "/api/remote/v1/plans", 200),
            ("GET", "/api/remote/v1/history", 503),
            ("GET", "/api/remote/v1/challenges", 503),
            ("POST", "/api/remote/v1/challenges", 503),
        )
        for method, path, expected_status in routes:
            with self.subTest(method=method, path=path):
                status, _, body = self.request(method, path, body="{}" if method == "POST" else None)
                self.assertEqual(status, expected_status, body.decode("utf-8"))

    def test_live_quotas_endpoint_returns_account_windows(self):
        class Handler:
            headers = {"Authorization": f"Bearer {KEY}"}
            path = "/api/remote/v1/quotas"

            def send(self, body, status, content_type):
                self.response = status, content_type, body

        handler = Handler()
        accounts = [{"profile": "codex-work", "provider": "codex", "status": "ok",
                     "observed_at": 1792411200, "windows": {"five_hour": {"used_percent": 27}}}]
        with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": KEY}), \
                patch("bt_quota_live.read_all_live", return_value=accounts):
            bt_remote_api.route_get(handler)

        status, content_type, body = handler.response
        self.assertEqual(status, 200)
        self.assertIn("application/json", content_type)
        payload = json.loads(body)
        self.assertEqual(payload["accounts"], accounts)
        self.assertTrue(payload["checkedAt"])

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
