from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import bt_scheduler_adapter as adapter
from test_scheduler_integration import Case, freeze, plan_text


class RecoveryTaskMetadata(Case):
    def test_approved_plan_preserves_compiler_metadata_and_rejects_unmarked_claims(self):
        tasks = [
            {"id": "T1", "milestone_id": "M1", "repository": "app", "expected_paths": ["src/a.py"],
             "after": [], "recovery_task": True, "recovery_case_id": "fixture-case-1",
             "recovery_owner_tasks": ["T0"], "bootstrap": {"required": True, "task_id": "T1"}},
            {"id": "T2", "milestone_id": "M1", "repository": "app", "expected_paths": ["src/b.py"],
             "after": [], "recovery_task": False, "recovery_case_id": "owner-authored-value"},
        ]
        plan_data = json.loads(plan_text(1, tasks))
        plan_data["schema_version"] = "1.2.0"
        for task in plan_data["tasks"]:
            task["kind"] = "implement"
        freeze(self.rdir, json.dumps(plan_data))

        plan = adapter.approved_plan(self.rdir)

        self.assertEqual(plan.task("T1").meta, {
            "kind": "implement", "recovery_task": True, "recovery_case_id": "fixture-case-1",
            "recovery_owner_tasks": ["T0"], "bootstrap": {"required": True, "task_id": "T1"},
        })
        self.assertNotIn("recovery_case_id", plan.task("T2").meta)

    def test_classification_overlay_cannot_replace_recovery_owned_metadata(self):
        port = object.__new__(adapter.DecisionAssignmentPort)
        port.classification_overlay = lambda: {"T1": {"recovery_case_id": "replacement", "kind": "docs"}}

        effective = port.effective_meta("T1", {"recovery_task": True, "recovery_case_id": "fixture-case-1"})

        self.assertEqual(effective, {"recovery_task": True, "recovery_case_id": "fixture-case-1", "kind": "docs"})


if __name__ == "__main__":
    unittest.main()
