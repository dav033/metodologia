"""`components watch`: a pool change reaches the projects with no manual step (D-293).

Owner, 2026-11-01: in development a change to the pool reaches the project without a manual step or an integration.
Real git repositories and a copy of the pool in a temporary directory; nothing touches a real project."""
from __future__ import annotations

import fcntl
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bt_ui
import bt_ui_sync as sync
import bt_ui_watch as watch

ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
SCRIPTS = Path(__file__).resolve().parents[1]


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True,
                          env={**os.environ, **ENV}).stdout.strip()


def guard_passes(package: Path) -> bool:
    """The rule of pictures' `scripts/test/test-ui-pool-guardia.ts` §1: the digest of the package's files, in
    `bt_ui.files` order, equals `SYNC.json`'s `pool`."""
    stamp = json.loads((package / "SYNC.json").read_text())
    src = [p for p in sorted((package / "src").rglob("*")) if p.is_file() and p.name not in {"README.md", ".DS_Store"}]
    order = [package / "package.json", *src] + ([package / "LICENSES.md"] if (package / "LICENSES.md").is_file() else [])
    order += [package / stamp["theme"]] if stamp.get("theme") else []
    h = hashlib.sha256()
    for p in order:
        h.update(p.relative_to(package).as_posix().encode() + b"\0" + p.read_bytes() + b"\0")
    return h.hexdigest()[:12] == stamp["pool"]


class Fixture(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.ui = self.tmp / "wt" / "skill" / "ui"             # a pool under development (a worktree's copy)
        shutil.copytree(bt_ui.UI, self.ui)
        self.repo = self.make_repo("project")
        self.other = self.make_repo("other")
        self.root = self.tmp / "bitacora"
        for name, repo, ui in (("pictures", self.repo, {"sync": True, "repo": "app"}), ("other", self.other, None)):
            (self.root / name).mkdir(parents=True)
            meta = {"repos": {"app": {"remote": "", "hint": str(repo)}}, **({"ui": ui} if ui else {})}
            (self.root / name / "project.json").write_text(json.dumps(meta))
        patcher = mock.patch("bt_core.ROOT", self.root)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.lines: list[str] = []

    def make_repo(self, name: str) -> Path:
        repo = self.tmp / name
        repo.mkdir()
        git(repo, "init", "-q", "-b", "main")
        git(repo, "config", "user.name", "Project Dev")
        git(repo, "config", "user.email", "dev@example.test")
        (repo / "app.ts").write_text("export const app = 1;\n")
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "init")
        return repo

    def edit_pool(self, text: str = "export const Button = () => null;\n") -> None:
        (self.ui / "src/components/ui/button.tsx").write_text(text)

    def count(self, repo: Path) -> int:
        return int(git(repo, "rev-list", "--count", "main"))


class Debounce(Fixture):
    def test_the_digest_follows_content_and_a_missing_pool_has_none(self):
        first = watch.pool_digest(self.ui)
        self.assertRegex(first, r"\A[0-9a-f]{12}\Z")
        self.assertEqual(watch.pool_digest(self.ui), first)
        os.utime(self.ui / "package.json")                           # a touch is not a change
        self.assertEqual(watch.pool_digest(self.ui), first)
        (self.ui / "themes" / "x.css").write_text(":root{}\n")      # themes count
        self.assertNotEqual(watch.pool_digest(self.ui), first)
        (self.ui / "src" / "README.md").write_text("notes\n")       # what the package skips does not
        second = watch.pool_digest(self.ui)
        (self.ui / "src" / "README.md").write_text("other notes\n")
        self.assertEqual(watch.pool_digest(self.ui), second)
        self.assertIsNone(watch.pool_digest(self.tmp / "nowhere"))

    def test_it_acts_only_on_two_equal_consecutive_digests_and_once_per_digest(self):
        acted: list[str] = []
        w = watch.Watch(self.ui, lambda d: acted.append(d) or True, note=self.lines.append)
        self.assertFalse(w.poll())                                   # first sight: not yet stable
        self.assertTrue(w.poll())
        self.assertFalse(w.poll())                                   # same digest: nothing
        self.edit_pool()
        self.assertFalse(w.poll())                                   # changed: wait one interval
        self.edit_pool("export const Button = () => 1;\n")           # still being written
        self.assertFalse(w.poll())
        self.assertTrue(w.poll())
        self.assertEqual(len(acted), 2)
        self.assertEqual(acted[-1], watch.pool_digest(self.ui))

    def test_a_failure_is_logged_once_and_retried_only_when_the_pool_changes(self):
        calls: list[str] = []
        w = watch.Watch(self.ui, lambda d: calls.append(d) and False, note=self.lines.append)
        for _ in range(6):
            w.poll()
        self.assertEqual(len(calls), 1)
        self.assertEqual(sum("not carried" in line for line in self.lines), 1)
        self.edit_pool()
        for _ in range(3):
            w.poll()
        self.assertEqual(len(calls), 2)

    def test_a_running_integration_holds_the_sync_until_it_ends(self):
        busy = [True]
        acted: list[str] = []
        w = watch.Watch(self.ui, lambda d: acted.append(d) or True, ready=lambda: not busy[0], note=self.lines.append)
        for _ in range(4):
            w.poll()
        self.assertEqual(acted, [])
        self.assertEqual(sum("integration is running" in line for line in self.lines), 1)
        busy[0] = False
        w.poll()
        self.assertEqual(len(acted), 1)

    def test_the_integrate_lock_is_seen_while_held(self):
        state = self.tmp / "state"
        state.mkdir()
        with mock.patch("bt_core.STATE", state):
            self.assertFalse(watch.integration_running())
            with open(state / "integrate.lock", "a+") as handle:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                self.assertTrue(watch.integration_running())
            self.assertFalse(watch.integration_running())

    def test_once_acts_a_single_time_and_returns(self):
        acted: list[str] = []
        w = watch.Watch(self.ui, lambda d: acted.append(d) or True, note=self.lines.append)
        self.assertEqual(watch.run(w, once=True, sleep=lambda s: None, max_polls=10), 0)
        self.assertEqual(len(acted), 1)
        failing = watch.Watch(self.ui, lambda d: False, note=self.lines.append)
        self.assertEqual(watch.run(failing, once=True, sleep=lambda s: None, max_polls=10), 1)

    def test_the_long_running_watcher_re_executes_itself_when_its_code_changes(self):
        w = watch.Watch(self.ui, lambda d: True, note=self.lines.append)
        codes = iter(["old", "old", "new"])
        with mock.patch.object(watch, "code_digest", lambda: next(codes)), \
                mock.patch.object(watch.os, "execv", side_effect=SystemExit(0)) as execv, \
                self.assertRaises(SystemExit):
            watch.run(w, sleep=lambda s: None, reexec=True, max_polls=5)
        self.assertEqual(execv.call_args.args[0], sys.executable)
        self.assertIn("re-executing", self.lines[-1])


class DefaultMode(Fixture):
    def watcher(self) -> watch.Watch:
        act = watch.sync_projects(lambda: sync.opted_in(self.root), note=self.lines.append, root=self.root,
                                  ui=self.ui)
        return watch.Watch(self.ui, act, note=self.lines.append)

    def test_a_change_commits_once_on_the_default_branch_and_never_touches_a_project_without_opt_in(self):
        w = self.watcher()
        self.assertEqual(watch.run(w, sleep=lambda s: None, max_polls=5), 0)
        self.assertEqual(self.count(self.repo), 2)
        self.assertIn("pictures: committed", self.lines[-1])
        self.edit_pool()
        watch.run(w, sleep=lambda s: None, max_polls=5)
        self.assertEqual(self.count(self.repo), 3)
        self.assertEqual(sync.recorded(self.repo, "main")["pool"], bt_ui.digest(bt_ui.files("pictures", self.ui), self.ui))
        watch.run(w, sleep=lambda s: None, max_polls=5)              # same digest: nothing
        self.assertEqual(self.count(self.repo), 3)
        self.assertEqual(self.count(self.other), 1)                   # no ui.sync: never touched
        self.assertFalse((self.other / "packages").exists())
        self.assertTrue(guard_passes(self.repo / sync.TARGET))

    def test_a_restarted_watcher_finds_the_same_pool_already_synced(self):
        watch.run(self.watcher(), sleep=lambda s: None, max_polls=3)
        watch.run(self.watcher(), sleep=lambda s: None, max_polls=3)  # what the integrate trigger also finds
        self.assertEqual(self.count(self.repo), 2)
        self.assertIn("pictures: unchanged", self.lines[-1])

    def test_a_dirty_target_is_logged_once_and_nothing_is_half_written(self):
        watch.run(self.watcher(), sleep=lambda s: None, max_polls=3)
        edited = self.repo / sync.TARGET / "src/components/ui/button.tsx"
        edited.write_text("// someone's edit\n")
        self.edit_pool()
        w = self.watcher()
        self.assertEqual(watch.run(w, sleep=lambda s: None, max_polls=8), 1)
        self.assertEqual(sum("not synced into pictures" in line for line in self.lines), 1)
        self.assertEqual(edited.read_text(), "// someone's edit\n")
        self.assertEqual(self.count(self.repo), 2)


class DevMode(Fixture):
    def setUp(self):
        super().setUp()
        sync.sync("pictures", self.repo, root=self.root)             # the committed copy, as on pictures' main
        git(self.repo, "worktree", "add", "-q", "-b", "feature", str(self.tmp / "feature"))
        self.tree = self.tmp / "feature"
        self.pkg = self.tree / sync.TARGET

    def test_dev_writes_are_uncommitted_marked_dev_and_fail_the_projects_guard(self):
        self.assertTrue(guard_passes(self.pkg))
        self.edit_pool()
        head = git(self.tree, "rev-parse", "HEAD")
        r = sync.write_dev("pictures", self.ui, self.tree)
        self.assertEqual(r["status"], "written")
        self.assertEqual((self.pkg / "src/components/ui/button.tsx").read_text(), "export const Button = () => null;\n")
        stamp = json.loads((self.pkg / "SYNC.json").read_text())
        self.assertIs(stamp["dev"], True)
        self.assertEqual(stamp["dev_source"], str(self.ui))
        self.assertEqual(stamp["pool"], f"dev-{stamp['dev_pool']}")
        self.assertEqual(git(self.tree, "rev-parse", "HEAD"), head)  # nothing committed
        self.assertIn(f"{sync.TARGET}/SYNC.json", git(self.tree, "status", "--porcelain"))
        self.assertFalse(guard_passes(self.pkg))                     # never committable by accident
        self.edit_pool("export const Button = () => 2;\n")             # a second dev write over the first
        self.assertEqual(sync.write_dev("pictures", self.ui, self.tree)["status"], "written")
        self.assertEqual(sync.write_dev("pictures", self.ui, self.tree)["status"], "unchanged")
        self.assertEqual(sync.restore(self.tree), "restored")
        self.assertEqual(git(self.tree, "status", "--porcelain"), "")
        self.assertTrue(guard_passes(self.pkg))
        self.assertEqual(sync.restore(self.tree), "clean")

    def test_foreign_uncommitted_changes_are_refused_and_kept(self):
        edited = self.pkg / "src/components/ui/button.tsx"
        edited.write_text("// someone's edit\n")
        with self.assertRaises(sync.SyncError) as raised:
            sync.write_dev("pictures", self.ui, self.tree)
        self.assertIn("not a previous dev write", str(raised.exception))
        self.assertEqual(edited.read_text(), "// someone's edit\n")
        with self.assertRaises(sync.SyncError):
            sync.restore(self.tree)
        edited.write_text(edited.read_text())
        git(self.tree, "checkout", "--", sync.TARGET)
        sync.write_dev("pictures", self.ui, self.tree)                # a dev write edited by hand afterwards
        (self.pkg / "src/components/ui/badge.tsx").write_text("// hand edit over the dev copy\n")
        with self.assertRaises(sync.SyncError):
            sync.write_dev("pictures", self.ui, self.tree)

    def test_a_dev_write_on_the_default_branch_worktree_is_replaced_by_the_normal_sync(self):
        self.edit_pool()
        sync.write_dev("pictures", self.ui, self.repo)
        r = sync.sync("pictures", self.repo, root=self.root)
        self.assertEqual(r["status"], "unchanged")                     # the committed pool is back, nothing new
        self.assertEqual(git(self.repo, "status", "--porcelain"), "")

    def test_the_watch_writes_into_the_tree_without_committing(self):
        w = watch.Watch(self.ui, watch.write_into("pictures", self.ui, self.tree, note=self.lines.append),
                        note=self.lines.append)
        self.edit_pool()
        self.assertEqual(watch.run(w, once=True, sleep=lambda s: None, max_polls=5), 0)
        self.assertIn("DEV copy", self.lines[-1])
        self.assertEqual(git(self.tree, "rev-list", "--count", "HEAD"), "2")
        self.assertIs(json.loads((self.pkg / "SYNC.json").read_text())["dev"], True)

    def test_the_command_line(self):
        env = {**os.environ, "BITACORA_ROOT": str(self.root), **ENV}
        def cli(*args: str) -> subprocess.CompletedProcess:
            return subprocess.run([sys.executable, str(SCRIPTS / "bitacora.py"), "components", "watch", *args],
                                  capture_output=True, text=True, env=env, timeout=60, check=False)
        self.edit_pool()
        done = cli("--from", str(self.ui.parent.parent), "--into", str(self.tree), "--once", "--interval", "0.2")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("DEV mode", done.stdout)
        self.assertIn("(pictures)", done.stdout)                        # inferred from the repository
        self.assertIs(json.loads((self.pkg / "SYNC.json").read_text())["dev"], True)
        refused = cli("--from", str(self.ui), "--once")                # no --into: only the live pool
        self.assertEqual(refused.returncode, 1)
        self.assertIn("develop with --into", refused.stderr)
        other = cli("--from", str(self.ui), "--into", str(self.other), "--once")
        self.assertEqual(other.returncode, 1)                          # a project without opt-in is never touched
        self.assertIn("no opted-in project", other.stderr)
        self.assertFalse((self.other / "packages").exists())
        done = cli("--into", str(self.tree), "--restore")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(git(self.tree, "status", "--porcelain"), "")


class Unit(unittest.TestCase):
    def test_install_writes_the_watcher_unit_with_this_machines_paths_and_never_enables_it(self):
        repo = Path(__file__).resolve().parents[3]
        spec = importlib.util.spec_from_file_location("metodologia_install_watch", repo / "install.py")
        install = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(install)
        source = repo / "skill/scripts/deploy/bitacora-ui-watch.service"
        self.assertIn("Restart=on-failure", source.read_text())
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(install.subprocess, "run") as run, \
                mock.patch.object(install.shutil, "which", return_value="/usr/bin/systemctl"), \
                mock.patch.object(install.sys, "platform", "linux"):
            units = Path(tmp)
            self.assertIn("installed", install.install_unit(source, Path("/b/root"), units))
            text = (units / source.name).read_text()
            self.assertIn(f"ExecStart=/usr/bin/python3 {install.REPO.as_posix()}/skill/scripts/bitacora.py components "
                          "watch", text)
            self.assertIn("BITACORA_ROOT=/b/root", text)
            self.assertIn("up to date", install.install_unit(source, Path("/b/root"), units))
            commands = [call.args[0] for call in run.call_args_list]
        self.assertEqual(commands, [["systemctl", "--user", "daemon-reload"]])   # never enable/start


if __name__ == "__main__":
    unittest.main()
