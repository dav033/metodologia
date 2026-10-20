"""The bitácora pull never leaves work in a stash: a slow fetch is abandoned, the rebase is never killed, and code with
uncommitted changes outside the bitácora is not rebased under running processes."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bt_vcs


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


class Pull(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.origin, self.here, self.other = base / "origin.git", base / "here", base / "other"
        git(base, "init", "-q", "--bare", "-b", "main", str(self.origin))
        for clone in (self.here, self.other):
            git(base, "clone", "-q", str(self.origin), str(clone))
            git(clone, "config", "user.email", "t@t"), git(clone, "config", "user.name", "t")
        for folder in ("bitacora", "skill"):
            (self.here / folder).mkdir()
            (self.here / folder / "a.txt").write_text("1\n")
        git(self.here, "add", "-A"), git(self.here, "commit", "-qm", "init"), git(self.here, "push", "-q", "-u", "origin", "main")
        git(self.other, "pull", "-q", "origin", "main")
        (self.other / "bitacora" / "b.txt").write_text("from the other machine\n")
        git(self.other, "add", "-A"), git(self.other, "commit", "-qm", "other"), git(self.other, "push", "-q", "origin", "main")
        self.root = self.here / "bitacora"

    def test_changes_of_other_machines_arrive_with_local_bitacora_work_kept(self):
        (self.root / "a.txt").write_text("local log\n")
        self.assertEqual(bt_vcs.pull(self.root), "")
        self.assertTrue((self.root / "b.txt").exists())
        self.assertEqual((self.root / "a.txt").read_text(), "local log\n")
        self.assertEqual(git(self.here, "stash", "list"), "")

    def test_uncommitted_code_outside_the_bitacora_is_left_alone(self):
        (self.here / "skill" / "a.txt").write_text("work in progress\n")
        warning = bt_vcs.pull(self.root)
        self.assertIn("skill/a.txt", warning)
        self.assertEqual((self.here / "skill" / "a.txt").read_text(), "work in progress\n")
        self.assertFalse((self.root / "b.txt").exists())
        self.assertEqual(git(self.here, "stash", "list"), "")

    def test_a_fetch_that_times_out_changes_nothing(self):
        (self.here / "skill" / "a.txt").write_text("work in progress\n")
        real = bt_vcs._run
        bt_vcs._run = lambda root, *args, timeout=20: None if args[0] == "fetch" else real(root, *args, timeout=timeout)
        try:
            self.assertEqual(bt_vcs.pull(self.root), "")
        finally:
            bt_vcs._run = real
        self.assertEqual((self.here / "skill" / "a.txt").read_text(), "work in progress\n")
        self.assertEqual(git(self.here, "stash", "list"), "")


if __name__ == "__main__":
    unittest.main()
