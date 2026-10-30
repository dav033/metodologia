"""A run line and its base pin exist together, whatever line of `_run_line` a crash interrupts (REQ-030 audit).

The base pin (`<line>-base`) is where every subplan line starts. It was written by a second `update-ref` after the line;
a crash between the two left a line without a pin, and every later `sync` reported LINE_BASE_UNKNOWN until an operator
pinned it by hand (the pictures REQ-021 r15 upgrade procedure). Real git; the crash is injected after each ref write."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from bt_contracts.execution import RunRef
from bt_durable.adapters import integration
from durable_support import git


class Crash(BaseException):
    """The engine dying right after a ref write (BaseException: nothing in the port may swallow it)."""


def _repo() -> Path:
    root = Path(tempfile.mkdtemp(prefix="bt-line-pin-"))
    git(root, "init", "-q", "-b", "main")
    (root / "a.txt").write_text("a\n")
    git(root, "add", "a.txt")
    git(root, "commit", "-q", "-m", "start")
    return root


RUN = RunRef(project="proj", req="REQ-900", revision=1, plan_id="REQ-900",
             plan_sha256="0" * 64, plan_path=Path("/nonexistent/plan-revisions/PLAN.r1.json"))


class RunLinePin(unittest.TestCase):
    def crash_after_ref_write(self, number: int):
        real, writes = integration._git, []

        def git_then_crash(repo, *args, **kwargs):
            done = real(repo, *args, **kwargs)
            if args and args[0] == "update-ref":
                writes.append(args)
                if len(writes) == number:
                    raise Crash(f"killed after ref write {number}")
            return done
        return mock.patch.object(integration, "_git", git_then_crash)

    def test_a_crash_after_any_ref_write_leaves_a_line_with_its_pin(self):
        for number in (1, 2):
            with self.subTest(crash_after=number):
                repo = _repo()
                head = git(repo, "rev-parse", "HEAD")
                line = integration.GitLineIntegrator({"app": repo})
                try:
                    with self.crash_after_ref_write(number):
                        line._run_line(RUN, "app")
                except Crash:
                    pass
                git(repo, "commit", "-q", "--allow-empty", "-m", "the repository moved on meanwhile")
                self.assertEqual(line._run_line(RUN, "app"), head)              # the engine after its restart
                self.assertEqual(line.line_base(RUN, "app"), head)

    def test_a_line_created_by_another_writer_is_adopted(self):
        repo = _repo()
        head = git(repo, "rev-parse", "HEAD")
        line = integration.GitLineIntegrator({"app": repo})
        ref = line.line_ref(RUN, "app")
        git(repo, "update-ref", ref, head)
        git(repo, "update-ref", ref + "-base", head)
        git(repo, "commit", "-q", "--allow-empty", "-m", "later")
        self.assertEqual(line._run_line(RUN, "app"), head)
        self.assertEqual(line.line_base(RUN, "app"), head)

    def test_a_pin_without_its_line_starts_the_line_at_the_pin(self):
        repo = _repo()
        head = git(repo, "rev-parse", "HEAD")
        line = integration.GitLineIntegrator({"app": repo})
        git(repo, "update-ref", line.line_ref(RUN, "app") + "-base", head)
        git(repo, "commit", "-q", "--allow-empty", "-m", "later")
        self.assertEqual(line._run_line(RUN, "app"), head)


if __name__ == "__main__":
    unittest.main()
