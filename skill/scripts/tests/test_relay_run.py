"""relay_run.py (parent launcher), wrapper proof, wrapper path of `relay launch`, wrapper generator, wrap-status.
Nothing real is signalled, typed or installed: children, /proc and signals are fakes."""
import io
import json
import os
import signal
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

if not os.environ.get("BITACORA_TEST_ROOT"):
    _tmp = Path(tempfile.mkdtemp(prefix="relay-run-test-"))
    os.environ["BITACORA_TEST_ROOT"] = str(_tmp)
    os.environ["BITACORA_ROOT"] = str(_tmp / "bitacora")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bt_relay  # noqa: E402
import bt_relay_client  # noqa: E402
import bt_relay_launch as launch  # noqa: E402
import relay_run  # noqa: E402

BIN = sys.executable  # absolute, executable


class FakeChild:
    def __init__(self, code):
        self.returncode = code
        self.signals = []

    def wait(self):
        return self.returncode

    def send_signal(self, sig):
        self.signals.append(sig)


class Case(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="relay-run-")
        self.addCleanup(self.tmp.cleanup)
        self.state = Path(self.tmp.name) / ".state"
        (self.state / "relay").mkdir(parents=True, mode=0o700)
        for target in ("relay_run.STATE", "bt_relay.STATE", "bt_profiles.STATE"):
            patch(target, self.state).start()
        self.addCleanup(patch.stopall)
        self.cwd = self.tmp.name

    def write_next(self, pid, **over):
        spec = {"argv": [BIN, "prompt"], "env": {}, "unset": [], "cwd": self.cwd, "profile": "claude-work",
                "stem": "h1", "created": time.time(), "client": 1, **over}
        path = self.state / "relay" / f"next-{pid}.json"
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as fh:
            json.dump(spec, fh)
        return path


class LauncherLoopTests(Case):
    def run_loop(self, codes, pid=None, max_chain=None):
        """Run the loop with fake children that exit with `codes` in order; returns (exit, argvs, stderr)."""
        pid = pid or os.getpid()
        seen, err = [], io.StringIO()
        queue = list(codes)

        def popen(argv, env=None, cwd=None):
            seen.append((argv, cwd, dict(env)))
            return FakeChild(queue.pop(0))
        if max_chain is not None:
            patch("relay_run.max_chain", lambda: max_chain).start()
        code = relay_run.run("claude-personal", ["claude"], popen=popen, environ={"PATH": "/bin"}, err=err,
                             install_signals=False)
        return code, seen, err.getvalue()

    def test_exits_with_child_code_when_no_next(self):
        code, seen, _ = self.run_loop([7])
        self.assertEqual(code, 7)
        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0][2]["METODOLOGIA_RELAY_WRAPPER"], str(os.getpid()))
        self.assertEqual(seen[0][2]["METODOLOGIA_RELAY_PROFILE"], "claude-personal")

    def test_signal_death_maps_to_shell_convention(self):
        self.assertEqual(relay_run.exit_code(-15), 128 + 15)
        self.assertEqual(relay_run.exit_code(None), 1)

    def test_runs_successor_in_same_terminal_then_exits(self):
        self.write_next(os.getpid(), env={"CLAUDE_CONFIG_DIR": "/acct", "PATH": "/evil"}, profile="claude-work")
        code, seen, err = self.run_loop([0, 3])
        self.assertEqual(code, 3)
        self.assertEqual(seen[1][0], [BIN, "prompt"])
        self.assertEqual(seen[1][1], self.cwd)
        self.assertEqual(seen[1][2]["CLAUDE_CONFIG_DIR"], "/acct")
        self.assertEqual(seen[1][2]["PATH"], "/bin")  # only account selectors may be overlaid
        self.assertEqual(seen[1][2]["METODOLOGIA_RELAY_PROFILE"], "claude-work")
        self.assertIn("relevo de cuota", err)

    def test_unset_removes_only_account_selectors(self):
        self.write_next(os.getpid(), unset=["CLAUDE_CONFIG_DIR", "HOME"])
        with patch.dict(os.environ, {}, clear=False):
            seen = []
            relay_env = {"PATH": "/bin", "CLAUDE_CONFIG_DIR": "/old", "HOME": "/h"}
            popen = lambda argv, env=None, cwd=None: (seen.append(dict(env)), FakeChild(0))[1]  # noqa: E731
            relay_run.run("p", ["claude"], popen=popen, environ=relay_env, err=io.StringIO(), install_signals=False)
        self.assertNotIn("CLAUDE_CONFIG_DIR", seen[1])
        self.assertEqual(seen[1]["HOME"], "/h")

    def test_next_is_consumed_once(self):
        path = self.write_next(os.getpid())
        self.assertIsNotNone(relay_run.take_next(os.getpid()))
        self.assertFalse(path.exists())
        self.assertIsNone(relay_run.take_next(os.getpid()))
        self.assertEqual(list((self.state / "relay").glob("*.consumed")), [])

    def test_stale_next_is_ignored(self):
        self.write_next(os.getpid(), created=time.time() - 3600)
        code, seen, _ = self.run_loop([0])
        self.assertEqual((code, len(seen)), (0, 1))

    def test_future_dated_next_is_ignored(self):
        self.write_next(os.getpid(), created=time.time() + 3600)
        self.assertIsNone(relay_run.take_next(os.getpid()))

    def test_cancelled_next_is_ignored(self):
        (self.state / "relay" / "cancelled").mkdir()
        (self.state / "relay" / "cancelled" / "h1").write_text("")
        self.write_next(os.getpid())
        code, seen, _ = self.run_loop([0])
        self.assertEqual(len(seen), 1)

    def test_next_of_another_wrapper_is_not_taken(self):
        self.write_next(os.getpid() + 1)
        self.assertIsNone(relay_run.take_next(os.getpid()))

    def test_loose_permissions_or_foreign_owner_are_refused(self):
        path = self.write_next(os.getpid())
        os.chmod(path, 0o644)
        self.assertIsNone(relay_run.take_next(os.getpid()))
        path = self.write_next(os.getpid())
        real_uid = os.getuid()
        with patch("relay_run.os.getuid", lambda: real_uid + 1):
            self.assertIsNone(relay_run.take_next(os.getpid()))

    def test_malformed_specs_are_discarded(self):
        for bad in ({"argv": "claude --x"}, {"argv": ["rel/claude"]}, {"argv": []}, {"cwd": "/nonexistent-dir-xyz"},
                    {"argv": [BIN, 5]}, {"argv": ["/nonexistent/bin"]}):
            self.write_next(os.getpid(), **bad)
            self.assertIsNone(relay_run.take_next(os.getpid()), bad)
        path = self.state / "relay" / f"next-{os.getpid()}.json"
        path.write_text("not json")
        os.chmod(path, 0o600)
        self.assertIsNone(relay_run.take_next(os.getpid()))

    def test_nul_and_symlinked_specs_are_refused(self):
        self.write_next(os.getpid(), argv=[BIN, "a\0b"])
        self.assertIsNone(relay_run.take_next(os.getpid()))
        real = Path(self.tmp.name) / "real.json"
        real.write_text(json.dumps({"argv": [BIN], "cwd": self.cwd, "created": time.time()}))
        os.chmod(real, 0o600)
        os.symlink(real, self.state / "relay" / f"next-{os.getpid()}.json")
        self.assertIsNone(relay_run.take_next(os.getpid()))

    def test_successor_that_cannot_start_exits_with_previous_code(self):
        self.write_next(os.getpid())
        calls = []

        def popen(argv, env=None, cwd=None):
            calls.append(argv)
            if len(calls) == 2:
                raise OSError("gone")
            return FakeChild(4)
        code = relay_run.run("p", ["claude"], popen=popen, environ={}, err=io.StringIO(), install_signals=False)
        self.assertEqual((code, len(calls)), (4, 2))

    def test_write_private_replaces_a_planted_symlink(self):
        target = Path(self.tmp.name) / "victim"
        target.write_text("keep")
        link = self.state / "relay" / "x.json"
        os.symlink(target, link)
        bt_relay.write_private(link, "new")
        self.assertEqual(target.read_text(), "keep")
        self.assertEqual(link.read_text(), "new")

    def test_chain_is_bounded(self):
        # every exit leaves another next behind; the loop must stop after max_chain successors
        count = {"n": 0}
        err = io.StringIO()

        def popen(argv, env=None, cwd=None):
            count["n"] += 1
            self.write_next(os.getpid())
            return FakeChild(0)
        patch("relay_run.max_chain", lambda: 3).start()
        code = relay_run.run("p", ["claude"], popen=popen, environ={}, err=err, install_signals=False)
        self.assertEqual(count["n"], 4)  # original + 3 relays
        self.assertIn("tope", err.getvalue())
        self.assertEqual(code, 0)

    def test_zero_chain_never_relays(self):
        self.write_next(os.getpid())
        _, seen, err = self.run_loop([0], max_chain=0)
        self.assertEqual(len(seen), 1)
        self.assertIn("tope", err)

    def test_max_chain_reads_config_with_default(self):
        self.assertEqual(relay_run.max_chain(), 3)
        (self.state / "config.json").write_text(json.dumps({"relay": {"max_chain": 1}}))
        self.assertEqual(relay_run.max_chain(), 1)
        (self.state / "config.json").write_text(json.dumps({"relay": {"max_chain": True}}))
        self.assertEqual(relay_run.max_chain(), 3)

    def test_signals_are_forwarded_to_the_child(self):
        child = FakeChild(0)
        relay_run.forward(child, signal.SIGTERM, True)
        relay_run.forward(child, signal.SIGWINCH, False)
        self.assertEqual(child.signals, [signal.SIGTERM, signal.SIGWINCH])

    def test_sigint_is_not_doubled_when_the_terminal_already_delivered_it(self):
        child = FakeChild(0)
        relay_run.forward(child, signal.SIGINT, True)
        self.assertEqual(child.signals, [])
        relay_run.forward(child, signal.SIGINT, False)  # e.g. sent by `kill -INT <launcher>`
        self.assertEqual(child.signals, [signal.SIGINT])

    def test_handlers_target_only_the_running_child(self):
        holder = []
        saved = {s: signal.getsignal(s) for s in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGWINCH)}
        self.addCleanup(lambda: [signal.signal(s, h) for s, h in saved.items()])
        relay_run._install(holder)
        handler = signal.getsignal(signal.SIGTERM)
        handler(signal.SIGTERM, None)  # no child yet: must not raise
        child = FakeChild(0)
        holder.append(child)
        with patch("relay_run._same_foreground", lambda: False):
            handler(signal.SIGTERM, None)
        self.assertEqual(child.signals, [signal.SIGTERM])

    def test_main_usage_and_missing_binary(self):
        with patch.object(sys, "argv", ["relay_run.py", "p"]), patch("sys.stderr", io.StringIO()):
            self.assertEqual(relay_run.main(), 2)
        with patch.object(sys, "argv", ["relay_run.py", "p", "--", "/nonexistent/agent-xyz"]), \
                patch("sys.stderr", io.StringIO()):
            self.assertEqual(relay_run.main(), 127)


class WrapperProofTests(Case):
    WRAPPER, CLIENT = 500, 600

    def setUp(self):
        super().setUp()
        self.procs, self.environs = {}, {}
        patch("bt_relay_proc.read", lambda pid: self.procs.get(pid)).start()
        patch("bt_relay_proc.environ_of", lambda pid: self.environs.get(pid)).start()
        self.procs[self.WRAPPER] = {"ppid": 1, "comm": "python3", "state": "S", "start": 50, "argv0": "python3",
                                    "args": [str(Path(relay_run.__file__).resolve()), "claude-work", "--", "/bin/claude"], "tty": True}
        self.procs[self.CLIENT] = {"ppid": self.WRAPPER, "comm": "claude", "state": "S", "start": 60,
                                   "argv0": "claude", "args": [], "tty": True}
        self.environs[self.CLIENT] = {"METODOLOGIA_RELAY_WRAPPER": str(self.WRAPPER)}

    def proof(self):
        return bt_relay_client.wrapper_proof(self.CLIENT, self.procs[self.CLIENT])

    def verify(self, **over):
        args = {"pid": self.CLIENT, "start": 60, "wrapper_pid": self.WRAPPER, "wrapper_start": 50, **over}
        return bt_relay_client.verify_wrapper(**args)

    def test_accepts_child_of_the_launcher(self):
        self.assertEqual(self.proof(), {"pid": self.WRAPPER, "start": 50})
        self.assertTrue(self.verify())

    def test_rejects_client_whose_parent_is_not_the_named_launcher(self):
        self.procs[self.CLIENT]["ppid"] = 77
        self.assertIsNone(self.proof())
        self.assertFalse(self.verify())

    def test_rejects_foreign_command_line(self):
        self.procs[self.WRAPPER]["args"] = ["/tmp/evil.py"]
        self.procs[self.WRAPPER]["argv0"] = "python3"
        self.assertIsNone(self.proof())
        self.assertFalse(self.verify())

    def test_rejects_missing_or_forged_variable(self):
        self.environs[self.CLIENT] = {}
        self.assertIsNone(self.proof())
        self.environs[self.CLIENT] = {"METODOLOGIA_RELAY_WRAPPER": "1"}
        self.assertIsNone(self.proof())
        self.environs[self.CLIENT] = {"METODOLOGIA_RELAY_WRAPPER": "abc"}
        self.assertIsNone(self.proof())

    def test_pid_reuse_is_caught_by_start_time(self):
        self.procs[self.CLIENT]["start"] = 999  # the pid now belongs to another process
        self.assertFalse(self.verify())
        self.procs[self.CLIENT]["start"] = 60
        self.procs[self.WRAPPER]["start"] = 777  # the launcher pid was recycled
        self.assertFalse(self.verify())

    def test_other_script_named_relay_run_is_not_the_launcher(self):
        self.procs[self.WRAPPER]["args"] = ["/tmp/other/relay_run.py", "x"]
        self.assertIsNone(self.proof())

    def test_zombie_launcher_is_not_a_launcher(self):
        self.procs[self.WRAPPER]["state"] = "Z"
        self.assertIsNone(self.proof())

    def test_ssh_client_without_multiplexer_variables_succeeds_through_the_launcher(self):
        # the client's ancestors include sshd, and the environment has no TMUX/ZELLIJ/KITTY variable
        self.procs[self.WRAPPER]["ppid"] = 40
        self.procs[40] = {"ppid": 1, "comm": "sshd", "state": "S", "start": 5, "argv0": "sshd", "args": [], "tty": False}
        self.procs[900] = {"ppid": self.CLIENT, "comm": "python3", "state": "S", "start": 70, "argv0": "python3",
                           "args": [], "tty": False}
        env = {"METODOLOGIA_RELAY_WRAPPER": str(self.WRAPPER)}
        got = bt_relay_client.locate(env, "sess-1", "claude", own_pid=900)
        self.assertEqual((got["pid"], got["start"]), (self.CLIENT, 60))
        self.assertEqual(got["wrapper"], {"pid": self.WRAPPER, "start": 50})
        self.assertIsNone(got["mux"])

    def test_without_launcher_variable_ssh_client_falls_back_to_manual(self):
        self.environs[self.CLIENT] = {}
        self.procs[self.WRAPPER]["ppid"] = 40
        self.procs[40] = {"ppid": 1, "comm": "sshd", "state": "S", "start": 5, "argv0": "sshd", "args": [], "tty": False}
        self.procs[900] = {"ppid": self.CLIENT, "comm": "python3", "state": "S", "start": 70, "argv0": "python3",
                           "args": [], "tty": False}
        got = bt_relay_client.locate({"TMUX_PANE": "%1"}, "sess-1", "claude", own_pid=900)
        self.assertIsNone(got["pid"])


class WrapperLaunchTests(WrapperProofTests):
    HANDOFF = "h1"

    def setUp(self):
        super().setUp()
        patch("bt_relay.settings", lambda: {"enabled": True, "threshold": 92, "exit_current": True}).start()
        patch("bt_relay.supervised", lambda: False).start()
        patch("bt_relay_launch.notify", lambda *a: None).start()
        patch("bt_relay_launch.shutil.which", lambda name: BIN).start()
        self.profile_cfg = {"provider": "claude", "env": {"CLAUDE_CONFIG_DIR": "/acct"}, "work_only": False,
                            "bin": "claude"}
        patch("bt_profiles.get", lambda pid: self.profile_cfg).start()
        patch("bt_profiles.env_of", lambda pid: self.profile_cfg["env"]).start()
        self.handoff = self.state / "relay" / "h1.md"
        bt_relay.write_private(self.handoff, "summary")
        self.sleeps = []

    def end_turn(self):
        marker = self.state / "relay" / "turn-ended-sess-1"
        bt_relay.write_private(marker, "")
        later = self.handoff.stat().st_mtime + 5
        os.utime(marker, (later, later))

    def test_signals_client_after_writing_next_and_never_types(self):
        order, killed = [], []
        self.end_turn()
        nxt = self.state / "relay" / f"next-{self.WRAPPER}.json"

        def kill(pid, sig):
            order.append(("kill", sig, nxt.exists()))
            killed.append((pid, sig))
            del self.procs[self.CLIENT]  # the client exits after SIGTERM
        runner = MagicMock()
        with patch("bt_relay_launch.os.kill", kill):
            result = launch.run(self.handoff, "claude-work", self.cwd, "sess-1", None, None, self.CLIENT, 60, True,
                                runner=runner, sleep=lambda s: None, wrapper=(self.WRAPPER, 50))
        self.assertEqual(result, "wrapper")
        self.assertEqual(killed, [(self.CLIENT, signal.SIGTERM)])
        self.assertTrue(order[0][2], "next file must exist before the client is signalled")
        runner.assert_not_called()  # nothing typed into any pane
        spec = json.loads(nxt.read_text())
        self.assertEqual(spec["argv"][0], BIN)
        self.assertIn(str(self.handoff), spec["argv"][1])  # the successor only receives the path
        self.assertEqual(oct(nxt.stat().st_mode & 0o777), "0o600")

    def test_never_signals_a_process_that_is_not_the_proven_client(self):
        self.end_turn()
        self.procs[self.CLIENT]["ppid"] = 77  # not the launcher's child any more
        killed = []
        with patch("bt_relay_launch.os.kill", lambda *a: killed.append(a)):
            result = launch.run(self.handoff, "claude-work", self.cwd, "sess-1", None, None, self.CLIENT, 60, True,
                                runner=MagicMock(), sleep=lambda s: None, wrapper=(self.WRAPPER, 50))
        self.assertEqual(killed, [])
        self.assertEqual(result, "manual")
        self.assertFalse((self.state / "relay" / f"next-{self.WRAPPER}.json").exists())

    def test_recycled_pid_after_waiting_is_not_signalled(self):
        killed = []

        def waiting_sleep(_):  # the turn ends, but meanwhile the client pid was recycled
            self.procs[self.CLIENT]["start"] = 4242
            self.end_turn()
        with patch("bt_relay_launch.os.kill", lambda *a: killed.append(a)):
            result = launch.run(self.handoff, "claude-work", self.cwd, "sess-1", None, None, self.CLIENT, 60, True,
                                runner=MagicMock(), sleep=waiting_sleep, wrapper=(self.WRAPPER, 50))
        self.assertEqual(killed, [])
        self.assertEqual(result, "manual")
        self.assertFalse((self.state / "relay" / f"next-{self.WRAPPER}.json").exists())

    def test_invalid_successor_is_validated_before_anything_is_written(self):
        self.end_turn()
        with patch("bt_relay_launch.shutil.which", lambda name: None):
            result = launch.run(self.handoff, "claude-work", self.cwd, "sess-1", None, None, self.CLIENT, 60, True,
                                runner=MagicMock(), sleep=lambda s: None, wrapper=(self.WRAPPER, 50))
        self.assertEqual(result, "manual")
        self.assertFalse((self.state / "relay" / f"next-{self.WRAPPER}.json").exists())
        missing = os.path.join(self.cwd, "no-such-dir")
        with self.assertRaises(launch.Refused):
            launch.run_wrapper(self.handoff, "claude-work", missing, "sess-1", self.CLIENT, 60,
                               (self.WRAPPER, 50), True, sleep=lambda s: None)

    def test_second_helper_for_same_session_never_touches_the_next_file(self):
        self.end_turn()
        launch.claim("other-stem", "sess-1")  # another handoff of this session already claimed it
        nxt = self.state / "relay" / f"next-{self.WRAPPER}.json"
        bt_relay.write_private(nxt, "winner")
        killed = []
        with patch("bt_relay_launch.os.kill", lambda *a: killed.append(a)):
            result = launch.run_wrapper(self.handoff, "claude-work", self.cwd, "sess-1", self.CLIENT, 60,
                                        (self.WRAPPER, 50), True, sleep=lambda s: None)
        self.assertEqual((result, killed, nxt.read_text()), ("skipped", [], "winner"))

    def test_next_is_not_written_before_the_turn_ends(self):
        nxt = self.state / "relay" / f"next-{self.WRAPPER}.json"
        seen = []

        def sleeper(_):
            seen.append(nxt.exists())
            self.end_turn()
        with patch("bt_relay_launch.os.kill", lambda *a: self.procs.pop(self.CLIENT, None)):
            launch.run_wrapper(self.handoff, "claude-work", self.cwd, "sess-1", self.CLIENT, 60,
                               (self.WRAPPER, 50), True, sleep=sleeper)
        self.assertEqual(seen, [False])

    def test_cancel_removes_next_and_signals_nothing(self):
        self.end_turn()
        (self.state / "relay" / "cancelled").mkdir()
        (self.state / "relay" / "cancelled" / "h1").write_text("")
        killed = []
        with patch("bt_relay_launch.os.kill", lambda *a: killed.append(a)):
            result = launch.run(self.handoff, "claude-work", self.cwd, "sess-1", None, None, self.CLIENT, 60, True,
                                runner=MagicMock(), sleep=lambda s: None, wrapper=(self.WRAPPER, 50))
        self.assertEqual((result, killed), ("cancelled", []))
        self.assertFalse((self.state / "relay" / f"next-{self.WRAPPER}.json").exists())

    def test_without_wrapper_it_falls_through_to_manual_with_no_multiplexer(self):
        result = launch.run(self.handoff, "claude-work", self.cwd, "sess-1", None, None, self.CLIENT, 60, True,
                            runner=MagicMock(), sleep=lambda s: None, wrapper=None)
        self.assertEqual(result, "manual")

    def test_wrapper_failure_falls_back_to_the_multiplexer_path(self):
        self.procs[self.CLIENT]["ppid"] = 77
        order = []
        with patch("bt_relay_launch.preflight", lambda *a, **k: order.append("preflight")), \
                patch("bt_relay_launch.wait_turn_end", lambda *a, **k: order.append("wait")), \
                patch("bt_relay_launch.stop_agent", lambda *a, **k: order.append("stop")), \
                patch("bt_relay_launch.proc.alive", lambda *a, **k: False), \
                patch("bt_relay_launch.run_steps", lambda *a, **k: order.append("type")):
            result = launch.run(self.handoff, "claude-work", self.cwd, "sess-1", "tmux", "%1", self.CLIENT, 60, True,
                                runner=MagicMock(), sleep=lambda s: None, wrapper=(self.WRAPPER, 50))
        self.assertEqual(result, "launched")
        self.assertEqual(order, ["preflight", "wait", "stop", "type"])


if __name__ == "__main__":
    unittest.main()
