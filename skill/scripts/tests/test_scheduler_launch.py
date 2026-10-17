from __future__ import annotations

import argparse
import contextlib
import io
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch

import bt_cli_launch
from test_plan_integration import Isolated, bt_launch, planner


class SchedulerLaunchTests(Isolated):
    def setUp(self):
        super().setUp()
        self.set_status("approved")
        self.good_plan()
        planner.approve_freeze(self.rdir, bt_launch.req_id(self.rdir), planner.APPROVED_STATES)
        self.repo = Path(self._tmp.name) / "app"
        self.repo.mkdir()
        self.launch_state = Path(self._tmp.name) / "state"

    def invoke(self, **kwargs):
        with patch.object(bt_launch.ws, "clone_missing"), \
                patch.object(bt_launch.ws, "repos", return_value={"app": self.repo}), \
                patch.object(bt_launch.ws, "workdir", return_value=self.repo), \
                patch.object(bt_launch, "STATE", self.launch_state), \
                patch("bt_requirements_gate.require_ready", return_value={"status": "ready"}):
            return bt_launch.launch("sample", "REQ-001", mode="marathon", dry_run=True, **kwargs)

    def test_scheduler_option_routes_to_scheduler_run_after_frozen_plan_gate(self):
        with patch.object(bt_launch, "open_window") as open_window, \
                patch.object(bt_launch, "write_handoff", side_effect=AssertionError("legacy handoff used")), \
                patch.object(bt_launch, "marathon_script", side_effect=AssertionError("legacy supervisor used")):
            result = self.invoke(scheduler=True)

        self.assertIn("scheduler-run REQ-001", Path(result["script"]).read_text(encoding="utf-8"))
        self.assertEqual(result["opened"], "(dry run: not opened)")
        open_window.assert_not_called()

    def test_force_does_not_bypass_scheduler_approval(self):
        self.set_status("review")
        with patch.object(bt_launch, "scheduler_script") as scheduler_script, \
                self.assertRaisesRegex(SystemExit, "Scheduler launch requires PLAN.md status 'approved'"):
            self.invoke(scheduler=True, force=True)
        scheduler_script.assert_not_called()

    def test_force_does_not_create_a_frozen_scheduler_plan(self):
        shutil.rmtree(self.rdir / "plan-revisions")
        with self.assertRaisesRegex(SystemExit, "PLAN_NOT_FROZEN"):
            self.invoke(scheduler=True, force=True)
        self.assertFalse((self.rdir / "plan-revisions").exists())

    def test_scheduler_rejects_legacy_plan_without_plan_json(self):
        (self.rdir / "PLAN.json").unlink()
        shutil.rmtree(self.rdir / "plan-revisions")
        with self.assertRaisesRegex(SystemExit, "requires an approved frozen PLAN.json revision"):
            self.invoke(scheduler=True)
        self.assertFalse((self.launch_state / "launch").exists())

    def test_scheduler_option_requires_marathon_mode(self):
        with self.assertRaisesRegex(SystemExit, "--scheduler is only supported with --mode marathon"):
            bt_launch.launch("sample", "REQ-001", mode="loop", scheduler=True)

    def test_scheduler_option_rejects_foreground_mode_instead_of_falling_back(self):
        with self.assertRaisesRegex(SystemExit, "cannot be combined with --foreground"):
            bt_launch.launch("sample", "REQ-001", mode="marathon", scheduler=True, foreground=True)

    def test_cli_option_dispatches_scheduler_selection(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="cmd", required=True)
        bt_cli_launch.register(subparsers)
        args = parser.parse_args(["launch", "REQ-001", "--mode", "marathon", "--scheduler"])
        with patch("bt_launch.launch", return_value={"opened": "dry run"}) as launch, \
                contextlib.redirect_stdout(io.StringIO()):
            bt_cli_launch.dispatch(args, "sample")
        self.assertIs(launch.call_args.kwargs["scheduler"], True)

    def test_omitting_scheduler_preserves_legacy_marathon_route(self):
        with patch.object(bt_launch, "scheduler_script", side_effect=AssertionError("scheduler selected")):
            result = self.invoke()
        self.assertIn("run REQ-001", Path(result["script"]).read_text(encoding="utf-8"))
        self.assertIsNotNone(result["handoff"])


if __name__ == "__main__":
    unittest.main()
