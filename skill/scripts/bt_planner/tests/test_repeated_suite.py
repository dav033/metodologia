"""A whole-repository suite copied into most work tasks is a planner warning (REQ-020: `npm run gate` ~10 min in nearly every task)."""
import unittest

from bt_planner import quality


def task(tid, commands, kind="implement"):
    return {"id": tid, "kind": kind, "verification": [{"type": "command", "value": c} for c in commands]}


class RepeatedWholeSuite(unittest.TestCase):
    def test_the_suite_in_most_work_tasks_is_reported_once_with_the_count(self):
        plan = {"tasks": [task(f"T{n}", ["npm run gate", f"npx vitest run t{n}"]) for n in range(1, 7)]
                + [task("T7", ["npm run gate"], kind="audit")]}
        found = quality.repeated_whole_suite(plan)
        self.assertEqual(len(found), 1)
        self.assertIn("`npm run gate`", found[0])
        self.assertIn("6 of 6 work tasks", found[0])             # the audit is not a work task

    def test_a_suite_on_few_tasks_focused_tests_and_other_suite_spellings(self):
        few = {"tasks": [task("T1", ["npm run gate"]), task("T2", ["npx vitest run a"]), task("T3", ["npx vitest run b"]),
                         task("T4", ["npx vitest run c"]), task("T5", ["npx vitest run d"])]}
        self.assertEqual(quality.repeated_whole_suite(few), [])
        many = {"tasks": [task(f"T{n}", ["python3 -m unittest discover -s tests"]) for n in range(1, 5)]}
        self.assertEqual(len(quality.repeated_whole_suite(many)), 1)
        focused = {"tasks": [task(f"T{n}", [f"python3 -m unittest tests.test_{n}"]) for n in range(1, 5)]}
        self.assertEqual(quality.repeated_whole_suite(focused), [])


if __name__ == "__main__":
    unittest.main()
