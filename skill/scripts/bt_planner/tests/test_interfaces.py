"""Schema 1.2.0 cross-task interface declarations and dependency proofs."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from bt_planner import contract as pc
from bt_planner import interfaces, quality

GOLDEN = Path(__file__).with_name("golden")


def proposed_plan() -> dict:
    return json.loads((GOLDEN / "input-1.2.0.json").read_text(encoding="utf-8"))


def interface_errors(plan: dict) -> list[str]:
    return interfaces.check(plan, quality.ancestors(plan))[0]


def subplan_plan(consumer_after: list[str], integration: str = "T3") -> dict:
    """SP-1 owns IF-1: T1 writes the contract, T2 wires it, T3 proves it end to end; T4 in SP-2 consumes it."""
    tasks = [{"id": "T1", "after": [], "subplan_id": "SP-1"}, {"id": "T2", "after": ["T1"], "subplan_id": "SP-1"},
             {"id": "T3", "after": ["T1", "T2"], "subplan_id": "SP-1"},
             {"id": "T4", "after": consumer_after, "subplan_id": "SP-2"},
             {"id": "G1", "after": ["T3", "T4"]}]
    return {"tasks": tasks, "subplans": [{"id": "SP-1"}, {"id": "SP-2"}],
            "composition_gates": [{"id": "CG-1", "subplans": ["SP-1", "SP-2"], "task": "G1"}],
            "interfaces": [{"id": "IF-1", "title": "ledger@1", "owner": "SP-1", "producer_task": "T1",
                            "integration_task": integration, "consumer_tasks": ["T2", "T4"], "inputs": ["calls"],
                            "outputs": ["rows"], "invariants": ["one row per call"],
                            "integration_criteria": ["a call writes one row"]}]}


class ForeignConsumers(unittest.TestCase):
    """A consumer outside the owner subplan depends on the task that proves the interface (D-165, pictures REQ-021 T7.4)."""

    def test_a_consumer_in_another_subplan_must_wait_for_the_proven_interface(self):
        errors = interface_errors(subplan_plan(["T1"]))
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("T4 (SP-2) relies on IF-1 of SP-1; it must depend on T3", errors[0])
        self.assertEqual(interface_errors(subplan_plan(["T3"])), [])

    def test_owner_consumers_gate_integration_and_plans_without_subplans_keep_the_old_rule(self):
        self.assertEqual(interface_errors(subplan_plan(["T1"], integration="G1")), [])     # the gate composes T4 itself
        plan = subplan_plan(["T1"])
        plan["interfaces"][0]["owner"] = "Payments team"
        self.assertFalse(any("relies on" in e for e in interface_errors(plan)))


class InterfaceContracts(unittest.TestCase):
    def test_interfaces_is_optional_but_must_be_a_list_when_present(self):
        plan = proposed_plan()
        plan.pop("interfaces")
        self.assertEqual(interface_errors(plan), [])
        plan["interfaces"] = None
        self.assertEqual(interface_errors(plan), ["interfaces: must be a list when provided"])

    def test_non_object_interface_is_reported_without_raising(self):
        plan = proposed_plan()
        plan["interfaces"] = [None]
        self.assertEqual(interface_errors(plan), ["interfaces[0]: must be an object"])

    def test_golden_interface_passes_with_direct_producer_dependency(self):
        self.assertEqual(interface_errors(proposed_plan()), [])

    def test_transitive_producer_dependency_satisfies_consumer(self):
        plan = proposed_plan()
        intermediary = dict(plan["tasks"][1], id="T3", after=["T1"])
        plan["tasks"][1]["after"] = ["T3"]
        plan["tasks"].append(intermediary)
        self.assertEqual(interface_errors(plan), [])

    def test_unknown_producer_and_consumer_tasks_are_rejected(self):
        plan = proposed_plan()
        plan["interfaces"][0]["producer_task"] = "T9"
        plan["interfaces"][0]["consumer_tasks"] = ["T8"]
        errors = "\n".join(interface_errors(plan))
        self.assertIn("interfaces[0].producer_task: task 'T9' does not exist", errors)
        self.assertIn("interfaces[0].consumer_tasks[0]: task 'T8' does not exist", errors)

    def test_producer_and_consumer_must_differ(self):
        plan = proposed_plan()
        plan["interfaces"][0]["consumer_tasks"] = ["T1"]
        errors = interface_errors(plan)
        self.assertTrue(any("producer and consumer must differ" in error for error in errors), errors)

    def test_unordered_consumer_requires_an_integration_task(self):
        plan = proposed_plan()
        plan["tasks"][1]["after"] = []
        errors = interface_errors(plan)
        self.assertTrue(any("consumer_tasks[0]" in error and "integration_task is required" in error
                            for error in errors), errors)

    def test_integration_task_must_depend_on_producer_and_unordered_consumer(self):
        plan = proposed_plan()
        plan["tasks"][1]["after"] = []
        integration = dict(plan["tasks"][1], id="T3", after=["T1"])
        plan["tasks"].append(integration)
        plan["interfaces"][0]["integration_task"] = "T3"
        errors = interface_errors(plan)
        self.assertTrue(any("interfaces[0].integration_task" in error and "T2" in error for error in errors), errors)

    def test_ordered_integration_task_satisfies_an_unordered_consumer(self):
        plan = proposed_plan()
        plan["tasks"][1]["after"] = []
        integration = dict(plan["tasks"][1], id="T3", after=["T1", "T2"])
        plan["tasks"].append(integration)
        plan["interfaces"][0]["integration_task"] = "T3"
        self.assertEqual(interface_errors(plan), [])

    def test_integration_task_cannot_be_a_consumer(self):
        plan = proposed_plan()
        plan["tasks"][1]["after"] = []
        plan["interfaces"][0]["integration_task"] = "T2"
        errors = interface_errors(plan)
        self.assertTrue(any("integration_task: cannot be one of the consumer tasks" in error
                            for error in errors), errors)

    def test_required_interface_fields_and_text_lists_are_checked(self):
        plan = proposed_plan()
        interface = plan["interfaces"][0]
        for field in ("title", "owner", "inputs", "outputs", "invariants", "integration_criteria"):
            interface.pop(field)
        errors = "\n".join(interface_errors(plan))
        for field in ("title", "owner", "inputs", "outputs", "invariants", "integration_criteria"):
            self.assertIn(f"interfaces[0].{field}", errors)

    def test_interface_ids_must_be_valid_and_unique(self):
        plan = proposed_plan()
        duplicate = dict(plan["interfaces"][0])
        plan["interfaces"].append(duplicate)
        errors = interface_errors(plan)
        self.assertTrue(any("duplicate interface ID IF-1" in error for error in errors), errors)
        plan["interfaces"][1]["id"] = "interface-two"
        errors = interface_errors(plan)
        self.assertTrue(any("must look like IF-1" in error for error in errors), errors)

    def test_contract_key_scanner_rejects_scheduling_keys_inside_interfaces(self):
        plan = proposed_plan()
        plan["interfaces"][0]["provider"] = "claude"
        errors = pc.validate(plan, spec_ids={"R1"}).errors
        self.assertTrue(any("plan.interfaces[0].provider" in error and "not allowed in a plan" in error
                            for error in errors), errors)

    def test_interface_text_rejects_concurrency_claims_but_allows_neutral_terms(self):
        plan = proposed_plan()
        plan["interfaces"][0]["inputs"] = ["T2 can be run in parallel with other tasks"]
        errors = interface_errors(plan)
        self.assertTrue(any("interfaces[0].inputs[0]" in error and "scheduling guarantees" in error
                            for error in errors), errors)

        plan["interfaces"][0]["inputs"] = ["the payload contains parallel arrays"]
        self.assertEqual(interface_errors(plan), [])

    def test_report_exposes_declared_interfaces_without_an_acceptance_verdict(self):
        report = interfaces.report(proposed_plan())
        self.assertEqual(report[0]["id"], "IF-1")
        self.assertEqual(report[0]["producer_task"], "T1")
        self.assertEqual(report[0]["consumer_tasks"], ["T2"])
        self.assertNotIn("accepted", report[0])


if __name__ == "__main__":
    unittest.main()
