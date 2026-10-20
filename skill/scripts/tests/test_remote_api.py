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

SCRIPTS = Path(__file__).resolve().parents[1]
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
            ("GET", "/api/remote/v1/quotas", 503),
            ("GET", "/api/remote/v1/commands", 503),
            ("POST", "/api/remote/v1/commands", 503),
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
