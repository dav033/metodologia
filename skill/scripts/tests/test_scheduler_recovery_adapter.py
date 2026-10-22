from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import bt_scheduler_adapter as sched
import bt_scheduler_recovery_adapter as adapter

core = sched.core


class RecoveryPortContract(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.now = 1000.0
        text = json.dumps({"schema_version": "1.0.0", "plan_id": "P", "revision": 1, "tasks": [
            {"id": "T1", "milestone_id": "M1", "repository": "app", "after": [], "expected_paths": ["x"]}]})
        plan = core.load_plan(text, approved_sha256=hashlib.sha256(text.encode()).hexdigest())
        self.scheduler = core.SchedulerCore(
            plan, core.InMemoryRepository(), config=core.Config(max_attempts=3), clock=lambda: self.now,
            ports=core.Ports(execution=core.FakeExecutor()))
        self.scheduler.start()
        self.scheduler.step()
        self.attempt_id = self.scheduler.snapshot().tasks["T1"]["attempt"]
        self.token = self.scheduler.read(lambda c: c.state.attempts[self.attempt_id].token)
        self.facts = {
            "schema_version": "m5.executor-facts/1", "request": {
                "plan_id": "P", "plan_sha256": self.scheduler.snapshot().plan_sha256, "revision": 1,
                "task_id": "T1", "attempt_id": self.attempt_id, "token": self.token},
            "state": "failed", "outcome": {"cause": "connection_lost", "reset_epoch": None},
            "handoff": {"status": "captured", "snapshot_sha": "a" * 40}, "snapshot_verified": True,
            "cancel_requested": False, "updated": self.now}
        self.port = adapter.RecoveryAdapter(
            Path(self.temp.name) / "history.db", scheduler=self.scheduler, run_id="run-1",
            describe=lambda _attempt: self.facts)
        self.addCleanup(self.port.close)
        self.scheduler.ports.recovery = self.port
        self.scheduler.ingest(core.Event("failed", "P", 1, "T1", self.attempt_id, "executor", "execution_failed",
                                         token=self.token, payload={"reason": "secret-not-to-persist"}))
        self.context = core.FailureContext("P", "T1", self.attempt_id, "execution_failed", 1, 3,
                                           "secret-not-to-persist")

    def test_unknown_executor_evidence_blocks_without_reading_raw_detail(self):
        self.facts = None
        self.scheduler.step()
        self.assertEqual(self.scheduler.snapshot().tasks["T1"]["state"], "blocked")
        self.assertNotIn("secret-not-to-persist", json.dumps(self.port.latest()))

    def test_a_start_the_scheduler_itself_rejected_is_named_for_what_it_is_not_filed_as_an_identity_anomaly(self):
        """39 of the 44 real `identity_unverified` blocks were `start rejected: INTEGRATION_CONFLICT / PREDECESSOR_*` (no executor record, by
        design): an integrity label that nobody answers for sent each one to a person."""
        self.facts = None
        for failure, reason in (("start rejected: INTEGRATION_CONFLICT: a.py, b.py", "m5:start_rejected_integration_conflict"),
                                ("start rejected: PREDECESSOR_HANDOFF_MISSING: retry is not authorised", "m5:start_rejected_predecessor_handoff_missing")):
            with self.subTest(failure=failure):
                self.port._official = lambda _c, failure=failure: {"current": True, "manual_cancel": False, "evidence": "", "failure": failure}
                proposal = self.port.propose(self.context)
                self.assertEqual((proposal.action, proposal.reason), ("block", reason))

    def test_a_refused_verification_order_blocks_with_its_code_even_though_the_executor_has_its_record(self):
        """The retry would send the same refused order again: it blocks with `verify_rejected_<code>`, and the attempt's snapshot stays."""
        self.port._official = lambda _c: {"current": True, "manual_cancel": False, "evidence": "",
                                          "failure": "verify rejected: ORDER_INVALID: verification entry has missing or unapproved fields"}
        proposal = self.port.propose(self.context)                                              # self.facts is a complete executor record
        self.assertEqual((proposal.action, proposal.reason), ("block", "m5:verify_rejected_order_invalid"))

    def test_uncovered_recovery_surface_blocks_under_the_same_verification_case(self):
        context = replace(self.context, cause="verification_rejected")
        self.port._official = lambda _context: {"current": True, "manual_cancel": False,
            "evidence": "verification_replan/blocked: web/page.ts lacks an independent check"}
        proposal = self.port.propose(context)
        self.assertEqual((proposal.action, proposal.reason), ("block", "verification_replan_blocked"))

    def test_cooldown_then_retry_has_one_decision_per_logical_round(self):
        first = self.port.propose(self.context)
        self.assertEqual(first.action, "wait")
        self.assertEqual(self.port.propose(self.context), first)
        self.scheduler.step()
        self.assertEqual(self.scheduler.snapshot().tasks["T1"]["state"], "recovering")
        self.now += 2
        self.scheduler.step()
        self.assertEqual(self.scheduler.snapshot().tasks["T1"]["attempts"], 2)
        self.assertEqual(self.port.metrics()["decisions"], 2)

    def test_wrong_plan_token_revision_and_late_context_cannot_retry(self):
        for key, value in (("token", self.token + 1), ("plan_id", "foreign"), ("plan_sha256", "0" * 64),
                           ("revision", 2)):
            with self.subTest(key=key):
                original = self.facts["request"][key]
                self.facts["request"][key] = value
                self.assertEqual(self.port.propose(self.context).action, "block")
                self.facts["request"][key] = original
        self.assertEqual(self.port.propose(replace(self.context, plan_id="foreign")).action, "block")
        self.scheduler.cancel("owner")
        self.assertEqual(self.port.propose(self.context).action, "block")

    def test_live_settling_cancelled_and_missing_snapshot_never_retry(self):
        for state in ("running", "settling", "cancelled", "not_found"):
            with self.subTest(state=state):
                self.facts["state"] = state
                self.assertEqual(self.port.propose(self.context).action, "block")
        self.facts["state"] = "failed"
        self.facts["snapshot_verified"] = False
        self.assertEqual(self.port.propose(self.context).action, "block")

    def test_full_history_blocks_visibly_instead_of_using_retry_fallback(self):
        self.port.close()
        self.port = adapter.RecoveryAdapter(
            Path(self.temp.name) / "full.db", scheduler=self.scheduler, run_id="run-1",
            describe=lambda _attempt: self.facts, policy={"max_decisions": 1})
        self.addCleanup(self.port.close)
        self.scheduler.ports.recovery = self.port
        self.scheduler.step()
        self.now += 2
        self.scheduler.step()
        self.assertEqual(self.scheduler.snapshot().tasks["T1"]["state"], "blocked")
        self.assertIn("recovery_unavailable", [entry.kind for entry in self.scheduler.audit_log()])

    def test_restart_cannot_replay_a_decision_after_evidence_expires(self):
        self.assertEqual(self.port.propose(self.context).action, "wait")
        self.port.close()
        self.now += 90000
        result = self.port.propose(self.context)
        self.assertEqual(result.action, "block")
        self.assertIn("recovery_unavailable", [entry.kind for entry in self.scheduler.audit_log()])

    def test_evidence_read_and_audit_failures_cannot_escape_into_default_retry(self):
        class UnavailableSource:
            def read(self, fn):
                raise OSError("read unavailable with secret-value")

            def record(self, *args, **kwargs):
                raise OSError("audit unavailable with secret-value")

        self.port.scheduler = UnavailableSource()
        with self.assertLogs("bt_scheduler_recovery_adapter", level="ERROR") as captured:
            self.scheduler.step()
        self.assertEqual(self.scheduler.snapshot().tasks["T1"]["state"], "blocked")
        self.assertEqual(self.scheduler.snapshot().tasks["T1"]["attempts"], 1)
        self.assertNotIn("secret-value", "\n".join(captured.output))


if __name__ == "__main__":
    unittest.main()
