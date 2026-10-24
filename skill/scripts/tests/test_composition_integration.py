from __future__ import annotations

import ast
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


class CompositionIntegrationTests(unittest.TestCase):
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
                with self.assertRaisesRegex(ValueError, "WORKSPACE_ROOT_INSIDE_REPOSITORY"):
                    adapter.GitSubprocessPort(repo, repo / "worktrees")
                for sp, commit in (("S1", s1v1), ("S2", s2v1), ("S3", s3v1)):
                    engine.publish_subplan_version("P", "r1", sp, commit, base, {"api@1": "declared"}, [])
                c1 = engine.build_candidate("P", {"S1": 1, "S2": 1, "S3": 1})
                self.assertTrue(engine.publish(c1.id, {"M6": "PASS"}))
                current = self.git(repo, "rev-parse", "refs/compositions/P/current")
                s1v2 = commit_file("s1.txt", "one\nnew\n", s1v1)
                engine.publish_subplan_version("P", "r2", "S1", s1v2, s1v1, {"api@1": "declared"}, [])
                c2 = engine.build_candidate("P", {"S1": 2, "S2": 1, "S3": 1})
                self.assertFalse(engine.publish(c2.id, {"M6": "FAIL"}))
                self.assertEqual(self.git(repo, "rev-parse", "refs/compositions/P/current"), current)

                # A later candidate whose atomic ref transaction fails remains retryable.
                s1v3 = commit_file("s1.txt", "one\nnew\nnewer\n", s1v2)
                engine.publish_subplan_version("P", "r3", "S1", s1v3, s1v1, {"api@1": "declared"}, [])
                c3 = engine.build_candidate("P", {"S1": 3, "S2": 1, "S3": 1})
                self.assertEqual(c3.state, "candidate", c3.conflict_paths)
                workspace = engine.open_workspace(c3.id)
                self.assertTrue(Path(workspace).is_relative_to(workspaces))
                engine.close_workspace(workspace)
                original_update = engine.git.update_refs
                def fail_once(updates):
                    engine.git.update_refs = original_update
                    raise adapter.GitCommandError("simulated_update_ref_failure")
                engine.git.update_refs = fail_once
                with self.assertRaisesRegex(adapter.GitCommandError, "simulated_update_ref_failure"):
                    engine.publish(c3.id, {"M6": "PASS"})
                self.assertEqual(self.git(repo, "rev-parse", "refs/compositions/P/current"), current)
                self.assertEqual(engine.build_candidate("P", {"S1": 3, "S2": 1, "S3": 1}).id, c3.id)
                self.assertTrue(engine.publish(c3.id, {"M6": "PASS"}))

                s1v4 = commit_file("s2.txt", "two changed\n", s1v3)
                engine.publish_subplan_version("P", "r4", "S1", s1v4, s1v1, {"api@1": "declared"}, [])
                conflict = engine.build_candidate("P", {"S1": 4, "S2": 1, "S3": 1})
                self.assertEqual(conflict.state, "rejected")
                self.assertEqual(conflict.reason_code, "git_text_conflict")
                self.assertEqual(self.git(repo, "rev-parse", "refs/compositions/P/current"), c3.integrated_commit)
                self.assertEqual(self.git(repo, "rev-parse", "HEAD"), original_head)
            finally:
                store.close()

    def test_package_is_declared_for_distribution(self):
        config = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
        setuptools = config["tool"]["setuptools"]
        self.assertIn("bt_composition", setuptools["packages"])
        self.assertIn("README.md", setuptools["package-data"]["bt_composition"])
        self.assertIn("bt_composition_adapter", setuptools["py-modules"])


if __name__ == "__main__":
    unittest.main()
