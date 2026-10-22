from __future__ import annotations

import sys
import sqlite3
import threading
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import Harness, approved, indep, plan_text, sqlite_path
import bt_scheduler_core as sc


class RecoveryRevisionBarrierTests(unittest.TestCase):
    def test_barrier_waits_for_live_work_then_applies_without_resetting_counters(self):
        old_tasks = [indep("T1"), indep("T2", ["T1"])]
        harness = Harness(old_tasks, parallel=1)
        harness.core.step()
        harness.finish_and_accept("T1")
        harness.core.step()
        self.assertEqual(harness.state("T2"), "active")
        old, _ = approved(plan_text(old_tasks))
        new, _ = approved(plan_text(old_tasks + [indep("T3", ["T2"])], revision=2))
        initial = harness.core.read(lambda ctx: (sc.accepted_map_digest(ctx.state), sc.stop_generation(ctx.state)))
        guard = sc.RevisionGuard("grant-1", old.sha256, new.sha256, initial[0], initial[1],
                                 ("T3",), "b" * 64, None, 1000)
        waiting = sc.apply_plan_revision(harness.repo, old, new, guard, clock=lambda: 100)
        self.assertEqual(waiting.outcome, "waiting")
        self.assertEqual(waiting.live_attempt_ids, (harness.attempt("T2"),))
        harness.finish_and_accept("T2")
        settled = harness.core.read(lambda ctx: dict(ctx.state.counters))
        applied = sc.apply_plan_revision(harness.repo, old, new, guard, clock=lambda: 101)
        self.assertEqual(applied.outcome, "applied")
        with harness.repo.read_transaction() as tx:
            self.assertEqual(tx.state.tasks["T1"].state, "completed")
            self.assertEqual(tx.state.tasks["T2"].state, "completed")
            self.assertEqual(tx.state.tasks["T3"].state, "ready")
            for counter in ("attempt", "token", "outbox"):
                self.assertEqual(tx.state.counters[counter], settled[counter])

    def test_stop_race_aborts_barrier_and_leaves_run_unmodified(self):
        tasks = [indep("T1")]
        harness = Harness(tasks, parallel=1)
        harness.core.step()
        old, _ = approved(plan_text(tasks))
        new, _ = approved(plan_text(tasks + [indep("T2", ["T1"])], revision=2))
        digest = harness.core.read(lambda ctx: sc.accepted_map_digest(ctx.state))
        generation = harness.core.read(lambda ctx: sc.stop_generation(ctx.state))
        guard = sc.RevisionGuard("grant-stop", old.sha256, new.sha256, digest, generation,
                                 ("T2",), "b" * 64, None, 1000)
        self.assertEqual(sc.apply_plan_revision(harness.repo, old, new, guard, clock=lambda: 100).outcome, "waiting")
        harness.core.pause("owner")
        result = sc.apply_plan_revision(harness.repo, old, new, guard, clock=lambda: 101)
        self.assertEqual((result.outcome, result.reason), ("refused", "stopped"))
        with harness.repo.read_transaction() as tx:
            self.assertIsNone(tx.state.revision_barrier)
            self.assertEqual(tx.state.revision, 1)

    def test_integrated_base_is_rechecked_inside_the_m1_transaction(self):
        temp, database = sqlite_path()
        self.addCleanup(temp.cleanup)
        tasks = [indep("T1")]
        harness = Harness(tasks, repository=sc.SqliteRepository(database), parallel=1)
        old, _ = approved(plan_text(tasks))
        new, _ = approved(plan_text(tasks + [indep("T2", ["T1"])], revision=2))
        identity = harness.core.read(lambda ctx: (sc.accepted_map_digest(ctx.state), sc.stop_generation(ctx.state)))
        base = {"digest": "b" * 64}
        entered = threading.Event()
        result = []
        guard = sc.RevisionGuard("grant-base", old.sha256, new.sha256, identity[0], identity[1],
                                 ("T2",), "b" * 64, lambda: (entered.set(), base["digest"])[1], 10**12)
        blocker = sqlite3.connect(database, timeout=5, isolation_level=None)
        blocker.execute("BEGIN IMMEDIATE")
        worker = threading.Thread(target=lambda: result.append(
            sc.apply_plan_revision(harness.repo, old, new, guard, clock=lambda: 100)))
        worker.start()
        time.sleep(0.05)
        self.assertFalse(entered.is_set())
        base["digest"] = "c" * 64
        blocker.execute("COMMIT")
        blocker.close()
        worker.join(timeout=5)
        self.assertFalse(worker.is_alive())
        self.assertEqual((result[0].outcome, result[0].reason), ("refused", "stale_base"))
        with harness.repo.read_transaction() as tx:
            self.assertEqual(tx.state.revision, 1)
            self.assertIsNone(tx.state.revision_barrier)

    def test_expired_barrier_allows_one_bounded_re_request(self):
        tasks = [indep("T1")]
        harness = Harness(tasks, parallel=1)
        harness.core.step()
        old, _ = approved(plan_text(tasks))
        new, _ = approved(plan_text(tasks + [indep("T2", ["T1"])], revision=2))
        accepted = harness.core.read(lambda ctx: sc.accepted_map_digest(ctx.state))
        stop = harness.core.read(lambda ctx: sc.stop_generation(ctx.state))
        def guard(deadline):
            return sc.RevisionGuard("grant-expiry", old.sha256, new.sha256, accepted, stop,
                                    ("T2",), "b" * 64, None, deadline)

        first = sc.apply_plan_revision(harness.repo, old, new, guard(100), clock=lambda: 90)
        expired_once = sc.apply_plan_revision(harness.repo, old, new, guard(100), clock=lambda: 101)
        retried = sc.apply_plan_revision(harness.repo, old, new, guard(200), clock=lambda: 102)
        expired_twice = sc.apply_plan_revision(harness.repo, old, new, guard(200), clock=lambda: 201)
        self.assertEqual(first.outcome, "waiting")
        self.assertEqual((expired_once.outcome, expired_once.reason), ("waiting", "barrier_expired"))
        self.assertEqual(retried.outcome, "waiting")
        self.assertEqual((expired_twice.outcome, expired_twice.reason), ("waiting", "barrier_expired"))


if __name__ == "__main__":
    unittest.main()
