"""«Probar» restarts a version clean from the project's recipe and the tab goes to its own URL (REQ-021, owner 2026-10-30)."""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bt_config
import bt_verify_procs as procs
import bt_verify_servers as servers
import bt_verification as verification

RECIPE = {"env_file": "", "env": {"DATABASE_URL": "${TEST_DB}", "BACKEND": "http://127.0.0.1:{port:api}"},
          "prepare": [{"unless": "node_modules", "run": "npm ci"}],
          "servers": [{"name": "api", "port": 8000, "ready": "/healthz", "run": "serve-api --port {port}"},
                      {"name": "web", "port": 3000, "ready": "/", "open": "/3d", "run": "serve-web --port {port}"}]}
ROW = {"id": "SP-1", "state": "to_test", "version": 2, "commit": "a" * 40}


def _state(row=ROW):
    return patch.object(verification, "state", return_value={"subplans": [row]})


class Recipe(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="bt-verify-servers-"))
        self.rdir = self.root / "proj" / "requirements" / "REQ-021-x"
        self.rdir.mkdir(parents=True)

    def write(self, data, where: Path | None = None) -> None:
        ((where or self.root / "proj") / servers.RECIPE).write_text(json.dumps(data))

    def test_a_recipe_needs_named_servers_with_a_command_and_a_port(self):
        self.assertIsNone(servers.recipe(self.root, "proj"))
        self.write({"servers": [{"name": "web", "run": "x"}]})
        self.assertIsNone(servers.recipe(self.root, "proj"))
        self.write(RECIPE)
        self.assertEqual(servers.recipe(self.root, "proj")["servers"][1]["name"], "web")

    def test_a_requirement_recipe_wins_over_the_project_one(self):
        self.write(RECIPE)
        own = {**RECIPE, "env": {"DATABASE_URL": "${REQ_DB}"}}
        self.write(own, self.rdir)
        self.assertEqual(servers.recipe(self.root, "proj", self.rdir)["env"], {"DATABASE_URL": "${REQ_DB}"})
        self.assertEqual(servers.recipe(self.root, "proj")["env"], RECIPE["env"])

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

    def test_the_script_marks_every_process_and_records_each_phase(self):
        paths = servers._files(self.root, "proj", self.rdir, "SP-1", 2)
        script = servers._script(paths, RECIPE, {"api": 8001, "web": 3002}, "proj/REQ-021/SP-1-v2")
        self.assertIn("export BITACORA_VERIFY_ID=proj/REQ-021/SP-1-v2", script)
        self.assertIn("[ -e node_modules ] || { npm ci ; }", script)
        self.assertIn("phase 'prepare 1/1 npm ci'", script)
        self.assertIn("( serve-api --port 8001 )", script)
        self.assertIn("( serve-web --port 3002 )", script)
        self.assertLess(script.index("npm ci"), script.index("phase servers"))
        self.assertLess(script.index("phase servers"), script.index("serve-api"))
        self.assertEqual(servers._url(RECIPE, {"api": 8001, "web": 3002}), "http://localhost:3002/3d")


class Ports(unittest.TestCase):
    def test_a_foreign_listener_is_skipped_and_never_taken(self):
        with tempfile.TemporaryDirectory() as copy, socket.socket() as taken:
            taken.bind(("127.0.0.1", 0))
            taken.listen(1)
            port = taken.getsockname()[1]
            chosen = servers.choose_ports([{"name": "web", "port": port}, {"name": "api", "port": port}], {},
                                          "proj/REQ-1/SP-1-v1", Path(copy), set())
        self.assertNotEqual(chosen["web"], port)
        self.assertNotEqual(chosen["api"], chosen["web"])

    def test_the_versions_own_listener_keeps_its_port_and_a_reserved_one_is_skipped(self):
        table = {3000: {111}, 3001: {222}}
        marks = {111: "proj/REQ-1/SP-1-v1", 222: "proj/REQ-1/SP-2-v1"}
        with patch.object(procs, "environ_mark", side_effect=lambda pid: marks.get(pid, "")), \
                patch.object(procs, "works_in", return_value=False), patch.object(procs, "port_busy", return_value=False):
            own = servers.choose_ports([{"name": "web", "port": 3000}], {}, "proj/REQ-1/SP-1-v1", Path("/c1"), set(), table)
            other = servers.choose_ports([{"name": "web", "port": 3000}], {}, "proj/REQ-1/SP-3-v1", Path("/c3"), {3002}, table)
            earlier = servers.choose_ports([{"name": "web", "port": 3000}], {"web": 3007}, "proj/REQ-1/SP-3-v1", Path("/c3"),
                                           set(), table)
        self.assertEqual(own, {"web": 3000})                  # its own server: stopped, then the same URL again
        self.assertEqual(other, {"web": 3003})                # 3000/3001 other versions, 3002 reserved by a starting one
        self.assertEqual(earlier, {"web": 3007})              # the port it had before: a stable URL


class Start(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="bt-verify-start-"))
        (self.root / "proj").mkdir()
        (self.root / "proj" / servers.RECIPE).write_text(json.dumps(RECIPE))
        self.rdir = self.root / "proj" / "requirements" / "REQ-021-x"
        self.rdir.mkdir(parents=True)
        self.copy = self.root / "verify" / "proj" / "REQ-021" / "SP-1-v2"
        (self.copy / ".next" / "dev").mkdir(parents=True)

    def _start(self, **extra):
        calls = []
        with _state(), patch.object(verification, "open_local", return_value=(self.copy, "ok")), \
                patch.object(verification, "workdir", return_value=self.copy), \
                patch.object(servers, "_dirty", return_value=extra.get("dirty", "")), \
                patch.object(servers, "environment", return_value=({"DATABASE_URL": "x"}, extra.get("missing", []))), \
                patch.object(servers, "choose_ports", return_value={"api": 8001, "web": 3002}), \
                patch.object(servers, "stop_version", side_effect=lambda *a: calls.append("stop") or {41, 42}), \
                patch.object(servers.terminal, "start", side_effect=lambda *a, **k: calls.append(("start",) + a)):
            return servers.start(self.root, "proj", self.rdir, "SP-1"), calls

    def test_every_start_stops_the_version_first_and_starts_it_clean(self):
        started, calls = self._start()
        self.assertTrue(started["ok"], started)
        self.assertEqual(calls[0], "stop")
        self.assertEqual(calls[1][1], "bv-proj-REQ-021-SP-1-v2")
        self.assertEqual(started["url"], "http://localhost:3002/3d")
        self.assertIn("Detuve 2 procesos", started["message"])
        self.assertFalse((self.copy / ".next").exists())                 # no cache from an earlier run
        self.assertEqual(oct(Path(f"{self.copy}.env").stat().st_mode & 0o777), "0o600")
        state = json.loads(Path(f"{self.copy}.servers.json").read_text())
        self.assertEqual((state["phase"], state["ports"], state["mark"]), ("preparing", {"api": 8001, "web": 3002},
                                                                           "proj/REQ-021/SP-1-v2"))
        again, calls = self._start()                                      # a second click: stop, then start again
        self.assertEqual([c if c == "stop" else c[0] for c in calls], ["stop", "start"])

    def test_a_copy_that_is_not_the_published_commit_starts_nothing(self):
        started, calls = self._start(dirty="la copia tiene cambios en src/a.ts")
        self.assertFalse(started["ok"])
        self.assertIn("src/a.ts", started["message"])
        self.assertEqual(calls, ["stop"])
        self.assertEqual(json.loads(Path(f"{self.copy}.servers.json").read_text())["phase"], "failed")

    def test_a_missing_secret_starts_nothing_and_says_which(self):
        started, calls = self._start(missing=["TEST_DB"])
        self.assertFalse(started["ok"])
        self.assertIn("TEST_DB", started["message"])
        self.assertEqual(calls, ["stop"])

    def test_begin_marks_the_restart_before_the_old_servers_could_look_ready(self):
        Path(f"{self.copy}.servers.json").write_text(json.dumps({"phase": "servers", "ports": {"web": 3002},
                                                                  "url": "http://localhost:3002/", "session": "s"}))
        with _state(), patch.object(verification, "workdir", return_value=self.copy), \
                patch.object(servers.threading, "Thread") as thread:
            told = servers.begin(self.root, "proj", self.rdir, "SP-1")
            now = servers.status(self.root, "proj", self.rdir, "SP-1")
        self.assertTrue(told["ok"])
        thread.return_value.start.assert_called_once()
        self.assertEqual(now["state"], "preparing")
        self.assertIn("Deteniendo", now["step"])


class Status(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="bt-verify-status-"))
        self.copy = self.root / "c"
        self.logs = Path(f"{self.copy}.logs")
        self.logs.mkdir(parents=True)

    def now(self, state: dict, answers=None, session=True) -> dict:
        Path(f"{self.copy}.servers.json").write_text(json.dumps({"session": "s", "ports": {"api": 8001, "web": 3002},
                                                                  "ready": {"api": "/healthz", "web": "/"},
                                                                  "url": "http://localhost:3002/", **state}))
        with _state(), patch.object(verification, "workdir", return_value=self.copy), \
                patch.object(servers.terminal, "exists", return_value=session), \
                patch.object(servers.terminal, "screen", return_value=""), \
                patch.object(servers, "_answers", side_effect=lambda url: (answers or {}).get(url, False)):
            return servers.status(self.root, "proj", self.root / "REQ-021-x", "SP-1")

    def test_prepare_steps_then_ready_only_when_every_server_answers(self):
        (self.logs / "phase").write_text("prepare 2/3 npm run build\n")
        self.assertEqual(self.now({"phase": "preparing", "run": "r"})["step"], "Preparando (2 de 3): npm run build")
        (self.logs / "phase").write_text("servers\n")
        answers = {"http://127.0.0.1:8001/healthz": True, "http://127.0.0.1:3002/": False}
        self.assertEqual(self.now({"phase": "preparing", "run": "r"}, answers)["state"], "preparing")
        answers["http://127.0.0.1:3002/"] = True
        self.assertEqual(self.now({"phase": "preparing", "run": "r"}, answers)["state"], "ready")
        self.assertEqual(self.now({"phase": "preparing", "run": "r"}, answers, session=False)["state"], "stopped")

    def test_a_failed_prepare_step_is_reported_with_its_log_not_waited_for(self):
        (self.logs / "phase").write_text("failed npm run rag:migrate\n")
        (self.logs / "prepare.log").write_text("[FAIL] Colisión de número de migración: 039\n")
        now = self.now({"phase": "preparing", "run": "r"})
        self.assertEqual(now["state"], "failed")
        self.assertIn("npm run rag:migrate", now["step"])
        self.assertIn("Colisión", now["log"])

    def test_a_server_that_died_is_reported_with_its_output(self):
        (self.logs / "phase").write_text("servers\n")
        (self.logs / "web.pid").write_text("999999999")
        (self.logs / "web.log").write_text("Another next dev server is already running.\n")
        now = self.now({"phase": "preparing", "run": "r"}, {"http://127.0.0.1:8001/healthz": True})
        self.assertEqual(now["state"], "failed")
        self.assertIn("Another next dev server", now["log"])

    def test_a_start_that_failed_or_was_interrupted_says_so(self):
        self.assertEqual(self.now({"phase": "failed", "error": "Falta TEST_DB"})["step"], "Falta TEST_DB")
        old = self.now({"phase": "stopping", "started_at": time.time() - 3600})
        self.assertEqual(old["state"], "failed")

    def test_servers_started_before_phases_existed_are_probed(self):
        answers = {"http://127.0.0.1:8001/healthz": True, "http://127.0.0.1:3002/": True}
        self.assertEqual(self.now({}, answers)["state"], "ready")         # pictures SP-1/SP-2, started 2026-10-29


class RealProcesses(unittest.TestCase):
    """The script runs for real (bash, no tmux): its prepare fails, then a version's servers are stopped by its mark."""

    def test_a_failing_prepare_writes_its_phase_and_log(self):
        root = Path(tempfile.mkdtemp(prefix="bt-verify-real-"))
        copy = root / "SP-1-v1"
        copy.mkdir()
        paths = {"copy": copy, "env": Path(f"{copy}.env"), "logs": Path(f"{copy}.logs")}
        paths["env"].write_text("")
        recipe = {"prepare": [{"run": "echo preparing; exit 3"}], "servers": [{"name": "web", "port": 1, "run": "true"}]}
        done = subprocess.run(["bash", "-c", servers._script(paths, recipe, {"web": 1}, "p/REQ-1/SP-1-v1")],
                              capture_output=True, text=True, timeout=30)
        self.assertEqual(done.returncode, 1)
        self.assertTrue((paths["logs"] / "phase").read_text().startswith("failed echo preparing"))
        self.assertIn("preparing", (paths["logs"] / "prepare.log").read_text())

    def test_stop_version_stops_the_versions_processes_and_spares_another_versions(self):
        root = Path(tempfile.mkdtemp(prefix="bt-verify-stop-"))
        copy = root / "SP-1-v1"
        copy.mkdir()
        sleeper = [sys.executable, "-c", "import time; time.sleep(60)"]
        mine = subprocess.Popen(["bash", "-c", f"{' '.join(sleeper[:2])} '{sleeper[2]}' & wait"], cwd=root,
                                env={**os.environ, procs.MARK: "p/REQ-1/SP-1-v1"}, start_new_session=True)
        other = subprocess.Popen(sleeper, cwd=root, env={**os.environ, procs.MARK: "p/REQ-1/SP-2-v1"})
        try:
            time.sleep(0.5)
            child = procs.descendants({mine.pid}) - {mine.pid}
            self.assertTrue(child)
            with patch.object(servers.terminal, "exists", return_value=False), patch.object(servers.terminal, "kill"):
                stopped = servers.stop_version({"copy": copy}, "bv-x", "p/REQ-1/SP-1-v1")
            self.assertTrue({mine.pid} | child <= stopped)
            mine.wait(timeout=5)
            self.assertFalse(any(procs.alive(p) for p in child))
            self.assertIsNone(other.poll())                                # another version's process: untouched
        finally:
            for proc in (mine, other):
                proc.kill()


class Panel(unittest.TestCase):
    CTX = {"project": "proj", "rid": "REQ-021", "token": "t", "root": Path("/r"), "rdir": Path("/r/x")}

    def test_the_url_is_shown_as_it_is_and_a_click_on_it_restarts_the_version(self):
        import bt_page_verification as page
        with patch.object(servers, "recipe", return_value=RECIPE), \
                patch.object(servers, "planned", return_value={"url": "http://localhost:3002/", "ports": {"web": 3002}}), \
                patch.object(servers, "status", return_value={"state": "stopped", "url": "", "servers": {}, "log": ""}):
            html = page._servers(dict(self.CTX), ROW)
        self.assertIn('<a class="pp-vurl" href="http://localhost:3002/"', html)
        self.assertIn('data-vstart="vstart-SP-1"', html)
        self.assertIn('<form id="vstart-SP-1" method="post" action="/p/proj/req/REQ-021/verify-run"', html)
        self.assertIn('target="_blank"', html)
        self.assertIn("bv-proj-x-SP-1-v2", html)
        self.assertNotIn("Detener servidores", html)
        self.assertNotIn("data-vport", html)                               # no relay through the panel any more
        with patch.object(servers, "recipe", return_value=None):
            self.assertEqual(page._servers(dict(self.CTX), ROW), "")
        with patch.object(servers, "recipe", return_value=RECIPE), \
                patch.object(servers, "planned", return_value={"url": "http://localhost:3002/", "ports": {"web": 3002}}), \
                patch.object(servers, "status", return_value={"state": "ready", "url": "http://localhost:3002/",
                                                              "ports": {"web": 3002}, "servers": {"web": True}, "log": ""}):
            html = page._servers(dict(self.CTX), ROW)
        self.assertIn("En marcha: responde.", html)
        self.assertIn("Detener servidores", html)

    def test_the_waiting_tab_follows_the_restart_and_goes_to_the_url_itself(self):
        import bt_page_verify_run as wait
        failed = {"state": "failed", "step": "Falló la preparación: npm run rag:migrate", "url": "http://localhost:3002/",
                  "servers": {}, "log": "[FAIL] 039", "ports": {}}
        with patch.object(servers, "status", return_value=failed):
            body = wait.page(Path("/r"), "proj", "REQ-021", Path("/r/x"), "SP-1", "tok")
        self.assertIn('<script src="/static/verify-run.js"></script>', body)       # a file: the panel's CSP refuses inline
        self.assertIn("Falló la preparación: npm run rag:migrate", body)
        self.assertIn("[FAIL] 039", body)
        self.assertIn("Reintentar desde cero", body)
        self.assertIn("http://localhost:3002/", body)
        script = (Path(__file__).resolve().parents[2] / "assets" / "verify-run.js").read_text()
        self.assertIn("location.replace(s.url)", script)
        self.assertIn('closest("a[data-vstart]")', script)
        self.assertNotIn("localhost:\" + ", script)


class UrlsToTest(unittest.TestCase):
    ROWS = [{"how": "1) `npm run dev` and open http://localhost:3000/login, sign in. 2) Open /3d → Añadir.",
             "expect": "Without the flag: sent to /login; account/session stay; see docs/req021/x.md and TCP/IP."}]

    def test_full_local_urls_and_bare_paths_once_each_never_files_or_words(self):
        import bt_page_verification as page
        self.assertEqual(page.test_paths(self.ROWS), ["/login", "/3d"])

    def test_links_point_straight_at_the_running_version_and_are_plain_until_it_runs(self):
        import bt_page_verification as page
        ctx = {"project": "proj", "rid": "REQ-021", "token": "t", "root": Path("/r"), "rdir": Path("/r/x")}
        ready = {"state": "ready", "url": "http://localhost:3002/", "servers": {"web": True}, "log": ""}
        with patch.object(servers, "status", return_value=ready):
            html = page._urls(dict(ctx), ROW, ["/login", "/3d"])
        self.assertIn('<a href="http://localhost:3002/3d" target="_blank"', html)
        self.assertNotIn("data-vport", html)
        with patch.object(servers, "status", return_value={"state": "stopped", "url": "", "servers": {}, "log": ""}):
            html = page._urls(dict(ctx), ROW, ["/login"])
        self.assertIn("<code>/login</code>", html)
        self.assertNotIn("href=", html)


if __name__ == "__main__":
    unittest.main()
