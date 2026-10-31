"""bt_regress creates the worktree's uv venv once when a suite needs it (an integration's worktree is a fresh checkout),
and every suite starts with the job-control signals at their default (D-227, D-229)."""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path
from unittest.mock import patch

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


class TmuxSocket(unittest.TestCase):
    def test_a_suite_never_reaches_the_live_tmux_socket(self):
        """D-252: a suite that half-mocks bt_agent_terminal (exists patched, tmux real) reached `-L bitacora`, where the
        owner's live Planner runs, and could have typed into or killed it."""
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        worktree = Path(temp.name) / "wt"
        tests = worktree / "skill" / "scripts" / "tests"
        tests.mkdir(parents=True)
        suite = tests / "test_job_socket.py"
        suite.write_text("import os, unittest\n"
                         "class T(unittest.TestCase):\n"
                         "    def test_own_socket(self):\n"
                         "        sock = os.environ.get('BITACORA_TMUX_SOCKET', '')\n"
                         "        self.assertTrue(sock.startswith('btr-') and 'test_job_socket' in sock, sock)\n",
                         encoding="utf-8")
        with patch.dict(os.environ, {"BITACORA_TMUX_SOCKET": "bitacora"}):
            line = bt_regress.run_suite(worktree, Path(temp.name) / "scratch", suite)
        self.assertEqual(line.split()[:2], ["test_job_socket", "0"],
                         (Path(temp.name) / "scratch" / "logs" / "test_job_socket.log").read_text(encoding="utf-8"))


class FastTemp(unittest.TestCase):
    """The suites' temporary files go to a tmpfs with room, and leave with the suite (D-250)."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.worktree = Path(self.temp.name) / "wt"
        self.tests = self.worktree / "skill" / "scripts" / "tests"
        self.tests.mkdir(parents=True)
        self.base = Path(self.temp.name) / "ram"
        self.base.mkdir()

    def run_probe(self, env):
        suite = self.tests / "test_probe.py"
        suite.write_text("import os, tempfile, unittest\n"
                         "class P(unittest.TestCase):\n"
                         "    def test_tmp(self):\n"
                         "        print('TMP=' + tempfile.gettempdir())\n"
                         "        open(os.path.join(tempfile.gettempdir(), 'left-behind'), 'w').close()\n",
                         encoding="utf-8")
        scratch = Path(self.temp.name) / "scratch"
        with unittest.mock.patch.dict(bt_regress.os.environ, env):
            line = bt_regress.run_suite(self.worktree, scratch, suite)
        log = (scratch / "logs" / "test_probe.log").read_text(encoding="utf-8")
        return line, log

    def test_suites_get_a_private_temp_dir_on_the_fast_base_removed_after_them(self):
        line, log = self.run_probe({"BT_REGRESS_TMPDIR": str(self.base)})
        self.assertEqual(line.split()[1], "0", log)
        used = next(row[4:] for row in log.splitlines() if row.startswith("TMP="))
        self.assertEqual(Path(used).parent, self.base)
        self.assertTrue(Path(used).name.startswith("bt-regress-test_probe-"))
        self.assertEqual(list(self.base.iterdir()), [])

    def test_an_empty_override_keeps_the_inherited_temp_dir(self):
        inherited = Path(self.temp.name) / "inherited"
        inherited.mkdir()
        line, log = self.run_probe({"BT_REGRESS_TMPDIR": "", "TMPDIR": str(inherited)})
        self.assertIn(f"TMP={inherited}", log)

    def test_only_a_tmpfs_with_room_is_chosen(self):
        with unittest.mock.patch.dict(bt_regress.os.environ, {}, clear=False):
            bt_regress.os.environ.pop("BT_REGRESS_TMPDIR", None)
            with unittest.mock.patch.object(bt_regress, "_tmpfs", return_value=False):
                self.assertIsNone(bt_regress.fast_tmp())
            with unittest.mock.patch.object(bt_regress, "_tmpfs", return_value=True), \
                    unittest.mock.patch.object(bt_regress, "FAST_TMP_MIN_FREE", 1 << 62):
                self.assertIsNone(bt_regress.fast_tmp())
            with unittest.mock.patch.object(bt_regress, "_tmpfs", side_effect=lambda p: p == "/tmp"):
                self.assertEqual(bt_regress.fast_tmp(), "/tmp")


if __name__ == "__main__":
    unittest.main()
