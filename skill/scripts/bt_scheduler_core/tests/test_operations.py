"""Operator operations and the meaning of 'finished' (SC-AC17): pause, cancel, reopen; run status; the loop sleeps."""
from __future__ import annotations

import sys
import threading
import time
import unittest
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2])]

from support import Harness, indep

import bt_scheduler_core as sc


class Status(unittest.TestCase):
    def test_completed_only_when_every_task_is_completed(self):
        h = Harness([indep("T1"), indep("T2")], parallel=2)
        h.core.step()
        h.finish_and_accept("T1")
        self.assertEqual(h.core.snapshot().status, "running")
        h.finish_and_accept("T2")
        self.assertEqual(h.core.snapshot().status, "completed")

    def test_no_ready_tasks_is_not_success(self):                           # SC-AC17
        h = Harness([indep("T1"), indep("T2", ["T1"]), indep("T3")], parallel=3)
        h.core.step()
        h.send("T1", "execution_failed")
        h.core.step()
        h.finish_and_accept("T3")
        snap = h.core.snapshot()
        self.assertEqual(snap.status, "blocked")
        self.assertEqual(snap.attention, ({"kind": "blocked_task", "task_id": "T1", "reason": "attempts_exhausted"},))
        self.assertEqual(h.core.run(idle_timeout=1).status, "blocked")       # run() returns instead of waiting forever

    def test_paused_is_not_completed(self):
        h = Harness([indep("T1")])
        h.core.pause("owner")
        self.assertEqual(h.core.snapshot().status, "paused")

    def test_cancelled_run_is_not_completed_and_keeps_finished_work(self):
        h = Harness([indep("T1"), indep("T2", ["T1"])])
        h.core.step()
        h.finish_and_accept("T1")
        h.core.step()
        h.core.cancel("owner", "no longer needed")
        self.assertEqual(h.core.snapshot().status, "running")               # T2 is still active: waiting for the executor
        h.send("T2", "execution_cancelled")
        snap = h.core.snapshot()
        self.assertEqual((snap.status, snap.tasks["T1"]["state"], snap.tasks["T2"]["state"]), ("cancelled", "completed", "cancelled"))

    def test_a_run_whose_every_task_completed_before_cancel_stays_completed(self):
        h = Harness([indep("T1")])
        h.core.step()
        h.finish_and_accept("T1")
        h.core.cancel("owner")
        self.assertEqual(h.core.snapshot().status, "completed")


class Cancel(unittest.TestCase):
    def test_unstarted_work_is_cancelled_at_once_and_running_work_gets_a_cancel_order(self):
        h = Harness([indep("T1"), indep("T2", ["T1"]), indep("T3"), indep("T4")], parallel=2)
        h.core.step()                                                       # T1, T3 active; T4 ready; T2 pending
        h.core.cancel("owner")
        self.assertEqual(h.states(), {"T1": "active", "T2": "cancelled", "T3": "active", "T4": "cancelled"})
        h.core.step()
        self.assertEqual(sorted(o.attempt_id for o in h.executor.cancelled.values()), sorted([h.attempt("T1"), h.attempt("T3")]))
        self.assertEqual(h.core.claim(sc.Assignment("T4", "x")).reason, "cancel_requested")

    def test_an_attempt_not_yet_sent_is_cancelled_without_ever_reaching_the_executor(self):
        h = Harness([indep("T1")])
        h.core.claim(sc.Assignment("T1", "local"))
        h.core.cancel("owner")
        h.core.step()
        self.assertEqual(h.executor.deliveries, {})
        self.assertEqual((h.state("T1"), h.core.snapshot().status), ("cancelled", "cancelled"))

    def test_cancellation_is_resolved_by_reconciliation_when_the_event_is_lost(self):
        h = Harness([indep("T1")])
        h.core.step()
        h.core.cancel("owner")
        h.executor.status[h.attempt("T1")] = sc.ExecutionStatus("cancelled")
        h.clock.advance(1000)
        h.core.step()
        self.assertEqual(h.core.snapshot().status, "cancelled")

    def test_work_that_finishes_and_verifies_despite_the_cancel_is_kept(self):
        h = Harness([indep("T1")])
        h.core.step()
        h.core.cancel("owner")
        h.send("T1", "execution_finished")
        h.verdict("T1")
        self.assertEqual(h.state("T1"), "completed")


class Authorisation(unittest.TestCase):
    def test_every_operator_action_needs_a_named_authority_and_is_audited(self):
        h = Harness([indep("T1")])
        for action in (h.core.pause, h.core.resume, h.core.cancel):
            with self.assertRaises(sc.SchedulerError) as cm:
                action("")
            self.assertEqual(cm.exception.code, "NOT_ALLOWED")
        h.core.pause("david", "meeting")
        row = next(e for e in h.core.audit_log() if e.kind == "run_paused")
        self.assertEqual((row.detail["by"], row.detail["reason"]), ("david", "meeting"))

    def test_reopen_only_applies_to_blocked_tasks_of_a_live_run(self):
        h = Harness([indep("T1"), indep("T2")], parallel=2)
        h.core.step()
        for tid in ("T1", "ghost"):
            with self.assertRaises(sc.SchedulerError) as cm:
                h.core.reopen(tid, "owner")
            self.assertIn(cm.exception.code, ("NOT_ALLOWED", "UNKNOWN_TASK"))
        h.finish_and_accept("T2")
        with self.assertRaises(sc.SchedulerError):
            h.core.reopen("T2", "owner")                                     # completed is terminal

    def test_reopen_after_cancel_is_refused(self):
        h = Harness([indep("T1")])
        h.core.step()
        h.send("T1", "execution_failed")
        h.core.step()
        h.core.cancel("owner")
        with self.assertRaises(sc.SchedulerError):
            h.core.reopen("T1", "owner")


class Loop(unittest.TestCase):
    def test_run_drives_a_plan_to_completion_when_the_world_answers(self):
        from bt_scheduler_core.simulation import simulate
        h = Harness([indep("T1"), indep("T2", ["T1"]), indep("T3")], parallel=2)
        snap, _core = simulate(h.plan, sc.InMemoryRepository(), sc.Config(max_parallel_tasks=2))
        self.assertEqual(snap.status, "completed")

    def test_an_idle_run_sleeps_instead_of_spinning(self):
        h = Harness([indep("T1")])
        steps = []
        original = h.core.step
        h.core.step = lambda: (steps.append(1), original())[1]
        started = time.monotonic()
        snap = h.core.run(idle_timeout=0.3)
        elapsed = time.monotonic() - started
        self.assertEqual(snap.status, "running")
        self.assertGreaterEqual(elapsed, 0.25)
        self.assertLessEqual(len(steps), 4, f"{len(steps)} steps in {elapsed:.2f}s: that is polling")

    def test_an_event_from_another_thread_wakes_the_loop_immediately(self):
        h = Harness([indep("T1")], config=sc.Config(reconcile_seconds=60, lease_seconds=3600))
        h.core.step()

        def feed():
            time.sleep(0.2)
            h.send("T1", "execution_finished")
            time.sleep(0.2)
            h.verdict("T1")

        thread = threading.Thread(target=feed)
        started = time.monotonic()
        thread.start()
        snap = h.core.run(idle_timeout=20)
        thread.join()
        self.assertEqual(snap.status, "completed")
        self.assertLess(time.monotonic() - started, 5)                      # woken by the events, not by the 60 s deadline

    def test_run_honours_max_steps_and_stop(self):
        h = Harness([indep("T1")])
        self.assertEqual(h.core.run(max_steps=1).status, "running")
        self.assertEqual(h.core.run(stop=lambda: True).status, "running")

    def test_config_is_validated(self):
        for bad in ({"max_parallel_tasks": 0}, {"max_attempts": 0}, {"lease_seconds": 0}, {"repository_isolation": "x"},
                    {"unknown_surface": "x"}, {"max_parallel_tasks": True}, {"reconcile_seconds": -1}):
            with self.subTest(bad=bad), self.assertRaises(sc.SchedulerError) as cm:
                sc.Config(**bad)
            self.assertEqual(cm.exception.code, "CONFIG_INVALID")


if __name__ == "__main__":
    unittest.main()
