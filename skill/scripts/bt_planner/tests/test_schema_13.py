"""Functional subplans and verification rules introduced by PLAN.json 1.3.0."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from bt_planner import contract as pc
from bt_planner import schema_13, subplan_graph
from bt_planner import revisions, sync


GOLDEN = Path(__file__).with_name("golden")


def base_plan() -> dict:
    plan = json.loads((GOLDEN / "input-1.2.0.json").read_text(encoding="utf-8"))
    plan["schema_version"] = "1.3.0"
    plan["requirements"] = ["AUTH-1"]
    plan["tasks"] = plan["tasks"][:1]
    task = plan["tasks"][0]
    task.update(covers=["AUTH-1"], kind="implement", subplan_id="SP-1")
    task["after"] = []
    task["acceptance_criteria"] = ["Expired sessions are rejected"]
    task["verification"] = [{"type": "command", "value": "pytest tests/auth -q", "purpose": "auth behaviour",
                              "category": "functional"}]
    test = copy.deepcopy(task)
    test.update(id="T2", title="Exercise integration", objective="Verify the API integration works",
                after=["T1"], kind="test", covers=["AUTH-1"], expected_paths=["tests/integration/**"],
                acceptance_criteria=["Session endpoint rejects expired credentials"],
                verification=[{"type": "command", "value": "pytest tests/integration -q", "purpose": "integration",
                               "category": "integration"}])
    audit = copy.deepcopy(test)
    audit.update(id="T3", title="Audit the implementation", objective="Review implementation evidence and findings",
                 after=["T2"], kind="audit", expected_paths=["docs/T3.findings.json"],
                 acceptance_criteria=["All implementation findings are resolved"],
                 verification=[{"type": "command", "value": "engine audit-ledger check docs/T3.findings.json",
                                "purpose": "verify findings ledger", "category": "static"}])
    plan["tasks"] = [task, test, audit]
    plan["subplans"] = [{"id": "SP-1", "milestone_id": "M1", "title": "Session validation",
                         "outcome": "Expired sessions are rejected by the API", "covers": ["AUTH-1"],
                         "acceptance_criteria": ["Expired sessions are rejected"], "produces": [], "consumes": [],
                         "checkpoints": [{"task": "T2", "purpose": "API behavior checked"}],
                         "integration_test_task": "T2", "audit_task": "T3"}]
    return plan


class Schema13Tests(unittest.TestCase):
    def assertCode(self, plan: dict, code: str) -> None:
        report = pc.validate(plan)
        self.assertTrue(any(line.startswith(f"{code}:") for line in report.errors), report.errors)

    def test_version_constants_and_legacy_canonical_output_are_separate(self):
        plan = base_plan()
        self.assertEqual(pc.SCHEMA_VERSION, "1.3.0")
        self.assertEqual(pc.LATEST_SCHEMA_VERSION, "1.3.0")
        self.assertEqual(pc.TASK_KEYS_13[-2:], ("subplan_id", "ui"))
        legacy = json.loads((GOLDEN / "input-1.2.0.json").read_text(encoding="utf-8"))
        self.assertNotIn("subplan_id", pc.canonicalize(legacy)["tasks"][0])
        self.assertTrue(pc.validate(plan).ok, pc.validate(plan).errors)

    def test_owner_composition_rules_fail_during_plan_validation(self):
        plan = base_plan()
        gate_task = copy.deepcopy(plan["tasks"][-1])
        gate_task.update(id="T4", subplan_id=None, kind="test", after=["T3"],
                         repository="other", expected_paths=[],
                         acceptance_criteria=["Composition works"],
                         verification=[{"type": "command", "value": "true", "purpose": "composition",
                                        "category": "integration"}])
        plan["tasks"].append(gate_task)
        plan["subplans"][0]["produces"] = [{"contract": "session-api", "version": 1, "defined_by": "T1"}]
        plan["tasks"][0]["expected_paths"] = ["src/**/*.py"]
        plan["composition_gates"] = [{"id": "CG-1", "subplans": ["SP-1"], "task": "T4",
                                      "criteria": ["Composition works"]}]
        report = pc.validate(plan)
        self.assertTrue(any(line.startswith("OWNER_COMPOSITION_SINGLE_REPOSITORY_REQUIRED:")
                            for line in report.errors), report.errors)
        self.assertTrue(any(line.startswith("OWNER_COMPOSITION_DEFINED_BY_PATHS_NOT_EXACT_FILES:")
                            for line in report.errors), report.errors)

    def test_schema_13_canonicalizes_new_fields_and_schema_document_is_valid_json(self):
        plan = base_plan()
        plan["tasks"][0]["ui"] = False
        plan["composition_gates"] = []
        canonical = pc.canonicalize(plan)
        self.assertLess(list(canonical["tasks"][0]).index("kind"), list(canonical["tasks"][0]).index("subplan_id"))
        self.assertIn('"subplans"', pc.dumps(plan))
        schema = json.loads((Path(__file__).parents[1] / "data" / "plan.schema.json").read_text())
        self.assertIn("subplans", schema["properties"])
        self.assertIn("environment", schema["$defs"]["verification"]["properties"])

    def test_schema_13_example_loads(self):
        path = Path(__file__).parents[1] / "data" / "plan.example.1.3.0.json"
        self.assertEqual(pc.load(path)["schema_version"], "1.3.0")

    def test_legacy_schema_fields_are_silent_for_consumers_and_error_at_publication(self):
        plan = json.loads((GOLDEN / "input-1.2.0.json").read_text(encoding="utf-8"))
        plan["tasks"][0]["subplan_id"] = "SP-1"
        warning = pc.validate(plan)
        self.assertFalse(warning.errors)
        self.assertFalse(any(line.startswith("SCHEMA_FIELD_UNSUPPORTED:") for line in warning.warnings))
        publication = pc.validate(plan, strict_publication=True)
        self.assertTrue(any(line.startswith("SCHEMA_FIELD_UNSUPPORTED:") for line in publication.errors))

        plan = json.loads((GOLDEN / "input-1.2.0.json").read_text(encoding="utf-8"))
        plan["tasks"][0]["kind"] = "design"
        report = pc.validate(plan)
        self.assertFalse(report.ok)
        self.assertTrue(any("kind" in line and "design" in line for line in report.errors), report.errors)
        self.assertFalse(any(line.startswith("SCHEMA_FIELD_UNSUPPORTED:") for line in report.warnings))
        publication = pc.validate(plan, strict_publication=True)
        self.assertTrue(any(line.startswith("SCHEMA_FIELD_UNSUPPORTED:") and "kind" in line
                            for line in publication.errors), publication.errors)

    def test_ui_extension_requires_explicit_boolean_and_false_is_valid(self):
        plan = base_plan()
        plan["tasks"][0]["expected_paths"] = ["src/page.tsx"]
        errors = pc.validate(plan).errors
        self.assertTrue(any(e.startswith("UI_WORK_UNDECLARED:") for e in errors), errors)
        plan["tasks"][0]["ui"] = False
        result = pc.validate(plan)
        errors = result.errors
        self.assertFalse(any(e.startswith("UI_WORK_UNDECLARED:") for e in errors), errors)
        self.assertTrue(result.ok, errors)

    def test_exposure_stops_at_first_barrier_and_report_uses_same_measure(self):
        plan = base_plan()
        downstream = copy.deepcopy(plan["tasks"][0])
        downstream.update(id="T4", kind="implement", after=["T2"], acceptance_criteria=["Downstream work completes"])
        plan["tasks"].append(downstream)
        self.assertEqual(subplan_graph.exposure(plan), 0)
        self.assertEqual(subplan_graph.report(plan)[0]["exposure"], 0)

    def test_final_audit_legacy_shaped_chain_fails_late_checkpoint(self):
        plan = base_plan()
        plan["tasks"] = []
        for index in range(1, 25):
            source = copy.deepcopy(base_plan()["tasks"][0])
            source.update(id=f"T{index}", subplan_id=None, kind="implement", after=[f"T{index-1}"] if index > 1 else [],
                          covers=["AUTH-1"], expected_paths=[f"src/module{index}.py"],
                          acceptance_criteria=[f"Feature {index} is correct"])
            plan["tasks"].append(source)
        plan["tasks"][-1]["kind"] = "audit"
        plan["tasks"][-1]["verification"] = [{"type": "command", "value": "engine audit-ledger check docs/T24.findings.json",
                                               "purpose": "audit", "category": "static"}]
        plan.pop("subplans", None)
        self.assertGreaterEqual(subplan_graph.exposure(plan), 20)
        self.assertTrue(any(e.startswith("LATE_CHECKPOINT:") for e in pc.validate(plan).errors))

    def test_p177_fixture_has_large_legacy_exposure_and_bounded_subplan_exposure(self):
        fixtures = Path(__file__).parent / "fixtures"
        defects = json.loads((fixtures / "P-177-defect-map.json").read_text(encoding="utf-8"))["defects"]
        legacy = json.loads((fixtures / "P-177-legacy-1.2.0.json").read_text(encoding="utf-8"))
        plan = json.loads((fixtures / "P-177-schema-1.3.0.json").read_text(encoding="utf-8"))

        self.assertEqual(len(legacy["tasks"]), 24)
        self.assertEqual(len(plan["tasks"]), 24)
        self.assertGreaterEqual(max(subplan_graph.exposure(legacy, introducing_task=item["introducing_task"])
                                    for item in defects), 20)
        self.assertTrue(all(subplan_graph.first_barrier(legacy, item["introducing_task"])
                            == item["legacy_first_barrier"] for item in defects))
        self.assertTrue(pc.validate(plan).ok, pc.validate(plan).errors)
        exposures = [subplan_graph.exposure(plan, introducing_task=item["introducing_task"]) for item in defects]
        self.assertTrue(all(subplan_graph.first_barrier(plan, item["introducing_task"])
                            == item["first_barrier"] for item in defects))
        self.assertTrue(all(exposure <= 6 for exposure in exposures), exposures)
        self.assertTrue(any(3 <= exposure <= 6 for exposure in exposures), exposures)

        # The cross-subplan edges cover both a frozen contract and audited implementation.
        self.assertIn("T1", next(task for task in plan["tasks"] if task["id"] == "T10")["after"])
        self.assertIn("T15", next(task for task in plan["tasks"] if task["id"] == "T16")["after"])
        self.assertTrue(any(subplan["checkpoints"] for subplan in plan["subplans"]))
        missing_checkpoint = copy.deepcopy(plan)
        next(sp for sp in missing_checkpoint["subplans"] if sp["id"] == "SP-1")["checkpoints"] = []
        self.assertTrue(any(line.startswith("SUBPLAN_LATE_CHECKPOINT:")
                            for line in pc.validate(missing_checkpoint).errors))

    def test_file_probe_is_not_functional_verification(self):
        plan = base_plan()
        plan["tasks"][0]["verification"] = [{"type": "command", "value": "test -f src/auth.py", "purpose": "file exists",
                                              "category": "functional"}]
        self.assertTrue(any(e.startswith("FILE_EXISTENCE_CHECK:") for e in pc.validate(plan).errors))

    def test_remaining_subplan_and_composition_error_codes(self):
        cases = []

        plan = base_plan()
        plan["subplans"][0]["id"] = "not-a-subplan"
        cases.append((plan, "SUBPLAN_INVALID"))

        plan = base_plan()
        for task in plan["tasks"]:
            task["subplan_id"] = "SP-2"
        cases.append((plan, "SUBPLAN_EMPTY"))

        plan = base_plan()
        plan["subplans"][0]["outcome"] = plan["subplans"][0]["title"]
        cases.append((plan, "SUBPLAN_NO_OUTCOME"))

        plan = base_plan()
        plan["subplans"][0]["milestone_id"] = "M99"
        cases.append((plan, "SUBPLAN_MILESTONE"))

        plan = base_plan()
        plan["subplans"][0]["covers"] = ["AUTH-2"]
        cases.append((plan, "SUBPLAN_COVERAGE"))

        plan = base_plan()
        plan["subplans"][0]["acceptance_criteria"] = ["A criterion with no task evidence"]
        cases.append((plan, "SUBPLAN_CRITERION_UNCARRIED"))

        plan = base_plan()
        plan["subplans"][0]["produces"] = [{"contract": "Invalid/slug", "version": 1, "defined_by": "T1"}]
        cases.append((plan, "SUBPLAN_CONTRACT"))

        plan = base_plan()
        plan["subplans"][0]["audit_task"] = "T2"
        cases.append((plan, "SUBPLAN_AUDIT"))

        plan = base_plan()
        plan["requirements"].append("AUTH-2")
        cases.append((plan, "REQUIREMENT_ORPHAN"))

        plan = base_plan()
        outside = copy.deepcopy(plan["tasks"][0])
        outside.update(id="T4", subplan_id=None, after=["T3"], kind="implement")
        plan["tasks"].append(outside)
        cases.append((plan, "TASK_OUTSIDE_SUBPLAN"))

        plan = base_plan()
        plan["composition_gates"] = [{"id": "CG-1", "subplans": ["SP-1"], "task": "T2", "criteria": []}]
        cases.append((plan, "COMPOSITION_INVALID"))

        plan = base_plan()
        producer = copy.deepcopy(plan["subplans"][0])
        producer.update(id="SP-2", title="Session producer", produces=[])
        plan["subplans"].append(producer)
        plan["subplans"][0]["consumes"] = [{"contract": "session-api", "version": 1, "from": "SP-2",
                                              "dependency": "contract"}]
        cases.append((plan, "COMPOSITION_MISSING"))

        for plan, code in cases:
            with self.subTest(code=code):
                self.assertCode(plan, code)

    def test_contract_order_and_consumer_test_warning(self):
        plan = base_plan()
        producer_task = copy.deepcopy(plan["tasks"][0])
        producer_task.update(id="T4", subplan_id="SP-2", after=[], kind="implement",
                             acceptance_criteria=["The session contract is frozen"])
        plan["tasks"].append(producer_task)
        producer = copy.deepcopy(plan["subplans"][0])
        producer.update(id="SP-2", title="Session API", outcome="The session API contract is frozen",
                        produces=[{"contract": "session-api", "version": 1, "defined_by": "T4"}],
                        acceptance_criteria=["The session contract is frozen"], integration_test_task="T4",
                        audit_task="T4", checkpoints=[])
        plan["subplans"].append(producer)
        plan["subplans"][0]["consumes"] = [{"contract": "session-api", "version": 1, "from": "SP-2",
                                              "dependency": "implementation"}]
        plan["subplans"][0]["produces"] = [{"contract": "consumer-api", "version": 1, "defined_by": "T1"}]
        self.assertCode(plan, "SUBPLAN_ORDER")
        report = pc.validate(plan)
        self.assertTrue(any(line.startswith("CONSUMER_CONTRACT_TEST_MISSING:") for line in report.warnings), report.warnings)

    def test_subplan_late_checkpoint_and_ui_order_errors(self):
        plan = base_plan()
        plan["tasks"] = []
        for index in range(1, 12):
            task = copy.deepcopy(base_plan()["tasks"][0])
            kind = "implement" if index < 10 else "test" if index == 10 else "audit"
            task.update(id=f"T{index}", kind=kind, subplan_id="SP-1",
                        after=[f"T{index-1}"] if index > 1 else [], covers=["AUTH-1"],
                        expected_paths=[f"src/step{index}.py"], acceptance_criteria=["Expired sessions are rejected"])
            if kind == "test":
                task["verification"] = [{"type": "command", "value": "pytest tests/integration -q",
                                          "purpose": "real integration", "category": "integration"}]
            if kind == "audit":
                task["expected_paths"] = ["docs/T11.findings.json"]
                task["verification"] = [{"type": "command", "value": "engine audit-ledger check docs/T11.findings.json",
                                          "purpose": "audit findings", "category": "static"}]
            plan["tasks"].append(task)
        plan["subplans"][0]["integration_test_task"] = "T10"
        plan["subplans"][0]["audit_task"] = "T11"
        plan["subplans"][0]["checkpoints"] = []
        self.assertCode(plan, "SUBPLAN_LATE_CHECKPOINT")

        plan = base_plan()
        design = copy.deepcopy(plan["tasks"][0])
        design.update(id="T4", subplan_id="SP-1", kind="design", after=[], ui=False,
                      acceptance_criteria=["The visual contract is defined"])
        plan["tasks"].append(design)
        plan["tasks"][0]["ui"] = True
        plan["subplans"][0]["acceptance_criteria"] = ["Expired sessions are rejected"]
        plan["subplans"][0]["ui"] = {"contract": "session-ui", "version": 1, "design_task": "T4",
                                       "visual_review_task": "T3"}
        self.assertCode(plan, "UI_GATE_ORDER")

        plan = base_plan()
        plan["tasks"][0]["ui"] = True
        self.assertCode(plan, "UI_GATE_MISSING")

        plan = base_plan()
        plan["tasks"][0]["ui"] = True
        plan["subplans"][0]["ui"] = {"contract": "session-ui", "version": 1,
                                       "design_task": "T1", "visual_review_task": "T3"}
        self.assertCode(plan, "UI_REVIEW_ORDER")

    def test_verification_environment_resources_and_implementation_sandbox(self):
        plan = base_plan()
        check = plan["tasks"][0]["verification"][0]
        check.update(environment="production", requires=["password=hunter2"])
        report = pc.validate(plan)
        self.assertTrue(any(e.startswith("EXTERNAL_ONLY_IMPLEMENT:") for e in report.errors), report.errors)
        self.assertTrue(any(e.startswith("SECRET_VALUE_IN_PLAN:") for e in report.errors), report.errors)
        check.update(environment="sandbox", requires=["DATABASE_URL"])
        report = pc.validate(plan)
        self.assertFalse(any(e.startswith("SECRET_VALUE_IN_PLAN:") for e in report.errors), report.errors)
        check["requires"] = ["postgres://user:secret@example.test/db"]
        self.assertTrue(any(e.startswith("SECRET_VALUE_IN_PLAN:") for e in pc.validate(plan).errors))

    def test_human_attestation_requires_manual_expected_and_production_authorization(self):
        plan = base_plan()
        check = plan["tasks"][0]["verification"][0]
        plan["tasks"][0]["kind"] = "test"
        check.update(environment="human_attestation")
        self.assertTrue(any(e.startswith("VERIFICATION_ENV_INVALID:") for e in pc.validate(plan).errors))
        check.update(type="manual", expected="Owner confirms the session behavior", environment="production",
                     authorization_needed="Owner grants staging deployment")
        report = pc.validate(plan)
        self.assertTrue(report.ok, report.errors)

    def test_malformed_subplan_collections_are_reported_without_type_errors(self):
        plan = base_plan()
        plan["subplans"][0]["covers"] = [{}]
        plan["composition_gates"] = [{"id": "CG-1", "subplans": [{}], "task": "T2", "criteria": []}]
        plan["tasks"][0]["subplan_id"] = ["SP-1"]
        plan["tasks"][0]["after"] = [[]]
        plan["tasks"][0]["verification"] = None
        plan["tasks"][0]["expected_paths"] = 7
        report = pc.validate(plan)
        self.assertFalse(report.ok)
        self.assertTrue(all(isinstance(error, str) for error in report.errors))

    def test_cross_subplan_undeclared_after_is_rejected(self):
        plan = base_plan()
        second = copy.deepcopy(plan["subplans"][0])
        second.update(id="SP-2", title="Second workstream", covers=["AUTH-2"],
                      acceptance_criteria=["Session endpoint rejects expired credentials"])
        plan["subplans"].append(second)
        plan["tasks"][1]["subplan_id"] = "SP-2"
        plan["tasks"][2]["subplan_id"] = "SP-2"
        plan["tasks"][1]["after"] = ["T1"]
        self.assertTrue(any(e.startswith("SUBPLAN_EDGE:") for e in pc.validate(plan).errors))

    def test_mutually_consumed_frozen_contracts_with_definition_exemptions_are_valid(self):
        plan = base_plan()
        plan["requirements"] = ["AUTH-1", "AUTH-2"]
        first = plan["tasks"]
        first[0]["covers"] = ["AUTH-1"]
        first[0]["acceptance_criteria"] = ["Session contract is defined"]
        first[0]["kind"] = "implement"
        first[0]["after"] = []
        first[0]["expected_paths"] = ["src/session-contract.json"]
        first[1].update(id="T2", subplan_id="SP-1", kind="test", after=["T1", "T4"], covers=["AUTH-1"],
                        acceptance_criteria=["Session contract tests pass"])
        first[2].update(id="T3", subplan_id="SP-1", kind="audit", after=["T2"], covers=["AUTH-1"],
                        expected_paths=["docs/T3.findings.json"], acceptance_criteria=["Session contract audit passes"],
                        verification=[{"type": "command", "value": "engine audit-ledger check docs/T3.findings.json",
                                       "purpose": "audit", "category": "static"}])
        second = [copy.deepcopy(first[0]), copy.deepcopy(first[1]), copy.deepcopy(first[2])]
        second[0].update(id="T4", subplan_id="SP-2", covers=["AUTH-2"], after=[],
                         acceptance_criteria=["Customer contract is defined"])
        second[0]["expected_paths"] = ["src/customer-contract.json"]
        second[1].update(id="T5", subplan_id="SP-2", covers=["AUTH-2"], after=["T4", "T1"],
                         acceptance_criteria=["Customer contract tests pass"])
        second[2].update(id="T6", subplan_id="SP-2", covers=["AUTH-2"], after=["T5"],
                         expected_paths=["docs/T6.findings.json"], acceptance_criteria=["Customer contract audit passes"],
                         verification=[{"type": "command", "value": "engine audit-ledger check docs/T6.findings.json",
                                        "purpose": "audit", "category": "static"}])
        gate_task = copy.deepcopy(first[1])
        gate_task.update(id="T7", subplan_id=None, kind="test", after=["T3", "T6"], covers=["AUTH-1", "AUTH-2"],
                         acceptance_criteria=["Both contract integrations pass"],
                         verification=[{"type": "command", "value": "pytest tests/contracts -q", "purpose": "integrate contracts",
                                        "category": "integration"}])
        plan["tasks"] = first + second + [gate_task]
        plan["tasks"][1]["verification"] = [{"type": "command", "value": "pytest tests/contracts -q", "purpose": "contract test",
                                               "category": "integration"}]
        plan["tasks"][4]["verification"] = [{"type": "command", "value": "pytest tests/contracts -q", "purpose": "contract test",
                                               "category": "integration"}]
        criteria = ["Session contract tests pass", "Customer contract tests pass"]
        plan["subplans"] = [
            {"id": "SP-1", "milestone_id": "M1", "title": "Session contract", "outcome": "Session contract is defined and verified",
             "covers": ["AUTH-1"], "acceptance_criteria": ["Session contract is defined"],
             "produces": [{"contract": "session-api", "version": 1, "defined_by": "T1"}],
             "consumes": [{"contract": "customer-api", "version": 1, "from": "SP-2", "dependency": "contract"}],
             "checkpoints": [], "integration_test_task": "T2", "audit_task": "T3"},
            {"id": "SP-2", "milestone_id": "M1", "title": "Customer contract", "outcome": "Customer contract is defined and verified",
             "covers": ["AUTH-2"], "acceptance_criteria": ["Customer contract is defined"],
             "produces": [{"contract": "customer-api", "version": 1, "defined_by": "T4"}],
             "consumes": [{"contract": "session-api", "version": 1, "from": "SP-1", "dependency": "contract"}],
             "checkpoints": [], "integration_test_task": "T5", "audit_task": "T6"}]
        plan["composition_gates"] = [{"id": "CG-1", "subplans": ["SP-1", "SP-2"], "task": "T7",
                                       "criteria": ["Both contract integrations pass"]}]
        report = pc.validate(plan)
        self.assertTrue(report.ok, report.errors)
        self.assertTrue(any(line.startswith("SUBPLAN_CYCLE:") for line in report.warnings), report.warnings)

    def test_mutual_publication_cycle_is_cut_by_two_producer_only_gates(self):
        subplans = {
            "SP-1": {"consumes": [{"from": "SP-2", "dependency": "publication"}]},
            "SP-2": {"consumes": [{"from": "SP-1", "dependency": "publication"}]},
        }
        errors: list[str] = []
        warnings: list[str] = []
        schema_13._validate_dependency_cycles(errors, warnings, subplans,
                                              [{"subplans": ["SP-1"]}, {"subplans": ["SP-2"]}])
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        schema_13._validate_dependency_cycles(errors, warnings, subplans, [])
        self.assertTrue(any(error.startswith("SUBPLAN_CYCLE:") for error in errors), errors)

    def test_subplans_are_part_of_frozen_hash_and_bind_reports_drift(self):
        plan = base_plan()
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp) / "REQ-GOLDEN"
            directory.mkdir()
            (directory / "SPEC.md").write_text("# Spec\n## Requirements\n- AUTH-1. Session validation\n", encoding="utf-8")
            (directory / "PLAN.md").write_text("---\nstatus: approved\n---\n# Plan\n\n### M1 — Authentication\n"
                                               "- [ ] T1 — Fix session validation · repo: backend · subplan: SP-1\n"
                                               "- [ ] T2 — Exercise integration · repo: backend · after: T1 · subplan: SP-1\n"
                                               "- [ ] T3 — Audit the implementation · repo: backend · after: T2 · subplan: SP-1\n",
                                               encoding="utf-8")
            (directory / "PLAN.json").write_text(pc.dumps(plan), encoding="utf-8")
            frozen = revisions.freeze(directory, plan, "approval")
            plan["subplans"][0]["outcome"] = "The session endpoint now rejects expired tokens"
            plan["revision"] = 2
            (directory / "PLAN.json").write_text(pc.dumps(plan), encoding="utf-8")
            self.assertNotEqual(frozen["sha256"], revisions.sha256(pc.dumps(plan)))
            with self.assertRaises(pc.PlanContractError) as error:
                sync.bind_approved(directory)
            self.assertEqual(error.exception.code, "PLAN_DRIFT")


if __name__ == "__main__":
    unittest.main()
