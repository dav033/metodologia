from __future__ import annotations

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import bt_scheduler_core as sc
from bt_scheduler_core.transitions import promote_ready
from support import approved, indep, plan_text


def make_plan():
    tasks = [
        {**indep("T1", kind="implement", subplan_id="SP-1",
                 verification=[{"type": "command", "value": "true", "category": "functional"}]),
         "acceptance_criteria": ["UI works"]},
        {**indep("T2", ["T1"], kind="test", subplan_id="SP-1",
                 verification=[{"type": "command", "value": "true", "category": "integration"}]),
         "acceptance_criteria": ["SP-1 works"]},
        {**indep("T3", ["T2"], kind="audit", subplan_id="SP-1",
                 verification=[{"type": "command", "value": "true", "category": "functional"}]),
         "acceptance_criteria": ["SP-1 audit passes"]},
        {**indep("T4", ["T3"], kind="test",
                 verification=[{"type": "command", "value": "true", "category": "integration"}]),
         "acceptance_criteria": ["Composition works"]},
        {**indep("T5", ["T4"], kind="test",
                 verification=[{"type": "command", "value": "true", "category": "functional"}]),
         "acceptance_criteria": ["T5 works"]},
        {**indep("T6", ["T4"], kind="test",
                 verification=[{"type": "command", "value": "true", "category": "functional"}]),
         "acceptance_criteria": ["T6 works"]},
    ]
    return approved(plan_text(tasks, schema_version="1.3.0", subplans=[{
        "id": "SP-1", "milestone_id": "M1", "title": "UI", "outcome": "UI works",
        "covers": ["R1"], "acceptance_criteria": ["UI works"],
        "produces": [{"contract": "customer-api", "version": 1, "defined_by": "T1", "interfaces": ["IF-1"]}],
        "consumes": [], "checkpoints": [], "integration_test_task": "T2", "audit_task": "T3",
        "ui": {"contract": "form", "version": 1, "design_task": "T1", "visual_review_task": "T3"},
    }], composition_gates=[{"id": "CG-1", "subplans": ["SP-1"], "task": "T4",
                            "criteria": ["Composition works"]}]))[0]


class CompositionHolds(unittest.TestCase):
    def test_hold_requires_a_declared_gate_and_a_bounded_reason(self):
        plan = make_plan()
        core = sc.SchedulerCore(plan, sc.InMemoryRepository())
        core.start()
        core.write(lambda ctx: setattr(ctx.state.tasks["T4"], "state", "completed"))
        for task_id, composition_id, reason in (("T5", "C1", "bad gate"), ("T4", "C1", "  "),
                                                 ("T4", "C1", "x" * 501)):
            with self.subTest(task_id=task_id, reason_length=len(reason)):
                with self.assertRaises(sc.SchedulerError):
                    core.hold_composition_gate(task_id, composition_id, reason)
        self.assertEqual(core.read(lambda ctx: ctx.state.composition_holds), {})
        self.assertNotIn("composition_gate_held", [row.kind for row in core.audit_log()])

    def test_hold_demotes_and_survives_until_matching_publication(self):
        plan = make_plan()
        repo = sc.InMemoryRepository()
        core = sc.SchedulerCore(plan, repo)
        core.start()
        for task_id in ("T1", "T2", "T3"):
            self._accept(core, plan, task_id)
        core.record_subplan_version("SP-1", 1, "a" * 40, "b" * 64)
        core.write(lambda ctx: (setattr(ctx.state.tasks["T4"], "state", "completed"),
                                setattr(ctx.state.tasks["T5"], "state", "ready"),
                                setattr(ctx.state.tasks["T6"], "state", "ready")))
        reserved = core.claim(sc.Assignment("T6", "fake"))
        self.assertEqual(core.read(lambda ctx: ctx.state.attempts[reserved.attempt_id].state), "reserved")

        core.hold_composition_gate("T4", "C1", "proof mismatch")
        self.assertEqual(core.snapshot().tasks["T5"]["state"], "pending")
        self.assertEqual(core.snapshot().tasks["T6"]["state"], "pending")
        self.assertEqual(core.read(lambda ctx: ctx.state.attempts[reserved.attempt_id].state), "cancelled")
        held_count = sum(row.kind == "composition_gate_held" for row in core.audit_log())
        core.hold_composition_gate("T4", "C1", "proof mismatch")
        self.assertEqual(sum(row.kind == "composition_gate_held" for row in core.audit_log()), held_count)

        resumed = sc.SchedulerCore(plan, repo)
        resumed.start()
        self.assertEqual(resumed.read(lambda ctx: ctx.state.composition_holds["T4"]["composition_id"]), "C1")
        self.assertEqual(resumed.snapshot().tasks["T5"]["state"], "pending")
        resumed.record_composition("candidate", "C1", {"SP-1": 1}, "c" * 64)
        resumed.record_composition("published", "C1", {"SP-1": 1}, "c" * 64, tree_digest="d" * 40)
        self.assertNotIn("T4", resumed.read(lambda ctx: ctx.state.composition_holds))
        self.assertEqual(resumed.snapshot().tasks["T4"]["state"], "completed")
        self.assertEqual(resumed.write(promote_ready), 2)
        self.assertEqual(resumed.snapshot().tasks["T5"]["state"], "ready")
        self.assertEqual(resumed.snapshot().tasks["T6"]["state"], "ready")

    @staticmethod
    def _accept(core, plan, task_id):
        core.claim(sc.Assignment(task_id, "fake"))
        attempt = core.snapshot().tasks[task_id]["attempt"]
        core.ingest(sc.Event(f"e-{task_id}-{attempt}", plan.plan_id, plan.revision, task_id, attempt,
                             "fake", "execution_finished"))
        core.step()
        core.submit_verdict(sc.Verdict(f"v-{task_id}-{attempt}", plan.plan_id, plan.revision, task_id,
                                       attempt, True, "validator", "ok"))
