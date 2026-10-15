"""T4: one isolated worktree + branch per attempt, allocated under a lock, idempotent after a crash, never destructive."""
from __future__ import annotations

import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2])]
import bt_scheduler_executor as ex
from bt_scheduler_executor.workspace import dirname_of
from support import git, make_repo, order


class Workspaces(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.repo = make_repo(self.base / "repo")
        self.ws = ex.GitWorkspaces(self.base / "root", {"main": self.repo})

    def test_an_allocation_creates_a_worktree_on_its_own_branch_at_the_recorded_base(self):
        a = self.ws.allocate(order(1))
        self.assertTrue((Path(a.path) / "README.md").exists())
        self.assertEqual(git(a.path, "rev-parse", "HEAD"), a.base_sha)
        self.assertEqual(git(a.path, "symbolic-ref", "--short", "HEAD"), a.branch)
        self.assertTrue(a.branch.startswith("m3/att-0001-"))
        self.assertNotEqual(Path(a.path), self.repo)

    def test_the_main_checkout_is_not_touched(self):
        before = (git(self.repo, "rev-parse", "HEAD"), git(self.repo, "status", "--porcelain"),
                  git(self.repo, "branch", "--show-current"))
        self.ws.allocate(order(1))
        after = (git(self.repo, "rev-parse", "HEAD"), git(self.repo, "status", "--porcelain"),
                 git(self.repo, "branch", "--show-current"))
        self.assertEqual(before, after)

    def test_the_base_is_pinned_even_if_the_repository_moves_on(self):
        a = self.ws.allocate(order(1))
        (self.repo / "later.txt").write_text("x")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-m", "later")
        b = self.ws.allocate(order(2))
        self.assertNotEqual(a.base_sha, b.base_sha)
        again = self.ws.allocate(order(1))
        self.assertEqual(again.base_sha, a.base_sha)

    def test_allocation_is_idempotent_per_attempt(self):
        a = self.ws.allocate(order(1))
        (Path(a.path) / "work.txt").write_text("agent work")
        b = self.ws.allocate(order(1))
        self.assertEqual((a.path, a.branch, a.base_sha), (b.path, b.branch, b.base_sha))
        self.assertEqual((Path(b.path) / "work.txt").read_text(), "agent work")     # nothing was reset or recreated

    def test_two_attempts_never_share_a_directory_branch_or_index(self):
        a, b = self.ws.allocate(order(1)), self.ws.allocate(order(2))
        self.assertNotEqual(a.path, b.path)
        self.assertNotEqual(a.branch, b.branch)
        (Path(a.path) / "only-a.txt").write_text("a")
        git(a.path, "add", "only-a.txt")
        self.assertEqual(git(b.path, "status", "--porcelain"), "")
        self.assertFalse((Path(b.path) / "only-a.txt").exists())

    def test_parallel_allocations_on_one_repository_all_succeed_and_are_distinct(self):
        results, errors = [], []

        def go(n):
            try:
                results.append(self.ws.allocate(order(n)))
            except Exception as error:
                errors.append(error)
        threads = [threading.Thread(target=go, args=(n,)) for n in range(1, 13)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        self.assertEqual(errors, [])
        self.assertEqual(len({r.path for r in results}), 12)
        self.assertEqual(len({r.branch for r in results}), 12)
        self.assertEqual(git(self.repo, "worktree", "list").count("\n") + 1, 13)

    def test_an_unknown_repository_or_base_is_refused_before_anything_is_created(self):
        with self.assertRaises(ex.ExecutorError) as caught:
            self.ws.allocate(order(1, repo="nope"))
        self.assertEqual(caught.exception.code, "REPOSITORY_UNKNOWN")
        with self.assertRaises(ex.ExecutorError) as caught:
            self.ws.allocate(order(1, base="no-such"))
        self.assertEqual(caught.exception.code, "BASE_UNRESOLVED")
        self.assertFalse((self.base / "root" / "worktrees").exists() and list((self.base / "root" / "worktrees").iterdir()))

    def test_a_directory_that_is_not_a_repository_is_unknown(self):
        plain = self.base / "plain"
        plain.mkdir()
        ws = ex.GitWorkspaces(self.base / "r2", {"main": plain})
        with self.assertRaises(ex.ExecutorError) as caught:
            ws.check(order(1))
        self.assertEqual(caught.exception.code, "REPOSITORY_UNKNOWN")

    def test_the_repository_may_be_resolved_by_a_function(self):
        ws = ex.GitWorkspaces(self.base / "r3", lambda role: self.repo if role == "main" else None)
        ws.check(order(1))
        with self.assertRaises(ex.ExecutorError):
            ws.check(order(1, repo="other"))

    def test_a_crash_after_the_manifest_but_before_git_leaves_a_record_and_is_recovered(self):
        # simulate: manifest written, git never ran
        a = self.ws.allocate(order(1))
        git(self.repo, "worktree", "remove", "--force", a.path)
        git(self.repo, "branch", "-D", a.branch)
        again = self.ws.allocate(order(1))                                   # manifest exists -> same base, rebuilt
        self.assertEqual(again.base_sha, a.base_sha)
        self.assertTrue(Path(again.path).is_dir())

    def test_a_crash_after_git_created_the_branch_but_the_directory_is_gone_reuses_the_branch(self):
        a = self.ws.allocate(order(1))
        git(self.repo, "worktree", "remove", "--force", a.path)               # branch survives
        again = self.ws.allocate(order(1))
        self.assertEqual(git(again.path, "symbolic-ref", "--short", "HEAD"), a.branch)

    def test_an_existing_directory_that_is_not_our_worktree_is_never_overwritten(self):
        name = dirname_of("att-0001")
        target = self.base / "root" / "worktrees" / name
        target.mkdir(parents=True)
        (target / "precious.txt").write_text("keep")
        with self.assertRaises(ex.ExecutorError) as caught:
            self.ws.allocate(order(1))
        self.assertEqual(caught.exception.code, "WORKSPACE_ERROR")
        self.assertEqual((target / "precious.txt").read_text(), "keep")

    def test_a_manifest_of_another_attempt_is_refused(self):
        a = self.ws.allocate(order(1))
        manifest = Path(self.base / "root" / "worktrees" / f"{dirname_of('att-0001')}.json")
        text = manifest.read_text().replace("att-0001", "att-9999")
        manifest.write_text(text)
        with self.assertRaises(ex.ExecutorError):
            self.ws.allocate(order(1))
        self.assertTrue(Path(a.path).is_dir())

    def test_repository_hooks_do_not_run(self):
        hook = self.repo / ".git" / "hooks" / "post-checkout"
        hook.write_text(f"#!/bin/sh\ntouch {self.base}/HOOK-RAN\n")
        hook.chmod(0o755)
        self.ws.allocate(order(1))
        self.assertFalse((self.base / "HOOK-RAN").exists())

    def test_the_journal_records_each_stage_durably(self):
        self.ws.allocate(order(1))
        rows = [line for line in (self.base / "root" / "journal.jsonl").read_text().splitlines()]
        self.assertEqual([__import__("json").loads(r)["stage"] for r in rows], ["allocating", "allocated"])

    def test_dirnames_are_unique_and_safe_for_hostile_ids(self):
        names = {dirname_of(x) for x in ("a/b", "a-b", "a b", "../x", "a\u0000b".replace("\u0000", "_"), "x" * 500)}
        self.assertEqual(len(names), 6)
        for name in names:
            self.assertNotIn("/", name)
            self.assertFalse(name.startswith("."))
            self.assertLessEqual(len(name), 80)

    def test_release_removes_the_checkout_and_branch_but_not_the_handoff_refs(self):
        a = self.ws.allocate(order(1))
        git(self.repo, "update-ref", "refs/m3/handoff/x", a.base_sha)
        self.ws.release(a)
        self.assertFalse(Path(a.path).exists())
        self.assertEqual(git(self.repo, "branch", "--list", a.branch), "")
        self.assertTrue(git(self.repo, "rev-parse", "refs/m3/handoff/x"))


if __name__ == "__main__":
    unittest.main()
