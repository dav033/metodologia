"""HTTP contract tests for remote failure reviews and redaction."""
from __future__ import annotations

import hashlib
import http.client
import json
import os
import sqlite3
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
import bt_live_api
import bt_remote_api
from bt_server import RemoteHandler

KEY = "test-gateway-key-0123456789"
ATTEMPT = "att-review-1"
SECRET_ASSIGNMENTS = (
    'FLOW_GATEWAY_KEY="example-gateway-value"',
    "TELEGRAM_BOT_TOKEN='example-telegram-value'",
    "GITHUB_CLIENT_SECRET=example-github-value",
)


class RemoteReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.rdir = self.root / "demo" / "requirements" / "REQ-001-review"
        self.rdir.mkdir(parents=True)
        self.state = self.root / ".state"
        scheduler_dir = self.state / "scheduler"
        scheduler_dir.mkdir(parents=True)
        run_db = scheduler_dir / "demo-REQ-001.db"
        runtime_id = "a" * 32
        run_db.with_name(run_db.stem + "-runtime.json").write_text(
            json.dumps({"runtime_id": runtime_id}), encoding="utf-8")
        self.m6 = self.state / "scheduler" / f"{run_db.stem}-{runtime_id}-modules" / "m6-quality.sqlite3"
        self.m6.parent.mkdir(parents=True)
        self._write_quality_fixture()
        self.attempt_dir = self._write_executor_fixture(run_db.stem)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), RemoteHandler)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.patches = [
            patch.object(bt_live_api, "runs", return_value=[("demo", self.rdir)]),
            patch("bt_attempt_facts.attempt_facts", return_value={"T1": [{
                "attempt": ATTEMPT, "task": "T1", "state": "rejected", "failure": "verification_rejected",
                "verdict": "rejected", "verifier": "m6-quality/checker-v1",
            }]}),
            patch.dict(os.environ, {"FLOW_GATEWAY_KEY": KEY}),
        ]
        for item in self.patches:
            item.start()
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        for item in reversed(self.patches):
            item.stop()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp.cleanup()

    def _write_quality_fixture(self):
        stdout = ("verification output\n" + "\n".join(SECRET_ASSIGNMENTS)).encode()
        stderr = b""
        stdout_ref = "m6://artifact/" + hashlib.sha256(stdout).hexdigest()
        stderr_ref = "m6://artifact/" + hashlib.sha256(stderr).hexdigest()
        result = {"checks": [{"command": "python -m unittest", "exit_code": 1,
                              "stdout_ref": stdout_ref, "stderr_ref": stderr_ref}]}
        with sqlite3.connect(self.m6) as connection:
            connection.executescript("CREATE TABLE requests(request_json TEXT, result_json TEXT);"
                                     "CREATE TABLE artifacts(digest TEXT, content BLOB);")
            connection.execute("INSERT INTO requests VALUES(?,?)",
                               (json.dumps({"attempt_id": ATTEMPT}), json.dumps(result)))
            for reference, content in ((stdout_ref, stdout), (stderr_ref, stderr)):
                connection.execute("INSERT INTO artifacts VALUES(?,?)", (reference.rsplit("/", 1)[-1], content))

    def _write_executor_fixture(self, stem: str) -> Path:
        executor_root = self.state / "executor" / f"{stem}-r1-deadbeef-123"
        attempts = executor_root / "attempts"
        attempt_dir = attempts / "attempt-fixture"
        handoff = attempt_dir / "handoff"
        handoff.mkdir(parents=True)
        with sqlite3.connect(executor_root / "ledger.db") as connection:
            connection.execute("CREATE TABLE attempts(attempt_id TEXT, dirname TEXT, request TEXT)")
            connection.execute("INSERT INTO attempts VALUES(?,?,?)",
                               (ATTEMPT, "attempt-fixture", json.dumps({"attempt_id": ATTEMPT})))
        (attempt_dir / "output.tail").write_text(
            "supervisor-only-marker\n" + "\n".join(f"agent-line-{i}" for i in range(205)) +
            "\n" + "\n".join(SECRET_ASSIGNMENTS), encoding="utf-8")
        (attempt_dir / "supervisor.log").write_text("must never be returned", encoding="utf-8")
        (handoff / "manifest.json").write_text(json.dumps({"changed_total": 1, "changed": ["M src/app.py"]}),
                                               encoding="utf-8")
        (handoff / "changes.patch").write_text(
            "diff --git a/src/app.py b/src/app.py\nindex 1111111..2222222 100644\n"
            "--- a/src/app.py\n+++ b/src/app.py\n@@ -1 +1,2 @@\n-old\n+new\n+added\n", encoding="utf-8")
        return attempt_dir

    def request(self, path: str):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=3)
        connection.request("GET", path, headers={"Authorization": f"Bearer {KEY}"})
        response = connection.getresponse()
        status, body = response.status, response.read()
        connection.close()
        return status, json.loads(body)

    def test_failure_review_returns_frontend_sections_from_attempt_evidence_and_caps_agent_log(self):
        status, review = self.request(f"/api/remote/v1/attempts/{ATTEMPT}/review")

        self.assertEqual(status, 200)
        self.assertEqual(set(review), {"attemptId", "cause", "verification", "diff", "logTail"})
        self.assertEqual(review["cause"], "verification_rejected")
        self.assertEqual(review["verification"]["command"], "python -m unittest")
        self.assertIn("verification output", review["verification"]["output"])
        self.assertTrue(review["diff"]["stat"])
        self.assertEqual(review["diff"]["files"], ["M src/app.py"])
        lines = review["logTail"].splitlines()
        self.assertEqual(len(lines), 200)
        self.assertEqual(lines[0], "agent-line-8")
        self.assertNotIn("supervisor-only-marker", review["logTail"])
        self.assertNotIn("must never be returned", json.dumps(review))
        self.assertNotIn("example-gateway-value", json.dumps(review))
        self.assertNotIn("example-telegram-value", json.dumps(review))
        self.assertNotIn("example-github-value", json.dumps(review))

    def test_snapshot_and_event_failure_text_is_redacted_at_the_http_boundary(self):
        with patch.object(bt_remote_api, "_snapshot_runs", return_value=[{"failure": " ".join(SECRET_ASSIGNMENTS)}]), \
                patch.object(bt_remote_api, "_plans", return_value=[]):
            status, snapshot = self.request("/api/remote/v1/snapshot")
        self.assertEqual(status, 200)
        self.assertNotIn("example-gateway-value", json.dumps(snapshot))
        self.assertNotIn("example-telegram-value", json.dumps(snapshot))
        self.assertNotIn("example-github-value", json.dumps(snapshot))

        with patch("bt_live_api.flow_events", return_value=([{
            "id": "event-1", "remote_type": "attempt.failed", "ord": "1", "at": "now",
            "run": "demo/REQ-001", "data": {"failure": " ".join(SECRET_ASSIGNMENTS)},
        }], {}, {})), patch.object(bt_remote_api, "_plans", return_value=[]):
            status, events = self.request("/api/remote/v1/events")
        self.assertEqual(status, 200)
        serialized = json.dumps(events)
        self.assertNotIn("example-gateway-value", serialized)
        self.assertNotIn("example-telegram-value", serialized)
        self.assertNotIn("example-github-value", serialized)


if __name__ == "__main__":
    unittest.main()
