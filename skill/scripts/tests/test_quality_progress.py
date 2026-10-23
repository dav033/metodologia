"""Operator status reads check activity without granting verdict authority."""
from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bt_run_stores
import bt_scheduler_adapter as adapter
from bitacora_platform import quality_progress, scheduler_status


class QualityProgressTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.rdir = Path(self.temp.name) / "REQ-001-x"
        self.rdir.mkdir()
        db = adapter.run_db_path(self.rdir)
        with sqlite3.connect(db) as conn:
            conn.execute("CREATE TABLE state(id INTEGER, doc TEXT)")
            conn.execute("INSERT INTO state VALUES (1, ?)", (json.dumps({"revision": 1,
                "attempts": {"att-0001": {"id": "att-0001", "task_id": "T1", "state": "verifying"}},
                "tasks": {"T1": {"state": "active"}}}),))
        bt_run_stores.runtime_marker(db).write_text(json.dumps({"runtime_id": "a" * 32}))
        self.store = bt_run_stores.paths(self.rdir)["m6"]

    def test_status_reports_elapsed_output_age_and_owner_liveness(self):
        journal = quality_progress.ProgressJournal(self.store)
        with patch("time.time", return_value=100):
            journal.observe("att-0001", "CHECK-002", "running", 0)
        with patch("time.time", return_value=102):
            journal.observe("att-0001", "CHECK-002", "running", 30)
        with patch("time.time", return_value=105):
            result = scheduler_status.status(self.rdir, [os.getpid()], [], False)
        info = result["live_attempts"][0]["verification"]
        self.assertEqual(info, {"check": "CHECK-002", "phase": "running", "elapsed_seconds": 5,
                               "heartbeat_age_seconds": 3, "last_output_age_seconds": 3, "owner_alive": True})
        self.assertEqual(result["task_states"], {"T1": "active"})
        self.assertEqual(os.stat(quality_progress.directory(self.store) / "att-0001.json").st_mode & 0o777, 0o600)
        with patch("time.time", return_value=106):
            info = scheduler_status.status(self.rdir, [], [], False)["live_attempts"][0]["verification"]
        self.assertFalse(info["owner_alive"])

    def test_missing_or_corrupt_progress_does_not_hide_the_run(self):
        self.assertNotIn("verification", scheduler_status.status(self.rdir, [], [], False)["live_attempts"][0])
        root = quality_progress.directory(self.store)
        root.mkdir(parents=True)
        (root / "att-0001.json").write_text("broken")
        result = scheduler_status.status(self.rdir, [], [], False)
        self.assertEqual(result["live_attempts"][0]["verification_progress_error"], "JSONDecodeError")
        self.assertEqual(result["task_states"], {"T1": "active"})

    def test_finished_check_stops_elapsed_time_and_next_check_resets_it(self):
        journal = quality_progress.ProgressJournal(self.store)
        for now, check, phase, size in [(100, "CHECK-001", "running", 0), (101, "CHECK-001", "running", 10),
                                         (102, "CHECK-001", "finished", 0)]:
            with patch("time.time", return_value=now):
                journal.observe("att-0001", check, phase, size)
        with patch("time.time", return_value=105):
            self.assertEqual(scheduler_status.status(self.rdir, [], [], False)["live_attempts"][0]["verification"]["elapsed_seconds"], 2)
            journal.observe("att-0001", "CHECK-002", "running", 0)
        with patch("time.time", return_value=107):
            info = scheduler_status.status(self.rdir, [], [], False)["live_attempts"][0]["verification"]
        self.assertEqual(info["elapsed_seconds"], 2)
        self.assertIsNone(info["last_output_age_seconds"])
