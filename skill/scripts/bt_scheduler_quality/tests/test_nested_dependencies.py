"""Nested applications receive their own dependencies in the verification sandbox."""
import tempfile
import unittest
from pathlib import Path

from bt_scheduler_quality.policy import CheckSpec, QualityPolicy
from bt_scheduler_quality.runner import SandboxRunner
from bt_scheduler_quality.sandbox_mounts import attempt_mounts


class NestedDependenciesTests(unittest.TestCase):
    def test_nested_dependencies_are_read_only_inside_real_sandbox(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            snapshot, worktree = root / 'snapshot', root / 'worktree'
            app = snapshot / 'remote/web'
            app.mkdir(parents=True)
            (app / 'package.json').write_text('{}')
            modules = worktree / 'remote/web/node_modules'
            modules.mkdir(parents=True)
            (modules / 'marker').write_text('installed')
            (app / 'probe.py').write_text(
                "from pathlib import Path\n"
                "assert Path('node_modules/marker').read_text() == 'installed'\n"
                "try:\n    Path('node_modules/marker').write_text('changed')\n"
                "except OSError:\n    pass\n"
                "else:\n    raise AssertionError('dependencies are writable')\n"
            )
            policy = QualityPolicy()
            mounts = attempt_mounts(policy, worktree, snapshot_root=snapshot)
            check = CheckSpec('C1', 'command', 'cd remote/web && python3 probe.py',
                              ('python3', 'probe.py'), 'remote/web', 'nested dependency isolation')
            result = SandboxRunner(policy).run(check, snapshot, mounts=mounts)
            self.assertEqual((result.status, result.exit_code), ('pass', 0), result)

    def test_nested_app_mounts_its_installed_dependencies(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            snapshot, worktree = root / "snapshot", root / "worktree"
            app = snapshot / "remote/web"
            app.mkdir(parents=True)
            (app / "package.json").write_text('{}')
            modules = worktree / "remote/web/node_modules"
            modules.mkdir(parents=True)
            mounts = attempt_mounts(QualityPolicy(), worktree, snapshot_root=snapshot)
            self.assertIn((str(modules), '/workspace/remote/web/node_modules'),
                          [(m.source, m.target) for m in mounts])

    def test_nested_shared_dependencies_require_matching_lock(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            snapshot, worktree, repo = root / "snapshot", root / "worktree", root / "repo"
            worktree.mkdir()
            for base in (snapshot, repo):
                app = base / "remote/web"
                app.mkdir(parents=True)
                (app / "package.json").write_text('{}')
                (app / "package-lock.json").write_text('same')
            (repo / "remote/web/node_modules").mkdir()
            mounts = attempt_mounts(QualityPolicy(), worktree, repo, snapshot)
            self.assertEqual(len(mounts), 1)
            (snapshot / "remote/web/package-lock.json").write_text('changed')
            self.assertEqual(attempt_mounts(QualityPolicy(), worktree, repo, snapshot), ())
