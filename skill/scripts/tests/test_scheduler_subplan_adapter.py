"""F4-3 adapter exposes the future composition facts without owning their implementation."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bt_scheduler_adapter as adapter


class SchedulerStub:
    def __init__(self):
        self.calls = []

    def record_subplan_version(self, *args):
        self.calls.append(("version", args))

    def record_composition(self, *args):
        self.calls.append(("composition", args))


class SubplanAdapter(unittest.TestCase):
    def test_fact_wrappers_forward_arguments_unchanged(self):
        scheduler = SchedulerStub()
        adapter.record_subplan_version(scheduler, "SP-1", 2, "a" * 40, "b" * 64)
        adapter.record_composition(scheduler, "published", "C2", {"SP-1": 2}, "c" * 64)
        self.assertEqual(scheduler.calls, [
            ("version", ("SP-1", 2, "a" * 40, "b" * 64)),
            ("composition", ("published", "C2", {"SP-1": 2}, "c" * 64, "")),
        ])


if __name__ == "__main__":
    unittest.main()
