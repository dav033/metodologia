"""A plan change extends an owner-chosen design (amend) instead of regenerating its directions."""
import argparse
import contextlib
import io
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from test_design_drafts import CONTRACT, PLAN

import bt_cli_design
import bt_delegate
import bt_design_amend as amend
import bt_design_brief_diff as brief_diff
import bt_design_directions as directions
import bt_design_drafts as drafts
import bt_design_iterate as iterate
import bt_planning_activity as activity

REF = "checkout@v1"


class Amend(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.rdir = Path(self.tmp.name) / "demo" / "requirements" / "REQ-001-shop"
        self.rdir.mkdir(parents=True)
        self.write_plan(PLAN)
        (self.rdir / "PLAN.md").write_text("---\nstatus: review\n---\n# Plan", encoding="utf-8")
        (self.rdir / "SPEC.md").write_text("# Shop", encoding="utf-8")
        self.orders, self.outcomes = [], {}

        def create(*args, **kwargs):
            order = {"id": f"D-{len(self.orders) + 1}", "task": args[1], "role": kwargs.get("role")}
            self.orders.append(order)
            return order
        for p in (patch.object(bt_delegate, "create", side_effect=create),
                  patch.object(bt_delegate, "start_background", return_value=1),
                  patch.object(bt_delegate, "summary", side_effect=lambda did: self.outcomes.get(
                      did, {"status": "running_or_pending"})),
                  patch.object(directions, "compare", return_value={"ok": True, "pairs": []})):
            p.start()
            self.addCleanup(p.stop)

    def write_plan(self, plan, age=3600):
        target = self.rdir / "PLAN.json"
        target.write_text(json.dumps(plan), encoding="utf-8")
        old = time.time() - age
        os.utime(target, (old, old))

    def direction(self, i, revision=1, did=None, thumbnails=True):
        key = chr(97 + i)
        out = directions.files(self.rdir, REF, revision, key)
        out["html"].write_text(f"<main><h1>Direction {key} r{revision}</h1></main>")
        out["md"].write_text(f"# Direction {key}")
        out["tsx"].write_text(f"// Direction {key} source r{revision}")
        for n in (1, 2) if thumbnails else ():
            Path(f"{out['html']}.candidate-{n}.html").write_text("<main>Candidate</main>")
        out["json"].write_text(json.dumps({"name": f"Direction {key}", "axes": {k: k for k in directions.AXES},
                                           "evidence": {k: ["main"] for k in ("layout", "navigation", "typography",
                                                                               "motion")}}))
        self.outcomes[did or f"D-{i + 1}"] = {"status": "claimed", "summary": "Done"}

    def finalised(self):
        """REQ-021 SP-2 shape: three directions explored, A chosen and finalised into the canonical contract."""
        drafts.request("demo", self.rdir)
        for i in range(3):
            self.direction(i)
        drafts.rows(self.rdir)
        directions.choose("demo", self.rdir, REF, "a", "cli")
        md, html = drafts.paths(self.rdir, REF)
        md.write_text(CONTRACT)
        html.write_text("<main>Chosen A</main>")
        self.outcomes["D-4"] = {"status": "claimed", "summary": "Finalized"}
        row = drafts.rows(self.rdir)[0]
        self.assertEqual((row["status"], row["chosen"], row["stale"]), ("ready", "a", False))
        return row

    def change_plan(self, age=3600):
        plan = json.loads(json.dumps(PLAN))
        plan["subplans"][1]["outcome"] = "The buyer pays in two steps."
        plan["tasks"][2]["title"] = "Build two-step checkout"
        plan["tasks"].append({"id": "T5", "title": "Review two-step checkout", "subplan_id": "SP-2",
                              "kind": "implement", "ui": True})
        self.write_plan(plan, age)

    def finish_amend(self, did, n=1):
        out = amend.files(self.rdir, REF, n)
        out["md"].write_text(CONTRACT.replace("Checkout contract", "Two-step checkout contract"))
        out["html"].write_text("<main>Chosen A, two steps</main>")
        out["tsx"].write_text("// two steps")
        self.outcomes[did] = {"status": "claimed", "summary": "Amended"}

    def test_plan_change_on_a_finalised_choice_amends_it_and_settles_ready_with_the_new_digest(self):
        self.finalised()
        self.change_plan()
        row = drafts.rows(self.rdir)[0]
        self.assertEqual((row["stale"], row["amend"]), (True, "contract"))
        self.assertTrue(any("Actualizar diseño" in p for p in drafts.readiness(self.rdir)))
        self.assertEqual(drafts.request("demo", self.rdir), [REF])
        self.assertEqual(len(self.orders), 5)  # one amendment, not three new directions
        brief = self.orders[4]["task"]
        for needle in ("AMENDMENT OF THE CHOSEN, FINALISED DESIGN", "PLAN CHANGE", f"{REF}.r1.behavior.md",
                       f"{REF}.amend-1.behavior.md", f"{REF}.amend-1.md", f"{REF}.r1.dir-a.tsx", "contrast.py",
                       "audit_mockup.py", "status `draft`", "do not redesign", "- The buyer pays.",
                       "+ The buyer pays in two steps.", "~ - T3 — Build checkout  →  - T3 — Build two-step checkout",
                       "+ - T5 — Review two-step checkout"):
            self.assertIn(needle, brief)
        self.assertNotIn("dir-b", brief)
        row = drafts.rows(self.rdir)[0]
        self.assertEqual((row["status"], row["chosen"]), ("amending", "a"))
        self.assertIn("el Designer sigue trabajando", " ".join(drafts.readiness(self.rdir)))
        self.finish_amend("D-5")
        row = drafts.rows(self.rdir)[0]
        self.assertEqual((row["status"], row["chosen"], row["stale"], row["amend"]), ("ready", "a", False, None))
        self.assertEqual(row["revision"], 2)
        md, html = drafts.paths(self.rdir, REF)
        self.assertIn("Two-step", md.read_text())
        self.assertEqual(html.read_text(), "<main>Chosen A, two steps</main>")
        self.assertIn("Chosen A", (self.rdir / "design/history" / REF / "r1.html").read_text())
        self.assertIn("Two-step", (self.rdir / "design/history" / REF / "r2.md").read_text())
        entry = drafts._load(self.rdir)["drafts"][REF]
        self.assertEqual(entry["ui_digest"], drafts.subplans(self.rdir)[1]["ui_digest"])
        self.assertEqual(entry["digest"], drafts.subplans(self.rdir)[1]["digest"])
        self.assertEqual(entry["behavior"], f"{REF}.amend-1.behavior.md")
        self.assertEqual(entry["history"][-1]["reason"], "plan changed")
        self.assertNotIn("amend", entry)
        self.assertEqual(drafts.readiness(self.rdir), [])
        self.assertTrue(any("contrato actualizado por cambio del plan" in ev.get("text", "")
                            for ev in activity.events(self.rdir)))
        self.assertEqual(drafts.sync("demo", self.rdir), [])
        self.assertEqual(drafts.pin_for_plan(self.rdir), [REF])

    def test_second_amend_starts_from_the_previous_amended_source(self):
        self.finalised()
        self.change_plan()
        amend.start("demo", self.rdir, REF, "", "cli")
        self.finish_amend("D-5")
        drafts.rows(self.rdir)
        plan = json.loads((self.rdir / "PLAN.json").read_text())
        plan["subplans"][1]["acceptance_criteria"] = ["Pay works.", "Six system roles are listed."]
        self.write_plan(plan)
        self.assertEqual(drafts.rows(self.rdir)[0]["amend"], "contract")
        amend.start("demo", self.rdir, REF, "Keep the role badges", "web")
        brief = self.orders[5]["task"]
        self.assertIn(f"{REF}.amend-1.tsx", brief)
        self.assertIn(f"{REF}.amend-1.behavior.md", brief)
        self.assertIn("+ - Six system roles are listed.", brief)
        self.assertIn("Keep the role badges", brief)

    def test_irrelevant_plan_change_does_not_make_the_design_stale(self):
        self.finalised()
        plan = json.loads(json.dumps(PLAN))
        plan["tasks"][1]["estimated_minutes"] = 90
        plan["tasks"].append({"id": "T6", "title": "Migrate the orders table", "subplan_id": "SP-2",
                              "kind": "implement", "ui": False, "acceptance_criteria": ["Migration runs."]})
        before = drafts.subplans(self.rdir)[1]
        self.write_plan(plan)
        after = drafts.subplans(self.rdir)[1]
        self.assertNotEqual(before["digest"], after["digest"])
        self.assertEqual(before["ui_digest"], after["ui_digest"])
        row = drafts.rows(self.rdir)[0]
        self.assertEqual((row["stale"], row["amend"]), (False, None))
        self.assertEqual(drafts.sync("demo", self.rdir), [])
        self.assertEqual(len(self.orders), 4)

    def test_failed_amend_keeps_the_files_and_the_choice_and_can_be_retried(self):
        self.finalised()
        self.change_plan()
        self.assertIn("Actualizando", amend.start("demo", self.rdir, REF, "", "cli"))
        md, html = drafts.paths(self.rdir, REF)
        md.write_text("half-written")  # the session broke the canonical contract and wrote no amendment
        self.outcomes["D-5"] = {"status": "claimed", "summary": "Done"}
        row = drafts.rows(self.rdir)[0]
        self.assertEqual((row["status"], row["chosen"], row["amend"]), ("failed", "a", "contract"))
        self.assertIn("falló", row["error"])
        self.assertEqual(md.read_text(), CONTRACT)
        self.assertEqual(html.read_text(), "<main>Chosen A</main>")
        self.assertTrue(drafts.readiness(self.rdir))
        self.assertIn("amend-2", amend.start("demo", self.rdir, REF, "", "cli") + self.orders[5]["task"])
        self.assertIn(f"{REF}.amend-2.md", self.orders[5]["task"])

    def test_launch_failure_keeps_the_choice(self):
        self.finalised()
        self.change_plan()
        with patch.object(bt_delegate, "create", side_effect=SystemExit("no account")), \
                self.assertRaisesRegex(SystemExit, "No se pudo actualizar"):
            amend.start("demo", self.rdir, REF, "", "cli")
        row = drafts.rows(self.rdir)[0]
        self.assertEqual((row["status"], row["chosen"], row["amend"]), ("failed", "a", "contract"))

    def test_amend_refuses_while_its_own_designer_works_or_without_chosen_work(self):
        self.finalised()
        self.change_plan()
        with drafts._locked(self.rdir) as data:
            entry = data["drafts"][REF]
            saved = {k: entry.get(k) for k in ("status", "delegation")}
            entry.update(status="drafting", delegation="D-busy")
        with self.assertRaisesRegex(SystemExit, f"ya está trabajando en {REF}"):
            amend.start("demo", self.rdir, REF, "", "cli")
        self.assertEqual(len(self.orders), 4)
        with drafts._locked(self.rdir) as data:
            data["drafts"][REF].update(saved)
            data["drafts"][REF]["chosen"] = None
        with self.assertRaisesRegex(SystemExit, "no tiene un diseño elegido"):
            amend.start("demo", self.rdir, REF, "", "cli")

    def test_current_design_is_not_amended(self):
        self.finalised()
        with self.assertRaisesRegex(SystemExit, "al día"):
            amend.start("demo", self.rdir, REF, "", "cli")

    def test_sync_respects_the_pause_then_amends_automatically(self):
        self.finalised()
        self.change_plan()
        pause = self.rdir / ".planning" / "designers.paused"
        pause.parent.mkdir(exist_ok=True)
        pause.write_text("")
        self.assertEqual(drafts.sync("demo", self.rdir), [])
        self.assertEqual(len(self.orders), 4)
        pause.unlink()
        self.assertEqual(drafts.sync("demo", self.rdir), [REF])
        self.assertEqual(len(self.orders), 5)
        self.assertIn("AMENDMENT OF THE CHOSEN", self.orders[4]["task"])
        entry = drafts._load(self.rdir)["drafts"][REF]
        self.assertEqual((entry["status"], entry["reason"], entry["auto_runs"]), ("amending", "plan changed", 1))

    def test_fresh_request_still_regenerates_directions_over_a_choice(self):
        self.finalised()
        self.change_plan()
        self.assertEqual(drafts.request("demo", self.rdir, [REF], fresh=True), [REF])
        self.assertEqual(len(self.orders), 7)
        self.assertTrue(all("FRESH START" in o["task"] for o in self.orders[4:]))
        self.assertEqual(drafts._load(self.rdir)["drafts"][REF]["direction_history"][-1]["chosen"], "a")

    def test_iteration_of_the_chosen_direction_is_amended_through_iterate(self):
        self.finalised()
        iterate.iterate("demo", self.rdir, REF, "a", "Rounder", "cli")
        self.direction(0, revision=2, did="D-5", thumbnails=False)
        row = drafts.rows(self.rdir)[0]
        self.assertEqual((row["status"], row["chosen"]), ("choosing", None))
        self.change_plan()
        row = drafts.rows(self.rdir)[0]
        self.assertEqual((row["stale"], row["amend"]), (True, "direction"))
        with self.assertRaisesRegex(SystemExit, "actualiza el diseño"):
            iterate.iterate("demo", self.rdir, REF, "a", "Rounder again", "cli")
        self.assertEqual(drafts.request("demo", self.rdir), [REF])
        self.assertEqual(len(self.orders), 6)
        brief = self.orders[5]["task"]
        for needle in ("ITERATION OF ONE DIRECTION", "PLAN CHANGE", f"{REF}.r2.dir-a.tsx", f"{REF}.r3.dir-a.html",
                       f"{REF}.r2.behavior.md", "+ The buyer pays in two steps."):
            self.assertIn(needle, brief)
        self.direction(0, revision=3, did="D-6", thumbnails=False)
        row = drafts.rows(self.rdir)[0]
        self.assertEqual((row["status"], row["stale"], row["amend"], row["reason"]),
                         ("choosing", False, None, "plan changed"))
        self.assertEqual(amend.last_chosen(drafts._load(self.rdir)["drafts"][REF]), "a")

    def test_cli_amend_prints_the_status_line_and_ignores_the_pause(self):
        self.finalised()
        self.change_plan()
        (self.rdir / ".planning").mkdir(exist_ok=True)
        (self.rdir / ".planning" / "designers.paused").write_text("")
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers(dest="cmd")
        bt_cli_design.register(sub)
        args = parser.parse_args(["design", "amend", "REQ-001", REF, "--comments", "Keep the badges"])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = bt_cli_design.dispatch(args, Path(self.tmp.name), "demo")
        self.assertEqual(code, 0)
        self.assertIn(f"Actualizando {REF}", out.getvalue())
        self.assertIn("Keep the badges", self.orders[4]["task"])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(bt_cli_design.dispatch(args, Path(self.tmp.name), "demo"), 1)
        self.assertIn(f"ya está trabajando en {REF}", out.getvalue())

    def test_plan_tab_banner_offers_the_update_with_the_diff_while_other_subplans_are_designed(self):
        import bt_page_design_amend as page
        import bt_page_planning
        self.finalised()
        self.change_plan()
        opts = bt_page_planning.options(self.rdir, {"lang": "en", "sp": "SP-2"})
        html = bt_page_planning.fragment("demo", "REQ-001", self.rdir, "review", "tok", opts)
        for needle in ("El plan cambió: actualizar el diseño con lo que ya está", "/design-amend",
                       ">Actualizar diseño</button>", "Qué cambió en el plan", "Build two-step checkout"):
            self.assertIn(needle, html)
        self.assertNotIn("se rehará", html)
        row = drafts.rows(self.rdir)[0]
        ctx = {"project": "demo", "rid": "REQ-001", "token": "t", "rdir": self.rdir, "opts": opts,
               "rows": {REF: row, "other@v1": {"status": "drafting"}}}
        self.assertNotIn("disabled", page.banner(ctx, row))  # another subplan's Designer never blocks this one
        self.assertEqual(page.banner(ctx, {**row, "status": "amending"}), "")
        self.assertEqual(page.banner(ctx, {**row, "amend": None}), "")


class BriefDiff(unittest.TestCase):
    def test_keyed_lines_pair_as_changes_and_bookkeeping_is_ignored(self):
        before = ("# Brief\n\n## Requisitos que cubre\n\n- R1: Plan 1 accounts\n- R2: Export\n\n## Superficie existente"
                  " a modificar\n\n- repo web: `/a`\n\n## Omitido a propósito\n\nTareas omitidas: T1.\n")
        after = ("# Brief\n\n## Requisitos que cubre\n\n- R1: Entusiasta accounts\n- R3: Six roles\n\n## Superficie "
                 "existente a modificar\n\n- repo web: `/b`\n\n## Omitido a propósito\n\nTareas omitidas: T1, T9.\n")
        changes = brief_diff.diff(before, after)
        self.assertEqual([(c["kind"], c["before"], c["after"]) for c in changes],
                         [("changed", "- R1: Plan 1 accounts", "- R1: Entusiasta accounts"),
                          ("removed", "- R2: Export", ""), ("added", "", "- R3: Six roles")])
        self.assertIn("[Requisitos que cubre]", brief_diff.render(changes))
        self.assertIn("no UI-relevant difference", brief_diff.render([]))


if __name__ == "__main__":
    unittest.main()
