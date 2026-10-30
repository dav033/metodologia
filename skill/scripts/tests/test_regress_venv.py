"""bt_regress creates the worktree's uv venv once when a suite needs it (an integration's worktree is a fresh checkout),
and every suite starts with the job-control signals at their default (D-227, D-229)."""
from __future__ import annotations

import signal
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bt_regress  # noqa: E402


class Venv(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.worktree = Path(self.temp.name) / "wt"
        (self.worktree / "skill" / "scripts" / "tests").mkdir(parents=True)
        bt_regress._VENVS.clear()
        self.addCleanup(bt_regress._VENVS.clear)
        self.calls = []

    def sync(self, *, ok=True):
        def runner(argv, **kwargs):
            self.calls.append((argv, kwargs["cwd"]))
            if ok:
                python = Path(kwargs["cwd"]) / ".venv" / "bin" / "python"
                python.parent.mkdir(parents=True, exist_ok=True)
                python.write_text("", encoding="utf-8")
            return subprocess.CompletedProcess(argv, 0 if ok else 2, "", "" if ok else "lock file out of date")
        return runner

    def test_a_missing_venv_is_synced_once_and_reused(self):
        first = bt_regress.venv(self.worktree, runner=self.sync())
        again = bt_regress.venv(self.worktree, runner=self.sync())
        self.assertEqual(first, (str(self.worktree.resolve() / ".venv" / "bin" / "python"), ""))
        self.assertEqual(again, first)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.calls[0][0][:3], ["uv", "sync", "--frozen"])

    def test_an_existing_venv_is_used_as_it_is(self):
        python = self.worktree / ".venv" / "bin" / "python"
        python.parent.mkdir(parents=True)
        python.write_text("", encoding="utf-8")
        self.assertEqual(bt_regress.venv(self.worktree, runner=self.sync())[0], str(python.resolve()))
        self.assertEqual(self.calls, [])

    def test_a_failed_sync_fails_the_suite_with_its_reason_instead_of_crashing_the_regression(self):
        bt_regress.venv(self.worktree, runner=self.sync(ok=False))           # cached: the suite sees the failure
        suite = self.worktree / "skill" / "scripts" / "tests" / "test_durable_x.py"
        suite.write_text("import dbos\n", encoding="utf-8")
        scratch = Path(self.temp.name) / "scratch"
        line = bt_regress.run_suite(self.worktree, scratch, suite)
        self.assertEqual(line.split()[:2], ["test_durable_x", "125"])
        self.assertIn("lock file out of date", (scratch / "logs" / "test_durable_x.log").read_text(encoding="utf-8"))


class Signals(unittest.TestCase):
    def test_a_suite_does_not_inherit_ignored_job_control_signals(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        worktree = Path(temp.name) / "wt"
        tests = worktree / "skill" / "scripts" / "tests"
        tests.mkdir(parents=True)
        suite = tests / "test_job_signals.py"
        suite.write_text("import signal, unittest\n"
                         "class T(unittest.TestCase):\n"
                         "    def test_default(self):\n"
                         "        for s in (signal.SIGTTIN, signal.SIGTTOU, signal.SIGTSTP):\n"
                         "            self.assertEqual(signal.getsignal(s), signal.SIG_DFL)\n", encoding="utf-8")
        before = {s: signal.signal(s, signal.SIG_IGN) for s in (signal.SIGTTIN, signal.SIGTTOU, signal.SIGTSTP)}
        try:                                       # as when the regression runs from a background shell
            line = bt_regress.run_suite(worktree, Path(temp.name) / "scratch", suite)
        finally:
            for s, handler in before.items():
                signal.signal(s, handler)
        self.assertEqual(line.split()[:2], ["test_job_signals", "0"],
                         (Path(temp.name) / "scratch" / "logs" / "test_job_signals.log").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
