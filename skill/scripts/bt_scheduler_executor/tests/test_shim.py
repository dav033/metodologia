"""T6: the detached shim owns the agent group, enforces timeout/caps, and leaves atomic records; identity helpers."""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2])]
from bt_scheduler_executor import procinfo
from bt_scheduler_executor.executor import SHIM
from support import FAKE_AGENT, wait_for


class ShimCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name) / "attempt"
        self.dir.mkdir()
        self.cwd = Path(self.tmp.name) / "cwd"
        self.cwd.mkdir()
        self.procs = []
        self.addCleanup(self.cleanup)

    def cleanup(self):
        for p in self.procs:
            try:
                os.killpg(p.pid, 9)
            except OSError:
                pass
            p.wait()
        for entry in Path("/proc").iterdir():
            if entry.name.isdigit():
                try:
                    if os.readlink(entry / "cwd").startswith(self.tmp.name):
                        os.kill(int(entry.name), 9)
                except OSError:
                    pass

    def spec(self, argv, **kw):
        spec = {"attempt_id": "a1", "argv": argv, "stdin": None, "cwd": str(self.cwd), "timeout_seconds": 30,
                "grace_seconds": 1, "head_bytes": 1 << 20, "tail_bytes": 1 << 16, **kw}
        (self.dir / "spec.json").write_text(json.dumps(spec))

    def launch(self):
        p = subprocess.Popen([sys.executable, str(SHIM), str(self.dir)], start_new_session=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.procs.append(p)
        return p

    def run_to_end(self, argv, **kw):
        self.spec(argv, **kw)
        self.launch()
        self.assertTrue(wait_for(lambda: (self.dir / "exit.json").exists(), 60), "no exit.json")
        return json.loads((self.dir / "exit.json").read_text())

    def shim_pid(self):
        self.assertTrue(wait_for(lambda: (self.dir / "shim.json").exists()))
        return json.loads((self.dir / "shim.json").read_text())["pid"]

    def agent(self, *a):
        return [sys.executable, str(FAKE_AGENT), *a]

    def test_a_clean_run_writes_both_records_and_the_output(self):
        exit_info = self.run_to_end(self.agent("ok"))
        self.assertEqual((exit_info["reason"], exit_info["returncode"]), ("exited", 0))
        self.assertIn(b"TERMINAL-EVENT", (self.dir / "output.log").read_bytes())
        shim = json.loads((self.dir / "shim.json").read_text())
        self.assertTrue(shim["ident"] and shim["child_ident"])
        self.assertTrue((self.cwd / "result.txt").exists())

    def test_the_spec_is_removed_as_soon_as_it_is_read(self):
        self.run_to_end(self.agent("ok"))
        self.assertFalse((self.dir / "spec.json").exists())

    def test_shim_json_exists_before_the_agent_finishes_and_exit_json_only_after(self):
        self.spec(self.agent("sleep", "30"))
        self.launch()
        self.assertTrue(wait_for(lambda: (self.dir / "shim.json").exists()))
        self.assertTrue(wait_for(lambda: json.loads((self.dir / "shim.json").read_text()).get("child_pid")))
        self.assertFalse((self.dir / "exit.json").exists())

    def test_the_shim_persists_an_agent_terminal_descendant_after_the_agent_exits(self):
        pid_file = self.cwd / "terminal.pid"
        code = (
            "import os, pty, signal, sys, time\n"
            "pid, master = pty.fork()\n"
            "if pid == 0:\n"
            "    signal.signal(signal.SIGHUP, signal.SIG_IGN)\n"
            "    os.execlp('sleep', 'sleep', '60')\n"
            "open(sys.argv[1], 'w').write(str(pid))\n"
            "time.sleep(0.6)\n"
            "os.close(master)\n"
        )
        self.spec([sys.executable, "-c", code, str(pid_file)])
        self.launch()
        self.assertTrue(wait_for(lambda: pid_file.exists() and pid_file.read_text().strip().isdigit()))
        pid = int(pid_file.read_text())
        self.assertTrue(wait_for(lambda: (self.dir / "exit.json").exists(), 10))

        record = json.loads((self.dir / "descendants.json").read_text())
        identities = {item["pid"]: item["ident"] for item in record["processes"]}
        self.assertIn(pid, identities)
        self.assertEqual(identities[pid], procinfo.start_ident(pid))
        self.assertEqual(procinfo.kill_in_cwd(str(self.cwd), spare_interactive=True,
                                               known_descendants=identities), 1)
        self.assertTrue(wait_for(lambda: not procinfo.alive(pid, identities[pid])))

    def test_the_exit_code_of_a_failing_agent_is_recorded(self):
        info = self.run_to_end(self.agent("crash"))
        self.assertEqual((info["reason"], info["returncode"]), ("exited", 3))

    def test_a_missing_binary_is_a_spawn_error_with_no_exit_code(self):
        info = self.run_to_end(["/no/such/binary"])
        self.assertEqual(info["reason"], "spawn_error")
        self.assertIsNone(info["returncode"])
        self.assertIn("FileNotFoundError", info["error"])

    def test_stdin_reaches_the_agent(self):
        info = self.run_to_end([sys.executable, "-c", "import sys; print('GOT:' + sys.stdin.read())"], stdin="prompt text")
        self.assertEqual(info["returncode"], 0)
        self.assertIn(b"GOT:prompt text", (self.dir / "output.log").read_bytes())

    def test_a_timeout_stops_the_agent_and_its_grandchildren(self):
        self.spec(self.agent("grandchild", "60"), timeout_seconds=1)
        self.launch()
        self.assertTrue(wait_for(lambda: (self.cwd / "grandchild.pid").exists()))
        gpid = int((self.cwd / "grandchild.pid").read_text())
        self.assertTrue(wait_for(lambda: (self.dir / "exit.json").exists(), 30))
        info = json.loads((self.dir / "exit.json").read_text())
        self.assertEqual(info["reason"], "timeout")
        self.assertTrue(wait_for(lambda: not procinfo.start_ident(gpid), 10), "the grandchild outlived the agent")

    def test_an_agent_that_ignores_sigterm_is_killed_after_the_grace_period(self):
        self.spec(self.agent("stubborn", "60"), timeout_seconds=1, grace_seconds=1)
        t0 = time.monotonic()
        self.launch()
        self.assertTrue(wait_for(lambda: (self.dir / "exit.json").exists(), 30))
        self.assertLess(time.monotonic() - t0, 15)
        info = json.loads((self.dir / "exit.json").read_text())
        self.assertEqual((info["reason"], info["returncode"]), ("timeout", -signal.SIGKILL))

    def test_sigterm_to_the_shim_cancels_the_agent_and_says_so(self):
        self.spec(self.agent("sleep", "60"))
        self.launch()
        self.assertTrue(wait_for(lambda: (self.cwd / "started.txt").exists()))
        os.kill(self.shim_pid(), signal.SIGTERM)
        self.assertTrue(wait_for(lambda: (self.dir / "exit.json").exists(), 30))
        info = json.loads((self.dir / "exit.json").read_text())
        self.assertEqual(info["reason"], "cancelled")
        self.assertEqual(info["returncode"], -signal.SIGTERM)

    def test_output_beyond_the_head_cap_is_dropped_with_a_count_and_the_tail_is_kept(self):
        info = self.run_to_end(self.agent("big", "400000"), head_bytes=10_000, tail_bytes=5_000)
        self.assertEqual(len((self.dir / "output.log").read_bytes()), 10_000)
        tail = (self.dir / "output.tail").read_bytes()
        self.assertEqual(len(tail), 5_000)
        self.assertIn(b"THE-END-MARKER", tail)
        self.assertEqual(info["output_bytes"], 10_000 + info["dropped_bytes"] + 5_000)
        self.assertGreater(info["dropped_bytes"], 300_000)

    def test_output_that_fits_has_no_dropped_bytes(self):
        info = self.run_to_end(self.agent("ok"))
        self.assertEqual(info["dropped_bytes"], 0)

    def test_the_exit_record_is_never_half_written(self):
        # exit.json appears only through an atomic rename: any reader sees complete JSON or nothing
        self.spec(self.agent("ok"))
        self.launch()
        seen = 0
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            path = self.dir / "exit.json"
            if path.exists():
                json.loads(path.read_text())
                seen += 1
                break
        self.assertEqual(seen, 1)
        self.assertEqual([p.name for p in self.dir.iterdir() if p.name.endswith(".tmp")], [])

    def test_the_shim_leads_its_own_session_and_the_agent_its_own_group(self):
        self.spec(self.agent("sleep", "30"))
        self.launch()
        self.assertTrue(wait_for(lambda: json.loads((self.dir / "shim.json").read_text()).get("child_pid")
                                 if (self.dir / "shim.json").exists() else False))
        shim = json.loads((self.dir / "shim.json").read_text())
        self.assertNotEqual(os.getsid(shim["pid"]), os.getsid(0))              # not in the launcher's session
        self.assertNotEqual(os.getpgid(shim["pid"]), os.getpgid(0))
        self.assertEqual(shim["pgid"], os.getpgid(shim["pid"]))
        self.assertEqual(os.getpgid(shim["child_pid"]), shim["child_pid"])      # the agent leads its own group
        self.assertNotEqual(os.getpgid(shim["child_pid"]), shim["pgid"])
        self.assertEqual(procinfo.start_ident(shim["pid"]), shim["ident"])

    def test_when_the_shim_dies_hard_the_agent_is_an_orphan_that_can_be_found_and_stopped_by_identity(self):
        self.spec(self.agent("sleep", "60"))
        self.launch()
        self.assertTrue(wait_for(lambda: (self.cwd / "started.txt").exists()))
        self.assertTrue(wait_for(lambda: json.loads((self.dir / "shim.json").read_text()).get("child_ident")))
        shim = json.loads((self.dir / "shim.json").read_text())
        os.kill(shim["pid"], signal.SIGKILL)                 # the shim itself dies hard: no exit.json
        self.assertTrue(wait_for(lambda: not procinfo.alive(shim["pid"], shim["ident"])))
        self.assertFalse((self.dir / "exit.json").exists())
        self.assertTrue(procinfo.alive(shim["child_pid"], shim["child_ident"]))     # orphan, findable by identity
        procinfo.signal_group(shim["child_pgid"], signal.SIGKILL)


class Identity(unittest.TestCase):
    def test_a_live_process_matches_its_own_identity_and_a_wrong_one_does_not(self):
        ident = procinfo.start_ident(os.getpid())
        self.assertTrue(ident)
        self.assertTrue(procinfo.alive(os.getpid(), ident))
        self.assertFalse(procinfo.alive(os.getpid(), ident + "x"))
        self.assertFalse(procinfo.alive(None, ident))
        self.assertFalse(procinfo.alive(os.getpid(), None))

    def test_a_recycled_pid_is_not_the_recorded_process(self):
        p = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
        ident = procinfo.start_ident(p.pid)
        self.assertTrue(procinfo.alive(p.pid, ident))
        p.kill()
        p.wait()
        self.assertFalse(procinfo.alive(p.pid, ident))
        fake_new_process_with_same_pid = ident.rsplit(":", 1)[0] + ":999999999999"
        self.assertFalse(procinfo.alive(os.getpid(), fake_new_process_with_same_pid))

    def test_a_zombie_counts_as_gone(self):
        p = subprocess.Popen([sys.executable, "-c", "pass"])
        self.assertTrue(wait_for(lambda: Path(f"/proc/{p.pid}/stat").read_text().split(")")[1].split()[0] == "Z"))
        self.assertIsNone(procinfo.start_ident(p.pid))
        p.wait()

    def test_signal_names(self):
        self.assertEqual(procinfo.signal_name(-15), "SIGTERM")
        self.assertEqual(procinfo.signal_name(-9), "SIGKILL")
        self.assertEqual(procinfo.signal_name(0), "")
        self.assertEqual(procinfo.signal_name(None), "")

    def test_signalling_a_dead_group_is_a_quiet_false(self):
        self.assertFalse(procinfo.signal_group(2_000_000_000, signal.SIGKILL))
        self.assertFalse(procinfo.signal_pid(2_000_000_000, signal.SIGKILL))

    def test_find_by_argv_matches_only_a_command_line_that_is_exactly_python_shim_directory(self):
        import tempfile
        with tempfile.TemporaryDirectory() as t:
            script = Path(t) / "fake_shim.py"
            script.write_text("import time; time.sleep(30)\n")
            real = subprocess.Popen([sys.executable, str(script), t])
            decoy = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)", str(script), t])
            try:
                self.assertTrue(wait_for(lambda: real.pid in procinfo.find_by_argv(str(script), t)))
                found = procinfo.find_by_argv(str(script), t)
                self.assertIn(real.pid, found)
                self.assertNotIn(decoy.pid, found)               # an operator's tail/vim/grep on those paths is not a shim
            finally:
                for p in (real, decoy):
                    p.kill()
                    p.wait()


if __name__ == "__main__":
    unittest.main()
