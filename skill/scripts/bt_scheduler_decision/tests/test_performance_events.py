from __future__ import annotations

import json
import unittest
from pathlib import Path

from bt_scheduler_decision import (
    PerformanceEvent,
    PerformanceEventError,
    normalize_performance_event,
    reduce_performance_events,
)

DECISION_ID = "a" * 64
ROUTE_ID = "b" * 64
OTHER_ROUTE_ID = "c" * 64
ATTEMPT_ID = "attempt-17"
VERDICT_ID = "verdict-42"
EXECUTOR_REF = f"route:m2:v1:{DECISION_ID}:{ROUTE_ID}"
_DEFAULT = object()


def attempt(**overrides):
    value = {
        "plan_id": "REQ-020",
        "revision": 3,
        "task_id": "T9",
        "attempt_id": ATTEMPT_ID,
        "executor_ref": EXECUTOR_REF,
        "state": "accepted",
        "synthetic": False,
    }
    return {**value, **overrides}


def decision(**overrides):
    value = {
        "schema_version": "1.2.0",
        "decision_id": DECISION_ID,
        "plan_id": "REQ-020",
        "revision": 3,
        "task_id": "T9",
        "selected_route_id": ROUTE_ID,
    }
    return {**value, **overrides}


def verdict(**overrides):
    value = {
        "verdict_id": VERDICT_ID,
        "plan_id": "REQ-020",
        "revision": 3,
        "task_id": "T9",
        "attempt_id": ATTEMPT_ID,
        "accepted": True,
        "verifier": "independent-reviewer",
        "evidence_present": True,
        "application_status": "applied",
        "synthetic": False,
        "applied_at": "2026-10-15T20:30:00Z",
    }
    return {**value, **overrides}


class PerformanceEventTests(unittest.TestCase):
    def normalize(self, *, attempt_row=_DEFAULT, decision_row=_DEFAULT, verdict_row=_DEFAULT):
        return normalize_performance_event(
            attempt() if attempt_row is _DEFAULT else attempt_row,
            decision() if decision_row is _DEFAULT else decision_row,
            verdict() if verdict_row is _DEFAULT else verdict_row,
        )

    def test_matching_independent_pass_is_eligible_and_redacted(self):
        event = self.normalize()
        self.assertEqual((event.outcome, event.eligible_for_history), ("pass", True))
        self.assertEqual((event.plan_id, event.revision, event.task_id, event.attempt_id),
                         ("REQ-020", 3, "T9", ATTEMPT_ID))
        self.assertEqual((event.decision_id, event.route_id, event.verdict_id),
                         (DECISION_ID, ROUTE_ID, VERDICT_ID))
        self.assertEqual(event.applied_at, "2026-10-15T20:30:00.000000Z")
        self.assertNotIn("evidence", event.to_dict())
        self.assertNotIn("executor_ref", event.to_dict())
        self.assertEqual(PerformanceEvent.from_dict(event.to_dict()), event)

    def test_matching_independent_fail_is_an_eligible_negative(self):
        event = self.normalize(attempt_row=attempt(state="rejected"),
                               verdict_row=verdict(accepted=False, evidence_present=False))
        self.assertEqual((event.outcome, event.eligible_for_history), ("fail", True))

    def test_m1_duplicate_verdict_replays_to_the_same_normalized_event(self):
        first = self.normalize()
        replay = self.normalize(verdict_row=verdict(application_status="duplicate"))
        self.assertEqual(first, replay)
        self.assertEqual(reduce_performance_events((first, replay)), (first,))

    def test_plan_revision_task_attempt_decision_and_route_must_all_match(self):
        cases = (
            ("plan", {"decision_row": decision(plan_id="REQ-OTHER")}),
            ("revision", {"decision_row": decision(revision=4)}),
            ("task", {"decision_row": decision(task_id="OTHER")}),
            ("decision", {"decision_row": decision(decision_id="d" * 64)}),
            ("route", {"decision_row": decision(selected_route_id=OTHER_ROUTE_ID)}),
            ("verdict attempt", {"verdict_row": verdict(attempt_id="attempt-other")}),
            ("verdict plan", {"verdict_row": verdict(plan_id="REQ-OTHER")}),
            ("verdict revision", {"verdict_row": verdict(revision=4)}),
            ("verdict task", {"verdict_row": verdict(task_id="OTHER")}),
        )
        for label, overrides in cases:
            with self.subTest(label=label):
                event = self.normalize(**overrides)
                self.assertEqual(event.outcome, "unknown")
                self.assertFalse(event.eligible_for_history)

    def test_executor_reference_must_name_the_selected_route(self):
        event = self.normalize(attempt_row=attempt(executor_ref="route:local"))
        self.assertEqual(event.outcome, "unknown")
        self.assertIn("route_reference_invalid", event.reason_codes)

    def test_verifier_must_be_present_and_independent_of_the_executor(self):
        for row, reason in ((verdict(verifier=""), "verifier_missing"),
                            (verdict(verifier=EXECUTOR_REF), "verifier_not_independent")):
            with self.subTest(reason=reason):
                event = self.normalize(verdict_row=row)
                self.assertEqual(event.outcome, "unknown")
                self.assertIn(reason, event.reason_codes)

    def test_claim_cancel_and_infrastructure_failure_never_become_quality_labels(self):
        cases = (("claimed", None, "claimed_unverified"),
                 ("cancelled", None, "cancelled"),
                 ("failed", None, "infrastructure_failure"),
                 ("running", None, "unknown"))
        for state, verdict_row, expected in cases:
            with self.subTest(state=state):
                event = self.normalize(attempt_row=attempt(state=state), verdict_row=verdict_row)
                self.assertEqual(event.outcome, expected)
                self.assertFalse(event.eligible_for_history)

    def test_accepted_attempt_without_applied_verdict_stays_unknown(self):
        for status in (None, "stale", "invalid", "noop"):
            with self.subTest(status=status):
                row = None if status is None else verdict(application_status=status)
                event = self.normalize(verdict_row=row)
                self.assertEqual(event.outcome, "unknown")
                self.assertFalse(event.eligible_for_history)

    def test_later_m1_application_supersedes_an_earlier_tardy_rejection(self):
        stale = self.normalize(verdict_row=verdict(application_status="stale"))
        applied = self.normalize()
        for rows in ((stale, applied), (applied, stale)):
            with self.subTest(order=rows):
                self.assertEqual(reduce_performance_events(rows), (applied,))

    def test_missing_decision_correlation_cannot_create_a_label(self):
        event = self.normalize(decision_row=None)
        self.assertEqual(event.outcome, "unknown")
        self.assertIn("decision_missing", event.reason_codes)

    def test_missing_timestamp_evidence_or_synthetic_inputs_fail_closed(self):
        cases = (
            (verdict(applied_at=""), attempt(), "verdict_timestamp_missing"),
            (verdict(applied_at="not-a-date"), attempt(), "verdict_timestamp_invalid"),
            (verdict(evidence_present=False), attempt(), "pass_evidence_missing"),
            (verdict(synthetic=True), attempt(), "synthetic_evidence"),
            (verdict(), attempt(synthetic=True), "synthetic_evidence"),
        )
        for verdict_row, attempt_row, reason in cases:
            with self.subTest(reason=reason, row=verdict_row):
                event = self.normalize(attempt_row=attempt_row, verdict_row=verdict_row)
                self.assertEqual(event.outcome, "unknown")
                self.assertIn(reason, event.reason_codes)

    def test_attempt_state_must_agree_with_verdict(self):
        event = self.normalize(attempt_row=attempt(state="rejected"), verdict_row=verdict(accepted=True))
        self.assertEqual(event.outcome, "unknown")
        self.assertIn("attempt_verdict_state_mismatch", event.reason_codes)

    def test_duplicate_reduction_is_order_independent_and_conflicts_fail_closed(self):
        first = self.normalize()
        replay = self.normalize(verdict_row=verdict(application_status="duplicate"))
        conflict = self.normalize(attempt_row=attempt(state="rejected"),
                                  verdict_row=verdict(accepted=False, evidence_present=False))
        forward = reduce_performance_events((first, replay, conflict))
        reverse = reduce_performance_events((conflict, replay, first))
        self.assertEqual(forward, reverse)
        self.assertEqual(len(forward), 1)
        self.assertEqual(forward[0].outcome, "unknown")
        self.assertFalse(forward[0].eligible_for_history)
        self.assertIn("conflicting_duplicate", forward[0].reason_codes)

    def test_multiple_applied_verdict_ids_for_one_attempt_are_not_arbitrated(self):
        first = self.normalize()
        second = self.normalize(verdict_row=verdict(verdict_id="verdict-43"))
        reduced = reduce_performance_events((first, second))
        self.assertEqual(len(reduced), 2)
        self.assertTrue(all(event.outcome == "unknown" for event in reduced))
        self.assertTrue(all("multiple_applied_verdicts" in event.reason_codes for event in reduced))

    def test_attempt_ids_are_scoped_by_plan_revision_and_task(self):
        other_decision_id = "d" * 64
        other_route_id = "e" * 64
        other = self.normalize(
            attempt_row=attempt(
                plan_id="REQ-OTHER", revision=1,
                executor_ref=f"route:m2:v1:{other_decision_id}:{other_route_id}",
            ),
            decision_row=decision(
                decision_id=other_decision_id, plan_id="REQ-OTHER", revision=1,
                selected_route_id=other_route_id,
            ),
            verdict_row=verdict(
                verdict_id="verdict-other", plan_id="REQ-OTHER", revision=1,
            ),
        )
        reduced = reduce_performance_events((self.normalize(), other))
        self.assertEqual(len(reduced), 2)
        self.assertTrue(all(event.eligible_for_history for event in reduced))

    def test_serialized_events_reject_forged_eligibility_and_unknown_fields(self):
        event = self.normalize()
        forged = {**event.to_dict(), "eligible_for_history": False}
        with self.assertRaises(PerformanceEventError):
            PerformanceEvent.from_dict(forged)
        unexpected = {**event.to_dict(), "raw_provider_output": "must not persist"}
        with self.assertRaises(PerformanceEventError):
            PerformanceEvent.from_dict(unexpected)

    def test_contract_declares_the_same_event_boundary(self):
        contract_path = Path(__file__).resolve().parents[1] / "api-contract.json"
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        evidence = contract["performance_event"]
        self.assertEqual(evidence["schema_version"], "1.2.0")
        self.assertIn("attempt_id", evidence["identity_fields"])
        self.assertIn("decision_id", evidence["identity_fields"])
        self.assertIn("route_id", evidence["identity_fields"])
        self.assertTrue(evidence["requires_m1_applied_verdict_for_history"])
        self.assertEqual(evidence["outcome_values"], ["pass", "fail", "claimed_unverified", "cancelled",
                                                       "infrastructure_failure", "unknown"])

    def test_attempt_envelope_rejects_boolean_revision_and_unexpected_payloads(self):
        with self.assertRaises(PerformanceEventError):
            self.normalize(attempt_row=attempt(revision=True))
        with self.assertRaises(PerformanceEventError):
            self.normalize(attempt_row=attempt(raw_output="not allowed"))
        with self.assertRaises(PerformanceEventError):
            self.normalize(verdict_row=verdict(accepted=1))


if __name__ == "__main__":
    unittest.main()
