"""Replay fidelity at the public simulator boundary; no provider calls."""
import importlib.util
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import bt_agents
import bt_runstate

path = Path(__file__).resolve().parents[3] / "evals" / "harness_replay.py"
spec = importlib.util.spec_from_file_location("harness_replay_fidelity", path)
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)


class ReplayFidelity(unittest.TestCase):
    def test_audits_inherit_milestone_risk_and_use_their_actual_tier(self):
        state = replay.build(bt_agents.start_tier)
        self.assertEqual([t["tier"] for t in state["tasks"] if t["kind"] == "audit"], [2, 1, 1])
        result = replay.replay(state, bt_runstate.unit_of, bt_agents.LADDER, False, lambda t: 0)
        audits = [s for s in result["log"] if s["tasks"] == ["M1-audit"]]
        self.assertEqual((audits[0]["model"], audits[0]["effort"]), ("opus", "high"))

    def test_docs_and_tests_match_runtime_budgets(self):
        for kind in ("docs", "test"):
            top_budget = ("haiku", None) if kind == "docs" else ("sonnet", "medium")
            for tier, budget in ((0, ("haiku", None)), (2, top_budget)):
                with self.subTest(kind=kind, tier=tier):
                    state = {"tasks": [{"id": "custom", "kind": kind, "tier": tier, "status": "todo", "after": []}]}
                    result = replay.replay(state, lambda s, t: [t], bt_agents.LADDER, False, lambda t: 0)
                    self.assertEqual((result["log"][0]["model"], result["log"][0]["effort"]), budget)

    def test_antagonist_cost_is_separate_and_reflects_review_policy(self):
        before = replay.replay(replay.build(bt_agents.start_tier), replay.old_unit_of,
                               replay.OLD_LADDER, True, lambda t: 0)
        after = replay.replay(replay.build(bt_agents.start_tier), bt_runstate.unit_of,
                              bt_agents.LADDER, False, lambda t: 0)
        self.assertEqual(before["antagonist_passes_per_commit"], 15)
        self.assertEqual(after["antagonist_passes_per_commit"], 0)
        self.assertEqual(before["antagonist_relative_cost_units"], 180.0)
        self.assertEqual(after["antagonist_relative_cost_units"], 0.0)


if __name__ == "__main__":
    unittest.main()
