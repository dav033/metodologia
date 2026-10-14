"""Regression tests for what the independent reviews found: each test names the defect it pins."""
from __future__ import annotations

import hashlib
import sqlite3
import sys
import threading
import time
import unittest
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2])]

from support import Harness, approved, indep, plan_text, sqlite_path

import bt_scheduler_core as sc
from bt_scheduler_core.model import SEEN_LIMIT, RunState


class RefusedIsNotRemembered(unittest.TestCase):
    def test_a_verdict_refused_as_early_is_applied_when_the_same_id_is_retried_in_time(self):
        h = Harness([indep("T1")])
        h.core.step()
        self.assertEqual(h.verdict("T1", verdict_id="retry-me").status, "stale")        # executor has not finished yet
        h.send("T1", "execution_finished")
        self.assertEqual(h.verdict("T1", verdict_id="retry-me").status, "applied")
        self.assertEqual(h.state("T1"), "completed")
        self.assertEqual(h.verdict("T1", verdict_id="retry-me").status, "duplicate")     # applied ones ARE remembered

    def test_an_event_refused_for_a_wrong_token_is_applied_when_corrected_under_the_same_id(self):
        h = Harness([indep("T1")])
        h.core.step()
        self.assertEqual(h.send("T1", "execution_started", event_id="e", token=999).status, "stale")
        self.assertEqual(h.send("T1", "execution_started", event_id="e").status, "applied")

    def test_the_same_refusal_repeated_is_audited_once(self):
        h = Harness([indep("T1")])
        h.core.step()
        for _ in range(20):
            h.send("T1", "execution_started", event_id="noisy", token=999)
        self.assertEqual(sum(1 for k in h.audit_kinds() if k == "message_rejected"), 1)

    def test_the_applied_id_window_is_bounded(self):
        state = RunState("P", 1, "0" * 64, 0.0)
        for i in range(SEEN_LIMIT + 500):
            state.remember(f"e{i}")
        self.assertEqual(len(state.seen_events), SEEN_LIMIT)
        self.assertTrue(state.has_seen(f"e{SEEN_LIMIT + 499}"))
        self.assertFalse(state.has_seen("e0"))


class UntrustedPortTypes(unittest.TestCase):
    def prep(self):
        h = Harness([indep("T1")])
        h.core.step()
        h.send("T1", "execution_finished")
        return h

    def verdict(self, h, **over):
        base = {"verdict_id": "v", "plan_id": "REQ-T", "revision": 1, "task_id": "T1", "attempt_id": h.attempt("T1"),
                "accepted": True, "verifier": "validator", "evidence": "ok", "token": h.token(h.attempt("T1"))}
        return h.core.submit_verdict(sc.Verdict(**{**base, **over}))

    def test_truthy_but_not_boolean_acceptance_cannot_complete_a_task(self):
        for bad in ("false", "no", 1, [], None):
            with self.subTest(accepted=bad):
                h = self.prep()
                self.assertEqual(self.verdict(h, accepted=bad).status, "invalid")
                self.assertEqual(h.state("T1"), "active")

    def test_other_malformed_verdicts_are_refused_not_raised(self):
        h = self.prep()
        for over in ({"token": "1"}, {"token": True}, {"revision": "1"}, {"verifier": 5}, {"evidence": None},
                     {"verdict_id": ""}, {"attempt_id": None}):
            with self.subTest(over=over):
                self.assertEqual(self.verdict(h, **over).status, "invalid")
        self.assertEqual(h.core.submit_verdict("not a verdict").status, "invalid")        # type: ignore[arg-type]
        self.assertEqual(h.state("T1"), "active")

    def test_a_directly_constructed_event_is_validated_like_a_dict(self):
        h = self.prep()
        for bad in (sc.Event("e", "REQ-T", 1, "T1", h.attempt("T1"), "x", "bogus_kind"),
                    sc.Event("", "REQ-T", 1, "T1", h.attempt("T1"), "x", "heartbeat"),
                    sc.Event("e", "REQ-T", 1, "T1", h.attempt("T1"), "x", "heartbeat", payload=[1]),     # type: ignore[arg-type]
                    sc.Event("e", "REQ-T", "1", "T1", h.attempt("T1"), "x", "heartbeat")):                # type: ignore[arg-type]
            self.assertEqual(h.core.ingest(bad).status, "invalid")

    def test_claim_with_something_that_is_not_an_assignment_is_a_refusal(self):
        h = Harness([indep("T1")])
        for junk in (None, "T1", 5, object(), {"task_id": "T1"}):
            self.assertEqual(h.core.claim(junk).reason, "unknown_task")                        # type: ignore[arg-type]


class WaitCap(unittest.TestCase):
    def test_a_recovery_module_that_always_says_wait_cannot_postpone_forever(self):
        rec = sc.ScriptedRecovery({"T1": sc.RecoveryProposal("wait", "later", 10)})
        h = Harness([indep("T1")], recovery=rec, max_attempts=5, config=sc.Config(max_recovery_waits=2, max_attempts=5))
        h.core.step()
        h.send("T1", "execution_failed")
        for _ in range(6):
            h.core.step()
            h.clock.advance(11)
        self.assertEqual((h.state("T1"), h.core.read(lambda c: c.state.tasks["T1"].reason)), ("blocked", "recovery_wait_limit"))
        self.assertEqual(len(rec.calls), 3)


class SqliteHonesty(unittest.TestCase):
    def setUp(self):
        self.tmp, self.path = sqlite_path()
        self.addCleanup(self.tmp.cleanup)

    def test_read_only_open_never_modifies_an_unrelated_database(self):
        conn = sqlite3.connect(self.path)
        conn.execute("CREATE TABLE precious (x)")
        conn.execute("INSERT INTO precious VALUES (1)")
        conn.commit()
        conn.close()
        before = self.path.read_bytes()
        with self.assertRaises(sc.SchedulerError) as cm:
            sc.SqliteRepository(self.path, create=False)
        self.assertEqual(cm.exception.code, "STATE_MISSING")
        self.assertEqual(self.path.read_bytes(), before)

    def test_read_only_open_of_a_missing_or_non_sqlite_file_is_a_clean_error_and_creates_nothing(self):
        with self.assertRaises(sc.SchedulerError) as cm:
            sc.SqliteRepository(self.path, create=False)
        self.assertEqual(cm.exception.code, "STATE_MISSING")
        self.assertFalse(self.path.exists())
        self.path.write_text("this is not a database at all" * 50)
        with self.assertRaises(sc.SchedulerError) as cm:
            sc.SqliteRepository(self.path, create=False)
        self.assertEqual(cm.exception.code, "STATE_UNAVAILABLE")

    def test_looking_never_waits_for_a_writer(self):
        h = Harness([indep("T1")], repository=sc.SqliteRepository(self.path))
        blocker = sqlite3.connect(self.path, isolation_level=None)
        blocker.execute("BEGIN IMMEDIATE")                                   # a long write is in progress
        try:
            started = time.monotonic()
            snap = h.core.snapshot()
            h.core.inspect()
            h.core.pending_orders()
            self.assertLess(time.monotonic() - started, 2.0)
            self.assertEqual(snap.status, "running")
        finally:
            blocker.execute("ROLLBACK")
            blocker.close()

    def test_a_read_only_transaction_keeps_nothing_and_cannot_audit(self):
        for repo in (sc.InMemoryRepository(), sc.SqliteRepository(self.path)):
            h = Harness([indep("T1")], repository=repo)
            before = h.core.audit_log()
            with self.assertRaises(RuntimeError):
                h.core.read(lambda c: c.audit("sneaky"))
            h.core.read(lambda c: setattr(c.state, "paused", True))
            self.assertFalse(h.core.snapshot().paused)
            self.assertEqual(h.core.audit_log(), before)

    def test_a_malformed_but_json_valid_document_is_a_typed_error(self):
        h = Harness([indep("T1")], repository=sc.SqliteRepository(self.path))
        conn = sqlite3.connect(self.path)
        conn.execute("UPDATE state SET doc = ?", ('{"schema": 1, "plan_id": "x", "tasks": 5}',))
        conn.commit()
        conn.close()
        with self.assertRaises(sc.SchedulerError) as cm:
            h.core.snapshot()
        self.assertEqual(cm.exception.code, "STATE_UNREADABLE")


class Scale(unittest.TestCase):
    def test_a_blocked_head_of_a_long_chain_is_reported_quickly(self):
        tasks = [indep("T0")] + [indep(f"T{i}", [f"T{i - 1}"]) for i in range(1, 2000)]
        plan, _ = approved(plan_text(tasks))
        state = RunState("REQ-T", 1, plan.sha256, 0.0)
        from bt_scheduler_core.model import TaskRec
        state.tasks = {t.id: TaskRec("pending") for t in plan.tasks}
        state.tasks["T0"].state = "blocked"
        from bt_scheduler_core.views import unreachable
        started = time.monotonic()
        self.assertEqual(len(unreachable(plan, state)), 1999)
        self.assertLess(time.monotonic() - started, 2.0)

    def test_many_blocked_roots_do_not_multiply_the_work(self):
        tasks = [indep(f"R{i}") for i in range(300)] + [indep(f"C{i}", [f"R{i}"]) for i in range(300)]
        plan, _ = approved(plan_text(tasks))
        from bt_scheduler_core.model import TaskRec
        from bt_scheduler_core.views import unreachable
        state = RunState("REQ-T", 1, plan.sha256, 0.0)
        state.tasks = {t.id: TaskRec("blocked" if t.id.startswith("R") else "pending") for t in plan.tasks}
        started = time.monotonic()
        self.assertEqual(len(unreachable(plan, state)), 300)
        self.assertLess(time.monotonic() - started, 1.0)


class ConfigLimits(unittest.TestCase):
    def test_new_limits_are_validated_and_documented_defaults_hold(self):
        config = sc.Config()
        self.assertEqual((config.max_recovery_waits, config.max_deliveries), (3, 5))
        for bad in ({"max_recovery_waits": 0}, {"max_deliveries": 0}, {"max_deliveries": True}, {"max_recovery_waits": 1.5}):
            with self.assertRaises(sc.SchedulerError):
                sc.Config(**bad)

    def test_the_delivery_limit_is_the_configured_one(self):
        h = Harness([indep("T1")], config=sc.Config(max_deliveries=2))
        h.executor.fail_next_starts = 100
        for _ in range(5):
            h.core.step()
        self.assertEqual(h.executor.deliveries, {})
        self.assertIn("delivery_abandoned", h.audit_kinds())
        row = next(e for e in h.core.audit_log() if e.kind == "delivery_abandoned")
        self.assertEqual(row.detail["deliveries"], 2)


class Threads(unittest.TestCase):
    def test_hash_of_the_state_document_is_stable_across_reads(self):
        h = Harness([indep("T1")])
        h.core.step()
        docs = [hashlib.sha256(repr(sorted(h.core.read(lambda c: c.state.to_dict()).items())).encode()).hexdigest()
                for _ in range(3)]
        self.assertEqual(len(set(docs)), 1)

    def test_readers_and_writers_interleave_without_errors(self):
        tmp, path = sqlite_path()
        self.addCleanup(tmp.cleanup)
        h = Harness([indep(f"T{i}") for i in range(8)], repository=sc.SqliteRepository(path), parallel=8)
        errors, stop = [], threading.Event()

        def reader():
            core = h.build()
            while not stop.is_set():
                try:
                    core.snapshot()
                except Exception as exc:  # noqa: BLE001 - collected and asserted empty below
                    errors.append(repr(exc))

        threads = [threading.Thread(target=reader) for _ in range(3)]
        [t.start() for t in threads]
        try:
            for i in range(8):
                h.core.claim(sc.Assignment(f"T{i}", "w"))
        finally:
            stop.set()
            [t.join(30) for t in threads]
        self.assertEqual(errors, [])
        self.assertEqual(h.core.snapshot().counts["live_attempts"], 8)


class VerifyingIsSettledByVerdict(unittest.TestCase):
    def verifying(self, **kw):
        h = Harness([indep("T1")], **kw)
        h.core.step()
        h.send("T1", "execution_finished")
        h.core.step()
        return h

    def test_an_unknown_observation_does_not_pull_a_verifying_attempt_back_to_uncertain(self):
        h = self.verifying()
        h.executor.status[h.attempt("T1")] = sc.ExecutionStatus("unknown", "flaky")
        h.clock.advance(h.config.lease_seconds + 1)
        h.core.step()
        h.core.step()
        self.assertEqual(h.core.snapshot().tasks["T1"]["attempt_state"], "verifying")
        self.assertEqual(h.verdict("T1").status, "applied")
        self.assertEqual(h.state("T1"), "completed")

    def test_an_abandoned_verify_order_can_be_asked_again_or_failed_by_an_operator_only(self):
        h = Harness([indep("T1")], config=sc.Config(max_parallel_tasks=3, max_attempts=1, max_deliveries=2))
        h.core.step()
        att = h.attempt("T1")

        def boom(order):
            raise ConnectionError("verifier down")
        h.verifier.request = boom
        h.send("T1", "execution_finished")
        for _ in range(4):
            h.core.step()
        self.assertIn("delivery_abandoned", h.audit_kinds())
        self.assertEqual(h.core.pending_orders(), [])
        h.verifier = sc.FakeVerifier()
        h.core.ports.verification = h.verifier
        self.assertEqual(h.core.resolve_attempt(att, "finished", "owner", "ask again"), "finished")
        h.core.step()
        self.assertIn(att, h.verifier.requests)                       # a fresh order exists after the operator asked
        self.assertEqual(h.core.resolve_attempt(att, "failed", "owner", "give up"), "failed")
        self.assertEqual(h.core.snapshot().tasks["T1"]["attempt_state"], "failed")


class NoPortKeepsOrders(unittest.TestCase):
    def test_pull_mode_keeps_start_and_verify_orders_untouched(self):
        h = Harness([indep("T1")])
        h.core.ports.execution = h.core.ports.verification = None
        for _ in range(10):
            h.core.step()
        orders = h.core.pending_orders()
        self.assertEqual([o["kind"] for o in orders], ["start"])
        self.assertEqual(h.core.read(lambda c: c.state.outbox[0].deliveries), 0)
        self.assertNotIn("delivery_abandoned", h.audit_kinds())
        h.core.ports.execution = h.executor                              # the port appears later: nothing was lost
        h.core.step()
        self.assertIn(h.attempt("T1"), h.executor.started)


class RecoveryWaitIsNotBusy(unittest.TestCase):
    def test_wait_zero_holds_and_is_not_progress(self):
        rec = sc.ScriptedRecovery({"T1": sc.RecoveryProposal("wait", "now", 0)})
        h = Harness([indep("T1")], recovery=rec, max_attempts=3, config=sc.Config(max_attempts=3))
        h.core.step()
        h.send("T1", "execution_failed")
        first = h.core.step()
        self.assertFalse(first.progress)
        self.assertEqual(len(rec.calls), 1)
        for _ in range(5):                                               # same instant: held, never re-asked
            self.assertFalse(h.core.step().progress)
        self.assertEqual(len(rec.calls), 1)
        self.assertGreaterEqual(h.core.next_deadline(), 0.0)
        h.clock.advance(1.5)
        h.core.step()
        self.assertEqual(len(rec.calls), 2)

    def test_run_returns_instead_of_spinning_when_a_recovery_module_keeps_waiting(self):
        rec = sc.ScriptedRecovery({"T1": sc.RecoveryProposal("wait", "later", 0)})
        h = Harness([indep("T1")], recovery=rec, max_attempts=3, config=sc.Config(max_attempts=3))
        h.core.step()
        h.send("T1", "execution_failed")
        snap = h.core.run(max_steps=50, idle_timeout=0.05)
        self.assertEqual(snap.tasks["T1"]["state"], "recovering")
        self.assertEqual(len(rec.calls), 1)


class CancelNeverResends(unittest.TestCase):
    def test_cancel_after_a_failed_start_voids_the_start_and_never_resends_it(self):
        h = Harness([indep("T1")], config=sc.Config(max_parallel_tasks=3, max_attempts=2, max_deliveries=5))
        h.executor.fail_next_starts = 1
        h.core.step()                                                    # delivery failed: pending, deliveries == 1
        self.assertEqual(h.core.read(lambda c: c.state.outbox[0].deliveries), 1)
        h.core.cancel("owner", "stop")
        kinds = {(i["kind"]) for i in h.core.pending_orders()}
        self.assertEqual(kinds, {"cancel"})
        for _ in range(4):
            h.core.step()
        self.assertEqual(h.executor.deliveries, {})                      # the start order never reached the executor
        self.assertEqual(h.state("T1"), "cancelled")

    def test_a_cancel_ack_asks_the_executor_what_became_of_the_attempt(self):
        h = Harness([indep("T1")])
        h.core.step()
        h.send("T1", "execution_started")
        h.core.cancel("owner", "stop")
        h.core.step()                                                    # cancel delivered; executor still says running
        self.assertIn(h.attempt("T1"), h.executor.cancelled)
        self.assertTrue(h.core.read(lambda c: c.state.attempts[h.attempt("T1")].needs_reconcile))
        h.executor.status[h.attempt("T1")] = sc.ExecutionStatus("cancelled", "stopped")
        h.core.step()
        self.assertEqual(h.state("T1"), "cancelled")


class OutboxIsBounded(unittest.TestCase):
    def test_settled_orders_of_closed_attempts_are_pruned_and_live_ones_kept(self):
        from bt_scheduler_core.model import OUTBOX_LIMIT
        from bt_scheduler_core.transitions import prune_outbox
        h = Harness([indep("T1")])
        h.core.step()
        live = h.attempt("T1")

        def fill(ctx):
            for i in range(OUTBOX_LIMIT + 50):
                ctx.state.outbox.insert(0, sc.model.OutboxItem(id=f"old-{i}", kind="verify", attempt_id=live,
                                                               key=f"k{i}", payload={}, status="delivered"))
            return prune_outbox(ctx)
        # items of a live attempt are never dropped, whatever their age
        self.assertEqual(h.core.write(fill), 0)

    def test_old_settled_items_of_a_closed_attempt_go_but_pending_and_recent_stay(self):
        from bt_scheduler_core.model import OUTBOX_KEEP, OUTBOX_LIMIT
        h = Harness([indep("T1"), indep("T2")])
        h.core.step()
        h.finish_and_accept("T1")
        closed = next(a for a, r in h.core.read(lambda c: c.state.attempts).items() if r.task_id == "T1")

        def fill(ctx):
            ctx.state.outbox[:] = [sc.model.OutboxItem(id=f"old-{i}", kind="verify", attempt_id=closed, key=f"k{i}",
                                                       payload={}, status="pending" if i == 3 else "delivered")
                                   for i in range(OUTBOX_LIMIT + 50)] + ctx.state.outbox
            from bt_scheduler_core.transitions import prune_outbox
            return prune_outbox(ctx)
        self.assertGreater(h.core.write(fill), 0)
        ids = h.core.read(lambda c: [i.id for i in c.state.outbox])
        self.assertIn("old-3", ids)                       # pending survives
        self.assertNotIn("old-4", ids)                    # settled and old: gone
        self.assertLessEqual(len(ids), OUTBOX_KEEP + 60)


if __name__ == "__main__":
    unittest.main()
