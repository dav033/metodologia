from __future__ import annotations

import copy
import sys
import unittest
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bt_recovery_compiler import (RecoveryCompilationError, compile_recovery_revision, coverage_checks,
                                  replan_verification)
from bt_plan_adapter import validate_candidate
from bt_scheduler_recovery import VerificationMap
from bt_scheduler_recovery.conflict_contracts import ConflictObservation, ConflictSide
from bt_scheduler_recovery_adapter import parse_verification_map


class RecoveryCompilerTests(unittest.TestCase):
    def setUp(self):
        self.plan = {"schema_version": "1.2.0", "plan_id": "REQ-029", "revision": 1, "spec_ref": "SPEC.md",
                     "milestones": [{"id": "M1", "title": "Build", "acceptance_criteria": ["Done"]}],
                     "requirements": ["R1"], "tasks": [
                         {"id": "T1", "milestone_id": "M1", "title": "Implement", "objective": "Implement page rendering behavior",
                          "repository": "repo", "after": [], "complexity": "low", "scope": "small_change",
                          "estimated_minutes": 30, "risk": "low", "coupling": "low", "confidence": "low",
                          "estimate_rationale": "Known implementation pattern", "classification_evidence": {k: {"justification": "This is a documented reason for " + k,
                          "evidence": ["spec:SPEC.md"]} for k in ("complexity", "scope", "duration", "risk", "coupling", "confidence")},
                          "expected_paths": ["web"], "shared_resources": [], "acceptance_criteria": ["Changed page renders expected content"],
                          "verification": [{"type": "command", "value": "npm run typecheck", "purpose": "Types", "category": "static"},
                                           {"type": "command", "value": "npm run build", "purpose": "Build", "category": "static"}],
                          "covers": ["R1"], "kind": "implement"},
                         {"id": "T2", "milestone_id": "M1", "title": "Audit", "objective": "Review the integrated recovery results",
                          "repository": "repo", "after": ["T3"], "complexity": "low", "scope": "small_change",
                          "estimated_minutes": 30, "risk": "low", "coupling": "low", "confidence": "low",
                          "estimate_rationale": "Known audit review pattern", "classification_evidence": {k: {"justification": "This is a documented audit reason for " + k,
                          "evidence": ["spec:SPEC.md"]} for k in ("complexity", "scope", "duration", "risk", "coupling", "confidence")},
                          "expected_paths": ["reviews/audit.findings.json"], "shared_resources": [], "acceptance_criteria": ["Audit findings are recorded"],
                          "verification": [{"type": "manual", "value": "Review", "purpose": "Audit", "expected": "Findings recorded", "category": "functional"}],
                          "covers": ["R1"], "kind": "audit"},
                         {"id": "T3", "milestone_id": "M1", "title": "Run integration checks", "objective": "Run integration checks across the app",
                          "repository": "repo", "after": ["T1"], "complexity": "low", "scope": "small_change",
                          "estimated_minutes": 30, "risk": "low", "coupling": "low", "confidence": "low",
                          "estimate_rationale": "Known integration check setup", "classification_evidence": {k: {"justification": "This is a documented integration reason for " + k,
                          "evidence": ["spec:SPEC.md"]} for k in ("complexity", "scope", "duration", "risk", "coupling", "confidence")},
                          "expected_paths": ["tests"], "shared_resources": [], "acceptance_criteria": ["App integration checks pass"],
                          "verification": [{"type": "command", "value": "python3 tests/integration.py", "purpose": "Run app integration", "category": "integration"}],
                          "covers": ["R1"], "kind": "test"}]}
        source_rows = {name: {"sha256": chr(98 + index) * 64, "document": {"source": name}}
                       for index, name in enumerate(("m1", "plan", "m6", "remediation", "m3_manifest"))}
        self.evidence = {"schema_version": "recovery-evidence/1", "diagnosable": True,
                         "identity": {"plan_id": "REQ-029", "revision": 1, "plan_sha256": source_rows["plan"]["sha256"]},
                         "sources": source_rows,
                         "snapshot_ledger": {"base_sha": "a" * 40, "snapshot_sha": "b" * 40,
                                             "file_count": 1, "total_bytes": 1,
                                             "files": [{"path": "web/page.tsx", "sha256": "a" * 64,
                                                        "blob": "c" * 40, "mode": "100644", "size": 1}]},
                         "actual_changed_paths": ["web/page.tsx"]}
        self.proposal = {"schema_version": "recovery-proposal/1", "confidence": "confirmed",
                         "actions": [{"type": "repair_verification", "owner_task_id": "T1", "task_ids": ["T1"], "verification": []}],
                         "symptom_oracle": {"red_command": "pytest tests/test_bug.py -q", "command": "pytest tests/test_bug.py -q",
                                            "symptom": "broken page renders"}}

    def test_web_coverage_includes_typecheck_and_build(self):
        checks = coverage_checks(self.plan, ["T1"], ["web/page.tsx"], "regression")
        self.assertEqual({row["command"] for row in checks}, {"npm run typecheck", "npm run build"})

    def test_additive_verification_and_map_contract(self):
        vm = {"schema_version": "recovery-verification-map/1",
              "changed_paths": [{"path": "web/page.tsx", "source_digest": "a" * 64, "owner_task_id": "T1"}],
              "checks": [{"check_id": "T1:1", "owner_task_id": "T1", "command": "npm run build",
                          "symptom": "renders", "verdict_identity": "m6:" + "a" * 64}],
              "existing_owner_commands": ["npm run typecheck", "npm run build"],
              "uncovered_paths": [], "uncovered_checks": []}
        rows = replan_verification(self.plan, vm, ["web/page.tsx"])
        self.assertEqual(rows[0]["category"], "regression")
        self.assertEqual(rows[0]["type"], "command")
        self.assertEqual(rows[0]["created_by"], "T1")

    def test_refuses_missing_oracle_and_unknown_paths(self):
        proposal = copy.deepcopy(self.proposal)
        del proposal["symptom_oracle"]
        with self.assertRaises(RecoveryCompilationError):
            compile_recovery_revision(self.plan, self.evidence, proposal)
        evidence = copy.deepcopy(self.evidence)
        evidence["actual_changed_paths"] = ["outside/file.py"]
        with self.assertRaises(RecoveryCompilationError):
            compile_recovery_revision(self.plan, evidence, self.proposal)

    def test_rejects_unsafe_commands_and_exclusive_convergence(self):
        proposal = copy.deepcopy(self.proposal)
        proposal["symptom_oracle"]["command"] = "pytest; rm -rf /"
        with self.assertRaises(RecoveryCompilationError):
            compile_recovery_revision(self.plan, self.evidence, proposal)
        with self.assertRaises(RecoveryCompilationError):
            compile_recovery_revision(self.plan, self.evidence, self.proposal,
                                      convergence={"schema_version": "convergence-work/1", "exclusive_side": True})

    def test_compiles_revision_and_returns_exact_changed_scope(self):
        result = compile_recovery_revision(self.plan, self.evidence, self.proposal)
        self.assertEqual(result.verification_map["schema_version"], "recovery-verification-map/1")
        self.assertEqual(result.verification_map["changed_paths"][0]["path"], "web/page.tsx")
        self.assertEqual(result.verification_map["checks"][0]["check_id"], "CHECK-001")
        VerificationMap.from_dict(result.verification_map)
        self.assertEqual(parse_verification_map(result.verification_map).to_dict(), result.verification_map)
        self.assertEqual(validate_candidate(result.plan), ())
        self.assertIn("T2", result.scope)
        self.assertEqual(result.plan["revision"], 2)
        integration = next(task for task in result.plan["tasks"] if task["id"] == "T4")
        self.assertTrue(any(item.get("category") == "integration" for item in integration["verification"]))
        purposes = [item["purpose"] for item in integration["verification"]]
        self.assertTrue(any("Red step" in purpose for purpose in purposes))
        self.assertTrue(any("Run union owner" in purpose for purpose in purposes))
        red = next(item for item in integration["verification"] if "Red step" in item["purpose"])
        green = next(item for item in integration["verification"]
                     if item["purpose"] == self.proposal["symptom_oracle"]["symptom"])
        self.assertEqual(red["created_by"], integration["id"])
        self.assertEqual(green["created_by"], integration["id"])
        self.assertIn("only the test overlay", red["purpose"])
        self.assertEqual(green["category"], "regression")
        before = {task["id"]: task for task in self.plan["tasks"]}
        after = {task["id"]: task for task in result.plan["tasks"]}
        self.assertEqual(set(result.scope), {task_id for task_id in set(before) | set(after)
                                             if before.get(task_id) != after.get(task_id)})

    def test_convergence_work_adds_producer_rebuilds_and_rewires_consumers(self):
        producer = copy.deepcopy(self.plan["tasks"][0])
        producer.update({"id": "T4", "title": "Converge both accepted sides", "after": ["T1"]})
        for check in producer["verification"]:
            check["created_by"] = "T4"
        rebuild = copy.deepcopy(self.plan["tasks"][0])
        rebuild.update({"id": "T5", "title": "Rebuild stale descendant", "after": ["T4"],
                        "expected_paths": ["web/stale.ts"]})
        for check in rebuild["verification"]:
            check["created_by"] = "T5"
        plan = copy.deepcopy(self.plan)
        plan["tasks"].append({**copy.deepcopy(self.plan["tasks"][0]), "id": "T6", "title": "Consumer",
                               "expected_paths": ["web/consumer.ts"], "after": ["T1"]})
        result = compile_recovery_revision(
            plan, self.evidence, self.proposal,
            convergence={"schema_version": "convergence-work/1", "convergence_task": producer,
                         "rebuilt_tasks": [rebuild], "consumer_updates": [{"task_id": "T6", "after": ["T4"],
                                                                               "remove_after": ["T1"]}],
                         "replaced_task_ids": ["T1"], "actions": [], "evidence_refs": [],
                         "bootstrap": {"schema_version": "conflict-bootstrap/1", "task_id": "T4",
                                       "paths": ["web/page.tsx"], "consumer_task_ids": ["T6"],
                                       "preservation_inputs": [{"side": "left", "sha256": "a" * 64},
                                                               {"side": "right", "sha256": "b" * 64}]}})
        without_convergence = compile_recovery_revision(plan, self.evidence, self.proposal)
        rows = {task["id"]: task for task in result.plan["tasks"]}
        self.assertIn("T4", rows)
        self.assertIn("T5", rows)
        self.assertEqual(rows["T6"]["after"], ["T4"])
        integration = next(task for task in result.plan["tasks"] if task["title"] == "Run integrated recovery verification")
        self.assertTrue({"T4", "T5"} <= set(integration["after"]))
        self.assertTrue({"T4", "T5", "T6"} <= set(result.scope))
        self.assertNotEqual(result.plan, without_convergence.plan)

    def test_refuses_weakened_replacement_and_unjustified_rewire(self):
        proposal = copy.deepcopy(self.proposal)
        proposal["actions"] = [{"type": "correct_tasks", "owner_task_id": "T1", "task_ids": ["T1"],
                                "replacements": [{"id": "T1", "verification": []}]}]
        with self.assertRaises(RecoveryCompilationError) as raised:
            compile_recovery_revision(self.plan, self.evidence, proposal)
        self.assertEqual(raised.exception.code, "WEAKENED_CHECKS")
        convergence = {"schema_version": "convergence-work/1", "convergence_task": "T1",
                       "consumer_updates": [{"task_id": "T3", "after": [], "remove_after": ["T1"]}],
                       "replaced_task_ids": [], "actions": [], "evidence_refs": []}
        with self.assertRaises(RecoveryCompilationError) as raised:
            compile_recovery_revision(self.plan, self.evidence, self.proposal, convergence=convergence)
        self.assertEqual(raised.exception.code, "INVALID_CONVERGENCE")

    def test_rejects_text_only_or_unbound_snapshot_evidence(self):
        proposal = copy.deepcopy(self.proposal)
        proposal["confidence"] = "inferred"
        with self.assertRaises(RecoveryCompilationError) as raised:
            compile_recovery_revision(self.plan, self.evidence, proposal)
        self.assertEqual(raised.exception.code, "TEXT_ONLY_PROPOSAL")
        evidence = copy.deepcopy(self.evidence)
        del evidence["sources"]["m6"]["document"]
        with self.assertRaises(RecoveryCompilationError) as raised:
            compile_recovery_revision(self.plan, evidence, self.proposal)
        self.assertEqual(raised.exception.code, "INVALID_EVIDENCE")

    def test_rejects_unknown_owner_unsafe_repair_and_weakened_acceptance(self):
        proposal = copy.deepcopy(self.proposal)
        proposal["actions"][0]["owner_task_id"] = "T99"
        with self.assertRaises(RecoveryCompilationError) as raised:
            compile_recovery_revision(self.plan, self.evidence, proposal)
        self.assertEqual(raised.exception.code, "UNKNOWN_TASK")

        proposal = copy.deepcopy(self.proposal)
        proposal["actions"] = [{"type": "repair_verification", "owner_task_id": "T1", "task_ids": ["T1"],
                                "verification": [{"type": "command", "value": "pytest; rm -rf /",
                                                  "created_by": "T1"}]}]
        with self.assertRaises(RecoveryCompilationError) as raised:
            compile_recovery_revision(self.plan, self.evidence, proposal)
        self.assertEqual(raised.exception.code, "UNSAFE_COMMAND")

        proposal["actions"] = [{"type": "correct_tasks", "owner_task_id": "T1", "task_ids": ["T1"],
                                "replacements": [{"id": "T1", "acceptance_criteria": []}]}]
        with self.assertRaises(RecoveryCompilationError) as raised:
            compile_recovery_revision(self.plan, self.evidence, proposal)
        self.assertEqual(raised.exception.code, "WEAKENED_CRITERIA")

        proposal["actions"] = [
            {"type": "correct_tasks", "owner_task_id": "T3", "task_ids": ["T3"],
             "replacements": [{"id": "T3", "after": []}]},
            {"type": "repair_verification", "owner_task_id": "T1", "task_ids": ["T1"], "verification": []},
        ]
        with self.assertRaises(RecoveryCompilationError) as raised:
            compile_recovery_revision(self.plan, self.evidence, proposal)
        self.assertEqual(raised.exception.code, "WEAKENED_GATES")

    def test_convergence_cycle_is_rejected_by_planner(self):
        producer = copy.deepcopy(self.plan["tasks"][0])
        producer.update({"id": "T4", "title": "Convergence self-cycle", "after": ["T4"]})
        for check in producer["verification"]:
            check["created_by"] = "T4"
        convergence = {"schema_version": "convergence-work/1", "convergence_task": producer,
                       "rebuilt_tasks": [], "consumer_updates": [], "actions": [], "evidence_refs": [],
                       "bootstrap": {"schema_version": "conflict-bootstrap/1", "task_id": "T4",
                                     "paths": ["web/page.tsx"], "consumer_task_ids": [],
                                     "preservation_inputs": [{"side": "left", "sha256": "c" * 64},
                                                             {"side": "right", "sha256": "d" * 64}]}}
        with self.assertRaises(RecoveryCompilationError) as raised:
            compile_recovery_revision(self.plan, self.evidence, self.proposal, convergence=convergence)
        self.assertEqual(raised.exception.code, "PLANNER_INVALID")

    def test_refuses_missing_web_build_coverage(self):
        plan = copy.deepcopy(self.plan)
        plan["tasks"][0]["verification"] = [plan["tasks"][0]["verification"][0]]
        with self.assertRaises(RecoveryCompilationError) as raised:
            coverage_checks(plan, ["T1"], ["web/page.tsx"], "regression")
        self.assertEqual(raised.exception.code, "MISSING_OWNER_CHECK")

    def test_adds_cross_check_only_when_owner_policy_requires_it(self):
        with patch("bt_recovery_compiler.second_auditor_required", return_value=True):
            result = compile_recovery_revision(self.plan, self.evidence, self.proposal)
        audits = [task for task in result.plan["tasks"] if task["kind"] == "audit"]
        self.assertEqual(len(audits), 2)
        cross_check = next(task for task in audits if task["id"] != "T2")
        self.assertIn("Cross-check audit", cross_check["title"])
        integration = next(task for task in result.plan["tasks"] if task["title"] == "Run integrated recovery verification")
        self.assertIn(integration["id"], cross_check["after"])
        self.assertIn(cross_check["id"], result.scope)

    def test_refuses_convergence_outside_named_owner_paths(self):
        producer = copy.deepcopy(self.plan["tasks"][0])
        producer.update({"id": "T4", "title": "Out of scope convergence", "expected_paths": ["server"]})
        convergence = {"schema_version": "convergence-work/1", "convergence_task": producer,
                       "rebuilt_tasks": [], "consumer_updates": [], "actions": [], "evidence_refs": [],
                       "bootstrap": {"schema_version": "conflict-bootstrap/1", "task_id": "T4",
                                     "paths": ["web/page.tsx"], "consumer_task_ids": [],
                                     "preservation_inputs": [{"side": "left", "sha256": "c" * 64},
                                                             {"side": "right", "sha256": "d" * 64}]}}
        with self.assertRaises(RecoveryCompilationError) as raised:
            compile_recovery_revision(self.plan, self.evidence, self.proposal, convergence=convergence)
        self.assertEqual(raised.exception.code, "OWNER_SCOPE_CHANGED")

    def test_accepts_validated_t3a_conflict_observation_as_convergence_bootstrap(self):
        observation = ConflictObservation(
            source_type="start", run_id="run", plan_id="REQ-029", revision=1,
            plan_sha256="a" * 64, task_id="T1", attempt_id="attempt1", token="token1",
            consumer_id="consumer1", repository_id="repo", paths=("web/page.tsx",),
            sides=(ConflictSide(0, "accepted", "T1", "attempt1", "b" * 64, "c" * 64, "d" * 64),
                   ConflictSide(1, "accepted", "T3", "attempt3", "e" * 64, "f" * 64, "1" * 64)),
            original_merge_base="2" * 64, carry_ancestry=(), evidence_digests=("3" * 64,),
            ordinary_rework_refusal="overlap_requires_structural_recovery",
            ordinary_rework_refusal_detail="overlapping accepted work requires a convergence task").to_dict()
        producer = copy.deepcopy(self.plan["tasks"][0])
        producer.update({"id": "T4", "title": "Converge accepted work", "after": ["T1", "T3"]})
        for check in producer["verification"]:
            check["created_by"] = "T4"
        convergence = {"schema_version": "convergence-work/1", "convergence_task": producer,
                       "rebuilt_tasks": [], "consumer_updates": [], "actions": [], "evidence_refs": [],
                       "replaced_task_ids": [], "bootstrap": observation}
        result = compile_recovery_revision(self.plan, self.evidence, self.proposal, convergence=convergence)
        self.assertIn("T4", result.scope)
        self.assertIn("T4", {task["id"] for task in result.plan["tasks"]})


if __name__ == "__main__":
    unittest.main()
