"""`components watch`: a pool change reaches the projects with no manual step (D-293).

Owner, 2026-11-01: in development a change to the pool reaches the project without a manual step or an integration.
Real git repositories and a copy of the pool in a temporary directory; nothing touches a real project."""
from __future__ import annotations

import contextlib
import fcntl
import hashlib
import importlib.util
import io
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
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
        with mock.patch.object(watch, "integration_running", lambda: busy[0]), \
                mock.patch.object(watch, "pool_wip", lambda ui: None):
            w = watch.Watch(self.ui, lambda d: acted.append(d) or True, ready=watch.default_ready(self.ui),
                            note=self.lines.append)
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
        self.assertIn("develop with `components dev` or --into", refused.stderr)
        other = cli("--from", str(self.ui), "--into", str(self.other), "--once")
        self.assertEqual(other.returncode, 1)                          # a project without opt-in is never touched
        self.assertIn("no opted-in project", other.stderr)
        self.assertFalse((self.other / "packages").exists())
        done = cli("--into", str(self.tree), "--restore")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(git(self.tree, "status", "--porcelain"), "")


class WorkInProgress(Fixture):
    """D-295: the owner edits the live checkout's `skill/ui`; the default mode never commits half-written work."""

    def setUp(self):
        super().setUp()
        self.live = self.tmp / "metodologia"                       # a live checkout: the pool tracked by git
        self.ui = self.live / "skill" / "ui"
        shutil.copytree(bt_ui.UI, self.ui)
        git(self.live, "init", "-q", "-b", "main")
        git(self.live, "add", "-A")
        git(self.live, "commit", "-q", "-m", "pool")

    def watcher(self) -> watch.Watch:
        act = watch.sync_projects(lambda: sync.opted_in(self.root), note=self.lines.append, root=self.root,
                                  ui=self.ui)
        return watch.Watch(self.ui, act, ready=watch.default_ready(self.ui), note=self.lines.append)

    def test_the_pool_is_work_in_progress_while_skill_ui_has_uncommitted_changes(self):
        self.assertIsNone(watch.pool_wip(self.ui))
        self.edit_pool()
        self.assertIn("uncommitted changes", watch.pool_wip(self.ui))
        git(self.live, "checkout", "--", ".")
        self.assertIsNone(watch.pool_wip(self.ui))
        (self.ui / "src/components/ui/new-thing.tsx").write_text("export const X = 1;\n")   # untracked counts
        self.assertIn("uncommitted changes", watch.pool_wip(self.ui))
        (self.ui / "src/components/ui/new-thing.tsx").unlink()
        (self.live / "elsewhere.txt").write_text("outside the pool\n")                     # outside skill/ui: no
        self.assertIsNone(watch.pool_wip(self.ui))
        self.assertIn("git cannot tell", watch.pool_wip(self.tmp / "wt" / "skill" / "ui"))  # not a repository

    def test_normal_mode_waits_for_a_committed_pool_and_logs_once_per_digest(self):
        with mock.patch.object(watch, "integration_running", lambda: False):
            w = self.watcher()
            watch.run(w, sleep=lambda s: None, max_polls=3)
            self.assertEqual(self.count(self.repo), 2)                # a clean pool syncs as before
            self.edit_pool()                                          # the owner starts editing: half-written
            watch.run(w, sleep=lambda s: None, max_polls=6)
            self.assertEqual(self.count(self.repo), 2)                # nothing committed on the project's main
            self.assertEqual(sum("uncommitted changes" in line for line in self.lines), 1)
            self.edit_pool("export const Button = () => 1;\n")         # still editing: one line for the new digest
            watch.run(w, sleep=lambda s: None, max_polls=6)
            self.assertEqual(sum("uncommitted changes" in line for line in self.lines), 2)
            self.assertEqual(self.count(self.repo), 2)
            git(self.live, "commit", "-q", "-am", "button")           # committed: synced on the next polls
            watch.run(w, sleep=lambda s: None, max_polls=3)
        self.assertEqual(self.count(self.repo), 3)
        self.assertEqual((self.repo / sync.TARGET / "src/components/ui/button.tsx").read_text(),
                         "export const Button = () => 1;\n")
        self.assertIn("pictures: committed", self.lines[-1])


class WriteOrder(unittest.TestCase):
    """D-295: a running `next dev` must never see an importer before the file it imports, nor a deleted file still
    imported, nor a half-written file."""

    def test_new_files_first_then_changed_and_deletions_last_each_replaced_atomically(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "pkg"
            (dest / "src").mkdir(parents=True)
            (dest / "src/gone.ts").write_text("old\n")
            (dest / "src/button.tsx").write_text("import './gone'\n")
            (dest / "node_modules/x").mkdir(parents=True)
            inode = (dest / "src/button.tsx").stat().st_ino
            ops: list[str] = []
            real_replace, real_unlink = sync._replace, Path.unlink
            def unlink(path: Path, missing_ok: bool = False) -> None:
                if not path.name.endswith(sync.TMP):
                    ops.append(f"rm {path.name}")
                real_unlink(path, missing_ok=missing_ok)
            data = {"src/button.tsx": b"import './zz-new'\n", "src/zz-new.ts": b"new\n", "SYNC.json": b"{}\n"}
            with mock.patch.object(sync, "_replace", lambda p, b: ops.append(f"write {p.name}") or real_replace(p, b)), \
                    mock.patch.object(Path, "unlink", unlink):
                sync._write_tree(dest, data)
            self.assertEqual(ops, ["write zz-new.ts", "write SYNC.json", "write button.tsx", "rm gone.ts"])
            self.assertEqual(sync._on_disk(dest), data)
            self.assertNotEqual((dest / "src/button.tsx").stat().st_ino, inode)   # renamed over, not truncated
            self.assertEqual(sorted(p.name for p in dest.rglob("*") if p.name.endswith(sync.TMP)), [])
            self.assertTrue((dest / "node_modules/x").is_dir())
            (dest / "src/.button.tsx.bt-tmp").write_text("left by a crash\n")       # never content
            self.assertEqual(sync._on_disk(dest), data)


class DevLoop(Fixture):
    """D-295: `components dev [PROJECT]`, the owner's two-step loop."""

    def setUp(self):
        super().setUp()
        (self.repo / "package.json").write_text(json.dumps({"name": "app", "workspaces": ["packages/*"],
                                                            "dependencies": {"@bitacora/ui": "*"}}))
        (self.repo / ".gitignore").write_text("/node_modules\n/packages/*/node_modules\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "wire the pool")
        sync.sync("pictures", self.repo, root=self.root)
        (self.repo / "node_modules/@bitacora").mkdir(parents=True)
        (self.repo / "node_modules/@bitacora/ui").symlink_to("../../packages/bitacora-ui")
        git(self.repo, "worktree", "add", "-q", "-b", "feature", str(self.tmp / "feature"))
        meta = json.loads((self.root / "pictures/project.json").read_text())
        meta["repos"]["app"]["hint"] = str(self.tmp / "feature")      # the role names a linked worktree
        (self.root / "pictures/project.json").write_text(json.dumps(meta))
        self.pkg = self.repo / sync.TARGET

    def run_dev(self, polls: int, **kw) -> tuple[int, str]:
        out = io.StringIO()
        real_run = watch.run
        def run(w, interval, once, reexec=False, on_stop=None):
            w.note = self.lines.append
            ticks = iter(range(polls))
            def sleep(_s: float) -> None:
                if next(ticks, None) is None:
                    raise KeyboardInterrupt
            return real_run(w, interval, once, sleep=sleep, on_stop=on_stop)
        with mock.patch.object(watch, "run", run), mock.patch.object(watch, "log", self.lines.append), \
                contextlib.redirect_stdout(out):
            code = watch.dev(kw.pop("project", "pictures"), str(self.ui), root=self.root, **kw)
        return code, out.getvalue()

    def test_it_writes_into_the_main_checkout_and_restores_it_on_ctrl_c(self):
        self.edit_pool()
        seen: list[str] = []
        real = sync.write_dev
        def spy(project, ui, tree):
            r = real(project, ui, tree)
            seen.append((Path(tree) / sync.TARGET / "src/components/ui/button.tsx").read_text())
            return r
        with mock.patch.object(sync, "write_dev", spy):
            code, banner = self.run_dev(3)
        self.assertEqual(code, 0)
        self.assertEqual(seen, ["export const Button = () => null;\n"])   # the main checkout got the dev copy
        self.assertIn(f"-> {self.pkg}", banner)
        self.assertIn("guard fails on it on purpose", banner)
        self.assertIn("git commit -a", banner)
        self.assertNotIn("npm install", banner)                        # wired: no warning
        self.assertIn("restored", self.lines[-1])
        self.assertEqual(git(self.repo, "status", "--porcelain"), "")   # Ctrl-C: the committed package is back
        self.assertEqual(git(self.tmp / "feature", "status", "--porcelain"), "")

    def test_keep_leaves_the_dev_copy_and_restore_puts_the_package_back(self):
        self.edit_pool()
        code, _banner = self.run_dev(3, keep=True)
        self.assertEqual(code, 0)
        self.assertIn("--keep", self.lines[-1])
        self.assertIs(json.loads((self.pkg / "SYNC.json").read_text())["dev"], True)
        self.assertFalse(guard_passes(self.pkg))
        with mock.patch.object(watch, "log", self.lines.append):
            self.assertEqual(watch.dev("pictures", restore=True, root=self.root), 0)
        self.assertIn("restored", self.lines[-1])
        self.assertEqual(git(self.repo, "status", "--porcelain"), "")

    def test_refusals_are_clear_and_touch_nothing(self):
        err = io.StringIO()
        edited = self.pkg / "src/components/ui/button.tsx"
        edited.write_text("// someone's edit\n")
        with contextlib.redirect_stderr(err):
            self.assertEqual(watch.dev("pictures", str(self.ui), root=self.root), 1)
        self.assertIn("not a previous dev write", err.getvalue())
        self.assertEqual(edited.read_text(), "// someone's edit\n")
        git(self.repo, "checkout", "--", sync.TARGET)
        git(self.repo, "checkout", "-q", "-b", "old-branch", "HEAD~2")    # a branch from before the wiring
        (self.repo / "package.json").write_text(json.dumps({"name": "app"}))
        git(self.repo, "add", "package.json")
        git(self.repo, "commit", "-q", "-m", "no pool here")
        with contextlib.redirect_stderr(err):
            self.assertEqual(watch.dev("pictures", str(self.ui), root=self.root), 1)
        self.assertIn("(old-branch) does not depend on @bitacora/ui", err.getvalue())
        self.assertFalse((self.repo / sync.TARGET).exists())
        with contextlib.redirect_stderr(err):
            self.assertEqual(watch.dev("other", str(self.ui), root=self.root), 1)
            self.assertEqual(watch.dev(None, str(self.ui), into=str(self.other), root=self.root), 1)
        self.assertIn("other does not opt in", err.getvalue())
        self.assertIn("no opted-in project uses this repository", err.getvalue())
        self.assertFalse((self.other / "packages").exists())

    def test_an_unlinked_package_is_warned_about(self):
        (self.repo / "node_modules/@bitacora/ui").unlink()
        self.edit_pool()
        _code, banner = self.run_dev(2)
        self.assertIn("run `npm install`", banner)

    def test_sigterm_restores_the_committed_package(self):
        self.edit_pool()
        env = {**os.environ, "BITACORA_ROOT": str(self.root), **ENV}
        proc = subprocess.Popen([sys.executable, str(SCRIPTS / "bitacora.py"), "components", "dev", "pictures",
                                 "--from", str(self.ui.parent.parent), "--interval", "0.2"],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
        try:
            for _ in range(150):
                stamp = self.pkg / "SYNC.json"
                if stamp.is_file() and json.loads(stamp.read_text()).get("dev"):
                    break
                if proc.poll() is not None:
                    self.fail(f"dev exited {proc.returncode}: {proc.communicate()}")
                time.sleep(0.1)
            self.assertIn(f"{sync.TARGET}/", git(self.repo, "status", "--porcelain"))
            proc.send_signal(signal.SIGTERM)
            out, err = proc.communicate(timeout=30)
        finally:
            if proc.poll() is None:
                proc.kill()
        self.assertEqual(proc.returncode, 0, err)
        self.assertIn("DEV loop for pictures", out)
        self.assertIn("restored", out)
        self.assertEqual(git(self.repo, "status", "--porcelain"), "")
        self.assertTrue(guard_passes(self.pkg))


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
