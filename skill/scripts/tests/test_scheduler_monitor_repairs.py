import hashlib
import json
import sqlite3
import tempfile
import unittest
from contextlib import closing, nullcontext
from pathlib import Path
from unittest.mock import patch

import bt_scheduler_monitor_repairs as repairs


class MonitorRepairsTests(unittest.TestCase):
    def test_failure_requires_matching_attempt_and_integrity_checked_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "m6.db"
            content = "locator.fill: Timeout 30000ms exceeded. getByLabel('Contraseña nueva')".encode()
            digest = hashlib.sha256(content).hexdigest()
            result = {"status": "FAIL", "identity": {"attempt_id": "att-0076"}, "checks": [
                {"status": "fail", "command": "npm run cuentas:test-integracion-ui", "stderr_ref": "m6://artifact/" + digest}]}
            raw = json.dumps(result)
            with closing(sqlite3.connect(path)) as db:
                db.execute("CREATE TABLE requests(idempotency_key TEXT, result_json TEXT, result_hash TEXT)")
                db.execute("CREATE TABLE artifacts(digest TEXT, content BLOB)")
                db.execute("INSERT INTO requests VALUES(?,?,?)", ("req", raw, hashlib.sha256(raw.encode()).hexdigest()))
                db.execute("INSERT INTO artifacts VALUES(?,?)", (digest, content))
                db.commit()
            with patch.object(repairs.bt_run_stores, "paths", return_value={"m6": path}):
                self.assertTrue(repairs.activation_failure(Path(tmp), "req", "att-0076"))
                self.assertFalse(repairs.activation_failure(Path(tmp), "req", "att-older"))
                with closing(sqlite3.connect(path)) as db:
                    db.execute("UPDATE artifacts SET content=?", (b"changed",))
                    db.commit()
                self.assertFalse(repairs.activation_failure(Path(tmp), "req", "att-0076"))

    def test_only_retries_new_verified_failure_when_no_work_is_live(self):
        state = {"revision": 13, "tasks": {"T2.6": {"state": "blocked", "attempts": ["att-0076"]}}}
        idle = {"owner_pids": [], "live_attempts": [], "hold": False}
        cards = [{"id": "T2.6:19", "task": "T2.6", "source": "task"}]
        with tempfile.TemporaryDirectory() as tmp, patch.object(repairs.decisions, "_state", return_value=state), \
             patch.object(repairs, "activation_failure", return_value=True) as evidence, \
             patch.object(repairs.decisions, "open_requests", return_value=cards), \
             patch.object(repairs.decisions, "answers_path", return_value=Path(tmp) / "answers"), \
             patch.object(repairs.ops, "hold", return_value=nullcontext("token")), patch.object(repairs.ops, "owns_hold", return_value=True), \
             patch.object(repairs.ops, "status", return_value=idle), patch.object(repairs.decisions, "answer") as answer:
            root = Path(tmp)
            self.assertIsNone(repairs.repair_once("pictures", "REQ-021", root, {**idle, "live_attempts": [1]}))
            evidence.assert_not_called()
            self.assertIn("reopened once", repairs.repair_once("pictures", "REQ-021", root, idle))
            answer.assert_called_once()
            (root / "answers").write_text(repairs.MARKER)
            self.assertIsNone(repairs.repair_once("pictures", "REQ-021", root, idle))
            answer.assert_called_once()

    def test_does_not_interrupt_an_owner_that_starts_during_recheck(self):
        state = {"revision": 13, "tasks": {"T2.6": {"state": "blocked", "attempts": ["att-0076"]}}}
        with tempfile.TemporaryDirectory() as tmp, patch.object(repairs.decisions, "_state", return_value=state), \
             patch.object(repairs, "activation_failure", return_value=True), \
             patch.object(repairs.decisions, "answers_path", return_value=Path(tmp) / "answers"), \
             patch.object(repairs.decisions, "open_requests", return_value=[{"id": "T2.6:19", "task": "T2.6", "source": "task"}]), \
             patch.object(repairs.ops, "hold", return_value=nullcontext("token")), patch.object(repairs.ops, "owns_hold", return_value=True), \
             patch.object(repairs.ops, "status", return_value={"owner_pids": [123], "live_attempts": []}), \
             patch.object(repairs.decisions, "answer") as answer:
            self.assertIsNone(repairs.repair_once("pictures", "REQ-021", Path(tmp), {"owner_pids": [], "live_attempts": []}))
            answer.assert_not_called()
