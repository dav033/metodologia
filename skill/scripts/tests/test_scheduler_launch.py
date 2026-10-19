from __future__ import annotations

import argparse
import contextlib
import io
import shutil
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
            return bt_launch.launch("sample", "REQ-001", dry_run=True, **kwargs)

    def test_launch_routes_to_scheduler_run_after_frozen_plan_gate(self):
        with patch.object(bt_launch, "open_window") as open_window:
            result = self.invoke()

        self.assertIn("scheduler-run REQ-001", Path(result["script"]).read_text(encoding="utf-8"))
        self.assertEqual(result["opened"], "(dry run: not opened)")
        self.assertIsNone(result["handoff"])
        open_window.assert_not_called()

    def test_launch_has_no_legacy_runner(self):
        for name in ("marathon_script", "write_handoff", "initial_prompt"):
            self.assertFalse(hasattr(bt_launch, name), name)

    def test_force_does_not_bypass_scheduler_approval(self):
        self.set_status("review")
        with patch.object(bt_launch, "scheduler_script") as scheduler_script, \
                self.assertRaisesRegex(SystemExit, "Scheduler launch requires PLAN.md status 'approved'"):
            self.invoke(force=True)
        scheduler_script.assert_not_called()

    def test_force_does_not_create_a_frozen_scheduler_plan(self):
        shutil.rmtree(self.rdir / "plan-revisions")
        with self.assertRaisesRegex(SystemExit, "PLAN_NOT_FROZEN"):
            self.invoke(force=True)
        self.assertFalse((self.rdir / "plan-revisions").exists())

    def test_plan_without_plan_json_is_refused_and_starts_no_runner(self):
        (self.rdir / "PLAN.json").unlink()
        shutil.rmtree(self.rdir / "plan-revisions")
        with patch.object(bt_launch, "open_window") as open_window, \
                patch.object(bt_launch, "scheduler_script") as scheduler_script, \
                self.assertRaisesRegex(SystemExit, r"PLAN_NOT_FROZEN: REQ-001 has no frozen PLAN\.json.*plan-json init"):
            bt_launch.launch("sample", "REQ-001", background=True)
        open_window.assert_not_called()
        scheduler_script.assert_not_called()
        self.assertFalse((self.launch_state / "launch").exists())

    def test_foreground_is_still_the_coordinator_path(self):
        with patch("bt_orchestration_transition.launch", return_value={"ok": True}) as fg:
            result = bt_launch.launch("sample", "REQ-001", foreground=True, dry_run=True)
        self.assertEqual(result, {"ok": True})
        fg.assert_called_once()

    def test_cli_no_longer_accepts_mode_pool_or_scheduler(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="cmd", required=True)
        bt_cli_launch.register(subparsers)
        for flag in (["--mode", "marathon"], ["--mode=loop"], ["--pool", "auto"], ["--scheduler"], ["--force"]):
            with self.subTest(flag=flag), contextlib.redirect_stderr(io.StringIO()), \
                    self.assertRaises(SystemExit):
                parser.parse_args(["launch", "REQ-001", *flag])

    def test_cli_dispatches_a_plain_launch(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="cmd", required=True)
        bt_cli_launch.register(subparsers)
        args = parser.parse_args(["launch", "REQ-001", "--background"])
        with patch("bt_launch.launch", return_value={"opened": "dry run"}) as launch, \
                contextlib.redirect_stdout(io.StringIO()):
            bt_cli_launch.dispatch(args, "sample")
        self.assertIs(launch.call_args.kwargs["background"], True)
        self.assertNotIn("scheduler", launch.call_args.kwargs)
