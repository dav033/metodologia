"""The watchdog restarts a dead owner, backs off, honours a hold and the disk, and gives up on repeated failure."""
from __future__ import annotations

import signal
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import bt_scheduler_adapter as adapter
import bt_scheduler_ops as ops
import bt_scheduler_watch as watch


class FakeOwner:
    pid = 4242

    def __init__(self, code):
        self.code = code

    def poll(self):
        return self.code


class WatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.rdir = Path(self.temp.name) / "REQ-001-x"
        self.rdir.mkdir()
        self.clock = [0.0]
        self.sleeps: list[float] = []
        self.notes: list[str] = []
        self.spawned: list[bool] = []
        self.codes: list[int] = []
        patcher = patch.object(adapter, "authority", return_value=adapter.AUTHORITY)
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch.object(ops, "owner_pids", return_value=[])
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch.object(adapter, "run_db_path", return_value=self.rdir / "SCHEDULER.db")
        patcher.start()
        self.addCleanup(patcher.stop)

    def watch(self, free=10 << 30):
        def sleep(seconds):
            self.sleeps.append(seconds)
            self.clock[0] += seconds

        def spawn(resume):
            self.spawned.append(resume)
            return FakeOwner(self.codes.pop(0))

        return watch.Watch("p", "REQ-001", self.rdir, now=lambda: self.clock[0], sleep=sleep, spawn=spawn,
                           free_bytes=lambda: free, notify=lambda title, text: self.notes.append(text), log=lambda t: None)

    def test_terminal_run_ends_the_watch_without_restart(self):
        self.codes = [0]
        self.assertEqual(self.watch().run(), 0)
        self.assertEqual(self.spawned, [True])

    def test_crash_is_restarted_with_growing_backoff(self):
        self.codes = [3, -signal.SIGBUS, 0]
        self.assertEqual(self.watch().run(), 0)
        self.assertEqual(len(self.spawned), 3)
        self.assertEqual(self.sleeps, [watch.BACKOFF_START, watch.BACKOFF_START * 2])

    def test_repeated_crashes_give_up_and_notify(self):
        self.codes = [3] * 10
        self.assertEqual(self.watch().run(), 4)
        self.assertEqual(len(self.spawned), watch.MAX_FAILURES)
        self.assertEqual(len(self.notes), 1)

    def test_a_refusal_is_not_retried(self):
        self.codes = [2]
        self.assertEqual(self.watch().run(), 2)
        self.assertEqual(len(self.spawned), 1)
        self.assertEqual(len(self.notes), 1)

    def test_a_long_healthy_owner_resets_the_failure_budget(self):
        watcher = self.watch()
        times = iter(range(100))

        def spawn(resume):
            self.clock[0] += watch.HEALTHY_SECONDS + 1 if next(times) % 2 == 0 else 1
            return FakeOwner(self.codes.pop(0))

        watcher.spawn = spawn
        self.codes = [3] * 8 + [0]
        self.assertEqual(watcher.run(), 0)

    def test_sigterm_is_a_deliberate_stop_not_a_failure(self):
        self.codes = [-signal.SIGTERM, 0]
        watcher = self.watch()
        self.assertEqual(watcher.run(), 0)
        self.assertEqual(len(watcher.failures), 0)
        self.assertEqual(self.sleeps, [])

    def test_a_hold_pauses_the_restart(self):
        ops.hold_path(self.rdir).write_text("{}")
        watcher = self.watch()
        self.codes = [0]
        watcher.run(max_loops=2)
        self.assertEqual(self.spawned, [])
        ops.hold_path(self.rdir).unlink()
        self.assertEqual(watcher.run(max_loops=2), 0)
        self.assertEqual(self.spawned, [True])

    def test_low_disk_waits_and_tells_once(self):
        watcher = self.watch(free=1 << 20)
        self.codes = [0]
        watcher.run(max_loops=3)
        self.assertEqual(self.spawned, [])
        self.assertEqual(len(self.notes), 1)

    def test_a_first_start_is_not_a_resume(self):
        with patch.object(adapter, "authority", return_value="none"):
            self.codes = [0]
            self.watch().run()
        self.assertEqual(self.spawned, [False])

    def test_second_watchdog_exits_quietly(self):
        with watch.single_instance(self.rdir) as first:
            self.assertTrue(first)
            with watch.single_instance(self.rdir) as second:
                self.assertFalse(second)
            self.assertTrue(ops.watching(self.rdir))
        self.assertFalse(ops.watching(self.rdir))


class ArgvMatching(unittest.TestCase):
    def test_only_an_exact_owner_command_matches(self):
        run = ["/usr/bin/python3", "bitacora.py", "--project", "pictures", "scheduler-run", "REQ-019", "--resume"]
        self.assertTrue(ops._command_matches(run, "scheduler-run", "pictures", "REQ-019"))
        self.assertFalse(ops._command_matches(run, "scheduler-run", "pictures", "REQ-018"))
        self.assertFalse(ops._command_matches(run, "scheduler-run", "other", "REQ-019"))
        self.assertFalse(ops._command_matches(run, "scheduler-watch", "pictures", "REQ-019"))
        self.assertFalse(ops._command_matches(["vim", "bitacora.py", "--project", "pictures", "scheduler-run", "REQ-019"],
                                              "scheduler-run", "pictures", "REQ-019"))
        self.assertFalse(ops._command_matches(["tail", "-f", "scheduler-run", "REQ-019"],
                                              "scheduler-run", "pictures", "REQ-019"))


if __name__ == "__main__":
    unittest.main()
