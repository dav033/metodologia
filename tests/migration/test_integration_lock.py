"""Integration lease contention and process identity safety."""
from __future__ import annotations

import json
import multiprocessing
import os
import tempfile
import time
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skill" / "scripts"))
import bt_integration_lock as lease  # noqa: E402


def _hold(path: str, ready: multiprocessing.synchronize.Event, seconds: float) -> None:
    lock = lease.IntegrationLock(path).acquire(timeout=3)
    ready.set()
    time.sleep(seconds)
    lock.release()


def _reclaim(path: str, outcomes: multiprocessing.Queue) -> None:
    try:
        lease.IntegrationLock(path).acquire(timeout=0.1, poll_interval=0.005).release()
        outcomes.put("acquired")
    except (lease.LockHeld, lease.LockTimeout):
        outcomes.put("held")


def _poll(path: str, done: multiprocessing.synchronize.Event, failures: multiprocessing.Queue) -> None:
    lock_path = Path(path) / "integration.lock"
    while not done.is_set():
        if lock_path.exists():
            try:
                owner = json.loads(lock_path.read_text(encoding="utf-8"))
                if not all(key in owner for key in ("host", "pid", "start", "heartbeat")):
                    failures.put("short")
            except (OSError, json.JSONDecodeError):
                failures.put("partial")


class IntegrationLockTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="integration-lock-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def test_two_processes_contend_and_timeout_never_proceeds_unlocked(self) -> None:
        ready = multiprocessing.Event()
        child = multiprocessing.Process(target=_hold, args=(str(self.root), ready, 1.0))
        child.start()
        self.assertTrue(ready.wait(3))
        with self.assertRaises(lease.LockTimeout):
            lease.IntegrationLock(self.root).acquire(timeout=0.1, poll_interval=0.01)
        child.join(3)
        self.assertEqual(child.exitcode, 0)
        with lease.IntegrationLock(self.root).acquire(timeout=0.2):
            self.assertTrue((self.root / "integration.lock").exists())

    def test_killed_owner_can_be_reclaimed_only_after_verified_death(self) -> None:
        ready = multiprocessing.Event()
        child = multiprocessing.Process(target=_hold, args=(str(self.root), ready, 30.0))
        child.start()
        self.assertTrue(ready.wait(3))
        child.kill()
        child.join(3)
        self.assertNotEqual(child.exitcode, 0)
        with lease.IntegrationLock(self.root).acquire(timeout=1):
            self.assertTrue((self.root / "integration.lock").exists())

    def test_same_pid_from_another_host_cannot_steal(self) -> None:
        path = self.root / "integration.lock"
        path.write_text(json.dumps({"host": "elsewhere", "pid": os.getpid(), "start": lease.process_start_time(os.getpid()), "heartbeat": 0}))
        with self.assertRaisesRegex(lease.LockHeld, "host"):
            lease.IntegrationLock(self.root, host_id="local").acquire(timeout=0)
        self.assertTrue(path.exists())

    def test_unknown_liveness_is_never_reclaimed(self) -> None:
        path = self.root / "integration.lock"
        path.write_text(json.dumps({"host": lease.socket.gethostname(), "pid": os.getpid(), "start": "unknown", "heartbeat": 0}))
        with self.assertRaisesRegex(lease.LockHeld, "unknown|unverifiable"):
            lease.IntegrationLock(self.root).acquire(timeout=0)
        self.assertTrue(path.exists())

    def test_old_file_age_does_not_release_live_owner(self) -> None:
        path = self.root / "integration.lock"
        path.write_text(json.dumps({"host": lease.socket.gethostname(), "pid": os.getpid(),
                                    "start": lease.process_start_time(os.getpid()), "heartbeat": 0}))
        os.utime(path, (1, 1))
        with self.assertRaises(lease.LockTimeout):
            lease.IntegrationLock(self.root).acquire(timeout=0)
        self.assertTrue(path.exists())

    def test_racing_reclaimers_never_remove_a_live_owner(self) -> None:
        ready = multiprocessing.Event()
        child = multiprocessing.Process(target=_hold, args=(str(self.root), ready, 2.0))
        child.start()
        self.assertTrue(ready.wait(3))
        outcomes = multiprocessing.Queue()
        workers = [multiprocessing.Process(target=_reclaim, args=(str(self.root), outcomes)) for _ in range(2)]
        for worker in workers: worker.start()
        for worker in workers: worker.join(2)
        self.assertTrue((self.root / "integration.lock").exists())
        owner = json.loads((self.root / "integration.lock").read_text(encoding="utf-8"))
        self.assertEqual(owner["pid"], child.pid)
        child.kill()
        child.join(2)
        self.assertNotEqual(child.exitcode, 0)

    def test_acquire_and_renew_publish_only_complete_owner_records(self) -> None:
        done = multiprocessing.Event()
        failures = multiprocessing.Queue()
        reader = multiprocessing.Process(target=_poll, args=(str(self.root), done, failures))
        reader.start()
        lock = lease.IntegrationLock(self.root).acquire()
        for _ in range(20): lock.renew()
        done.set(); reader.join(2); lock.release()
        self.assertTrue(failures.empty())


if __name__ == "__main__":
    unittest.main()
