"""Regression cases for the F1-A 1.3.0 review findings."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from bt_planner import contract as pc
from bt_planner.contract import PlanContractError
from bt_planner import schema_13
from bt_planner.tests.test_schema_13 import base_plan


class Schema13ReviewRegressionTests(unittest.TestCase):
    def test_malformed_p177_graph_inputs_are_reports_across_public_load_paths(self):
        fixture = Path(__file__).parent / "fixtures" / "P-177-schema-1.3.0.json"
        valid_plan = json.loads(fixture.read_text(encoding="utf-8"))
        mutations = (
            (("subplans", 0, "produces"), (None, {}, True, [False])),
            (("subplans", 1, "consumes"), (None, {}, True, [False])),
            (("subplans", 0, "audit_task"), (None, [], {}, True)),
            (("subplans", 1, "produces", 0, "defined_by"), (None, [], {}, True)),
            (("subplans", 1, "consumes", 0, "from"), (None, [], {}, True)),
            (("subplans", 1, "consumes", 0, "verified_by"), (None, {}, True, [False])),
            (("composition_gates", 0, "subplans"), (None, {}, True, [False])),
            (("composition_gates", 0, "task"), (None, [], {}, True)),
            (("composition_gates", 0, "audit_task"), ([], {}, True)),
        )
        for path, malformed_values in mutations:
            for malformed in malformed_values:
                with self.subTest(path=path, malformed=malformed):
                    plan = copy.deepcopy(valid_plan)
                    target = plan
                    for part in path[:-1]:
                        target = target[part]
                    target[path[-1]] = malformed
                    first = pc.validate(plan)
                    second = pc.validate(plan)
                    publication = pc.validate(plan, strict_publication=True)
                    self.assertIsInstance(first, pc.Report)
                    self.assertTrue(first.errors, (path, malformed))
                    self.assertEqual((first.errors, first.warnings), (second.errors, second.warnings))
                    self.assertTrue(publication.errors, (path, malformed))
                    with tempfile.TemporaryDirectory() as temp:
                        plan_path = Path(temp) / "PLAN.json"
                        plan_path.write_text(pc.dumps(plan), encoding="utf-8")
                        with self.assertRaises(PlanContractError) as raised:
                            pc.load(plan_path)
                    self.assertEqual(raised.exception.code, "PLAN_INVALID")
                    self.assertEqual(raised.exception.issues, first.errors)

    def test_publication_order_accepts_separate_valid_gates_per_consumer_branch(self):
        plan = self._publication_plan()
        tasks = {task["id"]: task for task in plan["tasks"]}
        tasks["T1"]["after"] = ["T7"]
        tasks["T10"]["after"] = ["T8"]
        report = pc.validate(plan)
        self.assertFalse(any(line.startswith("SUBPLAN_ORDER:") for line in report.errors), report.errors)

    def test_mixed_contract_cycles_are_errors_independent_of_subplan_order(self):
        for reversed_order in (False, True):
            first = {"consumes": [{"from": "SP-2", "dependency": "implementation"}]}
            second = {"consumes": [{"from": "SP-1", "dependency": "contract"}]}
            subplans = {"SP-1": first, "SP-2": second}
            if reversed_order:
                subplans = dict(reversed(list(subplans.items())))
            errors: list[str] = []
            warnings: list[str] = []
            schema_13._validate_dependency_cycles(errors, warnings, subplans, [])
            with self.subTest(reversed_order=reversed_order):
                self.assertTrue(any(line.startswith("SUBPLAN_CYCLE:") for line in errors), errors)
                self.assertFalse(warnings, warnings)

    def test_contract_only_cycles_remain_warnings_in_either_order(self):
        for reversed_order in (False, True):
            subplans = {
                "SP-1": {"consumes": [{"from": "SP-2", "dependency": "contract"}]},
                "SP-2": {"consumes": [{"from": "SP-1", "dependency": "contract"}]},
            }
            if reversed_order:
                subplans = dict(reversed(list(subplans.items())))
            errors: list[str] = []
            warnings: list[str] = []
            schema_13._validate_dependency_cycles(errors, warnings, subplans, [])
            with self.subTest(reversed_order=reversed_order):
                self.assertFalse(errors, errors)
                self.assertTrue(any(line.startswith("SUBPLAN_CYCLE:") for line in warnings), warnings)

    def test_gates_are_validated_when_no_subplans_are_declared(self):
        plan = base_plan()
        plan.pop("subplans")
        for task in plan["tasks"]:
            task.pop("subplan_id", None)
        plan["composition_gates"] = [{}]
        self.assertTrue(any(line.startswith("COMPOSITION_INVALID:") for line in pc.validate(plan).errors))

    @staticmethod
    def _publication_plan() -> dict:
        plan = base_plan()
        plan["tasks"] = []
        specs = (("T1", "implement", "SP-1", []), ("T2", "test", "SP-1", ["T1", "T10"]),
                 ("T3", "audit", "SP-1", ["T2"]), ("T4", "implement", "SP-2", []),
                 ("T5", "test", "SP-2", ["T4"]), ("T6", "audit", "SP-2", ["T5"]),
                 ("T7", "test", None, ["T6"]), ("T8", "test", None, ["T6"]),
                 ("T10", "implement", "SP-1", []),
                 ("T9", "test", None, ["T3", "T6"]))
        for task_id, kind, subplan_id, after in specs:
            template = base_plan()["tasks"][0] if kind == "implement" else base_plan()["tasks"][1]
            task = copy.deepcopy(template)
            task.update(id=task_id, kind=kind, subplan_id=subplan_id, after=after)
            if kind == "test":
                task["verification"] = [{"type": "command", "value": "pytest tests/integration -q",
                                          "purpose": "integration", "category": "integration"}]
            elif kind == "audit":
                task["expected_paths"] = [f"docs/{task_id}.findings.json"]
                task["verification"] = [{"type": "command", "value": f"engine audit-ledger check docs/{task_id}.findings.json",
                                          "purpose": "audit", "category": "static"}]
            plan["tasks"].append(task)
        consumer = copy.deepcopy(base_plan()["subplans"][0])
        consumer["consumes"] = [{"contract": "session-api", "version": 1, "from": "SP-2",
                                  "dependency": "publication"}]
        consumer.update(integration_test_task="T2", audit_task="T3", checkpoints=[])
        producer = copy.deepcopy(base_plan()["subplans"][0])
        producer.update(id="SP-2", title="Producer", outcome="Producer contract is frozen",
                        produces=[{"contract": "session-api", "version": 1, "defined_by": "T4"}],
                        integration_test_task="T5", audit_task="T6", checkpoints=[])
        plan["subplans"] = [consumer, producer]
        plan["composition_gates"] = [
            {"id": "CG-1", "subplans": ["SP-2"], "task": "T7",
             "criteria": ["Session endpoint rejects expired credentials"]},
            {"id": "CG-2", "subplans": ["SP-2"], "task": "T8",
             "criteria": ["Session endpoint rejects expired credentials"]},
            {"id": "CG-3", "subplans": ["SP-1", "SP-2"], "task": "T9",
             "criteria": ["Session endpoint rejects expired credentials"]},
        ]
        return plan

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
