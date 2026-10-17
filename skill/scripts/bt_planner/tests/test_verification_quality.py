"""Schema 1.2.0 verification categories, criterion honesty and planned-work reporting."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from bt_planner import contract as pc
from bt_planner import quality

GOLDEN = Path(__file__).with_name("golden")


def proposed_plan() -> dict:
    return json.loads((GOLDEN / "input-1.2.0.json").read_text(encoding="utf-8"))


class VerificationQuality(unittest.TestCase):
    def test_all_categories_are_allowed_for_command_and_manual_verification(self):
        for index, category in enumerate(quality.VERIFICATION_CATEGORIES):
            with self.subTest(category=category):
                plan = proposed_plan()
                verification = plan["tasks"][0]["verification"][0]
                verification["category"] = category
                if index % 2:
                    verification.update({"type": "manual", "expected": "The result is visible"})
                self.assertFalse(any("T1.verification[0].category" in finding
                                     for finding in quality.verification_findings(plan)))

    def test_each_verification_needs_one_allowed_category_independent_of_type(self):
        plan = proposed_plan()
        plan["tasks"][0]["verification"][0].pop("category")
        plan["tasks"][1]["verification"][0]["category"] = ["functional", "regression"]
        errors = "\n".join(pc.validate(plan, spec_ids={"R1"}).errors)
        self.assertIn("T1.verification[0].category: missing", errors)
        self.assertIn("T2.verification[0].category", errors)

        plan["tasks"][0]["verification"][0].update({"type": "manual", "expected": "The user sees the result"})
        plan["tasks"][0]["verification"][0]["category"] = "product"
        self.assertFalse(any("T1.verification[0].category" in finding
                             for finding in quality.verification_findings(plan)))

    def test_report_maps_declared_categories_to_every_covered_requirement(self):
        report = quality.verification_report(proposed_plan())
        self.assertEqual(set(report), {"verification_categories", "criteria_without_command"})
        coverage = report["verification_categories"]["R1"]
        self.assertEqual(coverage["categories"], ["functional", "regression"])
        self.assertNotIn("product_acceptance", coverage)
        self.assertEqual([row["task_id"] for row in coverage["verifications"]], ["T1", "T2"])

    def test_unmatched_criterion_names_m6_needs_review(self):
        plan = proposed_plan()
        findings = "\n".join(quality.verification_findings(plan))
        self.assertIn("T1.acceptance_criteria", findings)
        self.assertIn("'Expired sessions are rejected'", findings)
        self.assertIn("no verification purpose matches after whitespace trim", findings)
        self.assertIn("M6 will mark this criterion NEEDS_REVIEW", findings)
        missing = quality.criteria_without_command(plan)
        self.assertTrue(any(item["task_id"] == "T1" and item["m6_criterion_status"] == "NEEDS_REVIEW"
                            for item in missing), missing)

    def test_whitespace_normalized_match_still_warns_about_m6_exact_comparison(self):
        plan = proposed_plan()
        criterion = plan["tasks"][0]["acceptance_criteria"][0]
        plan["tasks"][0]["verification"][0]["purpose"] = f" {criterion} "
        findings = "\n".join(quality.verification_findings(plan))
        self.assertIn("purpose matches after whitespace trim, but M6 currently compares it exactly", findings)
        self.assertIn("M6 will mark this criterion NEEDS_REVIEW", findings)
        self.assertTrue(any(item["reason"] == "whitespace_mismatch" for item in quality.criteria_without_command(plan)))

    def test_created_by_is_listed_as_planned_work_not_existing_evidence(self):
        plan = proposed_plan()
        verification = plan["tasks"][0]["verification"][0]
        verification.update({"created_by": "T2", "purpose": plan["tasks"][0]["acceptance_criteria"][0]})
        planned = quality.planned_verifications(plan)
        self.assertEqual(len(planned), 1)
        self.assertEqual(planned[0]["status"], "planned_work")
        self.assertEqual(planned[0]["created_by"], "T2")
        coverage = quality.verification_categories(plan)["R1"]
        self.assertEqual(len(coverage["planned_work"]), 1)
        self.assertTrue(any("planned work, not existing evidence" in finding
                            for finding in quality.verification_findings(plan)))
        self.assertFalse(any(item["task_id"] == "T1" for item in quality.criteria_without_command(plan)))

    def test_manual_only_requirement_is_flagged_for_m6_review(self):
        plan = proposed_plan()
        for task in plan["tasks"]:
            verification = task["verification"][0]
            verification.update({"type": "manual", "expected": "The change is visible"})
        coverage = quality.verification_categories(plan)["R1"]
        self.assertTrue(coverage["manual_only"])
        findings = "\n".join(quality.verification_findings(plan))
        self.assertIn("requirements.R1: covering tasks have only manual verification", findings)
        self.assertIn("M6 will leave criteria NEEDS_REVIEW", findings)

    def test_lower_level_checks_are_not_reported_as_product_acceptance(self):
        plan = proposed_plan()
        findings = "\n".join(quality.verification_findings(plan))
        self.assertIn("Planner review whether user-visible/product claims need product-level verification", findings)
        self.assertIn("lower-level tests are not product acceptance", findings)
        self.assertNotIn("accepted", quality.verification_report(plan)["verification_categories"]["R1"])

    def test_planned_product_category_is_not_treated_as_existing_product_evidence(self):
        plan = proposed_plan()
        verification = plan["tasks"][0]["verification"][0]
        verification.update({"category": "product", "created_by": "T2"})
        findings = "\n".join(quality.verification_findings(plan))
        self.assertIn("product-category verification is only planned work", findings)

    def test_categories_are_contract_errors_but_quality_findings_remain_warnings(self):
        plan = proposed_plan()
        plan["tasks"][0]["verification"][0].pop("category")
        report = pc.validate(plan, spec_ids={"R1"})
        self.assertTrue(any("T1.verification[0].category: missing" in error for error in report.errors), report.errors)
        self.assertTrue(any("acceptance_criteria" in warning for warning in report.warnings), report.warnings)


if __name__ == "__main__":
    unittest.main()
