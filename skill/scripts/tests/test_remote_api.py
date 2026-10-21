"""HTTP-level tests for the remote health endpoint and unchanged local panel."""
from __future__ import annotations

import datetime as dt
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


if __name__ == "__main__":
    unittest.main()
