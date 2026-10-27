"""The Designer's UI brief: product scope only, Planner hand-off merged, staleness and brief wording."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bt_delegate
import bt_design_brief
import bt_design_directions as directions
import bt_design_drafts as drafts
import bt_design_iterate as iterate
import bt_design_ui_brief as ui_brief

SPEC = """# Shop

## Requirements
- R9. When a user adds a rectangular table, the system shall let them set size and chairs.
- R10. When a user exports to GLB, the system shall produce a file Blender opens.

## Behavior — SP-2 tables
Details.
"""
OUTCOME = "A user adds a rectangular table and edits its size and chairs."
PRODUCT = "Adding a rectangular table exposes length, depth and chair count."
REVIEW = "Phone and desktop renderings of table editing match the approved contract."
HARNESS = "The harness starts a real next start build and compares Blender-imported positions."
CHECKSUM = "An explicit setup step provisions a checksum-verified portable Blender LTS."
COPY = "The repository contract is byte-identical to the owner-approved tables@v1 artifact."
AUDIT = "An independent SP-2 spec and standards audit has no open critical findings."
PLAN = {"subplans": [
    {"id": "SP-1", "title": "Data", "outcome": "Stores orders."},
    {"id": "SP-2", "title": "Tables", "outcome": OUTCOME, "covers": ["R9", "R10"],
     "acceptance_criteria": [COPY, PRODUCT, HARNESS, CHECKSUM, OUTCOME, REVIEW, AUDIT],
     "ui": {"contract": "tables", "version": 1, "design_task": "T2.1", "visual_review_task": "T2.4"}}],
    "tasks": [
        {"id": "T2.1", "title": "Copy the design contract", "subplan_id": "SP-2", "kind": "design", "ui": False,
         "acceptance_criteria": [COPY]},
        {"id": "T2.2", "title": "Add rectangular tables", "subplan_id": "SP-2", "kind": "implement", "ui": True,
         "objective": "Tables through the existing editor", "acceptance_criteria": [PRODUCT],
         "expected_paths": ["src/editor/Tables.tsx"], "shared_resources": ["DATABASE_URL"],
         "verification": [{"type": "command", "value": "npm test -- tables-secret-cmd"}]},
        {"id": "T2.3", "title": "Implement the Blender harness", "subplan_id": "SP-2", "kind": "implement",
         "ui": False, "acceptance_criteria": [HARNESS, CHECKSUM], "expected_paths": ["scripts/harness.py"]},
        {"id": "T2.4", "title": "Review rendered tables", "subplan_id": "SP-2", "kind": "audit", "ui": False,
         "acceptance_criteria": [REVIEW]},
        {"id": "T2.5", "title": "Audit tables", "subplan_id": "SP-2", "kind": "audit", "ui": False,
         "acceptance_criteria": [AUDIT, OUTCOME]}]}
PLANNER = {"flows": [{"name": "Add a table", "steps": ["Open Fondos y muebles", "Pick the rectangular card"]}],
           "screens_states": ["Editor with inspector open", "Export error"],
           "existing_surface": {"routes": ["/taller"], "paths": ["src/app/taller/page.tsx"], "notes": "Keep toolbar"},
           "must_not_change": ["Top navigation"], "copy_rules": ["Use the existing Spanish labels"]}


class UIBrief(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.rdir = Path(self.tmp.name)
        self.write(PLAN)
        (self.rdir / "SPEC.md").write_text(SPEC, encoding="utf-8")
        (self.rdir / "PLAN.md").write_text("---\nstatus: review\n---\n# Plan", encoding="utf-8")

    def write(self, plan):
        (self.rdir / "PLAN.json").write_text(json.dumps(plan), encoding="utf-8")

    def row(self):
        return next(s for s in drafts.subplans(self.rdir) if s["id"] == "SP-2")

    def test_engineering_classifier(self):
        for text in (HARNESS, CHECKSUM, COPY, AUDIT, "A production build on loopback completes the flow."):
            self.assertTrue(ui_brief.engineering(text), text)
        for text in (PRODUCT, REVIEW, "An administrator sees the audit log of role changes."):
            self.assertFalse(ui_brief.engineering(text), text)

    def test_brief_keeps_product_scope_and_drops_engineering(self):
        text = ui_brief.build(self.rdir, self.row(), {})
        for needle in (OUTCOME, "R9: When a user adds a rectangular table", "R10: When a user exports to GLB",
                       PRODUCT, REVIEW, "T2.1", "T2.2 — Add rectangular tables", "T2.4", "«Behavior — SP-2 tables»",
                       "Omitido a propósito", "Tareas omitidas: T2.3, T2.5", "CAMBIO sobre una superficie existente"):
            self.assertIn(needle, text)
        for needle in (HARNESS, CHECKSUM, COPY, AUDIT, "Implement the Blender harness", "tables-secret-cmd",
                       "src/editor/Tables.tsx", "DATABASE_URL", self.row()["digest"]):
            self.assertNotIn(needle, text)
        self.assertEqual(text.count(OUTCOME), 1)
        self.assertIn("No hay repositorio clonado", text)

    def test_planner_ui_brief_merges_and_wins(self):
        plan = json.loads(json.dumps(PLAN))
        plan["subplans"][1]["ui_brief"] = {**PLANNER, "criteria": ["Only this criterion"]}
        self.write(plan)
        text = ui_brief.build(self.rdir, self.row(), {"web": self.rdir})
        for needle in ("1. Add a table", "   2. Pick the rectangular card", "- Editor with inspector open",
                       "`/taller`", "`src/app/taller/page.tsx`", "Keep toolbar", "- Top navigation",
                       "Use the existing Spanish labels", "Only this criterion", f"repo web: `{self.rdir}`"):
            self.assertIn(needle, text)
        self.assertNotIn(PRODUCT + "\n", text.split("## Flujos")[0])
        self.assertNotIn("No las adivines", text)

    def test_repos_without_planner_surface_ask_to_locate_without_guessing(self):
        text = ui_brief.build(self.rdir, self.row(), {"web": self.rdir})
        self.assertIn("No las adivines", text)
        self.assertIn(f"repo web: `{self.rdir}`", text)

    def test_ui_brief_change_makes_the_draft_stale(self):
        before = self.row()["digest"]
        plan = json.loads(json.dumps(PLAN))
        plan["subplans"][1]["ui_brief"] = PLANNER
        self.write(plan)
        self.assertNotEqual(self.row()["digest"], before)
        self.assertEqual(self.row()["ui_brief"], PLANNER)

    def test_behavior_file_is_the_ui_brief_not_a_row_dump(self):
        (self.rdir / "design").mkdir()
        path = directions.write_behavior(self.rdir, "tables@v1", 1, self.row())
        text = path.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# Brief de interfaz — SP-2 · Tables"))
        self.assertNotIn('"digest"', text)
        self.assertNotIn('"expected_paths"', text)

    def test_siblings_list_other_subplans_finalised_contracts(self):
        (self.rdir / "design").mkdir()
        (self.rdir / "design" / "tables@v1.md").write_text("own", encoding="utf-8")
        plan = json.loads(json.dumps(PLAN))
        plan["subplans"][0]["ui"] = {"contract": "orders", "version": 2, "design_task": "T1", "visual_review_task": "T1"}
        self.write(plan)
        (self.rdir / "design" / "orders@v2.md").write_text("sibling", encoding="utf-8")
        self.assertEqual([p.name for p in ui_brief.siblings(self.rdir, "tables@v1")], ["orders@v2.md"])


class BriefWording(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.rdir = Path(self.tmp.name)
        (self.rdir / "PLAN.json").write_text(json.dumps(PLAN), encoding="utf-8")
        (self.rdir / "SPEC.md").write_text(SPEC, encoding="utf-8")
        (self.rdir / "PLAN.md").write_text("---\nstatus: review\n---\n# Plan", encoding="utf-8")
        self.orders = []

        def create(*args, **kwargs):
            self.orders.append({"id": f"D-{len(self.orders) + 1}", "task": args[1]})
            return self.orders[-1]
        for p in (patch.object(bt_delegate, "create", side_effect=create),
                  patch.object(bt_delegate, "start_background", return_value=1),
                  patch.object(bt_delegate, "summary", return_value={"status": "running_or_pending"}),
                  patch.object(ui_brief, "cloned_repos", return_value={})):
            p.start()
            self.addCleanup(p.stop)

    def assertWording(self, brief):
        for needle in ("CHANGE to an existing product surface, never a new page or landing",
                       "design system is FIXED", "Do not propose a new palette, new font families",
                       "say so in CONCERNS", "No invented content"):
            self.assertIn(needle, brief)
        for needle in ("avoid repeating", "look ledger", "retain the product's shared identity", "memorable move"):
            self.assertNotIn(needle, brief)

    def test_canonical_brief_inlines_the_ui_brief(self):
        row = next(s for s in drafts.subplans(self.rdir) if s["ref"])
        brief = bt_design_brief._brief("demo", self.rdir, row, [])
        self.assertWording(brief)
        self.assertIn("# Brief de interfaz — SP-2", brief)
        self.assertNotIn(HARNESS, brief)

    def test_exploration_and_iteration_briefs_reuse_siblings(self):
        drafts.request("demo", self.rdir)
        self.assertEqual(len(self.orders), 3)
        for order in self.orders:
            self.assertWording(order["task"])
            self.assertIn("Reuse the app shell, navigation structure, tokens and component vocabulary", order["task"])
            self.assertIn("tables@v1.r1.behavior.md", order["task"])
        behavior = self.rdir / "design" / "tables@v1.r1.behavior.md"
        self.assertTrue(behavior.read_text(encoding="utf-8").startswith("# Brief de interfaz"))
        prior = {"id": "a", "revision": 1, "name": "Calm", "seed": directions.SEEDS[0]}
        row = next(s for s in drafts.subplans(self.rdir) if s["ref"])
        brief = iterate._brief("demo", self.rdir, row, [], prior, 2)
        self.assertWording(brief)
        self.assertIn("tables@v1.r2.behavior.md", brief)
        self.assertIn("Reuse the app shell", brief)

    def test_seeds_vary_layout_and_interaction_not_identity(self):
        self.assertEqual(len(directions.SEEDS), 3)
        for seed in directions.SEEDS:
            self.assertIn("shell", seed)
            self.assertNotIn("physical world", seed)


if __name__ == "__main__":
    unittest.main()
