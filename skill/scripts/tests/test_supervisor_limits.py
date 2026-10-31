"""bt_supervisor resource limits on real processes: MemoryMax -> oom-kill (systemd only: the pgroup backend has no
memory ceiling and records the limit as unenforced) and runtime_max_seconds -> timeout (both backends)."""
from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from supervisor_support import PY, Limits, PgroupCase, SystemdCase

MIB = 1024 * 1024
ALLOCATE = "import time; block = b'\\x01' * (512 * 1024 * 1024); time.sleep(30)"   # touched pages, not calloc


class RuntimeLimit:
    def test_runtime_limit_times_out(self):
        key = self.key("rt")
        started = time.monotonic()
        self.sup.launch(self.spec(key, ["sleep", "30"], limits=Limits(runtime_max_seconds=2)))
        done = self.wait_state(key, timeout=20)
        self.assertEqual(done.result, "timeout")
        self.assertEqual(done.live_pids, [])
        self.assertLess(time.monotonic() - started, 12)


class SystemdLimits(SystemdCase, RuntimeLimit):
    def test_memory_limit_is_an_oom_kill(self):
        key = self.key("oom")
        self.sup.launch(self.spec(key, [PY, "-I", "-c", ALLOCATE], limits=Limits(memory_max_bytes=64 * MIB)))
        done = self.wait_state(key, timeout=30)
        self.assertTrue(done.oom_killed, done)
        self.assertEqual(done.result, "oom-kill")
        self.assertEqual(done.live_pids, [])


class SystemdPriority(SystemdCase):
    def test_an_attempt_runs_at_background_priority(self):
        """The owner's desktop wins CPU contention against agents (D-250): low weight, high nice, in the unit itself."""
        import os
        import subprocess
        key = self.key("prio")
        self.sup.launch(self.spec(key, ["sleep", "30"]))
        self.wait_state(key, "running")
        unit = self.sup.unit_name(key)
        shown = subprocess.run(["systemctl", "--user", "show", unit, "-p", "FragmentPath", "-p", "MainPID"],
                               capture_output=True, text=True, check=True).stdout
        props = dict(line.split("=", 1) for line in shown.splitlines() if "=" in line)
        own = Path(props["FragmentPath"]).read_text(encoding="utf-8")    # the transient unit, not an operator drop-in
        for line in ("Nice=15", "CPUWeight=20", "IOWeight=20"):
            self.assertIn(line, own.splitlines())
        self.assertEqual(os.getpriority(os.PRIO_PROCESS, int(props["MainPID"])), 15)
        self.sup.terminate(key)

    def test_the_engine_unit_carries_the_same_priority(self):
        """M6 verifications run in the engine's own cgroup: its unit yields like an attempt does (D-250)."""
        from bt_supervisor import systemd
        unit = (Path(__file__).resolve().parents[1] / "bt_durable" / "deploy" / "bt-durable.service").read_text()
        for line in systemd.BACKGROUND_PRIORITY:
            self.assertIn(line, unit.splitlines())


class PgroupLimits(PgroupCase, RuntimeLimit):
    def test_memory_limit_is_recorded_as_unenforced(self):
        key = self.key("oomp")
        self.sup.launch(self.spec(key, ["true"], limits=Limits(memory_max_bytes=64 * MIB, tasks_max=10)))
        record = self.sup.store.read(key, "launch.json")
        self.assertEqual(record["unenforced_limits"], ["memory_max_bytes", "tasks_max"])
        self.assertEqual(self.wait_state(key).result, "success")


if __name__ == "__main__":
    unittest.main()
