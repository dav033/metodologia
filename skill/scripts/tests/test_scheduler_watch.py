"""The watchdog restarts a dead owner, backs off, honours a hold and the disk, and gives up on repeated failure."""
from __future__ import annotations

import signal
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import bt_scheduler_adapter as adapter
import bt_scheduler_ops as ops
import bt_scheduler_watch as watch


class FakeOwner:
    pid = 4242

    def __init__(self, code):
        self.code = code

    def poll(self):
        return self.code


class WatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.rdir = Path(self.temp.name) / "REQ-001-x"
        self.rdir.mkdir()
        self.clock = [0.0]
        self.sleeps: list[float] = []
        self.notes: list[str] = []
        self.logged: list[str] = []
        self.spawned: list[bool] = []
        self.codes: list[int] = []
        patcher = patch.object(adapter, "authority", return_value=adapter.AUTHORITY)
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch.object(ops, "owner_pids", return_value=[])
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch.object(adapter, "run_db_path", return_value=self.rdir / "SCHEDULER.db")
        patcher.start()
        self.addCleanup(patcher.stop)

    def watch(self, free=10 << 30, capture=lambda: "", heal=None):
        def sleep(seconds):
            self.sleeps.append(seconds)
            self.clock[0] += seconds

        def spawn(resume):
            self.spawned.append(resume)
            return FakeOwner(self.codes.pop(0))

        return watch.Watch("p", "REQ-001", self.rdir, now=lambda: self.clock[0], sleep=sleep, spawn=spawn,
                           free_bytes=lambda: free, notify=lambda title, text: self.notes.append(text), log=self.logged.append,
                           capture=capture, heal=heal)

    def test_terminal_run_ends_the_watch_without_restart(self):
        self.codes = [0]
        self.assertEqual(self.watch().run(), 0)
        self.assertEqual(self.spawned, [True])

    def test_the_healing_turn_runs_while_the_owner_waits_for_a_person(self):
        turns = []
        alive = [[1], [1], [1], [1], [1], [1], [1], []]                      # the owner is alive for 7 polls (35 s), then gone
        with patch.object(ops, "owner_pids", side_effect=lambda *a: alive.pop(0)):
            self.watch(heal=lambda: turns.append(self.clock[0]) or True)._wait_owner_gone()
        self.assertEqual(len(turns), 1)                                      # one turn after 30 s, none before

    def test_a_healing_turn_that_fails_while_waiting_does_not_stop_the_watch(self):
        def broken():
            raise RuntimeError("no env file")

        alive = [[1]] * 7 + [[]]
        with patch.object(ops, "owner_pids", side_effect=lambda *a: alive.pop(0)):
            self.watch(heal=broken)._wait_owner_gone()
        self.assertTrue(any("healing failed while the owner waits (RuntimeError" in line for line in self.logged))

    def test_a_finished_run_saves_its_replica_and_says_so(self):
        self.codes = [0]
        self.assertEqual(self.watch(capture=lambda: "replica of REQ-001 saved").run(), 0)
        self.assertIn("replica of REQ-001 saved", self.logged)

    def test_a_replica_that_cannot_be_saved_never_changes_how_the_run_ends(self):
        def broken():
            raise OSError("disk full")

        self.codes = [0]
        self.assertEqual(self.watch(capture=broken).run(), 0)
        self.assertTrue(any("replica not saved (OSError" in line for line in self.logged))

    def test_only_a_run_with_every_task_completed_is_captured(self):
        states = {"T1": "completed", "T2": "cancelled"}
        for given, expected in ((states, True), ({**states, "T3": "blocked"}, False), ({}, False)):
            with patch.object(ops, "status", return_value={"task_states": given}), \
                    patch("bt_scheduler_replica.extract", return_value={"recorded": {"attempts": 3}}) as extract:
                watcher = watch.Watch("p", "REQ-001", self.rdir.parent / "requirements" / "REQ-001-x")
                self.assertEqual(bool(watcher._capture()), expected)
                self.assertEqual(extract.called, expected)

    def test_an_audits_remediation_request_is_applied_and_the_owner_runs_again(self):
        import bt_remediation

        (self.rdir / bt_remediation.REQUEST).write_text("{}", encoding="utf-8")
        calls = []

        def apply(project, req, rdir, action, **kwargs):
            calls.append(action)
            (self.rdir / bt_remediation.REQUEST).unlink()
            return ["plan r8"]
        self.codes[:] = [0]
        with patch.object(ops, "apply", apply):
            self.assertEqual(self.watch().run(max_loops=3), 0)
        self.assertEqual(calls, ["remediate"])
        self.assertEqual(self.spawned, [True])                      # applied first, then the owner started on the new plan

    def test_a_remediation_that_fails_is_dropped_instead_of_looping(self):
        import bt_remediation

        (self.rdir / bt_remediation.REQUEST).write_text("{}", encoding="utf-8")

        def broken(*args, **kwargs):
            raise RuntimeError("no")
        self.codes[:] = [0]
        with patch.object(ops, "apply", broken):
            self.watch().run(max_loops=3)
        self.assertFalse(bt_remediation.requested(self.rdir))

    def card(self, **extra):
        base = {"id": "T9:5", "task": "T9", "options": [{"id": "retry"}, {"id": "rework_conflict"}, {"id": "stop"}],
                "diagnosis": {"kind": "conflict", "option": "rework_conflict", "confidence": "alta", "headline": "clash"}}
        return {**base, **extra}

    def test_a_plain_integration_clash_is_answered_by_the_scheduler_itself_a_bounded_number_of_times(self):
        import bt_scheduler_decisions as decisions

        answers = []

        def answer(project, req, rdir, request_id, option, reason="", by="owner"):
            answers.append((request_id, option, by))
            return [f"sent back for rework: T8a"]
        watcher = self.watch()
        with patch.object(decisions, "open_requests", return_value=[self.card()]), \
                patch.object(decisions, "answer", answer), patch.object(decisions, "automatic_answers", return_value=0):
            self.assertTrue(watcher.heal())
        self.assertEqual(answers, [("T9:5", "rework_conflict", "scheduler")])
        with patch.object(decisions, "open_requests", return_value=[self.card()]), \
                patch.object(decisions, "answer", answer), \
                patch.object(decisions, "automatic_answers", return_value=watch.HEAL_LIMIT):
            self.assertFalse(watcher.heal())                     # past the limit the card stays for a person
        self.assertEqual(len(answers), 1)

    def test_only_a_confident_clash_diagnosis_with_that_option_is_ever_answered_automatically(self):
        import bt_scheduler_decisions as decisions

        answers = []
        watcher = self.watch()
        others = [self.card(diagnosis={"kind": "code", "option": "retry_with_note", "confidence": "alta"}),
                  self.card(diagnosis={"kind": "conflict", "option": "rework_conflict", "confidence": "media"}),
                  self.card(diagnosis=None),
                  self.card(options=[{"id": "retry"}, {"id": "stop"}])]
        with patch.object(decisions, "open_requests", return_value=others), \
                patch.object(decisions, "answer", lambda *a, **k: answers.append(a) or []), \
                patch.object(decisions, "automatic_answers", return_value=0):
            self.assertFalse(watcher.heal())
        self.assertEqual(answers, [])

    def test_the_watchdog_advances_an_active_recovery_cycle_when_healing_has_nothing_to_do(self):
        import bt_recovery_pipeline
        import bt_scheduler_healing
        import bt_scheduler_decisions as decisions
        with patch.object(bt_scheduler_healing, "cycle", return_value=0), patch.object(decisions, "open_requests", return_value=[]), \
                patch.object(bt_recovery_pipeline, "advance", return_value=True) as advance:
            self.assertTrue(self.watch().heal())
        self.assertEqual(advance.call_args.args[:2], ("p", "REQ-001"))
        with patch.object(bt_scheduler_healing, "cycle", return_value=0), patch.object(decisions, "open_requests", return_value=[]), \
                patch.object(bt_recovery_pipeline, "advance", side_effect=RuntimeError("boom")):
            self.assertFalse(self.watch().heal())                                       # a failing cycle never stops the watch

    def test_a_failed_automatic_answer_leaves_the_card_for_a_person(self):
        import bt_scheduler_decisions as decisions

        def broken(*args, **kwargs):
            raise RuntimeError("no")
        with patch.object(decisions, "open_requests", return_value=[self.card()]), \
                patch.object(decisions, "answer", broken), patch.object(decisions, "automatic_answers", return_value=0):
            self.assertFalse(self.watch().heal())

    def test_crash_is_restarted_with_growing_backoff(self):
        self.codes = [3, -signal.SIGBUS, 0]
        self.assertEqual(self.watch().run(), 0)
        self.assertEqual(len(self.spawned), 3)
        self.assertEqual(self.sleeps, [watch.BACKOFF_START, watch.BACKOFF_START * 2])

    def test_repeated_crashes_give_up_and_notify(self):
        self.codes = [3] * 10
        self.assertEqual(self.watch().run(), 4)
        self.assertEqual(len(self.spawned), watch.MAX_FAILURES)
        self.assertEqual(len(self.notes), 1)

    def test_a_refusal_is_not_retried(self):
        self.codes = [2]
        self.assertEqual(self.watch().run(), 2)
        self.assertEqual(len(self.spawned), 1)
        self.assertEqual(len(self.notes), 1)

    def test_a_long_healthy_owner_resets_the_failure_budget(self):
        watcher = self.watch()
        times = iter(range(100))

        def spawn(resume):
            self.clock[0] += watch.HEALTHY_SECONDS + 1 if next(times) % 2 == 0 else 1
            return FakeOwner(self.codes.pop(0))

        watcher.spawn = spawn
        self.codes = [3] * 8 + [0]
        self.assertEqual(watcher.run(), 0)

    def test_sigterm_is_a_deliberate_stop_not_a_failure(self):
        self.codes = [-signal.SIGTERM, 0]
        watcher = self.watch()
        self.assertEqual(watcher.run(), 0)
        self.assertEqual(len(watcher.failures), 0)
        self.assertEqual(self.sleeps, [])

    def test_a_hold_pauses_the_restart(self):
        ops.hold_path(self.rdir).write_text("{}")
        watcher = self.watch()
        self.codes = [0]
        watcher.run(max_loops=2)
        self.assertEqual(self.spawned, [])
        ops.hold_path(self.rdir).unlink()
        self.assertEqual(watcher.run(max_loops=2), 0)
        self.assertEqual(self.spawned, [True])

    def test_low_disk_waits_and_tells_once(self):
        watcher = self.watch(free=1 << 20)
        self.codes = [0]
        watcher.run(max_loops=3)
        self.assertEqual(self.spawned, [])
        self.assertEqual(len(self.notes), 1)

    def test_a_first_start_is_not_a_resume(self):
        with patch.object(adapter, "authority", return_value="none"):
            self.codes = [0]
            self.watch().run()
        self.assertEqual(self.spawned, [False])

    def test_second_watchdog_exits_quietly(self):
        with watch.single_instance(self.rdir) as first:
            self.assertTrue(first)
            with watch.single_instance(self.rdir) as second:
                self.assertFalse(second)
            self.assertTrue(ops.watching(self.rdir))
        self.assertFalse(ops.watching(self.rdir))


class ArgvMatching(unittest.TestCase):
    def test_only_an_exact_owner_command_matches(self):
        run = ["/usr/bin/python3", "bitacora.py", "--project", "pictures", "scheduler-run", "REQ-019", "--resume"]
        self.assertTrue(ops._command_matches(run, "scheduler-run", "pictures", "REQ-019"))
        self.assertFalse(ops._command_matches(run, "scheduler-run", "pictures", "REQ-018"))
        self.assertFalse(ops._command_matches(run, "scheduler-run", "other", "REQ-019"))
        self.assertFalse(ops._command_matches(run, "scheduler-watch", "pictures", "REQ-019"))
        self.assertFalse(ops._command_matches(["vim", "bitacora.py", "--project", "pictures", "scheduler-run", "REQ-019"],
                                              "scheduler-run", "pictures", "REQ-019"))
        self.assertFalse(ops._command_matches(["tail", "-f", "scheduler-run", "REQ-019"],
                                              "scheduler-run", "pictures", "REQ-019"))


if __name__ == "__main__":
    unittest.main()
