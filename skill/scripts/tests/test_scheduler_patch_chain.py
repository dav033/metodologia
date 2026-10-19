"""Patch transfer gates without creating commits or invoking live agents."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock, patch

from bt_scheduler_executor.errors import ExecutorError
from bt_scheduler_executor.model import StartRequest, Workspace
from bt_scheduler_patch_chain import PatchChainReceipt, PatchChainWorkspaces

BASE = "a" * 40
TREE = "b" * 40


class PatchChainTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.worktree = self.root / "worktree"
        self.worktree.mkdir()
        self.ws = Workspace(str(self.worktree), "branch", BASE, str(self.root))
        self.request = StartRequest("key", "plan", 1, "T2", "attempt2", 1, "route", "repo", base_ref=BASE)
        self.delegate = Mock()
        self.delegate.check.return_value = BASE
        self.delegate.repository.return_value = self.root
        self.delegate.allocate.return_value = self.ws
        self.patch_path = self.root / "changes.patch"
        self.patch_path.write_bytes(b"diff --git a/x b/x\n")
        self.manifest_path = self.root / "manifest.json"
        self.manifest = {
            "schema": 2, "handoff_mode": "patch", "status": "captured", "base_sha": BASE,
            "head_sha": BASE, "has_commits": False, "attempt_id": "attempt1",
            "patch_bytes": self.patch_path.stat().st_size,
            "patch_sha256": hashlib.sha256(self.patch_path.read_bytes()).hexdigest(),
        }
        self.manifest["patch"] = {"path": str(self.patch_path), "bytes": self.manifest["patch_bytes"],
                                  "sha256": self.manifest["patch_sha256"]}
        self.rebind()
        self.git = patch("bt_scheduler_patch_chain.gitutil.run", side_effect=self.git_result).start()
        self.addCleanup(patch.stopall)

    def rebind(self):
        self.manifest_path.write_text(json.dumps(self.manifest))
        self.receipt = PatchChainReceipt(BASE, TREE, ("attempt1",), str(self.manifest_path),
                                         hashlib.sha256(self.manifest_path.read_bytes()).hexdigest())
        self.manager = PatchChainWorkspaces(self.delegate, lambda _: self.receipt,
                                            self.root / "receipts", lambda _: ("attempt1",))

    def git_result(self, cwd, args, **kwargs):
        if args == ["rev-parse", "HEAD"]:
            return BASE
        if args[0] == "write-tree" or args == ["rev-parse", f"{BASE}^{{tree}}"]:
            return TREE
        return ""

    def test_success_and_idempotent_pre_spawn_reallocation(self):
        self.assertEqual(self.manager.allocate(self.request), self.ws)
        calls = len([c for c in self.git.call_args_list if c.args[1][0] == "apply"])
        self.assertEqual(calls, 2)
        self.assertEqual(self.manager.allocate(self.request), self.ws)
        self.assertEqual(len([c for c in self.git.call_args_list if c.args[1][0] == "apply"]), 2)

    def test_refuses_missing_ancestor_before_allocation(self):
        self.receipt = replace(self.receipt, lineage=())
        with self.assertRaisesRegex(ExecutorError, "lineage"):
            self.manager.allocate(self.request)
        self.delegate.allocate.assert_not_called()

    def test_refuses_changed_manifest(self):
        self.manifest_path.write_text("{}")
        with self.assertRaisesRegex(ExecutorError, "manifest digest"):
            self.manager.check(self.request)

    def test_refuses_changed_patch(self):
        self.patch_path.write_bytes(b"corrupted")
        with self.assertRaisesRegex(ExecutorError, "size or digest"):
            self.manager.check(self.request)

    def test_refuses_wrong_base_or_unpinned_ref(self):
        with self.assertRaisesRegex(ExecutorError, "exact pinned"):
            self.manager.check(replace(self.request, base_ref="HEAD"))

    def test_refuses_modified_allocated_workspace(self):
        self.manager.allocate(self.request)
        self.git.side_effect = lambda cwd, args, **kw: "c" * 40 if args[0] == "write-tree" else self.git_result(cwd, args, **kw)
        with self.assertRaisesRegex(ExecutorError, "edited"):
            self.manager.allocate(self.request)

    def test_wrong_tree_leaves_preparing_record_and_restart_fails_closed(self):
        self.receipt = replace(self.receipt, target_tree="c" * 40)
        with self.assertRaisesRegex(ExecutorError, "trusted receipt"):
            self.manager.allocate(self.request)
        with self.assertRaisesRegex(ExecutorError, "interrupted"):
            self.manager.allocate(self.request)

    def test_empty_materialization_uses_cached_index_and_never_apply_to_worktree(self):
        self.manager.materialize_empty = True
        self.manager.allocate(self.request)
        applications = [c for c in self.git.call_args_list if c.args[1][0] == "apply"]
        self.assertTrue(all("--cached" in c.args[1] for c in applications))
        self.assertTrue(all(c.kwargs.get("env", {}).get("GIT_INDEX_FILE") for c in applications))
        self.assertTrue(any(c.args[1] == ["checkout-index", "--all"] for c in self.git.call_args_list))

    def test_empty_materialization_refuses_nonempty_worktree(self):
        (self.worktree / "existing").write_text("preserve")
        self.manager.materialize_empty = True
        with self.assertRaisesRegex(ExecutorError, "empty no-checkout"):
            self.manager.allocate(self.request)
        self.assertEqual((self.worktree / "existing").read_text(), "preserve")

    def test_root_baseline_and_release_keep_evidence(self):
        self.receipt = PatchChainReceipt(BASE, TREE)
        self.manager.expected_lineage = lambda _: ()
        self.manager.allocate(self.request)
        self.manager.release(self.ws)
        self.delegate.release.assert_not_called()


if __name__ == "__main__":
    unittest.main()
