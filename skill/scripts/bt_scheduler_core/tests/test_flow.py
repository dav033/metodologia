"""DAG, eligibility, parallelism and localised failure (SC-AC05, SC-AC06, SC-AC14, SC-AC17)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2])]

from support import Harness, indep, task

import bt_scheduler_core as sc


class Eligibility(unittest.TestCase):
    def test_dependent_waits_until_the_prerequisite_is_completed_and_verified(self):
        h = Harness([indep("T1"), indep("T2", ["T1"])])
        h.core.step()
        self.assertEqual(h.states(), {"T1": "active", "T2": "pending"})
        h.send("T1", "execution_finished")
        h.core.step()
        self.assertEqual(h.state("T2"), "pending")   # the agent said "done": not enough
        h.verdict("T1")
        self.assertEqual(h.state("T2"), "ready")     # unblocked by the accepted verdict itself
        h.core.step()
        self.assertEqual(h.state("T2"), "active")

    def test_a_rejected_verdict_does_not_unblock_dependents(self):
        h = Harness([indep("T1"), indep("T2", ["T1"])])
        h.core.step()
        h.send("T1", "execution_finished")
        h.verdict("T1", accepted=False)
        self.assertEqual((h.state("T1"), h.state("T2")), ("recovering", "pending"))

    def test_position_in_the_plan_or_milestone_creates_no_dependency(self):
        h = Harness([task("T9", milestone="M1", repo="a", paths=["a/**"]), indep("T1", milestone="M2"),
                     task("T5", milestone="M3", repo="c", paths=["c/**"])], parallel=3)
        h.core.step()
        self.assertEqual(set(h.states().values()), {"active"})

    def test_chain_fan_out_fan_in_and_diamond(self):
        tasks = [indep("A"), indep("B", ["A"]), indep("C", ["A"]), indep("D", ["B", "C"]), indep("E", ["D"])]
        h = Harness(tasks, parallel=4)
        order = []
        for _ in range(10):
            h.core.step()
            running = [t for t, s in h.states().items() if s == "active"]
            if not running:
                break
            order.append(sorted(running))
            for t in running:
                h.finish_and_accept(t)
        self.assertEqual(order, [["A"], ["B", "C"], ["D"], ["E"]])
        self.assertEqual(h.core.snapshot().status, "completed")

    def test_cross_milestone_dependency_is_just_an_edge(self):
        h = Harness([indep("T1", milestone="M2"), indep("T2", ["T1"], milestone="M1")])
        h.core.step()
        self.assertEqual(h.states(), {"T1": "active", "T2": "pending"})

    def test_partial_unblock_only_frees_tasks_whose_every_prerequisite_is_done(self):
        h = Harness([indep("A"), indep("B"), indep("C", ["A", "B"])])
        h.core.step()
        h.finish_and_accept("A")
        self.assertEqual(h.state("C"), "pending")
        h.finish_and_accept("B")
        self.assertIn(h.state("C"), ("ready", "active"))


class Parallelism(unittest.TestCase):
    def test_independent_tasks_run_together_up_to_the_configured_capacity(self):
        h = Harness([indep(f"T{i}") for i in range(1, 6)], parallel=3)
        h.core.step()
        self.assertEqual(sorted(h.states().values()), ["active"] * 3 + ["ready"] * 2)
        self.assertEqual(h.executor.running_attempts().__len__(), 3)

    def test_default_configuration_is_one_at_a_time(self):
        h = Harness([indep("T1"), indep("T2")], config=sc.Config())
        h.core.step()
        self.assertEqual(sorted(h.states().values()), ["active", "ready"])

    def test_a_freed_slot_is_refilled_on_the_next_step(self):
        h = Harness([indep(f"T{i}") for i in range(1, 4)], parallel=1)
        h.core.step()
        first = [t for t, s in h.states().items() if s == "active"]
        h.finish_and_accept(first[0])
        self.assertEqual(len([s for s in h.states().values() if s == "active"]), 1)
        self.assertEqual(h.state(first[0]), "completed")


class LocalisedFailure(unittest.TestCase):
    def build(self):
        h = Harness([indep("T1"), indep("T2", ["T1"]), indep("T3"), indep("T4", ["T3"]), indep("T5", ["T2"])], parallel=3)
        h.core.step()
        return h

    def test_a_failed_branch_does_not_stop_independent_branches(self):
        h = self.build()
        h.send("T1", "execution_failed", reason="boom")
        h.core.step()
        self.assertEqual(h.state("T1"), "blocked")        # budget of one attempt, no recovery module
        h.finish_and_accept("T3")
        h.core.step()
        h.finish_and_accept("T4")
        self.assertEqual((h.state("T3"), h.state("T4")), ("completed", "completed"))
        snap = h.core.snapshot()
        self.assertEqual(snap.unreachable, ("T2", "T5"))
        self.assertEqual(snap.status, "blocked")          # never "completed": two tasks cannot ever run

    def test_dependents_of_a_blocked_task_never_get_an_attempt(self):
        h = self.build()
        h.send("T1", "execution_failed")
        for _ in range(3):
            h.core.step()
        self.assertEqual(h.core.read(lambda c: c.state.tasks["T2"].attempts), [])

    def test_reopening_the_blocked_task_frees_its_dependents_again(self):
        h = self.build()
        h.send("T1", "execution_failed")
        h.core.step()
        h.core.reopen("T1", "owner", "fixed the cause")
        self.assertEqual(h.core.snapshot().unreachable, ())
        for tid in ("T1", "T2", "T5", "T3", "T4"):
            for _ in range(3):
                h.core.step()
                if h.state(tid) == "active":
                    h.finish_and_accept(tid)
        self.assertEqual(h.core.snapshot().status, "completed")


if __name__ == "__main__":
    unittest.main()
