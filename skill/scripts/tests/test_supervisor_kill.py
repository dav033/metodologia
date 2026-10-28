"""bt_supervisor safety properties on real processes, for both backends: the attempt survives the orchestrator's
SIGKILL and is found again; terminate leaves nothing alive (including a setsid grandchild that ignores SIGTERM);
freeze/thaw; secrets never reach a command line or the unit definition."""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import textwrap
import time
import unittest
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from supervisor_support import BASE_ENV, PY, SCRIPTS, PgroupCase, SystemdCase, procs

GROWER = "while :; do echo x >> '{path}'; sleep 0.05; done"


class KillTests:
    def test_attempt_survives_orchestrator_death_and_is_adopted(self):
        key = self.key("orph")
        beat = self.worktree / "beat"
        orchestrator = self.tmp / "orchestrator.py"
        orchestrator.write_text(textwrap.dedent(f"""
            import sys, time
            sys.path.insert(0, {str(SCRIPTS)!r})
            from pathlib import Path
            from bt_supervisor import LaunchSpec, make_supervisor
            sup = make_supervisor(Path({str(self.state_dir)!r}), {self.BACKEND!r}, unit_prefix={self.prefix!r})
            sup.launch(LaunchSpec(attempt_key={key!r}, argv=["/bin/sh", "-c", {GROWER.format(path=beat)!r}],
                                  cwd=Path({str(self.worktree)!r}), env={BASE_ENV!r},
                                  log_dir=Path({str(self.tmp / 'logs')!r}), kill_grace_seconds=1.0))
            print("launched", flush=True)
            time.sleep(600)
        """))
        proc = subprocess.Popen([sys.executable, str(orchestrator)], stdout=subprocess.PIPE, text=True)
        self.addCleanup(lambda: proc.poll() is None and proc.kill())
        self.assertEqual(proc.stdout.readline().strip(), "launched")
        proc.send_signal(signal.SIGKILL)
        proc.wait(10)
        proc.stdout.close()
        self.wait_file(beat)
        size = beat.stat().st_size
        time.sleep(0.5)
        self.assertGreater(beat.stat().st_size, size, "the attempt died with its orchestrator")
        fresh = self.supervisor()                                   # a NEW instance after the restart
        found = [identity for identity in fresh.list_attempts(self.keys[-1][:5]) if identity.attempt_key == key]
        self.assertEqual(len(found), 1)
        observation = fresh.observe(key)
        self.assertEqual(observation.state, "running")
        self.assertEqual(observation.identity, found[0])
        ended = fresh.terminate(key)
        self.assertEqual((ended.state, ended.result, ended.live_pids), ("exited", "terminated", []))
        self.assert_size_stable(beat, 0.5)

    def test_terminate_kills_setsid_grandchild_ignoring_sigterm(self):
        key = self.key("cancel")
        grow = self.worktree / "grow"
        inner = f"trap '' TERM; {GROWER.format(path=grow)}"
        script = f"setsid /bin/sh -c \"{inner}\" & trap '' TERM; sleep 60"
        self.sup.launch(self.sh(key, script, kill_grace_seconds=5.0))
        self.wait_file(grow, 20)
        started = time.monotonic()
        ended = self.sup.terminate(key, grace=1.0)
        self.assertLess(time.monotonic() - started, 15)
        self.assertEqual(ended.state, "exited")
        self.assertEqual(ended.result, "terminated")
        self.assertEqual(ended.live_pids, [])
        self.assert_size_stable(grow, 1.0)
        self.assertEqual(procs.marked(key), {}, "a process carrying the attempt marker survived")
        again = self.sup.terminate(key)                             # idempotent on an exited attempt
        self.assertEqual(again.state, "exited")

    def test_freeze_stops_progress_and_thaw_resumes(self):
        key = self.key("frz")
        grow = self.worktree / "frozen"
        self.sup.launch(self.sh(key, GROWER.format(path=grow)))
        self.wait_file(grow, 10)
        self.sup.freeze(key)
        self.sup.freeze(key)                                        # idempotent
        time.sleep(0.3)                                             # an append in flight may still land
        self.assert_size_stable(grow, 1.0)
        self.assertEqual(self.sup.observe(key).state, "running")
        self.sup.thaw(key)
        self.sup.thaw(key)
        size = grow.stat().st_size
        time.sleep(0.6)
        self.assertGreater(grow.stat().st_size, size, "thaw did not resume the attempt")
        frozen_again = self.sup.freeze(key)
        self.assertIsNone(frozen_again)
        ended = self.sup.terminate(key, grace=1.0)                  # terminate thaws before SIGTERM
        self.assertEqual((ended.state, ended.live_pids), ("exited", []))

    def test_secrets_stay_off_command_lines_and_disk(self):
        key = self.key("sec")
        secret = f"sekrit-{uuid.uuid4().hex}"
        self.sup.launch(self.spec(key, [PY, "-I", "-c", "import time; time.sleep(30)"],
                                  env={**BASE_ENV, "API_TOKEN": secret}, stdin_text="prompt"))
        observation = self.sup.observe(key)
        self.assertEqual(observation.state, "running")
        pids = set(observation.live_pids) | set(procs.marked(key))
        reaper = self.state_dir / "attempts" / key / "reaper.json"
        if reaper.exists():
            pids.add(json.loads(reaper.read_text())["pid"])
        self.assertTrue(pids)
        for pid in pids:
            self.assertNotIn(secret.encode(), Path(f"/proc/{pid}/cmdline").read_bytes(), f"pid {pid}")
        agent = json.loads((self.state_dir / "attempts" / key / "started.json").read_text())["child_pid"]
        self.assertIn(f"API_TOKEN={secret}".encode(), Path(f"/proc/{agent}/environ").read_bytes().split(b"\0"))
        if self.BACKEND == "systemd":
            shown = subprocess.run(["systemctl", "--user", "show", observation.identity.unit, "-p", "ExecStart",
                                    "-p", "ExecStopPost", "-p", "Environment", "-p", "EnvironmentFiles"],
                                   check=False, capture_output=True, text=True, timeout=30).stdout
            self.assertIn("ExecStart=", shown)
            self.assertNotIn(secret, shown)
        for path in self.state_dir.rglob("*"):                       # the env file was deleted at start
            if path.is_file():
                self.assertNotIn(secret.encode(), path.read_bytes(), str(path))
        self.assertFalse((self.state_dir / "attempts" / key / "stdin").exists())
        for path in (self.state_dir, self.state_dir / "attempts" / key):
            self.assertEqual(os.stat(path).st_mode & 0o077, 0, f"{path} is readable by others")
        self.sup.terminate(key, grace=1.0)


class SystemdKill(SystemdCase, KillTests):
    pass


class PgroupKill(PgroupCase, KillTests):
    pass


if __name__ == "__main__":
    unittest.main()
