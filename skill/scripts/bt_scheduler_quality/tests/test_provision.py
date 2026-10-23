"""An attempt that installed no dependencies gets the ones its lockfile pins, installed offline and mounted in the sandbox (writable there, never on the host)."""
from __future__ import annotations

import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bt_scheduler_quality.policy import QualityPolicy
from bt_scheduler_quality.sandbox_mounts import attempt_mounts
from bt_scheduler_quality.sandbox_provision import provision

NPM = """#!/bin/sh
here=$(dirname "$0")
echo "$@" >> "$here/npm.log"
[ -f "$here/fail" ] && { echo "boom" >&2; exit 1; }
mkdir -p node_modules/pkg && echo ok > node_modules/pkg/index.js
exit 0
"""


class Provision(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        bin_dir = self.root / "bin"
        bin_dir.mkdir()
        npm = bin_dir / "npm"
        npm.write_text(NPM)
        npm.chmod(npm.stat().st_mode | stat.S_IXUSR)
        self.log = bin_dir / "npm.log"
        self.fail = bin_dir / "fail"
        env = {"PATH": f"{bin_dir}:{os.environ['PATH']}", "M6_DEPS_CACHE": str(self.root / "cache")}
        patcher = patch.dict(os.environ, env)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.snapshot = self.root / "snapshot"
        self.app = self.snapshot / "web"
        self.app.mkdir(parents=True)
        (self.app / "package.json").write_text('{"name": "web"}')
        (self.app / "package-lock.json").write_text('{"lockfileVersion": 3}')
        self.worktree = self.root / "worktree"
        self.worktree.mkdir()

    def calls(self):
        return self.log.read_text().splitlines() if self.log.exists() else []

    def test_dependencies_are_installed_offline_without_scripts_once_per_lockfile(self):
        first = provision(self.app)
        self.assertTrue((first / "pkg" / "index.js").is_file())
        self.assertEqual(provision(self.app), first)
        self.assertEqual(self.calls(), ["ci --offline --ignore-scripts --no-audit --no-fund"])
        (self.app / "package-lock.json").write_text('{"lockfileVersion": 3, "x": 1}')
        self.assertNotEqual(provision(self.app), first)                                  # another lock, another tree

    def test_nothing_is_provisioned_without_a_lockfile_or_when_the_install_fails(self):
        (self.app / "package-lock.json").unlink()
        self.assertIsNone(provision(self.app))
        (self.app / "package-lock.json").write_text("{}")
        self.fail.write_text("")
        self.assertIsNone(provision(self.app))
        self.assertEqual([p.name for p in (self.root / "cache").iterdir()], [])           # no half-built tree is kept

    def test_an_attempt_without_dependencies_mounts_the_provisioned_ones(self):
        mounts = attempt_mounts(QualityPolicy(), self.worktree, snapshot_root=self.snapshot)
        shown = {m.target: m.source for m in mounts}
        self.assertIn("/workspace/web/node_modules", shown)
        self.assertTrue(shown["/workspace/web/node_modules"].startswith(str(self.root / "cache")))
        off = attempt_mounts(QualityPolicy(provision_dependencies=False), self.worktree, snapshot_root=self.snapshot)
        self.assertNotIn("/workspace/web/node_modules", {m.target for m in off})

    def test_an_install_that_stopped_halfway_is_replaced_but_a_finished_one_is_kept(self):
        partial = self.worktree / "web" / "node_modules"
        (partial / "left").mkdir(parents=True)
        shown = {m.target: m.source for m in attempt_mounts(QualityPolicy(), self.worktree, snapshot_root=self.snapshot)}
        self.assertNotEqual(shown["/workspace/web/node_modules"], str(partial.resolve()))
        (partial / ".package-lock.json").write_text("{}")                                  # npm writes it when it finishes
        shown = {m.target: m.source for m in attempt_mounts(QualityPolicy(), self.worktree, snapshot_root=self.snapshot)}
        self.assertEqual(shown["/workspace/web/node_modules"], str(partial.resolve()))


if __name__ == "__main__":
    unittest.main()
