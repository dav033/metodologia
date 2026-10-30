"""A durable run takes the operator's parallelism when it starts or a stage join starts its next run (D-239)."""
from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bt_durable import stage_join
from bt_durable.settings import Settings, configured


def knob(value):
    return patch("bt_config.get", lambda key, default=None: value if key == "scheduler.max_parallel_tasks" else default)


class Configured(unittest.TestCase):
    def test_the_operator_knob_sets_max_parallel(self):
        with knob(4):
            self.assertEqual(configured().max_parallel, 4)

    def test_a_recorded_run_keeps_everything_but_takes_the_live_knob(self):
        recorded = Settings(max_parallel=2, poll_seconds=3.0, owner_wait_seconds=60)
        with knob(5):
            out = configured(recorded)
        self.assertEqual((out.max_parallel, out.poll_seconds, out.owner_wait_seconds), (5, 3.0, 60))

    def test_out_of_range_is_clamped_and_garbage_keeps_the_base(self):
        with knob(99):
            self.assertEqual(configured().max_parallel, 16)
        with knob(0):
            self.assertEqual(configured().max_parallel, 1)
        for bad in ("4", True, None, 2.5):
            with knob(bad):
                self.assertEqual(configured(Settings(max_parallel=3)).max_parallel, 3)


class CallSites(unittest.TestCase):
    """Every place a run's settings are born goes through `configured` (pictures REQ-021 ran r15..r28 at 2 at once
    because `cli` started with `Settings()` and every join copied the previous run's value)."""

    def test_start_and_join_use_the_live_knobs(self):
        from bt_durable import cli
        source = inspect.getsource(cli)
        self.assertNotIn("Settings()", source)
        self.assertGreaterEqual(source.count("configured()"), 2)
        self.assertIn("configured(", inspect.getsource(stage_join))


if __name__ == "__main__":
    unittest.main()
