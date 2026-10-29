"""A sandbox check that names a host path fails on every attempt: the planner warns, approval refuses new ones (REQ-021 T4.1)."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bt_plan_adapter as adapter

GOLDEN = Path(adapter.planner.__file__).parent / "tests" / "golden" / "input-1.2.0.json"   # the adapter is the only door to the planner
HOST = "cmp -- design/contracts/x@v1.md /home/david/bitacora/p/requirements/REQ-021-x/design/x@v1.md"


class HostPathGate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.rdir = Path(self.tmp.name) / "REQ-001-x"
        self.rdir.mkdir()
        self.plan = json.loads(GOLDEN.read_text(encoding="utf-8"))

    def with_check(self, value: str, **extra) -> dict:
        plan = json.loads(json.dumps(self.plan))
        plan["tasks"][0]["verification"][0].update(value=value, **extra)
        return plan

    def test_host_paths_names_the_check_and_the_path(self):
        for value, path in ((HOST, "/home/david/bitacora/p/requirements/REQ-021-x/design/x@v1.md"),
                            ("python3 tool.py --input=/root/data.json", "/root/data.json"),
                            ("CONFIG=~/cfg.toml npm test", "~/cfg.toml"),
                            ("cat ~/notes.md", "~/notes.md")):
            found = adapter.planner_command_checks.host_paths(self.with_check(value))
            self.assertEqual([(c["task_id"], c["verification_index"], c["path"]) for c in found],
                             [(self.plan["tasks"][0]["id"], 0, path)], value)

    def test_repository_and_system_paths_and_other_environments_pass(self):
        for value in ("cmp -- design/contracts/x@v1.md docs/x.md", "/usr/bin/env node scripts/check.mjs",
                      "node -e \"process.exit(require('fs').existsSync('a/b')?0:1)\"", "test -s /dev/stdin"):
            self.assertEqual(adapter.planner_command_checks.host_paths(self.with_check(value)), [], value)
        staged = self.with_check(HOST, environment="staging")
        self.assertEqual(adapter.planner_command_checks.host_paths(staged), [])

    def test_the_contract_warns_without_refusing(self):
        report = adapter.planner_contract.validate(self.with_check(HOST))
        self.assertTrue(any("outside the repository" in w and "/home/david/bitacora" in w for w in report.warnings),
                        report.warnings)
        self.assertFalse(any("outside the repository" in e for e in report.errors))

    def test_approval_refuses_a_new_host_path_check(self):
        problem = adapter.host_path_lines(self.with_check(HOST), None)
        self.assertIn("PLAN_CHECK_HOST_PATH", problem)
        self.assertIn(f"{self.plan['tasks'][0]['id']}.verification[0]", problem)

    def test_a_check_frozen_as_it_is_is_not_gated_again_but_a_changed_one_is(self):
        frozen = self.with_check(HOST)
        self.assertIsNone(adapter.host_path_lines(frozen, ({"revision": 3}, frozen)))
        changed = self.with_check(HOST.replace("x@v1.md /home", "y@v1.md /home"))
        self.assertIn("PLAN_CHECK_HOST_PATH", adapter.host_path_lines(changed, ({"revision": 3}, frozen)))

    def test_whole_plan_approval_consults_the_gate(self):
        (self.rdir / "PLAN.json").write_text(json.dumps(self.with_check(HOST)), encoding="utf-8")
        with patch.object(adapter.planner, "check", return_value=adapter.planner_contract.Report()), \
                patch.object(adapter, "plan_consumer_problem", return_value=None), \
                patch.object(adapter, "preflight_problem", return_value=None):
            self.assertIn("PLAN_CHECK_HOST_PATH", adapter.publishable_problem(self.rdir))

    def test_stage_approval_consults_the_gate(self):
        projection = self.with_check(HOST)
        with patch.object(adapter, "plan_consumer_problem", return_value=None), \
                patch.object(adapter, "_next_stage", return_value=(projection, projection)), \
                patch.object(adapter.planner, "check_stage", return_value=adapter.planner_contract.Report()), \
                patch.object(adapter.planner.stages, "latest", return_value=None), \
                patch.object(adapter, "second_auditor_lines", return_value=None):
            self.assertIn("PLAN_CHECK_HOST_PATH", adapter.stage_problem(self.rdir, ["SP-1"]))


if __name__ == "__main__":
    unittest.main()
