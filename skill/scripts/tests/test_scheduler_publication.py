"""Only the plan's own publication step may push, and the brief marks it from the frozen verification."""
from __future__ import annotations

import unittest
from types import SimpleNamespace

from bt_scheduler_executor_adapter import PUBLISH_CHECK, PlanBriefs


class PublicationBrief(unittest.TestCase):
    def _brief(self, commands):
        spec = SimpleNamespace(id="T15", meta={"title": "t", "objective": "o"}, acceptance_criteria=("a",),
                               expected_paths=(),
                               verification=[{"type": "command", "value": c, "purpose": "a"} for c in commands])
        return PlanBriefs(SimpleNamespace(task=lambda _tid: spec)).brief(SimpleNamespace(task_id="T15"))

    def test_the_brief_marks_a_task_publishing_only_by_its_exact_origin_main_check(self):
        self.assertTrue(self._brief([PUBLISH_CHECK, "git diff --quiet HEAD origin/main"]).publishes)
        self.assertFalse(self._brief(["git diff --quiet HEAD origin/main"]).publishes)
        self.assertFalse(self._brief(["npm run gate"]).publishes)
        self.assertFalse(self._brief(["git merge-base --is-ancestor HEAD origin/develop"]).publishes)


if __name__ == "__main__":
    unittest.main()
