"""Find late product feedback before a multi-milestone plan starts."""
import unittest

from bt_planner import contract


class MilestoneAuditTests(unittest.TestCase):
    def plan(self):
        return {"schema_version": "1.2.0", "plan_id": "REQ-1", "revision": 1,
                "milestones": [{"id": "M1"}, {"id": "M2"}],
                "tasks": [{"id": "T1", "kind": "implement", "milestone_id": "M1", "after": []},
                          {"id": "T2", "kind": "implement", "milestone_id": "M2", "after": ["T1"]},
                          {"id": "T3", "kind": "audit", "milestone_id": "M2", "after": ["T2"]}]}

    def advice(self, plan):
        return [w for w in contract.validate(plan).warnings if "milestone product audit" in w]

    def test_final_only_audit_warns_before_later_work_begins(self):
        warnings = self.advice(self.plan())
        self.assertEqual(len(warnings), 1)
        self.assertIn("M1", warnings[0])

    def test_an_audit_that_gates_the_next_milestone_settles_the_warning(self):
        plan = self.plan()
        plan["tasks"].insert(1, {"id": "T1a", "kind": "audit", "milestone_id": "M1", "after": ["T1"]})
        plan["tasks"][2]["after"] = ["T1a"]
        self.assertEqual(self.advice(plan), [])

    def test_an_ungated_audit_does_not_prevent_late_feedback(self):
        plan = self.plan()
        plan["tasks"].append({"id": "T1a", "kind": "audit", "milestone_id": "M1", "after": ["T1"]})
        self.assertEqual(len(self.advice(plan)), 1)

    def test_a_single_milestone_does_not_require_an_extra_audit(self):
        plan = self.plan()
        plan["tasks"][1]["milestone_id"] = "M1"
        self.assertEqual(self.advice(plan), [])
