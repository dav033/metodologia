"""Disposable Git repositories exercise durable worktree integration and recovery."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[2] / "skill" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import bt_integration_lock as lease  # noqa: E402
import bt_worktree as worktree  # noqa: E402


class WorktreeRecoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="worktree-recovery-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.git(self.repo, "init", "-q", "-b", "main")
        self.git(self.repo, "config", "user.name", "Migration Test")
        self.git(self.repo, "config", "user.email", "migration@example.test")
        (self.repo / "README").write_text("base\n", encoding="utf-8")
        self.git(self.repo, "add", "README")
        self.git(self.repo, "commit", "-qm", "base")
        self.base = self.git(self.repo, "rev-parse", "HEAD")
        self.integration = self.root / "integration"
        self.git(self.repo, "worktree", "add", "-qb", "integrate/feature", str(self.integration), self.base)
        self.git(self.integration, "config", "user.name", "Migration Test")
        self.git(self.integration, "config", "user.email", "migration@example.test")
        self.alloc_root = self.root / "allocations"

    @staticmethod
    def git(cwd: Path, *args: str) -> str:
        result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)
        return result.stdout.strip()

    def new_candidate(self, task: str, relative: str, content: str) -> dict:
        allocation = worktree.allocate(self.repo, task, self.base, self.alloc_root)
        path = Path(allocation["worktree"]) / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        allocation["allowed_paths"] = [str(Path(relative).parent)] if Path(relative).parent != Path(".") else [relative]
        worktree.record_stage(allocation, "executed")
        worktree.check_scope(allocation, allocation["allowed_paths"])
        sha = worktree.candidate(allocation)
        return {"allocation": allocation, "sha": sha, "journal": allocation["journal"]}

    def test_three_disjoint_worktrees_integrate_serially_and_verify_combined_result(self) -> None:
        candidates = [self.new_candidate(f"T{i}", f"src/{i}.txt", f"task {i}\n") for i in range(3)]
        self.assertEqual(len({item["allocation"]["worktree"] for item in candidates}), 3)
        verify = "python -c \"from pathlib import Path; assert all(p.read_text().startswith('task') for p in Path('src').glob('*.txt'))\""
        result = worktree.integrate(candidates, self.integration, verify, lease.IntegrationLock(self.root / "lock"))
        self.assertEqual(result, {f"T{i}": "accepted" for i in range(3)})
        self.assertEqual(len(list(self.integration.joinpath("src").glob("*.txt"))), 3)
        stages = [r["stage"] for r in map(json.loads, Path(candidates[0]["journal"]).read_text().splitlines())
                  if r["task_id"] == "T0"]
        self.assertEqual(stages[-2:], ["accepted", "cleanup_eligible"])

    def test_faults_at_each_integration_journal_stage_recover_exactly_once(self) -> None:
        for stage in ("lock_acquired", "merged", "verified", "accepted", "cleanup_eligible"):
            with self.subTest(stage=stage):
                case = self.root / stage
                case.mkdir()
                repo = case / "repo"
                repo.mkdir()
                self.git(repo, "init", "-q", "-b", "main")
                self.git(repo, "config", "user.name", "Test")
                self.git(repo, "config", "user.email", "test@example.test")
                (repo / "base").write_text("base\n")
                self.git(repo, "add", "base")
                self.git(repo, "commit", "-qm", "base")
                base = self.git(repo, "rev-parse", "HEAD")
                integration = case / "integration"
                self.git(repo, "worktree", "add", "-qb", "integrate/feature", str(integration), base)
                self.git(integration, "config", "user.name", "Test")
                self.git(integration, "config", "user.email", "test@example.test")
                allocation = worktree.allocate(repo, "only", base, case / "alloc")
                allocation["allowed_paths"] = ["result"]
                (Path(allocation["worktree"]) / "result").write_text("ok\n")
                sha = worktree.candidate(allocation)
                candidate = {"allocation": allocation, "sha": sha, "journal": allocation["journal"]}
                original = worktree._record

                def fail_after(path: Path, task_id: str, actual: str, **fields: object) -> None:
                    original(path, task_id, actual, **fields)
                    if actual == stage:
                        raise RuntimeError("injected crash")

                with patch.object(worktree, "_record", side_effect=fail_after):
                    with self.assertRaisesRegex(RuntimeError, "injected crash"):
                        worktree.integrate([candidate], integration, "test -f result", lease.IntegrationLock(case / "lock"))
                outcome = worktree.recover([candidate], integration, "test -f result", lease.IntegrationLock(case / "lock"))
                self.assertEqual(outcome, {"only": "accepted"})
                rows = [json.loads(line) for line in Path(allocation["journal"]).read_text().splitlines()]
                self.assertEqual(sum(row.get("candidate_sha") == sha and row["stage"] == "accepted" for row in rows), 1)
                self.assertEqual(self.git(repo, "branch", "--format=%(refname:short)", "--list", allocation["branch"]).strip(), allocation["branch"])
                self.assertTrue(Path(allocation["worktree"]).exists())

    def test_merge_conflict_preserves_candidate_and_marks_blocked(self) -> None:
        one = self.new_candidate("one", "same", "one\n")
        two = self.new_candidate("two", "same", "two\n")
        result = worktree.integrate([one, two], self.integration, "true", lease.IntegrationLock(self.root / "lock"))
        self.assertEqual(result, {"one": "accepted", "two": "blocked"})
        self.assertTrue(Path(two["allocation"]["worktree"]).exists())
        self.assertEqual(self.git(self.repo, "branch", "--format=%(refname:short)", "--list", two["allocation"]["branch"]).strip(), two["allocation"]["branch"])
        rows = [json.loads(line) for line in Path(two["journal"]).read_text().splitlines()]
        self.assertIn("conflict", next(row["reason"] for row in rows if row["task_id"] == "two" and row["stage"] == "blocked"))

    def test_failed_combined_verify_rolls_back_and_preserves_candidate(self) -> None:
        item = self.new_candidate("bad", "bad.txt", "candidate\n")
        result = worktree.integrate([item], self.integration, "false", lease.IntegrationLock(self.root / "lock"))
        self.assertEqual(result, {"bad": "blocked"})
        self.assertFalse((self.integration / "bad.txt").exists())
        self.assertTrue(Path(item["allocation"]["worktree"]).exists())
        self.assertEqual(self.git(self.repo, "branch", "--format=%(refname:short)", "--list", item["allocation"]["branch"]).strip(), item["allocation"]["branch"])

    def test_scope_rejects_traversal_sibling_prefix_and_symlink_escape(self) -> None:
        item = self.new_candidate("scope", "src/application/file", "x\n")
        with self.assertRaises(worktree.WorktreeError):
            worktree.check_scope(item["allocation"], ["../src"])
        with self.assertRaisesRegex(worktree.WorktreeError, "outside"):
            worktree.check_scope(item["allocation"], ["src/app"])
        escape = Path(item["allocation"]["worktree"]) / "escape"
        escape.symlink_to(self.root, target_is_directory=True)
        self.git(Path(item["allocation"]["worktree"]), "add", "escape")
        with self.assertRaisesRegex(worktree.WorktreeError, "outside|symlink"):
            worktree.check_scope(item["allocation"], ["src", "escape"])

    def test_scope_rejects_rename_from_outside_and_integration_requires_scope(self) -> None:
        (self.integration / "outside.txt").write_text("move me\n", encoding="utf-8")
        self.git(self.integration, "add", "outside.txt")
        self.git(self.integration, "commit", "-qm", "add move source")
        self.base = self.git(self.integration, "rev-parse", "HEAD")
        allocation = worktree.allocate(self.repo, "move", self.base, self.alloc_root)
        allocation["allowed_paths"] = ["src"]
        candidate_worktree = Path(allocation["worktree"])
        (candidate_worktree / "src").mkdir()
        self.git(candidate_worktree, "mv", "outside.txt", "src/moved.txt")
        sha = worktree.candidate(allocation)
        item = {"allocation": allocation, "sha": sha, "journal": allocation["journal"]}
        self.assertEqual(worktree._changed_paths(allocation), ["outside.txt", "src/moved.txt"])
        with self.assertRaises(worktree.WorktreeError):
            worktree.check_scope(allocation, ["src"])
        blocked = worktree.integrate([item], self.integration, "true", lease.IntegrationLock(self.root / "lock"))
        self.assertEqual(blocked, {"move": "blocked"})
        self.assertFalse((self.integration / "src/moved.txt").exists())
        allocation.pop("allowed_paths", None)
        result = worktree.integrate([item], self.integration, "true", lease.IntegrationLock(self.root / "lock"))
        self.assertEqual(result, {"move": "serialize-only"})
        self.assertFalse((self.integration / "src/moved.txt").exists())

    def test_scope_rejects_dot_and_empty_and_allow_all_is_explicit(self) -> None:
        item = self.new_candidate("dot", "file", "x\n")
        for scope in (".", ""):
            with self.assertRaises(worktree.WorktreeError):
                worktree.check_scope(item["allocation"], [scope])
        self.assertEqual(worktree.check_scope({**item["allocation"], "allow_all": True}, ["."])["status"], "serialize")

    def test_detached_and_default_branches_are_rejected(self) -> None:
        self.git(self.integration, "checkout", "--detach", "HEAD")
        with self.assertRaisesRegex(worktree.WorktreeError, "branch"):
            worktree.integrate([], self.integration, "true", lease.IntegrationLock(self.root / "lock"))

    def test_post_merge_recovery_verify_failure_restores_recorded_parent(self) -> None:
        item = self.new_candidate("crash", "result", "bad\n")
        before = self.git(self.integration, "rev-parse", "HEAD")
        original = worktree._record
        def crash_after_merge(path: Path, task_id: str, stage: str, **fields: object) -> None:
            original(path, task_id, stage, **fields)
            if stage == "merged":
                raise RuntimeError("crash after merge")
        with patch.object(worktree, "_record", side_effect=crash_after_merge):
            with self.assertRaisesRegex(RuntimeError, "crash after merge"):
                worktree.integrate([item], self.integration, "true", lease.IntegrationLock(self.root / "lock"))
        result = worktree.recover([item], self.integration, "false", lease.IntegrationLock(self.root / "lock"))
        self.assertEqual(result, {"crash": "blocked"})
        self.assertEqual(self.git(self.integration, "rev-parse", "HEAD"), before)

    def test_torn_trailing_journal_line_is_ignored(self) -> None:
        path = self.root / "torn.jsonl"
        path.write_text('{"stage":"ok"}\n{"stage":', encoding="utf-8")
        self.assertEqual(worktree._journal_rows(path), [{"stage": "ok"}])

    def test_missing_scope_serializes_and_integration_protects_main(self) -> None:
        allocation = {"worktree": str(self.integration), "base_sha": self.base}
        self.assertEqual(worktree.check_scope(allocation, None)["status"], "serialize")
        with self.assertRaisesRegex(worktree.WorktreeError, "protected"):
            worktree.integrate([], self.repo, "true", lease.IntegrationLock(self.root / "lock"))

    def test_cleanup_refuses_dirty_worktree_and_source_avoids_forced_git_options(self) -> None:
        item = self.new_candidate("dirty", "clean.txt", "ok\n")
        worktree.integrate([item], self.integration, "true", lease.IntegrationLock(self.root / "lock"))
        allocation = item["allocation"]
        (Path(allocation["worktree"]) / "later").write_text("keep\n")
        with self.assertRaisesRegex(worktree.WorktreeError, "dirty"):
            worktree.cleanup(allocation)
        source = (SCRIPTS / "bt_worktree.py").read_text(encoding="utf-8")
        self.assertNotIn('"-B"', source)
        self.assertNotIn('"--force"', source)


if __name__ == "__main__":
    unittest.main()
