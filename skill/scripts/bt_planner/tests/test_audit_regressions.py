"""Regression tests for defects found during the independent REQ-012 audit."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from bt_planner import contract as pc  # noqa: E402
from bt_planner import revisions as rev  # noqa: E402
from support import PLAN_MD, PlanDir  # noqa: E402


class AuditRegressions(PlanDir):
    def test_internal_underscore_runs_do_not_normalise_into_other_titles(self):
        self.md(text=PLAN_MD.format(status="approved").replace("Fix validation", "foo__bar"))
        plan = self.good()
        plan["tasks"][0]["title"] = "foobar"
        self.write(plan)
        self.assertTrue(any("T1.title:" in error for error in self.sync.check(self.rdir).errors))

    def test_compound_always_success_command_is_not_a_verification(self):
        plan = self.good()
        for command in ("true || true", ": && true", "echo ok || true"):
            with self.subTest(command=command):
                plan["tasks"][0]["verification"] = [
                    {"type": "command", "value": command, "purpose": "verify the task result"}]
                self.assertTrue(any("cannot fail, so it verifies nothing" in error
                                    for error in pc.validate(plan).errors))

    def test_file_evidence_cannot_follow_a_symlink_outside_the_repository(self):
        plan = self.good()
        repo = self.root / "backend"
        repo.mkdir()
        outside = self.root / "outside.py"
        outside.write_text("value = 1\n", encoding="utf-8")
        (repo / "external.py").symlink_to(outside)
        plan["tasks"][0]["classification_evidence"]["scope"]["evidence"] = ["file:external.py"]
        self.write(plan)

        report = self.sync.check(self.rdir, repo_roots={"backend": repo}, verify_files=True)
        self.assertTrue(any("does not exist in repository" in error for error in report.errors), report.errors)

    def test_non_utf8_frozen_revision_is_reported_without_leaking_decode_errors(self):
        self.good()
        self.sync.approve_freeze(self.rdir, "REQ-042")
        frozen = rev.revision_path(self.rdir, 1)
        frozen.chmod(0o644)
        frozen.write_bytes(b"\xff")

        report = self.sync.check(self.rdir)
        self.assertFalse(report.ok)
        with self.assertRaises(pc.PlanContractError):
            self.sync.bind_approved(self.rdir, "REQ-042")

    def test_deep_revision_manifest_is_reported_without_recursion_error(self):
        self.good()
        folder = self.rdir / "plan-revisions"
        folder.mkdir()
        (folder / rev.MANIFEST).write_text("[" * 2000 + "0" + "]" * 2000, encoding="utf-8")

        report = self.sync.check(self.rdir)
        self.assertFalse(report.ok)
        with self.assertRaises(pc.PlanContractError):
            self.sync.bind_approved(self.rdir, "REQ-042")
        with self.assertRaises(pc.PlanContractError):
            self.sync.approve_freeze(self.rdir, "REQ-042")

    def test_failed_revision_install_leaves_no_orphan_file(self):
        self.good()
        with patch.object(rev.os, "chmod", side_effect=PermissionError("permission denied")):
            with self.assertRaises(pc.PlanContractError):
                self.sync.approve_freeze(self.rdir, "REQ-042")
        self.assertFalse(rev.revision_path(self.rdir, 1).exists())

    def test_freeze_refuses_to_adopt_an_orphan_revision_symlink(self):
        plan = self.good()
        folder = self.rdir / "plan-revisions"
        folder.mkdir()
        outside = self.root / "outside-plan.json"
        original = pc.dumps(plan)
        outside.write_text(original, encoding="utf-8")
        rev.revision_path(self.rdir, 1).symlink_to(outside)

        with self.assertRaises(pc.PlanContractError):
            self.sync.approve_freeze(self.rdir, "REQ-042")
        self.assertFalse((folder / rev.MANIFEST).exists())
        self.assertEqual(outside.read_text(encoding="utf-8"), original)

if __name__ == "__main__":
    unittest.main()
