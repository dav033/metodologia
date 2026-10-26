import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bt_page_plans as pages
import bt_plan_gate as gate
import bt_planning_flow as planning_flow
import bt_presence as presence

SID = "abcd1234-0000-0000-0000-000000000002"


def plan_dir(root, status="draft", with_json=True):
    rdir = root / "p" / "requirements" / "REQ-005-x"
    rdir.mkdir(parents=True)
    (rdir / "PLAN.md").write_text(f"---\nstatus: {status}\n---\n# P\n")
    if with_json:
        (rdir / "PLAN.json").write_text("{}")
    return rdir


class Gate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def planned(self, req="REQ-005"):
        presence.record(self.root, {"session_id": SID, "hook_event_name": "PostToolUse", "tool_name": "Bash",
                                    "tool_input": {"command": f"bitacora --project p plan-json init {req}"}}, "p")

    def failing_check(self):
        class R:
            returncode, stdout = 2, "ERROR T1.complexity: missing\nINVALID: 199 error(s)\n"
        return patch("bt_plan_gate.subprocess.run", return_value=R())

    def test_planning_commands_and_plan_edits_mark_the_requirement_as_planned_by_the_session(self):
        self.planned()
        presence.record(self.root, {"session_id": SID, "hook_event_name": "PostToolUse", "tool_name": "Edit",
                                    "tool_input": {"file_path": "/b/p/requirements/REQ-007-y/PLAN.md"}}, "p")
        self.assertEqual(presence.planned_reqs(self.root, SID), ["p:REQ-005", "p:REQ-007"])

    def test_an_unclassified_draft_keeps_the_session_from_ending_then_lets_go_after_the_limit(self):
        plan_dir(self.root)
        self.planned()
        with self.failing_check():
            for _ in range(gate.MAX_HOLDS):
                why = gate.hold_reason(self.root, "p", SID)
                self.assertIn("REQ-005", why)
                self.assertIn("plan-json check", why)
            self.assertIsNone(gate.hold_reason(self.root, "p", SID))

    def test_the_plan_is_checked_in_its_own_project_not_in_the_one_the_session_is_bound_to(self):
        """A session bound to `pictures` that launched david-ui's REQ-001 was held for pictures' old REQ-001 (no PLAN.json)."""
        plan_dir(self.root)                                           # p/REQ-005 is a valid plan ...
        other = self.root / "q" / "requirements" / "REQ-005-old"
        other.mkdir(parents=True)
        (other / "PLAN.md").write_text("---\nstatus: draft\n---\n# old\n")      # ... and q/REQ-005 an unrelated draft without one
        self.planned()
        ok = type("R", (), {"returncode": 0, "stdout": "OK"})()
        with patch("bt_plan_gate.subprocess.run", return_value=ok):
            self.assertIsNone(gate.hold_reason(self.root, "q", SID))

    def test_missing_plan_json_holds_too_and_a_passing_check_does_not(self):
        plan_dir(self.root, with_json=False)
        self.planned()
        self.assertIn("no PLAN.json", gate.hold_reason(self.root, "p", SID))

    def test_a_plan_that_passes_or_is_no_longer_a_draft_is_left_alone(self):
        rdir = plan_dir(self.root)
        self.planned()

        class Ok:
            returncode, stdout = 0, ""
        with patch("bt_plan_gate.subprocess.run", return_value=Ok()):
            self.assertIsNone(gate.hold_reason(self.root, "p", SID))
        (rdir / "PLAN.md").write_text("---\nstatus: launched\n---\n")
        with self.failing_check():
            self.assertIsNone(gate.hold_reason(self.root, "p", SID))

    def test_a_session_that_planned_nothing_is_never_held(self):
        plan_dir(self.root)
        with self.failing_check():
            self.assertIsNone(gate.hold_reason(self.root, "p", SID))

    def test_the_plan_page_says_loudly_when_nothing_is_classified(self):
        s = {"project": "p", "req_id": "REQ-005", "plan": {"status": "draft", "has_contract": True},
             "summary": {"tasks_total": 2}, "run": {"authority": "none"},
             "milestones": [{"tasks": [{"complexity": None, "state": "pending"}, {"complexity": None, "state": "pending"}]}]}
        html = pages.unclassified_banner(s)
        self.assertIn("2 de 2", html)
        self.assertIn("go REQ-005", html)
        s["milestones"][0]["tasks"][0]["complexity"] = "low"
        s["milestones"][0]["tasks"][1]["complexity"] = "high"
        self.assertEqual(pages.unclassified_banner(s), "")


if __name__ == "__main__":
    unittest.main()

    def test_a_collaborative_plan_is_not_held_before_its_subplans_are_confirmed(self):
        """D-130: the skeleton has no tasks yet, so plan-json check fails until every subplan is defined."""
        rdir = plan_dir(self.root)
        planning_flow.start(rdir)
        self.planned()
        with self.failing_check():
            self.assertIsNone(gate.hold_reason(self.root, "p", SID))
        with self.failing_check(), patch("bt_plan_gate.planning_flow.state", return_value={"phase": "ready"}):
            self.assertIn("plan-json check", gate.hold_reason(self.root, "p", SID))
