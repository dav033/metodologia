"""Regression cases for the F1-A 1.3.0 review findings."""
from __future__ import annotations

import copy
import unittest

from bt_planner import contract as pc
from bt_planner import schema_13
from bt_planner.tests.test_schema_13 import base_plan


class Schema13ReviewRegressionTests(unittest.TestCase):
    def test_late_checkpoint_boundaries_count_the_source_task(self):
        for code in ("LATE_CHECKPOINT", "SUBPLAN_LATE_CHECKPOINT"):
            for trailing_barrier in (False, True):
                for length, accepted in ((6, True), (7, False)):
                    with self.subTest(code=code, trailing_barrier=trailing_barrier, length=length):
                        plan = base_plan()
                        plan["tasks"] = []
                        scoped = code == "SUBPLAN_LATE_CHECKPOINT"
                        task_ids = [f"T{i}" for i in range(1, length + 1)]
                        for index, tid in enumerate(task_ids, 1):
                            task = copy.deepcopy(base_plan()["tasks"][0])
                            task.update(id=tid, kind="implement", subplan_id="SP-1" if scoped else None,
                                        after=[task_ids[index - 2]] if index > 1 else [],
                                        covers=["AUTH-1"], expected_paths=[f"src/step{index}.py"],
                                        acceptance_criteria=["Expired sessions are rejected"])
                            plan["tasks"].append(task)
                        barrier_id, audit_id = f"T{length + 1}", f"T{length + 2}"
                        barrier = copy.deepcopy(base_plan()["tasks"][1])
                        barrier.update(id=barrier_id, subplan_id="SP-1" if scoped else None,
                                       after=[task_ids[-1]] if trailing_barrier else [], kind="test")
                        plan["tasks"].append(barrier)
                        audit = copy.deepcopy(base_plan()["tasks"][2])
                        audit.update(id=audit_id, subplan_id="SP-1" if scoped else None,
                                     after=[barrier_id, *task_ids])
                        plan["tasks"].append(audit)
                        if scoped:
                            plan["subplans"][0].update(integration_test_task=barrier_id, audit_task=audit_id,
                                                        checkpoints=[{"task": barrier_id, "purpose": "Boundary test"}])
                        else:
                            plan.pop("subplans")
                        errors = pc.validate(plan).errors
                        self.assertEqual(any(line.startswith(f"{code}:") for line in errors), not accepted, errors)

    def test_plan_wide_checkpoint_spans_subplans_and_unassigned_docs(self):
        plan = base_plan()
        plan["requirements"] = ["AUTH-1", "AUTH-2"]
        plan["tasks"] = []
        for index in range(1, 9):
            sid = "SP-1" if index == 1 else (None if index == 8 else "SP-2")
            task = copy.deepcopy(base_plan()["tasks"][0])
            task.update(id=f"T{index}", kind="docs" if index == 8 else "implement", subplan_id=sid,
                        after=[f"T{index - 1}"] if index > 1 else [],
                        covers=["AUTH-1" if sid == "SP-1" else "AUTH-2"],
                        expected_paths=[f"src/step{index}.py"],
                        acceptance_criteria=["Expired sessions are rejected"])
            plan["tasks"].append(task)
        plan["subplans"] = [
            {"id": "SP-1", "milestone_id": "M1", "title": "Producer", "outcome": "Producer contract is frozen",
             "covers": ["AUTH-1"], "acceptance_criteria": ["Expired sessions are rejected"],
             "produces": [{"contract": "session-api", "version": 1, "defined_by": "T1"}], "consumes": [],
             "checkpoints": [], "integration_test_task": "T2", "audit_task": "T3"},
            {"id": "SP-2", "milestone_id": "M1", "title": "Consumer", "outcome": "Consumer uses producer contract",
             "covers": ["AUTH-2"], "acceptance_criteria": ["Expired sessions are rejected"],
             "produces": [], "consumes": [{"contract": "session-api", "version": 1, "from": "SP-1",
                                              "dependency": "contract"}],
             "checkpoints": [], "integration_test_task": "T4", "audit_task": "T7"},
        ]
        report = pc.validate(plan)
        self.assertTrue(any(line.startswith("LATE_CHECKPOINT:") for line in report.errors), report.errors)

    def test_malformed_schema_13_values_return_reports(self):
        cases = [("top", field) for field in ("subplans", "composition_gates")]
        cases += [("subplan", field) for field in ("id", "milestone_id", "title", "outcome", "covers",
                  "acceptance_criteria", "produces", "consumes", "checkpoints", "integration_test_task",
                  "audit_task", "ui")]
        cases += [("gate", field) for field in ("id", "subplans", "task", "audit_task", "criteria")]
        cases += [("task", field) for field in ("subplan_id", "ui", "kind")]
        cases += [("verification", field) for field in ("environment", "requires", "authorization_needed")]
        for location, field in cases:
            for value in (None, 7, [], {}, "malformed"):
                with self.subTest(location=location, field=field, value=value):
                    plan = base_plan()
                    plan["tasks"][0]["ui"] = "malformed"
                    if location == "top":
                        plan[field] = value
                    elif location == "subplan":
                        plan["subplans"][0][field] = value
                    elif location == "gate":
                        plan["composition_gates"] = [{"id": "CG-1", "subplans": ["SP-1"], "task": "T2",
                                                       "audit_task": "T3",
                                                       "criteria": ["Session endpoint rejects expired credentials"]}]
                        plan["composition_gates"][0][field] = value
                    elif location == "task":
                        plan["tasks"][0][field] = value
                    else:
                        plan["tasks"][0]["verification"][0][field] = value
                    report = pc.validate(plan)
                    self.assertIsInstance(report, pc.Report)
                    self.assertTrue(report.errors, (location, field, value))

    def test_publication_order_accepts_any_matching_gate(self):
        plan = base_plan()
        plan["tasks"] = []
        task_specs = [("T1", "implement", "SP-1", ["T8"]), ("T2", "test", "SP-1", ["T1"]),
                      ("T3", "audit", "SP-1", ["T2"]), ("T4", "implement", "SP-2", []),
                      ("T5", "test", "SP-2", ["T4"]), ("T6", "audit", "SP-2", ["T5"]),
                      ("T7", "test", None, ["T6"]), ("T8", "test", None, ["T6"]),
                      ("T9", "test", None, ["T3", "T6"])]
        for tid, kind, sid, after in task_specs:
            template = base_plan()["tasks"][0] if kind == "implement" else base_plan()["tasks"][1]
            task = copy.deepcopy(template)
            task.update(id=tid, kind=kind, subplan_id=sid, after=after)
            if kind == "test":
                task["verification"] = [{"type": "command", "value": "pytest tests/integration -q",
                                          "purpose": "integration", "category": "integration"}]
            if kind == "audit":
                task["expected_paths"] = [f"docs/{tid}.findings.json"]
                task["verification"] = [{"type": "command", "value": f"engine audit-ledger check docs/{tid}.findings.json",
                                          "purpose": "audit", "category": "static"}]
            plan["tasks"].append(task)
        producer = copy.deepcopy(base_plan()["subplans"][0])
        producer.update(id="SP-2", title="Producer", outcome="Producer contract is frozen",
                        produces=[{"contract": "session-api", "version": 1, "defined_by": "T4"}],
                        integration_test_task="T5", audit_task="T6", checkpoints=[])
        consumer = copy.deepcopy(base_plan()["subplans"][0])
        consumer.update(consumes=[{"contract": "session-api", "version": 1, "from": "SP-2",
                                   "dependency": "publication"}], integration_test_task="T2",
                        audit_task="T3", checkpoints=[])
        plan["subplans"] = [consumer, producer]
        plan["composition_gates"] = [
            {"id": "CG-1", "subplans": ["SP-2"], "task": "T7", "criteria": ["Session endpoint rejects expired credentials"]},
            {"id": "CG-2", "subplans": ["SP-2"], "task": "T8", "criteria": ["Session endpoint rejects expired credentials"]},
            {"id": "CG-3", "subplans": ["SP-1", "SP-2"], "task": "T9", "criteria": ["Session endpoint rejects expired credentials"]},
        ]
        report = pc.validate(plan)
        self.assertFalse(any(line.startswith("SUBPLAN_ORDER:") for line in report.errors), report.errors)

    def test_contract_diagnostics_and_requirement_membership_are_typed(self):
        plan = base_plan()
        plan["subplans"][0]["consumes"] = [{"contract": "external-api", "version": 1, "from": "external",
                                              "dependency": "contract", "verified_by": ["T1"]}]
        self.assertTrue(any(line.startswith("SUBPLAN_CONTRACT:") and "verified_by" in line
                            for line in pc.validate(plan).errors))

        errors: list[str] = []
        task = copy.deepcopy(plan["tasks"][1])
        task["covers"] = "AUTH-10"
        schema_13._validate_requirements(errors, {"AUTH-1"}, plan, {"T2": task}, [], [{"task": "T2"}])
        self.assertTrue(any(line.startswith("REQUIREMENT_ORPHAN:") for line in errors), errors)

    def test_unknown_verification_environment_has_stable_code(self):
        plan = base_plan()
        plan["tasks"][1]["verification"][0]["environment"] = "staging"
        self.assertTrue(any(line.startswith("VERIFICATION_ENV_INVALID:") for line in pc.validate(plan).errors))

    def test_probe_commands_reject_shell_operators_and_accept_multiple_test_flags(self):
        for command in ("test -f a | cat", "test -f a || echo missing", "test -f $(printf a)",
                        "test -f `printf a`", "test -f a >out", "test -f a 2>&1"):
            with self.subTest(command=command):
                self.assertFalse(schema_13._file_probe(command))
        self.assertTrue(schema_13._file_probe("test -f a -a -f b"))

    def test_subplanless_tests_are_allowed(self):
        plan = base_plan()
        extra = copy.deepcopy(plan["tasks"][1])
        extra.update(id="T4", subplan_id=None, after=["T3"])
        plan["tasks"].append(extra)
        self.assertFalse(any(line.startswith("TASK_OUTSIDE_SUBPLAN: T4:") for line in pc.validate(plan).errors))
