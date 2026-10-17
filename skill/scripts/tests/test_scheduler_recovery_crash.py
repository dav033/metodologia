"""Recovery checkpoints through durable M1/M3/M5 stores, restarted with the same approved plan."""
from __future__ import annotations

import time

import scheduler_executor_support as support


class SimulatedProcessExit(BaseException):
    pass


class CrashPort:
    def __init__(self, real, *, after_persist):
        self.real, self.after_persist = real, after_persist

    def propose(self, context):
        if self.after_persist:
            self.real.propose(context)
        raise SimulatedProcessExit()


class RecoveryCrashMatrix(support.World):
    def test_restart_before_persist_and_after_persist_before_apply(self):
        for after_persist in (False, True):
            with self.subTest(after_persist=after_persist):
                self.rdir = self.tmp / f"REQ-042-crash-{after_persist}"
                self.rdir.mkdir()
                self.approve([support.task("T1", "recover", scenario="recover")])
                history = self.rdir / "m5.db"
                wiring = self.wire("direct:claude/sonnet@claude-personal", max_attempts=3,
                                      recovery_store_path=history)
                wiring.scheduler.ports.recovery = CrashPort(wiring.recovery, after_persist=after_persist)
                deadline = time.monotonic() + 15
                crashed = False
                while time.monotonic() < deadline:
                    try:
                        wiring.scheduler.step()
                    except SimulatedProcessExit:
                        crashed = True
                        break
                    time.sleep(0.03)
                self.assertTrue(crashed)
                self.assertEqual(wiring.scheduler.snapshot().tasks["T1"]["attempts"], 1)
                wiring.close()
                self.wirings.remove(wiring)
                resumed = self.wire("direct:claude/sonnet@claude-personal", max_attempts=3,
                                       recovery_store_path=history)
                while time.monotonic() < deadline:
                    resumed.scheduler.step()
                    if resumed.scheduler.snapshot().status in {"completed", "blocked"}:
                        break
                    time.sleep(0.03)
                self.assertEqual(resumed.scheduler.snapshot().status, "completed", resumed.recovery.latest())
                self.assertEqual(resumed.scheduler.snapshot().tasks["T1"]["attempts"], 2)
                self.assertEqual(len(resumed.executor.ledger.all_ids()), 2)
                # One wait + one retry even when the first wait was durable before M1 applied it.
                self.assertLessEqual(resumed.recovery.metrics()["decisions"], 2)
