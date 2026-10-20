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


class Rework(unittest.TestCase):
    """An audit rejected work built on accepted tasks: the system sends them back, never completes anything itself."""

    def chain(self, **kw):
        h = Harness([indep("T1"), indep("T2", ["T1"]), indep("T3", ["T2"]), indep("T9")], parallel=2, max_attempts=2, **kw)
        h.core.step()
        h.finish_and_accept("T1")
        h.finish_and_accept("T2")
        h.core.step()
        return h

    def reject(self, h, tid, named, reason="F1 critical"):
        h.core.step()
        h.send(tid, "execution_finished")
        h.core.step()
        h.n += 1
        attempt = h.attempt(tid)
        verdict = sc.Verdict(f"vd-r{h.n}", h.plan.plan_id, h.plan.revision, tid, attempt, False, "validator",
                             "audit gate: open findings", h.token(attempt))
        return h.core.reject_and_rework(verdict, named, "audit-gate", reason)

    def states(self, h):
        return {tid: v["state"] for tid, v in h.core.snapshot().tasks.items()}

    def test_the_named_task_its_dependents_and_the_rejected_task_go_back(self):
        h = self.chain()
        result, moved = self.reject(h, "T3", ("T1",))
        self.assertEqual(result.status, "applied")
        self.assertEqual(moved, ("T1", "T2", "T3"))
        states = self.states(h)
        self.assertEqual((states["T1"], states["T2"], states["T3"]), ("ready", "pending", "pending"))
        self.assertIn("rework_requested", h.audit_kinds())

    def test_without_cascade_only_the_named_and_the_rejected_task_go_back(self):
        h = self.chain()
        h.core.step()
        h.send("T3", "execution_finished")
        h.core.step()
        h.n += 1
        attempt = h.attempt("T3")
        verdict = sc.Verdict("vd-nc", h.plan.plan_id, h.plan.revision, "T3", attempt, False, "validator", "audit gate",
                             h.token(attempt))
        result, moved = h.core.reject_and_rework(verdict, ("T1",), "audit-gate", "F1", cascade=False)
        self.assertEqual((result.status, moved), ("applied", ("T1", "T3")))
        states = self.states(h)
        # T3's direct prerequisite T2 is completed, but T1 above it is being redone: T3 waits for the whole chain
        self.assertEqual((states["T1"], states["T2"], states["T3"]), ("ready", "completed", "pending"))
        self.assertEqual(h.core.rework_scope(("T1",), ("T3",), cascade=False), ("T1", "T3"))
        self.assertEqual(h.core.rework_scope(("T1",), ("T3",)), ("T1", "T2", "T3"))
        event = [e for e in h.core.audit_log() if e.kind == "rework_requested"][-1]
        self.assertFalse(event.detail["cascade"])

    def test_the_operator_can_send_back_only_what_it_names(self):
        h = self.chain()
        self.assertEqual(h.core.rework(("T1",), "operator", "why", cascade=False), ("T1",))
        self.assertEqual(self.states(h)["T2"], "completed")

    def test_a_rework_can_be_taken_back_for_tasks_that_redid_nothing(self):
        h = self.chain()
        h.finish_and_accept("T3")
        h.core.rework(("T1",), "operator", "audit", cascade=True)
        self.assertEqual({t: s for t, s in self.states(h).items() if t != "T9"}, {"T1": "ready", "T2": "pending", "T3": "pending"})
        restored = h.core.withdraw_rework(("T2", "T3"), "operator", "keep the accepted results")
        self.assertEqual(restored, ("T2", "T3"))
        states = self.states(h)
        self.assertEqual((states["T1"], states["T2"], states["T3"]), ("ready", "completed", "completed"))
        self.assertIn("rework_withdrawn", h.audit_kinds())
        self.assertEqual(h.core.read(lambda c: c.state.tasks["T2"].reworks), 0)

    def test_taking_back_is_refused_when_work_was_redone_or_never_accepted_and_changes_nothing(self):
        h = self.chain()
        h.finish_and_accept("T3")
        h.core.rework(("T1",), "operator", "audit", cascade=True)
        h.core.step()                                                   # T1 starts again: it is being redone
        with self.assertRaises(sc.SchedulerError):
            h.core.withdraw_rework(("T1",), "operator", "no")
        with self.assertRaises(sc.SchedulerError):
            h.core.withdraw_rework(("T2", "T9"), "operator", "T9 never reworked")
        self.assertEqual(self.states(h)["T2"], "pending")                # all or nothing

    def test_a_task_sent_back_while_a_prerequisite_is_being_redone_waits_for_it(self):
        h = self.chain()
        h.finish_and_accept("T3")
        h.core.rework(("T1",), "operator", "audit", cascade=False)      # T1 pending/ready, T2 and T3 keep their results
        h.core.step()                                                    # T1 starts again
        self.assertEqual(self.states(h)["T3"], "completed")
        h.core.rework(("T3",), "operator", "again", cascade=False)       # T3 back to pending with T1 still being redone
        self.assertEqual(self.states(h)["T3"], "pending")

    def test_independent_branches_are_left_alone(self):
        h = self.chain()
        h.finish_and_accept("T9")
        self.reject(h, "T3", ("T1",))
        self.assertEqual(self.states(h)["T9"], "completed")

    def test_rework_gets_a_fresh_attempt_budget_and_is_completed_only_by_a_new_verdict(self):
        h = self.chain()
        self.reject(h, "T3", ("T2",))
        h.core.step()
        self.assertEqual(self.states(h)["T2"], "active")
        h.finish_and_accept("T2")
        self.assertEqual(self.states(h)["T2"], "completed")

    def test_the_limit_blocks_the_rejected_task_at_once_instead_of_burning_retries(self):
        h = Harness([indep("T1"), indep("T2", ["T1"])], parallel=1, max_attempts=3,
                    config=sc.Config(max_attempts=3, max_reworks=1))
        h.core.step()
        h.finish_and_accept("T1")
        h.core.step()
        result, moved = self.reject(h, "T2", ("T1",))
        self.assertEqual(moved, ("T1", "T2"))
        h.core.step()
        h.finish_and_accept("T1")
        h.core.step()
        result, moved = self.reject(h, "T2", ("T1",))
        self.assertEqual((result.status, moved), ("applied", ()))
        self.assertIn("rework_refused", h.audit_kinds())
        states = self.states(h)
        self.assertEqual((states["T1"], states["T2"]), ("completed", "blocked"))
        self.assertEqual(h.core.snapshot().tasks["T2"]["reason"], "rework_limit")

    def test_the_owner_may_rework_past_the_limit(self):
        h = Harness([indep("T1"), indep("T2", ["T1"])], parallel=1, max_attempts=3,
                    config=sc.Config(max_attempts=3, max_reworks=1))
        h.core.step()
        h.core.pause("owner")                                   # nothing new starts: T2 never gets a live attempt
        h.finish_and_accept("T1")
        self.assertEqual(h.core.rework(("T1",), "owner", "redo it"), ("T1", "T2"))
        h.core.resume("owner")
        h.core.step()
        h.core.pause("owner")
        h.finish_and_accept("T1")
        self.assertEqual(h.core.rework(("T1",), "owner", "and again"), ("T1", "T2"))   # past max_reworks
        self.assertEqual(self.states(h)["T1"], "ready")

    def test_a_live_attempt_in_scope_defers_the_whole_verdict(self):
        h = Harness([indep("T1"), indep("T2", ["T1"]), indep("T3", ["T1"])], parallel=2, max_attempts=2)
        h.core.step()
        h.finish_and_accept("T1")
        h.core.step()                                   # T2 and T3 are both active now
        result, moved = self.reject(h, "T2", ("T1",))
        self.assertEqual((result.status, moved), ("deferred", ()))
        self.assertTrue(result.reason.startswith("busy"))
        self.assertEqual(self.states(h)["T2"], "active")           # nothing was applied: M6 offers it again later
        self.assertEqual(self.states(h)["T1"], "completed")
        h.finish_and_accept("T3")
        h.core.step()
        result, moved = self.reject(h, "T2", ("T1",))
        self.assertEqual((result.status, moved), ("applied", ("T1", "T2", "T3")))

    def test_an_accepting_verdict_cannot_ask_for_rework(self):
        h = self.chain()
        h.core.step()
        h.send("T3", "execution_finished")
        h.core.step()
        attempt = h.attempt("T3")
        verdict = sc.Verdict("vd-ok", h.plan.plan_id, h.plan.revision, "T3", attempt, True, "validator", "ok", h.token(attempt))
        with self.assertRaises(sc.SchedulerError):
            h.core.reject_and_rework(verdict, ("T1",), "audit-gate")

    def test_the_same_verdict_twice_reworks_once(self):
        h = self.chain()
        h.core.step()
        h.send("T3", "execution_finished")
        h.core.step()
        attempt = h.attempt("T3")
        verdict = sc.Verdict("vd-dup", h.plan.plan_id, h.plan.revision, "T3", attempt, False, "validator", "bad", h.token(attempt))
        first = h.core.reject_and_rework(verdict, ("T1",), "audit-gate")
        second = h.core.reject_and_rework(verdict, ("T1",), "audit-gate")
        self.assertEqual((first[0].status, first[1]), ("applied", ("T1", "T2", "T3")))
        self.assertEqual((second[0].status, second[1]), ("duplicate", ()))

    def test_unknown_task_is_refused(self):
        h = self.chain()
        with self.assertRaises(sc.SchedulerError):
            self.reject(h, "T3", ("T404",))


class ReworkOfPairedAudits(unittest.TestCase):
    """Two audits that both reject must not wait for each other: the first rework supersedes the other's verdict wait."""

    def pair(self):
        h = Harness([indep("T1"), indep("A", ["T1"]), indep("B", ["T1"])], parallel=2, max_attempts=2)
        h.core.step()
        h.finish_and_accept("T1")
        h.core.step()                                  # A and B active
        h.send("A", "execution_finished")
        h.send("B", "execution_finished")
        h.core.step()                                  # both VERIFYING
        return h

    def reject(self, h, tid, vid):
        attempt = h.attempt(tid)
        return h.core.reject_and_rework(sc.Verdict(vid, h.plan.plan_id, h.plan.revision, tid, attempt, False,
                                                   "validator", "audit gate: open findings", h.token(attempt)),
                                        ("T1",), "audit-gate", "F1")

    def test_the_first_rejection_supersedes_the_other_audit_instead_of_deferring_forever(self):
        h = self.pair()
        first, moved = self.reject(h, "A", "vd-a")
        self.assertEqual((first.status, moved), ("applied", ("T1", "A", "B")))
        states = {t: v["state"] for t, v in h.core.snapshot().tasks.items()}
        self.assertEqual((states["A"], states["B"]), ("pending", "pending"))
        self.assertEqual(states["T1"], "ready")
        superseded = [e for e in h.core.audit_log() if e.kind == "attempt_transition" and e.task_id == "B"
                      and e.detail.get("to") == "cancelled"]
        self.assertEqual(len(superseded), 1)

    def test_the_late_verdict_of_the_superseded_audit_is_stale_not_applied(self):
        h = self.pair()
        self.reject(h, "A", "vd-a")
        late, moved = self.reject(h, "B", "vd-b")
        self.assertEqual((late.status, moved), ("stale", ()))

    def test_a_running_attempt_still_defers(self):
        h = Harness([indep("T1"), indep("A", ["T1"]), indep("B", ["T1"])], parallel=2, max_attempts=2)
        h.core.step()
        h.finish_and_accept("T1")
        h.core.step()
        h.send("A", "execution_finished")
        h.core.step()                                  # B is still running
        result, moved = self.reject(h, "A", "vd-a")
        self.assertEqual((result.status, moved), ("deferred", ()))
