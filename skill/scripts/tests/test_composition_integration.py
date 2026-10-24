from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
REPO = SCRIPTS.parent.parent
sys.path.insert(0, str(SCRIPTS))

import bt_composition_adapter as adapter
from bt_composition import VerdictProof


class CompositionIntegrationTests(unittest.TestCase):
    @staticmethod
    def proofs(engine, candidate, verdict="PASS"):
        return {"M6": VerdictProof(candidate.id, candidate.manifest_sha256, candidate.integrated_commit,
                                    engine.git.tree_oid(candidate.integrated_commit), verdict, "M6",
                                    "sha256:" + hashlib.sha256(b"integration-evidence").hexdigest())}

    def test_only_adapter_imports_module(self):
        offenders = []
        for path in SCRIPTS.rglob("*.py"):
            relative = path.relative_to(SCRIPTS)
            if "tests" in relative.parts or "bt_composition" in relative.parts:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                names = [alias.name.split(".")[0] for alias in node.names] if isinstance(node, ast.Import) else []
                if isinstance(node, ast.ImportFrom) and not node.level:
                    names.append((node.module or "").split(".")[0])
                if "bt_composition" in names and path.name != "bt_composition_adapter.py":
                    offenders.append(str(relative))
        self.assertEqual(offenders, [])

    def test_only_adapter_owns_git_subprocess_calls(self):
        package = SCRIPTS / "bt_composition"
        source = "\n".join(path.read_text(encoding="utf-8") for path in package.rglob("*.py")
                            if "tests" not in path.parts)
        self.assertNotIn("subprocess", source)
        self.assertIn("import subprocess", (SCRIPTS / "bt_composition_adapter.py").read_text(encoding="utf-8"))

    def test_package_suite_runs_as_subprocess(self):
        result = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s",
                                 str(SCRIPTS / "bt_composition" / "tests")], cwd=SCRIPTS,
                                capture_output=True, text=True, timeout=90)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    @staticmethod
    def git(repo: Path, *args: str, input_text: str | None = None) -> str:
        result = subprocess.run(["git", "-C", str(repo), *args], input=input_text,
                                capture_output=True, text=True, check=False)
        if result.returncode:
            raise AssertionError(result.stderr)
        return result.stdout.strip()

    def test_real_git_candidate_publish_failure_conflict_and_retry(self):
        with tempfile.TemporaryDirectory(prefix="composition-git-") as directory:
            root = Path(directory)
            repo = root / "repo"
            repo.mkdir()
            self.git(repo, "init", "-q")
            self.git(repo, "config", "user.name", "Test")
            self.git(repo, "config", "user.email", "test@example.invalid")
            (repo / "base.txt").write_text("base\n", encoding="utf-8")
            self.git(repo, "add", "base.txt")
            self.git(repo, "commit", "-qm", "base")
            base = self.git(repo, "rev-parse", "HEAD")
            original_head = self.git(repo, "rev-parse", "HEAD")

            def commit_file(name: str, text: str, parent: str) -> str:
                self.git(repo, "read-tree", parent)
                (repo / name).write_text(text, encoding="utf-8")
                self.git(repo, "add", name)
                tree = self.git(repo, "write-tree")
                return self.git(repo, "commit-tree", tree, "-p", parent, input_text=f"{name}\n")

            s1v1 = commit_file("s1.txt", "one\n", base)
            s2v1 = commit_file("s2.txt", "two\n", base)
            s3v1 = commit_file("s3.txt", "three\n", base)
            store_path, workspaces = root / "run.db", root / "workspaces"
            engine, store = adapter.create_engine(repo, store_path, workspaces)
            try:
                with self.assertRaisesRegex(ValueError, "STORE_PATH_INSIDE_REPOSITORY"):
                    adapter.create_engine(repo, repo / "state.db", root / "other-workspaces")
                with self.assertRaisesRegex(ValueError, "WORKSPACE_ROOT_OVERLAPS_REPOSITORY"):
                    adapter.GitSubprocessPort(repo, repo / "worktrees")
                for sp, commit in (("S1", s1v1), ("S2", s2v1), ("S3", s3v1)):
                    engine.publish_subplan_version("P", "r1", sp, commit, base, {"api@1": "declared"}, [])
                c1 = engine.build_candidate("P", {"S1": 1, "S2": 1, "S3": 1}, member_order=("S1", "S2", "S3"))
                self.assertTrue(engine.publish(c1.id, self.proofs(engine, c1)))
                current = self.git(repo, "rev-parse", "refs/compositions/P/current")
                s1v2 = commit_file("s1.txt", "one\nnew\n", s1v1)
                engine.publish_subplan_version("P", "r2", "S1", s1v2, s1v1, {"api@1": "declared"}, [])
                c2 = engine.build_candidate("P", {"S1": 2, "S2": 1, "S3": 1}, member_order=("S1", "S2", "S3"))
                self.assertFalse(engine.publish(c2.id, self.proofs(engine, c2, "FAIL")))
                self.assertEqual(self.git(repo, "rev-parse", "refs/compositions/P/current"), current)

                # A later candidate whose atomic ref transaction fails remains retryable.
                s1v3 = commit_file("s1.txt", "one\nnew\nnewer\n", s1v2)
                engine.publish_subplan_version("P", "r3", "S1", s1v3, s1v1, {"api@1": "declared"}, [])
                c3 = engine.build_candidate("P", {"S1": 3, "S2": 1, "S3": 1}, member_order=("S1", "S2", "S3"))
                self.assertEqual(c3.state, "candidate", c3.conflict_paths)
                workspace = engine.open_workspace(c3.id)
                self.assertTrue(Path(workspace).is_relative_to(workspaces))
                marker_path = workspaces / f"{Path(workspace).name}.composition-owner.json"
                engine.close_workspace(workspace)
                self.assertFalse(marker_path.exists())
                original_update = engine.git.update_refs
                def fail_once(updates):
                    engine.git.update_refs = original_update
                    raise adapter.GitCommandError("simulated_update_ref_failure")
                engine.git.update_refs = fail_once
                with self.assertRaisesRegex(adapter.GitCommandError, "simulated_update_ref_failure"):
                    engine.publish(c3.id, self.proofs(engine, c3))
                self.assertEqual(self.git(repo, "rev-parse", "refs/compositions/P/current"), current)
                self.assertEqual(engine.build_candidate("P", {"S1": 3, "S2": 1, "S3": 1}, member_order=("S1", "S2", "S3")).id, c3.id)
                self.assertTrue(engine.publish(c3.id, self.proofs(engine, c3)))

                s1v4 = commit_file("s2.txt", "two changed\n", s1v3)
                engine.publish_subplan_version("P", "r4", "S1", s1v4, s1v1, {"api@1": "declared"}, [])
                conflict = engine.build_candidate("P", {"S1": 4, "S2": 1, "S3": 1}, member_order=("S1", "S2", "S3"))
                self.assertEqual(conflict.state, "rejected")
                self.assertEqual(conflict.reason_code, "git_text_conflict")
                self.assertEqual(self.git(repo, "rev-parse", "refs/compositions/P/current"), c3.integrated_commit)
                self.assertEqual(self.git(repo, "rev-parse", "HEAD"), original_head)
            finally:
                store.close()

    def test_real_git_c1_to_c2_publish_refs_oid_validation_digest_and_wal(self):
        with tempfile.TemporaryDirectory(prefix="composition-real-") as directory:
            root = Path(directory)
            repo = root / "repo"
            repo.mkdir()
            self.git(repo, "init", "-q")
            self.git(repo, "config", "user.name", "Test")
            self.git(repo, "config", "user.email", "test@example.invalid")
            (repo / "base.txt").write_text("base\n", encoding="utf-8")
            self.git(repo, "add", "base.txt")
            self.git(repo, "commit", "-qm", "base")
            base = self.git(repo, "rev-parse", "HEAD")

            def commit_file(name: str, text: str, parent: str) -> str:
                self.git(repo, "read-tree", parent)
                (repo / name).write_text(text, encoding="utf-8")
                self.git(repo, "add", name)
                tree = self.git(repo, "write-tree")
                return self.git(repo, "commit-tree", tree, "-p", parent, input_text=f"{name}\n")

            s1v1 = commit_file("s1.txt", "one\n", base)
            s2v1 = commit_file("s2.txt", "two\n", base)
            s3v1 = commit_file("s3.txt", "three\n", base)
            workspaces = root / "workspaces"
            engine, store = adapter.create_engine(repo, root / "state.db", workspaces)
            try:
                self.assertEqual(store.connection.execute("PRAGMA journal_mode").fetchone()[0].lower(), "wal")
                port = engine.git
                self.assertTrue(port.tree_digest(base, ("base.txt",)))
                self.assertEqual(port.diff_paths(base, s1v1), ("s1.txt",))
                with self.assertRaisesRegex(ValueError, "EMPTY_RELEVANT_PATHS"):
                    port.tree_digest(base, ())
                with self.assertRaisesRegex(ValueError, "TREE_PATHS_MISSING"):
                    port.tree_digest(base, ("missing.txt",))

                version = engine.publish_subplan_version("P", "r1", "HEADSP", "HEAD", "HEAD", {}, [])
                self.assertEqual(version.commit, base)
                a, b = s1v1, s2v1
                injected = f"{a}\nupdate refs/heads/evil {b}"
                with self.assertRaisesRegex(ValueError, "INVALID_VERSION_COMMIT"):
                    engine.publish_subplan_version("P", "r1", "INJECTED", injected, base, {}, [])
                with self.assertRaisesRegex(ValueError, "INVALID_REF_OID"):
                    port.update_refs((("refs/compositions/P/candidates/C999", injected, None),))
                self.assertIsNone(port.rev_parse("refs/heads/evil"))

                engine.publish_subplan_version("P", "r1", "S1", s1v1, base, {"api@1": "declared"}, [])
                engine.publish_subplan_version("P", "r1", "S2", s2v1, base, {"api@1": "declared"}, [])
                engine.publish_subplan_version("P", "r1", "S3", s3v1, base, {"api@1": "declared"}, [])
                c1 = engine.build_candidate("P", {"S1": 1, "S2": 1, "S3": 1}, member_order=("S1", "S2", "S3"))
                self.assertTrue(engine.publish(c1.id, self.proofs(engine, c1)))
                s2_ref = port.rev_parse("refs/subplans/P/S2/v1")
                s3_ref = port.rev_parse("refs/subplans/P/S3/v1")
                s1v2 = commit_file("s1.txt", "one\nnew\n", s1v1)
                engine.publish_subplan_version("P", "r2", "S1", s1v2, s1v1, {"api@1": "declared"}, [])
                c2 = engine.build_candidate("P", {"S1": 2, "S2": 1, "S3": 1}, member_order=("S1", "S2", "S3"))
                workspace = Path(engine.open_workspace(c2.id))
                self.assertTrue(workspace.exists())
                marker_path = workspaces / f"{workspace.name}.composition-owner.json"
                marker = json.loads(marker_path.read_text(encoding="utf-8"))
                marker["owner_pid"] = 2_000_000_000
                marker_path.write_text(json.dumps(marker), encoding="utf-8")
                self.assertIn(str(workspace), engine.prune_workspaces())
                self.assertFalse(workspace.exists())
                self.assertFalse(marker_path.exists())
                self.assertTrue(engine.publish(c2.id, self.proofs(engine, c2)))
                self.assertEqual(port.rev_parse("refs/compositions/P/current"), c2.integrated_commit)
                self.assertEqual(port.rev_parse("refs/compositions/P/C1"), c1.integrated_commit)
                self.assertEqual(port.rev_parse("refs/subplans/P/S2/v1"), s2_ref)
                self.assertEqual(port.rev_parse("refs/subplans/P/S3/v1"), s3_ref)
            finally:
                store.close()

    def test_git_ref_transaction_does_not_follow_namespaced_symrefs(self):
        with tempfile.TemporaryDirectory(prefix="composition-symref-") as directory:
            root = Path(directory)
            repo = root / "repo"
            repo.mkdir()
            self.git(repo, "init", "-q")
            self.git(repo, "config", "user.name", "Test")
            self.git(repo, "config", "user.email", "test@example.invalid")
            (repo / "base.txt").write_text("base\n", encoding="utf-8")
            self.git(repo, "add", "base.txt")
            self.git(repo, "commit", "-qm", "base")
            main_before = self.git(repo, "rev-parse", "HEAD")
            target_ref = self.git(repo, "symbolic-ref", "HEAD")
            self.git(repo, "symbolic-ref", "refs/compositions/P/current", target_ref)
            port = adapter.GitSubprocessPort(repo, root / "workspaces")
            replacement = self.git(repo, "rev-parse", "HEAD^{tree}")
            port.update_refs((("refs/compositions/P/candidates/C1", main_before, None),
                              ("refs/compositions/P/current", replacement, main_before)))
            self.assertEqual(self.git(repo, "rev-parse", target_ref), main_before)
            self.assertEqual(self.git(repo, "rev-parse", "refs/compositions/P/current"), replacement)
            symbolic = subprocess.run(["git", "-C", str(repo), "symbolic-ref", "-q",
                                       "refs/compositions/P/current"], capture_output=True, check=False)
            self.assertNotEqual(symbolic.returncode, 0)

    def test_git_ref_transaction_does_not_follow_symrefs_on_later_delete(self):
        with tempfile.TemporaryDirectory(prefix="composition-symref-delete-") as directory:
            root = Path(directory)
            repo = root / "repo"
            repo.mkdir()
            self.git(repo, "init", "-q")
            self.git(repo, "config", "user.name", "Test")
            self.git(repo, "config", "user.email", "test@example.invalid")
            (repo / "base.txt").write_text("base\n", encoding="utf-8")
            self.git(repo, "add", "base.txt")
            self.git(repo, "commit", "-qm", "base")
            main_ref = self.git(repo, "symbolic-ref", "HEAD")
            main_before = self.git(repo, "rev-parse", "HEAD")
            self.git(repo, "symbolic-ref", "refs/compositions/P/current", main_ref)
            port = adapter.GitSubprocessPort(repo, root / "workspaces")
            port.update_refs((("refs/compositions/P/candidates/C1", main_before, None),
                              ("refs/compositions/P/current", None, main_before)))
            self.assertEqual(self.git(repo, "rev-parse", main_ref), main_before)
            self.assertEqual(self.git(repo, "rev-parse", "refs/compositions/P/candidates/C1"), main_before)

    def test_tree_digest_rejects_option_like_commit(self):
        with tempfile.TemporaryDirectory(prefix="composition-tree-args-") as directory:
            root = Path(directory)
            repo = root / "repo"
            repo.mkdir()
            self.git(repo, "init", "-q")
            port = adapter.GitSubprocessPort(repo, root / "workspaces")
            with self.assertRaisesRegex(ValueError, "INVALID_TREE_COMMIT"):
                port.tree_digest("--help", ("README.md",))

    def test_workspace_root_ancestor_of_repository_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="composition-overlap-") as directory:
            root = Path(directory)
            repo = root / "repo"
            repo.mkdir()
            self.git(repo, "init", "-q")
            with self.assertRaisesRegex(ValueError, "WORKSPACE_ROOT_OVERLAPS_REPOSITORY"):
                adapter.GitSubprocessPort(repo, root)

    def test_workspace_root_nested_under_repository_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="composition-overlap-reverse-") as directory:
            repo = Path(directory) / "repo"
            repo.mkdir()
            self.git(repo, "init", "-q")
            with self.assertRaisesRegex(ValueError, "WORKSPACE_ROOT_OVERLAPS_REPOSITORY"):
                adapter.GitSubprocessPort(repo, repo / "workspaces")

    def test_pruning_never_removes_active_or_foreign_worktrees(self):
        with tempfile.TemporaryDirectory(prefix="composition-prune-") as directory:
            root = Path(directory)
            repo = root / "repo"
            workspaces = root / "workspaces"
            repo.mkdir()
            self.git(repo, "init", "-q")
            self.git(repo, "config", "user.name", "Test")
            self.git(repo, "config", "user.email", "test@example.invalid")
            (repo / "base.txt").write_text("base\n", encoding="utf-8")
            self.git(repo, "add", "base.txt")
            self.git(repo, "commit", "-qm", "base")
            base = self.git(repo, "rev-parse", "HEAD")
            port = adapter.GitSubprocessPort(repo, workspaces)
            active_path = Path(port.add_worktree(base, workspaces))
            self.assertEqual(self.git(active_path, "status", "--porcelain"), "")
            self.assertEqual(port.prune_workspaces(), ())
            self.assertTrue(active_path.exists())
            foreign_path = workspaces / "foreign"
            self.git(repo, "worktree", "add", "--detach", str(foreign_path), base)
            with self.assertRaisesRegex(ValueError, "WORKTREE_OWNERSHIP_UNVERIFIED"):
                port.remove_worktree(foreign_path)
            self.assertEqual(port.prune_workspaces(), ())
            self.assertTrue(foreign_path.exists())

    def test_locked_and_git_failure_worktrees_are_never_deleted(self):
        with tempfile.TemporaryDirectory(prefix="composition-prune-failure-") as directory:
            root = Path(directory)
            repo = root / "repo"
            workspaces = root / "workspaces"
            repo.mkdir()
            self.git(repo, "init", "-q")
            self.git(repo, "config", "user.name", "Test")
            self.git(repo, "config", "user.email", "test@example.invalid")
            (repo / "base.txt").write_text("base\n", encoding="utf-8")
            self.git(repo, "add", "base.txt")
            self.git(repo, "commit", "-qm", "base")
            base = self.git(repo, "rev-parse", "HEAD")
            port = adapter.GitSubprocessPort(repo, workspaces)
            locked_path = Path(port.add_worktree(base, workspaces))
            self.git(repo, "worktree", "lock", str(locked_path))
            self.assertEqual(port.prune_workspaces(), ())
            self.assertTrue(locked_path.exists())

            orphan = Path(port.add_worktree(base, workspaces))
            marker_path = workspaces / f"{orphan.name}.composition-owner.json"
            marker = json.loads(marker_path.read_text(encoding="utf-8"))
            marker["owner_pid"] = 2_000_000_000
            marker_path.write_text(json.dumps(marker), encoding="utf-8")
            original_run = port._run
            def fail_remove(*args, **kwargs):
                if args[:2] == ("worktree", "remove"):
                    return subprocess.CompletedProcess(args, 1, "", "simulated removal failure")
                return original_run(*args, **kwargs)
            port._run = fail_remove
            with self.assertRaisesRegex(adapter.GitCommandError, "simulated removal failure"):
                port.prune_workspaces()
            self.assertTrue(orphan.exists())

    def test_package_is_declared_for_distribution(self):
        config = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
        setuptools = config["tool"]["setuptools"]
        self.assertIn("bt_composition", setuptools["packages"])
        self.assertIn("README.md", setuptools["package-data"]["bt_composition"])
        self.assertIn("bt_composition_adapter", setuptools["py-modules"])


if __name__ == "__main__":
    unittest.main()
