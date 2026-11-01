"""`components sync`: the pool written into a project's repository and committed on its default branch (D-280).

Owner, 2026-10-31: «Directo, sin paso intermedio». Real git repositories in a temporary directory; nothing touches a
real project."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bt_integrate as integ
import bt_ui
import bt_ui_sync as sync
import test_integrate as base
from test_integrate import commit, sh

ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True,
                          env={**__import__("os").environ, **ENV}).stdout.strip()


class Fixture(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.repo = self.tmp / "project"
        self.repo.mkdir()
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "config", "user.name", "Project Dev")
        git(self.repo, "config", "user.email", "dev@example.test")
        (self.repo / "package.json").write_text('{"name": "app", "workspaces": ["packages/*"]}\n')
        (self.repo / "app.ts").write_text("export const app = 1;\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "init")

    def files_on(self, ref: str) -> set[str]:
        return set(git(self.repo, "ls-tree", "-r", "--name-only", ref).splitlines())


class Sync(Fixture):
    def test_checked_out_default_branch_gets_one_commit_of_the_package_path_only_and_is_idempotent(self):
        (self.repo / "app.ts").write_text("export const app = 2; // the developer's work in progress\n")
        r = sync.sync("pictures", self.repo)
        self.assertEqual((r["status"], r["branch"]), ("committed", "main"))
        names = self.files_on("main")
        self.assertIn("packages/bitacora-ui/package.json", names)
        self.assertIn("packages/bitacora-ui/src/components/ui/button.tsx", names)
        self.assertIn("packages/bitacora-ui/themes/pictures.css", names)
        self.assertNotIn("packages/bitacora-ui/themes/other.css", names)
        changed = git(self.repo, "show", "--name-only", "--format=", "HEAD").splitlines()
        self.assertTrue(all(p.startswith("packages/bitacora-ui/") for p in changed))
        self.assertIn("app = 2", (self.repo / "app.ts").read_text())          # the developer's edit is untouched
        self.assertEqual(git(self.repo, "status", "--porcelain"), "M app.ts")
        stamp = sync.recorded(self.repo, "main")
        self.assertEqual(stamp["pool"], r["pool"])
        self.assertEqual(stamp["pool"], bt_ui.digest(bt_ui.files("pictures")))
        self.assertEqual(stamp["theme"], "themes/pictures.css")
        self.assertIn("sync @bitacora/ui", git(self.repo, "log", "-1", "--format=%s"))
        self.assertEqual(git(self.repo, "log", "-1", "--format=%an"), "Project Dev")
        again = sync.sync("pictures", self.repo)
        self.assertEqual((again["status"], again["commit"]), ("unchanged", r["commit"]))
        self.assertEqual(git(self.repo, "rev-list", "--count", "main"), "2")

    def test_a_feature_branch_checked_out_never_moves_and_the_default_branch_is_committed_by_plumbing(self):
        git(self.repo, "checkout", "-q", "-b", "feature")
        (self.repo / "wip.txt").write_text("not committed\n")
        r = sync.sync("pictures", self.repo)
        self.assertEqual(r["status"], "committed")
        self.assertEqual(git(self.repo, "branch", "--show-current"), "feature")
        self.assertFalse((self.repo / "packages").exists())                    # the checkout did not move
        self.assertTrue((self.repo / "wip.txt").is_file())
        self.assertIn("packages/bitacora-ui/src/styles.css", self.files_on("main"))
        self.assertIn("app.ts", self.files_on("main"))
        self.assertEqual(git(self.repo, "rev-parse", "main^"), git(self.repo, "rev-parse", "feature"))
        self.assertEqual(sync.sync("pictures", self.repo)["status"], "unchanged")

    def test_a_pool_change_is_one_more_commit_and_stale_files_go(self):
        first = sync.sync("pictures", self.repo)
        with tempfile.TemporaryDirectory() as tmp:
            import shutil
            ui = Path(tmp) / "ui"
            shutil.copytree(bt_ui.UI, ui)
            (ui / "src/components/ui/button.tsx").write_text("export const Button = () => null;\n")
            (ui / "src/components/ui/badge.tsx").unlink()
            with mock.patch.object(bt_ui, "UI", ui), mock.patch.object(bt_ui, "SRC", ui / "src"), \
                    mock.patch.object(bt_ui, "THEMES", ui / "themes"):
                second = sync.sync("pictures", self.repo)
        self.assertEqual(second["status"], "committed")
        self.assertNotEqual(second["pool"], first["pool"])
        self.assertNotIn("packages/bitacora-ui/src/components/ui/badge.tsx", self.files_on("main"))
        self.assertEqual((self.repo / "packages/bitacora-ui/src/components/ui/button.tsx").read_text(),
                         "export const Button = () => null;\n")
        self.assertEqual(sync.recorded(self.repo, "main")["pool"], second["pool"])

    def test_dependencies_npm_installs_inside_the_package_survive_a_sync_and_are_never_committed(self):
        sync.sync("pictures", self.repo)
        nested = self.repo / "packages/bitacora-ui/node_modules/framer-motion/package.json"
        nested.parent.mkdir(parents=True)
        nested.write_text('{"version": "12.43.0"}\n')                      # npm could not hoist it (pictures, D-291)
        with tempfile.TemporaryDirectory() as tmp:
            import shutil
            ui = Path(tmp) / "ui"
            shutil.copytree(bt_ui.UI, ui)
            (ui / "src/components/ui/button.tsx").write_text("export const Button = () => null;\n")
            with mock.patch.object(bt_ui, "UI", ui), mock.patch.object(bt_ui, "SRC", ui / "src"), \
                    mock.patch.object(bt_ui, "THEMES", ui / "themes"):
                r = sync.sync("pictures", self.repo)
        self.assertEqual(r["status"], "committed")
        self.assertTrue(nested.is_file())
        self.assertFalse(any("node_modules" in p for p in self.files_on("main")))

    def test_uncommitted_edits_in_the_package_path_are_never_overwritten(self):
        sync.sync("pictures", self.repo)
        edited = self.repo / "packages/bitacora-ui/src/components/ui/button.tsx"
        edited.write_text("// someone's edit\n")
        with self.assertRaises(sync.SyncError) as raised:
            sync.sync("pictures", self.repo)
        self.assertIn("uncommitted changes", str(raised.exception))
        self.assertEqual(edited.read_text(), "// someone's edit\n")

    def test_branch_and_repo_problems_are_refused(self):
        with self.assertRaises(sync.SyncError):
            sync.sync("pictures", self.repo, branch="nope")
        with self.assertRaises(sync.SyncError):
            sync.sync("pictures", self.tmp / "missing-repo")
        with self.assertRaises(sync.SyncError):
            sync.sync("../x", self.repo)

    def test_sync_all_takes_only_opted_in_projects_from_their_project_json(self):
        root = self.tmp / "bitacora"
        (root / "pictures").mkdir(parents=True)
        (root / "other").mkdir()
        (root / "pictures/project.json").write_text(json.dumps(
            {"repos": {"app": {"remote": "", "hint": str(self.repo)}}, "ui": {"sync": True, "repo": "app"}}))
        (root / "other/project.json").write_text(json.dumps({"repos": {}}))
        lines = []
        with mock.patch("bt_core.ROOT", root):
            self.assertEqual(sync.opted_in(root), ["pictures"])
            out = sync.sync_all(lines.append, root=root)
        self.assertEqual(out["pictures"]["status"], "committed")
        self.assertNotIn("other", out)
        self.assertIn("@bitacora/ui → pictures: committed", lines[0])


class Adopt(Fixture):
    """A project built from scratch with a UI uses the pool by default (D-290); existing projects keep the explicit
    opt-in."""

    def setUp(self):
        super().setUp()
        self.root = self.tmp / "bitacora"
        patcher = mock.patch("bt_core.ROOT", self.root)
        patcher.start()
        self.addCleanup(patcher.stop)
        repo_patch = mock.patch("bt_vcs.ensure_repo", lambda _root: None)
        repo_patch.start()
        self.addCleanup(repo_patch.stop)
        import bt_core
        bt_core.ensure_project("fresh")

    def meta(self, project: str = "fresh") -> dict:
        return json.loads((self.root / project / "project.json").read_text())

    def test_a_new_project_adopting_the_pool_gets_the_opt_in_and_its_first_sync(self):
        import bt_workspace
        bt_workspace.add_repo(self.root, "fresh", self.repo, "web")
        r = sync.adopt("fresh", "web", root=self.root)
        self.assertEqual(r["status"], "committed")
        self.assertIsNone(r["theme"])                                   # no tokens: the pool's default theme.css
        self.assertEqual(self.meta()["ui"], {"sync": True, "repo": "web", "push": False})
        self.assertIn("web", self.meta()["repos"])                      # the rest of project.json is kept
        self.assertEqual(sync.recorded(self.repo, "main")["pool"], r["pool"])
        self.assertIn("fresh", sync.opted_in(self.root))
        self.assertEqual(sync.adopt("fresh", root=self.root)["status"], "unchanged")

    def test_opting_in_before_the_repo_exists_is_pending_and_registering_the_repo_does_the_first_sync(self):
        r = sync.adopt("fresh", "web", root=self.root)
        self.assertEqual(r["status"], "pending")
        self.assertEqual(self.meta()["ui"]["sync"], True)
        self.assertFalse((self.repo / "packages").exists())
        import bt_workspace
        bt_workspace.add_repo(self.root, "fresh", self.repo, "api")
        self.assertIsNone(sync.first_sync("fresh", "api", root=self.root))   # not the UI repo
        bt_workspace.add_repo(self.root, "fresh", self.repo, "web")
        first = sync.first_sync("fresh", "web", root=self.root)
        self.assertEqual(first["status"], "committed")
        self.assertIn("packages/bitacora-ui/SYNC.json", self.files_on("main"))
        self.assertIsNone(sync.first_sync("fresh", "web", root=self.root))   # already synced: the merges keep it

    def test_workspace_add_of_the_ui_repo_syncs_a_project_that_opted_in(self):
        sync.adopt("fresh", "web", root=self.root)
        env = {**__import__("os").environ, "BITACORA_ROOT": str(self.root), **ENV}
        done = subprocess.run([sys.executable, str(Path(sync.__file__).parent / "bitacora.py"), "--project", "fresh",
                               "workspace", "add", "web", str(self.repo)], capture_output=True, text=True, env=env)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("@bitacora/ui first sync: committed", done.stdout)
        self.assertIn("packages/bitacora-ui/package.json", self.files_on("main"))

    def test_a_declined_pool_is_recorded_and_never_synced(self):
        import bt_workspace
        self.assertEqual(sync.adopt("fresh", "web", root=self.root, off=True)["status"], "declined")
        self.assertEqual(self.meta()["ui"]["sync"], False)
        bt_workspace.add_repo(self.root, "fresh", self.repo, "web")
        self.assertIsNone(sync.first_sync("fresh", "web", root=self.root))
        self.assertFalse((self.repo / "packages").exists())

    def test_an_existing_project_without_the_key_is_never_synced(self):
        import bt_workspace
        bt_workspace.add_repo(self.root, "fresh", self.repo, "web")
        self.assertNotIn("ui", self.meta())
        self.assertIsNone(sync.first_sync("fresh", "web", root=self.root))
        self.assertEqual(sync.opted_in(self.root), [])
        self.assertFalse((self.repo / "packages").exists())


class Integration(unittest.TestCase):
    """A merge that changes `skill/ui/` writes the pool into the projects after the smoke; other merges do not."""
    setUp, request, run_it = base.Integrate.setUp, base.Integrate.request, base.Integrate.run_it

    def fake(self):
        fake = base.Fake(self)
        fake.synced = []
        fake.sync_ui = lambda live: (fake.synced.append(live), "@bitacora/ui → pictures: committed abc on main")[1]
        return fake

    def test_a_pool_change_syncs_after_a_passing_smoke(self):
        commit(self.wt, "skill/ui/src/components/ui/button.tsx", "export {}\n", "pool change")
        fake = self.fake()
        outcome = self.run_it(fake, regression="none")
        self.assertEqual(outcome.code, 0, outcome.lines)
        self.assertEqual(len(fake.synced), 1)
        self.assertIn("@bitacora/ui → pictures: committed", "\n".join(outcome.lines))

    def test_a_change_outside_the_pool_does_not_sync(self):
        fake = self.fake()
        self.assertEqual(self.run_it(fake, regression="none").code, 0)
        self.assertEqual(fake.synced, [])


if __name__ == "__main__":
    unittest.main()
