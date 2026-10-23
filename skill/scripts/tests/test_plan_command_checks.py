"""Ignored verification inputs are caught against real, temporary git checkouts."""
import subprocess
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bt_plan_adapter as adapter


class IgnoredInputs(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        subprocess.run(["git", "init", "--quiet", str(self.root)], check=True, capture_output=True)
        (self.root / ".gitignore").write_text("reports/*\n!reports/kept.json\n")

    def errors(self, *commands, repository=None):
        plan = {"tasks": [{"id": "T1", "repository": repository or str(self.root),
                           "verification": [{"type": "command", "value": c} for c in commands]}]}
        return [error for error in adapter.plan_errors(plan) if "git-ignored" in error]

    def test_an_ignored_input_is_rejected_even_when_it_exists_locally(self):
        (self.root / "reports").mkdir()
        (self.root / "reports/results.json").write_text("{}")
        self.assertEqual(len(self.errors("cat reports/results.json")), 1)

    def test_only_an_earlier_output_in_the_same_task_supplies_the_input(self):
        self.assertFalse(self.errors("generate --output reports/results.json", "cat reports/results.json"))
        self.assertTrue(self.errors("cat reports/results.json", "generate --output reports/results.json"))
        self.assertTrue(self.errors("cat reports/results.json", "cat reports/results.json"))
        self.assertFalse(self.errors("generate > reports/results.json", "cat reports/results.json"))
        self.assertFalse(self.errors("echo '{}' >reports/results.json", "cat reports/results.json"))

    def test_git_negations_and_tracked_files_are_not_reported_as_ignored(self):
        (self.root / "reports").mkdir()
        (self.root / "reports/results.json").write_text("{}")
        subprocess.run(["git", "-C", str(self.root), "add", "-f", "reports/results.json"], check=True, capture_output=True)
        self.assertFalse(self.errors("cat reports/results.json"))
        self.assertFalse(self.errors("cat reports/kept.json"))

    def test_options_quoted_paths_and_changed_directory_are_resolved(self):
        self.assertTrue(self.errors("check --input=reports/results.json"))
        self.assertTrue(self.errors("cat 'reports/a b.json'"))
        self.assertTrue(self.errors("cd reports && cat results.json"))
        self.assertTrue(self.errors(f"cat {self.root}/reports/results.json"))
        self.assertFalse(self.errors("cat /outside/reports/results.json"))

    def test_unignored_inputs_and_unavailable_checkouts_are_silent(self):
        self.assertFalse(self.errors("cat docs/results.json"))
        self.assertFalse(self.errors("cat reports/results.json", repository="unresolved"))
        with patch("bitacora_platform.plan_command_checks.subprocess.run", side_effect=FileNotFoundError):
            self.assertFalse(self.errors("cat reports/results.json"))

    def test_plan_json_check_resolves_repository_roles_and_prints_the_engine_ledger_command(self):
        golden = Path(adapter.planner.__file__).parent / "tests" / "golden" / "input-1.2.0.json"
        plan = json.loads(golden.read_text())
        task = plan["tasks"][0]
        task.update(repository="app", kind="audit")
        task["verification"][0]["value"] = "python scripts/check.py --input=reports/T1.findings.json"
        rdir = self.root / "REQ-001-example"
        rdir.mkdir()
        (rdir / "PLAN.json").write_text(json.dumps(plan))
        (rdir / "PLAN.md").write_text("---\nstatus: draft\n---\n# Plan\n")
        output = []
        with patch.object(adapter, "repo_roots", return_value={"app": self.root}), \
                patch.object(adapter, "ref_verifier", return_value=None):
            self.assertEqual(adapter.run_cli("check", rdir, emit=output.append), 2)
        self.assertTrue(any("git-ignored" in p for p in output))
        self.assertTrue(any("bitacora.py audit-ledger check" in p for p in output))


if __name__ == "__main__":
    unittest.main()
