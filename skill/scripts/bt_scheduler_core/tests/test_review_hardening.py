from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bt_scheduler_core as sc
from bt_scheduler_core.contracts import ExecutionStatus
from bt_scheduler_core.recovery import apply_observation, apply_recovery, attempts_used, pending
from support import approved, indep, plan_text


def test_plan():
    return approved(plan_text([indep("T1")]))[0]


class RecoveryHardening(unittest.TestCase):
    def test_blocked_environment_is_structured_and_m5_retry_cannot_consume_attempt_budget(self):
        class Blocked:
            def start(self, _order):
                return sc.Ack("rejected", "ordinary informational text", True, classification="blocked_environment")
            def cancel(self, _order):
                return sc.Ack("accepted")
            def query(self, _attempt_id):
                return sc.ExecutionStatus("not_found")

        core = sc.SchedulerCore(test_plan(), sc.InMemoryRepository(), ports=sc.Ports(execution=Blocked()))
        core.start()
        core.step()
        core.write(lambda ctx: apply_recovery(ctx, pending(ctx)[0], sc.RecoveryProposal("retry", "M5 retry")))
        attempt = core.read(lambda ctx: ctx.state.attempts[ctx.state.tasks["T1"].attempts[-1]])
        self.assertEqual(core.snapshot().tasks["T1"]["state"], "blocked")
        self.assertEqual(attempt.failure_classification, "blocked_environment")
        self.assertFalse(attempt.budget_consumed)

    def test_free_text_markers_do_not_classify_blocked_environment(self):
        class TextOnly:
            def start(self, _order):
                return sc.Ack("rejected", "COMPOSITION_BASE_MISSING: [blocked-environment]")
            def cancel(self, _order):
                return sc.Ack("accepted")
            def query(self, _attempt_id):
                return sc.ExecutionStatus("not_found")

        core = sc.SchedulerCore(test_plan(), sc.InMemoryRepository(), ports=sc.Ports(execution=TextOnly()))
        core.start()
        core.step()
        attempt = core.read(lambda ctx: ctx.state.attempts[ctx.state.tasks["T1"].attempts[-1]])
        self.assertEqual(attempt.failure_classification, "")
        self.assertTrue(attempt.budget_consumed)
        self.assertEqual(core.snapshot().tasks["T1"]["state"], "recovering")

    def test_schema_seven_attempts_upgrade_with_empty_classification(self):
        core = sc.SchedulerCore(test_plan(), sc.InMemoryRepository())
        core.start()
        core.claim(sc.Assignment("T1", "worker"))
        state = core.read(lambda ctx: ctx.state)
        old = state.to_dict()
        old["schema"] = 7
        for attempt in old["attempts"].values():
            attempt.pop("failure_classification", None)
        restored = sc.RunState.from_dict(old)
        attempt = next(iter(restored.attempts.values()))
        self.assertEqual(restored.schema, 8)
        self.assertEqual(attempt.failure_classification, "")

    def test_reconciled_execution_consumes_budget_when_start_ack_was_lost(self):
        for reported in ("running", "finished", "failed"):
            core = sc.SchedulerCore(test_plan(), sc.InMemoryRepository())
            core.start()
            core.claim(sc.Assignment("T1", "worker"))
            attempt_id = core.snapshot().tasks["T1"]["attempt"]
            core.write(lambda ctx, state=reported, aid=attempt_id: apply_observation(
                ctx, aid, ExecutionStatus(state, "M3 status")))
            self.assertEqual(core.read(lambda ctx: attempts_used(ctx.state, "T1")), 1, reported)

    def test_m1_blocks_a_resumed_hold_when_m6_resume_is_exhausted(self):
        core = sc.SchedulerCore(test_plan(), sc.InMemoryRepository())
        core.start()
        core.claim(sc.Assignment("T1", "worker"))
        attempt_id = core.snapshot().tasks["T1"]["attempt"]
        core.ingest(sc.Event("finished", core.plan.plan_id, core.plan.revision, "T1", attempt_id, "worker",
                             "execution_finished"))
        core.step()
        identity = {"plan_id": core.plan.plan_id, "revision": core.plan.revision, "task_id": "T1",
                    "attempt_id": attempt_id, "token": 1}
        self.assertEqual(core.handle_needs_review(**identity, evidence_ref="m6://result/" + "a" * 64,
                                                  advice_port=lambda _case: "resume"), "resumed")
        self.assertEqual(core.block_exhausted_needs_review_resume(identity), "blocked")
        self.assertEqual(core.snapshot().tasks["T1"]["state"], "blocked")
        self.assertEqual(core.read(lambda ctx: ctx.state.review_holds[attempt_id]["state"]), "blocked")


if __name__ == "__main__":
    unittest.main()
