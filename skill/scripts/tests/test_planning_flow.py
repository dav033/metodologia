from __future__ import annotations

import json
import unittest
from unittest.mock import patch

import test_design_drafts as base

import bt_design_drafts as drafts
import bt_page_planning
import bt_planning_flow as flow
import bt_rounds
from bt_core import _front

PLAN = {"milestones": [{"id": "M1", "title": "Shop"}],
        "subplans": [
            {"id": "SP-1", "milestone_id": "M1", "title": "Data layer", "outcome": "Stores orders."},
            {"id": "SP-2", "milestone_id": "M1", "title": "Checkout screen", "outcome": "The buyer pays.",
             "ui": {"contract": "checkout", "version": 1, "design_task": "T2", "visual_review_task": "T3"}}],
        "tasks": [{"id": "T1", "title": "Store", "subplan_id": "SP-1", "kind": "implement",
                   "acceptance_criteria": ["Orders persist."]},
                  {"id": "T2", "title": "Design checkout", "subplan_id": "SP-2", "kind": "design",
                   "acceptance_criteria": ["Contract approved."]},
                  {"id": "T3", "title": "Build checkout", "subplan_id": "SP-2", "kind": "implement", "ui": True,
                   "acceptance_criteria": ["Pay works."]}]}
SKELETON = {"milestones": PLAN["milestones"], "subplans": PLAN["subplans"], "tasks": []}
SPEC = """---
status: ready
---
# Shop

## Inputs

| Item | Subplan | Where | Who | Status |
|---|---|---|---|---|
| Repository path | all | ~/dev/shop | owner | available |
| Stripe test key | SP-2 | env STRIPE_KEY in ~/.config/shop/.env | owner | {status} |
"""


class FlowTests(unittest.TestCase):
    setUp = base.DraftTests.setUp
    write_plan = base.DraftTests.write_plan
    create = base.DraftTests.create
    finish = base.DraftTests.finish

    def spec(self, status: str) -> None:
        (self.rdir / "SPEC.md").write_text(SPEC.format(status=status), encoding="utf-8")

    def page(self, **q) -> str:
        return bt_page_planning.fragment("demo", "REQ-001", self.rdir, _front(self.rdir / "PLAN.md", "status"), "tok",
                                         bt_page_planning.options(self.rdir, {"lang": "en", **q}))

    def approve(self):
        with patch("bt_scheduler_adapter.plan_compatibility_report", return_value=None), \
                patch("bt_plan_adapter.publishable_problem", return_value=None), \
                patch("bt_plan_adapter.freeze_approved", return_value=None):
            return bt_rounds.plan_decide(self.rdir, True, "", "web")

    def test_requirements_off_the_flow_are_untouched(self):
        self.assertFalse(flow.active(self.rdir))
        self.assertEqual(flow.approval_problems(self.rdir), [])
        self.assertIsNone(flow.design_scope(self.rdir))
        self.assertNotIn('data-k="steps"', self.page())

    def test_interview_then_skeleton_then_subplans(self):
        (self.rdir / "PLAN.json").unlink()
        self.assertTrue(flow.start(self.rdir))
        self.assertFalse(flow.start(self.rdir))
        self.assertEqual(flow.state(self.rdir)["phase"], "interview")
        self.assertIn('data-k="interview"', self.page())
        self.write_plan(SKELETON)
        self.assertEqual(flow.state(self.rdir)["phase"], "outline")
        html = self.page()
        self.assertIn('data-k="outline"', html)
        self.assertIn("Confirmar esqueleto", html)
        self.assertEqual(flow.approval_problems(self.rdir), ["falta confirmar el esqueleto"])

    def test_designer_waits_for_the_skeleton_and_follows_the_focus(self):
        flow.start(self.rdir)
        drafts.request("demo", self.rdir, ["nope@v1"])  # turn drafts on without starting anything
        self.assertEqual(drafts.sync("demo", self.rdir), [])  # no Designer before the skeleton is confirmed
        self.assertIn("Ahora se define SP-1", flow.confirm_outline("demo", self.rdir))
        self.assertEqual(self.orders, [])  # SP-1 has no UI
        self.assertEqual(drafts.sync("demo", self.rdir), [])  # SP-2 is not in focus yet
        self.assertIn("El Designer empezó checkout@v1", flow.focus("demo", self.rdir, "SP-2"))
        self.assertEqual(len(self.orders), 1)
        self.assertEqual(flow.state(self.rdir)["subplans"]["SP-2"]["state"], "defining")

    def test_confirmation_needs_tasks_criteria_inputs_and_a_ready_design(self):
        self.spec("pending")
        self.write_plan(SKELETON)
        flow.start(self.rdir)
        flow.confirm_outline("demo", self.rdir)
        self.assertIn("todavía no tiene tareas", flow.confirm("demo", self.rdir, "SP-1"))
        self.write_plan(PLAN)
        self.assertIn("SP-1 confirmado. Ahora se define SP-2", flow.confirm("demo", self.rdir, "SP-1"))
        refused = flow.confirm("demo", self.rdir, "SP-2")
        self.assertIn("faltan entradas: Stripe test key", refused)
        self.assertIn("Designer sigue trabajando", refused)
        self.finish("D-1")
        self.spec("location given")
        self.assertIn("listo para aprobar", flow.confirm("demo", self.rdir, "SP-2"))
        self.assertEqual(_front(self.rdir / "PLAN.md", "status"), "review")
        self.assertEqual(flow.state(self.rdir)["phase"], "ready")
        self.assertEqual(self.approve(), "approved")
        self.assertEqual(flow.state(self.rdir)["subplans"]["SP-2"]["state"], "confirmed")  # pinning keeps it

    def test_a_change_after_confirmation_reopens_the_subplan_and_blocks_approval(self):
        self.write_plan(PLAN)
        flow.start(self.rdir)
        flow.confirm_outline("demo", self.rdir)
        flow.confirm("demo", self.rdir, "SP-1")
        changed = json.loads(json.dumps(PLAN))
        changed["tasks"][0]["title"] = "Store with retries"
        self.write_plan(changed)
        self.assertEqual(flow.state(self.rdir)["subplans"]["SP-1"]["state"], "changed")
        with self.assertRaises(SystemExit) as raised:
            self.approve()
        self.assertIn("SP-1: cambió después de confirmarlo", str(raised.exception))

    def test_subplan_page_shows_the_flow_actions_and_inputs(self):
        self.spec("pending")
        self.write_plan(PLAN)
        flow.start(self.rdir)
        flow.confirm_outline("demo", self.rdir)
        html = self.page(sp="SP-2")
        self.assertIn('data-k="steps"', html)
        self.assertIn("Subplanes 0/2", html)
        self.assertIn("Definir ahora", html)
        self.assertIn("Entradas · faltan 1", html)
        self.assertIn('value="approve" disabled', html)
        inputs = self.page(sp="SP-2", view="inputs")
        self.assertIn("Stripe test key", inputs)
        self.assertIn("todo el plan", inputs)

    def test_inputs_table_scopes_and_statuses(self):
        self.spec("deferred: use a mock gateway")
        rows = flow.inputs(self.rdir)
        self.assertEqual([(r["item"], r["subplan"], r["pending"]) for r in rows],
                         [("Repository path", "", False), ("Stripe test key", "SP-2", False)])
        self.spec("deferred")  # a deferral without its fallback is not an answer
        self.assertTrue(flow.inputs(self.rdir)[1]["pending"])
        self.assertEqual([r["item"] for r in flow.inputs_for(self.rdir, "SP-1", rows)], ["Repository path"])

    def test_inputs_parser_handles_real_tables(self):
        (self.rdir / "SPEC.md").write_text("""# Shop

## Inputs

| # | Item | Subplan | Where it lives | Supplier | Status |
|---|---|---|---|---|---|
| 1 | Host a\\|b | sp-1, SP2 | ssh `a\\|b` | Owner | available after Friday |
| 2 | Token | SP-1/SP-9 | env TOKEN | Owner | deferred |
| 3 | Repo | all | ~/dev/shop | Owner | location given |

### Notes

| Subplan | Why |
|---|---|
| SP-1 | context |

## Inputs (extra)

| Item | Where |
|---|---|
| Mail account | 1Password |

## Next
""", encoding="utf-8")
        rows = flow.inputs(self.rdir)
        self.assertEqual([(r["item"], r["subplans"], r["pending"]) for r in rows],
                         [("Host a|b", ["SP-1", "SP-2"], True), ("Token", ["SP-1", "SP-9"], True),
                          ("Repo", [], False), ("Mail account", [], True)])
        self.assertEqual(rows[-1]["status"], "sin columna Status")
        self.assertEqual([r["item"] for r in flow.inputs_for(self.rdir, "SP-2", rows)],
                         ["Host a|b", "Repo", "Mail account"])
        flow.start(self.rdir)
        self.write_plan(PLAN)
        flow.confirm_outline("demo", self.rdir)
        self.assertIn("hay entradas para subplanes que no existen: SP-9", flow.approval_problems(self.rdir))

    def test_a_reopened_subplan_becomes_the_focus_and_its_design_follows(self):
        self.write_plan(PLAN)
        flow.start(self.rdir)
        flow.confirm_outline("demo", self.rdir)
        flow.confirm("demo", self.rdir, "SP-1")
        self.finish("D-1")
        drafts.rows(self.rdir)
        flow.confirm("demo", self.rdir, "SP-2")
        self.assertEqual(flow.state(self.rdir)["phase"], "ready")
        changed = json.loads(json.dumps(PLAN))
        changed["subplans"][1]["outcome"] = "The buyer pays in two steps."
        self.write_plan(changed)
        st = flow.state(self.rdir)
        self.assertEqual((st["phase"], st["focus"], st["subplans"]["SP-2"]["state"]), ("subplans", "SP-2", "changed"))
        self.assertEqual(flow.design_scope(self.rdir), {"checkout@v1"})
        self.assertIn("desactualizado", " ".join(st["subplans"]["SP-2"]["problems"]))
        self.assertEqual(drafts.sync("demo", self.rdir), ["checkout@v1"])  # redesigned without a click

    def test_actions_are_refused_off_planning_or_while_plan_json_is_written(self):
        self.write_plan(PLAN)
        self.assertIn("no está en la planificación conjunta", flow.confirm_outline("demo", self.rdir))
        flow.start(self.rdir)
        (self.rdir / "PLAN.json").write_text("{", encoding="utf-8")
        self.assertIn("se está editando", flow.confirm_outline("demo", self.rdir))
        self.assertEqual(flow.state(self.rdir)["phase"], "outline")  # not flipped back to the interview
        self.write_plan(PLAN)
        (self.rdir / "PLAN.md").write_text("---\nstatus: approved\n---\n# Plan\n", encoding="utf-8")
        self.assertIn("ya no está en planificación", flow.confirm_outline("demo", self.rdir))
        self.assertIsNone(flow._load(self.rdir)["outline"])


if __name__ == "__main__":
    unittest.main()
