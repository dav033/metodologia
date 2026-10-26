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
                   patch.object(bt_delegate, "start_background", return_value=1),
                   patch.object(bt_delegate, "summary", side_effect=lambda did: self.outcomes.get(
                       did, {"id": did, "status": "running_or_pending"})),
                   patch.object(drafts, "_brief", side_effect=lambda project, rdir, row, feedback:
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

    def finish(self, did: str, contract: str = "# Checkout contract\n") -> None:
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
        self.assertEqual(row["sha256"], hashlib.sha256(b"# Checkout contract\n").hexdigest())

    def test_session_without_contract_fails_visibly(self):
        drafts.request("demo", self.rdir)
        self.outcomes["D-1"] = {"id": "D-1", "status": "failed", "summary": "no account"}
        row = drafts.rows(self.rdir)[0]
        self.assertEqual(row["status"], "failed")
        self.assertIn("no account", row["error"])

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
        self.assertEqual(record["sha256"], hashlib.sha256(b"# Checkout contract\n").hexdigest())
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

    def test_unknown_contract_is_refused_and_does_not_enable_planning_design(self):
        self.assertIn("no es un subplan", drafts.add_feedback("demo", self.rdir, "../x@v1", "hi", "web"))
        drafts.request("demo", self.rdir, ["nope@v1"], force=True)
        self.assertFalse(drafts.active(self.rdir))

    def test_plan_tab_shows_subplans_designs_and_stamps_live_blocks(self):
        drafts.request("demo", self.rdir)
        self.finish("D-1")
        html = bt_page_planning.fragment("demo", "REQ-001", self.rdir, "review", "tok", "en")
        self.assertIn('data-k="sp-SP-2" data-h=', html)
        self.assertIn("/mockup?contract=checkout@v1", html)
        self.assertIn("Which payment providers?", html)
        self.assertIn("Enviar al Designer", html)
        self.assertNotIn(" disabled", html)


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
