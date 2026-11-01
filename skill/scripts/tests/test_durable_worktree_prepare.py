"""D-273: an attempt worktree starts with the tree the verifier checks — lockfile installed, `sandbox_prepare` run.

pictures REQ-021 r32 T3.91 a2-a4: M6's `next typegen` wrote `next-env.d.ts` into its copy, a full `tsc --noEmit` failed
there and passed in the fresh worktree, and three attempts were spent before the owner was asked.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from bt_durable.adapters import worktree_prepare
from bt_scheduler_quality import sandbox_mounts, sandbox_prepare, sandbox_provision
from bt_scheduler_quality.policy import QualityPolicy
from durable_support import git
from test_durable_agent_env import AttemptLab

PY = sys.executable
INSTALL = ("-c", ("import os; os.makedirs('node_modules', exist_ok=True); "
                  "open('node_modules/.package-lock.json', 'w').write('{}'); open('ran.log', 'a').write('install\\n')"))
TYPEGEN = (PY, "-c", ("import os; os.makedirs('.next/types', exist_ok=True); open('next-env.d.ts', 'w').write('x'); "
                      "open('.next/types/routes.d.ts', 'w').write('x'); open('ran.log', 'a').write('typegen\\n')"))
NO_TOOLCHAIN = sandbox_mounts.Toolchain()


def _repo(root: Path, *, ignore: str = "node_modules/\nnext-env.d.ts\n.next/\nran.log\n", workspaces: bool = False) -> Path:
    repo = root / "repo"
    repo.mkdir()
    manifest = {"name": "app", "dependencies": {"next": "16.3.0"}}
    if workspaces:
        manifest["workspaces"] = ["packages/*"]
        (repo / "packages" / "lib").mkdir(parents=True)
        (repo / "packages" / "lib" / "package.json").write_text(json.dumps({"scripts": {"build": "tsc"}}))
    (repo / "package.json").write_text(json.dumps(manifest))
    (repo / "package-lock.json").write_text("{}")
    (repo / ".gitignore").write_text(ignore)
    git(repo, "init", "-q")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "base")
    return repo


class WorktreePreparation(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="bt-wt-prepare-"))
        self.attempt_dir = self.root / "attempt"
        self.attempt_dir.mkdir()
        for target in (patch.object(sandbox_prepare, "NEXT_TYPEGEN", TYPEGEN),
                       patch.object(sandbox_provision, "NPM_CI_ARGS", INSTALL),
                       patch.object(worktree_prepare.shutil, "which", return_value=PY),
                       patch.object(worktree_prepare, "toolchain", return_value=NO_TOOLCHAIN)):
            target.start()
            self.addCleanup(target.stop)

    def prepare(self, repo: Path, policy: QualityPolicy | None = None, **kwargs) -> str:
        return worktree_prepare.prepare_worktree(repo, self.attempt_dir, policy, os.environ, **kwargs)

    def test_a_next_worktree_is_installed_and_prepared_like_the_verifiers_copy_once(self):
        repo = _repo(self.root)
        note = self.prepare(repo)
        again = self.prepare(repo)                       # a retried bt.prepare step: same brief, nothing rerun

        self.assertEqual((repo / "ran.log").read_text(), "install\ntypegen\n")
        self.assertTrue((repo / "next-env.d.ts").is_file())
        self.assertEqual(again, note)
        self.assertIn(f"`npm {' '.join(INSTALL)}` then `{' '.join(TYPEGEN)}` ran here", note)
        self.assertIn("This mirrors the verifier", note)
        self.assertIn("(next-env.d.ts and .next/types/**)", note)
        self.assertNotIn("does not git-ignore", note)
        report = json.loads((self.attempt_dir / worktree_prepare.REPORT).read_text())
        self.assertEqual([step["status"] for step in report["steps"]], ["ok", "ok"])

    def test_dependencies_already_installed_are_not_installed_again(self):
        repo = _repo(self.root)
        (repo / "node_modules").mkdir()
        (repo / "node_modules" / ".package-lock.json").write_text("{}")

        note = self.prepare(repo)

        self.assertEqual((repo / "ran.log").read_text(), "typegen\n")
        self.assertIn(f"Worktree prepared before you started: `{' '.join(TYPEGEN)}` ran here", note)

    def test_a_failing_step_is_reported_with_its_output_and_the_steps_after_it_are_named_not_run(self):
        repo = _repo(self.root, workspaces=True)
        broken = (PY, "-c", "import sys; print('packages/lib: error TS2307'); sys.exit(3)")
        with patch.object(sandbox_prepare, "BUILD_WORKSPACES", broken):
            note = self.prepare(repo)

        self.assertIn(f"`{' '.join(broken)}` failed (exit 3)", note)
        self.assertIn(f"Not run after it: `{' '.join(TYPEGEN)}`", note)
        self.assertIn("packages/lib: error TS2307", note)
        self.assertIn("a check will fail the same way", note)
        self.assertFalse((repo / "next-env.d.ts").exists())

    def test_a_step_past_the_budget_is_killed_and_reported(self):
        repo = _repo(self.root)
        (repo / "node_modules").mkdir()
        (repo / "node_modules" / ".package-lock.json").write_text("{}")
        slow = (PY, "-c", "import time; time.sleep(60)")
        started = time.monotonic()
        with patch.object(sandbox_prepare, "NEXT_TYPEGEN", slow):
            note = self.prepare(repo, budget=1)

        self.assertLess(time.monotonic() - started, 15)
        self.assertIn(f"`{' '.join(slow)}` timed out", note)

    def test_nothing_runs_without_a_lockfile_a_step_or_the_verifiers_toolchain(self):
        repo = _repo(self.root)
        self.assertEqual(self.prepare(repo, QualityPolicy(toolchain=False)), "")
        (self.attempt_dir / worktree_prepare.REPORT).unlink()
        (repo / "package-lock.json").unlink()
        self.assertEqual(self.prepare(repo), "")
        self.assertFalse((repo / "ran.log").exists())

    def test_generated_files_the_repository_does_not_ignore_are_named_as_captured(self):
        repo = _repo(self.root, ignore="node_modules/\nran.log\n")
        note = self.prepare(repo)

        self.assertIn("does not git-ignore (`.next/types/routes.d.ts`, `next-env.d.ts`)", note)

    def test_the_steps_get_the_verifiers_environment_on_the_host(self):
        fake = sandbox_mounts.Toolchain((), ("/opt/node/bin",), (("NODE_OPTIONS", "--max-old-space-size=6144"),))
        policy = QualityPolicy(environment=(("NODE_OPTIONS", "--max-old-space-size=12288"), ("APP_KEY", "k")),
                               ambient_environment=(("FNM_DIR", "/f"),))
        with patch.object(worktree_prepare, "toolchain", return_value=fake):
            env = worktree_prepare._environment(policy, {"PATH": "/usr/bin", "HOME": "/h", "SECRET_ENGINE": "x"})

        self.assertEqual(env["PATH"], "/opt/node/bin:/usr/bin")
        self.assertEqual((env["NODE_OPTIONS"], env["APP_KEY"], env["FNM_DIR"], env["HOME"]),
                         ("--max-old-space-size=12288", "k", "/f", "/h"))
        self.assertNotIn("SECRET_ENGINE", env)


class AttemptBriefNamesThePreparation(AttemptLab):
    def test_the_attempt_worktree_is_prepared_before_the_agent_and_its_brief_says_so(self):
        repo = self.lab.repo
        (repo / "package.json").write_text(json.dumps({"dependencies": {"next": "16.3.0"}}))
        (repo / "package-lock.json").write_text("{}")
        (repo / ".gitignore").write_text("node_modules/\nnext-env.d.ts\n.next/\nran.log\n")
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "node app")
        with patch.object(sandbox_prepare, "NEXT_TYPEGEN", TYPEGEN), \
                patch.object(sandbox_provision, "NPM_CI_ARGS", INSTALL), \
                patch.object(worktree_prepare.shutil, "which", return_value=PY), \
                patch.object(worktree_prepare, "toolchain", return_value=NO_TOOLCHAIN):
            prepared = self.prepare(str(self.tmp / "missing-{project}.env"))

        self.assertTrue((prepared.worktree / "next-env.d.ts").is_file())
        self.assertIn("Worktree prepared before you started", prepared.prompt_path.read_text())
        self.assertIn("This mirrors the verifier", prepared.prompt_path.read_text())


if __name__ == "__main__":
    unittest.main()
