"""T5: the work is preserved with or without commits, without touching the branch, the index or the base."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2])]
import bt_scheduler_executor as ex
from bt_scheduler_executor import handoff
from support import git, make_repo, order


class Handoff(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.repo = make_repo(self.base / "repo")
        self.gw = ex.GitWorkspaces(self.base / "root", {"main": self.repo})
        self.ws = self.gw.allocate(order(1))
        self.wt = Path(self.ws.path)
        self.out = self.base / "attempt"
        self.dirname = Path(self.ws.path).name

    def commit(self, name="c.txt", text="c\n"):
        (self.wt / name).write_text(text)
        git(self.wt, "add", "-A")
        git(self.wt, "commit", "-m", f"commit {name}")

    def capture(self, **kw):
        return handoff.capture(self.ws, self.out, dirname=self.dirname, attempt_id="att-0001", when=1_800_000_000,
                               patch_max=kw.pop("patch_max", 1 << 20), **kw)

    def test_patch_mode_reapplies_dirty_binary_and_deletion_without_mutating_git_state(self):
        (self.wt / "README.md").unlink()
        (self.wt / "src.txt").write_text("staged then edited\n")
        binary = bytes(range(256)) * 11
        (self.wt / "new blob.bin").write_bytes(binary)
        git(self.wt, "add", "src.txt")
        (self.wt / "src.txt").write_text("final working tree\n")
        before = self.state()
        refs = git(self.repo, "for-each-ref", "--format=%(refname) %(objectname)")
        real_run = handoff.gitutil.run

        def forbid_git_mutation(cwd, args, **kwargs):
            if args and args[0] in ("commit-tree", "update-ref"):
                self.fail(f"patch capture invoked forbidden git command: {args[0]}")
            return real_run(cwd, args, **kwargs)

        with mock.patch.object(handoff.gitutil, "run", side_effect=forbid_git_mutation):
            manifest = self.capture(mode="patch")
        self.assertIsNone(manifest["snapshot_sha"])
        self.assertEqual(manifest["refs"], {})
        self.assertEqual(manifest["handoff_mode"], "patch")
        self.assertEqual(manifest["schema"], 2)
        self.assertEqual(self.state(), before)
        self.assertEqual(git(self.repo, "for-each-ref", "--format=%(refname) %(objectname)"), refs)
        fresh = self.base / "patch-restore"
        git(self.repo, "worktree", "add", "--detach", str(fresh), self.ws.base_sha)
        git(fresh, "apply", "--binary", manifest["patch"]["path"])
        self.assertFalse((fresh / "README.md").exists())
        self.assertEqual((fresh / "src.txt").read_text(), "final working tree\n")
        self.assertEqual((fresh / "new blob.bin").read_bytes(), binary)
        raw = Path(manifest["patch"]["path"]).read_bytes()
        self.assertEqual(manifest["patch_bytes"], len(raw))
        self.assertEqual(manifest["patch_sha256"], hashlib.sha256(raw).hexdigest())

    def test_patch_mode_empty_state_has_an_applicable_empty_artifact(self):
        manifest = self.capture(mode="patch")
        self.assertTrue(manifest["empty"])
        self.assertEqual(manifest["schema"], 2)
        self.assertIsNone(manifest["snapshot_sha"])
        self.assertEqual(manifest["refs"], {})
        self.assertEqual(Path(manifest["patch"]["path"]).read_bytes(), b"")
        self.assertEqual(manifest["patch_bytes"], 0)

    def test_patch_mode_preserves_committed_files_that_are_now_ignored(self):
        (self.wt / ".gitignore").write_text("ignored.bin\n")
        content = bytes(range(256))
        (self.wt / "ignored.bin").write_bytes(content)
        git(self.wt, "add", ".gitignore")
        git(self.wt, "add", "-f", "ignored.bin")
        git(self.wt, "commit", "-m", "force-add ignored binary")
        manifest = self.capture(mode="patch")
        fresh = self.base / "ignored-restore"
        git(self.repo, "worktree", "add", "--detach", str(fresh), self.ws.base_sha)
        git(fresh, "apply", "--binary", manifest["patch"]["path"])
        self.assertEqual((fresh / "ignored.bin").read_bytes(), content)
        self.assertIn("A\tignored.bin", manifest["changed"])

    def test_patch_mode_cap_overflow_fails_with_failure_manifest_and_no_stale_patch(self):
        (self.wt / "large.txt").write_text("x" * 4096)
        with self.assertRaises(ex.ExecutorError) as caught:
            self.capture(mode="patch", patch_max=100)
        self.assertEqual(caught.exception.code, "ARTIFACT_ERROR")
        manifest = json.loads((self.out / "handoff" / "manifest.json").read_text())
        self.assertEqual((manifest["status"], manifest["error"], manifest["snapshot_sha"]),
                         ("failed", "PATCH_TOO_LARGE", None))
        self.assertFalse((self.out / "handoff" / "changes.patch").exists())

    def test_patch_mode_overflow_keeps_prior_patch_without_advertising_it_as_current(self):
        (self.wt / "small.txt").write_text("small\n")
        first = self.capture(mode="patch")
        prior_patch = Path(first["patch"]["path"]).read_bytes()
        (self.wt / "large.txt").write_text("x" * 4096)
        with self.assertRaises(ex.ExecutorError):
            self.capture(mode="patch", patch_max=100)
        self.assertEqual(Path(first["patch"]["path"]).read_bytes(), prior_patch)
        failure = json.loads((self.out / "handoff" / "manifest.json").read_text())
        self.assertEqual(failure["status"], "failed")
        self.assertIsNone(failure["patch"]["path"])

    def test_patch_continuation_brief_does_not_claim_snapshot_refs_or_diff(self):
        (self.wt / "w.txt").write_text("w\n")
        manifest = self.capture(mode="patch")
        text = handoff.write_brief(self.out, attempt_id="a", task_id="T1", title="t", outcome="failed",
                                   cause="lost", manifest=manifest).read_text()
        self.assertIn("apply `", text)
        self.assertIn("automatic predecessor integration cannot use", text)
        self.assertNotIn("None", text)
        self.assertNotIn("refs/m3/handoff", text)

    def state(self):
        return {"head": git(self.wt, "rev-parse", "HEAD"), "branch": git(self.wt, "rev-parse", self.ws.branch),
                "index": git(self.wt, "ls-files", "-s"), "status": git(self.wt, "status", "--porcelain"),
                "base_branch": git(self.repo, "rev-parse", "main")}

    def rebuild_from_patch(self, manifest):
        fresh = self.base / "fresh"
        git(self.repo, "worktree", "add", "--detach", str(fresh), self.ws.base_sha)
        git(fresh, "apply", "--binary", manifest["patch"]["path"])
        git(fresh, "add", "-A")
        return git(fresh, "write-tree")

    def test_commits_only(self):
        self.commit()
        m = self.capture()
        self.assertTrue(m["has_commits"] and not m["dirty"] and not m["empty"])
        self.assertEqual((m["commit_count"], m["head_sha"], m["snapshot_sha"]), (1, git(self.wt, "rev-parse", "HEAD"),) * 1 + (git(self.wt, "rev-parse", "HEAD"),))
        self.assertEqual(m["changed"], ["A\tc.txt"])

    def test_dirty_tree_only_modified_tracked_plus_untracked(self):
        (self.wt / "README.md").write_text("edited\n")
        (self.wt / "new.txt").write_text("new\n")
        m = self.capture()
        self.assertFalse(m["has_commits"])
        self.assertTrue(m["dirty"])
        self.assertEqual(m["untracked_count"], 1)
        self.assertEqual(m["head_sha"], self.ws.base_sha)
        self.assertNotEqual(m["snapshot_sha"], m["head_sha"])
        self.assertEqual(git(self.repo, "show", f"{m['snapshot_sha']}:new.txt"), "new")
        self.assertEqual(git(self.repo, "show", f"{m['snapshot_sha']}:README.md"), "edited")
        self.assertEqual(sorted(m["changed"]), ["A\tnew.txt", "M\tREADME.md"])

    def test_commits_and_uncommitted_work_together(self):
        self.commit()
        (self.wt / "more.txt").write_text("more\n")
        (self.wt / "c.txt").write_text("c changed again\n")
        m = self.capture()
        self.assertTrue(m["has_commits"] and m["dirty"])
        self.assertEqual(git(self.repo, "rev-parse", f"{m['snapshot_sha']}^"), m["head_sha"])
        self.assertEqual(git(self.repo, "show", f"{m['snapshot_sha']}:c.txt"), "c changed again")

    def test_an_attempt_that_changed_nothing_is_reported_empty_not_missing(self):
        m = self.capture()
        self.assertTrue(m["empty"])
        self.assertEqual(m["snapshot_sha"], self.ws.base_sha)
        self.assertIsNone(m["patch"]["path"])
        self.assertEqual(m["changed_total"], 0)
        self.assertTrue((self.out / "handoff" / "manifest.json").exists())

    def test_deletions_binary_files_and_spaces_in_names(self):
        (self.wt / "README.md").unlink()
        (self.wt / "with space.txt").write_text("x\n")
        (self.wt / "blob.bin").write_bytes(bytes(range(256)) * 8)
        (self.wt / "ünï.txt").write_text("unicode\n")
        m = self.capture()
        tree = self.rebuild_from_patch(m)
        self.assertEqual(tree, git(self.repo, "rev-parse", f"{m['snapshot_sha']}^{{tree}}"))   # the patch reproduces the work
        self.assertEqual(git(self.repo, "cat-file", "-s", f"{m['snapshot_sha']}:blob.bin"), "2048")

    def test_the_branch_the_index_the_base_and_the_worktree_are_untouched(self):
        self.commit()
        (self.wt / "README.md").write_text("dirty\n")
        (self.wt / "u.txt").write_text("u\n")
        git(self.wt, "add", "README.md")                     # partially staged on purpose
        before = self.state()
        listing = sorted(p.name for p in self.wt.iterdir())
        self.capture()
        self.assertEqual(self.state(), before)
        self.assertEqual(sorted(p.name for p in self.wt.iterdir()), listing)
        self.assertEqual((self.wt / "README.md").read_text(), "dirty\n")

    def test_ignored_files_are_not_swept_into_the_snapshot(self):
        (self.wt / ".gitignore").write_text("*.log\nnode_modules/\n")
        (self.wt / "debug.log").write_text("noise")
        (self.wt / "node_modules").mkdir()
        (self.wt / "node_modules" / "big.js").write_text("x" * 1000)
        m = self.capture()
        files = git(self.repo, "ls-tree", "-r", "--name-only", m["snapshot_sha"]).splitlines()
        self.assertIn(".gitignore", files)
        self.assertNotIn("debug.log", files)
        self.assertNotIn("node_modules/big.js", files)

    def test_capture_is_repeatable_and_yields_the_same_snapshot(self):
        (self.wt / "w.txt").write_text("work\n")
        first = self.capture()
        second = self.capture()
        self.assertEqual(first["snapshot_sha"], second["snapshot_sha"])
        self.assertEqual(first["patch"]["sha256"], second["patch"]["sha256"])

    def test_the_work_survives_deleting_the_branch_and_garbage_collection(self):
        (self.wt / "w.txt").write_text("work\n")
        self.commit("kept.txt")
        m = self.capture()
        self.gw.release(self.ws)                                  # worktree + branch gone
        git(self.repo, "reflog", "expire", "--expire=now", "--all")
        git(self.repo, "gc", "--prune=now", "-q")
        self.assertEqual(git(self.repo, "show", f"{m['refs']['snapshot']}:w.txt"), "work")
        self.assertEqual(git(self.repo, "show", f"{m['refs']['head']}:kept.txt"), "c")

    def test_the_patch_applies_on_the_base_and_its_hash_is_recorded(self):
        self.commit()
        (self.wt / "x.txt").write_text("x\n")
        m = self.capture()
        raw = Path(m["patch"]["path"]).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), m["patch"]["sha256"])
        self.assertEqual(self.rebuild_from_patch(m), git(self.repo, "rev-parse", f"{m['snapshot_sha']}^{{tree}}"))

    def test_an_oversized_patch_is_skipped_but_the_snapshot_ref_still_holds_the_work(self):
        (self.wt / "big.txt").write_text("y" * 5000)
        m = self.capture(patch_max=100)
        self.assertIsNone(m["patch"]["path"])
        self.assertIn("over the 100 byte cap", m["patch"]["skipped"])
        self.assertEqual(git(self.repo, "show", f"{m['refs']['snapshot']}:big.txt"), "y" * 5000)

    def test_a_detached_head_is_recorded_and_still_captured(self):
        self.commit()
        git(self.wt, "checkout", "--detach", "-q")
        (self.wt / "d.txt").write_text("d\n")
        m = self.capture()
        self.assertEqual(m["branch_at_end"], "(detached)")
        self.assertEqual(m["branch"], self.ws.branch)
        self.assertTrue(m["has_commits"] and m["dirty"])

    def test_an_agent_that_switched_branch_is_still_captured(self):
        git(self.wt, "checkout", "-q", "-b", "agent-made")
        (self.wt / "s.txt").write_text("s\n")
        m = self.capture()
        self.assertEqual(m["branch_at_end"], "agent-made")
        self.assertEqual(git(self.repo, "show", f"{m['snapshot_sha']}:s.txt"), "s")

    def test_the_log_tail_is_kept_next_to_the_manifest(self):
        m = self.capture(log_tail=b"last words")
        self.assertEqual(Path(m["log_tail"]).read_bytes(), b"last words")

    def test_a_missing_worktree_is_a_workspace_error_not_a_crash(self):
        self.gw.release(self.ws)
        with self.assertRaises(ex.ExecutorError) as caught:
            self.capture()
        self.assertEqual(caught.exception.code, "WORKSPACE_ERROR")

    def test_the_continuation_brief_states_facts_and_never_claims_reasoning_transfers(self):
        (self.wt / "w.txt").write_text("w\n")
        m = self.capture()
        path = handoff.write_brief(self.out, attempt_id="att-0001", task_id="T1", title="Do it", outcome="failed",
                                   cause="quota_exhausted", manifest=m, detail="limit reached")
        text = path.read_text()
        for needle in ("Task: Do it", "quota_exhausted", m["base_sha"], m["snapshot_sha"], "NOT transferred", "claim"):
            self.assertIn(needle, text)
        failed = handoff.write_brief(self.out, attempt_id="a", task_id="T1", title="t", outcome="failed", cause="lost",
                                     manifest={"status": "failed"}).read_text()
        self.assertIn("No work could be captured", failed)

    def test_the_manifest_is_valid_json_and_has_no_environment_or_secret(self):
        (self.wt / "w.txt").write_text("w\n")
        self.capture()
        data = json.loads((self.out / "handoff" / "manifest.json").read_text())
        self.assertEqual(data["schema"], 1)
        self.assertNotIn("TOKEN", json.dumps(data))


if __name__ == "__main__":
    unittest.main()
