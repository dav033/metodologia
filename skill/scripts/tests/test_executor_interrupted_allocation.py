"""An allocation killed mid-checkout is rebuilt, not reused half empty (pictures REQ-021 r35 T3.15 a201, 2026-11-01:
the engine restarted during `git worktree add`; the retry found the directory registered and handed an auditor a tree
whose every tracked file was a staged deletion)."""
import subprocess
import tempfile
import unittest
from pathlib import Path

import bt_scheduler_executor as m3
from bt_scheduler_executor.workspace import GitWorkspaces


def git(cwd, *args):
    return subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *args], cwd=cwd, check=True,
                          capture_output=True, text=True).stdout.strip()


class InterruptedAllocation(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name) / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q", "-b", "main")
        for name in ("a.txt", "b.txt"):
            (self.repo / name).write_text(name)
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "base")
        self.spaces = GitWorkspaces(Path(tmp.name) / "root", {"r": self.repo})
        self.request = m3.StartRequest("k", "P", 1, "T", "att-1", 1, "x", "r", "", "main")

    def test_a_killed_checkout_is_rebuilt_before_the_agent_starts(self):
        first = self.spaces.allocate(self.request)
        tree = Path(first.path)
        # what the SIGKILL left: «allocating» without «allocated», registered directory, empty index, no files
        lines = (self.spaces.root / "journal.jsonl").read_text().splitlines()
        (self.spaces.root / "journal.jsonl").write_text("\n".join(l for l in lines if '"allocated"' not in l) + "\n")
        git(tree, "read-tree", "--empty")
        for name in ("a.txt", "b.txt"):
            (tree / name).unlink()
        self.assertTrue(git(tree, "status", "--short").startswith("D "))
        again = self.spaces.allocate(self.request)
        self.assertEqual(again.path, first.path)
        self.assertEqual(git(tree, "status", "--short"), "")
        self.assertTrue((tree / "a.txt").is_file() and (tree / "b.txt").is_file())

    def test_a_finished_allocation_is_reused_untouched(self):
        first = self.spaces.allocate(self.request)
        (Path(first.path) / "a.txt").write_text("the agent's work")
        self.spaces.allocate(self.request)
        self.assertEqual((Path(first.path) / "a.txt").read_text(), "the agent's work")


if __name__ == "__main__":
    unittest.main()
