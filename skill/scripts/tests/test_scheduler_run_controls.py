"""Web controls for Scheduler-owned runs call M1 without using legacy RUN.json."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import bt_cli_run_control
import bt_page_run
import bt_scheduler_adapter as adapter
import bt_server


class SchedulerRunControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.rdir = Path(self.temp.name) / "REQ-042-demo"
        self.rdir.mkdir()
        (self.rdir / "SCHEDULER.db").touch()

    def test_adapter_maps_controls_to_m1_and_opens_existing_database_read_write(self):
        fake = Mock()
        with patch.object(adapter, "authority", return_value=adapter.AUTHORITY), \
                patch.object(adapter, "approved_plan", return_value=object()), \
                patch.object(adapter, "run_db_path", return_value=self.rdir / "SCHEDULER.db"), \
                patch.object(adapter.core, "SqliteRepository") as repository, \
                patch.object(adapter.core, "SchedulerCore", return_value=fake) as scheduler:
            for action in ("pause", "resume", "stop"):
                adapter.apply_control(self.rdir, action, by="web")

        self.assertEqual(repository.call_args_list[0].kwargs, {"create": False})
        self.assertEqual(scheduler.call_count, 3)
        fake.pause.assert_called_once_with("web")
        fake.resume.assert_called_once_with("web")
        fake.cancel.assert_called_once_with("web")
        self.assertEqual(fake.inspect.call_count, 3)
        fake.start.assert_not_called()

    def test_scheduler_web_control_does_not_commit_but_legacy_behavior_still_does(self):
        handler = object.__new__(bt_server.Handler)
        handler.path = "/"
        with patch.object(bt_page_run, "scheduler_authority", return_value=True), \
                patch.object(bt_page_run, "apply_control", return_value="Pausada"), \
                patch.object(bt_server, "commit") as commit:
            self.assertEqual(handler.run_control("p", "REQ-042", self.rdir, {"action": "pause"}), "Pausada")
            commit.assert_not_called()

        with patch.object(bt_page_run, "scheduler_authority", return_value=False), \
                patch.object(bt_page_run, "apply_control", return_value="Pausada"), \
                patch.object(bt_server, "commit") as commit:
            handler.run_control("p", "REQ-042", self.rdir, {"action": "pause"})
            commit.assert_called_once()

    def test_scheduler_control_rejects_unknown_action_before_opening_database(self):
        with patch.object(adapter, "authority", return_value=adapter.AUTHORITY), \
                patch.object(adapter.core, "SqliteRepository") as repository, \
                self.assertRaisesRegex(SystemExit, "Acción desconocida"):
            adapter.apply_control(self.rdir, "merge", by="web")
        repository.assert_not_called()

    def test_cli_control_routes_scheduler_to_m1_and_preserves_legacy_implementation(self):
        run_file = self.rdir / "RUN.json"
        run_file.write_text('{"control":"leave untouched"}', encoding="utf-8")
        with patch.object(adapter, "scheduler_authority", return_value=True), \
                patch.object(adapter, "apply_control") as control:
            message = bt_cli_run_control.dispatch(self.rdir, "stop")
        control.assert_called_once_with(self.rdir, "stop", by="cli")
        self.assertIn("Cancelación", message)
        self.assertEqual(run_file.read_text(encoding="utf-8"), '{"control":"leave untouched"}')

        with patch.object(adapter, "scheduler_authority", return_value=False), \
                patch("bt_runtask.run_control", return_value="legacy control") as legacy:
            message = bt_cli_run_control.dispatch(self.rdir, "pause")
        legacy.assert_called_once_with(self.rdir, "pause")
        self.assertEqual(message, "legacy control")

    def test_web_scheduler_control_does_not_write_legacy_run_json(self):
        run_file = self.rdir / "RUN.json"
        original = '{"control":"legacy state"}'
        run_file.write_text(original, encoding="utf-8")
        with patch.object(bt_page_run, "scheduler_authority", return_value=True), \
                patch.object(adapter, "apply_control") as control:
            bt_page_run.apply_control(self.rdir, "stop")
        control.assert_called_once_with(self.rdir, "stop", by="web")
        self.assertEqual(run_file.read_text(encoding="utf-8"), original)


if __name__ == "__main__":
    unittest.main()
