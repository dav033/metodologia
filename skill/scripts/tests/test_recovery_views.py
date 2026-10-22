"""REQ-029 R7 (T10): the plan page shows what the scheduler healed by itself, what it gave up on, and lets the owner stop it or
revert a plan change; legacy cards stay."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bt_interventions
import bt_page_plans as pages
import bt_plans_api as api
import bt_scheduler_adapter as scheduler_
import bt_scheduler_healing as healing


class Views(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.rdir = self.root / "demo" / "requirements" / "REQ-001-x"
        self.rdir.mkdir(parents=True)
        (self.rdir / scheduler_.PROJECTION).write_text("{}")

    def case(self, **over):
        entry = {"id": "abc", "task": "T7", "class": "regression", "status": "applied", "applied": 1,
                 "repair": "plan r8: repair task T7.1 before T7", "revision": 8, "task_added": "T7.1", "target": "T7",
                 "after_restored": ["T6"]}
        entry.update(over)
        healing.save(self.rdir, {"actions": 1, "cases": {"abc": entry}})

    def test_the_state_lists_cases_and_the_latest_interventions_and_is_absent_for_a_plan_that_never_ran(self):
        self.case()
        bt_interventions.record(self.rdir, kind="regression", source="auto", task="T7", repair="repair task", result="fixed",
                                minutes_lost=12.4)
        state = api.healing_state(self.rdir)
        self.assertTrue(state["enabled"])
        self.assertEqual(state["cases"]["abc"]["task"], "T7")
        self.assertEqual(state["recent"][0]["class"], "regression")
        (self.rdir / scheduler_.PROJECTION).unlink()
        self.assertIsNone(api.healing_state(self.rdir))

    def test_the_panel_escapes_everything_that_comes_from_run_files_and_offers_stop_and_undo(self):
        self.case(task="T7<script>", repair="plan <img src=x onerror=alert(1)>")
        state = api.healing_state(self.rdir)
        html = pages._healing({"project": "demo", "req_id": "REQ-001", "healing": state}, "/p/demo/req/REQ-001", "tok")
        self.assertNotIn("<script>", html)
        self.assertNotIn("<img", html)
        self.assertIn("&lt;img", html)
        self.assertIn('value="stop"', html)                               # on: the control stops it
        self.assertIn('value="revert"', html)                             # a plan change can be undone
        self.assertIn('name="token" value="tok"', html)
        healing.stop(self.rdir)
        off = pages._healing({"project": "demo", "req_id": "REQ-001", "healing": api.healing_state(self.rdir)}, "/b", "tok")
        self.assertIn("detenida", off)
        self.assertIn('value="start"', off)
        self.assertEqual(pages._healing({"project": "demo", "req_id": "REQ-001", "healing": None}, "/b", "tok"), "")

    def test_a_reverted_case_offers_no_second_undo(self):
        self.case(status="reverted")
        html = pages._healing({"project": "d", "req_id": "R", "healing": api.healing_state(self.rdir)}, "/b", "t")
        self.assertNotIn('value="revert"', html)

    def test_the_controls_stop_start_and_revert_through_the_same_moves_as_the_cli(self):
        self.assertIn("off", api.heal_control(self.root, "demo", "REQ-001", "stop"))
        self.assertTrue((self.rdir / healing.OFF).exists())
        self.assertIn("on", api.heal_control(self.root, "demo", "REQ-001", "start"))
        self.assertFalse((self.rdir / healing.OFF).exists())
        with self.assertRaises(api.PlanError):
            api.heal_control(self.root, "demo", "REQ-001", "format-disk")
        with self.assertRaises(api.PlanError):
            api.heal_control(self.root, "demo", "REQ-001", "revert", "nope")            # a case that made no revision
        with patch.object(healing, "revert", return_value=["plan r9 without T7.1"]) as undo:
            self.assertEqual(api.heal_control(self.root, "demo", "REQ-001", "revert", "abc"), "plan r9 without T7.1")
            self.assertEqual(undo.call_args.args[:2], ("demo", "REQ-001"))

    def test_the_server_route_needs_the_token_like_every_other_post(self):
        import bt_server
        source = Path(bt_server.__file__).read_text()
        self.assertIn('"heal": lambda p, r: api.heal_control(', source)
        self.assertIn('form.get("token") != token()', source)                          # the shared guard runs before any action


if __name__ == "__main__":
    unittest.main()
