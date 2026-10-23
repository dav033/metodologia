"""The prompt reflects the configured handoff policy actually used by the executor."""
from __future__ import annotations

import sys
import unittest
from types import SimpleNamespace
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


class PromptChecks(unittest.TestCase):
    def test_the_prompt_says_a_missing_check_script_is_the_agents_to_create(self):
        from bt_scheduler_executor.model import Brief
        from bt_scheduler_executor.prompt import build_prompt

        brief = Brief(title="T", objective="o", acceptance_criteria=("a",),
                      verification=("a: npx tsx scripts/test/new.ts",), expected_paths=(), notes="")
        request = SimpleNamespace(task_id="T1", acceptance_criteria=("a",))
        prompt = build_prompt(brief, request, workdir="/w", branch="b", report_path="/r.json")
        self.assertIn("npx tsx scripts/test/new.ts", prompt)
        self.assertIn("is yours to create", prompt)
        self.assertIn("nothing git-ignored", prompt)
        none = build_prompt(Brief(title="T", objective="o", acceptance_criteria=("a",), verification=(),
                                  expected_paths=(), notes=""), request, workdir="/w", branch="b",
                            report_path="/r.json")
        self.assertNotIn("is yours to create", none)


class PromptPublication(unittest.TestCase):
    def _prompt(self, publishes):
        from bt_scheduler_executor.model import Brief
        from bt_scheduler_executor.prompt import build_prompt

        brief = Brief(title="T", objective="o", acceptance_criteria=("a",), verification=("a: x",),
                      expected_paths=(), notes="", publishes=publishes)
        return build_prompt(brief, SimpleNamespace(task_id="T15", acceptance_criteria=("a",)),
                            workdir="/w", branch="b", report_path="/r.json")

    def test_only_the_publication_task_may_push_and_only_to_main_without_force(self):
        plain, publish = self._prompt(False), self._prompt(True)
        self.assertIn("Do not push, merge, rebase onto other branches", plain)
        self.assertNotIn("Publication", plain)
        self.assertIn("git push origin HEAD:main", publish)
        self.assertIn("Never use `--force`", publish)
        self.assertNotIn("Do not push, merge, rebase", publish)
        self.assertIn("The only remote action allowed is the publication above", publish)


class PromptRemoteActions(unittest.TestCase):
    def test_a_task_that_creates_and_pushes_its_own_repository_may_use_gh_and_push_never_force(self):
        from bt_scheduler_executor.model import Brief
        from bt_scheduler_executor.prompt import build_prompt

        def prompt(remote):
            brief = Brief(title="T", objective="o", acceptance_criteria=("a",), verification=("a: x",), remote_actions=remote)
            return build_prompt(brief, SimpleNamespace(task_id="T1", acceptance_criteria=("a",)), workdir="/w", branch="b",
                                report_path="/r.json")
        plain, remote = prompt(False), prompt(True)
        self.assertIn("Do not push, merge, rebase onto other branches", plain)
        self.assertIn("`gh repo view", remote)
        self.assertIn("Never use `--force`", remote)
        self.assertNotIn("Do not push, merge, rebase", remote)
        self.assertNotIn("mounted read-only", remote)


class PromptRtk(unittest.TestCase):
    def test_optional_rtk_preserves_native_prompt_and_verification(self):
        import hashlib
        from unittest.mock import patch
        from bt_scheduler_executor.model import Brief
        from bt_scheduler_executor.prompt import build_prompt, _rtk_available

        brief = Brief(title="T", verification=("npm run verify",))
        request = SimpleNamespace(task_id="T1", acceptance_criteria=())
        args = dict(workdir="/w", branch="b", report_path="/r.json")
        self.addCleanup(_rtk_available.cache_clear)
        _rtk_available.cache_clear()
        with patch("shutil.which", return_value=None):
            absent = build_prompt(brief, request, **args)
        _rtk_available.cache_clear()
        with patch("shutil.which", return_value="/bin/rtk"):
            present = build_prompt(brief, request, **args)
            disabled = build_prompt(brief, request, rtk=False, **args)
        self.assertEqual(hashlib.sha256(absent.encode()).hexdigest(),
                         "8ae02948b2b1d95850b35ee67c7833bf5c8e9ebd5a834717402085089607ce8b")
        self.assertEqual(absent, disabled)
        self.assertIn("rtk git status", present)
        self.assertIn("rtk recall <hash> --full", present)
        self.assertIn("verification commands exactly as written", present)
        self.assertIn("npm run verify", present)


class PromptWholeSuites(unittest.TestCase):
    def test_a_whole_suite_is_left_to_the_verifier_and_focused_checks_are_still_run_by_the_agent(self):
        from bt_scheduler_executor.model import Brief
        from bt_scheduler_executor.prompt import build_prompt, whole_suites

        def prompt(checks):
            brief = Brief(title="T", objective="o", acceptance_criteria=("a",), verification=checks)
            return build_prompt(brief, SimpleNamespace(task_id="T1", acceptance_criteria=("a",)), workdir="/w", branch="b",
                                report_path="/r.json")
        mixed = prompt(("regression: npm run gate", "functional: npx vitest run a.test.ts", "regression: npm run gate"))
        self.assertIn("do NOT run them yourself", mixed)
        self.assertIn("`npm run gate`", mixed)
        self.assertEqual(whole_suites(("x: npm run gate", "y: npx vitest run a", "z: python3 -m unittest discover -s tests")),
                         ["npm run gate", "python3 -m unittest discover -s tests"])
        self.assertNotIn("do NOT run them yourself", prompt(("functional: npx vitest run a.test.ts",)))


if __name__ == "__main__":
    unittest.main()
