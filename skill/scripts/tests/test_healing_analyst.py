"""A confident external-cause analysis interrupts attempts through the ordinary stop and repair path."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bt_attempt_analyst as analyst
import bt_scheduler_decisions as decisions
import bt_scheduler_healing as healing


class AnalystStops(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.rdir = Path(self.tmp.name)
        self.doc = {"tasks": {"T1": {"state": "active", "attempts": ["a1"]}},
                    "attempts": {"a1": {"id": "a1", "task_id": "T1", "state": "running"}}}
        self.analysis = {"state": "done", "not_the_task": True, "confidence": "media", "failures": 7,
                         "cause": "The checker reads an ignored input", "solution": "repair the checker"}
        self.moves = []
        self.stop_during_move = False

    def run_cycle(self):
        analyst._save(self.rdir, "T1", self.analysis)

        def move(*args, **kwargs):
            self.moves.append((args, kwargs))
            self.doc["tasks"]["T1"].update(state="blocked", reason=args[5])
            self.doc["attempts"]["a1"]["state"] = "cancelled"
            if self.stop_during_move:
                healing.stop(self.rdir)
            return ["cancelled"]

        def cards(rdir):
            return [card for card in decisions._blocked(self.doc, rdir) if card["id"] not in decisions._answered(rdir)]

        with patch("bt_scheduler_decisions._state", side_effect=lambda _: copy.deepcopy(self.doc)), \
                patch("bt_scheduler_decisions._plan", return_value=None), \
                patch("bt_scheduler_decisions._context", return_value={"verify": "cancelled_by_executor"}), \
                patch("bt_scheduler_decisions.open_requests", side_effect=cards), \
                patch("bt_scheduler_ops.apply", side_effect=move), \
                patch.object(healing, "repair_task", return_value={"repair": "repair task T1.1", "result": "fixed"}) as repair:
            result = healing.cycle("p", "REQ-1", self.rdir)
        return result, repair

    def test_active_attempt_is_cancelled_and_analyst_case_builds_the_repair_in_the_same_cycle(self):
        result, repair = self.run_cycle()
        self.assertEqual(result, 1)
        self.assertEqual(self.moves[0][0][3:5], ("cancel-attempt", "a1"))
        self.assertTrue(self.moves[0][1]["block_task"])
        self.assertEqual(self.moves[0][1]["expected_task_state"], "active")
        self.assertIn("checker reads", repair.call_args.args[4].evidence[0])
        self.assertEqual(repair.call_args.args[4].kind, "regression")
        self.assertTrue(healing.load(self.rdir).get("analyst_stops"))

    def test_a_ready_task_is_blocked_without_cancelling_its_earlier_attempt(self):
        self.doc["tasks"]["T1"]["state"] = "ready"
        self.doc["attempts"]["a1"]["state"] = "failed"
        result, _ = self.run_cycle()
        self.assertEqual(result, 1)
        self.assertEqual(self.moves[0][0][4], "")

    def test_a_ready_task_whose_previous_card_was_answered_gets_a_fresh_card_and_repair(self):
        self.doc["tasks"]["T1"]["state"] = "ready"
        self.doc["attempts"]["a1"]["state"] = "failed"
        decisions.answers_path(self.rdir).write_text(json.dumps({"request": "T1:1"}) + "\n")
        result, repair = self.run_cycle()
        self.assertEqual(result, 1)
        self.assertNotEqual(repair.call_args.args[3]["id"], "T1:1")
        self.assertIn("analyst_not_the_task:", repair.call_args.args[3]["id"])

    def test_the_same_analysis_never_cancels_another_attempt_after_a_restart(self):
        self.run_cycle()
        self.doc["tasks"]["T1"]["state"] = "active"
        self.doc["attempts"]["a1"]["state"] = "running"
        self.assertEqual(self.run_cycle()[0], 0)
        self.assertEqual(len(self.moves), 1)

    def test_low_confidence_unfinished_and_task_local_analyses_do_not_interrupt(self):
        for change in ({"confidence": "baja"}, {"state": "running"}, {"not_the_task": False}):
            with self.subTest(change=change):
                original = self.analysis.copy()
                self.analysis.update(change)
                self.assertEqual(self.run_cycle()[0], 0)
                self.assertFalse(self.moves)
                self.analysis = original

    def test_hold_and_heal_stop_prevent_cancellation(self):
        with patch("bt_scheduler_ops.on_hold", return_value=True):
            self.assertEqual(self.run_cycle()[0], 0)
        healing.stop(self.rdir)
        self.assertEqual(self.run_cycle()[0], 0)
        self.assertFalse(self.moves)

    def test_heal_stop_during_cancellation_prevents_a_repair_in_the_same_turn(self):
        self.stop_during_move = True
        result, repair = self.run_cycle()
        self.assertEqual(result, 0)
        repair.assert_not_called()

    def test_a_committed_block_restores_the_marker_if_the_watcher_crashed_before_saving_it(self):
        self.run_cycle()
        state = healing.load(self.rdir)
        state.pop("analyst_stops")
        healing.save(self.rdir, state)
        self.run_cycle()
        self.doc["tasks"]["T1"]["state"] = "active"
        self.doc["attempts"]["a1"]["state"] = "running"
        self.assertEqual(self.run_cycle()[0], 0)
        self.assertEqual(len(self.moves), 1)


if __name__ == "__main__":
    unittest.main()
