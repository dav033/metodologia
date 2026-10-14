"""Boundaries with M2 (assignment) and M5 (recovery) (SC-AC16): advice is validated, failures never corrupt state,
no model is ever chosen by the core."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2])]

from support import Harness, indep

import bt_scheduler_core as sc


def failing(h, tid="T1"):
    h.core.step()
    h.send(tid, "execution_failed", reason="boom")


class DefaultPolicy(unittest.TestCase):
    def test_no_recovery_module_and_one_attempt_blocks_the_task(self):
        h = Harness([indep("T1")])
        failing(h)
        h.core.step()
        self.assertEqual((h.state("T1"), h.core.read(lambda c: c.state.tasks["T1"].reason)), ("blocked", "attempts_exhausted"))

    def test_without_a_module_the_budget_decides_how_many_attempts_run(self):
        h = Harness([indep("T1")], max_attempts=3)
        for expected in (1, 2, 3):
            h.core.step()
            h.core.step()
            self.assertEqual(h.core.read(lambda c: len(c.state.tasks["T1"].attempts)), expected)
            h.send("T1", "execution_failed")
        h.core.step()
        self.assertEqual(h.state("T1"), "blocked")

    def test_reopen_gives_a_fresh_budget(self):
        h = Harness([indep("T1")], max_attempts=1)
        failing(h)
        h.core.step()
        h.core.reopen("T1", "owner", "environment fixed")
        h.core.step()
        self.assertEqual(h.state("T1"), "active")
        self.assertEqual(h.core.read(lambda c: len(c.state.tasks["T1"].attempts)), 2)


class RecoveryAdvice(unittest.TestCase):
    def test_a_valid_retry_within_budget_is_applied_and_the_context_is_complete(self):
        rec = sc.ScriptedRecovery({"T1": sc.RecoveryProposal("retry", "flaky")})
        h = Harness([indep("T1")], max_attempts=2, recovery=rec)
        failing(h)
        h.core.step()
        ctx = rec.calls[0]
        self.assertEqual((ctx.task_id, ctx.cause, ctx.attempts_used, ctx.max_attempts, ctx.detail),
                         ("T1", "execution_failed", 1, 2, "boom"))
        self.assertEqual(h.state("T1"), "active")

    def test_a_retry_beyond_the_budget_is_refused_by_the_core(self):
        rec = sc.ScriptedRecovery({"T1": sc.RecoveryProposal("retry")})
        h = Harness([indep("T1")], max_attempts=1, recovery=rec)
        failing(h)
        h.core.step()
        self.assertEqual(h.state("T1"), "blocked")
        self.assertIn("recovery_refused", h.audit_kinds())

    def test_block_advice_is_applied_with_its_reason(self):
        h = Harness([indep("T1")], max_attempts=5, recovery=sc.ScriptedRecovery({"T1": sc.RecoveryProposal("block", "needs a human")}))
        failing(h)
        h.core.step()
        self.assertEqual((h.state("T1"), h.core.read(lambda c: c.state.tasks["T1"].reason)), ("blocked", "needs a human"))

    def test_wait_advice_holds_the_task_then_asks_again(self):
        answers = iter([sc.RecoveryProposal("wait", "cool down", 60), sc.RecoveryProposal("retry")])
        rec = sc.ScriptedRecovery(lambda ctx: next(answers))
        h = Harness([indep("T1")], max_attempts=2, recovery=rec)
        failing(h)
        h.core.step()
        self.assertEqual((h.state("T1"), len(rec.calls)), ("recovering", 1))
        h.core.step()
        self.assertEqual(len(rec.calls), 1)                      # not asked again during the hold
        h.clock.advance(61)
        h.core.step()
        self.assertEqual((len(rec.calls), h.state("T1")), (2, "active"))

    def test_waiting_is_capped(self):
        rec = sc.ScriptedRecovery({"T1": sc.RecoveryProposal("wait", "forever", 10 ** 9)})
        h = Harness([indep("T1")], recovery=rec, config=sc.Config(max_recovery_wait=100))
        failing(h)
        h.core.step()
        self.assertLessEqual(h.core.read(lambda c: c.state.tasks["T1"].hold_until) - h.clock(), 100)

    def test_invalid_advice_falls_back_to_the_deterministic_policy_and_is_noted(self):
        bad = [None, "retry", {"action": "retry"}, sc.RecoveryProposal("complete"), sc.RecoveryProposal("wait", "", -5),
               sc.RecoveryProposal("retry", 5), sc.RecoveryProposal("wait", "", True)]
        for advice in bad:
            with self.subTest(advice=advice):
                h = Harness([indep("T1")], max_attempts=2, recovery=sc.ScriptedRecovery(lambda ctx, a=advice: a))
                failing(h)
                h.core.step()
                self.assertEqual(h.state("T1"), "active")      # policy: retry while the budget lasts
                if advice is not None:
                    self.assertIn("port_invalid", h.audit_kinds())

    def test_a_crashing_recovery_module_does_not_stop_the_core(self):
        def boom(ctx):
            raise RuntimeError("M5 is down")
        h = Harness([indep("T1"), indep("T2")], max_attempts=2, recovery=sc.ScriptedRecovery(boom))
        h.core.step()
        h.send("T1", "execution_failed")
        h.core.step()
        self.assertIn("port_error", h.audit_kinds())
        self.assertEqual(h.state("T1"), "active")                # fallback policy
        self.assertEqual(h.state("T2"), "active")                # unrelated work is untouched

    def test_advice_cannot_complete_a_task_or_touch_another(self):
        rec = sc.ScriptedRecovery({"T1": sc.RecoveryProposal("complete")})
        h = Harness([indep("T1"), indep("T2")], recovery=rec)
        failing(h)
        h.core.step()
        self.assertNotEqual(h.state("T1"), "completed")
        self.assertEqual(h.state("T2"), "active")



class AssignmentAdvice(unittest.TestCase):
    class Port:
        def __init__(self, answer):
            self.answer, self.requests = answer, []

        def propose(self, request):
            self.requests.append(request)
            if isinstance(self.answer, Exception):
                raise self.answer
            return self.answer(request) if callable(self.answer) else self.answer

    def harness(self, answer, tasks=None):
        port = self.Port(answer)
        h = Harness(tasks or [indep("T1"), indep("T2", ["T1"]), indep("T3")], parallel=2)
        h.core = sc.SchedulerCore(h.plan, h.repo, config=h.config, clock=h.clock,
                                  ports=sc.Ports(assignment=port, execution=h.executor, verification=h.verifier))
        h.core.start()
        return h, port

    def test_the_port_only_sees_eligible_tasks_and_opaque_classification(self):
        h, port = self.harness(lambda r: [], [indep("T1", risk="high", complexity="extreme"), indep("T2", ["T1"])])
        h.core.step()
        request = port.requests[0]
        self.assertEqual([t.id for t in request.ready], ["T1"])
        self.assertEqual(request.free_slots, 2)
        self.assertEqual(request.ready[0].meta["risk"], "high")
        self.assertEqual(h.state("T1"), "ready")                 # an empty answer reserves nothing

    def test_the_executor_label_is_opaque_and_recorded_verbatim(self):
        h, _ = self.harness(lambda r: [sc.Assignment(t.id, "pool-7/slow lane") for t in r.ready])
        h.core.step()
        self.assertEqual(h.core.snapshot().tasks["T1"]["executor"], "pool-7/slow lane")

    def test_unavailable_or_garbage_answers_leave_the_state_intact(self):
        for answer in (RuntimeError("M2 down"), "T1", 5, [1, 2], [sc.Assignment("T1", "x"), "junk"], None):
            with self.subTest(answer=answer):
                h, _ = self.harness(answer)
                before = h.core.read(lambda c: (c.state.to_dict()["tasks"], c.state.holds))
                h.core.step()
                self.assertEqual(h.core.read(lambda c: (c.state.to_dict()["tasks"], c.state.holds)), before)
                self.assertTrue({"port_error", "port_invalid"} & set(h.audit_kinds()))

    def test_proposals_for_unknown_blocked_or_unready_tasks_and_over_capacity_are_refused(self):
        h, _ = self.harness(lambda r: [sc.Assignment("ghost", "x"), sc.Assignment("T2", "x"), sc.Assignment("T1", "x"),
                                       sc.Assignment("T1", "again"), sc.Assignment("T3", "x"), sc.Assignment("T3", "y")])
        h.core.step()
        self.assertEqual(h.states(), {"T1": "active", "T2": "pending", "T3": "active"})
        self.assertEqual(h.core.read(lambda c: len(c.state.attempts)), 2)

    def test_proposals_for_tasks_that_conflict_with_held_resources_are_refused(self):
        tasks = [indep("T1", resources=["db"]), indep("T3", resources=["db"])]
        h, _ = self.harness(lambda r: [sc.Assignment("T1", "x"), sc.Assignment("T3", "x")], tasks)
        h.core.step()
        self.assertEqual(sorted(h.states().values()), ["active", "ready"])

    def test_the_default_assignment_policy_is_plain_plan_order_with_no_intelligence(self):
        h = Harness([indep("B"), indep("A"), indep("C")], parallel=2)
        h.core.step()
        self.assertEqual(h.states(), {"B": "active", "A": "active", "C": "ready"})
        self.assertEqual({v["executor"] for v in h.core.snapshot().tasks.values() if v["executor"]}, {"local"})


if __name__ == "__main__":
    unittest.main()
