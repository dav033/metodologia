"""Plan scope/resource metadata stays frozen in RUN.json and participates in drift checks."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

_TEST_HOME = Path(tempfile.mkdtemp(prefix="isolation-plan-home-"))
os.environ["HOME"] = str(_TEST_HOME)

from test_marathon import MarathonCase
import bt_runstate as rs


class IsolationPlanMetadata(MarathonCase):
    def test_parse_task_line_keeps_absent_metadata_as_none(self):
        parsed = rs.parse_task_line("A task · repo: app · files: src/a, docs/b · resources: lockfile, port:5432")
        self.assertEqual(parsed["files"], ["src/a", "docs/b"])
        self.assertEqual(parsed["resources"], ["lockfile", "port:5432"])
        absent = rs.parse_task_line("A task · repo: app")
        self.assertIsNone(absent["files"])
        self.assertIsNone(absent["resources"])

    def test_new_task_preserves_scopes_and_resources(self):
        plan = {"id": "T1", "title": "task", "repo": "app", "after": [], "verify": None,
                "level": None, "files": ["src/a"], "resources": ["lockfile"], "done": False}
        task = rs._new_task(plan)
        self.assertEqual(task["files"], ["src/a"])
        self.assertEqual(task["resources"], ["lockfile"])
        self.assertEqual(task["files"], ["src/a"])
        self.assertEqual(task["resources"], ["lockfile"])

    def test_scope_metadata_strips_quotes_and_rejects_unsafe_paths(self):
        parsed = rs.parse_task_line("A task · files: `src/a.txt`, 'src/b' · resources: `verify`, \"port:5432\"")
        self.assertEqual(parsed["files"], ["src/a.txt", "src/b"])
        self.assertEqual(parsed["resources"], ["verify", "port:5432"])
        for value in ("../x", ".", "/tmp/a"):
            unsafe = rs.parse_task_line(f"A task · files: {value}")
            self.assertIsNone(unsafe["files"], value)
            self.assertTrue(unsafe["files_invalid"], value)

    def test_resume_reports_files_and_resources_drift_without_adopting_changes(self):
        self.make_req(["- [ ] T1 — task · repo: backend · files: src/a · resources: lockfile"])
        state = rs.init_state(self.project, self.rdir, "claude", "haiku", True)
        rs.save(self.rdir, state)
        plan = (self.rdir / "PLAN.md").read_text()
        (self.rdir / "PLAN.md").write_text(plan.replace("src/a", "src/b").replace("lockfile", "port:5432"))
        reopened = rs.sync_plan(rs.load(self.rdir), self.rdir)
        self.assertIn("T1.files", reopened["plan_drift"])
        self.assertIn("T1.resources", reopened["plan_drift"])
        self.assertEqual(reopened["tasks"][0]["files"], ["src/a"])
        self.assertEqual(reopened["tasks"][0]["resources"], ["lockfile"])


if __name__ == "__main__":
    import unittest
    unittest.main()
