from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import bt_delegate
import bt_design_approval as approval
import bt_design_directions as directions
import bt_design_drafts as drafts
import bt_page_planning
import bt_rounds
import bt_translate as tr

PLAN = {"subplans": [
    {"id": "SP-1", "title": "Data layer", "outcome": "Stores orders."},
    {"id": "SP-2", "title": "Checkout screen", "outcome": "The buyer pays.", "acceptance_criteria": ["Pay works."],
     "ui": {"contract": "checkout", "version": 1, "design_task": "T2", "visual_review_task": "T4"}}],
    "tasks": [{"id": "T1", "title": "Store", "subplan_id": "SP-1", "kind": "implement"},
              {"id": "T2", "title": "Design checkout", "subplan_id": "SP-2", "kind": "design"},
              {"id": "T3", "title": "Build checkout", "subplan_id": "SP-2", "kind": "implement", "ui": True}]}


CONTRACT = "# Checkout contract\n" + "".join(f"## {i}. Section\nText {i}.\n" for i in range(1, 13))
REAL_SUMMARY = bt_delegate.summary


class DraftTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.rdir = Path(self.tmp.name) / "demo" / "requirements" / "REQ-001-shop"
        self.rdir.mkdir(parents=True)
        self.write_plan(PLAN)
        (self.rdir / "SPEC.md").write_text("---\nstatus: ready\n---\n# Shop\n\nSell things.\n", encoding="utf-8")
        (self.rdir / "PLAN.md").write_text("---\nstatus: review\n---\n# Plan\n\n## Approach\nBuild it.\n", encoding="utf-8")
        self.orders: list[dict] = []
        self.outcomes: dict[str, dict] = {}
        patches = [patch.object(bt_delegate, "create", side_effect=self.create),
                   # Canonical contract lifecycle, with exploration/owner choice isolated in test_design_directions.
                   patch.object(directions, "start", side_effect=lambda project, rdir, ref, reason, fresh, count:
                                drafts.launch(project, rdir, ref, reason, fresh=fresh)),
                   patch.object(bt_delegate, "start_background", return_value=1),
                   patch.object(bt_delegate, "summary", side_effect=lambda did: self.outcomes.get(
                       did, {"id": did, "status": "running_or_pending"})),
                   patch.object(drafts, "_brief", side_effect=lambda project, rdir, row, feedback, **kwargs:
                                json.dumps([f["text"] for f in feedback]))]
        for item in patches:
            item.start()
            self.addCleanup(item.stop)

    def write_plan(self, plan: dict, age: float = 3600) -> None:
        target = self.rdir / "PLAN.json"
        target.write_text(json.dumps(plan), encoding="utf-8")
        old = time.time() - age
        os.utime(target, (old, old))

    def create(self, project, task, *args, **kwargs):
        order = {"id": f"D-{len(self.orders) + 1}", "agent": "claude", "model": "opus", "task": task,
                 "role": kwargs.get("role")}
        self.orders.append(order)
        return order

    def finish(self, did: str, contract: str = CONTRACT) -> None:
        md, html = drafts.paths(self.rdir, "checkout@v1")
        md.write_text(contract, encoding="utf-8")
        html.write_text("<!doctype html><p>Mockup</p>", encoding="utf-8")
        result = Path(self.tmp.name) / f"{did}.json"
        result.write_text(json.dumps({"notes": "Q: Which payment providers?\nother note"}), encoding="utf-8")
        self.outcomes[did] = {"id": did, "status": "claimed", "summary": "Checkout designed.",
                              "result_file": result.as_posix()}

    def test_request_drafts_only_ui_subplans_with_the_designer_role(self):
        started = drafts.request("demo", self.rdir)
        self.assertEqual(started, ["checkout@v1"])
        self.assertEqual(self.orders[0]["role"], "designer")
        self.assertEqual(drafts.rows(self.rdir)[0]["status"], "drafting")
        self.assertEqual(drafts.request("demo", self.rdir), [])  # already drafting: no second session

    def test_finished_session_becomes_ready_with_questions_and_hash(self):
        drafts.request("demo", self.rdir)
        self.finish("D-1")
        row = drafts.rows(self.rdir)[0]
        self.assertEqual(row["status"], "ready")
        self.assertEqual(row["questions"], ["Which payment providers?"])
        self.assertTrue(row["mockup"])
        self.assertEqual(row["sha256"], hashlib.sha256(CONTRACT.encode()).hexdigest())

    def test_session_without_contract_fails_visibly(self):
        drafts.request("demo", self.rdir)
        self.outcomes["D-1"] = {"id": "D-1", "status": "failed", "summary": "no account"}
        row = drafts.rows(self.rdir)[0]
        self.assertEqual(row["status"], "failed")
        self.assertIn("no account", row["error"])

    def test_dead_claimant_becomes_failed_and_can_be_relaunched(self):
        drafts.request("demo", self.rdir)
        registry = Path(self.tmp.name) / "delegations"
        order = registry / "D-1"
        order.mkdir(parents=True)
        (order / "TASK.json").write_text("{}")
        (order / "CLAIMED").write_text("999999999")
        with patch.object(bt_delegate, "DIR", registry), patch.object(bt_delegate, "summary", REAL_SUMMARY), \
                patch("bt_runutil.pid_alive", return_value=False):
            self.assertEqual(drafts.rows(self.rdir)[0]["status"], "failed")
        self.assertEqual(drafts.request("demo", self.rdir, force=True), ["checkout@v1"])
        self.assertEqual(len(self.orders), 2)

    def test_feedback_waits_for_running_draft_then_sync_redrafts_with_it(self):
        drafts.request("demo", self.rdir)
        message = drafts.add_feedback("demo", self.rdir, "checkout@v1", "Add Apple Pay", "web")
        self.assertIn("al terminar", message)
        self.finish("D-1")
        self.assertEqual(drafts.sync("demo", self.rdir), ["checkout@v1"])
        self.assertEqual(json.loads(self.orders[1]["task"]), ["Add Apple Pay"])
        self.assertEqual(drafts.rows(self.rdir)[0]["pending_feedback"], 0)

    def test_subplan_change_redrafts_only_after_the_conversation_settles(self):
        drafts.request("demo", self.rdir)
        self.finish("D-1")
        changed = json.loads(json.dumps(PLAN))
        changed["subplans"][1]["outcome"] = "The buyer pays in two steps."
        self.write_plan(changed, age=1)
        self.assertTrue(drafts.rows(self.rdir)[0]["stale"])
        self.assertEqual(drafts.sync("demo", self.rdir), [])
        self.assertEqual(drafts.sync("demo", self.rdir, now=time.time() + drafts.DEBOUNCE_SEC + 1), ["checkout@v1"])

    def test_plan_approval_requires_ready_drafts_then_pins_them(self):
        drafts.request("demo", self.rdir)
        self.assertTrue(drafts.readiness(self.rdir))
        self.finish("D-1")
        self.assertEqual(drafts.readiness(self.rdir), [])
        self.assertEqual(drafts.pin_for_plan(self.rdir), ["checkout@v1"])
        record = approval.approvals(self.rdir)["checkout@v1"]
        self.assertEqual((record["status"], record["via"]), ("approved", "plan"))
        self.assertEqual(record["sha256"], hashlib.sha256(CONTRACT.encode()).hexdigest())
        self.assertIn("Planning draft:", drafts.execution_notes(self.rdir, "checkout@v1"))
        self.assertIn("ya fue aprobado", drafts.add_feedback("demo", self.rdir, "checkout@v1", "more", "web"))

    def test_plan_decide_refuses_while_designer_works(self):
        drafts.request("demo", self.rdir)
        with patch("bt_scheduler_adapter.plan_compatibility_report", return_value=None), \
                patch("bt_plan_adapter.publishable_problem", return_value=None), \
                self.assertRaises(SystemExit) as raised:
            bt_rounds.plan_decide(self.rdir, True, "", "web")
        self.assertIn("diseños", str(raised.exception))

    def test_requirements_without_planning_drafts_keep_the_legacy_flow(self):
        self.assertFalse(drafts.active(self.rdir))
        self.assertEqual(drafts.readiness(self.rdir), [])
        self.assertEqual(drafts.pin_for_plan(self.rdir), [])
        self.assertEqual(drafts.sync("demo", self.rdir), [])

    def test_failed_redesign_keeps_feedback_pending_and_old_draft_not_ready(self):
        drafts.request("demo", self.rdir)
        self.finish("D-1")
        drafts.add_feedback("demo", self.rdir, "checkout@v1", "Add Apple Pay", "web")
        self.outcomes["D-2"] = {"id": "D-2", "status": "blocked", "summary": "stuck"}  # contract left untouched
        row = drafts.rows(self.rdir)[0]
        self.assertEqual((row["status"], row["pending_feedback"]), ("failed", 1))
        self.assertEqual(drafts.sync("demo", self.rdir), [])  # backoff: no relaunch on every poll
        with self.assertRaises(SystemExit):
            drafts.pin_for_plan(self.rdir)

    def test_stop_hook_follows_only_requirements_still_being_planned(self):
        root = self.rdir.parent.parent.parent
        self.assertEqual(drafts.follow_project(root, "demo"), [])  # planning-time design never started: no-op
        drafts.request("demo", self.rdir)
        self.finish("D-1")
        drafts.add_feedback("demo", self.rdir, "checkout@v1", "Bigger pay button", "web")  # starts D-2 itself
        self.outcomes["D-2"] = {"id": "D-2", "status": "running_or_pending"}
        plan = self.rdir / "PLAN.md"
        plan.write_text(plan.read_text(encoding="utf-8").replace("status: review", "status: approved"), encoding="utf-8")
        self.assertEqual(drafts.follow_project(root, "demo"), [])  # approved plans are left alone

    def test_incomplete_contract_is_not_ready(self):
        drafts.request("demo", self.rdir)
        self.finish("D-1", contract="# Checkout\n## Only one section\n")
        row = drafts.rows(self.rdir)[0]
        self.assertEqual(row["status"], "failed")
        self.assertIn("fewer than", row["error"])

    def test_repeated_failures_stop_automatic_relaunches_until_the_owner_asks(self):
        drafts.request("demo", self.rdir)
        drafts.add_feedback("demo", self.rdir, "checkout@v1", "Add Apple Pay", "web")
        for did in ("D-1",):
            self.outcomes[did] = {"id": did, "status": "failed", "summary": "boom"}
        drafts.rows(self.rdir)
        with drafts._locked(self.rdir) as data:  # two more failures already happened, long ago
            data["drafts"]["checkout@v1"].update({"failures": drafts.MAX_FAILURES, "finished": "2000-01-01T00:00:00+00:00"})
        self.assertEqual(drafts.sync("demo", self.rdir), [])
        self.assertEqual(drafts.request("demo", self.rdir, ["checkout@v1"], force=True, reason="web"), ["checkout@v1"])

    def test_nothing_starts_once_the_plan_left_planning(self):
        plan = self.rdir / "PLAN.md"
        plan.write_text(plan.read_text(encoding="utf-8").replace("status: review", "status: launched"), encoding="utf-8")
        self.assertEqual(drafts.request("demo", self.rdir), [])
        self.assertIn("ya no está en planificación", drafts.add_feedback("demo", self.rdir, "checkout@v1", "x", "web"))
        self.assertFalse(drafts.active(self.rdir))

    def test_pinned_copy_is_what_the_run_uses_and_drift_after_approval_shows(self):
        drafts.request("demo", self.rdir)
        self.finish("D-1")
        drafts.pin_for_plan(self.rdir)
        drafts.paths(self.rdir, "checkout@v1")[0].write_text("tampered", encoding="utf-8")
        notes = drafts.execution_notes(self.rdir, "checkout@v1")
        self.assertIn("history/checkout@v1/approved.md", notes)
        changed = json.loads(json.dumps(PLAN))
        changed["subplans"][1]["outcome"] = "Pays twice."
        self.write_plan(changed)
        row = drafts.rows(self.rdir)[0]
        self.assertEqual((row["status"], row["stale"]), ("approved", True))

    def test_unparsable_plan_json_logs_no_phantom_changes(self):
        import bt_planning_activity as activity
        activity.observe(self.rdir)
        (self.rdir / "PLAN.json").write_text("{ broken", encoding="utf-8")
        self.assertEqual(activity.observe(self.rdir), 0)
        self.write_plan(PLAN)
        self.assertEqual(activity.observe(self.rdir), 0)
        self.assertEqual(activity.events(self.rdir), [])

    def test_view_options_reject_odd_input_and_markdown_cannot_break_out(self):
        import bt_pages
        opts = bt_page_planning.options(self.rdir, {"rev": "²", "sp": "<x>", "filter": "evil", "mode": "x"})
        self.assertEqual((opts["rev"], opts["sp"], opts["filter"], opts["mode"]), (0, "", "", "subplans"))
        block = bt_pages.md("b", "<!--<script>x</script>")
        self.assertNotIn("<!--", block)
        self.assertEqual(block.count("</script>"), 1)

    def test_unknown_contract_is_refused_and_does_not_enable_planning_design(self):
        self.assertIn("no es un subplan", drafts.add_feedback("demo", self.rdir, "../x@v1", "hi", "web"))
        drafts.request("demo", self.rdir, ["nope@v1"], force=True)
        self.assertFalse(drafts.active(self.rdir))

    def test_plan_tab_shows_subplans_designs_and_stamps_live_blocks(self):
        drafts.request("demo", self.rdir)
        self.finish("D-1")
        opts = bt_page_planning.options(self.rdir, {"lang": "en", "sp": "SP-2"})
        html = bt_page_planning.fragment("demo", "REQ-001", self.rdir, "review", "tok", opts)
        self.assertIn('data-k="detail-SP-2-design" data-h=', html)
        self.assertIn("/mockup?contract=checkout@v1", html)
        self.assertIn("Which payment providers?", html)
        self.assertIn('aria-label="Enviar al Designer"', html)
        self.assertIn('value="approve">Aprobar y lanzar', html)
        self.assertNotIn('value="approve" disabled', html)
        review = bt_page_planning.fragment("demo", "REQ-001", self.rdir, "review", "tok",
                                           bt_page_planning.options(self.rdir, {"mode": "review", "sp": "SP-2"}))
        self.assertIn('data-k="review-SP-2-1"', review)
        doc = bt_page_planning.fragment("demo", "REQ-001", self.rdir, "review", "tok",
                                        bt_page_planning.options(self.rdir, {"mode": "doc", "lang": "both"}))
        self.assertIn("Traducción · ES", doc)

    def test_activity_logs_plan_changes_after_the_baseline(self):
        import bt_planning_activity as activity
        self.assertEqual(activity.observe(self.rdir), 0)  # first look is the baseline
        changed = json.loads(json.dumps(PLAN))
        changed["subplans"][1]["acceptance_criteria"].append("Apple Pay is offered.")
        self.write_plan(changed)
        plan = self.rdir / "PLAN.md"
        plan.write_text(plan.read_text(encoding="utf-8") + "\n## Risks\nNone.\n", encoding="utf-8")
        self.assertEqual(activity.observe(self.rdir), 2)
        first, second = activity.events(self.rdir)[:2]
        self.assertIn("«Risks»", first["text"])
        self.assertEqual((second["sp"], second["diff"]), ("SP-2", "+ Apple Pay is offered."))
        self.assertIn("Risks", activity.changed_sections(self.rdir))


class TranslateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.rdir = Path(self.tmp.name) / "REQ-002-x"
        self.rdir.mkdir()
        (self.rdir / "PLAN.md").write_text("---\nstatus: review\n---\n# Plan\n\nIntro.\n\n## Tasks\nDo `T1`.\n",
                                           encoding="utf-8")
        (self.rdir / "SPEC.md").write_text("# Spec\n\nGoal.\n", encoding="utf-8")
        (self.rdir / "PLAN.json").write_text(json.dumps(PLAN), encoding="utf-8")
        self.calls = 0

    def ask(self, prompt: str) -> str:
        self.calls += 1
        items = json.loads(prompt[prompt.index("["):])
        return json.dumps(["ES:" + item for item in items])

    def test_sections_keep_front_matter_and_split_at_headings(self):
        front, parts = tr.sections((self.rdir / "PLAN.md").read_text(encoding="utf-8"))
        self.assertEqual(front, "---\nstatus: review\n---\n")
        self.assertEqual(parts, ["# Plan\n\nIntro.\n\n", "## Tasks\nDo `T1`.\n"])

    def test_translate_writes_spanish_files_and_only_retranslates_changed_sections(self):
        result = tr.translate("demo", self.rdir, ask=self.ask)
        self.assertEqual(result["pending"], 0)
        es = (self.rdir / "PLAN.es.md").read_text(encoding="utf-8")
        self.assertTrue(es.startswith("---\nstatus: review\n---\nES:# Plan"))
        self.assertEqual(tr.phrase(tr.load_cache(self.rdir), "Checkout screen"), "ES:Checkout screen")
        (self.rdir / "PLAN.md").write_text("---\nstatus: review\n---\n# Plan\n\nIntro.\n\n## Tasks\nDo `T2`.\n",
                                           encoding="utf-8")
        self.assertEqual(tr.pending(self.rdir), ["## Tasks\nDo `T2`.\n"])
        rendered, missing = tr.render(self.rdir, (self.rdir / "PLAN.md").read_text(encoding="utf-8"))
        self.assertEqual(missing, 1)
        self.assertIn("ES:# Plan", rendered)

    def test_bad_batch_answer_falls_back_to_one_call_per_section(self):
        answers = iter(["not json"])
        result = tr.translate("demo", self.rdir, ask=lambda p: next(answers, None) or self.ask(p))
        self.assertEqual(result["failed"], 0)
        self.assertGreater(self.calls, 1)

    def test_ensure_waits_for_edits_to_settle(self):
        with patch.object(tr, "start_background", return_value=7) as start:
            self.assertFalse(tr.ensure("demo", self.rdir))
            self.assertTrue(tr.ensure("demo", self.rdir, now=time.time() + tr.DEBOUNCE_SEC + 1))
        start.assert_called_once()


if __name__ == "__main__":
    unittest.main()
