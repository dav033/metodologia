"""A check maps to a criterion by exact text. The reverse direction (a check whose purpose is no criterion) was never linted, and
it was the most frequent stop of four real runs (CHECK_UNMAPPED)."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from bt_planner import contract, quality

GOLDEN = Path(__file__).with_name("golden")


def plan_with(criteria, checks):
    plan = json.loads((GOLDEN / "input-1.2.0.json").read_text(encoding="utf-8"))
    task = plan["tasks"][0]
    task["acceptance_criteria"] = list(criteria)
    task["verification"] = [{"type": "command", "value": f"python3 t{n}.py", "purpose": purpose, "category": "functional"}
                            for n, purpose in enumerate(checks)]
    return plan, task["id"]


class UnmappedChecks(unittest.TestCase):
    def test_a_purpose_that_is_no_criterion_is_found_with_the_closest_one(self):
        plan, tid = plan_with(["The login page shows the error text"], ["The login page shows the error text", "Login page error text"])
        found = [f for f in quality.unmapped_checks(plan) if f["task_id"] == tid]
        self.assertEqual([(f["task_id"], f["verification_index"]) for f in found], [(tid, 1)])
        self.assertEqual(found[0]["closest"], "The login page shows the error text")

    def test_exact_texts_and_checks_sharing_a_criterion_are_fine(self):
        plan, tid = plan_with(["A", "B"], ["A", "A", "B"])
        self.assertEqual([f for f in quality.unmapped_checks(plan) if f["task_id"] == tid], [])

    def test_a_group_label_has_no_closest_criterion(self):
        plan, tid = plan_with(["The login page shows the error text"], ["Regression suite"])
        self.assertIsNone([f for f in quality.unmapped_checks(plan) if f["task_id"] == tid][0]["closest"])

    def test_the_check_of_a_plan_reports_each_one_as_a_warning_not_an_error(self):
        plan, tid = plan_with(["The login page shows the error text"], ["Login page error text"])
        report = contract.validate(plan)
        text = [w for w in report.warnings if "CHECK_UNMAPPED" in w and w.startswith(f"{tid}.")]
        self.assertEqual(len(text), 1)
        self.assertIn(f"{tid}.verification[0]", text[0])
        self.assertFalse([e for e in report.errors if "CHECK_UNMAPPED" in e])               # legacy plans keep validating


if __name__ == "__main__":
    unittest.main()
