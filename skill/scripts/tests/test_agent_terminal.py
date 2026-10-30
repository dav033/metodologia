import os
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import unquote

import bt_agent_terminal as terminal


@unittest.skipUnless(terminal._tmux_path(), "tmux is not installed")
class RealTmux(unittest.TestCase):
    """Runs a tiny `read` program in a private tmux server: send types into it, screen shows it, kill ends it."""

    def setUp(self):
        patcher = patch.dict(os.environ, {"BITACORA_TMUX_SOCKET": f"bt-test-{os.getpid()}"})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(lambda: terminal._run("kill-server"))

    def test_send_types_into_the_agent_and_screen_shows_the_answer(self):
        name = "bit-test-REQ-1-x"
        terminal.start(name, Path.home(), "read -p 'tu> ' x; echo GOT:$x; sleep 20")
        for _ in range(20):
            if "tu>" in terminal.screen(name):
                break
            time.sleep(0.2)
        self.assertTrue(terminal.exists(name))
        self.assertEqual(terminal.send(name, "hola\ncon salto \u001b[31mrojo"), "Enviado.")
        for _ in range(20):
            if "GOT:" in terminal.screen(name):
                break
            time.sleep(0.2)
        self.assertIn("GOT:hola con salto rojo", terminal.screen(name))
        with self.assertRaises(RuntimeError):
            terminal.start(name, Path.home(), "true")                           # never a second agent under one name
        self.assertTrue(terminal.kill(name))
        self.assertFalse(terminal.exists(name))
        self.assertEqual(terminal.send(name, "hi"), "El agente ya no está en marcha.")

    def test_names_are_validated_and_empty_messages_refused(self):
        self.assertFalse(terminal.exists("bad name; rm -rf"))
        self.assertEqual(terminal.send("bit-x", "   "), "No hay nada que enviar.")
        self.assertEqual(terminal.name_for("pictures", "REQ-021", "planner"), "bit-pictures-REQ-021-planner")


class PlannerStart(unittest.TestCase):
    def test_the_planner_prompt_points_to_resume_and_carries_the_owner_brief(self):
        with tempfile.TemporaryDirectory() as tmp:
            rdir = Path(tmp) / "REQ-021-demo"
            rdir.mkdir()
            (rdir / "PLANNER-PROMPT.md").write_text("BRIEF-TEXT", encoding="utf-8")
            text = terminal.planner_prompt("pictures", rdir)
            self.assertIn("planning resume REQ-021", text)
            self.assertIn("never confirm a subplan or the skeleton for the owner", text)
            self.assertIn("BRIEF-TEXT", text)

    def test_start_planner_refuses_a_second_planner_and_reports_failures(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {"HOME": tmp}):
            rdir = Path(tmp) / "REQ-021-demo"
            rdir.mkdir()
            with patch("bt_agent_terminal.exists", return_value=True):
                self.assertFalse(terminal.start_planner(Path(tmp), "pictures", rdir)[0])
            with patch("bt_agent_terminal.exists", return_value=False), \
                    patch("bt_agent_terminal.start", side_effect=RuntimeError("sin tmux")):
                ok, msg = terminal.start_planner(Path(tmp), "pictures", rdir)
                self.assertEqual((ok, msg), (False, "sin tmux"))


class ScopedStart(unittest.TestCase):
    def test_a_scoped_session_starts_outside_the_callers_service_and_falls_back_without_systemd(self):
        """REQ-031: a tmux server the engine spawns dies with bt-durable.service, which the Solucionador restarts."""
        calls = []

        def run(*args, timeout=15, prefix=()):
            calls.append(prefix)
            return SimpleNamespace(returncode=1 if prefix else 0, stderr="no user manager", stdout="")
        with patch.object(terminal, "_run", side_effect=run), patch.object(terminal, "exists", return_value=False), \
                patch.object(terminal.shutil, "which", return_value="/usr/bin/systemd-run"):
            terminal.start("bit-p-REQ-1-solver", Path("/tmp"), "true", scope="bt-solver-x")
        self.assertEqual(calls[0], ("/usr/bin/systemd-run", "--user", "--scope", "--quiet", "--collect",
                                    "--unit=bt-solver-x"))
        self.assertEqual(calls[1], ())                       # the scope failed: started as before


class SessionEnvironment(unittest.TestCase):
    @unittest.skipUnless(shutil.which("tmux"), "tmux is not installed")
    def test_a_server_the_engine_starts_never_carries_its_database_url_or_its_venv(self):
        """bt-durable.service starts the bitácora tmux server for the Solucionador; every later session on the socket
        gets the server's environment. Real tmux on a private socket (audit of REQ-030, 2026-10-29)."""
        with tempfile.TemporaryDirectory() as tmp:
            out, venv = Path(tmp) / "env.txt", Path(tmp) / "metodologia" / ".venv"
            engine = {"BITACORA_TMUX_SOCKET": f"bt-test-env-{os.getpid()}",
                      "BT_DURABLE_DATABASE_URL": "postgresql://postgres:s3cret@127.0.0.1:5435/bt_durable",
                      "VIRTUAL_ENV": str(venv), "UV_RUN_RECURSION_DEPTH": "1",
                      "PATH": f"{venv}/bin:{os.environ.get('PATH', '/usr/bin')}"}
            with patch.dict(os.environ, engine):
                self.addCleanup(lambda: subprocess.run(["tmux", "-L", engine["BITACORA_TMUX_SOCKET"], "kill-server"],
                                                       capture_output=True, check=False))
                terminal.start("bit-p-REQ-1-solver", Path(tmp), f"env > {out}")
                for _ in range(100):
                    if out.is_file() and out.read_text():
                        break
                    time.sleep(0.05)
            names = dict(line.split("=", 1) for line in out.read_text().splitlines() if "=" in line)
            for name in ("BT_DURABLE_DATABASE_URL", "VIRTUAL_ENV", "UV_RUN_RECURSION_DEPTH"):
                self.assertFalse(name in names, f"{name} reached the session")    # never print the values
            self.assertNotIn(f"{venv}/bin", names.get("PATH", "").split(os.pathsep))


class WebPieces(unittest.TestCase):
    def ctx(self, tmp):
        return {"project": "pictures", "rid": "REQ-021", "rdir": Path(tmp), "token": "tok", "root": Path(tmp),
                "opts": {"sp": ""}, "flow": {"focus": "SP-1"}}

    def test_without_a_planner_the_strip_offers_to_open_one_and_the_say_block_is_hidden(self):
        import bt_page_planning_agent as view
        with tempfile.TemporaryDirectory() as tmp, patch("bt_agent_terminal.exists", return_value=False), \
                patch("bt_presence.sessions", return_value=[]):
            ctx = self.ctx(tmp)
            self.assertIn("agent-start", view.strip(ctx))
            self.assertIn("hidden", view.say(ctx))

    def test_with_a_planner_the_strip_shows_its_screen_and_the_say_block_has_a_box(self):
        import bt_page_planning_agent as view
        with tempfile.TemporaryDirectory() as tmp, patch("bt_agent_terminal.exists", return_value=True), \
                patch("bt_agent_terminal.screen", return_value="Leyendo <SPEC.md>"), patch("bt_presence.sessions", return_value=[]):
            ctx = self.ctx(tmp)
            html, box = view.strip(ctx), view.say(ctx)
            self.assertIn("Planner abierto desde la web", html)
            self.assertIn(">Pantalla<", html)
            self.assertIn(">Reiniciar<", html)
            self.assertIn("Leyendo &lt;SPEC.md&gt;", html)
            self.assertNotIn("agent-start", html)
            self.assertIn("<textarea", box)
            self.assertIn("agent-say", box)
            self.assertNotIn("Leyendo", box)                  # the box never changes with the screen, so it is never swapped mid-typing

    def test_the_server_action_types_into_the_right_agent_only_from_loopback(self):
        import bt_server
        with tempfile.TemporaryDirectory() as tmp:
            rdir = Path(tmp) / "REQ-021-demo"
            rdir.mkdir()
            call = lambda who, form, action="agent-say": bt_server.Handler.agent_post(  # noqa: E731
                SimpleNamespace(client_address=(who, 1)), "pictures", "REQ-021", rdir, action, form, "/p/pictures/req/REQ-021")
            with patch.object(bt_server, "ROOT", Path(tmp)), patch("bt_agent_terminal.send", return_value="Enviado.") as send:
                self.assertIn("solo se manejan desde esta máquina", unquote(call("203.0.113.9", {"kind": "planner", "text": "hola"})))
                send.assert_not_called()
                self.assertIn("msg=Enviado.", call("127.0.0.1", {"kind": "planner", "text": "sigue con SP-1"}))
                send.assert_called_once_with("bit-pictures-REQ-021-planner", "sigue con SP-1")
                self.assertIn("No encuentro ese agente", unquote(call("127.0.0.1", {"kind": "session", "anchor": "SP-3", "text": "x"})))
                self.assertIn("No encuentro ese agente", unquote(call("127.0.0.1", {"kind": "../x", "text": "x"})))
            events = (rdir / ".planning" / "activity.jsonl").read_text(encoding="utf-8")
            self.assertIn("Le escribiste al Planner", events)
            self.assertIn("sigue con SP-1", events)


if __name__ == "__main__":
    unittest.main()
