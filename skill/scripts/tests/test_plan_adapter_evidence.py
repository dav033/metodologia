"""Integration regressions for planner evidence checks in the methodology adapter."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import bt_plan_adapter as adapter  # noqa: E402
from bt_planner import sync  # noqa: E402
from bt_planner import contract as pc  # noqa: E402
from bt_planner import revisions as rev  # noqa: E402
from bt_planner.tests.support import classify  # noqa: E402


class PlanAdapterEvidence(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="plan-adapter-audit-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.rdir = self.root / "sample" / "requirements" / "REQ-001-demo"
        self.rdir.mkdir(parents=True)
        (self.rdir / "SPEC.md").write_text(
            "# Spec\n## Contract\n## Requirements\n- R1. Validate evidence safely.\n", encoding="utf-8"
        )
        (self.rdir / "PLAN.md").write_text(
            "---\nstatus: approved\n---\n# Plan\n\n### M1 — Base\n"
            "- [ ] T1 — Validate evidence · repo: app · verify: `python3 -m unittest`\n",
            encoding="utf-8")
        self.repo = self.root / "repo"
        (self.repo / "scripts").mkdir(parents=True)
        (self.repo / "package.json").write_text('{"scripts": {"test": "x"}}', encoding="utf-8")
        self.plan = classify(sync.skeleton(self.rdir, plan_id="REQ-001"))
        (self.rdir / "PLAN.json").write_text(pc.dumps(self.plan), encoding="utf-8")

    def verifier(self):
        with patch.object(adapter, "repo_roots", return_value={"app": self.repo}):
            return adapter.ref_verifier(self.rdir)

    def approve(self) -> dict:
        return sync.approve_freeze(self.rdir, "REQ-001", repo_roots={"app": self.repo}, verify_files=True)

    def compatibility_report(self) -> dict[str, object]:
        import bt_scheduler_adapter
        return bt_scheduler_adapter.plan_compatibility_report(self.rdir)

    def test_interpreter_options_and_wrappers_cannot_hide_missing_targets(self):
        verify = self.verifier()
        missing = (
            "python3 -W ignore scripts/missing.py",
            "python3.14 scripts/missing.py",
            "python3 -m missing_audit_module_49382",
            "npm --prefix no-such-folder run nope",
            "sh -c 'python3 scripts/missing.py'",
            "env python3 scripts/missing.py",
            "cd no-such-folder && python3 scripts/missing.py",
        )
        for command in missing:
            with self.subTest(command=command):
                self.assertIs(verify("command", command, "app"), False)

    def test_real_targets_still_pass_the_offline_command_check(self):
        (self.repo / "scripts" / "real.py").write_text("print(1)\n", encoding="utf-8")
        verify = self.verifier()
        self.assertTrue(verify("command", "python3 -W ignore scripts/real.py", "app"))
        self.assertTrue(verify("command", "python3 -m unittest", "app"))
        self.assertTrue(verify("command", "npm run test", "app"))
        self.assertTrue(verify("command", "cd scripts && python3 real.py", "app"))

    def test_resume_checks_plan_ref_identity_hash_and_presence(self):
        entry = self.approve()
        report = self.compatibility_report()
        wrong_id = {"plan_ref": {"plan_id": "REQ-OTHER", "revision": 1, "sha256": entry["sha256"]}}
        self.assertIn("PLAN_REF_MISMATCH", adapter.resume_problem(
            self.rdir, wrong_id, compatibility_report=report
        ) or "")

        missing_hash = {"plan_ref": {"plan_id": "REQ-001", "revision": 1}}
        self.assertIn("PLAN_REF_MISMATCH", adapter.resume_problem(
            self.rdir, missing_hash, compatibility_report=report
        ) or "")
        self.assertIn("PLAN_REF_MISSING", adapter.resume_problem(self.rdir, {}, compatibility_report=report) or "")

    def test_malformed_revision_state_is_returned_as_a_resume_problem(self):
        self.approve()
        frozen = rev.revision_path(self.rdir, 1)
        frozen.chmod(0o644)
        frozen.write_bytes(b"\xff")
        state = {"plan_ref": {"plan_id": "REQ-001", "revision": 1,
                               "sha256": rev.list_revisions(self.rdir)[0]["sha256"]}}
        report = self.compatibility_report()
        self.assertTrue((adapter.resume_problem(self.rdir, state, compatibility_report=report) or "").startswith("REVISION_"))
        self.assertTrue((adapter.launch_problem(self.rdir, compatibility_report=report) or "").startswith("REVISION_"))

    def test_malformed_manifest_is_returned_as_a_resume_problem(self):
        folder = self.rdir / "plan-revisions"
        folder.mkdir()
        (folder / rev.MANIFEST).write_text("[" * 100000 + "0" + "]" * 100000, encoding="utf-8")
        problem = adapter.resume_problem(self.rdir, {}, compatibility_report=self.compatibility_report())
        self.assertTrue(problem and problem.startswith("REVISION_STORE_UNREADABLE"), problem)


if __name__ == "__main__":
    unittest.main()
