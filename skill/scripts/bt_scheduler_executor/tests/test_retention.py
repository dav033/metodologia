"""Three-day worktree retention: exercise real Git snapshots and destructive boundaries."""
from __future__ import annotations

import fcntl
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2])]
from bt_scheduler_executor import handoff
from bt_scheduler_executor.retention import RETENTION_SECONDS, retain_run
from bt_scheduler_executor.workspace import GitWorkspaces, dirname_of
from support import git, make_repo, order


class RetentionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.repo = make_repo(self.base / "repo")
        (self.repo / ".gitignore").write_text("node_modules/\n.next/\n.env\n")
        git(self.repo, "add", ".gitignore")
        git(self.repo, "commit", "-qm", "ignore generated files")
        self.root = self.base / "run"
        self.manager = GitWorkspaces(self.root / "ws", {"main": self.repo})
        self.request = order(1)
        self.workspace = self.manager.allocate(self.request)
        self.tree = Path(self.workspace.path)
        (self.tree / "README.md").write_text("captured agent change\n")
        (self.tree / "untracked.txt").write_text("captured new source\n")
        self.dirname = dirname_of(self.request.attempt_id)
        self.saved = handoff.capture(
            self.workspace, self.root / "attempts" / self.dirname,
            dirname=self.dirname, attempt_id=self.request.attempt_id,
            when=time.time() - RETENTION_SECONDS - 60, patch_max=2**20,
        )
        self.now = time.time()
        (self.root / "executor.lock").touch()
        with sqlite3.connect(self.root / "ledger.db") as db:
            db.execute("CREATE TABLE attempts(attempt_id, dirname, state, ended_at, workspace, handoff)")
            db.execute("INSERT INTO attempts VALUES (?,?,?,?,?,?)", (
                self.request.attempt_id, self.dirname, "finished", self.now - RETENTION_SECONDS - 1,
                json.dumps(asdict(self.workspace)), json.dumps(self.saved),
            ))
        db.close()

    def update(self, field, value):
        with sqlite3.connect(self.root / "ledger.db") as db:
            db.execute(f"UPDATE attempts SET {field}=?", (value,))
        db.close()

    def result(self, apply=False):
        return retain_run(self.root, apply=apply, now=self.now)[0]

    def test_dry_run_keeps_dirty_captured_worktree_and_real_index(self):
        index = git(self.tree, "diff", "--cached")
        self.assertEqual(self.result()["action"], "eligible")
        self.assertTrue(self.tree.is_dir())
        self.assertEqual(git(self.tree, "diff", "--cached"), index)
        self.assertFalse((self.root / "retention.jsonl").exists())

    def test_remove_preserves_snapshot_branch_manifest_and_ledger(self):
        generated = self.tree / "node_modules"
        generated.mkdir()
        (generated / "generated.js").write_text("dependency")
        self.assertEqual(self.result(True)["action"], "removed")
        self.assertFalse(self.tree.exists())
        self.assertTrue(self.tree.with_suffix(".json").exists())
        self.assertTrue((self.root / "ledger.db").is_file())
        self.assertEqual(git(self.repo, "show", self.saved["refs"]["snapshot"] + ":untracked.txt"), "captured new source")
        self.assertEqual(git(self.repo, "rev-parse", self.workspace.branch), self.saved["head_sha"])
        self.assertEqual(self.result(True)["reason"], "already_absent")

    def test_newer_than_three_days_is_preserved(self):
        self.update("ended_at", self.now - RETENTION_SECONDS + 1)
        self.assertEqual(self.result(True)["reason"], "younger_than_three_days")
        self.assertTrue(self.tree.is_dir())

    def test_live_attempt_is_preserved_even_if_old(self):
        self.update("state", "running")
        self.assertEqual(self.result(True)["reason"], "attempt_not_terminal")

    def test_live_executor_lock_prevents_cleanup(self):
        with (self.root / "executor.lock").open("r+") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertEqual(self.result(True)["reason"], "executor_busy")

    def test_new_source_changes_are_preserved(self):
        (self.tree / "new-work.txt").write_text("do not lose me")
        self.assertEqual(self.result(True)["reason"], "content_changed_since_capture")
        self.assertTrue((self.tree / "new-work.txt").is_file())

    def test_modified_captured_source_is_preserved(self):
        (self.tree / "README.md").write_text("later owner edits")
        self.assertEqual(self.result(True)["reason"], "content_changed_since_capture")

    def test_staged_only_new_content_is_preserved(self):
        (self.tree / "README.md").write_text("new staged content")
        git(self.tree, "add", "README.md")
        (self.tree / "README.md").write_text("captured agent change\n")
        self.assertEqual(self.result(True)["reason"], "staged_changes_preserved")
        self.assertEqual(git(self.tree, "show", ":README.md"), "new staged content")

    def test_submodules_are_never_removed(self):
        head = git(self.repo, "rev-parse", "HEAD")
        git(self.tree, "update-index", "--add", "--cacheinfo", f"160000,{head},nested")
        git(self.tree, "commit", "-qm", "add gitlink")
        self.saved["head_sha"] = git(self.tree, "rev-parse", "HEAD")
        self.update("handoff", json.dumps(self.saved))
        self.assertEqual(self.result(True)["reason"], "submodules_preserved")
        self.assertTrue(self.tree.exists())

    def test_malformed_refs_is_local_skip(self):
        self.saved["refs"] = None
        self.update("handoff", json.dumps(self.saved))
        self.assertEqual(self.result(True)["reason"], "invalid_snapshot_ref")

    def test_non_dumpable_process_cwd_is_preserved(self):
        child = subprocess.Popen(
            [sys.executable, "-c", "import ctypes,time; ctypes.CDLL(None).prctl(4,0); print('ready',flush=True); time.sleep(20)"],
            cwd=self.tree, stdout=subprocess.PIPE, text=True,
        )
        try:
            self.assertEqual(child.stdout.readline().strip(), "ready")
            self.assertEqual(self.result(True)["reason"], "process_using_worktree")
        finally:
            child.terminate()
            child.wait(timeout=3)
            child.stdout.close()

    def test_unknown_ignored_data_is_preserved(self):
        (self.tree / ".env").write_text("PRIVATE_TEST_DATA=true")
        self.assertEqual(self.result(True)["reason"], "unknown_ignored_data")
        self.assertTrue((self.tree / ".env").exists())

    def test_snapshot_ref_must_still_preserve_exact_commit(self):
        git(self.repo, "update-ref", "-d", self.saved["refs"]["snapshot"])
        self.assertEqual(self.result(True)["action"], "skip")
        self.assertTrue(self.tree.is_dir())

    def test_symlinked_checkout_is_preserved(self):
        parked = self.tree.with_name("parked")
        self.tree.rename(parked)
        self.tree.symlink_to(parked, target_is_directory=True)
        self.assertEqual(self.result(True)["reason"], "unmanaged_or_symlinked_worktree")
        self.assertTrue((parked / "README.md").is_file())

    def test_directory_traversal_is_rejected(self):
        self.update("dirname", "../../outside")
        self.assertEqual(self.result(True)["reason"], "invalid_directory_name")

    def test_active_process_cwd_is_preserved(self):
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(20)"], cwd=self.tree)
        try:
            self.assertEqual(self.result(True)["reason"], "process_using_worktree")
        finally:
            child.terminate()
            child.wait(timeout=3)

    def test_cleanup_process_cannot_remove_its_own_cwd(self):
        previous = Path.cwd()
        try:
            os.chdir(self.tree)
            self.assertEqual(self.result(True)["reason"], "process_using_worktree")
        finally:
            os.chdir(previous)

    def test_git_locked_worktree_is_preserved(self):
        git(self.repo, "worktree", "lock", str(self.tree))
        self.assertEqual(self.result(True)["reason"], "unregistered_or_locked")

    def test_missing_handoff_never_removes_checkout(self):
        self.update("handoff", "null")
        self.assertEqual(self.result(True)["reason"], "invalid_workspace_or_handoff")

    def test_process_check_failure_is_not_treated_as_unused(self):
        with patch("bt_scheduler_executor.retention._in_use", side_effect=PermissionError("cannot inspect")):
            self.assertEqual(self.result(True)["action"], "skip")
        self.assertTrue(self.tree.is_dir())

    def test_process_probe_timeout_preserves_checkout(self):
        with patch("bt_scheduler_executor.retention._in_use", side_effect=subprocess.TimeoutExpired("readlink", 3)):
            result = self.result(True)
        self.assertEqual(result["action"], "skip")
        self.assertIn("timed out", result["reason"])
        self.assertTrue(self.tree.is_dir())


if __name__ == "__main__":
    unittest.main()
