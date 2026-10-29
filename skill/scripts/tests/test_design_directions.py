"""Owner choice, independent failures, fresh revisions and rendered distinctness boundaries."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_design_drafts import CONTRACT, PLAN

import bt_delegate
import bt_design_directions as directions
import bt_design_drafts as drafts
import bt_design_iterate as iterate


class Directions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.rdir = Path(self.tmp.name)
        (self.rdir / "PLAN.json").write_text(json.dumps(PLAN))
        (self.rdir / "PLAN.md").write_text("---\nstatus: review\n---\n# Plan")
        (self.rdir / "SPEC.md").write_text("# Shop")
        self.orders, self.outcomes = [], {}
        def create(*args, **kwargs):
            order = {"id": f"D-{len(self.orders)+1}", "task": args[1], "role": kwargs.get("role")}
            self.orders.append(order)
            return order
        for p in (patch.object(bt_delegate, "create", side_effect=create),
                  patch.object(bt_delegate, "start_background", return_value=1),
                  patch.object(bt_delegate, "summary", side_effect=lambda did: self.outcomes.get(did, {"status": "running_or_pending"})),
                  patch.object(directions, "compare", return_value={"ok": True, "pairs": []})):
            p.start()
            self.addCleanup(p.stop)

    def finish(self, i, revision=1, key=None, did=None, thumbnails=True):
        key = key or chr(97 + i)
        out = directions.files(self.rdir, "checkout@v1", revision, key)
        out["html"].write_text(f'<main><h1>Direction {key}</h1></main>')
        out["md"].write_text(f"# Direction {key}")
        out["tsx"].write_text(f"// Direction {key} source")
        for n in (1, 2) if thumbnails else ():
            Path(f"{out['html']}.candidate-{n}.html").write_text(f"<main>Candidate {n}</main>")
        out["json"].write_text(json.dumps({"name": f"Direction {key}", "axes": {k: f"{key} {k}" for k in directions.AXES},
            "evidence": {k: ["main"] for k in ("layout", "navigation", "typography", "motion")}}))
        self.outcomes[did or f"D-{i+1}"] = {"status": "claimed", "summary": "Done"}

    def explored(self):
        drafts.request("demo", self.rdir)
        for i in range(3):
            self.finish(i)
        self.assertEqual(drafts.rows(self.rdir)[0]["status"], "choosing")

    def test_default_starts_three_independent_designers_and_blocks_approval(self):
        self.assertEqual(drafts.request("demo", self.rdir, fresh=True), ["checkout@v1"])
        self.assertEqual(len(self.orders), 3)
        self.assertEqual({o["role"] for o in self.orders}, {"designer"})
        for i, order in enumerate(self.orders):
            self.assertIn(f"dir-{chr(97+i)}.html", order["task"])
            self.assertIn("FRESH START", order["task"])
        self.assertTrue(any("elige una dirección" in p for p in drafts.readiness(self.rdir)))

    def test_failed_sibling_does_not_lose_other_directions(self):
        drafts.request("demo", self.rdir)
        self.finish(0)
        self.finish(1)
        self.outcomes["D-3"] = {"status": "failed", "summary": "process died"}
        row = drafts.rows(self.rdir)[0]
        self.assertEqual(row["status"], "choosing")
        self.assertEqual([d["status"] for d in row["directions"]], ["ready", "ready", "failed"])
        self.assertEqual(drafts.sync("demo", self.rdir), [])
        self.assertIn("elegida", directions.choose("demo", self.rdir, "checkout@v1", "a", "cli"))
        self.assertEqual(len(self.orders), 4)
        md, html = drafts.paths(self.rdir, "checkout@v1")
        md.write_text(CONTRACT)
        html.write_text("<main>Chosen A</main>")
        self.outcomes["D-4"] = {"status": "claimed", "summary": "Finalized"}
        row = drafts.rows(self.rdir)[0]
        self.assertEqual((row["status"], row["chosen"]), ("ready", "a"))
        self.assertEqual(drafts.readiness(self.rdir), [])
        self.assertTrue(directions.preview(self.rdir, "checkout@v1", "b").is_file())

    def test_gate_failure_or_modified_mockup_cannot_be_chosen(self):
        drafts.request("demo", self.rdir)
        for i in range(3):
            self.finish(i)
        drafts.rows(self.rdir)
        out = directions.files(self.rdir, "checkout@v1", 1, "a")
        out["html"].write_text("Changed after comparison")
        with self.assertRaisesRegex(SystemExit, "cambió"):
            directions.choose("demo", self.rdir, "checkout@v1", "a", "cli")
        with drafts._locked(self.rdir) as data:
            data["drafts"]["checkout@v1"]["comparison"] = {"ok": False}
        with self.assertRaisesRegex(SystemExit, "comparación"):
            directions.choose("demo", self.rdir, "checkout@v1", "a", "cli")

    def test_one_direction_with_unseen_traits_does_not_hide_the_sound_ones(self):
        def evidence(ok):
            return {"motion": [{"selector": ".rail-mark", "ok": ok}], "layout": [{"selector": ".paper", "ok": True}]}

        report = {"evidence_ok": False, "pairs": [{"a": "x", "b": "y", "ok": True}],
                  "directions": [{"id": "S@v1.r3.dir-a.html", "evidence": evidence(True)},
                                 {"id": "S@v1.r3.dir-b.html", "evidence": evidence(False)},
                                 {"id": "S@v1.r3.dir-c.html", "evidence": evidence(True)}]}
        entry = {"comparison": {"ok": False, "error": "Alguna dirección declara rasgos que no se ven", "report": report}}
        pick = lambda key: directions.choosable("S@v1", entry, {"id": key, "revision": 3})  # noqa: E731
        self.assertEqual([pick("a"), pick("b"), pick("c")], [True, False, True])
        report["pairs"][0]["ok"] = False                      # directions too alike: the comparison itself failed
        self.assertFalse(pick("a"))
        report["pairs"][0]["ok"] = True
        entry["comparison"]["report"] = {"error": "playwright missing"}                # a tool failure proves nothing
        self.assertFalse(pick("a"))
        entry["comparison"] = {"ok": True}
        self.assertTrue(pick("b"))

    def test_fresh_preserves_completed_exploration_and_increments_attempt(self):
        drafts.request("demo", self.rdir)
        for i in range(3):
            self.finish(i)
        drafts.rows(self.rdir)
        old = directions.files(self.rdir, "checkout@v1", 1, "a")["html"]
        blob = old.read_bytes()
        drafts.request("demo", self.rdir, fresh=True)
        self.assertEqual(old.read_bytes(), blob)
        self.assertIn("r2.dir-a.html", self.orders[3]["task"])
        self.assertIsNone(directions.preview(self.rdir, "../checkout@v1", "a"))
        self.assertIsNone(directions.preview(self.rdir, "checkout@v1", "../a"))

    def test_rebuild_source_cannot_change_after_the_direction_was_compared(self):
        drafts.request("demo", self.rdir)
        for i in range(3):
            self.finish(i)
        drafts.rows(self.rdir)
        directions.files(self.rdir, "checkout@v1", 1, "a")["tsx"].write_text("// Changed composition")
        with self.assertRaisesRegex(SystemExit, "cambió"):
            directions.choose("demo", self.rdir, "checkout@v1", "a", "cli")

    def test_invalid_direction_count_fails_before_spawning(self):
        for n in (0, 4, True):
            with self.assertRaises(SystemExit):
                drafts.request("demo", self.rdir, directions=n)
        self.assertEqual(self.orders, [])

    def test_single_direction_still_requires_a_choice_after_triple_exploration(self):
        drafts.request("demo", self.rdir)
        for i in range(3):
            self.finish(i)
        drafts.rows(self.rdir)
        drafts.request("demo", self.rdir, fresh=True, directions=1)
        self.assertEqual(len(self.orders), 4)
        row = drafts.rows(self.rdir)[0]
        self.assertEqual(len(row["directions"]), 1)
        self.assertEqual(row["attempt"], 2)
        self.assertIsNone(row["chosen"])
        self.assertIn("r2.dir-a.html", self.orders[3]["task"])
        self.assertTrue(any("elige una dirección" in p for p in drafts.readiness(self.rdir)))

    def test_abandoned_queued_directions_expire_and_allow_fresh_retry(self):
        with drafts._locked(self.rdir) as data:
            data["drafts"]["checkout@v1"] = {"status": "drafting", "phase": "explore", "attempt": 1,
                "started": "2020-01-01T00:00:00+00:00", "directions": [{"id": "a", "status": "queued", "revision": 1}]}
        self.assertEqual(drafts.rows(self.rdir)[0]["status"], "failed")
        self.assertEqual(drafts.request("demo", self.rdir, fresh=True), ["checkout@v1"])

    def test_failed_explorations_stop_at_the_automatic_retry_limit(self):
        drafts.add_feedback("demo", self.rdir, "checkout@v1", "New composition", "web")
        for attempt in range(drafts.MAX_FAILURES):
            for order in self.orders:
                self.outcomes[order["id"]] = {"status": "failed", "summary": "process died"}
            self.assertEqual(drafts.rows(self.rdir)[0]["status"], "failed")
            with drafts._locked(self.rdir) as data:
                data["drafts"]["checkout@v1"]["finished"] = "2020-01-01T00:00:00+00:00"
            drafts.sync("demo", self.rdir)
        self.assertEqual(len(self.orders), 3 * drafts.MAX_FAILURES)
        self.assertEqual(drafts.sync("demo", self.rdir), [])

    def test_feedback_used_by_exploration_does_not_redo_it_while_choosing(self):
        drafts.add_feedback("demo", self.rdir, "checkout@v1", "Different motion", "web")
        for i in range(3):
            self.finish(i)
        drafts.rows(self.rdir)
        self.assertEqual(drafts.sync("demo", self.rdir), [])
        self.assertEqual(len(self.orders), 3)

    def test_plan_change_invalidates_an_unselected_exploration(self):
        drafts.request("demo", self.rdir)
        for i in range(3):
            self.finish(i)
        drafts.rows(self.rdir)
        plan = json.loads((self.rdir / "PLAN.json").read_text())
        plan["subplans"][1]["outcome"] = "Changed behaviour"
        (self.rdir / "PLAN.json").write_text(json.dumps(plan))
        self.assertTrue(drafts.rows(self.rdir)[0]["stale"])
        with self.assertRaisesRegex(SystemExit, "subplan cambió"):
            directions.choose("demo", self.rdir, "checkout@v1", "a", "cli")
        self.assertEqual(drafts.request("demo", self.rdir), ["checkout@v1"])
        self.assertIn("r2.dir-a.html", self.orders[3]["task"])


    def test_iterate_revises_only_the_picked_direction_into_a_new_revision(self):
        self.explored()
        old = {ext: f.read_bytes() for ext, f in directions.files(self.rdir, "checkout@v1", 1, "b").items()}
        msg = iterate.iterate("demo", self.rdir, "checkout@v1", "b", "Rounder, more modern", "cli")
        self.assertIn("revisión 2", msg)
        self.assertEqual(len(self.orders), 4)
        brief = self.orders[3]["task"]
        for needle in ("ITERATION OF ONE DIRECTION", "r1.dir-b.tsx", "r1.dir-b.json", "r2.dir-b.html", "audit_mockup.py",
                       "contrast.py", "Rounder, more modern"):
            self.assertIn(needle, brief)
        row = drafts.rows(self.rdir)[0]
        self.assertEqual((row["status"], row["attempt"]), ("drafting", 2))
        self.assertEqual([(d["id"], d["revision"], d["name"]) for d in row["directions"]], [("b", 2, "Direction b")])
        self.assertEqual([d["id"] for d in row["direction_history"][-1]["directions"]], ["a", "b", "c"])
        self.finish(1, revision=2, did="D-4", thumbnails=False)
        row = drafts.rows(self.rdir)[0]
        self.assertEqual((row["status"], len(row["directions"]), row["directions"][0]["status"]), ("choosing", 1, "ready"))
        self.assertTrue(all(f.get("consumed") == "D-4" for f in row["feedback"]))
        self.assertEqual({ext: f.read_bytes() for ext, f in directions.files(self.rdir, "checkout@v1", 1, "b").items()}, old)
        self.assertEqual(drafts.sync("demo", self.rdir), [])
        self.assertIn("elegida", directions.choose("demo", self.rdir, "checkout@v1", "b", "cli"))
        self.assertIn("r2.dir-b.md", self.orders[4]["task"])

    def test_iterate_refuses_while_another_batch_is_active(self):
        drafts.request("demo", self.rdir)
        with self.assertRaisesRegex(SystemExit, "ya está trabajando en checkout@v1"):
            iterate.iterate("demo", self.rdir, "checkout@v1", "a", "Rounder", "cli")
        self.assertEqual(len(self.orders), 3)

    def test_feedback_on_a_direction_iterates_and_untargeted_feedback_regenerates(self):
        self.explored()
        self.assertIn("Iterando la dirección A", drafts.add_feedback("demo", self.rdir, "checkout@v1", "Rounder", "web",
                                                                      direction="a"))
        self.assertEqual(len(self.orders), 4)
        self.assertIn("ITERATION OF ONE DIRECTION", self.orders[3]["task"])
        self.finish(0, revision=2, did="D-4", thumbnails=False)
        self.assertEqual(drafts.rows(self.rdir)[0]["status"], "choosing")
        self.assertIn("rediseñando", drafts.add_feedback("demo", self.rdir, "checkout@v1", "Start over", "web"))
        self.assertEqual(len(self.orders), 7)
        self.assertTrue(all("FRESH START" in o["task"] for o in self.orders[4:]))

    def test_direction_feedback_saved_while_busy_is_iterated_by_sync(self):
        drafts.request("demo", self.rdir)
        self.assertIn("guardado", drafts.add_feedback("demo", self.rdir, "checkout@v1", "Rounder", "web", direction="c"))
        for i in range(3):
            self.finish(i)
        self.assertEqual(drafts.sync("demo", self.rdir), ["checkout@v1"])
        self.assertEqual(len(self.orders), 4)
        self.assertIn("r2.dir-c.html", self.orders[3]["task"])

    def test_failed_iteration_is_reported_and_can_be_retried_from_the_same_source(self):
        self.explored()
        iterate.iterate("demo", self.rdir, "checkout@v1", "a", "Rounder", "cli")
        self.outcomes["D-4"] = {"status": "claimed", "summary": "Done"}  # but no files written
        row = drafts.rows(self.rdir)[0]
        self.assertEqual(row["status"], "failed")
        self.assertIn("iteración de la dirección A", row["error"])
        self.assertEqual(row["pending_feedback"], 1)
        with drafts._locked(self.rdir) as data:
            self.assertEqual(iterate.route(data["drafts"]["checkout@v1"]), "a")
        iterate.iterate("demo", self.rdir, "checkout@v1", "a", "", "cli")
        self.assertIn("r1.dir-a.tsx", self.orders[4]["task"])
        self.assertIn("r3.dir-a.html", self.orders[4]["task"])

    def test_iteration_fails_when_the_source_revision_was_modified(self):
        self.explored()
        iterate.iterate("demo", self.rdir, "checkout@v1", "a", "Rounder", "cli")
        directions.files(self.rdir, "checkout@v1", 1, "a")["html"].write_text("patched in place")
        self.finish(0, revision=2, did="D-4", thumbnails=False)
        self.assertIn("inmutables", drafts.rows(self.rdir)[0]["error"])

    def test_finalised_choice_can_be_iterated_but_not_an_unchosen_direction(self):
        self.explored()
        directions.choose("demo", self.rdir, "checkout@v1", "a", "cli")
        md, html = drafts.paths(self.rdir, "checkout@v1")
        md.write_text(CONTRACT)
        html.write_text("<main>Chosen A</main>")
        self.outcomes["D-4"] = {"status": "claimed", "summary": "Finalized"}
        self.assertEqual(drafts.rows(self.rdir)[0]["status"], "ready")
        with self.assertRaisesRegex(SystemExit, "no está lista"):
            iterate.iterate("demo", self.rdir, "checkout@v1", "b", "Rounder", "cli")
        iterate.iterate("demo", self.rdir, "checkout@v1", "a", "Rounder", "cli")
        self.assertIn("r2.dir-a.html", self.orders[4]["task"])
        self.assertTrue(any("Designer sigue trabajando" in p for p in drafts.readiness(self.rdir)))

    def test_selected_direction_iteration_continues_without_reselecting(self):
        self.explored()
        directions.choose("demo", self.rdir, "checkout@v1", "a", "cli")
        md, html = drafts.paths(self.rdir, "checkout@v1")
        md.write_text(CONTRACT)
        html.write_text("<main>Chosen A</main>")
        self.outcomes["D-4"] = {"status": "claimed", "summary": "Finalized"}
        self.assertEqual(drafts.rows(self.rdir)[0]["status"], "ready")
        iterate.iterate("demo", self.rdir, "checkout@v1", "a", "Rounder", "web")
        self.finish(0, revision=2, did="D-5", thumbnails=False)
        self.assertEqual(drafts.rows(self.rdir)[0]["status"], "choosing")
        with patch.object(drafts, "DEBOUNCE_SEC", 0):
            drafts.sync("demo", self.rdir)
        row = drafts.rows(self.rdir)[0]
        self.assertEqual((row["chosen"], row["phase"], row["status"]), ("a", "finalise", "drafting"))
        self.assertIn("r2.dir-a.html", self.orders[-1]["task"])

    def test_new_exploration_does_not_inherit_an_old_choice(self):
        self.explored()
        with drafts._locked(self.rdir) as data:
            data["drafts"]["checkout@v1"].update(status="failed", continuation_choice="a")
        directions.start("demo", self.rdir, "checkout@v1", "requested", True, 3)
        self.assertIsNone(drafts.rows(self.rdir)[0].get("continuation_choice"))

    def test_designer_question_answer_goes_to_planner_without_design_feedback(self):
        from types import SimpleNamespace

        import bt_planning_notes
        import bt_server
        question = "Which legal contact applies?"
        self.explored()
        with drafts._locked(self.rdir) as data:
            data["drafts"]["checkout@v1"]["questions"] = [question]
        handler = SimpleNamespace(tell_planner=unittest.mock.Mock())
        form = {"contract": "checkout@v1", "anchor": "SP-2", "question": question,
                "comments": "Sempertex; contact pending", "lang": "es"}
        with patch.object(bt_server, "commit"), patch.object(drafts, "add_feedback") as feedback:
            bt_server.Handler.planning_post(handler, "demo", self.rdir, "design-answer", form, "/p/demo/req/REQ-001")
            bt_server.Handler.planning_post(handler, "demo", self.rdir, "design-answer", form, "/p/demo/req/REQ-001")
            feedback.assert_not_called()
        self.assertIn("Sempertex; contact pending", bt_planning_notes.notes(self.rdir)[-1]["text"])
        self.assertEqual(len(bt_planning_notes.notes(self.rdir)), 1)
        handler.tell_planner.assert_called_once()
        self.assertEqual(drafts.rows(self.rdir)[0]["status"], "choosing")

    def test_panel_offers_iteration_and_disables_it_while_drafting(self):
        import bt_page_design_directions as page
        ctx = {"project": "demo", "rid": "REQ-001", "token": "t"}
        d = {"id": "a", "status": "ready", "revision": 1, "name": "Calm"}
        row = {"ref": "checkout@v1", "id": "SP-2", "status": "choosing", "directions": [d], "comparison": {"ok": True}}
        html = page.panel(ctx, row)
        self.assertIn("design-iterate", html)
        self.assertIn("Iterar esta dirección", html)
        self.assertIn("Evidencia de la dirección: comprobada", html)
        self.assertNotIn("disabled", html)
        busy = page.panel(ctx, {**row, "status": "drafting", "directions": [{**d, "status": "drafting"}]})
        self.assertIn("disabled", busy)

    def test_chosen_direction_hides_comparison_and_feedback_alternatives(self):
        import bt_page_design_directions as page
        from bt_page_planning_views import _composer
        ctx = {"project": "demo", "rid": "REQ-001", "token": "t", "opts": {"lang": "es"}}
        ds = [{"id": k, "status": "ready", "revision": 1, "name": f"Option {k}"} for k in "abc"]
        for status in ("drafting", "ready", "approved", "failed"):
            row = {"ref": "checkout@v1", "id": "SP-2", "status": status, "chosen": "c",
                   "directions": ds, "comparison": {"ok": True},
                   "direction_history": [{"revision": 1, "directions": ds}]}
            with self.subTest(status=status):
                self.assertEqual(page.panel(ctx, row), "")
                composer = _composer(ctx, row, "Comment")
                self.assertNotIn("Option a", composer)
                self.assertNotIn("Option b", composer)
                self.assertIn('name="direction" value="c"', composer)

    def test_finalising_choice_does_not_show_previous_canonical_mockup(self):
        from bt_page_planning_views import _frame
        _, html = drafts.paths(self.rdir, "checkout@v1")
        html.parent.mkdir(parents=True, exist_ok=True)
        html.write_text("<main>Old canonical design</main>")
        ctx = {"project": "demo", "rid": "REQ-001", "rdir": self.rdir}
        row = {"ref": "checkout@v1", "chosen": "c", "phase": "finalise", "status": "drafting"}
        self.assertNotIn("<iframe", _frame(ctx, row))
        self.assertIn("<iframe", _frame(ctx, {**row, "status": "ready"}))

    def test_pending_iteration_shows_only_its_preview_until_chosen(self):
        from bt_page_planning_views import design_panel
        md, html = drafts.paths(self.rdir, "checkout@v1")
        html.parent.mkdir(parents=True, exist_ok=True)
        html.write_text("<main>Previous canonical design</main>")
        md.write_text(CONTRACT)
        opts = {"lang": "es", "mode": "subplans", "view": "design", "sp": "SP-2", "rev": 0, "only": False}
        ctx = {"project": "demo", "rid": "REQ-001", "token": "t", "rdir": self.rdir, "opts": opts}
        d = {"id": "a", "status": "ready", "revision": 2, "name": "New iteration"}
        row = {"ref": "checkout@v1", "id": "SP-2", "status": "choosing", "chosen": None,
               "directions": [d], "comparison": {"ok": True}, "stale": False,
               "direction_history": [{"revision": 1, "directions": [d]}], "questions": ["Legal contact?"]}
        preview = design_panel(ctx, {"id": "SP-2"}, row)
        self.assertEqual(preview.count("<iframe"), 1)
        self.assertIn("direction=a", preview)
        self.assertNotIn('class="pp-mock"', preview)
        self.assertIn("Elegir esta dirección", preview)
        self.assertNotIn("Direcciones anteriores", preview)
        self.assertNotIn("Comparar todas", preview)
        self.assertIn('/design-answer', preview)
        self.assertIn('name="question" value="Legal contact?"', preview)
        canonical = design_panel(ctx, {"id": "SP-2"}, {**row, "chosen": "a", "status": "ready"})
        self.assertEqual(canonical.count("<iframe"), 1)
        self.assertNotIn("direction=a", canonical)

class DNA(unittest.TestCase):
    def test_colour_swap_does_not_count_as_a_direction(self):
        spec = importlib.util.spec_from_file_location("compare_directions", drafts.KIT / "compare_directions.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        base = {"id": "a", "shape": ["MAIN:0:0:12:12", "NAV:0:0:3:12"], "fonts": ["Arial"], "sizes": ["16px"],
                "nav": ["left"], "motion": ["linear:200"], "density": 2, "evidence": {"layout": [{"ok": True}]}}
        self.assertFalse(module.compare_dna([base, {**base, "id": "b", "fonts": ["Serif"]}])["ok"])
        different = {**base, "id": "b", "shape": ["MAIN:2:0:10:8", "NAV:0:0:12:1"], "nav": ["top"], "motion": ["spring:400"]}
        self.assertTrue(module.compare_dna([base, different])["ok"])
        different["evidence"] = {"motion": [{"ok": False}]}
        self.assertFalse(module.compare_dna([base, different])["ok"])

    def test_shared_product_typography_does_not_count_against_distinctness(self):
        spec = importlib.util.spec_from_file_location("compare_directions", drafts.KIT / "compare_directions.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        base = {"id": "a", "shape": ["MAIN:0:0:12:12", "NAV:0:0:3:12"], "fonts": ["Inter"], "sizes": ["16px"],
                "nav": ["left"], "motion": ["linear:200"], "density": 100, "evidence": {"layout": [{"ok": True}]}}
        other = {**base, "id": "b", "shape": ["MAIN:2:0:10:8", "NAV:0:0:12:1"], "density": 160}
        pair = module.compare_dna([base, other])["pairs"][0]
        self.assertTrue(pair["same_typography"] and pair["same_navigation"] and pair["same_motion"])
        self.assertTrue(pair["ok"])
        self.assertFalse(module.compare_dna([base, {**other, "density": 95}])["ok"])

    def test_single_direction_passes_on_its_evidence_alone(self):
        spec = importlib.util.spec_from_file_location("compare_directions", drafts.KIT / "compare_directions.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        one = {"id": "a", "shape": ["MAIN:0:0:12:12"], "fonts": ["Arial"], "sizes": ["16px"], "nav": ["left"],
               "motion": ["linear:200"], "density": 2, "evidence": {"layout": [{"ok": True}]}}
        self.assertEqual(module.compare_dna([one])["ok"], True)
        self.assertEqual(module.compare_dna([one])["pairs"], [])
        self.assertFalse(module.compare_dna([{**one, "evidence": {"motion": [{"ok": False}]}}])["ok"])
