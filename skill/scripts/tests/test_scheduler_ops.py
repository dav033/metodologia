"""Operator moves: the owner is stopped under a hold, the move is applied through M1, the agent is killed."""
from __future__ import annotations

import contextlib
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import bt_core
import bt_scheduler_adapter as adapter
import bt_scheduler_ops as ops


class OpsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.rdir = Path(self.temp.name) / "REQ-001-x"
        self.rdir.mkdir()
        self.calls: list[str] = []
        self.sch = Mock()
        self.sch.resolve_attempt.return_value = "cancelled"
        self.sch.read.return_value = [("att-0001", "T1", "running")]

        def stop(project, req, **kw):
            self.calls.append(f"stop held={ops.on_hold(self.rdir)}")
            return 1

        @contextlib.contextmanager
        def opened(rdir):
            yield self.sch

        for target, value in (("run_db_path", self.rdir / "SCHEDULER.db"),):
            patcher = patch.object(adapter, target, return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)
        for name, new in (("stop_owner", stop), ("_opened", opened),
                          ("kill_agent", lambda p, r, a: self.calls.append(f"kill {a}") or 1)):
            patcher = patch.object(ops, name, new)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_cancel_attempt_stops_the_owner_under_a_hold_then_kills_the_agent(self):
        lines = ops.apply("p", "REQ-001", self.rdir, "cancel-attempt", "att-0001", "stuck")
        self.assertEqual(self.calls, ["stop held=True", "kill att-0001"])
        self.sch.resolve_attempt.assert_called_once_with("att-0001", "cancelled", ops.OPERATOR, "stuck")
        self.assertFalse(ops.on_hold(self.rdir))
        self.assertIn("att-0001: cancelled", lines)

    def test_reopen_goes_through_m1(self):
        ops.apply("p", "REQ-001", self.rdir, "reopen", "T3", "retry")
        self.sch.reopen.assert_called_once_with("T3", ops.OPERATOR, "retry")

    def test_revise_cancels_live_attempts_then_rebases(self):
        report = SimpleNamespace(from_revision=6, to_revision=7, kept=["T1"], reset=[], added=[], removed=[])
        with patch.object(adapter, "rebase_to_latest", return_value=report) as rebase, \
                patch("bt_scheduler_run.rebind_runtime") as rebind:
            lines = ops.apply("p", "REQ-001", self.rdir, "revise")
        self.assertEqual(self.calls, ["stop held=True", "kill att-0001"])
        rebase.assert_called_once_with(self.rdir)
        rebind.assert_called_once_with(self.rdir)
        self.assertTrue(any("r6 → r7" in line for line in lines))
        self.assertFalse(ops.on_hold(self.rdir))

    def test_a_refused_move_still_releases_the_hold(self):
        self.sch.reopen.side_effect = adapter.core.SchedulerError("NOT_ALLOWED", "no")
        with self.assertRaises(adapter.core.SchedulerError):
            ops.apply("p", "REQ-001", self.rdir, "reopen", "T3")
        self.assertFalse(ops.on_hold(self.rdir))

    def test_keep_held_leaves_the_run_stopped(self):
        ops.apply("p", "REQ-001", self.rdir, "reopen", "T3", keep_held=True)
        self.assertTrue(ops.on_hold(self.rdir))

    def test_unknown_action_is_refused(self):
        with self.assertRaises(adapter.core.SchedulerError):
            ops.apply("p", "REQ-001", self.rdir, "explode")


class RetryTests(unittest.TestCase):
    def test_retry_cancels_the_live_attempt_waits_for_the_block_and_reopens(self):
        rdir = Path("/nonexistent")
        views = iter([
            {"live_attempts": [{"attempt": "att-0007", "task": "T3"}], "blocked_tasks": []},
            {"live_attempts": [], "blocked_tasks": []},
            {"live_attempts": [], "blocked_tasks": ["T3"]},
        ])
        moves = []
        with patch.object(ops, "status", side_effect=lambda *a: next(views)), \
                patch.object(ops, "apply", side_effect=lambda p, r, d, action, target, why: moves.append((action, target)) or [action]), \
                patch.object(ops.time, "sleep"):
            lines = ops.retry("p", "REQ-001", rdir, "T3", "why")
        self.assertEqual(moves, [("cancel-attempt", "att-0007"), ("reopen", "T3")])
        self.assertEqual(lines, ["cancel-attempt", "reopen"])


class AgentKill(unittest.TestCase):
    def test_kill_agent_reads_every_revision_ledger_and_signals_shim_and_worktree(self):
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as tree:
            ledger = Path(root) / ".state" / "executor" / "p-REQ-001-r3-abc-1" / "ledger.db"
            ledger.parent.mkdir(parents=True)
            conn = sqlite3.connect(ledger)
            conn.execute("CREATE TABLE attempts (attempt_id TEXT, state TEXT, workspace TEXT, shim TEXT)")
            conn.execute("INSERT INTO attempts VALUES ('att-0001', 'running', ?, ?)",
                         (json.dumps({"path": tree}), json.dumps({"pid": 777, "pgid": 778})))
            conn.execute("INSERT INTO attempts VALUES ('att-0001', 'finished', ?, ?)",
                         (json.dumps({"path": "/nope"}), json.dumps({"pid": 1, "pgid": 1})))
            conn.commit()
            conn.close()
            with patch.object(bt_core, "ROOT", Path(root)), \
                    patch("bt_scheduler_executor.procinfo.signal_group") as group, \
                    patch("bt_scheduler_executor.procinfo.signal_pid") as pid, \
                    patch("bt_scheduler_executor.procinfo.kill_in_cwd", return_value=2) as cwd:
                hit = ops.kill_agent("p", "REQ-001", "att-0001")
        group.assert_called_once()
        pid.assert_called_once()
        cwd.assert_called_once_with(tree, 9)
        self.assertEqual(hit, 4)


if __name__ == "__main__":
    unittest.main()
