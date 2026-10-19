"""Scheduler-only launch boundaries refuse overrides and duplicate authority."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import run_case_support  # noqa: F401
import bt_handoff
import bt_launch
import bt_orchestration_terminal as terminal
import bt_orchestration_transition as transition
import bt_scheduler_adapter
import bt_server


class SchedulerLaunchBoundaries(unittest.TestCase):
    def test_routing_overrides_refuse_before_requirement_lookup(self):
        for module, exception, options in (
            (bt_launch, SystemExit, ('agent', 'model', 'profile')),
            (bt_handoff, SystemExit, ('model', 'profile')),
            (transition, terminal.TerminalError, ('model', 'profile')),
        ):
            function = module.handoff if module is bt_handoff else module.launch
            for option in options:
                with self.subTest(module=module.__name__, option=option), \
                        self.assertRaisesRegex(exception, 'SCHEDULER_ROUTING_REQUIRED'):
                    function('demo', 'REQ-001', **{option: 'explicit'})

    def test_transition_requires_frozen_plan_before_inspecting_authority(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(bt_scheduler_adapter, 'authority') as authority:
            with self.assertRaisesRegex(terminal.TerminalError, 'PLAN_NOT_FROZEN'):
                transition.require_new_plan(Path(directory))
            authority.assert_not_called()

    def test_transition_refuses_existing_scheduler_or_legacy_authority(self):
        with tempfile.TemporaryDirectory() as directory:
            rdir = Path(directory)
            (rdir / 'PLAN.json').write_text('{}')
            for owner in ('scheduler', 'legacy'):
                with self.subTest(owner=owner), \
                        patch.object(bt_scheduler_adapter, 'authority', return_value=owner), \
                        self.assertRaisesRegex(terminal.TerminalError, 'FOREGROUND_RUN_EXISTS'):
                    transition.require_new_plan(rdir)

    def test_standard_launch_refuses_existing_authority_before_freeze_or_script(self):
        with tempfile.TemporaryDirectory() as directory:
            rdir = Path(directory)
            (rdir / 'PLAN.md').write_text('---\nstatus: approved\n---\n')
            (rdir / 'PLAN.json').write_text('{}')
            for owner in ('scheduler', 'legacy'):
                with self.subTest(owner=owner), \
                        patch.object(bt_launch, 'find_req', return_value=rdir), \
                        patch('bt_requirements_gate.require_ready'), \
                        patch.object(bt_launch.ws, 'repos', return_value={'main': rdir}), \
                        patch.object(bt_scheduler_adapter, 'authority', return_value=owner), \
                        patch('bt_plan_adapter.freeze_on_launch') as freeze, \
                        patch.object(bt_launch, 'scheduler_script') as script:
                    with self.assertRaisesRegex(SystemExit, 'SCHEDULER_RUN_EXISTS'):
                        bt_launch.launch('demo', 'REQ-001', dry_run=True)
                    freeze.assert_not_called()
                    script.assert_not_called()

    def test_review_changes_preserves_completed_status_and_does_not_launch(self):
        with tempfile.TemporaryDirectory() as directory:
            rdir = Path(directory)
            plan = rdir / 'PLAN.md'
            plan.write_text('---\nstatus: done\n---\n')
            with patch.object(bt_server, 'commit'), patch.object(bt_launch, 'launch') as launch:
                message = bt_server.Handler.review(None, 'demo', 'REQ-001', rdir,
                                                  {'decision': 'changes', 'comments': 'Fix the evidence'})
            self.assertIn('status: done', plan.read_text())
            self.assertIn('Fix the evidence', plan.read_text())
            self.assertIn('nueva revisión', message)
            launch.assert_not_called()
