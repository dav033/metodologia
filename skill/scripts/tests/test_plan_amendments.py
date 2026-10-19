"""Plan evolution seen from the methodology: `plan-json amend`, the overlay M2 reads, the note in M1's audit."""
from __future__ import annotations

import io
import json
import tempfile
import unittest
from argparse import Namespace
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import bt_cli_plan
import bt_core
import bt_plan_adapter as plan_adapter
import bt_scheduler_adapter as adapter
import scheduler_chain_support as chain
import scheduler_executor_support as support
from bt_scheduler_decision.tests.support import PLAN_HASH, candidate


class Amendments(support.World):
    def setUp(self):
        super().setUp()
        tasks = [{"id": "T1", "title": "First", "repo": "app", "after": [], "complexity": "medium"},
                 {"id": "T2", "title": "Second", "repo": "app", "after": ["T1"], "complexity": "low"}]
        pipeline = chain.Pipeline(self, "amproj", "REQ-070", tasks, ["README.md"])
        (pipeline.rdir / "SPEC.md").write_text("# Amendments\n\n## Requirements\n- R1. Evolve.\n", encoding="utf-8")
        (pipeline.rdir / "PLAN.md").write_text(chain.plan_md("REQ-070", tasks), encoding="utf-8")
        with patch.object(bt_core, "ROOT", self.root):
            pipeline.step("init")
            chain.classify(pipeline.rdir, tasks, ["README.md"])
            pipeline.step("check")
            pipeline.step("freeze")
        self.rdir, self.pipeline, self.tasks = pipeline.rdir, pipeline, tasks

    def cli(self, *rest, **kw):
        args = Namespace(action=kw.pop("action", "amend"), req="REQ-070", rest=list(rest), reason=kw.pop("reason", "bigger"),
                         evidence=kw.pop("evidence", ["file:README.md"]), by=kw.pop("by", None),
                         proposed_by=kw.pop("proposed_by", "agent"), kind=None, force=False, json=False,
                         complexity=None, scope=None, risk=None, coupling=None)
        out = io.StringIO()
        with redirect_stdout(out), patch.object(bt_core, "ROOT", self.root):
            code = bt_cli_plan.dispatch(args, self.root, "amproj")
        return code, out.getvalue()

    def test_agent_raise_is_accepted_lower_needs_the_owner_and_evidence_is_required(self):
        code, out = self.cli("T1", "complexity", "high")
        self.assertEqual(code, 0, out)
        self.assertIn("medium → high", out)
        code, out = self.cli("T1", "complexity", "low")
        self.assertEqual((code, out.split(":")[0]), (2, "AMEND_LOWER_NEEDS_OWNER"))
        code, out = self.cli("T2", "risk", "high", evidence=[])
        self.assertEqual((code, out.split(":")[0]), (2, "AMEND_EVIDENCE"))
        code, out = self.cli("T1", "complexity", "low", proposed_by="owner", by="david")
        self.assertEqual(code, 0, out)
        self.assertEqual([r["to"] for r in plan_adapter.amendments(self.rdir)], ["high", "low"])

    def test_effective_overrides_only_list_what_changed(self):
        self.assertEqual(plan_adapter.effective_overrides(self.rdir), {})
        self.cli("T1", "complexity", "high")
        self.cli("T2", "estimated_minutes", "90")
        self.assertEqual(plan_adapter.effective_overrides(self.rdir),
                         {"T1": {"complexity": "high"}, "T2": {"estimated_minutes": 90}})

    def test_plan_status_shows_the_amended_value_the_original_and_the_timeline(self):
        import bt_planstatus
        self.cli("T1", "complexity", "high")
        with patch.object(bt_core, "ROOT", self.root):
            status = bt_planstatus.plan_status("amproj", self.rdir)
        tasks = {t["id"]: t for m in status["milestones"] for t in m["tasks"]}
        self.assertEqual((tasks["T1"]["complexity"], tasks["T1"]["complexity_original"]), ("high", "medium"))
        self.assertEqual((tasks["T2"]["complexity"], tasks["T2"]["complexity_original"]), ("low", None))
        self.assertEqual(status["milestones"][0]["difficulty"], "high")            # the milestone follows the amendment
        kinds = [item["kind"] for item in status["evolution"]["timeline"]]
        self.assertEqual(sorted(kinds), ["amendment", "revision"])

    def test_usage_error_and_listing(self):
        self.assertEqual(self.cli("T1", "complexity")[0], 2)
        self.cli("T1", "complexity", "high")
        code, out = self.cli(action="amendments")
        self.assertEqual((code, json.loads(out)[0]["field"]), (0, "complexity"))

    def test_the_next_m2_decision_sees_the_amended_classification_not_the_old_one(self):
        seen = []
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            overlay = lambda: plan_adapter.effective_overrides(self.rdir)  # noqa: E731
            port = adapter.DecisionAssignmentPort("proj", root / "m2.db", laya_root=root, classification_overlay=overlay)
            self.addCleanup(port.close)
            view = adapter.core.TaskView("T1", "M1", "app", (), (), 0,
                                         {"title": "x", "risk": "low", "complexity": "medium", "scope": "small_change"})

            def capture(project, kind, classifications, at):
                seen.append(dict(classifications))
                return (candidate(),)

            def order():
                return adapter.core.AssignmentRequest("REQ-070", 1, (view,), 1, 100.0, PLAN_HASH)

            with patch.object(adapter, "refresh_quota_preflight", return_value={
                    "work": {"status": "available", "reason": "quota_fresh"}}), \
                    patch.object(adapter.decision_sources, "_candidate_rows", side_effect=capture), \
                    patch("bt_scheduler_plan_routing.time.time", return_value=100.0):
                port.propose(order())
                code, out = self.cli("T1", "complexity", "high")
                self.assertEqual(code, 0, out)
                port.propose(adapter.core.AssignmentRequest("REQ-070", 1, (view,), 1, 100.0, PLAN_HASH))
        self.assertEqual(len(seen), 2)
        self.assertEqual(seen[0].get("complexity"), "medium")
        self.assertEqual(seen[1].get("complexity"), "high")

    def test_amendment_is_noted_in_the_m1_audit_without_changing_any_state(self):
        with patch.object(bt_core, "ROOT", self.root):
            scheduler = adapter.open_scheduler(self.rdir)
        try:
            before = scheduler.snapshot().tasks
            code, out = self.cli("T1", "complexity", "high")
            self.assertEqual(code, 0, out)
            self.assertIn("noted in the run audit", out)
            notes = [e for e in scheduler.audit_log() if e.kind == "amendment_applied"]
            self.assertEqual(len(notes), 1)
            self.assertEqual((notes[0].task_id, notes[0].detail["old"], notes[0].detail["new"], notes[0].detail["by"]),
                             ("T1", "medium", "high", "agent"))
            self.assertEqual(scheduler.snapshot().tasks, before)
        finally:
            del scheduler


if __name__ == "__main__":
    unittest.main()


class RebaseToLatest(Amendments):
    """A run on revision 1 is moved onto a revision 2 that added a task: the accepted task is kept."""

    def test_run_moves_to_revision_two_keeping_accepted_unchanged_work(self):
        tasks = self.tasks + [{"id": "T3", "title": "Third", "repo": "app", "after": ["T2"], "complexity": "low"}]
        pipeline = self.pipeline
        with patch.object(bt_core, "ROOT", self.root):
            scheduler = adapter.open_scheduler(self.rdir)               # a run on revision 1 (T1, T2)
            scheduler.step()
            attempt = scheduler.snapshot().tasks["T1"]["attempt"]
            token = scheduler.read(lambda c: c.state.attempts[attempt].token)
            core = adapter.core
            scheduler.ingest(core.Event("e1", "REQ-070", 1, "T1", attempt, "executor-x", "execution_finished", "", {}, token))
            scheduler.step()
            scheduler.submit_verdict(core.Verdict("v1", "REQ-070", 1, "T1", attempt, True, "validator", "ok", token))
            del scheduler
            (self.rdir / "PLAN.md").write_text(chain.plan_md("REQ-070", tasks), encoding="utf-8")
            plan_adapter.run_cli("init", self.rdir, force=True, emit=lambda _l: None)
            chain.classify(self.rdir, tasks, ["README.md"])
            pipeline.step("check")
            pipeline.step("freeze")
            report = adapter.rebase_to_latest(self.rdir)
        self.assertEqual((report.from_revision, report.to_revision), (1, 2))
        self.assertEqual(report.kept, ("T1",))
        self.assertEqual(report.added, ("T3",))
        self.assertEqual(set(report.reset), {"T2"})
        with patch.object(bt_core, "ROOT", self.root):
            resumed = adapter.open_scheduler(self.rdir)                  # binds to revision 2 without PLAN_MISMATCH
            states = {k: v["state"] for k, v in resumed.snapshot().tasks.items()}
        self.assertEqual((states["T1"], states["T3"]), ("completed", "pending"))
        self.assertEqual(states["T2"], "ready")

    def test_rebase_is_refused_without_a_run(self):
        with self.assertRaises(adapter.core.SchedulerError) as ctx:
            adapter.rebase_to_latest(self.rdir)
        self.assertEqual(ctx.exception.code, "NOT_ALLOWED")
