import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bt_notify
from types import SimpleNamespace
from unittest.mock import patch


def ev(kind, state, task="T1"):
    return {"kind": kind, "run": "p/REQ-001", "task": task, "summary": "x", "data": {"state": state}}


class TaskAlerts(unittest.TestCase):
    def test_only_enabled_projects_get_alerts_for_outcomes(self):
        self.assertIsNone(bt_notify.task_alert(ev("state_change", "accepted"), False))
        title, msg = bt_notify.task_alert(ev("state_change", "accepted"), True)
        self.assertIn("p/REQ-001", title)
        self.assertIn("aceptada", msg)
        self.assertIsNone(bt_notify.task_alert(ev("state_change", "running"), True))
        self.assertIsNone(bt_notify.task_alert(ev("state_change", "blocked"), True))     # attempts never "block"
        self.assertIsNotNone(bt_notify.task_alert(ev("task_state", "blocked"), True))
        self.assertIsNone(bt_notify.task_alert(ev("task_state", "completed"), True))

    def test_notify_task_events_reads_the_project_flag(self):
        with tempfile.TemporaryDirectory() as d, patch.object(bt_notify, "notify") as n:
            self.assertEqual(bt_notify.notify_task_events(Path(d), [ev("state_change", "rejected")]), 0)
            (Path(d) / "project.json").write_text(json.dumps({"notify_tasks": True}))
            self.assertEqual(bt_notify.notify_task_events(Path(d), [ev("state_change", "rejected"),
                                                                    ev("state_change", "running")]), 1)
            n.assert_called_once()

    def test_design_waiting_notification_is_sent_once_per_contract_version(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as d, patch.object(bt_notify, "notify") as send:
            self.assertTrue(bt_notify.notify_design_waiting(Path(d), "proj", "REQ-1", "checkout@v1"))
            self.assertFalse(bt_notify.notify_design_waiting(Path(d), "proj", "REQ-1", "checkout@v1"))
            self.assertTrue(bt_notify.notify_design_waiting(Path(d), "proj", "REQ-1", "checkout@v2"))
            self.assertEqual(send.call_count, 2)
            self.assertIn("Contrato de diseño esperando aprobación", send.call_args_list[0].args[1])

    def test_scheduler_completion_observer_claims_design_notice_outside_page_render(self):
        import bt_core
        import bt_scheduler_run
        with tempfile.TemporaryDirectory() as d, patch.object(bt_core, "ROOT", Path(d)), \
                patch.object(bt_notify, "notify") as send:
            rdir = Path(d) / "proj/requirements/REQ-1"
            rdir.mkdir(parents=True)
            (rdir / "PLAN.json").write_text(json.dumps({
                "subplans": [{"id": "SP-1", "ui": {"contract": "checkout", "version": 1,
                                                     "design_task": "T1"}}],
                "tasks": [{"id": "T1"}]}))
            snap = SimpleNamespace(tasks={"T1": {"state": "completed"}})
            bt_scheduler_run._notify_design_completions("proj", "REQ-1", rdir, snap)
            bt_scheduler_run._notify_design_completions("proj", "REQ-1", rdir, snap)
            send.assert_called_once()


if __name__ == "__main__":
    unittest.main()
