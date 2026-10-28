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


class PgroupLimits(PgroupCase, RuntimeLimit):
    def test_memory_limit_is_recorded_as_unenforced(self):
        key = self.key("oomp")
        self.sup.launch(self.spec(key, ["true"], limits=Limits(memory_max_bytes=64 * MIB, tasks_max=10)))
        record = self.sup.store.read(key, "launch.json")
        self.assertEqual(record["unenforced_limits"], ["memory_max_bytes", "tasks_max"])
        self.assertEqual(self.wait_state(key).result, "success")


if __name__ == "__main__":
    unittest.main()
