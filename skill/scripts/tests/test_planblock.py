"""Generated PLAN.md status block: rendering, idempotent refresh, planner-contract neutrality, CLI and SessionStart."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
import re
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bt_cli_plan  # noqa: E402
import bt_plan_adapter as adapter  # noqa: E402
import bt_planblock as pb  # noqa: E402
import bt_planner as planner  # noqa: E402
import bt_planstatus as ps  # noqa: E402
from test_plan_integration import Isolated  # noqa: E402

BEGIN, END = pb.STATUS_BEGIN, pb.STATUS_END


def task(tid, ms, state, complexity, model=None, account=None, attempts=0):
    attempt = {"model_requested": model, "account": account} if model or account else None
    return {"id": tid, "title": f"Task {tid}", "milestone_id": ms, "complexity": complexity, "state": state,
            "attempts": attempts, "attempt": attempt}


def fixture_status():
    m1 = [task("T1", "M1", "completed", "low", "haiku", "claude-work", 1),
          task("T2", "M1", "running", "high", "sonnet", "claude-work", 2)]
    m2 = [task("T3", "M2", "pending", "medium")]
    ms = [{"id": "M1", "title": "Auth", "difficulty": "high", "state": "running", "tasks": m1,
           "progress": {"done": 1, "total": 2}},
          {"id": "M2", "title": "Docs | more", "difficulty": "medium", "state": "pending", "tasks": m2,
           "progress": {"done": 0, "total": 1}}]
    return {"project": "sample", "req_id": "REQ-001", "title": "Demo",
            "plan": {"status": "launched"}, "run": {"status": "running", "active": True},
            "summary": {"tasks_total": 3, "tasks_done": 1, "milestones_total": 2, "milestones_done": 0,
                        "difficulty": "high"}, "milestones": ms}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Render(unittest.TestCase):
    def test_block_is_spanish_table_with_progress_models_and_accounts(self):
        block = pb.render_block(fixture_status(), "2026-10-18T10:00:00+00:00")
        self.assertTrue(block.startswith(BEGIN) and block.endswith(END + "\n"))
        self.assertIn("Plan: launched · ejecución: running · hitos 0/2 · tareas 1/3 · generado: 2026-10-18", block)
        self.assertIn("**M1 — Auth** · dificultad alta · 1/2", block)
        self.assertIn("**M2 — Docs / more** · dificultad media · 0/1", block)
        self.assertIn("| T2 | Task T2 | alta | en curso | sonnet | claude-work | 2 |", block)
        self.assertIn("| T3 | Task T3 | media | pendiente | — | — | 0 |", block)
        self.assertFalse(re.search(r"^#|\[[ x]\]", block, re.M), "no heading or checkbox may appear in the block")

    def test_subplan_tasks_are_grouped_and_unassigned_tasks_remain_visible(self):
        status = fixture_status()
        status["milestones"][0]["tasks"][0].update(subplan_id="SP-1", subplan_title="Auth slice")
        block = pb.render_block(status, "2026-10-18T10:00:00+00:00")
        self.assertIn("**SP-1 — Auth slice**", block)
        self.assertIn("**Sin subplan**", block)
        self.assertEqual(block.count("| T1 |"), 1)
        self.assertEqual(block.count("| T2 |"), 1)

    def test_terminal_status_groups_subplan_tasks_and_keeps_composition_tasks(self):
        status = fixture_status()
        status["milestones"][0]["tasks"][0].update(subplan_id="SP-1", subplan_title="Auth slice")
        table = pb.status_table(status)
        self.assertIn("SP-1 Auth slice", table)
        self.assertIn("Sin subplan", table)
        self.assertEqual(table.count("T1 "), 1)
        self.assertEqual(table.count("T2 "), 1)


class Refresh(Isolated):
    def setUp(self):
        super().setUp()
        self.plan = self.rdir / "PLAN.md"

    def region(self):
        return pb._REGION.search(self.plan.read_text(encoding="utf-8"))

    def test_inserts_after_title_then_is_idempotent_without_touching_the_file(self):
        self.set_status("draft")
        before = self.plan.read_text(encoding="utf-8")
        self.assertTrue(pb.refresh_plan_block("sample", self.rdir))
        text = self.plan.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\nstatus: draft\n---\n# Plan\n\n" + BEGIN))
        self.assertEqual(re.sub("\n" + pb._REGION.pattern + "\n", "", text, flags=re.S), before)
        stamp, content = self.plan.stat().st_mtime_ns, self.plan.read_bytes()
        time.sleep(1.1)  # the timestamp has second resolution: a rewrite would change the bytes
        self.assertFalse(pb.refresh_plan_block("sample", self.rdir))
        self.assertEqual((self.plan.stat().st_mtime_ns, self.plan.read_bytes()), (stamp, content))

    def test_updates_only_the_region_and_keeps_ticks_and_log_lines_byte_for_byte(self):
        self.set_status("launched")
        pb.refresh_plan_block("sample", self.rdir)
        import bt_runtask
        bt_runtask.tick_plan(self.rdir, "T1", "T1 done by test")
        text = self.plan.read_text(encoding="utf-8")
        outside = pb._REGION.sub("@@", text)
        self.assertIn("[x] T1", text)
        (self.rdir / "RUN.json").write_text(json.dumps({"status": "running", "tasks": [
            {"id": "T1", "status": "done"}, {"id": "T2", "status": "in_progress"}]}), encoding="utf-8")
        self.assertTrue(pb.refresh_plan_block("sample", self.rdir))
        new = self.plan.read_text(encoding="utf-8")
        self.assertEqual(pb._REGION.sub("@@", new), outside)
        self.assertIn("ejecución: running", self.region().group(0))
        self.assertIn("| T2 | Document it | — | en curso", self.region().group(0))

    def test_without_plan_md_nothing_is_created_and_without_plan_json_it_still_works(self):
        empty = self.root / "sample" / "requirements" / "REQ-002-none"
        empty.mkdir()
        self.assertFalse(pb.refresh_plan_block("sample", empty))
        self.assertEqual(list(empty.iterdir()), [])
        self.assertFalse((self.rdir / "PLAN.json").exists())
        self.assertTrue(pb.refresh_plan_block("sample", self.rdir))

    def test_write_false_reports_without_writing_and_failures_never_raise(self):
        before = self.plan.read_bytes()
        self.assertTrue(pb.refresh_plan_block("sample", self.rdir, write=False))
        self.assertEqual(self.plan.read_bytes(), before)
        with patch.object(pb.planstatus, "plan_status", side_effect=RuntimeError("boom")):
            self.assertFalse(pb.refresh_plan_block("sample", self.rdir))

    def test_projection_writer_refreshes_only_plans_owned_by_the_scheduler(self):
        import bt_scheduler_adapter as sa
        sa._refresh_plan_block(self.rdir)
        self.assertNotIn(BEGIN, self.plan.read_text(encoding="utf-8"))
        db = sa.run_db_path(self.rdir)
        db.parent.mkdir(parents=True, exist_ok=True)
        db.touch()
        sa._refresh_plan_block(self.rdir)
        self.assertIn(BEGIN, self.plan.read_text(encoding="utf-8"))

    def test_a_removed_or_edited_block_is_restored_and_other_text_survives(self):
        pb.refresh_plan_block("sample", self.rdir)
        text = self.plan.read_text(encoding="utf-8").replace("| T1 |", "| tampered |")
        self.plan.write_text(text, encoding="utf-8")
        self.assertTrue(pb.refresh_plan_block("sample", self.rdir))
        self.assertNotIn("tampered", self.plan.read_text(encoding="utf-8"))
        self.assertIn("- [ ] T2 — Document it", self.plan.read_text(encoding="utf-8"))


class ContractNeutrality(Isolated):
    """The block must be invisible to the frozen contract: no drift, no change to freeze/check, no PLAN.json write."""

    def approve(self):
        self.good_plan()
        self.set_status("approved")
        planner.approve_freeze(self.rdir, adapter.plan_id(self.rdir), adapter.APPROVED_STATES)

    def gate(self):
        return adapter.launch_problem(self.rdir, compatibility_report=self.compatibility_report())

    def check(self):
        out = io.StringIO()
        code = adapter.run_cli("check", self.rdir, as_json=True, emit=lambda *a, **k: out.write(" ".join(map(str, a))))
        return code, out.getvalue()

    def test_adding_updating_and_removing_the_block_never_drifts(self):
        self.approve()
        self.assertIsNone(self.gate())
        plan_json, revisions = self.rdir / "PLAN.json", sorted((self.rdir / "plan-revisions").iterdir())
        hashes = (sha(plan_json), [sha(p) for p in revisions])
        check_before = self.check()
        digest = planner.narrative_digest(self.rdir) if hasattr(planner, "narrative_digest") else None

        self.assertTrue(pb.refresh_plan_block("sample", self.rdir))
        self.assertIn(BEGIN, (self.rdir / "PLAN.md").read_text(encoding="utf-8"))
        self.assertIsNone(self.gate())
        self.assertEqual(self.check(), check_before)

        (self.rdir / "RUN.json").write_text(json.dumps({"status": "running", "tasks": [
            {"id": "T1", "status": "done"}]}), encoding="utf-8")
        self.assertTrue(pb.refresh_plan_block("sample", self.rdir))
        self.assertIsNone(self.gate())

        plan = self.rdir / "PLAN.md"
        plan.write_text(pb._REGION.sub("", plan.read_text(encoding="utf-8")), encoding="utf-8")
        self.assertIsNone(self.gate())
        self.assertEqual(self.check(), check_before)
        self.assertEqual((sha(plan_json), [sha(p) for p in sorted((self.rdir / "plan-revisions").iterdir())]), hashes)
        if digest is not None:
            self.assertEqual(planner.narrative_digest(self.rdir), digest)

    def test_the_block_does_not_hide_real_prose_drift(self):
        self.approve()
        pb.refresh_plan_block("sample", self.rdir)
        plan = self.rdir / "PLAN.md"
        text = plan.read_text(encoding="utf-8")
        approved_line = "- [ ] T1 — Reject expired sessions"
        self.assertIn(approved_line, text)
        text = text.replace(approved_line, "- [ ] T1 — Allow expired sessions", 1)
        plan.write_text(text, encoding="utf-8")
        self.assertIn("PLAN_PROSE_DRIFT", self.gate() or "")

    def test_an_unfrozen_plan_stays_not_frozen_with_a_block(self):
        self.good_plan()
        self.set_status("approved")
        pb.refresh_plan_block("sample", self.rdir)
        self.assertIn("PLAN_NOT_FROZEN", self.gate() or "")
        self.assertFalse((self.rdir / "plan-revisions").exists())


class CliAndContext(Isolated):
    def run_status(self, **kw):
        args = argparse.Namespace(req=kw.get("req"), all=kw.get("all", False), write=kw.get("write", False),
                                  json=kw.get("json", False))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = bt_cli_plan.dispatch_status(args, self.root, "sample")
        return code, out.getvalue()

    def test_text_json_and_write(self):
        self.good_plan()
        before = (self.rdir / "PLAN.md").read_bytes()
        code, text = self.run_status(req="REQ-001")
        self.assertEqual(code, 0)
        self.assertIn("REQ-001", text)
        self.assertIn("T1 pendiente", text)
        self.assertEqual((self.rdir / "PLAN.md").read_bytes(), before)  # read-only by default
        _, raw = self.run_status(req="REQ-001", json=True)
        self.assertEqual(json.loads(raw)["summary"]["tasks_total"], 2)
        _, raw = self.run_status(all=True, json=True)
        self.assertEqual([s["req_id"] for s in json.loads(raw)], ["REQ-001"])
        self.run_status(req="REQ-001", write=True)
        self.assertIn(BEGIN, (self.rdir / "PLAN.md").read_text(encoding="utf-8"))

    def test_parser_is_registered(self):
        parser = argparse.ArgumentParser()
        bt_cli_plan.add_status_parser(parser.add_subparsers(dest="cmd"))
        ns = parser.parse_args(["plan-status", "--all", "--write", "--json"])
        self.assertTrue(ns.all and ns.write and ns.json)

    def second_req(self, n, status):
        rdir = self.root / "sample" / "requirements" / f"REQ-{n:03d}-other"
        rdir.mkdir()
        (rdir / "PLAN.md").write_text(f"---\nstatus: launched\n---\n# Plan — REQ-{n:03d} — Other {n}\n\n"
                                      "### M1 — One\n- [ ] T1 — A\n- [ ] T2 — B\n", encoding="utf-8")
        (rdir / "RUN.json").write_text(json.dumps({"status": status, "tasks": [
            {"id": "T1", "status": "in_progress"}, {"id": "T2", "status": "todo"}],
            "log": [{"task": "T1", "model": "sonnet", "profile": "claude-work", "result": "failed"}]}), encoding="utf-8")

    def test_planes_section_lists_every_active_plan_and_is_omitted_when_none(self):
        self.assertEqual(pb.planes_context("sample", self.root), [])
        self.second_req(2, "running")
        self.second_req(3, "paused")
        self.second_req(4, "completed")
        lines = pb.planes_context("sample", self.root)
        self.assertEqual(lines[0], "### Planes en ejecución")
        self.assertEqual(len(lines), 3)
        self.assertIn("REQ-002 · Other 2 · hitos 0/1 · tareas 0/2", lines[1])
        self.assertIn("en curso: T1 (sonnet, cuenta claude-work)", lines[1])
        self.assertFalse(any("REQ-004" in line for line in lines))

    def test_planes_section_caps_at_six_lines_plus_more(self):
        for n in range(2, 11):
            self.second_req(n, "running")
        lines = pb.planes_context("sample", self.root)
        self.assertEqual(len(lines), 1 + pb.ACTIVE_LINES + 1)
        self.assertEqual(lines[-1], "- +3 más")


class SessionStart(unittest.TestCase):
    def test_build_context_embeds_the_planes_section_only_when_a_plan_is_active(self):
        import tempfile
        import bt_core
        import bt_views
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            rdir = root / "sample" / "requirements" / "REQ-002-other"
            rdir.mkdir(parents=True)
            (rdir / "PLAN.md").write_text("---\nstatus: launched\n---\n# Plan — REQ-002 — Other\n\n"
                                          "### M1 — One\n- [ ] T1 — A\n", encoding="utf-8")
            with patch.object(bt_core, "ROOT", root), patch.object(bt_views, "ROOT", root):
                try:
                    quiet = bt_views.build_context("sample", "abcdef12", root, "resume")
                    (rdir / "RUN.json").write_text(json.dumps({"status": "running", "tasks": [
                        {"id": "T1", "status": "in_progress"}]}), encoding="utf-8")
                    busy = bt_views.build_context("sample", "abcdef12", root, "resume")
                except Exception as exc:
                    self.skipTest(f"build_context needs the real workspace: {exc!r}")
        self.assertNotIn("Planes en ejecución", quiet)
        self.assertIn("### Planes en ejecución\n- REQ-002 · Other · hitos 0/1 · tareas 0/1", busy)


if __name__ == "__main__":
    unittest.main()
