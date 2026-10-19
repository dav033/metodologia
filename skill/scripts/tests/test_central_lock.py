"""Shared central locks serialize concurrent writers."""
import os
import subprocess
import sys
import threading
import unittest
from pathlib import Path
from run_case_support import TMP, SCRIPTS
import bt_lock

class CentralLock(unittest.TestCase):
    def test_threads_do_not_interleave_read_modify_write(self):
        counter = TMP / "counter.txt"
        counter.write_text("0")

        def bump():
            for _ in range(40):
                with bt_lock.central_lock("test-counter"):
                    value = int(counter.read_text())
                    counter.write_text(str(value + 1))

        threads = [threading.Thread(target=bump) for _ in range(4)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        self.assertEqual(int(counter.read_text()), 160)

    def test_lock_is_reentrant_and_released(self):
        with bt_lock.central_lock("test-reentrant"):
            with bt_lock.central_lock("test-reentrant"):
                pass
        lock = Path(os.environ["BITACORA_ROOT"]) / ".state" / "locks" / "central-test-reentrant.lock"
        self.assertFalse(lock.exists())

    def test_two_processes_serialize(self):
        counter = TMP / "proc-counter.txt"
        counter.write_text("0")
        code = (f"import sys; sys.path.insert(0, {str(SCRIPTS)!r})\nimport bt_lock, pathlib\n"
                f"p = pathlib.Path({str(counter)!r})\nfor _ in range(30):\n"
                f"    with bt_lock.central_lock('test-proc'):\n        p.write_text(str(int(p.read_text()) + 1))\n")
        procs = [subprocess.Popen([sys.executable, "-c", code], env=os.environ.copy()) for _ in range(3)]
        [p.wait(timeout=60) for p in procs]
        self.assertEqual(int(counter.read_text()), 90)
