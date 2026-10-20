"""Exercise the production CLI listener and the reverse-tunnel target."""

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
REPO = SCRIPTS.parents[1]


class RemoteListenerTests(unittest.TestCase):
    def test_cli_listener_does_not_serve_local_panel_routes(self):
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        with tempfile.TemporaryDirectory() as state_dir:
            env = {**os.environ, "BITACORA_ROOT": state_dir}
            process = subprocess.Popen(
                [sys.executable, str(SCRIPTS / "bitacora.py"), "serve-remote", "--port", str(port)],
                cwd=SCRIPTS,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            try:
                deadline = time.monotonic() + 8
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        self.fail("serve-remote exited before accepting requests")
                    try:
                        with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                            break
                    except OSError:
                        time.sleep(0.05)
                else:
                    self.fail("serve-remote did not start listening")

                for path in ("/", "/plans", "/p/metodologia/REQ-027", "/api/now", "/api/remote/v1evil",
                             "/api/remote/v1/health"):
                    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
                    connection.request("GET", path)
                    response = connection.getresponse()
                    response.read()
                    connection.close()
                    self.assertEqual(response.status, 404, path)

                connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
                connection.request("POST", "/plans/metodologia/REQ-027/launch", body="confirm=REQ-027")
                response = connection.getresponse()
                response.read()
                connection.close()
                self.assertEqual(response.status, 404, "POST /plans must not reach local plan controls")

                # Exercise the production CLI and HTTP command entry point: an edit-brief that could
                # freeze an owner-approved revision and invoke revise must carry the typed REQ challenge.
                connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
                command = {"schemaVersion": 1, "idempotencyKey": "edit-brief-test-0001", "type": "edit-brief",
                           "target": {"kind": "task", "project": "demo", "req": "REQ-027", "taskId": "T3"},
                           "precondition": {"state": "failed", "revision": 1}, "brief": "Updated brief"}
                connection.request("POST", "/api/remote/v1/commands", body=json.dumps(command),
                                   headers={"Content-Type": "application/json"})
                response = connection.getresponse()
                payload = json.loads(response.read())
                connection.close()
                self.assertEqual(response.status, 409)
                self.assertEqual(payload["code"], "CONFIRMATION_REQUIRED")

                command["confirmation"] = {"challengeId": "challenge-0123456789", "typedReq": "REQ-026"}
                connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
                connection.request("POST", "/api/remote/v1/commands", body=json.dumps(command),
                                   headers={"Content-Type": "application/json"})
                response = connection.getresponse()
                payload = json.loads(response.read())
                connection.close()
                self.assertEqual(response.status, 409)
                self.assertEqual(payload["code"], "CONFIRMATION_REQUIRED")
            finally:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)

    def test_tunnel_unit_forwards_to_remote_listener_not_panel(self):
        unit = (REPO / "remote/deploy/advin-bitacora-tunnel.service").read_text(encoding="utf-8")
        self.assertIn("-R 127.0.0.1:18765:127.0.0.1:8766", unit)
        self.assertNotIn("127.0.0.1:8765:127.0.0.1:8765", unit)


if __name__ == "__main__":
    unittest.main()
