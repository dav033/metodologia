"""Recovery through actual M1 and M3 stores/processes, with controlled external provider failures."""
from __future__ import annotations

import time
from pathlib import Path

import scheduler_executor_support as support
from scheduler_executor_support import adapter, core


class RecoveryFailures(support.World):
    def pump(self, wiring, *, deadline_seconds=20):
        deadline = time.monotonic() + deadline_seconds
        while time.monotonic() < deadline:
            wiring.scheduler.step()
            if wiring.scheduler.snapshot().status in {"completed", "blocked", "cancelled"}:
                return wiring.scheduler.snapshot()
            time.sleep(0.03)
        self.fail(f"recovery did not settle: {wiring.scheduler.snapshot()}")

    def test_one_quota_failure_leaves_independent_branch_running_and_preserves_work(self):
        self.approve([support.task("T1", "quota", scenario="quota"),
                      support.task("T2", "independent", repo="docs"), support.task("T3", "dependent", ["T1"])])
        wiring = self.wire("direct:claude/sonnet@claude-personal", max_attempts=4,
                              recovery_store_path=self.tmp / "m5.db")
        snap = self.pump(wiring)
        self.assertEqual((snap.tasks["T1"]["state"], snap.tasks["T2"]["state"]), ("blocked", "completed"))
        self.assertIn("T3", snap.unreachable)
        failed = wiring.executor.describe(snap.tasks["T1"]["attempt"])
        self.assertEqual(failed["handoff"]["status"], "captured")
        self.assertTrue(Path(failed["handoff"]["worktree"]).joinpath("claude-half.txt").exists())
        self.assertIn("wait_window_exceeded", snap.tasks["T1"]["reason"])

    def test_repeated_connection_failure_is_bounded_below_large_core_budget(self):
        self.approve([support.task("T1", "network", scenario="net")])
        wiring = self.wire("direct:claude/sonnet@claude-personal", max_attempts=10,
                              recovery_store_path=self.tmp / "m5.db")
        snap = self.pump(wiring)
        self.assertEqual((snap.tasks["T1"]["attempts"], snap.tasks["T1"]["state"]), (3, "blocked"))
        self.assertEqual(snap.tasks["T1"]["reason"], "m5:same_cause_limit")
        self.assertEqual(wiring.recovery.metrics()["decisions"], 5)
        for aid in wiring.executor.ledger.all_ids():
            self.assertEqual(wiring.executor.describe(aid)["handoff"]["status"], "captured")

    def test_timeout_retry_does_not_increase_timeout_or_loop(self):
        self.approve([support.task("T1", "timeout", scenario="sleep")])
        wiring = self.wire(
            "direct:claude/sonnet@claude-personal", max_attempts=10,
            executor_config=adapter.m3.Config(timeout_seconds=0.2, grace_seconds=0.1, poll_seconds=0.02),
            recovery_store_path=self.tmp / "m5.db")
        snap = self.pump(wiring)
        self.assertEqual((snap.tasks["T1"]["attempts"], snap.tasks["T1"]["reason"]), (2, "m5:timeout_repeated"))
        self.assertEqual(wiring.executor.cfg.timeout_seconds, 0.2)

    def test_unauthorized_profile_is_never_recovered_through_another_account(self):
        self.approve([support.task("T1", "profile")])
        wiring = self.wire("direct:claude/sonnet@claude-work", max_attempts=5,
                              recovery_store_path=self.tmp / "m5.db")
        snap = self.pump(wiring)
        self.assertEqual((snap.tasks["T1"]["state"], snap.tasks["T1"]["attempts"]), ("blocked", 1))
        self.assertEqual(self.records(), [])

    def test_human_cancellation_never_resumes_or_records_recovery_history(self):
        self.approve([support.task("T1", "cancel", scenario="sleep")])
        history = self.tmp / "m5.db"
        wiring = self.wire("direct:claude/sonnet@claude-personal", max_attempts=5,
                              recovery_store_path=history)
        wiring.scheduler.step()
        wiring.scheduler.cancel("owner", "stop")
        snap = self.pump(wiring)
        self.assertEqual((snap.status, snap.tasks["T1"]["attempts"]), ("cancelled", 1))
        self.assertTrue(history.exists())
        self.assertEqual(wiring.recovery.metrics()["decisions"], 0)

    def test_legacy_run_and_two_recovery_owners_are_refused_before_launch(self):
        self.approve([support.task("T1", "legacy")])
        with self.assertRaisesRegex(ValueError, "supply recovery"):
            adapter.wire(self.rdir, project="proj", recovery=object(), recovery_store_path=self.tmp / "m5.db")
        legacy = self.rdir / "RUN.json"
        legacy.write_bytes(b'{"schema":0,"keep":"unchanged"}')
        with self.assertRaises(core.SchedulerError):
            adapter.wire(self.rdir, project="proj", recovery_store_path=self.tmp / "m5.db")
        self.assertEqual(legacy.read_bytes(), b'{"schema":0,"keep":"unchanged"}')
        self.assertEqual(self.records(), [])
