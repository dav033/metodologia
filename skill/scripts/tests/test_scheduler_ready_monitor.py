import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bt_scheduler_ready_monitor as monitor
from bt_scheduler_ready_monitor import ready_signature


class ReadyMonitorTests(unittest.TestCase):
    def test_only_recovers_unowned_ready_work_while_another_decision_waits(self):
        status = {"hold": False, "owner_pids": [], "live_attempts": [], "open_decisions": ["T1:1"],
                  "revision": 13, "task_states": {"T1": "blocked", "T2": "ready"}}
        state = {"tasks": {"T2": {"attempts": ["att-1"]}}}
        signature = ready_signature(status, state)
        self.assertIsNotNone(signature)
        self.assertEqual(signature, ready_signature(status, state))
        self.assertNotEqual(signature, ready_signature(status, {"tasks": {"T2": {"attempts": ["att-1", "att-2"]}}}))
        for changes in ({"hold": True}, {"owner_pids": [1]}, {"live_attempts": [1]}, {"open_decisions": []},
                        {"task_states": {"T1": "blocked"}}):
            self.assertIsNone(ready_signature({**status, **changes}, state))

    def test_recovery_is_recorded_and_not_repeated_for_unchanged_state(self):
        status = {"owner_pids": [], "live_attempts": [], "open_decisions": ["T1:1"], "revision": 13,
                  "task_states": {"T1": "blocked", "T2": "ready"}}
        state = {"tasks": {"T2": {"attempts": []}}}
        with tempfile.TemporaryDirectory() as tmp, patch.object(monitor.ops, "status", return_value=status), \
             patch.object(monitor.decisions, "_state", return_value=state), \
             patch.object(monitor.adapter, "run_db_path", return_value=Path(tmp) / "run.db"), \
             patch.object(monitor.subprocess, "run") as run:
            self.assertIn("started owner", monitor.start_once("pictures", "REQ-021", Path(tmp)))
            self.assertEqual(monitor.start_once("pictures", "REQ-021", Path(tmp)), "already attempted")
            run.assert_called_once()
