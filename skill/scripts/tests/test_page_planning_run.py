"""The «Ejecución» tab of a subplan: run progress in the Plan tab, forms that come back to it, and the actions behind them."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bt_page_planning_run as run  # noqa: E402
import bt_plans_api as api  # noqa: E402
import bt_server_plans  # noqa: E402


def task(tid, sid, state, live=False):
    return {"id": tid, "subplan_id": sid, "state": state, "attempt": {"live": live}}


def ctx(tasks):
    return {"run_status": {"milestones": [{"id": "M1", "tasks": tasks}], "decisions": []}}


class Progress(unittest.TestCase):
    def test_done_over_total_per_subplan_and_the_tab_label(self):
        c = ctx([task("T1", "SP-1", "completed"), task("T2", "SP-1", "completed"), task("T3", "SP-2", "pending")])
        self.assertEqual(run.counts(c), {"SP-1": (2, 2), "SP-2": (0, 1)})
        self.assertEqual(run.tab_label(c, "SP-1"), "Ejecución · 2/2")
        self.assertEqual(run.tab_label(c, "SP-9"), "Ejecución")

    def test_the_list_chip_marks_a_finished_subplan_and_hides_one_that_never_ran(self):
        c = ctx([task("T1", "SP-1", "completed"), task("T2", "SP-2", "pending"), task("T3", "SP-3", "completed"),
                 task("T4", "SP-3", "active", live=True), task("T5", "SP-4", "pending", live=False)])
        self.assertEqual(run.chip(c, "SP-1"), "ejecución 1/1 ✓")
        self.assertEqual(run.chip(c, "SP-3"), "ejecución 1/2")
        self.assertEqual(run.chip(c, "SP-2"), "")
        self.assertEqual(run.chip(c, "SP-4"), "")

    def test_without_a_readable_run_nothing_breaks(self):
        c = {"run_status": None}
        self.assertEqual((run.counts(c), run.chip(c, "SP-1"), run.tab_label(c, "SP-1")), ({}, "", "Ejecución"))


class Forms(unittest.TestCase):
    def test_every_form_gets_the_way_back_right_after_its_token(self):
        html = '<form><input type="hidden" name="token" value="t1"><button></button></form><form><input type="hidden" name="token" value="t2"></form>'
        out = run._back(html, "/p/x/req/REQ-1?tab=plan&view=run")
        self.assertEqual(out.count('name="back"'), 2)
        self.assertIn('name="token" value="t1"><input type="hidden" name="back"', out)


class Back(unittest.TestCase):
    def find(self):
        for value in vars(bt_server_plans).values():
            if isinstance(value, type) and "_back" in vars(value):
                return value._back
        raise AssertionError("no class with _back")

    def test_it_returns_to_a_local_plan_tab_path_and_replaces_the_old_message(self):
        back = self.find()
        out = back({"back": "/p/pictures/req/REQ-021?tab=plan&view=run&sp=SP-2&msg=old"}, "/plans/pictures/REQ-021", "hola mundo")
        self.assertTrue(out.startswith("/p/pictures/req/REQ-021?tab=plan&view=run&sp=SP-2"))
        self.assertEqual(out.count("msg="), 1)
        self.assertTrue(out.endswith("msg=hola%20mundo"))

    def test_it_refuses_anything_that_is_not_a_local_panel_path(self):
        back = self.find()
        for bad in ("https://evil.example/x", "//evil.example/x", "/plans/x", "/p/x\nSet-Cookie: a=b", "/p/x\\y", ""):
            self.assertEqual(back({"back": bad}, "/plans/p/r", "m"), "/plans/p/r?msg=m", bad)


class Actions(unittest.TestCase):
    def test_rework_needs_tasks_and_a_reason_and_sends_only_the_named_ones(self):
        with self.assertRaises(api.PlanError):
            api.rework(Path("/r"), "p", "REQ-1", [], "why")
        with patch.object(api, "req_dir", return_value=Path("/r")), self.assertRaises(api.PlanError):
            api.rework(Path("/r"), "p", "REQ-1", ["T1"], "   ")
        with patch.object(api, "req_dir", return_value=Path("/r")), patch("bt_scheduler_ops.apply", return_value=["T1: ok"]) as apply:
            msg = api.rework(Path("/r"), "p", "REQ-1", ["T1", "T1", "x; rm", "T2.3"], "fix it", confirm=True)
        self.assertEqual(apply.call_args.args[3:5], ("rework", "T1,T2.3"))
        self.assertTrue(apply.call_args.kwargs["only"] and apply.call_args.kwargs["confirm"])
        self.assertIn("T1, T2.3", msg)

    def test_retry_task_refuses_a_malformed_task_id(self):
        with patch.object(api, "req_dir", return_value=Path("/r")), self.assertRaises(api.PlanError):
            api.retry_task(Path("/r"), "p", "REQ-1", "T1; reboot")


if __name__ == "__main__":
    unittest.main()
