"""Offline regressions for T24 evidence attribution, scope and cancellation settlement."""
from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace

from scheduler_executor_support import make_repo
from scheduler_m2_live_experiment_support import (
    attempt_task_id,
    settle_after_stop,
    workspace_scope,
)


class T24EvidenceContracts(unittest.TestCase):
    def test_attempt_uses_nested_request_or_unique_m1_executor_binding(self):
        task_rows = {"T1": {"executor": "route:one"}, "T2": {"executor": "route:two"}}
        self.assertEqual(attempt_task_id({"request": {"task_id": "T1"}, "route": {"reference": "route:one"}}, task_rows), "T1")
        self.assertEqual(attempt_task_id({"request": {}, "route": {"reference": "route:two"}}, task_rows), "T2")
        self.assertIsNone(attempt_task_id({"request": {"task_id": "T1"}, "route": {"reference": "route:two"}}, task_rows))
        self.assertIsNone(attempt_task_id({"request": {}, "route": {"reference": "unknown"}}, task_rows))

    def test_duplicate_executor_binding_is_ambiguous(self):
        task_rows = {"T1": {"executor": "route:one"}, "T2": {"executor": "route:one"}}
        self.assertIsNone(attempt_task_id({"request": {}, "route": {"reference": "route:one"}}, task_rows))

    def test_workspace_scope_accepts_declared_files_only(self):
        with tempfile.TemporaryDirectory(prefix="req020-t24-scope-") as tmp_name:
            repo = make_repo(Path(tmp_name) / "project")
            expected = ("src/collapse_ws.py", "tests/test_t1.py")
            for relative in expected:
                path = repo / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("# evidence\n", encoding="utf-8")
            valid, changed, undeclared = workspace_scope(repo, expected)
            self.assertTrue(valid)
            self.assertEqual(set(changed), set(expected))
            self.assertEqual(undeclared, ())

    def test_workspace_scope_rejects_undeclared_changes(self):
        with tempfile.TemporaryDirectory(prefix="req020-t24-scope-") as tmp_name:
            repo = make_repo(Path(tmp_name) / "project")
            expected = ("src/collapse_ws.py", "tests/test_t1.py")
            for relative in (*expected, "notes.txt"):
                path = repo / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("# evidence\n", encoding="utf-8")
            valid, changed, undeclared = workspace_scope(repo, expected)
            self.assertFalse(valid)
            self.assertEqual(set(changed), {*expected, "notes.txt"})
            self.assertEqual(undeclared, ("notes.txt",))

    def test_cancellation_is_delivered_then_m1_is_stepped_to_terminal(self):
        class Scheduler:
            def __init__(self):
                self.steps = 0
                self.status = "running"

            def step(self):
                self.steps += 1
                if self.steps == 2:
                    self.status = "cancelled"

            def snapshot(self):
                return SimpleNamespace(status=self.status)

        class Executor:
            def __init__(self, scheduler):
                self.scheduler = scheduler
                self.timeouts = []

            def wait_idle(self, timeout=30.0):
                self.timeouts.append(timeout)
                return self.scheduler.steps == 1

        scheduler = Scheduler()
        executor = Executor(scheduler)
        idle, settled = settle_after_stop(scheduler, executor, time.monotonic() + 10.0)
        self.assertTrue(idle)
        self.assertTrue(settled)
        self.assertEqual(scheduler.steps, 2)
        self.assertEqual(len(executor.timeouts), 1)


if __name__ == "__main__":
    unittest.main()
