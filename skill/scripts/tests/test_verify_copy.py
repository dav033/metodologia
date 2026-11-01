"""«Probar» on a copy left at an older publication of the same version moves it to the published commit (D-278).

Owner evidence, pictures REQ-021, 2026-10-31: «…/SP-2-v2 existe pero no está en el commit publicado; ciérralo primero».
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bt_page_verification as page
import bt_verification as v
import bt_verify_copy as copy
import bt_verify_servers as servers

PLAN = {"subplans": [{"id": "SP-1", "title": "One"}], "tasks": [{"id": "T1", "subplan_id": "SP-1"}]}
SPEC = "# REQ-9\n\n## Pruebas\n| Subplan | Dónde | Cómo | Qué debes ver |\n|---|---|---|---|\n| SP-1 | Local | x | y |\n"
RECIPE = {"prepare": [{"unless": "node_modules", "run": "npm ci"}],
          "servers": [{"name": "web", "port": 3000, "ready": "/", "open": "/", "run": "serve --port {port}"}]}


def git(repo, *args):
    env = {k: val for k, val in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=env, check=True).stdout.strip()


class StaleCopy(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.rdir = self.root / "proj" / "requirements" / "REQ-009-demo"
        self.rdir.mkdir(parents=True)
        (self.rdir / "SPEC.md").write_text(SPEC, encoding="utf-8")
        (self.rdir / "PLAN.json").write_text(json.dumps(PLAN), encoding="utf-8")
        self.repo = self.root / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q")
        (self.repo / ".gitignore").write_text("node_modules/\n")
        (self.repo / "a.txt").write_text("one")
        (self.repo / "package-lock.json").write_text("{}")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-qm", "first publication of SP-1 v2")
        self.old = git(self.repo, "rev-parse", "HEAD")
        (self.repo / "a.txt").write_text("two")
        git(self.repo, "commit", "-qam", "accepted work landed on the line")
        self.new = git(self.repo, "rev-parse", "HEAD")
        os.environ["BITACORA_VERIFY_DIR"] = str(self.root / "verify")
        self.addCleanup(os.environ.pop, "BITACORA_VERIFY_DIR", None)
        for patcher in (patch("bt_workspace.repos", return_value={"app": self.repo}),
                        patch.object(servers.terminal, "exists", return_value=False),     # never the real tmux
                        patch.object(servers.terminal, "kill", return_value=False)):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.publish(self.old)
        self.target, _ = v.open_local(self.root, "proj", self.rdir, "SP-1")
        (self.target / "node_modules").mkdir()
        (self.target / "node_modules" / "dep.js").write_text("installed")
        self.publish(self.new)                                # same «versión 2», a newer commit

    def publish(self, commit):
        rows = [{"id": "SP-1", "status": "published", "version": 2, "commit": commit}]
        (self.rdir / v.PROJECTION).write_text(json.dumps({"subplans": rows}), encoding="utf-8")

    def activity(self) -> list[str]:
        log = self.rdir / ".planning" / "activity.jsonl"
        return [json.loads(line)["text"] for line in log.read_text().splitlines()] if log.exists() else []

    def spawn(self, mark: str = "") -> subprocess.Popen:
        env = {**os.environ, **({"BITACORA_VERIFY_ID": mark} if mark else {})}
        proc = subprocess.Popen(["sleep", "60"], cwd=self.target, env=env)
        self.addCleanup(lambda: (proc.poll() is None and proc.kill(), proc.wait()))
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and not Path(f"/proc/{proc.pid}/environ").read_bytes():
            time.sleep(0.02)
        return proc

    def test_a_clean_copy_at_an_older_publication_is_moved_and_opened(self):
        target, msg = v.open_local(self.root, "proj", self.rdir, "SP-1")
        self.assertEqual(target, self.target)
        self.assertEqual(git(target, "rev-parse", "HEAD"), self.new)
        self.assertEqual((target / "a.txt").read_text(), "two")
        self.assertIn(f"commit anterior ({self.old[:7]})", msg)
        self.assertIn(f"versión 2 (commit {self.new[:7]})", msg)
        self.assertTrue((target / "node_modules" / "dep.js").exists())     # same lockfile: dependencies kept
        self.assertEqual(self.activity(), [(f"la copia de SP-1 v2 estaba en un commit anterior ({self.old[:7]}); "
                                            f"se movió al publicado ({self.new[:7]})")])
        self.assertEqual(git(self.repo, "rev-parse", "HEAD"), self.new)     # the repo's own checkout never moved

    def test_a_changed_lockfile_drops_the_old_dependencies_as_on_a_fresh_copy(self):
        (self.repo / "package-lock.json").write_text('{"x": 1}')
        git(self.repo, "commit", "-qam", "dependency bump")
        newer = git(self.repo, "rev-parse", "HEAD")
        self.publish(newer)
        target, _ = v.open_local(self.root, "proj", self.rdir, "SP-1")
        self.assertEqual(git(target, "rev-parse", "HEAD"), newer)
        self.assertFalse((target / "node_modules").exists())               # prepare's `unless: node_modules` reinstalls

    def test_a_server_of_the_old_copy_is_stopped_before_the_move(self):
        server = self.spawn(mark="proj/REQ-009/SP-1-v2")
        (Path(f"{self.target}.servers.json")).write_text(json.dumps({"phase": "servers", "commit": self.old}))
        target, msg = v.open_local(self.root, "proj", self.rdir, "SP-1")
        self.assertEqual(git(target, "rev-parse", "HEAD"), self.new, msg)
        self.assertIsNotNone(server.poll())                                # the stale server is gone
        self.assertIn("Detuve 1 procesos", msg)
        self.assertEqual(json.loads(Path(f"{self.target}.servers.json").read_text())["phase"], "stopped")

    def test_probar_stops_the_stale_servers_and_restarts_on_the_published_commit(self):
        (self.root / "proj" / servers.RECIPE).write_text(json.dumps(RECIPE))
        calls = []
        with patch.object(servers, "environment", return_value=({}, [])), \
                patch.object(servers, "choose_ports", return_value={"web": 3002}), \
                patch.object(servers, "stop_version", side_effect=lambda *a: calls.append("stop") or {41}), \
                patch.object(servers.terminal, "start", side_effect=lambda name, cwd, cmd: calls.append(("start", cwd))):
            started = servers.start(self.root, "proj", self.rdir, "SP-1")
        self.assertTrue(started["ok"], started)
        self.assertEqual(calls, ["stop", ("start", self.target)])
        self.assertEqual(git(self.target, "rev-parse", "HEAD"), self.new)
        self.assertIn(f"versión 2 (commit {self.new[:7]})", started["message"])
        self.assertEqual(json.loads(Path(f"{self.target}.servers.json").read_text())["commit"], self.new)

    def test_edits_refuse_with_the_file_list_and_the_owner_chooses(self):
        (self.target / "a.txt").write_text("my edit")
        (self.target / "nuevo.txt").write_text("new")
        target, msg = v.open_local(self.root, "proj", self.rdir, "SP-1")
        self.assertIsNone(target)
        self.assertIn("a.txt (modificado), nuevo.txt (nuevo)", msg)
        self.assertNotIn("node_modules", msg)                              # ignored output is not an edit
        self.assertIn("«Descartar los cambios»", msg)
        self.assertIn("«Guardar la copia aparte»", msg)
        self.assertEqual(git(self.target, "rev-parse", "HEAD"), self.old)  # nothing moved, nothing lost
        self.assertEqual((self.target / "a.txt").read_text(), "my edit")
        html = page._stale({"project": "proj", "rid": "REQ-009", "token": "t"},
                           {"id": "SP-1", "version": 2, "commit": self.new}, self.target)
        self.assertIn("verify-discard", html)
        self.assertIn("verify-keep", html)
        told = copy.keep_aside(self.root, "proj", self.rdir, "SP-1")
        kept = self.target.with_name(f"SP-1-v2-kept-{self.old[:7]}")
        self.assertEqual((kept / "a.txt").read_text(), "my edit", told)
        self.assertTrue((kept / "nuevo.txt").exists())
        self.assertEqual(git(self.target, "rev-parse", "HEAD"), self.new)
        self.assertIn("Listo: guardaste la copia", told)
        from bt_durable import gc_verify
        kinds = {c.slug: c.kind for c in gc_verify.inventory(self.root / "verify")}
        self.assertEqual(kinds[kept.name], "unknown")                       # the disk pass never collects it

    def test_discard_drops_the_edits_and_opens_the_published_commit(self):
        (self.target / "a.txt").write_text("my edit")
        told = copy.discard(self.root, "proj", self.rdir, "SP-1")
        self.assertIn("descartaste los cambios", told)
        self.assertIn("a.txt (modificado)", told)
        self.assertEqual(git(self.target, "rev-parse", "HEAD"), self.new)
        self.assertEqual((self.target / "a.txt").read_text(), "two")

    def test_a_foreign_process_inside_the_copy_refuses_naming_it(self):
        shell = self.spawn()
        target, msg = v.open_local(self.root, "proj", self.rdir, "SP-1")
        self.assertIsNone(target)
        self.assertIn(f"pid {shell.pid} (sleep)", msg)
        self.assertIsNone(shell.poll())                                     # not the version's: never killed
        self.assertEqual(git(self.target, "rev-parse", "HEAD"), self.old)

    def test_a_copy_at_the_published_commit_is_left_as_it_is(self):
        self.publish(self.old)
        with patch.object(servers, "halt", side_effect=AssertionError("nothing to stop")):
            target, msg = v.open_local(self.root, "proj", self.rdir, "SP-1")
        self.assertEqual((target, msg), (self.target, f"Ya estaba abierto en {self.target}."))
        self.assertEqual(git(target, "rev-parse", "HEAD"), self.old)
        self.assertTrue((target / "node_modules" / "dep.js").exists())
        self.assertEqual(self.activity(), [])
        self.assertIsNone(copy.stale(self.target, {"commit": self.old}))


if __name__ == "__main__":
    unittest.main()
