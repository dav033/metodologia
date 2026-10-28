"""`plan-json stages`: would each next stage be approved? A deterministic walk of the cumulative stages, in plan order."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bt_plan_adapter as adapter  # noqa: E402


def plan(*pairs: tuple[str, int]) -> dict:
    return {"subplans": [{"id": sid} for sid, _ in pairs],
            "tasks": [{"id": f"{sid}.{n}", "subplan_id": sid} for sid, count in pairs for n in range(count)]}


class Readiness(unittest.TestCase):
    def run_it(self, draft: dict, approved: list[str], problems: dict[tuple, str]) -> list[dict]:
        calls: list[list[str]] = []

        def fake(rdir, subplans, **kwargs):
            calls.append(list(subplans))
            return problems.get(tuple(subplans))

        self.calls = calls
        with patch.object(adapter.planner.sync, "read_plan", return_value=(draft, None)), \
                patch.object(adapter.planner.stages, "latest", return_value=({"revision": 1}, {}) if approved else None), \
                patch.object(adapter.planner.stages, "subplans_in", return_value=approved), \
                patch.object(adapter, "stage_problem", side_effect=fake):
            return adapter.stage_readiness(Path("/nowhere"))

    def test_every_stage_is_cumulative_and_an_approved_subplan_is_skipped(self):
        rows = self.run_it(plan(("SP-1", 2), ("SP-2", 1), ("SP-3", 3), ("SP-4", 1)), ["SP-1", "SP-2"], {})
        self.assertEqual(self.calls, [["SP-3"], ["SP-3", "SP-4"]])
        self.assertEqual([(r["subplan"], r["ok"]) for r in rows], [("SP-3", True), ("SP-4", True)])

    def test_a_refused_stage_reports_its_problem_and_the_ones_after_it_still_run(self):
        rows = self.run_it(plan(("SP-1", 1), ("SP-3", 1), ("SP-4", 1)), ["SP-1"],
                           {("SP-3",): "COMPOSITION_MISSING: no gate composes SP-3 with SP-1"})
        self.assertFalse(rows[0]["ok"])
        self.assertIn("COMPOSITION_MISSING", rows[0]["problem"])
        self.assertTrue(rows[1]["ok"] or rows[1]["problem"] == "")            # judged on its own cumulative stage

    def test_a_subplan_without_tasks_ends_the_chain_and_what_follows_is_not_judged(self):
        rows = self.run_it(plan(("SP-3", 1), ("SP-7", 0), ("SP-8", 2)), [], {})
        self.assertEqual(self.calls, [["SP-3"]])
        self.assertEqual(rows[1]["problem"].split(":")[0], "sin tareas")
        self.assertEqual(rows[2]["depends_on_unfinished"], "SP-7")
        self.assertFalse(rows[2]["ok"])


if __name__ == "__main__":
    unittest.main()
