"""Project guards: the architecture checks every implement task of a repository carries."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bt_plan_guards as guards

GUARD = {"repo": "skill", "command": "cd skill/scripts && python3 -m unittest tests.test_plan_boundary", "why": "module boundaries"}


def task(tid, repo="skill", kind="implement", commands=()):
    return {"id": tid, "repository": repo, "kind": kind,
            "verification": [{"type": "command", "value": c, "purpose": "x"} for c in commands]}


class Guards(unittest.TestCase):
    def test_an_implement_task_without_the_guard_of_its_repository_is_warned_about(self):
        plan = {"tasks": [task("T1", commands=["pytest"]), task("T2", commands=[GUARD["command"]]),
                          task("T3", repo="other", commands=["pytest"]), task("T4", kind="test", commands=["pytest"]),
                          task("T5", kind="audit")]}
        found = guards.warnings(plan, [GUARD])
        self.assertEqual(len(found), 1)
        self.assertIn("T1.verification", found[0])
        self.assertIn("module boundaries", found[0])
        self.assertEqual(guards.warnings(plan, []), [])

    def test_the_guards_come_from_project_json_and_malformed_ones_are_ignored(self):
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp) / "project.json").write_text(json.dumps(
                {"repos": {}, "guards": [GUARD, {"repo": "skill"}, {"command": "x"}, "text", {"repo": "a", "command": " "}]}))
            self.assertEqual(guards.load(Path(temp)), [GUARD])
            self.assertEqual(guards.load(Path(temp) / "absent"), [])
            (Path(temp) / "project.json").write_text("not json")
            self.assertEqual(guards.load(Path(temp)), [])


if __name__ == "__main__":
    unittest.main()
