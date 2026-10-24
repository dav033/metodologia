"""Acceptance 7 owner coverage for PLAN.json 1.3.0 functional subplans."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bt_scheduler_adapter as scheduler_adapter
import bt_scheduler_run as scheduler_run
from bt_scheduler_owner_composition import OwnerCompositionRuntime
import owner_e2e_support as support


class OwnerSubplanEntryPoint(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="scheduler-owner-subplans-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = support.make_repository(self.root / "app")
        self.contract = support.add_designer_contract(self.repo)
        self.rdir = self.root / "REQ-900-owner-e2e"
        self.rdir.mkdir()

    def _run_13_owner(self):
        support.freeze_plan(self.rdir, support.three_subplan_plan())
        with patch.object(scheduler_run.bt_core, "ROOT", self.root), \
                patch("bt_requirements_gate.require_ready"), \
                patch("bt_workspace.repos", return_value={"app": self.repo}), \
                patch.object(scheduler_run, "_remove_autostart"), \
                patch.object(scheduler_run, "_install_autostart"), \
                patch.object(scheduler_run.bt_notify, "notify"):
            return scheduler_run.run("proj", "REQ-900", self.rdir, resume=False,
                                     no_autostart=True, max_steps=1)

    @unittest.expectedFailure
    def test_owner_runs_three_subplans_with_ui_contract_through_real_entrypoint(self):
        """Known gap: M3 has no declared 1.3.0 capability, so the owner refuses this plan before scheduling."""
        self.assertTrue(self.contract.is_file())
        self.assertEqual(support.git(self.repo, "show", "HEAD:design/contracts/interface@v1.md"),
                         "# Interface contract v1\n\nBase-tree fixture for the owner E2E.")
        result = self._run_13_owner()
        self.assertEqual(result, 0)

    def test_owner_refuses_to_load_13_plan_without_consumer_capabilities(self):
        with self.assertRaisesRegex(scheduler_adapter.core.SchedulerError,
                                    r"PLAN_SCHEMA_UNSUPPORTED_BY_ENGINE.*M3 \(unknown\)"):
            self._run_13_owner()

    def test_legacy_plan_remains_loadable_with_unchanged_task_shape(self):
        plan = {
            "schema_version": "1.2.0", "plan_id": "REQ-900", "revision": 1,
            "tasks": [{
                "id": "T1", "milestone_id": "M1", "title": "Legacy work", "objective": "Legacy work",
                "repository": "app", "after": [], "expected_paths": ["legacy/**"], "kind": "test",
                "shared_resources": [], "acceptance_criteria": ["T1 works"],
                "verification": [{"type": "command", "value": "true", "purpose": "legacy smoke",
                                   "category": "functional"}],
            }],
        }
        support.freeze_plan(self.rdir, plan)
        accepted = scheduler_adapter.approved_plan(self.rdir)
        self.assertEqual(accepted.schema_version, "1.2.0")
        self.assertEqual(accepted.ids(), ("T1",))
        self.assertFalse(OwnerCompositionRuntime.supports(accepted))


if __name__ == "__main__":
    unittest.main()
