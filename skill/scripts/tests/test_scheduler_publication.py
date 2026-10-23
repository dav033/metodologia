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

    def test_a_task_that_itself_creates_its_repository_or_pushes_gets_the_remote_actions_its_plan_approved(self):
        """david-ui REQ-001 T1: 'create private GitHub repo and push' with a prompt that said NEVER push blocked the run."""
        def brief(objective, criteria=("a",)):
            spec = SimpleNamespace(id="T1", meta={"title": "t", "objective": objective}, acceptance_criteria=criteria,
                                   expected_paths=(), verification=[])
            return PlanBriefs(SimpleNamespace(task=lambda _tid: spec)).brief(SimpleNamespace(task_id="T1"))

        self.assertTrue(brief("Scaffold the app; create private GitHub repo `dav033/david-ui` and push").remote_actions)
        self.assertTrue(brief("x", ("The GitHub repository dav033/david-ui is private and the scaffold is pushed.",)).remote_actions)
        self.assertFalse(brief("Add a push button to the form and fix the git remote url parsing").remote_actions)


if __name__ == "__main__":
    unittest.main()
