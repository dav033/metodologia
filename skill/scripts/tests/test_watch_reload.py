"""A fix merged while a run lives reaches the watcher and the owner without a person restarting them."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bt_scheduler_ops as ops  # noqa: E402
import bt_scheduler_watch as watch  # noqa: E402
import bt_watch_reload as reload  # noqa: E402


def decide(**over):
    base = dict(current="b", stable=True, watcher_started_with="b", owner_started_with="b", owner_alive=True, live_states=[], waited=0.0)
    base.update(over)
    return reload.decide(**base)


class Decide(unittest.TestCase):
    def test_nothing_changed_nothing_happens(self):
        self.assertEqual(decide(), "none")

    def test_an_edit_still_landing_is_not_a_release(self):
        self.assertEqual(decide(current="c", stable=False), "none")

    def test_a_changed_engine_restarts_the_watcher_first(self):
        self.assertEqual(decide(current="c"), "reexec")

    def test_the_owner_is_restarted_at_once_when_idle_and_waits_otherwise(self):
        owner_old = dict(watcher_started_with="c", current="c", owner_started_with="b")
        self.assertEqual(decide(**owner_old), "restart_owner")
        self.assertEqual(decide(**owner_old, live_states=["verifying"], waited=60), "none")
        self.assertEqual(decide(**owner_old, live_states=["verifying"], waited=reload.PATIENCE_VERIFYING), "restart_owner")
        self.assertEqual(decide(**owner_old, live_states=["running"], waited=reload.PATIENCE_VERIFYING), "none")   # an agent is working
        self.assertEqual(decide(**owner_old, live_states=["running", "verifying"], waited=reload.PATIENCE_BUSY), "restart_owner")

    def test_a_dead_owner_or_an_unmarked_one_is_left_to_the_watchdog(self):
        self.assertEqual(decide(watcher_started_with="c", current="c", owner_alive=False), "none")
        self.assertEqual(decide(watcher_started_with="c", current="c", owner_started_with=""), "none")


class Committed(unittest.TestCase):
    def test_only_a_clean_committed_engine_is_released(self):
        import subprocess

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skill" / "scripts"
            root.mkdir(parents=True)
            git = lambda *a: subprocess.run(["git", "-C", tmp, "-c", "user.name=t", "-c", "user.email=t@t", *a], check=True, capture_output=True)  # noqa: E731
            git("init", "-q")
            (root / "a.py").write_text("x = 1")
            git("add", "."), git("commit", "-qm", "one")
            first = reload.fingerprint(root)
            self.assertNotIn(first, ("", reload.DIRTY))
            (root / "a.py").write_text("x = 2")                     # an edit in flight: not released
            self.assertEqual(reload.fingerprint(root), reload.DIRTY)
            git("add", "."), git("commit", "-qm", "two")
            self.assertNotIn(reload.fingerprint(root), (first, reload.DIRTY))   # committed: a new release
            (root / "tests").mkdir()
            (root / "tests" / "test_a.py").write_text("z")          # a test edit is not an engine change
            self.assertNotEqual(reload.fingerprint(root), reload.DIRTY)

    def test_a_dirty_or_unknown_fingerprint_decides_nothing(self):
        self.assertEqual(decide(current=reload.DIRTY, watcher_started_with="b"), "none")
        self.assertEqual(decide(current="", watcher_started_with="b"), "none")


class Fingerprint(unittest.TestCase):
    def test_it_follows_the_engine_sources_and_ignores_tests_and_caches(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.py").write_text("x = 1")
            (root / "tests").mkdir()
            (root / "__pycache__").mkdir()
            before = reload.fingerprint(root)
            (root / "tests" / "test_a.py").write_text("y")
            (root / "__pycache__" / "a.py").write_text("z")
            self.assertEqual(reload.fingerprint(root), before)
            (root / "a.py").write_text("x = 22")
            self.assertNotEqual(reload.fingerprint(root), before)

    def test_the_owners_marker_round_trips_and_a_missing_one_is_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(reload.read_marker(tmp), "")
            reload.write_marker(tmp, "abc")
            self.assertEqual(reload.read_marker(tmp), "abc")


class Watcher(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.rdir = Path(self.tmp.name)
        self.logged, self.execs, self.stops = [], [], []
        self.fp = ["v1"]

    def watcher(self):
        return watch.Watch("p", "REQ-1", self.rdir, fingerprint=lambda: self.fp[0], reexec=lambda *a: self.execs.append(a),
                           log=self.logged.append, now=lambda: 1000.0)

    def check(self, w, live=()):
        with patch.object(ops, "status", return_value={"live_attempts": [{"state": s} for s in live]}), \
                patch.object(ops, "owner_pids", return_value=[7]), patch.object(ops, "stop_owner", side_effect=lambda *a: self.stops.append(a) or 1):
            w._reload_check()

    def test_a_new_engine_makes_the_watcher_restart_itself_after_two_equal_checks(self):
        w = self.watcher()
        reload.write_marker(self.rdir, "v1")
        self.fp[0] = "v2"
        self.check(w)                                   # first sight of v2: not yet stable
        self.assertEqual(self.execs, [])
        self.check(w)                                   # same again: release
        self.assertEqual(self.execs, [("p", "REQ-1")])

    def test_an_idle_owner_on_old_code_is_stopped_so_the_watchdog_restarts_it(self):
        w = self.watcher()
        reload.write_marker(self.rdir, "v0")
        self.check(w)                                   # the watcher already runs v1 and the files did not move: only the owner is old
        self.assertEqual(self.stops, [("p", "REQ-1")])
        self.assertEqual(self.execs, [])

    def test_a_busy_owner_is_not_touched(self):
        w = self.watcher()
        reload.write_marker(self.rdir, "v0")
        self.check(w, live=["running"])
        self.check(w, live=["running"])
        self.assertEqual(self.stops, [])

    def test_the_owner_the_watcher_started_itself_is_also_checked_for_a_new_engine(self):
        """REQ-001 (david-ui): `_wait(owner)` ran the healing every 5 s but never the reload check, so the watcher stayed on its 06:14 code
        for hours (the manual reviewer never ran there). The check now runs every HEAL_SECONDS while the watcher waits for its own owner."""
        clock = [1000.0]
        checks = []
        w = watch.Watch("p", "REQ-1", self.rdir, fingerprint=lambda: "v1", reexec=lambda *a: None, log=self.logged.append,
                        now=lambda: clock[0], sleep=lambda seconds: clock.__setitem__(0, clock[0] + seconds), heal=lambda: False,
                        announce=lambda: None)
        w._reload_check = lambda: checks.append(clock[0])

        class Owner:
            polls = 0

            def poll(self):
                Owner.polls += 1
                return 0 if Owner.polls > 20 else None            # about 100 s of waiting

        self.assertEqual(w._wait(Owner()), 0)
        self.assertGreaterEqual(len(checks), 3)

    def test_a_failing_check_never_stops_the_watch(self):
        w = self.watcher()
        with patch.object(ops, "status", side_effect=RuntimeError("db locked")):
            w._reload_check()
        self.assertTrue(any("reload check failed" in line for line in self.logged))


if __name__ == "__main__":
    unittest.main()
