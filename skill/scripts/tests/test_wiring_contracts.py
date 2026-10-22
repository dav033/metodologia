"""`PredecessorIntegrator.bind` REPLACES the whole binding. The composition binds it twice (the recovery block binds again to add
its evidence sink), and the second call once dropped `start_base_of` and `on_event`: the file-loss invariant then measured each
attempt's start from `snapshot^1` and none of its repairs was recorded. Every bind call of the composition must say all of it."""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "bt_scheduler_executor_wiring.py"
REQUIRED = {"plan", "repo_of", "default_repository", "identity", "accepted", "snapshot_of", "earlier_of", "start_base_of", "on_event",
            "on_conflict"}


class IntegratorBinding(unittest.TestCase):
    def test_the_binding_that_wins_names_every_hook(self):
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        calls = sorted((node for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                        and node.func.attr == "bind" and isinstance(node.func.value, ast.Name) and node.func.value.id == "integrate"),
                       key=lambda node: node.lineno)
        self.assertGreaterEqual(len(calls), 2)
        first, winner = {kw.arg for kw in calls[0].keywords}, {kw.arg for kw in calls[-1].keywords}
        self.assertEqual(REQUIRED - winner, set(), "the last bind() drops hooks the first one set")
        self.assertEqual({"start_base_of", "on_event"} - first, set())


if __name__ == "__main__":
    unittest.main()
