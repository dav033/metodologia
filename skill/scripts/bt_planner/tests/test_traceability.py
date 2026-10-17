"""Schema 1.2.0 requirement-to-task traceability and SPEC extraction."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from bt_planner import contract as pc
from bt_planner import sync, traceability

GOLDEN = Path(__file__).with_name("golden")


def proposed_plan() -> dict:
    return json.loads((GOLDEN / "input-1.2.0.json").read_text(encoding="utf-8"))


class RequirementTraceability(unittest.TestCase):
    def test_fully_covered_plan_matches_spec(self):
        plan = proposed_plan()
        errors, warnings = traceability.check(plan, {"R1"})
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_uncovered_requirement_names_its_id_through_contract(self):
        plan = proposed_plan()
        plan["requirements"].append("R2")
        errors = pc.validate(plan, spec_ids={"R1", "R2"}).errors
        self.assertTrue(any("requirements.R2" in error and "no task covers" in error for error in errors), errors)

    def test_empty_covers_is_reported_as_orphan_work(self):
        plan = proposed_plan()
        plan["tasks"][0]["covers"] = []
        errors, _ = traceability.check(plan, {"R1"})
        self.assertTrue(any("T1.covers" in error and "orphan work" in error for error in errors), errors)

    def test_invalid_and_undeclared_cover_ids_are_reported_per_task(self):
        plan = proposed_plan()
        plan["tasks"][0]["covers"] = ["bad", "R9"]
        errors, _ = traceability.check(plan, {"R1"})
        joined = "\n".join(errors)
        self.assertIn("T1.covers[0]", joined)
        self.assertIn("T1.covers[1]: R9 is not declared", joined)
        self.assertIn("T1.covers: task covers no declared requirement", joined)

    def test_requirement_ids_must_be_valid_and_unique(self):
        plan = proposed_plan()
        plan["requirements"] = ["R1", "R1", "invalid"]
        errors, _ = traceability.check(plan, {"R1"})
        joined = "\n".join(errors)
        self.assertIn("duplicate requirement ID R1", joined)
        self.assertIn("requirements[2]", joined)

    def test_missing_spec_context_is_a_warning(self):
        errors, warnings = traceability.check(proposed_plan())
        self.assertEqual(errors, [])
        self.assertTrue(any("SPEC Requirements IDs are unavailable" in warning for warning in warnings), warnings)

    def test_coverage_report_maps_each_requirement_to_planned_tasks(self):
        plan = proposed_plan()
        plan["requirements"].append("R2")
        plan["tasks"][0]["covers"] = ["R1", "R2"]
        self.assertEqual(traceability.coverage_report(plan), {"R1": ["T1", "T2"], "R2": ["T1"]})


class SpecRequirements(unittest.TestCase):
    def test_extracts_supported_ids_only_inside_requirements_section(self):
        text = """# Proposal
- R0. Outside the target section

## Requirements
- R1. First requirement
  - US-1: Nested requirement ID
1. ABC9: Ordered requirement ID
```md
- R99. This is an example, not a requirement
```
### Notes
- R88. Still inside the Requirements section
## Design
- R77. Outside the target section
"""
        self.assertEqual(traceability.requirements_from_spec(text), {"R1", "US-1", "ABC9", "R88"})

    def test_missing_heading_is_distinct_from_an_empty_section(self):
        self.assertIsNone(traceability.requirements_from_spec("# Overview\n- R1. Not in requirements\n"))
        self.assertEqual(traceability.requirements_from_spec("## Requirements\n\n## Design\n"), set())

    def test_check_passes_spec_ids_to_the_1_2_validator(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan_dir = root / "REQ-042-demo"
            plan_dir.mkdir()
            (plan_dir / "SPEC.md").write_text("## Requirements\n- R2. From SPEC\n", encoding="utf-8")
            (plan_dir / "PLAN.md").write_text("# Plan\n", encoding="utf-8")
            plan = proposed_plan()
            plan["plan_id"] = "REQ-042"
            report = sync.check(plan_dir, plan)

        joined = "\n".join(report.errors)
        self.assertIn("SPEC requirement R2 is missing from PLAN.json", joined)
        self.assertIn("R1 is declared in PLAN.json but missing from SPEC Requirements", joined)

    def test_legacy_schema_does_not_read_requirements_for_validation(self):
        plan = proposed_plan()
        plan["schema_version"] = "1.1.0"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "SPEC.md").write_text("## Requirements\n- R2. From SPEC\n", encoding="utf-8")
            with patch.object(traceability, "read_spec_ids", side_effect=AssertionError):
                report = sync.check(root, plan)
        self.assertFalse(any("requirements" in finding.casefold() for finding in report.errors + report.warnings))


if __name__ == "__main__":
    unittest.main()
