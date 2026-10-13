"""A resumed marathon must not leave the previous run's agent session editing the worktree."""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import bt_runsession  # noqa: E402  (imports bt_core: this file must sort after test_marathon.py)


def alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


@unittest.skipUnless(sys.platform.startswith("linux"), "identity proof needs /proc")
class OrphanTests(unittest.TestCase):
    def spawn(self, **env):
        proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"], start_new_session=True,
                                env={**os.environ, **env})
        self.addCleanup(proc.wait)  # cleanups run last-in first-out: kill first, then reap
        self.addCleanup(lambda: proc.poll() is None and proc.kill())
        time.sleep(0.2)
        return proc

    def state(self, pid):
        return {"req": "REQ-001", "heartbeat": {"session_pid": pid, "machine": socket.gethostname()}}

    def test_matching_orphan_is_ended(self):
        proc = self.spawn(BITACORA_RUN="REQ-001", BITACORA_PROJECT="demo")
        msg = bt_runsession.reap_orphan("demo", self.state(proc.pid))
        self.assertIn("ended orphaned session", msg)
        proc.wait(timeout=5)
        self.assertFalse(alive(proc.pid) and proc.poll() is None)

    def test_other_run_or_recycled_pid_is_left_alone(self):
        for env in ({"BITACORA_RUN": "REQ-009", "BITACORA_PROJECT": "demo"}, {}):
            proc = self.spawn(**env)
            self.assertIsNone(bt_runsession.reap_orphan("demo", self.state(proc.pid)))
            self.assertIsNone(proc.poll())

    def test_nothing_to_do_without_a_recorded_live_session(self):
        for hb in ({}, {"session_pid": None}, {"session_pid": 999999999, "machine": socket.gethostname()},
                   {"session_pid": os.getpid(), "machine": "another-host"}):
            self.assertIsNone(bt_runsession.reap_orphan("demo", {"req": "REQ-001", "heartbeat": hb}))


if __name__ == "__main__":
    unittest.main()
