"""Approving a plan (`plan-json freeze`) refuses checks that the verifier cannot map to a criterion (config planner.require_mapped_checks)."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bt_config
import bt_plan_adapter as adapter

GOLDEN = Path(__file__).resolve().parents[1] / "bt_planner" / "tests" / "golden" / "input-1.2.0.json"


class MappingGate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.rdir = Path(self.tmp.name) / "REQ-001-x"
        self.rdir.mkdir()
        self.plan = json.loads(GOLDEN.read_text(encoding="utf-8"))

    def setUp_gate_on(self):
        patcher = patch.object(bt_config, "get", side_effect=lambda key, default=None: True if key == "planner.require_mapped_checks" else default)
        patcher.start()
        self.addCleanup(patcher.stop)

    def write(self, plan):
        (self.rdir / "PLAN.json").write_text(json.dumps(plan), encoding="utf-8")

    def mapped(self):
        plan = json.loads(json.dumps(self.plan))
        for task in plan["tasks"]:
            criteria = task["acceptance_criteria"]
            for index, check in enumerate(task["verification"]):
                check["purpose"] = criteria[min(index, len(criteria) - 1)]
            used = {c["purpose"] for c in task["verification"]}
            for criterion in criteria:
                if criterion not in used:
                    task["verification"].append({"type": "command", "value": "python3 extra.py", "purpose": criterion,
                                                 "category": "functional"})
        return plan

    def test_an_unmapped_check_stops_the_approval_and_says_which(self):
        self.setUp_gate_on()
        plan = self.mapped()
        plan["tasks"][0]["verification"][0]["purpose"] = "a paraphrase of the criterion"
        self.write(plan)
        problem = adapter.mapping_problem(self.rdir)
        self.assertIn("PLAN_CHECKS_UNMAPPED", problem)
        self.assertIn("T1.verification[0]", problem)
        self.assertIn("--force", problem)

    def test_a_plan_whose_checks_carry_the_criteria_texts_passes(self):
        self.setUp_gate_on()
        self.write(self.mapped())
        self.assertIsNone(adapter.mapping_problem(self.rdir))

    def test_the_gate_is_off_unless_the_owner_turns_it_on(self):
        plan = self.mapped()
        plan["tasks"][0]["verification"][0]["purpose"] = "a paraphrase"
        self.write(plan)
        with patch.object(bt_config, "get", side_effect=lambda key, default=None: default):
            self.assertIsNone(adapter.mapping_problem(self.rdir))

    def test_approval_consults_the_gate_and_force_skips_it(self):
        self.setUp_gate_on()
        plan = self.mapped()
        plan["tasks"][0]["verification"][0]["purpose"] = "a paraphrase"
        self.write(plan)
        with patch.object(adapter.planner, "check", return_value=adapter.planner_contract.Report()), patch.object(adapter, "plan_consumer_problem", return_value=None):
            self.assertIn("PLAN_CHECKS_UNMAPPED", adapter.publishable_problem(self.rdir))
            self.assertIsNone(adapter.publishable_problem(self.rdir, allow_unmapped=True))


if __name__ == "__main__":
    unittest.main()
