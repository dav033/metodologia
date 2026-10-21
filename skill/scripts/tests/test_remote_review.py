"""HTTP tests for run-scoped failure review evidence."""
from __future__ import annotations

import http.client
import hashlib
import json
import os
import sqlite3
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

import bt_core
import bt_live_api
import bt_server

TEST_KEY = "test-only-review-key"
ATTEMPT_ID = "att-0001"


class RemoteReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.patches = [
            patch.object(bt_core, "ROOT", self.root),
            patch.dict(os.environ, {"FLOW_GATEWAY_KEY": TEST_KEY}),
        ]
        for active in self.patches:
            active.start()
            self.addCleanup(active.stop)
        bt_live_api._runs_seen.clear()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), bt_server.RemoteHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def create_failed_run(self, req: str, cause: str, log_lines: list[str]) -> None:
        project_dir = self.root / "demo"
        rdir = project_dir / "requirements" / f"{req}-fixture"
        rdir.mkdir(parents=True)
        (rdir / "PLAN.md").write_text(f"# Plan — {req} — Fixture\n", encoding="utf-8")
        db = self.root / ".state" / "scheduler" / f"demo-{req}.db"
        db.parent.mkdir(parents=True, exist_ok=True)
        document = {
            "tasks": {"T1": {"attempts": [ATTEMPT_ID]}},
            "attempts": {ATTEMPT_ID: {
                "id": ATTEMPT_ID, "task_id": "T1", "number": 1, "state": "failed",
                "created_at": 1_800_000_000, "updated_at": 1_800_000_010, "failure": cause,
            }},
        }
        with sqlite3.connect(db) as connection:
            connection.execute("CREATE TABLE state (id INTEGER PRIMARY KEY, version INTEGER NOT NULL, doc TEXT NOT NULL)")
            connection.execute("INSERT INTO state VALUES (1, 1, ?)", (json.dumps(document),))

        runtime_id = "a" * 32
        db.with_name(db.stem + "-runtime.json").write_text(json.dumps({"runtime_id": runtime_id}), encoding="utf-8")
        quality_db = db.parent / f"{db.stem}-{runtime_id}-modules" / "m6-quality.sqlite3"
        quality_db.parent.mkdir(parents=True)
        output = "verification output TOKEN=verification-secret-value"
        digest = hashlib.sha256(output.encode("utf-8")).hexdigest()
        result = {"checks": [{"command": "python -m unittest", "exit_code": 1,
                              "stdout_ref": f"m6://artifact/{digest}"}]}
        with sqlite3.connect(quality_db) as connection:
            connection.execute("CREATE TABLE requests (idempotency_key TEXT, request_json TEXT, result_json TEXT, created_at TEXT)")
            connection.execute("CREATE TABLE artifacts (digest TEXT, content BLOB)")
            connection.execute("INSERT INTO requests VALUES (?, ?, ?, ?)",
                               ("verify-1", json.dumps({"attempt_id": ATTEMPT_ID}), json.dumps(result), "now"))
            connection.execute("INSERT INTO artifacts VALUES (?, ?)", (digest, output.encode("utf-8")))

        executor_root = self.root / ".state" / "executor" / f"demo-{req}-r1"
        attempts_dir = executor_root / "attempts" / "attempt-one"
        (attempts_dir / "handoff").mkdir(parents=True)
        (attempts_dir / "handoff" / "manifest.json").write_text(
            json.dumps({"changed_total": 2, "changed": ["fixture.py"]}), encoding="utf-8")
        with sqlite3.connect(executor_root / "ledger.db") as connection:
            connection.execute("CREATE TABLE attempts (attempt_id TEXT, dirname TEXT, request TEXT)")
            connection.execute("INSERT INTO attempts VALUES (?, ?, ?)",
                               (ATTEMPT_ID, "attempt-one", json.dumps({"attempt_id": ATTEMPT_ID})))
        (attempts_dir / "output.tail").write_text("\n".join(log_lines), encoding="utf-8")

    def get_review(self, target: str, attempt: str = ATTEMPT_ID):
        connection = http.client.HTTPConnection(*self.server.server_address, timeout=3)
        path = f"/api/remote/v1/attempts/{attempt}/review?target={target}"
        connection.request("GET", path, headers={"Authorization": f"Bearer {TEST_KEY}"})
        response = connection.getresponse()
        result = response.status, json.loads(response.read())
        connection.close()
        return result

    def test_real_http_entrypoint_returns_selected_run_and_four_review_sections(self):
        self.create_failed_run("REQ-001", "first run failure", ["one"])
        self.create_failed_run("REQ-002", "selected run failure", ["two"])

        status, review = self.get_review("demo%2FREQ-002")

        self.assertEqual(status, 200)
        self.assertEqual(review["cause"], "selected run failure")
        self.assertEqual(set(review), {"attemptId", "cause", "verification", "diff", "logTail"})
        self.assertEqual(review["attemptId"], ATTEMPT_ID)
        self.assertEqual(review["verification"], {
            "command": "python -m unittest", "output": "verification output TOKEN=[REDACTED]"})
        self.assertEqual(review["diff"]["stat"], "2 files changed")
        self.assertEqual(review["diff"]["files"], ["fixture.py"])

    def test_log_tail_is_limited_to_200_lines_and_returned_text_is_redacted(self):
        log_lines = [f"line-{number}" for number in range(250)]
        log_lines[210] = "FLOW_GATEWAY_KEY=fixture-secret-value"
        self.create_failed_run("REQ-003", "failure TOKEN=another-secret-value", log_lines)

        status, review = self.get_review("demo%2FREQ-003")

        self.assertEqual(status, 200)
        returned_lines = review["logTail"].splitlines()
        self.assertEqual(len(returned_lines), 200)
        self.assertEqual(returned_lines[0], "line-50")
        returned_text = json.dumps(review)
        self.assertNotIn("fixture-secret-value", returned_text)
        self.assertNotIn("another-secret-value", returned_text)
        self.assertNotIn("verification-secret-value", returned_text)
        self.assertIn("[REDACTED]", returned_text)

    def test_attempt_must_exist_in_the_selected_run_and_target_must_be_present(self):
        self.create_failed_run("REQ-004", "failure", ["log"])

        status, _ = self.get_review("demo%2FREQ-005")
        self.assertEqual(status, 404)

        connection = http.client.HTTPConnection(*self.server.server_address, timeout=3)
        connection.request("GET", f"/api/remote/v1/attempts/{ATTEMPT_ID}/review",
                           headers={"Authorization": f"Bearer {TEST_KEY}"})
        response = connection.getresponse()
        body = json.loads(response.read())
        connection.close()
        self.assertEqual(response.status, 400)
        self.assertEqual(body["code"], "INVALID_TARGET")


if __name__ == "__main__":
    unittest.main()
