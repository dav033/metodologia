"""End-to-end smoke of the verifier on a minimal JS monorepo, with the real Node, npm and bubblewrap.

It exercises the seams that broke the first real run, none of which a unit test with a fake runner can reach: an attempt
with no dependencies of its own that borrows the repository's, a workspace package whose ignored `dist` must be built
inside the sandbox before the check, the git metadata of a linked worktree, and a check that must really fail.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from bt_scheduler_quality.policy import CheckSpec, QualityPolicy
from bt_scheduler_quality.runner import SandboxRunner
from bt_scheduler_quality.sandbox_mounts import attempt_mounts, toolchain

AVAILABLE = shutil.which("bwrap") and shutil.which("node") and shutil.which("npm") and shutil.which("git")
LOCK = '{"name": "smoke", "lockfileVersion": 3}\n'


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(cwd), "-c", "user.email=t@t", "-c", "user.name=t", *args],
                          check=True, capture_output=True, text=True).stdout.strip()


def check(*argv: str) -> CheckSpec:
    return CheckSpec("CHECK-001", "command", " ".join(argv), tuple(argv), ".", "smoke")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@unittest.skipUnless(AVAILABLE and toolchain(QualityPolicy()).mounts, "needs bwrap, git and a Node under $HOME")
class VerifierSmoke(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.repo, self.worktree = base / "repo", base / "attempt"
        write(self.repo / "package.json", json.dumps({"private": True, "workspaces": ["packages/*"],
                                                       "scripts": {"test": "node packages/app/test.js"}}))
        write(self.repo / "package-lock.json", LOCK)
        write(self.repo / ".gitignore", "node_modules\ndist\n")
        write(self.repo / "packages/lib/package.json", json.dumps({"name": "lib", "scripts": {"build": "node build.js"}}))
        write(self.repo / "packages/lib/build.js",
              "const fs = require('fs'); fs.mkdirSync('dist', {recursive: true});"
              "fs.writeFileSync('dist/index.js', \"module.exports = require('dep') + '-lib';\");")
        self.test_js = "const lib = require('../lib/dist/index.js'); if (lib !== 'dep-lib') process.exit(7);"
        write(self.repo / "packages/app/test.js", self.test_js)
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-q", "-m", "base")
        write(self.repo / "node_modules/dep/index.js", "module.exports = 'dep';")      # installed, ignored by git
        write(self.repo / "node_modules/dep/package.json", '{"name": "dep", "version": "1.0.0"}')
        git(self.repo, "worktree", "add", "-q", "-b", "attempt", str(self.worktree))
        self.snapshot = base / "snapshot"
        shutil.copytree(self.worktree, self.snapshot, ignore=shutil.ignore_patterns(".git"))
        self.policy = QualityPolicy()

    def run_check(self, *argv: str, snapshot: Path | None = None):
        root = snapshot or self.snapshot
        mounts = attempt_mounts(self.policy, self.worktree, self.repo, root)
        return SandboxRunner(self.policy).run(check(*argv), root, mounts=mounts)

    def test_a_workspace_test_passes_with_borrowed_dependencies_and_a_sandbox_built_dist(self):
        self.assertFalse((self.snapshot / "packages/lib/dist").exists())
        result = self.run_check("npm", "test")
        self.assertEqual((result.status, result.exit_code), ("pass", 0), result.stderr.decode()[-600:])

    def test_the_same_check_fails_when_the_code_is_wrong(self):
        write(self.snapshot / "packages/app/test.js", self.test_js.replace("'dep-lib'", "'other'"))
        result = self.run_check("npm", "test")
        self.assertEqual(result.status, "fail")

    def test_dependencies_of_another_lockfile_are_not_borrowed(self):
        write(self.snapshot / "package-lock.json", LOCK.replace("smoke", "changed"))
        result = self.run_check("npm", "test")
        self.assertEqual(result.status, "fail")

    def test_git_sees_the_attempt_branch_inside_the_sandbox(self):
        result = self.run_check("git", "rev-parse", "--abbrev-ref", "HEAD")
        self.assertEqual((result.status, result.stdout.decode().splitlines()[-1]), ("pass", "attempt"))

    def test_the_sandbox_writes_to_a_throwaway_overlay_never_the_host(self):
        write(self.snapshot / "write.js", "require('fs').writeFileSync('/workspace/node_modules/dep/index.js', 'x')")
        result = self.run_check("node", "write.js")
        self.assertEqual(result.status, "pass")      # the sandbox may write its own copy (overlay) ...
        self.assertEqual((self.repo / "node_modules/dep/index.js").read_text(), "module.exports = 'dep';")


if __name__ == "__main__":
    unittest.main()
