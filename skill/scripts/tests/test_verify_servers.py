"""«Probar esta versión» starts a version's test servers from the project's recipe and the tab goes to it (REQ-021)."""
from __future__ import annotations

import json
import socket
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bt_config
import bt_verify_servers as servers
import bt_verification as verification

RECIPE = {"env_file": "", "env": {"DATABASE_URL": "${TEST_DB}", "BACKEND": "http://127.0.0.1:{port:api}"},
          "prepare": [{"unless": "node_modules", "run": "npm ci"}],
          "servers": [{"name": "api", "port": 8000, "ready": "/healthz", "run": "serve-api --port {port}"},
                      {"name": "web", "port": 3000, "ready": "/", "open": "/3d", "run": "serve-web --port {port}"}]}
ROW = {"id": "SP-1", "state": "to_test", "version": 2, "commit": "a" * 40}


class Recipe(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="bt-verify-servers-"))
        (self.root / "proj").mkdir()
        self.rdir = self.root / "proj" / "requirements" / "REQ-021-x"
        self.rdir.mkdir(parents=True)

    def write(self, data) -> None:
        (self.root / "proj" / servers.RECIPE).write_text(json.dumps(data))

    def test_a_recipe_needs_named_servers_with_a_command_and_a_port(self):
        self.assertIsNone(servers.recipe(self.root, "proj"))
        self.write({"servers": [{"name": "web", "run": "x"}]})
        self.assertIsNone(servers.recipe(self.root, "proj"))
        self.write(RECIPE)
        self.assertEqual(servers.recipe(self.root, "proj")["servers"][1]["name"], "web")

    def test_a_busy_port_moves_to_the_next_free_one(self):
        with socket.socket() as taken:
            taken.bind(("127.0.0.1", 0))
            taken.listen(1)
            port = taken.getsockname()[1]
            chosen = servers._ports([{"name": "web", "port": port}, {"name": "api", "port": port}])
        self.assertNotEqual(chosen["web"], port)
        self.assertNotEqual(chosen["api"], chosen["web"])

    def test_the_environment_fills_ports_and_secrets_and_names_a_missing_secret(self):
        with tempfile.TemporaryDirectory() as tmp:
            secrets = Path(tmp) / "secrets.env"
            secrets.write_text("TEST_DB=postgresql://t:pw@127.0.0.1:1/test\n")
            real = bt_config.get
            with patch.object(bt_config, "get", side_effect=lambda key, default=None:
                              [str(secrets)] if key == "verifier.secret_files" else real(key, default)):
                env, missing = servers.environment("proj", RECIPE, {"api": 8001, "web": 3002})
                self.assertEqual((env["DATABASE_URL"], env["BACKEND"], missing),
                                 ("postgresql://t:pw@127.0.0.1:1/test", "http://127.0.0.1:8001", []))
                _env, missing = servers.environment("proj", {**RECIPE, "env": {"X": "${ABSENT}"}}, {})
                self.assertEqual(missing, ["ABSENT"])

    def test_the_script_prepares_then_starts_every_server_on_its_port(self):
        paths = servers._files(self.root, "proj", self.rdir, "SP-1", 2)
        script = servers._script(paths, RECIPE, {"api": 8001, "web": 3002})
        self.assertIn("[ -e node_modules ] || npm ci", script)
        self.assertIn("( serve-api --port 8001 )", script)
        self.assertIn("( serve-web --port 3002 )", script)
        self.assertLess(script.index("npm ci"), script.index("serve-api"))
        self.assertEqual(servers._url(RECIPE, {"api": 8001, "web": 3002}), "http://localhost:3002/3d")

    def test_start_opens_the_copy_starts_one_session_and_reuses_it(self):
        self.write(RECIPE)
        copy = self.root / "verify" / "proj" / "REQ-021" / "SP-1-v2"
        copy.mkdir(parents=True)
        with patch.object(verification, "open_local", return_value=(copy, "ok")), \
                patch.object(verification, "state", return_value={"subplans": [ROW]}), \
                patch.object(verification, "workdir", return_value=copy), \
                patch.object(servers, "environment", return_value=({"DATABASE_URL": "x"}, [])), \
                patch.object(servers, "_ports", return_value={"api": 8001, "web": 3002}), \
                patch.object(servers.terminal, "exists", return_value=False), \
                patch.object(servers.terminal, "start") as start:
            started = servers.start(self.root, "proj", self.rdir, "SP-1")
        self.assertTrue(started["ok"], started)
        self.assertEqual(started["url"], "http://localhost:3002/3d")
        self.assertEqual(start.call_args.args[0], "bv-proj-REQ-021-SP-1-v2")
        env_file = Path(f"{copy}.env")
        self.assertEqual(oct(env_file.stat().st_mode & 0o777), "0o600")
        with patch.object(verification, "open_local", return_value=(copy, "ok")), \
                patch.object(verification, "state", return_value={"subplans": [ROW]}), \
                patch.object(verification, "workdir", return_value=copy), \
                patch.object(servers.terminal, "exists", return_value=True), patch.object(servers.terminal, "start") as again:
            reused = servers.start(self.root, "proj", self.rdir, "SP-1")
        again.assert_not_called()
        self.assertEqual(reused["url"], "http://localhost:3002/3d")

    def test_a_missing_secret_starts_nothing(self):
        self.write(RECIPE)
        copy = self.root / "c"
        copy.mkdir()
        with patch.object(verification, "open_local", return_value=(copy, "ok")), \
                patch.object(verification, "state", return_value={"subplans": [ROW]}), \
                patch.object(verification, "workdir", return_value=copy), \
                patch.object(servers, "environment", return_value=({}, ["TEST_DB"])), \
                patch.object(servers.terminal, "exists", return_value=False), patch.object(servers.terminal, "start") as start:
            started = servers.start(self.root, "proj", self.rdir, "SP-1")
        self.assertFalse(started["ok"])
        self.assertIn("TEST_DB", started["message"])
        start.assert_not_called()

    def test_status_is_ready_only_when_every_server_answers(self):
        copy = self.root / "c"
        Path(f"{copy}.servers.json").write_text(json.dumps({"ports": {"api": 8001, "web": 3002}, "url": "http://localhost:3002/",
                                                            "ready": {"api": "/healthz", "web": "/"}}))
        answers = {"http://127.0.0.1:8001/healthz": True, "http://127.0.0.1:3002/": False}
        with patch.object(verification, "state", return_value={"subplans": [ROW]}), \
                patch.object(verification, "workdir", return_value=copy), \
                patch.object(servers.terminal, "exists", return_value=True), \
                patch.object(servers.terminal, "screen", return_value="[bitácora] web en el puerto 3002"), \
                patch.object(servers, "_answers", side_effect=lambda url: answers[url]):
            self.assertEqual(servers.status(self.root, "proj", self.rdir, "SP-1")["state"], "preparing")
            answers["http://127.0.0.1:3002/"] = True
            self.assertEqual(servers.status(self.root, "proj", self.rdir, "SP-1")["state"], "ready")
        with patch.object(verification, "state", return_value={"subplans": [ROW]}), \
                patch.object(verification, "workdir", return_value=copy), \
                patch.object(servers.terminal, "exists", return_value=False):
            self.assertEqual(servers.status(self.root, "proj", self.rdir, "SP-1")["state"], "stopped")


class Strays(unittest.TestCase):
    def test_only_a_server_listening_inside_the_copy_is_stopped(self):
        import subprocess
        import time
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "copy"
            copy.mkdir()
            server = subprocess.Popen([sys.executable, "-m", "http.server", "0", "--bind", "127.0.0.1"], cwd=copy,
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            editor = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"], cwd=copy)
            try:
                for _ in range(50):
                    if server.pid in self._listeners(copy):
                        break
                    time.sleep(0.1)
                stopped = servers._stop_strays(copy)
                server.wait(timeout=5)
                self.assertIn(server.pid, stopped)
                self.assertIsNone(editor.poll())                 # not a server: left alone
            finally:
                for proc in (server, editor):
                    proc.kill()

    @staticmethod
    def _listeners(copy: Path) -> list[int]:
        import os
        inodes = servers._listening_inodes()
        found = []
        for proc in Path("/proc").glob("[0-9]*"):
            try:
                if os.readlink(proc / "cwd") == str(copy.resolve()) and any(
                        os.readlink(fd)[8:-1] in inodes for fd in (proc / "fd").iterdir()
                        if os.readlink(fd).startswith("socket:[")):
                    found.append(int(proc.name))
            except OSError:
                continue
        return found

    def test_a_server_that_died_is_reported_with_its_output(self):
        root = Path(tempfile.mkdtemp(prefix="bt-verify-dead-"))
        copy = root / "c"
        logs = Path(f"{copy}.logs")
        logs.mkdir(parents=True)
        (logs / "web.pid").write_text("999999999")
        (logs / "web.log").write_text("Another next dev server is already running.\n")
        Path(f"{copy}.servers.json").write_text(json.dumps({"ports": {"web": 3002}, "url": "http://localhost:3002/"}))
        with patch.object(verification, "state", return_value={"subplans": [ROW]}), \
                patch.object(verification, "workdir", return_value=copy), \
                patch.object(servers.terminal, "exists", return_value=True), \
                patch.object(servers, "_answers", return_value=False):
            now = servers.status(root, "proj", root / "REQ-021-x", "SP-1")
        self.assertEqual(now["state"], "failed")
        self.assertIn("Another next dev server", now["log"])


class Panel(unittest.TestCase):
    def test_the_button_opens_a_new_tab_and_the_wait_page_goes_to_the_version(self):
        import bt_page_verification as page
        import bt_page_verify_run as wait
        ctx = {"project": "proj", "rid": "REQ-021", "token": "t", "root": Path("/r"), "rdir": Path("/r/x")}
        with patch.object(servers, "recipe", return_value=RECIPE), \
                patch.object(servers, "status", return_value={"state": "stopped", "url": "", "servers": {}, "log": ""}):
            html = page._servers(ctx, ROW)
        self.assertIn('action="/p/proj/req/REQ-021/verify-run"', html)
        self.assertIn('target="_blank"', html)
        with patch.object(servers, "recipe", return_value=None):
            self.assertEqual(page._servers(ctx, ROW), "")
        with patch.object(servers, "status", return_value={"state": "ready", "url": "http://localhost:3002/",
                                                           "servers": {"web": True}, "log": ""}):
            html = page._servers({**ctx}, ROW) if servers.recipe(ctx["root"], "proj") else ""
            body = wait.page(Path("/r"), "proj", "REQ-021", Path("/r/x"), "SP-1")
        self.assertIn('<script src="/static/verify-run.js"></script>', body)       # a file: the panel's CSP refuses inline
        script = (Path(__file__).resolve().parents[2] / "assets" / "verify-run.js").read_text()
        self.assertIn("location.replace(viaPanel(", script)
        self.assertIn("Lista: abriendo la versión", body)


if __name__ == "__main__":
    unittest.main()


class UrlsToTest(unittest.TestCase):
    ROWS = [{"how": "1) `npm run dev` and open http://localhost:3000/login, sign in. 2) Open /3d → Añadir.",
             "expect": "Without the flag: sent to /login; account/session stay; see docs/req021/x.md and TCP/IP."}]

    def test_full_local_urls_and_bare_paths_once_each_never_files_or_words(self):
        import bt_page_verification as page
        self.assertEqual(page.test_paths(self.ROWS), ["/login", "/3d"])

    def test_links_point_at_the_running_version_and_are_plain_until_it_runs(self):
        import bt_page_verification as page
        ctx = {"project": "proj", "rid": "REQ-021", "token": "t", "root": Path("/r"), "rdir": Path("/r/x")}
        ready = {"state": "ready", "url": "http://localhost:3002/", "servers": {"web": True}, "log": ""}
        with patch.object(servers, "status", return_value=ready):
            html = page._urls(dict(ctx), ROW, ["/login", "/3d"])
        self.assertIn('data-vport="3002" data-vpath="/3d"', html)                  # verify-run.js sends it through the panel
        self.assertIn("puerto 3002", html)
        with patch.object(servers, "status", return_value={"state": "stopped", "url": "", "servers": {}, "log": ""}):
            html = page._urls(dict(ctx), ROW, ["/login"])
        self.assertIn("<code>/login</code>", html)
        self.assertNotIn("href=", html)
