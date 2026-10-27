"""Launch and resume gate integration tests."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from test_plan_integration import Isolated, PLAN_MD, SCRIPTS, adapter, bt_launch, planner


class LaunchPaths(Isolated):
    """Every way of starting work passes the same gate: valid, consistent with PLAN.md, exactly the approved revision."""

    def approved(self) -> dict:
        """What `plan approve` does: the plan is approved and exactly that PLAN.json is frozen."""
        plan = self.good_plan()
        self.set_status("approved")
        planner.approve_freeze(self.rdir, adapter.plan_id(self.rdir), adapter.APPROVED_STATES)
        return plan

    def revise(self, plan: dict, minutes: int) -> None:
        plan["revision"] += 1
        plan["tasks"][0]["estimated_minutes"] = minutes
        (self.rdir / "PLAN.json").write_text(planner.dumps(plan), encoding="utf-8")

    def revisions(self) -> list[int]:
        return [r["revision"] for r in planner.list_revisions(self.rdir)]

    def standard_launch(self, **kw):
        class Stop(Exception):
            pass
        with patch.object(bt_launch, "find_req", return_value=self.rdir), \
                patch("bt_requirements_gate.require_ready", return_value={"status": "ready"}), \
                patch.object(bt_launch.ws, "clone_missing"), \
                patch.object(bt_launch, "scheduler_script", side_effect=Stop):
            try:
                bt_launch.launch("sample", "REQ-001", **kw)
            except Stop:
                return "passed the gate"
        return "completed"

    def foreground_launch(self, **kw):
        import bt_orchestration_transition as transition
        with patch.object(transition.core, "find_req", return_value=self.rdir), \
                patch.object(transition.gate, "require_ready", return_value={"status": "ready"}), \
                patch.object(transition.state_, "load", return_value=None), \
                patch.object(transition.core.ws, "workdir", return_value=self.rdir), \
                patch.object(transition.client, "locate", return_value={"wrapper": None, "why": "no parent"}):
            return transition.launch("sample", "REQ-001", **kw)

    def open_run(self):
        adapter.freeze_on_launch(self.rdir, compatibility_report=self.compatibility_report())
        revision = planner.list_revisions(self.rdir)[-1]
        return {"plan_ref": {"plan_id": "REQ-001", "revision": revision["revision"], "sha256": revision["sha256"]}}

    # -- standard / web / handoff launch (bt_launch.launch) ---------------------------------------------------------
    def test_standard_launch_refuses_content_nobody_approved(self):
        plan = self.approved()
        self.assertEqual(self.standard_launch(), "passed the gate")
        self.assertEqual(self.revisions(), [1])
        self.revise(plan, 55)  # an edit after approval, with a bumped revision number
        with self.assertRaises(SystemExit) as ctx:
            self.standard_launch()
        self.assertIn("PLAN_DRIFT", str(ctx.exception))
        self.assertEqual(self.revisions(), [1])  # the launch did not freeze it on the way in

    def test_launch_after_a_new_approval_runs_the_new_revision(self):
        plan = self.approved()
        self.standard_launch()
        self.revise(plan, 55)
        rounds_module = __import__("bt_rounds")
        self.set_status("review")
        rounds_module.plan_decide(self.rdir, True, "", "test")
        self.assertEqual(self.revisions(), [1, 2])
        self.assertEqual(self.standard_launch(), "passed the gate")

    def test_force_neither_approves_nor_freezes_what_it_launches(self):
        self.good_plan()
        self.set_status("review")
        with self.assertRaisesRegex(SystemExit, "requires PLAN.md status 'approved'"):
            self.standard_launch(force=True)
        self.assertEqual(self.revisions(), [])
        broken = self.rdir.parent / "REQ-002-broken"
        broken.mkdir()
        (broken / "SPEC.md").write_text("# s\n", encoding="utf-8")
        (broken / "PLAN.md").write_text(PLAN_MD.format(status="review"), encoding="utf-8")
        planner.write_skeleton(broken)
        with self.assertRaises(SystemExit) as ctx:
            import bt_scheduler_adapter
            adapter.freeze_on_launch(
                broken, forced=True,
                compatibility_report=bt_scheduler_adapter.plan_compatibility_report(broken),
            )
        self.assertIn("PLAN_NOT_FROZEN", str(ctx.exception))         # a launch never approves anything
        self.assertFalse((broken / "plan-revisions").exists())

    def test_dry_run_validates_without_writing(self):
        self.approved()
        self.assertEqual(self.standard_launch(dry_run=True), "passed the gate")
        self.assertEqual(self.revisions(), [1])  # only the approval froze anything
        data = json.loads((self.rdir / "PLAN.json").read_text())
        data["tasks"][0]["risk"] = "critical"
        (self.rdir / "PLAN.json").write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(SystemExit) as ctx:
            self.standard_launch(dry_run=True)
        self.assertIn("PLAN_DRIFT", str(ctx.exception))
        self.assertEqual(self.revisions(), [1])

    def test_an_edit_of_approved_scope_blocks_launch_and_names_the_task(self):
        plan = self.approved()
        plan["tasks"][1]["after"] = []
        (self.rdir / "PLAN.json").write_text(planner.dumps(plan), encoding="utf-8")
        with self.assertRaises(SystemExit) as ctx:
            self.standard_launch()
        self.assertIn("PLAN_DRIFT", str(ctx.exception))
        self.assertIn("T2: changed", str(ctx.exception))

    # -- foreground transition ---------------------------------------------------------------------------------
    def test_foreground_launch_freezes_the_same_revision(self):
        self.approved()
        self.assertEqual(self.foreground_launch()["decision"], "manual")
        self.assertEqual(self.revisions(), [1])

    def test_foreground_dry_run_writes_nothing_and_refuses_drift(self):
        plan = self.approved()
        self.foreground_launch()
        self.revise(plan, 99)
        import bt_orchestration_terminal as terminal
        for kw in ({}, {"dry_run": True}):
            with self.assertRaisesRegex(terminal.TerminalError, "FOREGROUND_PLAN_REFUSED: PLAN_DRIFT"):
                self.foreground_launch(**kw)
        self.assertEqual(self.revisions(), [1])

    def test_foreground_refuses_an_invalid_plan_json(self):
        planner.write_skeleton(self.rdir)
        self.set_status("approved")
        import bt_orchestration_terminal as terminal
        with self.assertRaisesRegex(terminal.TerminalError, "FOREGROUND_PLAN_REFUSED: PLAN_NOT_FROZEN"):
            self.foreground_launch()
        self.assertFalse((self.rdir / "plan-revisions").exists())

    def test_successor_helper_rechecks_the_revision_before_replacing_the_session(self):
        import bt_orchestration_transition as transition
        source = Path(transition.__file__).read_text(encoding="utf-8")
        self.assertIn("plan_adapter.launch_problem(", source)
        self.assertIn("compatibility_report=bt_scheduler_adapter.plan_compatibility_report(rdir)", source)

    # -- the run itself ------------------------------------------------------------------------------------------
    def test_a_new_run_binds_the_frozen_revision_and_refuses_drift(self):
        plan = self.approved()
        state = self.open_run()
        self.assertEqual(state["plan_ref"]["revision"], 1)
        self.revise(plan, 70)
        with self.assertRaises(SystemExit) as ctx:
            self.open_run()
        self.assertIn("PLAN_DRIFT", str(ctx.exception))

    def test_a_new_run_of_an_unapproved_contract_plan_is_refused(self):
        self.good_plan()
        self.set_status("draft")
        with self.assertRaises(SystemExit) as ctx:
            self.open_run()
        self.assertIn("PLAN_NOT_APPROVED", str(ctx.exception))


    def resume(self, existing: dict):
        problem = adapter.resume_problem(self.rdir, existing, compatibility_report=self.compatibility_report())
        if problem:
            raise SystemExit(problem)
        return existing

    def test_a_resumed_run_is_never_rewritten_and_never_runs_unapproved_content(self):
        plan = self.approved()
        self.open_run()  # freezes r1
        existing = {"req": "REQ-001", "status": "paused", "sessions": 1, "tasks": [], "limits": {}, "log": [],
                    "plan_ref": {"plan_id": "REQ-001", "revision": 1,
                                 "sha256": planner.list_revisions(self.rdir)[0]["sha256"]}}
        before = json.dumps(existing, sort_keys=True)
        self.assertIs(self.resume(existing), existing)  # still the approved revision: resumes
        self.assertEqual(json.dumps(existing, sort_keys=True), before)
        self.revise(plan, 80)  # D-134: the draft is edited; the run keeps executing its approved revision
        self.assertIs(self.resume(existing), existing)
        self.assertEqual(json.dumps(existing, sort_keys=True), before)
        with self.assertRaises(SystemExit) as ctx:  # but never content with a hash nobody approved
            self.resume({**existing, "plan_ref": {**existing["plan_ref"], "sha256": "0" * 64}})
        self.assertIn("PLAN_REF_MISMATCH", str(ctx.exception))

    def test_resume_runs_the_frozen_revision_even_without_the_draft_but_never_an_unknown_hash(self):
        self.approved()
        self.open_run()
        (self.rdir / "PLAN.json").unlink()
        ref = {"plan_id": "REQ-001", "revision": 1, "sha256": planner.list_revisions(self.rdir)[0]["sha256"]}
        existing = {"req": "REQ-001", "status": "paused", "sessions": 1, "tasks": [], "limits": {}, "log": []}
        self.assertIsNone(adapter.resume_problem(self.rdir, {**existing, "plan_ref": ref},
                                                 compatibility_report=self.compatibility_report()))
        with self.assertRaises(SystemExit) as ctx:
            self.resume({**existing, "plan_ref": {**ref, "sha256": "x"}})
        self.assertIn("PLAN_REF_MISMATCH", str(ctx.exception))
        with self.assertRaises(SystemExit):                    # and a new launch needs the draft
            self.standard_launch()

    def test_resume_does_not_need_the_checkouts_that_launch_needed(self):
        plan = self.good_plan()
        plan["tasks"][0]["classification_evidence"]["scope"]["evidence"] = ["file:src/auth/session.py"]
        (self.rdir / "PLAN.json").write_text(planner.dumps(plan), encoding="utf-8")
        self.set_status("approved")
        planner.approve_freeze(self.rdir, adapter.plan_id(self.rdir), adapter.APPROVED_STATES)  # verified elsewhere
        existing = {"req": "REQ-001", "status": "paused", "sessions": 1, "tasks": [], "limits": {}, "log": [],
                    "plan_ref": {"plan_id": "REQ-001", "revision": 1,
                                 "sha256": planner.list_revisions(self.rdir)[0]["sha256"]}}
        report = self.compatibility_report()
        self.assertIsNone(adapter.resume_problem(self.rdir, existing, compatibility_report=report))
        self.assertIsNone(adapter.launch_problem(self.rdir, compatibility_report=report))  # evidence is judged at approval

    def test_foreground_freezes_nothing_when_the_workspace_is_unusable(self):
        import bt_orchestration_terminal as terminal
        import bt_orchestration_transition as transition
        self.approved()
        with patch.object(transition.core, "find_req", return_value=self.rdir), \
                patch.object(transition.gate, "require_ready", return_value={"status": "ready"}), \
                patch.object(transition.state_, "load", return_value=None), \
                patch.object(transition.core.ws, "workdir", return_value=None):
            with self.assertRaisesRegex(terminal.TerminalError, "FOREGROUND_WORKSPACE_REQUIRED"):
                transition.launch("sample", "REQ-001")
        self.assertEqual(self.revisions(), [1])  # nothing beyond the approval record

    def test_a_run_started_under_r1_resumes_on_r1_when_r2_is_approved_and_joins_it_later(self):
        plan = self.approved()
        self.open_run()
        existing = {"req": "REQ-001", "status": "paused", "sessions": 1, "tasks": [], "limits": {}, "log": [],
                    "plan_ref": {"plan_id": "REQ-001", "revision": 1, "sha256": planner.list_revisions(self.rdir)[0]["sha256"]}}
        report = self.compatibility_report()
        self.assertIsNone(adapter.resume_problem(self.rdir, existing, compatibility_report=report))
        self.revise(plan, 90)
        self.set_status("review")
        import bt_rounds
        bt_rounds.plan_decide(self.rdir, True, "", "test")  # approve r2
        self.assertIsNone(adapter.resume_problem(self.rdir, existing, compatibility_report=report))  # D-134
        self.assertIsNone(adapter.resume_problem(self.rdir, {**existing, "plan_ref": {"plan_id": "REQ-001",
                          "revision": 2, "sha256": planner.list_revisions(self.rdir)[-1]["sha256"]}},
                          compatibility_report=self.compatibility_report()))

    def test_approved_task_lines_changed_in_plan_md_block_the_launch_but_other_prose_does_not(self):
        self.approved()
        self.assertEqual(self.standard_launch(), "passed the gate")
        with (self.rdir / "PLAN.md").open("a", encoding="utf-8") as fh:
            fh.write("\n- 2026-10-15 09:00 launched marathon from HQ\n")  # dated log lines are bookkeeping
        self.assertEqual(self.standard_launch(), "passed the gate")
        text = (self.rdir / "PLAN.md").read_text(encoding="utf-8").replace("[ ] T1", "[x] T1")
        (self.rdir / "PLAN.md").write_text(text, encoding="utf-8")  # a tick is progress, not new instructions
        self.assertEqual(self.standard_launch(), "passed the gate")
        with (self.rdir / "PLAN.md").open("a", encoding="utf-8") as fh:
            fh.write("\nNotes for a later stage: ask about exports.\n")      # free prose is the planners' draft
        self.assertEqual(self.standard_launch(), "passed the gate")
        text = (self.rdir / "PLAN.md").read_text(encoding="utf-8")
        line = next(l for l in text.splitlines() if " T1 " in l and l.lstrip().startswith("- ["))
        (self.rdir / "PLAN.md").write_text(text.replace(line, line + " · risk: high"), encoding="utf-8")
        with self.assertRaises(SystemExit) as ctx:
            self.standard_launch()
        self.assertIn("PLAN_PROSE_DRIFT", str(ctx.exception))

    def test_resuming_a_run_of_a_legacy_plan_is_untouched(self):
        existing = {"req": "REQ-001", "status": "paused", "sessions": 1, "tasks": [], "limits": {}, "log": []}
        self.assertIs(self.resume(existing), existing)

    # -- approval ----------------------------------------------------------------------------------------------------
    def test_approval_refuses_an_invalid_plan_json_and_leaves_the_status(self):
        import bt_rounds
        planner.write_skeleton(self.rdir)
        self.set_status("review")
        with self.assertRaises(SystemExit) as ctx:
            bt_rounds.plan_decide(self.rdir, True, "", "terminal")
        self.assertIn("PLAN_INVALID", str(ctx.exception))
        self.assertEqual(planner.plan_status(self.rdir), "review")
        self.assertEqual(bt_rounds.plan_decide(self.rdir, False, "needs work", "terminal"), "changes-requested")

    def test_approval_freezes_exactly_the_approved_bytes(self):
        import bt_rounds
        plan = self.good_plan()
        self.set_status("review")
        self.assertEqual(bt_rounds.plan_decide(self.rdir, True, "", "terminal"), "approved")
        frozen = planner.load_revision(self.rdir, 1)
        self.assertEqual(planner.dumps(frozen), planner.dumps(plan))

    def test_approving_a_legacy_plan_is_unchanged(self):
        import bt_rounds
        self.set_status("review")
        self.assertEqual(bt_rounds.plan_decide(self.rdir, True, "", "terminal"), "approved")
        self.assertFalse((self.rdir / "plan-revisions").exists())

    # -- nothing can start a run around the gate ------------------------------------------------------------------
    def test_every_entry_that_creates_a_run_or_launches_goes_through_the_gate(self):
        callers = {path.name for path in SCRIPTS.glob("*.py")
                   if "init_state(" in path.read_text(encoding="utf-8") and path.name != "bt_runstate.py"}
        self.assertEqual(callers, set(), "a new module creates run state: route it through the launch gate")
        gated = {"bt_launch.py": "freeze_on_launch(",
                 "bt_orchestration_transition.py": "launch_problem("}
        for name, call in gated.items():
            self.assertIn(call, (SCRIPTS / name).read_text(encoding="utf-8"), name)
        self.assertIn("freeze_approved(", (SCRIPTS / "bt_rounds.py").read_text(encoding="utf-8"))
