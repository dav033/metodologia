from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import bt_scheduler_core as sc
from support import approved, indep, plan_text


def plan_13(*, schema="1.3.0", extra_tasks=()):
    tasks = [
        {**indep("T1", kind="implement", subplan_id="SP-1", ui=True,
                 verification=[{"type": "command", "value": "true", "category": "functional"}]),
         "acceptance_criteria": ["UI works"]},
        {**indep("T2", ["T1"], kind="test", subplan_id="SP-1"),
         "verification": [{"type": "command", "value": "true", "category": "integration"}],
         "acceptance_criteria": ["SP-1 integration works"]},
        {**indep("T3", ["T2"], kind="audit", subplan_id="SP-1",
                 verification=[{"type": "command", "value": "true", "category": "functional"}]),
         "acceptance_criteria": ["SP-1 audit passes"]},
        {**indep("T4", ["T3"], kind="test"),
         "verification": [{"type": "command", "value": "true", "category": "integration"}],
         "acceptance_criteria": ["Composition works"]},
        *extra_tasks,
    ]
    return plan_text(tasks, schema_version=schema, subplans=[{
        "id": "SP-1", "milestone_id": "M1", "title": "UI", "outcome": "The UI is usable end to end",
        "covers": ["R1"], "acceptance_criteria": ["UI works"],
        "produces": [{"contract": "customer-api", "version": 1, "defined_by": "T1", "interfaces": ["IF-1"]}],
        "consumes": [],
        "checkpoints": [], "integration_test_task": "T2", "audit_task": "T3",
        "ui": {"contract": "form", "version": 1, "design_task": "T1", "visual_review_task": "T3"},
    }], composition_gates=[{
        "id": "CG-1", "subplans": ["SP-1"], "task": "T4", "criteria": ["Composition works"],
    }])


def load(text):
    return approved(text)[0]


class Subplans(unittest.TestCase):
    def test_schema_13_loads_subplans_gates_and_task_metadata(self):
        plan = load(plan_13())
        self.assertEqual(sc.PLAN_SCHEMA_CAPABILITIES, frozenset({"1.0.0", "1.1.0", "1.2.0", "1.3.0"}))
        self.assertEqual(plan.subplans[0].id, "SP-1")
        self.assertEqual(plan.composition_gates[0].task, "T4")
        self.assertEqual(plan.task("T1").meta["subplan_id"], "SP-1")
        self.assertTrue(plan.task("T1").meta["ui"])
        with self.assertRaises((AttributeError, TypeError)):
            plan.composition_gates[0].task = "T3"
        with self.assertRaises(TypeError):
            plan.subplans[0].produces[0]["contract"] = "mutated"

    def test_malformed_subplan_and_gate_shapes_are_plan_invalid(self):
        for edit in (
            lambda data: data.update(subplans=[{"id": "SP-1"}]),
            lambda data: data.update(composition_gates=[{"id": "CG-1", "subplans": "SP-1", "task": "T4"}]),
            lambda data: data["subplans"][0].update(produces=[{"contract": "bad slug", "version": 1,
                                                               "defined_by": "T1"}]),
            lambda data: data["tasks"][0].update(subplan_id=[]),
            lambda data: data["tasks"][0].update(ui="yes"),
        ):
            data = json.loads(plan_13())
            edit(data)
            text = json.dumps(data)
            with self.assertRaises(sc.SchedulerError) as caught:
                sc.load_plan(text, approved_sha256=hashlib.sha256(text.encode()).hexdigest())
            self.assertEqual(caught.exception.code, "PLAN_INVALID")

    def test_legacy_fingerprint_stays_byte_identical_and_13_includes_new_task_fields(self):
        legacy, _ = approved(plan_text([indep("T1", kind="implement", verification=[
            {"type": "command", "value": "true", "category": "functional"}])], schema_version="1.2.0"))
        expected = hashlib.sha256(json.dumps({"id": "T1", "after": [], "repository": "repo-T1",
                                              "acceptance_criteria": ["T1 works"], "verification":
                                              [{"type": "command", "value": "true", "category": "functional"}]}, sort_keys=True,
                                             separators=(",", ":"), default=str).encode()).hexdigest()
        self.assertEqual(sc.fingerprint(legacy.task("T1")), expected)
        base = json.loads(plan_13())
        plain = json.loads(json.dumps(base))
        plain["tasks"][0].pop("subplan_id")
        plain["tasks"][0].pop("ui")
        a, b = load(json.dumps(base)), load(json.dumps(plain))
        self.assertNotEqual(sc.fingerprint(a.task("T1")), sc.fingerprint(b.task("T1")))

    def test_fact_operations_are_audited_additive_and_do_not_change_task_state(self):
        plan = load(plan_13())
        repo = sc.InMemoryRepository()
        core = sc.SchedulerCore(plan, repo)
        core.start()
        before = core.snapshot().tasks
        core.record_subplan_version("SP-1", 1, "a" * 40, "b" * 64)
        core.record_composition("candidate", "C1", {"SP-1": 1}, "c" * 64)
        self.assertEqual(core.snapshot().tasks, before)
        state = core.read(lambda tx: tx.state)
        self.assertEqual(state.subplan_versions["SP-1"]["version"], 1)
        self.assertEqual(state.compositions["C1"]["state"], "candidate")
        self.assertIn("subplan_version_published", [row.kind for row in core.audit_log()])
        self.assertIn("composition_candidate", [row.kind for row in core.audit_log()])

    def test_fact_retries_are_idempotent_and_published_composition_is_immutable(self):
        plan = load(plan_13())
        core = sc.SchedulerCore(plan, sc.InMemoryRepository())
        core.start()
        version = ("SP-1", 1, "a" * 40, "b" * 64)
        core.record_subplan_version(*version)
        audit_count = len(core.audit_log())
        core.record_subplan_version(*version)
        self.assertEqual(len(core.audit_log()), audit_count)
        fact = ("C1", {"SP-1": 1}, "c" * 64)
        core.record_composition("candidate", fact[0], fact[1], fact[2])
        core.record_composition("published", fact[0], fact[1], fact[2])
        with self.assertRaises(sc.SchedulerError) as caught:
            core.record_composition("candidate", fact[0], fact[1], "d" * 64)
        self.assertEqual(caught.exception.code, "NOT_ALLOWED")

    def test_gate_waits_with_attention_until_member_has_published_version(self):
        plan = load(plan_13())
        repo = sc.InMemoryRepository()
        core = sc.SchedulerCore(plan, repo)
        core.start()
        for task_id in ("T1", "T2", "T3"):
            core.claim(sc.Assignment(task_id, "fake"))
            attempt = core.snapshot().tasks[task_id]["attempt"]
            core.ingest(sc.Event(f"e-{task_id}", plan.plan_id, 1, task_id, attempt, "fake", "execution_finished"))
            core.step()
            core.submit_verdict(sc.Verdict(f"v-{task_id}", plan.plan_id, 1, task_id, attempt, True, "validator", "ok"))
            core.step()
        self.assertEqual(core.snapshot().tasks["T4"]["state"], "pending")
        self.assertTrue(any(row["kind"] == "composition_waiting" and row["task_id"] == "T4"
                            for row in core.snapshot().attention))
        core.record_subplan_version("SP-1", 1, "a" * 40, "b" * 64)
        core.step()
        self.assertEqual(core.snapshot().tasks["T4"]["state"], "active")

    def test_m2_and_m3_receive_only_declared_13_metadata(self):
        text = plan_13()
        plan = load(text)
        class M2:
            request = None
            assignment_request = None

            def plan(self, request):
                self.request = request
                return tuple(sc.PlannedRoute(task.id, reason="not_routed") for task in request.tasks)

            def propose(self, request):
                self.assignment_request = request
                return (sc.Assignment(request.ready[0].id, "fake"),)

        routing = M2()
        execution = sc.FakeExecutor()
        core = sc.SchedulerCore(plan, sc.InMemoryRepository(),
                                ports=sc.Ports(assignment=routing, routing=routing, execution=execution))
        core.start()
        meta = {task.id: task.meta for task in routing.request.tasks}
        self.assertEqual(meta["T1"]["subplan_id"], "SP-1")
        self.assertEqual(meta["T3"]["review_axis"], "visual")
        self.assertTrue(meta["T1"]["ui"])
        core.step()
        self.assertEqual(routing.assignment_request.ready[0].meta["subplan_id"], "SP-1")
        self.assertEqual(execution.started["att-0001"].meta["subplan_id"], "SP-1")


if __name__ == "__main__":
    unittest.main()
