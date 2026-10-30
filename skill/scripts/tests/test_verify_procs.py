"""Which processes belong to a test version, and stopping exactly those (owner, 2026-10-30: never by port alone)."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bt_verify_procs as procs

SLEEP = [sys.executable, "-c", "import time; time.sleep(60)"]
SERVE = [sys.executable, "-m", "http.server", "0", "--bind", "127.0.0.1"]


def _wait(cond, timeout=10.0) -> bool:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if cond():
            return True
        time.sleep(0.1)
    return False


class Ownership(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="bt-verify-procs-"))
        self.copy = self.tmp / "SP-1-v1"
        self.copy.mkdir()
        self.started: list[subprocess.Popen] = []

    def tearDown(self):
        for proc in self.started:
            proc.kill()
            proc.wait(timeout=5)

    def spawn(self, args, cwd=None, mark="", **kw) -> subprocess.Popen:
        env = {**os.environ, procs.MARK: mark} if mark else {k: v for k, v in os.environ.items() if k != procs.MARK}
        proc = subprocess.Popen(args, cwd=cwd or self.tmp, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **kw)
        self.started.append(proc)
        return proc

    def listening(self, pid: int) -> bool:
        return any(pid in pids for pids in procs.listeners().values())

    def test_the_mark_a_listener_in_the_copy_and_their_children_belong_to_the_version(self):
        marked = self.spawn(["bash", "-c", f"{SLEEP[0]} -c 'import time; time.sleep(60)' & wait"], mark="p/REQ-1/SP-1-v1")
        server = self.spawn(SERVE, cwd=self.copy)                       # started by hand, before marks existed
        editor = self.spawn(SLEEP, cwd=self.copy)                       # an editor or a shell in the copy: not a server
        other = self.spawn(SLEEP, mark="p/REQ-1/SP-2-v1")                # another version
        elsewhere = self.spawn(SERVE)                                   # a server outside the copy (pid 2419 on 8000)
        self.assertTrue(_wait(lambda: self.listening(server.pid) and self.listening(elsewhere.pid)))
        self.assertTrue(_wait(lambda: len(procs.descendants({marked.pid})) > 1))
        found = procs.owned("p/REQ-1/SP-1-v1", self.copy)
        self.assertTrue(procs.descendants({marked.pid}) <= found)
        self.assertIn(server.pid, found)
        self.assertFalse({editor.pid, other.pid, elsewhere.pid} & found)
        self.assertNotIn(os.getpid(), found)

    def test_listeners_maps_a_port_to_its_process_and_port_busy_sees_it(self):
        server = self.spawn(SERVE)
        self.assertTrue(_wait(lambda: self.listening(server.pid)))
        port = next(p for p, pids in procs.listeners().items() if server.pid in pids)
        self.assertTrue(procs.port_busy(port))

    def test_terminate_kills_a_whole_group_only_when_every_member_is_meant(self):
        group = self.spawn(["bash", "-c", f"{SLEEP[0]} -c 'import time; time.sleep(60)' & exec {SLEEP[0]} -c "
                            "'import time; time.sleep(60)'"], start_new_session=True)     # a leader that outlives its child
        self.assertTrue(_wait(lambda: len(procs.descendants({group.pid})) > 1))
        child = next(iter(procs.descendants({group.pid}) - {group.pid}))
        procs.terminate({child}, grace=3)                               # one member asked: its leader is not someone else's
        self.assertFalse(procs.alive(child))
        self.assertIsNone(group.poll())
        group2 = self.spawn(["bash", "-c", f"{SLEEP[0]} -c 'import time; time.sleep(60)' & wait"], start_new_session=True)
        self.assertTrue(_wait(lambda: len(procs.descendants({group2.pid})) > 1))
        everyone = procs.descendants({group2.pid})
        procs.terminate(everyone, grace=3)
        group2.wait(timeout=5)
        self.assertFalse(any(procs.alive(p) for p in everyone))

    def test_a_process_that_ignores_sigterm_is_killed_after_the_grace(self):
        stubborn = subprocess.Popen([sys.executable, "-c", "import signal, time; signal.signal(signal.SIGTERM, "
                                     "signal.SIG_IGN); print('ok', flush=True); time.sleep(60)"],
                                    stdout=subprocess.PIPE, text=True)
        self.started.append(stubborn)
        stubborn.stdout.readline()
        started = time.monotonic()
        procs.terminate({stubborn.pid}, grace=0.5)
        stubborn.wait(timeout=5)
        self.assertLess(time.monotonic() - started, 5)


if __name__ == "__main__":
    unittest.main()
