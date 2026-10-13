"""New-project onboarding guidance and its persistent purpose field."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import bt_core  # noqa: E402
import bt_views  # noqa: E402


class OnboardingContextTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="onboarding-test-")
        self.root = Path(self.tmp.name) / "bitacora"
        self.cwd = Path(self.tmp.name) / "workspace"
        self.cwd.mkdir()
        self.patches = [
            patch.object(bt_core, "ROOT", self.root),
            patch.object(bt_views, "ROOT", self.root),
        ]
        for item in self.patches:
            item.start()
        # Project creation must not initialize a git repository in the fixture.
        from bt_vcs import ensure_repo
        self.repo_patch = patch("bt_vcs.ensure_repo", lambda _root: None)
        self.repo_patch.start()

    def tearDown(self) -> None:
        self.repo_patch.stop()
        for item in reversed(self.patches):
            item.stop()
        self.tmp.cleanup()

    def test_new_project_context_starts_owner_interview_before_audit(self):
        context = bt_views.build_context("sample", "session-1234", self.cwd, "startup")

        self.assertIn("NEW PROJECT", context)
        self.assertIn("interview the owner", context)
        self.assertIn("purpose, users,", context)
        self.assertIn("deep workspace onboarding/audit", context)
        self.assertIn("then bootstrap ARCHITECTURE.md", context)

    def test_existing_project_does_not_get_a_false_new_project_prompt(self):
        bt_core.ensure_project("sample")

        context = bt_views.build_context("sample", "session-5678", self.cwd, "startup")

        self.assertNotIn("NEW PROJECT", context)
        self.assertNotIn("interview the owner", context)

    def test_summary_template_requires_explicit_owner_confirmation_date(self):
        template = (SCRIPTS.parent / "templates" / "SUMMARY.md").read_text(encoding="utf-8")

        self.assertIn("Last confirmed with owner: YYYY-MM-DD", template)
        self.assertIn("not yet confirmed", template)

    def test_empty_implementation_workspace_is_partial_and_not_started(self):
        guidance = (SCRIPTS.parent / "references" / "architecture-audit.md").read_text(encoding="utf-8")

        self.assertIn("no implementation repository yet", guidance)
        self.assertIn("code analysis to `not started`", guidance)
        self.assertIn("architecture audit `partial`", guidance)

    def test_reaudit_reconfirms_purpose_and_reports_material_changes(self):
        skill = (SCRIPTS.parent / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("restate it, ask what changed and confirm it with the owner", skill)
        self.assertIn("update its date only after confirmation", skill)


if __name__ == "__main__":
    unittest.main()
