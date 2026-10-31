"""A run line and its base pin exist together, whatever line of `_run_line` a crash interrupts (REQ-030 audit).

The base pin (`<line>-base`) is where every subplan line starts. It was written by a second `update-ref` after the line;
a crash between the two left a line without a pin, and every later `sync` reported LINE_BASE_UNKNOWN until an operator
pinned it by hand (the pictures REQ-021 r15 upgrade procedure). Real git; the crash is injected after each ref write."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
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


class RetryCatchUp(unittest.TestCase):
    """D-262: a continuing retry starts from its earlier attempt's snapshot WITH the work integrated into its line since
    (pictures REQ-021 r32 T2.57 a2..a5 continued a1's empty snapshot while the v2 contract reached the SP-2 line)."""

    def setUp(self):
        self.repo = _repo()
        self.line = integration.GitLineIntegrator({"app": self.repo})
        self.task = SimpleNamespace(id="T2.57", repository="app")
        self.base = self.line.base_ref(RUN, self.task)                 # the run line, created at HEAD

    def commit_on(self, parent: str, name: str, text: str, message: str) -> str:
        git(self.repo, "checkout", "-q", "--detach", parent)
        (self.repo / name).parent.mkdir(parents=True, exist_ok=True)
        (self.repo / name).write_text(text)
        git(self.repo, "add", name)
        git(self.repo, "commit", "-q", "-m", message)
        return git(self.repo, "rev-parse", "HEAD")

    def advance_line(self, name: str, text: str) -> str:
        tip = self.commit_on(self.base, name, text, f"accepted {name}")
        git(self.repo, "update-ref", integration.GitLineIntegrator.line_ref(RUN, "app"), tip)
        return tip

    def files(self, ref: str) -> set[str]:
        return set(git(self.repo, "ls-tree", "-r", "--name-only", ref).split())

    def test_the_earlier_attempt_s_work_and_the_line_s_newer_work_both_reach_the_retry(self):
        snapshot = self.commit_on(self.base, "src/menu.tsx", "a1\n", "m3 snapshot proj-REQ-900-r1-T2.57-a1-0000aaaa")
        tip = self.advance_line("design/contracts/cuentas-admin@v2.md", "v2\n")
        base = self.line.continuation_base(RUN, self.task, snapshot)
        self.assertEqual(self.files(base), {"a.txt", "src/menu.tsx", "design/contracts/cuentas-admin@v2.md"})
        self.assertEqual(git(self.repo, "rev-parse", f"{base}^1"), snapshot)    # the continuation note reads it
        self.assertEqual(git(self.repo, "rev-parse", f"{base}^2"), tip)
        self.assertTrue(git(self.repo, "log", "-1", "--format=%s", base).startswith(integration.CATCH_UP))
        self.assertEqual(self.line.continuation_base(RUN, self.task, snapshot), base)   # deterministic (a step re-run)
        from bt_durable.adapters import m3
        ws = SimpleNamespace(repo=str(self.repo), base_sha=base, branch="m3/x-T2.57")
        note = m3._continuation(ws)
        self.assertIn("proj-REQ-900-r1-T2.57-a1-0000aaaa", note)
        self.assertIn(snapshot[:12], note)
        self.assertIn("merged into your tree", note)

    def test_an_attempt_that_changed_nothing_continues_from_the_current_line(self):
        tip = self.advance_line("design/contracts/cuentas-admin@v2.md", "v2\n")
        self.assertEqual(self.line.continuation_base(RUN, self.task, self.base), tip)  # a1: snapshot == its base

    def test_a_line_that_conflicts_with_the_snapshot_is_left_out(self):
        snapshot = self.commit_on(self.base, "a.txt", "mine\n", "m3 snapshot proj-REQ-900-r1-T2.57-a1-0000aaaa")
        self.advance_line("a.txt", "theirs\n")
        self.assertEqual(self.line.continuation_base(RUN, self.task, snapshot), snapshot)

    def test_a_snapshot_already_holding_the_line_is_kept(self):
        snapshot = self.commit_on(self.base, "src/menu.tsx", "a1\n", "m3 snapshot proj-REQ-900-r1-T2.57-a1-0000aaaa")
        self.assertEqual(self.line.continuation_base(RUN, self.task, snapshot), snapshot)


if __name__ == "__main__":
    unittest.main()
