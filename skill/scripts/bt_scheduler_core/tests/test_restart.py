"""Restart and reconciliation (SC-AC13, SC-AC15): crash at every critical transition and at every single commit,
then restart on the same store; never two writers, never a false completion, never a death inferred from a heartbeat."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2])]

from support import Harness, indep, sqlite_path

import bt_scheduler_core as sc

Crash = sc.FakeExecutor.Crash
TASKS = [indep("T1"), indep("T2", ["T1"]), indep("T3")]


def ev(h, tid, kind):
    """Idempotent: fixed event id, so re-issuing after a crash is harmless (at-least-once world)."""
    return lambda: h.core.ingest(h.ev(tid, kind, event_id=f"fixed-{tid}-{kind}"))


def accept(h, tid):
    return lambda: h.core.submit_verdict(sc.Verdict(f"fixed-vd-{tid}", "REQ-T", 1, tid, h.attempt(tid), True, "validator",
                                                    "ok", h.token(h.attempt(tid))))


def actions(h):
    return [lambda: h.core.step(), ev(h, "T1", "execution_started"), ev(h, "T1", "execution_finished"),
            lambda: h.core.step(), accept(h, "T1"), lambda: h.core.step(), ev(h, "T3", "execution_finished"),
            lambda: h.core.step(), accept(h, "T3"), ev(h, "T2", "execution_finished"), lambda: h.core.step(),
            accept(h, "T2"), lambda: h.core.step()]


def check_outcome(test, h):
    test.assertEqual(h.states(), {"T1": "completed", "T2": "completed", "T3": "completed"})
    test.assertEqual(h.core.snapshot().status, "completed")
    for tid in ("T1", "T2", "T3"):
        test.assertEqual(h.core.read(lambda c, t=tid: len(c.state.tasks[t].attempts)), 1, f"{tid}: a second attempt appeared")
    starts = [n for k, n in h.executor.deliveries.items() if k.endswith(":start")]
    test.assertEqual(starts, [1, 1, 1], "an order reached the executor more than once")
    test.assertEqual(len(h.executor.started), 3)
    # verification requests are idempotent by key: a lost ack may repeat one (acknowledged as duplicate), never create two
    test.assertEqual(len(h.verifier.requests), 3)
    test.assertTrue(all(1 <= n <= 2 for n in h.verifier.deliveries.values()), h.verifier.deliveries)
    seqs = [e.seq for e in h.core.audit_log()]
    test.assertEqual(seqs, list(range(1, len(seqs) + 1)))


class EveryCriticalTransition(unittest.TestCase):
    def matrix(self, make_repo):
        total = len(actions(Harness(TASKS, parallel=3)))
        for k in range(total + 1):
            with self.subTest(restart_before_action=k):
                h = Harness(TASKS, repository=make_repo(), parallel=3)
                script = actions(h)
                for action in script[:k]:
                    action()
                h.crash()
                script = actions(h)
                for action in script[k:]:
                    action()
                check_outcome(self, h)

    def test_memory_store(self):
        self.matrix(sc.InMemoryRepository)

    def test_sqlite_store_reopened_by_a_fresh_connection(self):
        tmp, path = sqlite_path()
        self.addCleanup(tmp.cleanup)
        counter = iter(range(1000))

        def make():
            n = next(counter)
            return sc.SqliteRepository(path.with_name(f"run{n}.db"))
        self.matrix(make)


class EverySingleCommit(unittest.TestCase):
    """Kill the process at the commit point of the n-th transaction (the commit is lost), restart, and re-issue the
    interrupted action like an at-least-once world would. The end result must be the same for every n."""

    def run_with_crash_at(self, n: int):
        h = Harness(TASKS, parallel=3)
        counter = {"n": 0, "armed": True}

        def before_commit():
            counter["n"] += 1
            if counter["armed"] and counter["n"] == n:
                counter["armed"] = False
                raise Crash()

        h.repo.before_commit = before_commit
        index = 0
        crashed = False
        while index < len(actions(h)):
            try:
                actions(h)[index]()
                index += 1
            except Crash:
                crashed = True
                h.crash()
        return h, crashed

    def test_losing_any_one_commit_never_breaks_the_outcome(self):
        probe = Harness(TASKS, parallel=3)
        counter = {"n": 0}
        probe.repo.before_commit = lambda: counter.__setitem__("n", counter["n"] + 1)
        for action in actions(probe):
            action()
        commits = counter["n"]
        self.assertGreater(commits, 20)
        crashed_any = 0
        for n in range(1, commits + 1):
            with self.subTest(lost_commit=n):
                h, crashed = self.run_with_crash_at(n)
                crashed_any += crashed
                check_outcome(self, h)
        self.assertGreater(crashed_any, 15)


class Reconciliation(unittest.TestCase):
    def running(self):
        h = Harness([indep("T1"), indep("T3")], parallel=2)
        h.core.step()
        h.send("T1", "execution_started")
        return h

    def test_an_old_heartbeat_or_lapsed_lease_never_declares_an_attempt_dead(self):     # SC-AC15
        h = self.running()
        att = h.attempt("T1")
        h.clock.advance(10_000)
        h.core.step()
        self.assertEqual(h.core.snapshot().tasks["T1"]["attempt_state"], "running")    # executor says running
        self.assertEqual(h.core.read(lambda c: len(c.state.tasks["T1"].attempts)), 1)
        self.assertEqual(h.attempt("T1"), att)
        self.assertIn("lease_expired", h.audit_kinds())
        self.assertIn("reconciled", h.audit_kinds())

    def test_a_lease_that_lapses_without_a_port_is_flagged_not_acted_upon(self):
        h = self.running()
        core = sc.SchedulerCore(h.plan, h.repo, clock=h.clock)                         # no execution port
        h.clock.advance(10_000)
        core.step()
        self.assertEqual(core.snapshot().tasks["T1"]["attempt_state"], "running")

    def test_the_executor_that_never_heard_of_a_running_attempt_makes_it_lost_and_the_task_recovers(self):
        h = self.running()
        h.executor.status.pop(h.attempt("T1"))
        h.crash()
        snap = h.core.snapshot().tasks["T1"]
        self.assertEqual(snap["attempt_state"], "failed")
        self.assertEqual(h.core.read(lambda c: c.state.tasks["T1"].reason), "lost")
        self.assertIn(snap["state"], ("recovering", "blocked"))

    def test_unavailable_executor_at_restart_makes_running_attempts_uncertain_and_others_keep_going(self):
        h = self.running()
        h.executor.unavailable = True
        h.crash()
        snap = h.core.snapshot()
        self.assertEqual(snap.tasks["T1"]["attempt_state"], "uncertain")
        self.assertEqual(snap.tasks["T3"]["attempt_state"], "uncertain")               # equally unknown
        self.assertEqual(h.core.read(lambda c: sorted(c.state.holds)), sorted([h.attempt("T1"), h.attempt("T3")]))
        # an event still reaches a task whose attempt is uncertain and resolves it
        self.assertEqual(h.send("T1", "execution_finished").status, "applied")
        self.assertEqual(h.core.snapshot().tasks["T1"]["attempt_state"], "verifying")

    def test_a_port_that_is_not_ready_at_restart_leaves_running_attempts_running_and_asks_again(self):
        h = self.running()
        h.executor.not_ready = True
        h.crash()
        snap = h.core.snapshot()
        self.assertEqual(snap.tasks["T1"]["attempt_state"], "running")                 # not «uncertain»: nothing was observed
        self.assertTrue(h.core.read(lambda c: c.state.attempts[h.attempt("T1")].needs_reconcile))
        h.executor.not_ready = False
        h.core.step()
        self.assertEqual(h.core.snapshot().tasks["T1"]["attempt_state"], "running")
        self.assertFalse(h.core.read(lambda c: c.state.attempts[h.attempt("T1")].needs_reconcile))
        self.assertNotIn("port_error", h.audit_kinds())

    def test_uncertainty_resolves_when_the_executor_answers_again(self):
        h = self.running()
        h.executor.unavailable = True
        h.crash()
        h.executor.unavailable = False
        h.clock.advance(1000)
        h.core.step()
        self.assertEqual(h.core.snapshot().tasks["T1"]["attempt_state"], "running")

    def test_manual_resolution_of_an_uncertain_attempt_is_authorised_and_audited(self):
        h = self.running()
        h.executor.unavailable = True
        h.crash()
        with self.assertRaises(sc.SchedulerError):
            h.core.resolve_attempt(h.attempt("T1"), "failed", by="")
        h.core.resolve_attempt(h.attempt("T1"), "failed", by="david", reason="host was rebooted")
        row = next(e for e in h.core.audit_log() if e.kind == "attempt_resolved_manually")
        self.assertEqual((row.detail["by"], row.detail["outcome"]), ("david", "failed"))
        self.assertEqual(h.core.snapshot().tasks["T1"]["attempt_state"], "failed")

    def test_only_uncertain_attempts_stall_run_so_an_operator_can_step_in(self):
        h = Harness([indep("T1")])
        h.core.step()
        h.send("T1", "execution_started")
        h.executor.unavailable = True
        h.crash()
        snap = h.core.run(idle_timeout=5)
        self.assertEqual(snap.tasks["T1"]["attempt_state"], "uncertain")

    def test_restart_keeps_every_confirmed_decision(self):
        h = self.running()
        before = h.core.read(lambda c: c.state.to_dict())
        h.crash()
        after = h.core.read(lambda c: c.state.to_dict())
        for key in ("tasks", "holds", "seen_events", "plan_sha256"):
            self.assertEqual(after[key], before[key], key)
        for att, rec in before["attempts"].items():           # identity is kept; only knowledge may advance (asked, not assumed)
            for field in ("id", "task_id", "number", "token", "executor", "key"):
                self.assertEqual(after["attempts"][att][field], rec[field], field)
        self.assertEqual(sorted(after["attempts"]), sorted(before["attempts"]))


class BindingAfterRestart(unittest.TestCase):
    def test_a_persisted_run_of_another_revision_or_hash_is_refused_and_left_untouched(self):
        h = Harness([indep("T1")])
        h.core.step()
        before = (h.core.read(lambda c: c.state.to_dict()), len(h.core.audit_log()))
        for kwargs in ({"revision": 2}, {"plan_id": "REQ-OTHER"}):
            other = Harness([indep("T1")], repository=sc.InMemoryRepository(), **kwargs)
            with self.assertRaises(sc.SchedulerError) as cm:
                sc.SchedulerCore(other.plan, h.repo, clock=h.clock).start()
            self.assertEqual(cm.exception.code, "PLAN_MISMATCH")
        changed = Harness([indep("T1", risk="high")])
        with self.assertRaises(sc.SchedulerError) as cm:
            sc.SchedulerCore(changed.plan, h.repo, clock=h.clock).start()
        self.assertEqual(cm.exception.code, "PLAN_MISMATCH")
        self.assertEqual((h.core.read(lambda c: c.state.to_dict()), len(h.core.audit_log())), before)

    def test_inspect_is_read_only(self):
        h = Harness([indep("T1")])
        before = (h.core.read(lambda c: c.state.to_dict()), len(h.core.audit_log()))
        h.core.inspect()
        self.assertEqual((h.core.read(lambda c: c.state.to_dict()), len(h.core.audit_log())), before)


if __name__ == "__main__":
    unittest.main()
