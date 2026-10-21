"""Durable requirements approval through the public gate and runtime boundaries."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import bt_requirements_gate as gate


class RequirementsGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.rdir = Path(self.tmp.name)
        (self.rdir / "SPEC.md").write_text("# Scope\nBuild the approved feature.\n")
        (self.rdir / "PLAN.md").write_text(
            "---\nstatus: approved\nexecution_contract: requirements-v1\n---\n"
            "# Plan\n- [ ] T1 — implement\n## Progress log\n- started\n")
        self.review = {"goal": "Solve the problem", "scope": "Feature", "requirements": "Preserve behavior",
                       "limits": "No push or commits", "acceptance": "Tests pass",
                       "evidence": ["SPEC.md", "PLAN.md"], "unresolved": [],
                       "approval": "Owner approved in chat"}

    def test_missing_review_blocks_and_unchanged_review_retains_approval(self):
        self.assertEqual(gate.check(self.rdir)["status"], "needs_revalidation")
        gate.record(self.rdir, self.review)
        self.assertEqual(gate.check(self.rdir)["status"], "ready")
        gate.require_ready(self.rdir)
        plan = self.rdir / "PLAN.md"
        plan.write_text(plan.read_text().replace("approved", "launched").replace("[ ]", "[x]") + "- verified\n")
        self.assertEqual(gate.check(self.rdir)["status"], "ready")
        self.assertEqual(json.loads((self.rdir / "REQUIREMENTS.json").read_text())["approval"],
                         "Owner approved in chat")

    def test_drift_unresolved_and_revalidation(self):
        gate.record(self.rdir, self.review)
        spec = self.rdir / "SPEC.md"
        spec.write_text("# Scope\nChanged acceptance\n")
        self.assertIn("SPEC.md", " ".join(gate.check(self.rdir)["reasons"]))
        with self.assertRaises(SystemExit):
            gate.require_ready(self.rdir)
        gate.record(self.rdir, {**self.review, "unresolved": ["Owner must choose new limit"]})
        self.assertEqual(gate.check(self.rdir)["status"], "needs_revalidation")
        gate.record(self.rdir, self.review)
        self.assertEqual(gate.check(self.rdir)["status"], "ready")

    def test_removed_marker_cannot_bypass_snapshot_and_unknown_version_blocks(self):
        gate.record(self.rdir, self.review)
        plan = self.rdir / "PLAN.md"
        plan.write_text(plan.read_text().replace("execution_contract: requirements-v1\n", ""))
        self.assertEqual(gate.check(self.rdir)["status"], "needs_revalidation")
        plan.write_text(plan.read_text().replace("status: approved", "status: approved\nexecution_contract: future"))
        self.assertEqual(gate.check(self.rdir)["status"], "needs_revalidation")

    def test_invalid_snapshot_and_review_fail_closed(self):
        for field in ("goal", "scope", "requirements", "limits", "acceptance", "approval", "unresolved"):
            with self.subTest(field=field), self.assertRaises(ValueError):
                gate.record(self.rdir, {k: v for k, v in self.review.items() if k != field})
        for evidence in (["../outside"], [str(self.rdir / "SPEC.md")], ["REQUIREMENTS.json"]):
            with self.subTest(evidence=evidence), self.assertRaises((ValueError, OSError)):
                gate.record(self.rdir, {**self.review, "evidence": evidence})
        snapshot = gate.record(self.rdir, self.review)
        snapshot["schema"] = 2
        (self.rdir / "REQUIREMENTS.json").write_text(json.dumps(snapshot))
        self.assertEqual(gate.check(self.rdir)["status"], "needs_revalidation")

    def test_legacy_plan_remains_compatible(self):
        (self.rdir / "PLAN.md").write_text("---\nstatus: approved\n---\n# Legacy plan\n")
        self.assertEqual(gate.require_ready(self.rdir)["status"], "legacy")

    def test_runtime_launch_force_and_supervisor_cannot_bypass(self):
        import bt_handoff
        import bt_launch
        with (patch.object(bt_launch, "find_req", return_value=self.rdir),
              self.assertRaisesRegex(SystemExit, "REQUIREMENTS_REVALIDATION_REQUIRED")):
            bt_launch.launch("test", "REQ-001", force=True, dry_run=True)
        with (patch.object(bt_handoff, "find_req", return_value=self.rdir),
              self.assertRaisesRegex(SystemExit, "REQUIREMENTS_REVALIDATION_REQUIRED")):
            bt_handoff.handoff("test", "REQ-001", dry_run=True)

    def test_entry_context_distinguishes_supervised_children(self):
        root = self.rdir / "root"
        req = root / "test" / "requirements" / "REQ-001"
        req.mkdir(parents=True)
        (req / "PLAN.md").write_text((self.rdir / "PLAN.md").read_text())
        with patch.dict("os.environ", {}, clear=True):
            self.assertIn("missing or contradictory", gate.entry_context(root, "test"))
        with patch.dict("os.environ", {"BITACORA_RUN": "REQ-001", "BITACORA_TASK": "T1"}):
            self.assertIn("do not interview", gate.entry_context(root, "test"))

    def test_live_project_decisions_are_authority_and_spec_status_is_operational(self):
        project = self.rdir / "project"
        req = project / "requirements" / "REQ-001"
        req.mkdir(parents=True)
        for name in ("PLAN.md", "SPEC.md"):
            (req / name).write_text((self.rdir / name).read_text())
        spec = req / "SPEC.md"
        spec.write_text("---\nstatus: planned\n---\n# Scope\nApproved feature\n")
        decisions = project / "DECISIONS.md"
        decisions.write_text("# Decisions\nNo push\n")
        gate.record(req, self.review)
        spec.write_text(spec.read_text().replace("planned", "done"))
        self.assertEqual(gate.check(req)["status"], "ready")
        decisions.write_text("# Decisions\nContradictory limit\n")
        self.assertEqual(gate.check(req)["status"], "needs_revalidation")

    def test_a_decision_appended_after_the_approval_is_not_drift_but_an_edit_of_the_approved_text_is(self):
        project = self.rdir / "project"
        req = project / "requirements" / "REQ-001"
        req.mkdir(parents=True)
        for name in ("PLAN.md", "SPEC.md"):
            (req / name).write_text((self.rdir / name).read_text())
        decisions = project / "DECISIONS.md"
        decisions.write_text("# Decisions\n\n## D-001 No push\n- keep local\n")
        gate.record(req, self.review)
        with decisions.open("a") as handle:                                   # another session logs D-002
            handle.write("\n## D-002 Something else\n- unrelated\n")
        self.assertEqual(gate.check(req)["status"], "ready")
        decisions.write_text(decisions.read_text().replace("keep local", "push freely"))
        self.assertEqual(gate.check(req)["status"], "needs_revalidation")
        decisions.write_text("# Decisions\n\n## D-001 No push\n- keep local\n")        # back to the approved text
        self.assertEqual(gate.check(req)["status"], "ready")

    def test_contract_comments_quotes_and_malformed_present_marker_fail_closed(self):
        plan = self.rdir / "PLAN.md"
        for value in ("requirements-v1 # comment", "'requirements-v1'", '\"requirements-v1\" # comment'):
            plan.write_text("---\nexecution_contract: " + value + "\n---\nPlan\n")
            self.assertEqual(gate.check(self.rdir)["status"], "needs_revalidation")
        for value in ("", "''", '""', "[]", "future", "requirements-v1\nexecution_contract: requirements-v1"):
            plan.write_text("---\nexecution_contract: " + value + "\n---\nPlan\n")
            self.assertEqual(gate.check(self.rdir)["status"], "needs_revalidation")

    def test_aliased_plan_evidence_preserves_operational_status_and_checkbox_changes(self):
        gate.record(self.rdir, {**self.review, "evidence": ["./PLAN.md", "./SPEC.md"]})
        plan = self.rdir / "PLAN.md"
        plan.write_text(plan.read_text().replace("approved", "launched").replace("[ ]", "[x]"))
        self.assertEqual(gate.check(self.rdir)["status"], "ready")


    def test_last_dispatch_guard_persists_revalidation_and_releases_unstarted_tasks(self):
        import bt_runsession
        import bt_runstate
        state = bt_runstate.init_state("test", self.rdir, "codex", None, False)
        state["tasks"][0]["status"] = "in_progress"
        bt_runstate.save(self.rdir, state)
        with self.assertRaisesRegex(SystemExit, "REQUIREMENTS_REVALIDATION_REQUIRED"):
            bt_runsession.run_session("test", self.rdir, state, state["tasks"][0], 1, self.rdir, None)
        current = bt_runstate.load(self.rdir)
        self.assertEqual(current["status"], "needs_revalidation")
        self.assertEqual(current["tasks"][0]["status"], "todo")

    def test_business_status_in_body_is_authority_not_operational_frontmatter(self):
        for name in ("SPEC.md", "PLAN.md"):
            path = self.rdir / name
            body = "\n## Business contract\n```yaml\nstatus: pending\n```\n"
            original = path.read_text()
            path.write_text(original.replace("## Progress log", body + "## Progress log")
                            if "## Progress log" in original else original + body)
            gate.record(self.rdir, self.review)
            path.write_text(path.read_text().replace("status: pending", "status: accepted"))
            self.assertEqual(gate.check(self.rdir)["status"], "needs_revalidation")


if __name__ == "__main__":
    unittest.main()
