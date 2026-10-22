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
        self.sch.rework_impact.return_value = ()

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

    def test_rework_sends_the_listed_tasks_back_through_m1(self):
        self.sch.rework.return_value = ("T1", "T2")
        lines = ops.apply("p", "REQ-001", self.rdir, "rework", "T1, T2", "audit found it")
        self.sch.rework.assert_called_once_with(("T1", "T2"), ops.OPERATOR, "audit found it", cascade=True, confirmed=True)
        self.assertIn("sent back for rework: T1, T2", lines)

    def test_withdraw_rework_takes_the_listed_tasks_back_through_m1(self):
        self.sch.withdraw_rework.return_value = ("T2",)
        lines = ops.apply("p", "REQ-001", self.rdir, "withdraw-rework", "T2", "keep it")
        self.sch.withdraw_rework.assert_called_once_with(("T2",), ops.OPERATOR, "keep it")
        self.assertTrue(any("T2" in line for line in lines))

    def test_continue_from_directs_the_next_start_of_one_task_and_checks_the_attempt(self):
        import json
        import tempfile
        from types import SimpleNamespace
        ctx = SimpleNamespace(state=SimpleNamespace(
            tasks={"T3": SimpleNamespace(state="pending", attempts=["att-1", "att-2"])},
            attempts={"att-1": SimpleNamespace(state="accepted"), "att-2": SimpleNamespace(state="accepted")}))
        sch = SimpleNamespace(read=lambda fn: fn(ctx))
        with tempfile.TemporaryDirectory() as tmp:
            line = ops.direct_continuation(Path(tmp), sch, "T3", "att-1")
            self.assertIn("att-1", line)
            self.assertEqual(json.loads((Path(tmp) / "RUN.continue.json").read_text()),
                             {"T3": {"attempt": "att-1", "attempts": 2}})
            with self.assertRaises(ops.core.SchedulerError):
                ops.direct_continuation(Path(tmp), sch, "T3", "att-9")        # not an attempt of the task
            with self.assertRaises(ops.core.SchedulerError):
                ops.direct_continuation(Path(tmp), sch, "T3", "")

    def test_rework_only_does_not_cascade(self):
        self.sch.rework.return_value = ("T1",)
        ops.apply("p", "REQ-001", self.rdir, "rework", "T1", "just this one", only=True)
        self.sch.rework.assert_called_once_with(("T1",), ops.OPERATOR, "just this one", cascade=False, confirmed=True)
        self.assertFalse(ops.on_hold(self.rdir))

    def test_rework_past_the_ceiling_is_refused_with_its_cost_until_the_owner_confirms(self):
        self.sch.rework_impact.return_value = ("T1", "T2", "T3", "T4")
        with patch("bt_rework_impact.ceiling", return_value=3), patch("bt_rework_impact.estimate",
                                                                    return_value={"tasks": ["T1", "T2", "T3", "T4"], "minutes": 95,
                                                                                  "recorded": 4}), \
                patch.object(ops, "bound_plan", return_value=None):
            with self.assertRaises(adapter.core.SchedulerError) as caught:
                ops.apply("p", "REQ-001", self.rdir, "rework", "T1", "everything")
            self.assertIn("4 accepted tasks", str(caught.exception))
            self.assertIn("95 minutes", str(caught.exception))
            self.assertIn("--confirm", str(caught.exception))
            self.sch.rework.assert_not_called()
            self.assertFalse(ops.on_hold(self.rdir))
            self.sch.rework.return_value = ("T1",)
            ops.apply("p", "REQ-001", self.rdir, "rework", "T1", "everything", confirm=True)
            self.sch.rework.assert_called_once()
            self.sch.rework_impact.return_value = ("T1", "T2", "T3")                 # at the ceiling: no confirmation needed
            ops.apply("p", "REQ-001", self.rdir, "rework", "T1", "three")

    def test_a_revision_that_would_redo_many_accepted_tasks_needs_the_owner_to_confirm(self):
        done = ("T1", "T2", "T3", "T4", "T5")
        with patch.object(ops, "_revise_impact", return_value=(6, done)), patch("bt_rework_impact.ceiling", return_value=3), \
                patch.object(ops, "bound_plan", return_value=None), patch("bt_rework_impact.estimate",
                                                                         return_value={"tasks": list(done), "minutes": 300,
                                                                                       "recorded": 5}), \
                patch.object(adapter, "rebase_to_latest") as rebase:
            with self.assertRaises(adapter.core.SchedulerError) as caught:
                ops.apply("p", "REQ-001", self.rdir, "revise")
            self.assertIn("revise r6", str(caught.exception))
            rebase.assert_not_called()
            self.assertEqual(self.calls, ["stop held=True"])                         # nothing was cancelled before the refusal

    def test_the_cost_is_the_recorded_minutes_of_the_accepted_attempts(self):
        import bt_rework_impact as impact
        db = self.rdir / "SCHEDULER.db"
        with contextlib.closing(sqlite3.connect(db)) as conn:
            conn.execute("CREATE TABLE audit (at REAL, kind TEXT, task_id TEXT, attempt_id TEXT, detail TEXT)")
            for at, kind, task, attempt, detail in ((0, "reserved", "T1", "a1", "{}"),
                                                    (600, "attempt_transition", "T1", "a1", '{"to": "accepted"}'),
                                                    (0, "reserved", "T2", "a2", "{}"),
                                                    (300, "attempt_transition", "T2", "a2", '{"to": "rejected"}')):
                conn.execute("INSERT INTO audit VALUES (?,?,?,?,?)", (at, kind, task, attempt, detail))
            conn.commit()
        cost = impact.estimate(db, ["T1", "T2"], SimpleNamespace(task=lambda t: SimpleNamespace(meta={"estimated_minutes": 60})))
        self.assertEqual((cost["minutes"], cost["recorded"]), (40, 1))                 # T1 recorded 10, T2 half of 60

    def test_revise_cancels_live_attempts_then_rebases(self):
        report = SimpleNamespace(from_revision=6, to_revision=7, kept=["T1"], reset=[], added=[], removed=[])
        with patch.object(adapter, "rebase_to_latest", return_value=report) as rebase, \
                patch("bt_scheduler_run.rebind_runtime") as rebind, patch.object(ops, "_revise_impact", return_value=(6, ())):
            lines = ops.apply("p", "REQ-001", self.rdir, "revise")
        self.assertEqual(self.calls, ["stop held=True", "kill att-0001"])
        rebase.assert_called_once_with(self.rdir)
        rebind.assert_called_once_with(self.rdir)
        self.assertTrue(any("r6 → r7" in line for line in lines))
        self.assertFalse(ops.on_hold(self.rdir))

    def test_a_move_rewrites_the_read_model_even_while_the_run_is_held(self):
        report = SimpleNamespace(from_revision=2, to_revision=3, kept=[], reset=["T3"], added=[], removed=[])
        with patch.object(adapter, "rebase_to_latest", return_value=report), patch("bt_scheduler_run.rebind_runtime"), \
                patch.object(adapter, "write_projection") as write, patch.object(ops, "_revise_impact", return_value=(2, ())):
            ops.apply("p", "REQ-001", self.rdir, "revise", keep_held=True)
        write.assert_called_once_with(self.rdir, self.sch)
        self.assertTrue(ops.on_hold(self.rdir))

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
                patch.object(ops, "apply", side_effect=lambda p, r, d, action, target, why, **kw: moves.append((action, target)) or [action]), \
                patch.object(ops.time, "sleep"):
            lines = ops.retry("p", "REQ-001", rdir, "T3", "why")
        self.assertEqual(moves, [("cancel-attempt", "att-0007"), ("reopen", "T3")])
        self.assertEqual(lines, ["cancel-attempt", "reopen"])

    def test_retry_accepts_a_task_already_ready_after_an_operator_reopen(self):
        with patch.object(ops, "status", return_value={"live_attempts": [], "blocked_tasks": [],
                                                         "task_states": {"T3": "ready"}}), \
                patch.object(ops, "apply") as apply, patch.object(ops.time, "sleep") as sleep:
            lines = ops.retry("p", "REQ-001", Path("/nonexistent"), "T3", "why")
        self.assertEqual(lines, ["T3: already ready"])
        apply.assert_not_called()
        sleep.assert_not_called()

    def test_retry_reopens_a_task_already_recovering_without_waiting_for_blocked(self):
        with patch.object(ops, "status", return_value={"live_attempts": [], "blocked_tasks": [],
                                                         "task_states": {"T3": "recovering"}}), \
                patch.object(ops, "apply", return_value=["reopen"]) as apply, patch.object(ops.time, "sleep") as sleep:
            lines = ops.retry("p", "REQ-001", Path("/nonexistent"), "T3", "why")
        apply.assert_called_once_with("p", "REQ-001", Path("/nonexistent"), "reopen", "T3", "why",
                                      expected_task="T3", expected_task_state=None)
        self.assertEqual(lines, ["reopen"])
        sleep.assert_not_called()


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
