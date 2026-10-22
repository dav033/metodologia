"""Outbox dispatch and idempotent delivery (SC-AC13): the intent is persisted first, a crash never starts two writers."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2])]

from support import Harness, indep

import bt_scheduler_core as sc

Crash = sc.FakeExecutor.Crash


def start_keys(h):
    return {k: n for k, n in h.executor.deliveries.items() if k.startswith("REQ-T:")}


class WriteAhead(unittest.TestCase):
    def test_the_intent_and_the_reservation_are_persisted_before_the_port_is_called(self):
        seen = {}
        h = Harness([indep("T1")])

        def hook():
            with h.repo.transaction() as tx:
                item = tx.state.outbox[0]
                seen.update(status=item.status, deliveries=item.deliveries, attempt=tx.state.attempts[item.attempt_id].state,
                            holds=len(tx.state.holds), task=tx.state.tasks["T1"].state)

        h.executor.latency_hook = hook
        h.core.step()
        self.assertEqual(seen, {"status": "pending", "deliveries": 1, "attempt": "reserved", "holds": 1, "task": "active"})

    def test_a_delivered_start_is_not_sent_again(self):
        h = Harness([indep("T1")])
        for _ in range(4):
            h.core.step()
        self.assertEqual(list(start_keys(h).values()), [1])
        self.assertEqual(h.core.snapshot().pending_outbox, 0)

    def test_orders_carry_identity_token_and_the_plan_acceptance_data_untouched(self):
        h = Harness([indep("T1")])
        h.core.step()
        order = next(iter(h.executor.started.values()))
        self.assertEqual((order.plan_id, order.revision, order.task_id, order.executor), ("REQ-T", 1, "T1", "local"))
        self.assertEqual(order.token, h.token(order.attempt_id))
        self.assertEqual(order.acceptance_criteria, ("T1 works",))
        self.assertEqual(order.verification[0]["value"], "true")


class CrashPoints(unittest.TestCase):
    def test_crash_after_the_executor_took_the_order_never_starts_a_second_writer(self):
        h = Harness([indep("T1")])
        h.executor.crash_after_start = True
        with self.assertRaises(Crash):
            h.core.step()
        h.crash()
        for _ in range(3):
            h.core.step()
        self.assertEqual(list(start_keys(h).values()), [1])
        self.assertEqual(h.core.snapshot().tasks["T1"]["attempt_state"], "running")   # learned by asking, not assuming
        self.assertEqual(len(h.executor.started), 1)

    def test_crash_before_the_executor_recorded_the_order_delivers_it_exactly_once(self):
        h = Harness([indep("T1")])

        def boom():
            h.executor.latency_hook = None
            raise Crash()

        h.executor.latency_hook = boom
        with self.assertRaises(Crash):
            h.core.step()
        self.assertEqual(h.executor.deliveries, {})
        h.crash()
        for _ in range(3):
            h.core.step()
        self.assertEqual(list(start_keys(h).values()), [1])
        self.assertEqual(h.core.snapshot().tasks["T1"]["attempt_state"], "dispatched")

    def test_crash_between_reservation_and_delivery(self):
        h = Harness([indep("T1")])
        self.assertTrue(h.core.claim(sc.Assignment("T1", "local")).ok)    # reserved + intent persisted, nothing sent
        self.assertEqual(h.executor.deliveries, {})
        h.crash()
        h.core.step()
        self.assertEqual(list(start_keys(h).values()), [1])
        self.assertEqual(h.core.read(lambda c: len(c.state.attempts)), 1)  # the same attempt, not a second logical one

    def test_crash_after_delivery_but_before_the_ack_was_recorded(self):
        h = Harness([indep("T1")])
        h.core.step()
        # emulate the lost ack: put the item back to pending as if the post-call transaction never committed
        def lose_ack(ctx):
            item = ctx.state.outbox[0]
            item.status = "pending"
            ctx.state.attempts[item.attempt_id].state = "reserved"
        h.core.write(lose_ack)
        h.crash()
        h.core.step()
        self.assertEqual(list(start_keys(h).values()), [1])                 # asked first: the executor already had it


class PortFailures(unittest.TestCase):
    def test_an_unavailable_executor_keeps_the_intent_and_does_not_raise(self):
        h = Harness([indep("T1")])
        h.executor.fail_next_starts = 1
        h.core.step()
        self.assertEqual(h.core.snapshot().tasks["T1"]["attempt_state"], "reserved")
        self.assertIn("port_error", h.audit_kinds())
        h.core.step()                                                       # recovers: query says never received, resend
        self.assertEqual(h.core.snapshot().tasks["T1"]["attempt_state"], "dispatched")
        self.assertEqual(list(start_keys(h).values()), [1])

    def test_an_executor_that_cannot_even_answer_a_query_makes_the_attempt_uncertain_not_failed(self):
        h = Harness([indep("T1")])
        h.executor.unavailable = True
        h.core.step()
        h.core.step()
        snap = h.core.snapshot()
        self.assertEqual(snap.tasks["T1"]["attempt_state"], "uncertain")
        self.assertEqual(snap.attention[0]["kind"], "uncertain_attempt")
        self.assertEqual(h.core.read(lambda c: len(c.state.holds)), 1)      # still reserved: no second writer
        self.assertEqual(h.core.claim(sc.Assignment("T1", "again")).reason, "not_ready")

    def test_an_uncertain_attempt_whose_order_never_arrived_is_redelivered_after_the_executor_returns(self):
        h = Harness([indep("T1")])
        h.executor.unavailable = True
        h.core.step()
        h.core.step()
        h.executor.unavailable = False
        h.clock.advance(1000)                                               # lease lapses -> reconcile asks
        for _ in range(3):
            h.core.step()
        self.assertEqual(h.core.snapshot().tasks["T1"]["attempt_state"], "dispatched")
        self.assertEqual(h.core.read(lambda c: len(c.state.attempts)), 1)
        self.assertEqual(list(start_keys(h).values()), [1])

    def test_a_rejected_start_fails_the_attempt(self):
        h = Harness([indep("T1")])
        h.executor.reject_start = True
        h.core.step()
        self.assertEqual(h.core.snapshot().tasks["T1"]["attempt_state"], "failed")
        h.core.step()
        self.assertEqual(h.state("T1"), "blocked")                         # one-attempt budget, no recovery module

    def test_a_permanent_verify_rejection_fails_the_attempt_instead_of_resending_it_forever(self):
        """REQ-020 att-0087: ORDER_INVALID answered 20 times over 99 minutes, the attempt `verifying` all along."""
        h = Harness([indep("T1")])
        h.verifier.reject = sc.Ack("rejected", "ORDER_INVALID", permanent=True)
        h.core.step()
        h.send("T1", "execution_finished")
        h.core.step()
        self.assertEqual(h.core.snapshot().tasks["T1"]["attempt_state"], "failed")
        self.assertIn("verify rejected: ORDER_INVALID", h.core.read(lambda c: [a.failure for a in c.state.attempts.values()][0]))
        self.assertEqual(h.verifier.deliveries and sum(h.verifier.deliveries.values()), 1)       # asked once

    def test_a_transient_verify_rejection_keeps_the_attempt_waiting_for_the_next_lease(self):
        h = Harness([indep("T1")])
        h.verifier.reject = sc.Ack("rejected", "QUALITY_BUSY")
        h.core.step()
        h.send("T1", "execution_finished")
        h.core.step()
        self.assertEqual(h.core.snapshot().tasks["T1"]["attempt_state"], "verifying")

    def test_a_delivery_that_keeps_failing_is_abandoned_visibly(self):
        h = Harness([indep("T1")])
        h.executor.fail_next_starts = 100
        for _ in range(sc.Config().max_deliveries + 3):
            h.core.step()
        self.assertIn("delivery_abandoned", h.audit_kinds())
        self.assertEqual(h.core.snapshot().tasks["T1"]["attempt_state"], "uncertain")

    def test_invalid_replies_from_the_executor_are_ignored_and_noted(self):
        class Garbage:
            def start(self, order): return "ok"
            def cancel(self, order): return None
            def query(self, attempt_id): return {"state": "running"}
        h = Harness([indep("T1")], executor=Garbage())
        h.core.step()
        self.assertIn("port_invalid", h.audit_kinds())
        self.assertEqual(h.core.snapshot().tasks["T1"]["attempt_state"], "reserved")


class PullStyleAndPause(unittest.TestCase):
    def test_without_an_execution_port_orders_wait_in_the_outbox_for_an_adapter_to_pull(self):
        h = Harness([indep("T1")])
        core = sc.SchedulerCore(h.plan, h.repo, clock=h.clock)             # no ports at all
        core.step()
        orders = core.pending_orders()
        self.assertEqual([o["kind"] for o in orders], ["start"])
        self.assertEqual(orders[0]["payload"]["executor"], "local")

    def test_pause_stops_new_work_but_not_what_is_already_reserved_resume_continues(self):
        h = Harness([indep("T1"), indep("T2")], parallel=1)
        h.core.step()
        h.core.pause("owner", "lunch")
        h.send("T1", "execution_finished")
        h.verdict("T1")
        h.core.step()
        self.assertEqual(h.state("T2"), "ready")                           # nothing new while paused
        self.assertEqual(h.core.snapshot().status, "paused")
        h.core.resume("owner")
        h.core.step()
        self.assertEqual(h.state("T2"), "active")

    def test_verification_is_requested_once_per_finished_attempt(self):
        h = Harness([indep("T1")])
        h.core.step()
        h.send("T1", "execution_finished")
        for _ in range(3):
            h.core.step()
        self.assertEqual(list(h.verifier.deliveries.values()), [1])
        order = next(iter(h.verifier.requests.values()))
        self.assertEqual((order.task_id, order.token), ("T1", h.token(order.attempt_id)))


if __name__ == "__main__":
    unittest.main()
