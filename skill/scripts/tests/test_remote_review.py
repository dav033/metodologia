"""HTTP contract coverage for the remote failed-attempt read model."""
from __future__ import annotations

import hashlib
import http.client
import json
import os
import socket
import sqlite3
import sys
import tempfile
import threading
import unittest
from contextlib import closing
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
import bt_remote_api
from bt_server import RemoteHandler

ATTEMPT_ID = "att-review-1"
GATEWAY_KEY = "test-only-gateway-key"


class RemoteReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.rdir = self.root / "demo" / "requirements" / "REQ-001-review"
        self.rdir.mkdir(parents=True)
        self.executor_root = self.root / ".state" / "executor" / "demo-REQ-001-r1-fixture"
        self.attempt_dir = self.executor_root / "attempts" / "fixture-attempt"
        (self.attempt_dir / "handoff").mkdir(parents=True)
        self._write_executor_fixture()
        self.m6_path = self.root / "m6-quality.sqlite3"
        self._write_quality_fixture()

        import bt_attempt_facts
        import bt_live_api
        import bt_run_stores
        self.patches = [
            patch.object(bt_live_api, "runs", return_value=[("demo", self.rdir)]),
            patch.object(bt_attempt_facts, "attempt_facts", return_value={"T1": [{
                "attempt": ATTEMPT_ID, "task": "T1", "state": "rejected",
                "failure": "verification_rejected", "verdict": "rejected",
            }]}),
            patch.object(bt_run_stores, "paths", return_value={"m6": self.m6_path}),
            patch.dict(os.environ, {"FLOW_GATEWAY_KEY": GATEWAY_KEY}),
        ]
        for item in self.patches:
            item.start()
        self.addCleanup(self._stop_patches)

        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        self.server = ThreadingHTTPServer(("127.0.0.1", port), RemoteHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self._stop_server)
        self.port = port

    def _stop_patches(self):
        for item in reversed(self.patches):
            item.stop()

    def _stop_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def _write_executor_fixture(self):
        ledger = self.executor_root / "ledger.db"
        ledger.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(ledger)) as connection, connection:
            connection.execute("CREATE TABLE attempts (attempt_id TEXT, dirname TEXT, request TEXT)")
            connection.execute("INSERT INTO attempts VALUES (?, ?, ?)",
                               (ATTEMPT_ID, "fixture-attempt", json.dumps({"attempt_id": ATTEMPT_ID})))
        (self.attempt_dir / "output.tail").write_text(
            "\n".join(f"agent-line-{number}" +
                      (" SESSION_SECRET=example-session-secret" if number == 204 else "")
                      for number in range(205)) +
            "\nTELEGRAM_BOT_TOKEN=example-telegram-secret\n", encoding="utf-8")
        (self.attempt_dir / "supervisor.log").write_text("supervisor text must stay private", encoding="utf-8")
        (self.attempt_dir / "handoff" / "manifest.json").write_text(
            json.dumps({"changed_total": 1, "changed": ["M src/app.py"]}), encoding="utf-8")

    def _write_quality_fixture(self):
        stdout = b"verification failed\nFLOW_GATEWAY_KEY=example-gateway-secret\n"
        stderr = b""
        stdout_ref = "m6://artifact/" + hashlib.sha256(stdout).hexdigest()
        stderr_ref = "m6://artifact/" + hashlib.sha256(stderr).hexdigest()
        result = {"checks": [{"command": "python -m unittest", "exit_code": 1,
                              "stdout_ref": stdout_ref, "stderr_ref": stderr_ref}]}
        with closing(sqlite3.connect(self.m6_path)) as connection, connection:
            connection.executescript("CREATE TABLE requests(request_json TEXT, result_json TEXT, created_at TEXT);"
                                     "CREATE TABLE artifacts(digest TEXT, content BLOB);")
            connection.execute("INSERT INTO requests VALUES (?, ?, ?)",
                               (json.dumps({"attempt_id": ATTEMPT_ID}), json.dumps(result), "2026-10-20T00:00:00Z"))
            for reference, content in ((stdout_ref, stdout), (stderr_ref, stderr)):
                connection.execute("INSERT INTO artifacts VALUES (?, ?)",
                                   (reference.rsplit("/", 1)[-1], content))

    def request(self, path: str):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=3)
        connection.request("GET", path, headers={"Authorization": f"Bearer {GATEWAY_KEY}"})
        response = connection.getresponse()
        result = response.status, json.loads(response.read())
        connection.close()
        return result

    def test_failed_attempt_returns_cause_verification_diff_and_log_tail(self):
        status, review = self.request(f"/api/remote/v1/attempts/{ATTEMPT_ID}/review")

        self.assertEqual(status, 200)
        self.assertEqual(set(review), {"attemptId", "cause", "verification", "diff", "logTail"})
        self.assertEqual(review["cause"], "verification_rejected")
        self.assertEqual(review["verification"]["command"], "python -m unittest")
        self.assertIn("verification failed", review["verification"]["output"])
        self.assertEqual(review["diff"]["stat"], "1 file changed")
        self.assertEqual(review["diff"]["files"], ["M src/app.py"])

    def test_log_tail_is_limited_to_200_lines(self):
        status, review = self.request(f"/api/remote/v1/attempts/{ATTEMPT_ID}/review")

        self.assertEqual(status, 200)
        lines = review["logTail"].splitlines()
        self.assertEqual(len(lines), 200)
        self.assertEqual(lines[0], "agent-line-6")

    def test_secret_values_are_filtered_from_every_returned_text_section(self):
        status, review = self.request(f"/api/remote/v1/attempts/{ATTEMPT_ID}/review")

        self.assertEqual(status, 200)
        serialized = json.dumps(review)
        for secret in ("example-gateway-secret", "example-telegram-secret", "example-session-secret"):
            self.assertNotIn(secret, serialized)
        self.assertIn("[REDACTED]", serialized)
        self.assertNotIn("supervisor text must stay private", serialized)


if __name__ == "__main__":
    unittest.main()
