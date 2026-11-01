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
from bt_scheduler_executor import handoff, retention
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
        settled = self.result(True)
        self.assertEqual((settled["action"], settled["reason"]), ("settled", "already_absent"))
        self.assertEqual(retain_run(self.root, apply=True, now=self.now), [])    # indexed: never retried (D-270)

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


class PreservingRetentionTests(RetentionTests):
    """D-270: under `preserve` a checkout is retired once what it holds beyond its snapshot is preserved elsewhere; what
    cannot be preserved is reported and kept. (Inherits the setUp; the parent's tests run again in default mode.)"""

    def run_preserving(self, apply=True, **kw):
        kw.setdefault("archive_max_bytes", 2**20)
        return retain_run(self.root, apply=apply, now=self.now, preserve=True, **kw)

    def test_unknown_ignored_data_is_archived_with_the_evidence_then_removed(self):
        (self.tree / ".env").write_text("PRIVATE_TEST_DATA=true")
        reports = self.tree / "node_modules" / "x.js"
        reports.parent.mkdir()
        reports.write_text("cache")
        dry = self.run_preserving(apply=False)[0]
        self.assertEqual((dry["action"], dry["archive_paths"]), ("eligible", 1))
        self.assertTrue(self.tree.is_dir())
        result = self.run_preserving()[0]
        self.assertEqual(result["action"], "removed")
        self.assertFalse(self.tree.exists())
        archive = self.root / "attempts" / self.dirname / retention.ARCHIVE_NAME
        import tarfile
        with tarfile.open(archive) as tar:
            self.assertEqual(tar.getnames(), [".env"])
            self.assertEqual(tar.extractfile(".env").read(), b"PRIVATE_TEST_DATA=true")
        self.assertEqual(result["archive"], str(archive))
        self.assertNotIn("preserve", result)                     # the snapshot already held the rest

    def test_ignored_data_over_the_cap_is_reported_and_kept(self):
        (self.tree / ".env").write_text("x" * 5000)
        result = self.run_preserving(archive_max_bytes=1000)[0]
        self.assertEqual(result["action"], "skip")
        self.assertTrue(result["reason"].startswith("unpreserved_ignored_data (5000 bytes > 1000"), result["reason"])
        self.assertTrue((self.tree / ".env").is_file())
        result = self.run_preserving(archive_max_bytes=0)[0]      # archiving off: the old rule
        self.assertEqual(result["reason"], "unknown_ignored_data")

    def test_staged_content_becomes_a_retained_commit_before_removal(self):
        (self.tree / "README.md").write_text("new staged content")
        git(self.tree, "add", "README.md")
        (self.tree / "README.md").write_text("captured agent change\n")
        result = self.run_preserving()[0]
        self.assertEqual((result["action"], result["preserve"]), ("removed", ["staged_changes"]))
        ref = retention.retained_ref(self.root.resolve(), self.dirname)
        self.assertEqual(result["retained_ref"], ref)
        self.assertEqual(git(self.repo, "show", f"{ref}^2:README.md"), "new staged content")
        self.assertEqual(git(self.repo, "show", f"{ref}:untracked.txt"), "captured new source")
        self.assertEqual(git(self.repo, "rev-parse", f"{ref}^1"), self.saved["head_sha"])
        self.assertFalse(self.tree.exists())

    def test_staged_content_the_snapshot_already_holds_needs_no_retained_commit(self):
        git(self.tree, "add", "README.md")
        result = self.run_preserving()[0]
        self.assertEqual(result["action"], "removed")
        self.assertNotIn("retained_ref", result)

    def test_edits_after_the_capture_are_kept_in_the_retained_commit(self):
        (self.tree / "new-work.txt").write_text("do not lose me")
        result = self.run_preserving()[0]
        self.assertEqual((result["action"], result["preserve"]), ("removed", ["content_changed_since_capture"]))
        self.assertEqual(git(self.repo, "show", f"{result['retained_ref']}:new-work.txt"), "do not lose me")

    def test_unpreservable_states_still_keep_the_checkout(self):
        git(self.repo, "worktree", "lock", str(self.tree))
        self.assertEqual(self.run_preserving()[0]["reason"], "unregistered_or_locked")
        git(self.repo, "worktree", "unlock", str(self.tree))
        git(self.repo, "update-ref", "-d", self.saved["refs"]["snapshot"])
        self.assertEqual(self.run_preserving()[0]["action"], "skip")
        self.assertTrue(self.tree.is_dir())

    def test_an_absent_checkout_is_settled_once_and_never_inspected_again(self):
        self.assertEqual(self.run_preserving()[0]["action"], "removed")
        settled = self.run_preserving()
        self.assertEqual([(r["action"], r["reason"]) for r in settled], [("settled", "already_absent")])
        index = json.loads((self.root / retention.INDEX_NAME).read_text())
        self.assertEqual(index["absent"], [self.request.attempt_id])
        self.assertEqual(self.run_preserving(), [])
        self.assertEqual(self.run_preserving(apply=False), [])

    def test_the_limit_bounds_removals(self):
        result = self.run_preserving(limit=0)[0]
        self.assertEqual((result["action"], result["reason"]), ("eligible", "limit"))
        self.assertTrue(self.tree.is_dir())

    def orphan(self, *, updated=None, shim=None):
        with sqlite3.connect(self.root / "ledger.db") as db:
            db.execute("ALTER TABLE attempts ADD COLUMN shim")
            db.execute("ALTER TABLE attempts ADD COLUMN updated")
            db.execute("UPDATE attempts SET state='running', ended_at=NULL, handoff=NULL, shim=?, updated=?",
                       (json.dumps(shim) if shim else None, self.now - RETENTION_SECONDS - 5 if updated is None else updated))
        db.close()
        (self.tree / "uncaptured.txt").write_text("work nobody captured")

    def test_an_abandoned_attempt_of_a_superseded_run_is_preserved_then_removed(self):
        self.orphan()
        self.assertEqual(self.run_preserving()[0]["reason"], "attempt_not_terminal")      # the run is not superseded
        result = self.run_preserving(superseded=True)[0]
        self.assertEqual((result["action"], result["preserve"]), ("removed", ["uncaptured"]))
        self.assertEqual(git(self.repo, "show", f"{result['retained_ref']}:uncaptured.txt"), "work nobody captured")
        self.assertFalse(self.tree.exists())

    def test_a_live_or_recent_attempt_of_a_superseded_run_is_kept(self):
        me = {"pid": os.getpid(), "ident": retention.procinfo.start_ident(os.getpid())}
        self.orphan(shim=me)
        self.assertEqual(self.run_preserving(superseded=True)[0]["reason"], "attempt_live")
        self.update("shim", None)
        self.update("updated", self.now - 60)
        self.assertEqual(self.run_preserving(superseded=True)[0]["reason"], "younger_than_three_days")
        self.assertTrue((self.tree / "uncaptured.txt").is_file())

    def test_superseded_runs_are_older_revisions_of_the_same_requirement(self):
        base = self.base / "executor"
        for name in ("p-REQ-1-r1-c1da55c1-1792409909290", "p-REQ-1-r2-dcdf0af4-1792409909290",
                     "p-REQ-2-r7-8e551ac4-1792409909290", "unrelated"):
            (base / name).mkdir(parents=True)
        self.assertEqual(retention.superseded_runs(base), {"p-REQ-1-r1-c1da55c1-1792409909290"})


if __name__ == "__main__":
    unittest.main()
