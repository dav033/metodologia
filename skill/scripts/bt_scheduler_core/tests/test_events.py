"""Events and verdicts: idempotent, correlated, guarded (SC-AC09..SC-AC12, SC-AC10)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2])]

from support import Harness, indep

import bt_scheduler_core as sc


def fresh():
    h = Harness([indep("T1"), indep("T2", ["T1"])], max_attempts=2)
    h.core.step()
    return h


def snapshot_of(h):
    return h.core.read(lambda c: c.state.to_dict())


class ContractVersion(unittest.TestCase):
    def test_new_events_advertise_contract_v12(self):
        event = sc.Event("e1", "REQ-T", 1, "T1", "a1", "monitor", "execution_started")
        self.assertEqual(sc.CONTRACT_VERSION, "1.2.0")
        self.assertEqual(sc.SchedulerCore.contract_version, "1.2.0")
        self.assertEqual(event.to_dict()["contract_version"], "1.2.0")

    def test_v10_events_remain_readable(self):
        event = sc.Event("e1", "REQ-T", 1, "T1", "a1", "monitor", "execution_started",
                         contract_version="1.0.0")
        parsed = sc.Event.from_dict(event.to_dict())
        self.assertEqual(parsed.contract_version, "1.0.0")
        self.assertEqual(parsed.to_dict(), event.to_dict())


class Lifecycle(unittest.TestCase):
    def test_started_then_finished_moves_the_attempt_but_never_completes_the_task(self):
        h = fresh()
        self.assertEqual(h.send("T1", "execution_started").status, "applied")
        self.assertEqual(h.core.snapshot().tasks["T1"]["attempt_state"], "running")
        self.assertEqual(h.send("T1", "execution_finished").status, "applied")
        snap = h.core.snapshot().tasks["T1"]
        self.assertEqual((snap["state"], snap["attempt_state"]), ("active", "verifying"))   # SC-AC10
        self.assertEqual(h.state("T2"), "pending")

    def test_only_an_independent_accepted_verdict_completes(self):
        h = fresh()
        h.send("T1", "execution_finished")
        self.assertEqual(h.verdict("T1").status, "applied")
        self.assertEqual(h.state("T1"), "completed")
        self.assertEqual(h.core.snapshot().tasks["T1"]["verifier"], "validator")

    def test_the_executors_own_label_cannot_accept_its_work(self):
        h = fresh()
        h.send("T1", "execution_finished")
        result = h.verdict("T1", verifier="local")        # the default executor label
        self.assertEqual((result.status, result.reason), ("invalid", "verifier_not_independent"))
        self.assertEqual(h.state("T1"), "active")

    def test_independence_check_can_be_disabled_explicitly(self):
        h = Harness([indep("T1")], config=sc.Config(require_independent_verifier=False))
        h.core.step()
        h.send("T1", "execution_finished")
        self.assertEqual(h.verdict("T1", verifier="local").status, "applied")

    def test_acceptance_needs_evidence_and_a_named_verifier(self):
        h = fresh()
        h.send("T1", "execution_finished")
        self.assertEqual(h.verdict("T1", evidence="  ").reason, "evidence_missing")
        self.assertEqual(h.verdict("T1", verifier="").reason, "verifier_missing")
        self.assertEqual(h.state("T1"), "active")

    def test_a_verdict_before_the_executor_finished_is_stale(self):
        h = fresh()
        self.assertEqual((h.verdict("T1").status, h.verdict("T1").reason), ("stale", "attempt_not_verifying"))

    def test_a_rejecting_verdict_sends_the_task_to_recovery_and_keeps_the_evidence(self):
        h = fresh()
        h.send("T1", "execution_finished")
        h.verdict("T1", accepted=False, evidence="tests red")
        snap = h.core.snapshot().tasks["T1"]
        self.assertEqual((snap["state"], snap["attempt_state"], snap["evidence"]), ("recovering", "rejected", "tests red"))

    def test_events_reordered_in_flight_are_tolerated(self):
        h = fresh()
        self.assertEqual(h.send("T1", "execution_finished").status, "applied")   # the 'started' event is lost or late
        self.assertEqual(h.send("T1", "execution_started").status, "stale")
        steps = [(e.detail["from"], e.detail["to"]) for e in h.core.audit_log() if e.kind == "attempt_transition"]
        self.assertEqual(steps, [("reserved", "dispatched"), ("dispatched", "running"), ("running", "verifying")])

    def test_failure_and_cancellation_events_close_the_attempt_and_free_resources(self):
        h = fresh()
        h.send("T1", "execution_failed", reason="segfault")
        self.assertEqual(h.core.read(lambda c: c.state.holds), {})
        self.assertEqual(h.core.snapshot().tasks["T1"]["attempt_state"], "failed")
        h2 = fresh()
        h2.send("T1", "execution_cancelled")
        self.assertEqual(h2.core.snapshot().tasks["T1"]["attempt_state"], "cancelled")
        self.assertEqual(h2.state("T1"), "recovering")


class Idempotency(unittest.TestCase):
    def test_the_same_event_twice_equals_once(self):                       # SC-AC11
        h = fresh()
        event = h.ev("T1", "execution_started", event_id="dup-1")
        self.assertEqual(h.core.ingest(event).status, "applied")
        once = snapshot_of(h)
        audit_once = len(h.core.audit_log())
        for _ in range(3):
            self.assertEqual(h.core.ingest(event).status, "duplicate")
        self.assertEqual(snapshot_of(h), once)
        self.assertEqual(len(h.core.audit_log()), audit_once)

    def test_the_same_verdict_twice_equals_once(self):
        h = fresh()
        h.send("T1", "execution_finished")
        self.assertEqual(h.verdict("T1", verdict_id="v-1").status, "applied")
        once = snapshot_of(h)
        self.assertEqual(h.verdict("T1", verdict_id="v-1").status, "duplicate")
        self.assertEqual(snapshot_of(h), once)

    def test_a_second_distinct_verdict_after_acceptance_is_stale(self):
        h = fresh()
        h.send("T1", "execution_finished")
        h.verdict("T1", verdict_id="v-1")
        self.assertEqual(h.verdict("T1", accepted=False, verdict_id="v-2").status, "stale")
        self.assertEqual(h.state("T1"), "completed")

    def test_event_ids_are_remembered_across_a_restart(self):
        h = fresh()
        event = h.ev("T1", "execution_started", event_id="dup-2")
        h.core.ingest(event)
        h.crash()
        self.assertEqual(h.core.ingest(event).status, "duplicate")

    def test_heartbeats_are_liveness_hints_not_state_or_memory(self):
        h = fresh()
        att = h.attempt("T1")
        before = snapshot_of(h)
        h.clock.advance(100)
        self.assertEqual(h.send("T1", "heartbeat").status, "noop")
        after = snapshot_of(h)
        self.assertEqual(after["tasks"], before["tasks"])
        self.assertEqual(after["seen_events"], before["seen_events"])           # not stored: they would flood the log
        self.assertGreater(after["attempts"][att]["lease_expires_at"], before["attempts"][att]["lease_expires_at"])


class Stale(unittest.TestCase):
    def retried(self):
        h = Harness([indep("T1")], max_attempts=3)
        h.core.step()
        first = h.attempt("T1")
        h.send("T1", "execution_failed")
        h.core.step()                       # recovery default policy: retry
        h.core.step()                       # second attempt reserved
        self.assertNotEqual(h.attempt("T1"), first)
        return h, first

    def test_a_late_event_of_an_old_attempt_cannot_touch_the_current_one(self):   # SC-AC12
        h, first = self.retried()
        before = snapshot_of(h)
        for kind in ("execution_finished", "execution_failed", "execution_started", "execution_cancelled"):
            res = h.send("T1", kind, first, token=None)
            self.assertEqual(res.status, "stale", kind)
        self.assertEqual(snapshot_of(h)["tasks"], before["tasks"])
        self.assertEqual(snapshot_of(h)["holds"], before["holds"])
        self.assertEqual(h.core.snapshot().tasks["T1"]["attempt_state"], "dispatched")

    def test_a_late_verdict_of_an_old_attempt_is_stale(self):
        h, first = self.retried()
        self.assertEqual(h.verdict("T1", True, first, verdict_id="old").status, "stale")
        self.assertEqual(h.state("T1"), "active")

    def test_a_wrong_fencing_token_is_stale(self):
        h = fresh()
        self.assertEqual(h.send("T1", "execution_finished", token=12345).reason, "token_mismatch")
        self.assertEqual(h.core.snapshot().tasks["T1"]["attempt_state"], "dispatched")

    def test_events_for_a_closed_attempt_change_nothing(self):
        h = fresh()
        h.send("T1", "execution_finished")
        h.verdict("T1")
        self.assertEqual(h.send("T1", "execution_failed").reason, "attempt_closed")
        self.assertEqual(h.state("T1"), "completed")


class Invalid(unittest.TestCase):
    def test_messages_for_another_plan_or_revision_or_attempt_are_invalid(self):
        h = fresh()
        att = h.attempt("T1")
        wrong_plan = sc.Event("e1", "REQ-OTHER", 1, "T1", att, "x", "execution_started")
        wrong_rev = sc.Event("e2", "REQ-T", 7, "T1", att, "x", "execution_started")
        ghost = sc.Event("e3", "REQ-T", 1, "T1", "att-9999", "x", "execution_started")
        mismatch = sc.Event("e4", "REQ-T", 1, "T2", att, "x", "execution_started")
        self.assertEqual([h.core.ingest(e).reason for e in (wrong_plan, wrong_rev, ghost, mismatch)],
                         ["wrong_plan", "wrong_plan", "unknown_attempt", "unknown_attempt"])
        self.assertEqual(h.core.snapshot().tasks["T1"]["attempt_state"], "dispatched")

    def test_malformed_events_are_rejected_without_raising(self):
        h = fresh()
        for bad in ({}, {"event_id": "x"}, "text", None, 5, {"event_id": "a", "plan_id": "p", "revision": "1", "task_id": "T1",
                                                           "attempt_id": "a", "source": "s", "kind": "execution_started"},
                    {"event_id": "a", "plan_id": "REQ-T", "revision": 1, "task_id": "T1", "attempt_id": "a", "source": "s",
                     "kind": "execution_completed"}):
            with self.subTest(bad=bad):
                self.assertEqual(h.core.ingest(bad).status, "invalid")  # type: ignore[arg-type]

    def test_a_dict_event_is_accepted_like_an_Event(self):
        h = fresh()
        data = h.ev("T1", "execution_started", event_id="d1").to_dict()
        self.assertEqual(h.core.ingest(data).status, "applied")

    def test_rejected_messages_are_audited_with_their_reason(self):
        h = fresh()
        h.send("T1", "execution_finished", token=999)
        rows = [e for e in h.core.audit_log() if e.kind == "message_rejected"]
        self.assertEqual(rows[-1].detail["reason"], "token_mismatch")
        self.assertEqual((rows[-1].plan_id, rows[-1].task_id), ("REQ-T", "T1"))

    def test_without_a_started_run_nothing_can_be_ingested(self):
        core = sc.SchedulerCore(Harness([indep("T1")]).plan, sc.InMemoryRepository())
        with self.assertRaises(sc.SchedulerError) as cm:
            core.ingest({"x": 1} | {"event_id": "a", "plan_id": "p", "revision": 1, "task_id": "T", "attempt_id": "a",
                                    "source": "s", "kind": "heartbeat"})
        self.assertEqual(cm.exception.code, "STATE_MISSING")


if __name__ == "__main__":
    unittest.main()
