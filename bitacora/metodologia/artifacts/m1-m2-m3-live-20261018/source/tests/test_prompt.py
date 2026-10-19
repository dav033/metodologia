"""The prompt reflects the configured handoff policy actually used by the executor."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2])]
import bt_scheduler_executor as ex
from support import World, order


class Prompt(unittest.TestCase):
    def test_patch_mode_executor_prompt_forbids_commits(self):
        world = World(self, config=ex.Config(handoff_mode="patch", poll_seconds=0.02, grace_seconds=1,
                                             timeout_seconds=60))
        world.x.start(order(1, "ok"))
        details = world.finish("att-0001")
        prompt = Path(details["artifacts"]["prompt"]).read_text()
        self.assertIn("Do not create commits", prompt)
        self.assertNotIn("You may commit", prompt)
        self.assertIn("patch artifact", prompt)
