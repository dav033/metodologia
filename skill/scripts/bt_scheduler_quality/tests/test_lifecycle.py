from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace

import bt_scheduler_executor_adapter as executor_adapter
from bt_scheduler_quality.policy import QualityPolicy
from bt_scheduler_quality.store import QualityStore
from bt_scheduler_quality_adapter import QualityVerificationPort


class SlowDispatcher:
    def __init__(self):
        self.join_started = threading.Event()
        self.release = threading.Event()
        self.timeout = "not-called"

    def join(self, timeout=None):
        self.timeout = timeout
        self.join_started.set()
        if timeout is None:
            self.release.wait(timeout=3)


class TrackedStore:
    def __init__(self, wrapped):
        self.wrapped = wrapped
        self.closed = threading.Event()

    def close(self):
        self.closed.set()
        self.wrapped.close()


class Stream:
    def close_all(self):
        return None


class Executor:
    def close(self):
        return None


class WiringShutdownTests(unittest.TestCase):
    def test_wiring_waits_for_slow_m6_dispatcher_before_closing_store(self):
        with tempfile.TemporaryDirectory(prefix="m6-lifecycle-") as temporary:
            attempts_root = Path(temporary)
            store = QualityStore(":memory:")
            runtime = QualityVerificationPort(
                object(),
                SimpleNamespace(attempts_dir=attempts_root),
                store,
                QualityPolicy(),
                lambda _order: attempts_root,
            )
            self.addCleanup(store.close)
            self.addCleanup(runtime.close)
            runtime.start()
            dispatcher = runtime._thread
            runtime._stop.set()
            runtime._wake.set()
            dispatcher.join(timeout=2)
            self.assertFalse(dispatcher.is_alive())

            slow = SlowDispatcher()
            self.addCleanup(slow.release.set)
            runtime._thread = slow
            tracked_store = TrackedStore(store)
            wiring = executor_adapter.Wiring(
                None,
                Executor(),
                None,
                None,
                Stream(),
                verification_runtime=runtime,
                verification_store=tracked_store,
            )
            close_errors = []

            def close_wiring():
                try:
                    wiring.close()
                except Exception as error:  # noqa: BLE001
                    close_errors.append(error)

            closer = threading.Thread(target=close_wiring)
            closer.start()
            self.assertTrue(slow.join_started.wait(timeout=2))
            self.assertIsNone(slow.timeout)
            self.assertTrue(closer.is_alive())
            self.assertFalse(tracked_store.closed.is_set())

            slow.release.set()
            closer.join(timeout=2)

            self.assertFalse(closer.is_alive())
            self.assertEqual(close_errors, [])
            self.assertTrue(tracked_store.closed.is_set())


if __name__ == "__main__":
    unittest.main()
