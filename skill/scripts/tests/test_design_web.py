from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bt_design_approval as approval
import bt_design_web
import bt_page_req


class DesignWebTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "root"
        self.rdir = self.root / "demo" / "requirements" / "REQ-001-ui"
        self.rdir.mkdir(parents=True)
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.repo, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=self.repo, check=True)
        contract = self.repo / "design/contracts/shop@v1.md"
        contract.parent.mkdir(parents=True)
        contract.write_text("# Shop contract\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-qm", "contract"], cwd=self.repo, check=True)
        (self.root / "demo" / "project.json").write_text(
            json.dumps({"repos": {"app": {"hint": str(self.repo), "remote": ""}}}), encoding="utf-8")
        (self.rdir / "PLAN.json").write_text(json.dumps({"subplans": [{"id": "SP-1", "ui": {
            "contract": "shop", "version": 1, "design_task": "T1"}}],
            "tasks": [{"id": "T1", "kind": "design", "repository": "app"}]}), encoding="utf-8")

    def test_changes_records_request_then_reworks_design_task_through_m1_adapter(self):
        rows = [{"contract": "shop@v1", "design_task": "T1"}]
        with patch.object(approval, "ui_contracts", return_value=rows), \
                patch("bt_scheduler_ops.apply", return_value=["sent back for rework: T1"]) as rework:
            commits = []
            message = bt_design_web.decide(self.root, "demo", "REQ-001", self.rdir,
                                           {"contract": "shop@v1", "decision": "changes",
                                            "comments": "Add an empty state"},
                                           lambda path, text: commits.append((path, text)))
        self.assertEqual(approval.approvals(self.rdir)["shop@v1"]["status"], "changes-requested")
        self.assertEqual(rework.call_args.args[3:6], ("rework", "T1", "Add an empty state"))
        self.assertIn("devuelta para rework", message)
        self.assertEqual(len(commits), 1)

    def test_matching_approval_reopens_ui_task_held_by_the_environment_gate(self):
        plan = json.loads((self.rdir / "PLAN.json").read_text(encoding="utf-8"))
        plan["tasks"].append({"id": "T2", "ui": True})
        (self.rdir / "PLAN.json").write_text(json.dumps(plan), encoding="utf-8")
        status = {"milestones": [{"tasks": [{"id": "T2", "state": "blocked",
                                                 "reason": "blocked_environment"}]}]}
        with patch("bt_planstatus.plan_status", return_value=status), \
                patch("bt_scheduler_ops.apply", return_value=["T2: reopened"]) as reopen:
            bt_design_web.decide(self.root, "demo", "REQ-001", self.rdir,
                                 {"contract": "shop@v1", "decision": "approve", "comments": ""},
                                 lambda *_: True)
        self.assertEqual(reopen.call_args.args[3:5], ("reopen", "T2"))
        self.assertIn("approved", approval.approvals(self.rdir)["shop@v1"]["status"])

    def test_requirement_panel_renders_contract_state_forms_and_enabled_preview(self):
        (self.repo / "design/preview").mkdir(parents=True)
        (self.repo / "design/preview/index.html").write_text("<h1>Preview</h1>", encoding="utf-8")
        row = {"subplan_id": "SP-1", "title": "Shop", "contract": "shop@v1",
               "path": "design/contracts/shop@v1.md", "design_task": "T1", "design_state": "completed",
               "approval": None}
        with patch.object(approval, "ui_contracts", return_value=[row]), \
                patch.object(approval, "repository_for_contract", return_value=self.repo), \
                patch("bt_config.get", return_value=True), patch("bt_notify.notify_design_waiting"):
            panel = bt_page_req.design_panel("demo", "REQ-001", self.rdir, "csrf-token")
        self.assertIn("Shop contract", panel)
        self.assertIn("Aprobar", panel)
        self.assertIn("Pedir cambios", panel)
        self.assertIn("aprobación", panel)
        self.assertIn("Abrir preview", panel)


if __name__ == "__main__":
    unittest.main()
