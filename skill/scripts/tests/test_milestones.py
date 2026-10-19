"""Plan parsing, milestone grouping and idempotent audit tasks of the run state."""
from __future__ import annotations

import unittest

from run_case_support import MilestoneCase, rs


class PlanUnits(MilestoneCase):
    def test_plan_parses_milestones_kind_risk_and_heading_boundaries(self):
        self.make_milestone_req([
            ("### M1 — First", ["- [ ] T1 — Write guide · kind: docs · risk: high",
                                  "- [ ] T2 — Add tests · after: T1"]),
            ("## Other section", ["- [ ] T3 — Outside milestone · kind: research"]),
            ("### M2 — Second", ["- [ ] T4 — Review design"]),
        ])
        parsed = rs.parse_plan(self.rdir / "PLAN.md")
        self.assertEqual([t["milestone"] for t in parsed], ["M1", "M1", None, "M2"])
        self.assertEqual((parsed[0]["kind"], parsed[0]["risk"]), ("docs", "high"))
        self.assertEqual(parsed[1]["kind"], "test")
        self.assertEqual(parsed[3]["kind"], "audit")
        self.assertEqual(rs.milestones(self.rdir / "PLAN.md"), [
            {"id": "M1", "title": "First", "tasks": ["T1", "T2"]},
            {"id": "M2", "title": "Second", "tasks": ["T4"]},
        ])

    def test_plan_without_groups_keeps_single_task_units(self):
        self.make_req(["- [ ] T1 — one", "- [ ] T2 — two"])
        state = rs.init_state(self.project, self.rdir, "claude", "haiku", True)
        self.assertEqual([t["milestone"] for t in rs.parse_plan(self.rdir / "PLAN.md")], [None, None])
        self.assertEqual(rs.unit_of(state, state["tasks"][0]), [state["tasks"][0]])
        self.assertEqual(rs.milestones(self.rdir / "PLAN.md"), [])

    def test_sync_inserts_idempotent_audits_after_each_group(self):
        self.make_milestone_req([
            ("### M1 — First", ["- [ ] T1 — one", "- [ ] T2 — two · after: T1"]),
            ("### M2 — Second", ["- [ ] T3 — three"]),
        ])
        state = rs.init_state(self.project, self.rdir, "claude", "haiku", True, audit=True)
        self.assertEqual([t["id"] for t in state["tasks"]], ["T1", "T2", "M1-audit", "T3", "M2-audit"])
        first_audit = state["tasks"][2]
        self.assertEqual((first_audit["after"], first_audit["kind"], first_audit["tier"]),
                         (["T1", "T2"], "audit", 1))
        rs.sync_plan(state, self.rdir)
        self.assertEqual([t["id"] for t in state["tasks"]].count("M1-audit"), 1)
        plain = rs.init_state(self.project, self.rdir, "claude", "haiku", True, audit=False)
        self.assertNotIn("M1-audit", [t["id"] for t in plain["tasks"]])

    def test_unit_contains_ready_pending_members_but_never_audit(self):
        self.make_milestone_req([("### M1 — First", ["- [ ] T1 — one", "- [ ] T2 — two · after: T1",
                                                       "- [ ] T3 — three · after: T2"])])
        state = rs.init_state(self.project, self.rdir, "claude", "haiku", True, audit=True)
        unit = rs.next_unit(state)
        self.assertEqual([t["id"] for t in unit], ["T1", "T2", "T3"])
        self.assertEqual(rs.unit_label(unit), "M1")
        state["tasks"][0]["status"] = "done"
        self.assertEqual([t["id"] for t in rs.unit_of(state, state["tasks"][1])], ["T2", "T3"])
        state["tasks"][0]["status"] = "todo"
        state["tasks"][1]["status"] = "blocked"
        state["tasks"][2]["after"] = ["T1"]
        self.assertEqual([t["id"] for t in rs.unit_of(state, state["tasks"][0])], ["T1", "T3"])
        self.assertEqual(rs.unit_of(state, state["tasks"][3]), [state["tasks"][3]])


if __name__ == "__main__":
    unittest.main()
