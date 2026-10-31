import contextlib
import io
import os
import shlex
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

    def test_a_message_left_as_a_paste_is_submitted_again(self):
        """D-199: Codex keeps a long text as «[Pasted Content N chars]» until a second Enter; send said «Enviado» anyway."""
        name = "bit-test-REQ-1-paste"
        terminal.start(name, Path.home(), "read -p '› ' x; echo '› [Pasted Content 40 chars]'; read y; echo GOT:$x; echo '› '; sleep 20")
        for _ in range(20):
            if "›" in terminal.screen(name):
                break
            time.sleep(0.2)
        self.assertEqual(terminal.send(name, "a long message for the planner"), "Enviado.")
        self.assertIn("GOT:a long message for the planner", terminal.screen(name))

    def test_unsent_reads_only_the_input_box(self):
        self.assertTrue(terminal.unsent("• working\n› [Pasted Content 1020 chars]\n  GPT-6.1-Sol low", "x"))
        self.assertTrue(terminal.unsent("› Plan defect found by the operator (2026", "Plan defect found by the operator (2026-10-30)"))
        self.assertFalse(terminal.unsent("› Plan defect found\n• Aye, revisaré\n› Ask Codex to do anything", "Plan defect found"))
        self.assertFalse(terminal.unsent("› [Pasted Content 40 chars]\nGOT:x\n› ", "x"))

    def test_names_are_validated_and_empty_messages_refused(self):
        self.assertFalse(terminal.exists("bad name; rm -rf"))
        self.assertEqual(terminal.send("bit-x", "   "), "No hay nada que enviar.")
        self.assertEqual(terminal.name_for("pictures", "REQ-021", "planner"), "bit-pictures-REQ-021-planner")


WALL = ("■ You've hit your usage limit. Upgrade to Pro (https://chatgpt.com/explore/pro), visit "
        "https://chatgpt.com/codex/settings/usage to purchase more credits or try again at 4:32 PM.")
MODAL = """  Approaching rate limits
  Switch to gpt-6-luna for lower credit usage?

› 1. Switch to gpt-6-luna
  2. Keep current model
  3. Keep current model (never show again)

  enter select · esc back"""


def fake_codex(folder: Path, *steps: str) -> str:
    """A shell stand-in for the Codex TUI. Each step reads one message at the «› » prompt and logs it, then:
    `wall` answers it with Codex's exact quota text, `ok` echoes GOT:<message>; `modal` first shows the rate-limit
    modal and takes single keys like Codex's list (Enter picks the highlighted «Switch», a digit picks that option),
    logging the choice and clearing the window."""
    log = folder / "codex.log"
    lines = ["#!/bin/bash"]
    for step in steps:
        if step == "modal":
            lines += [f"cat <<'EOF'\n{MODAL}\nEOF",
                      "while IFS= read -rsn1 k; do case \"$k\" in",
                      f"  2) echo KEEP >> {log}; break;; 3) echo NEVER >> {log}; break;;",
                      f"  1|'') echo SWITCH >> {log}; break;; esac; done", "printf '\\033[2J\\033[H'"]
            continue
        lines += [f"read -rp '› ' x; echo \"MSG:$x\" >> {log}"]
        lines += [f"echo {shlex.quote(WALL)}" if step == "wall" else 'echo "GOT:$x"']
    lines += ["echo '› '", "sleep 60"]
    script = folder / "codex.sh"
    script.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return f"bash {script}"


def wait_for(name: str, text: str, tries: int = 40) -> str:
    for _ in range(tries):
        shown = terminal.screen(name, 60)
        if text in shown:
            return shown
        time.sleep(0.15)
    return terminal.screen(name, 60)


@unittest.skipUnless(terminal._tmux_path(), "tmux is not installed")
class AgentWalls(unittest.TestCase):
    """pictures REQ-021, 2026-10-30: `tell-planner` said «Enviado al Planner.» while the Planner's Codex account answered
    «You've hit your usage limit … try again at 4:32 PM»; later Codex's model-switch modal took every notice."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        patcher = patch.dict(os.environ, {"BITACORA_TMUX_SOCKET": f"bt-test-wall-{os.getpid()}"})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(lambda: terminal._run("kill-server"))

    def log(self) -> list[str]:
        path = self.tmp / "codex.log"
        return path.read_text(encoding="utf-8").splitlines() if path.is_file() else []

    def test_a_quota_wall_that_answers_the_message_is_not_reported_as_sent(self):
        name = "bit-test-REQ-1-wall"
        terminal.start(name, self.tmp, fake_codex(self.tmp, "wall"))
        wait_for(name, "›")
        said = terminal.send(name, "Plan change request: add the 039 migration")
        self.assertNotEqual(said, "Enviado.")
        self.assertEqual(said.state, "limited")
        self.assertIn("sin cuota", said)
        self.assertGreater(said.until, time.time())
        self.assertEqual(time.strftime("%H:%M", time.localtime(said.until)), "16:32")
        self.assertIn("MSG:Plan change request: add the 039 migration", self.log())

    def test_a_message_that_quotes_a_wall_is_still_sent(self):
        name = "bit-test-REQ-1-quote"
        terminal.start(name, self.tmp, fake_codex(self.tmp, "ok"))
        wait_for(name, "›")
        said = terminal.send(name, "Codex said «You've hit your usage limit» to the operator; plan for it")
        self.assertEqual((said, said.state), ("Enviado.", "sent"))

    def test_the_model_switch_modal_is_answered_keep_current_model_and_the_message_arrives(self):
        name = "bit-test-REQ-1-modal"
        terminal.start(name, self.tmp, fake_codex(self.tmp, "modal", "ok"))
        wait_for(name, "enter select")
        said = terminal.send(name, "SP-8 confirmado")
        self.assertEqual(said, "Enviado.")
        self.assertEqual(self.log()[0], "KEEP")                 # never Switch, never «never show again»
        self.assertIn("MSG:SP-8 confirmado", self.log())
        self.assertIn("GOT:SP-8 confirmado", wait_for(name, "GOT:"))
        self.assertTrue(any("Keep current model" in a for a in said.answered))

    def test_an_unknown_selection_list_is_never_typed_into(self):
        name = "bit-test-REQ-1-list"
        terminal.start(name, self.tmp, "printf '  Pick one\\n› 1. Yes\\n  2. No\\n\\n  enter select · esc back\\n'; "
                       f"read -rsn1 k; echo \"KEY:$k\" >> {self.tmp / 'codex.log'}; sleep 30")
        wait_for(name, "enter select")
        said = terminal.send(name, "hola")
        self.assertEqual(said.state, "blocked")
        time.sleep(0.3)
        self.assertEqual(self.log(), [])

    def test_a_planner_without_quota_anywhere_holds_the_notice_and_delivers_it_after_the_reset(self):
        import bt_core
        import bt_planner_notices as notices
        rdir = self.tmp / "pictures" / "requirements" / "REQ-021-demo"
        (rdir / ".planning").mkdir(parents=True)
        (rdir / terminal.RECORD).write_text('{"provider": "codex", "codex_home": "/acc/codex-luis"}')
        name = terminal.name_for("pictures", "REQ-021", "planner")
        terminal.start(name, self.tmp, fake_codex(self.tmp, "wall", "ok"))
        wait_for(name, "›")
        spent = {"provider": "claude", "home": "", "model": "opus", "effort": "high", "exhausted": "1", "until": ""}
        with patch.object(bt_core, "ROOT", self.tmp), patch.object(terminal, "planner_route", return_value=spent), \
                patch.object(terminal, "start_planner") as start:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(terminal.main(["tell-planner", "pictures", "REQ-021", "add the 039 migration"]), 3)
            self.assertNotIn("Enviado", out.getvalue())
            self.assertIn("sin cuota y ninguna otra cuenta tiene: guardé el mensaje y se lo reenvío solo", out.getvalue())
            [kept] = terminal.wall.held(rdir)
            self.assertIn("add the 039 migration", kept["text"])
            self.assertEqual(time.strftime("%H:%M", time.localtime(kept["due"])), "16:32")
            self.assertEqual(notices.deliver_held(self.tmp, now=kept["due"] - 60), [])    # not before the reset
            said = notices.deliver_held(self.tmp, now=kept["due"] + 1)
        start.assert_not_called()
        self.assertEqual(said, ["pictures/REQ-021: held notice sent"])
        self.assertEqual(terminal.wall.held(rdir), [])
        self.assertEqual([m for m in self.log() if "039" in m], [f"MSG:{kept['text']}"] * 2)
        self.assertIn("GOT:[Automatic notice", wait_for(name, "GOT:"))


def fake_agent(folder: Path, *, exits: bool) -> str:
    """A stand-in agent: logs its arguments, shows a «› » prompt and logs each message it reads; `exits` quits at once
    like pictures REQ-021's Planner Codex at 09:53 on 2026-10-31, leaving `start`'s `exec bash` shell in the window."""
    script = folder / ("gone.sh" if exits else "agent.sh")
    log = folder / "agent.log"
    body = ["#!/bin/bash", f'printf "ARGS:%s\\n" "$*" >> {log}']
    body += ["echo 'agent: session ended'", "exit 0"] if exits else \
        ["while true; do read -rp '› ' x || exit; echo \"MSG:$x\" >> " + str(log) + "; echo \"GOT:$x\"; done"]
    script.write_text("\n".join(body) + "\n", encoding="utf-8")
    return f"bash {script}"


class DeadPaneBase(unittest.TestCase):
    """pictures REQ-021, 2026-10-31: the Planner's Codex exited at 09:53 and its pane fell back to `start`'s shell; at
    09:57 `tell-planner` printed «Enviado al Planner.» and the plan change request sat typed at the shell prompt, where
    one more Enter runs it as a command. Real tmux on a private socket, never `-L bitacora`."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        patcher = patch.dict(os.environ, {"BITACORA_TMUX_SOCKET": f"bt-test-dead-{os.getpid()}"})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(lambda: terminal._run("kill-server"))
        self.pwned = self.tmp / "pwned"
        self.trap = f"echo PWNED > {self.pwned} #"       # what a shell would do with the text: create this file

    def shell(self, name: str) -> None:
        terminal.start(name, self.tmp, fake_agent(self.tmp, exits=True))
        for _ in range(50):
            if "session ended" in terminal.screen(name):
                time.sleep(0.5)                           # the interactive shell's prompt, as the owner saw it at 10:12
                return
            time.sleep(0.1)
        self.fail("the fake agent never left its shell: " + terminal.screen(name))

    def log(self) -> list[str]:
        path = self.tmp / "agent.log"
        return path.read_text(encoding="utf-8").splitlines() if path.is_file() else []


@unittest.skipUnless(terminal._tmux_path(), "tmux is not installed")
class DeadPane(DeadPaneBase):
    def test_the_agent_state_tells_a_running_agent_from_the_shell_it_leaves(self):
        terminal.start("bit-test-REQ-1-live", self.tmp, fake_agent(self.tmp, exits=False))
        wait_for("bit-test-REQ-1-live", "›")
        self.assertEqual(terminal.agent_state("bit-test-REQ-1-live"), "running")
        self.assertTrue(terminal.alive("bit-test-REQ-1-live"))
        self.shell("bit-test-REQ-1-gone")
        self.assertTrue(terminal.exists("bit-test-REQ-1-gone"))           # the session is still there: only a shell
        self.assertFalse(terminal.alive("bit-test-REQ-1-gone"))
        self.assertEqual(terminal.agent_state("bit-test-REQ-1-none"), "absent")
        self.assertEqual(terminal.send("bit-test-REQ-1-live", "hola"), "Enviado.")
        self.assertIn("MSG:hola", self.log())
        hand = self.tmp / "bin" / "codex"                 # the owner attaches and starts the agent again by hand
        hand.parent.mkdir()
        hand.write_text(Path(fake_agent(self.tmp, exits=False).split()[1]).read_text(), encoding="utf-8")
        subprocess.run([terminal._tmux_path(), "-L", terminal.socket(), "send-keys", "-t", "=bit-test-REQ-1-gone:",
                        f"bash {hand}", "Enter"], check=True)
        for _ in range(30):
            if terminal.alive("bit-test-REQ-1-gone"):
                break
            time.sleep(0.1)
        self.assertEqual(terminal.agent_state("bit-test-REQ-1-gone"), "running")
        self.assertFalse(terminal._agent_program(["bash"]) or terminal._agent_program(["-bash", "-l"]))
        self.assertTrue(terminal._agent_program(["node", "/usr/lib/node_modules/@anthropic-ai/claude-code/cli.js"]))

    def test_nothing_is_ever_typed_into_the_shell_an_exited_agent_leaves(self):
        name = "bit-test-REQ-1-shell"
        self.shell(name)
        said = terminal.send(name, self.trap)
        time.sleep(0.5)
        self.assertFalse(self.pwned.exists(), "the text ran as a shell command")
        self.assertNotIn("PWNED", terminal.screen(name))                   # not even left at the prompt
        self.assertNotEqual(said, "Enviado.")
        self.assertEqual(said.state, "gone")
        self.assertFalse(terminal._keys(name, "Enter"))

    def test_tell_planner_kills_the_shell_and_starts_the_planner_again_with_the_notice(self):
        import bt_core
        rdir = self.tmp / "pictures" / "requirements" / "REQ-021-demo"
        (rdir / ".planning").mkdir(parents=True)
        (rdir / terminal.RECORD).write_text('{"provider": "codex", "codex_home": "/acc/codex-luis"}')
        name = terminal.name_for("pictures", "REQ-021", "planner")
        self.shell(name)
        real_start = terminal.start
        agent = fake_agent(self.tmp, exits=False)
        launched: list[str] = []

        def start(name, cwd, command, env=None, **kw):     # the real tmux start, with the stand-in instead of Codex
            launched.append(command)
            return real_start(name, cwd, f"{agent} {shlex.quote(command)}", env)
        route = {"provider": "codex", "home": str(self.tmp / "codex-work"), "model": "", "effort": "high"}
        with patch.object(bt_core, "ROOT", self.tmp), patch.object(terminal, "planner_route", return_value=route), \
                patch.object(terminal, "start", side_effect=start), \
                patch.object(terminal, "_prompt_file", side_effect=lambda p, n, text: (
                    self.tmp / f"{n}.prompt.md", (self.tmp / f"{n}.prompt.md").write_text(text))[0]):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = terminal.main(["tell-planner", "pictures", "REQ-021", self.trap])
        time.sleep(0.5)
        self.assertFalse(self.pwned.exists(), "the request ran as a shell command")
        self.assertNotIn("Enviado", out.getvalue())
        self.assertEqual(code, 0, out.getvalue())
        self.assertIn("había terminado", out.getvalue())
        self.assertEqual(len(launched), 1)
        self.assertIn(self.trap, (self.tmp / f"{name}.prompt.md").read_text())   # the request goes along on start
        wait_for(name, "›")
        self.assertTrue(terminal.alive(name))                              # a new session with a running agent
        self.assertNotIn("session ended", terminal.screen(name))           # the old shell was killed, not cleared
        self.assertEqual(terminal.wall.held(rdir), [])
        self.assertEqual(terminal.main(["tell-planner", "pictures", "REQ-021", "SP-2 ok"]), 0)   # a live one is told
        self.assertIn("MSG:[Automatic notice, not typed by the owner] SP-2 ok", self.log())

    def test_a_planner_that_cannot_start_again_holds_the_notice_and_types_nothing(self):
        import bt_core
        import bt_planner_notices as notices
        rdir = self.tmp / "pictures" / "requirements" / "REQ-021-demo"
        (rdir / ".planning").mkdir(parents=True)
        name = terminal.name_for("pictures", "REQ-021", "planner")
        self.shell(name)
        with patch.object(bt_core, "ROOT", self.tmp), \
                patch.object(terminal, "start_planner", return_value=(False, "sin cuentas")) as start:
            state, text = notices.tell("pictures", "REQ-021", self.trap)
        time.sleep(0.5)
        self.assertFalse(self.pwned.exists(), "the request ran as a shell command")
        self.assertEqual(state, "held", text)
        start.assert_called_once()
        self.assertFalse(terminal.exists(name))                            # the shell is killed either way
        [kept] = terminal.wall.held(rdir)
        self.assertEqual(kept["text"], self.trap)


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
                patch("bt_agent_terminal.agent_state", return_value="running"), \
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
        with tempfile.TemporaryDirectory() as tmp, patch("bt_agent_terminal.exists", return_value=True), \
                patch("bt_agent_terminal.agent_state", return_value="gone"), patch("bt_presence.sessions", return_value=[]):
            self.assertIn("agent-start", view.strip(self.ctx(tmp)))  # a Planner whose agent exited: offer to open one

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
            limited = terminal.Said.of("El agente no lo leyó: su cuenta se quedó sin cuota.", "limited", 1793395920.0)
            with patch.object(bt_server, "ROOT", Path(tmp)), patch("bt_agent_terminal.send", return_value=limited), \
                    patch("bt_planner_notices.after_wall", return_value=("held", "guardé el mensaje")) as after:
                self.assertIn("guardé el mensaje", unquote(call("127.0.0.1", {"kind": "planner", "text": "sigue con SP-2"})))
            after.assert_called_once_with("pictures", "REQ-021", "sigue con SP-2", 1793395920.0)
            self.assertNotIn("sigue con SP-2", (rdir / ".planning" / "activity.jsonl").read_text(encoding="utf-8"))
            gone = terminal.Said.of(terminal.GONE_TEXT, "gone")
            with patch.object(bt_server, "ROOT", Path(tmp)), patch("bt_agent_terminal.send", return_value=gone), \
                    patch("bt_agent_terminal.exists", return_value=True), \
                    patch("bt_planner_notices.after_exit", return_value=("restarted", "lo abrí otra vez")) as again:
                self.assertIn("lo abrí otra vez", unquote(call("127.0.0.1", {"kind": "planner", "text": "sigue con SP-3"})))
            again.assert_called_once_with("pictures", "REQ-021", "sigue con SP-3")


if __name__ == "__main__":
    unittest.main()
