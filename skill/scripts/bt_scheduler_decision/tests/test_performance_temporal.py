from __future__ import annotations

import hashlib
import json
import unittest
from datetime import datetime
from pathlib import Path

from bt_scheduler_decision import (
    PerformanceContext,
    TemporalEvaluationError,
    evaluate_prequential_history,
    normalize_performance_event,
)

ROUTE_ID = "b" * 64
TARGET = PerformanceContext(
    task_family="implementation",
    complexity="medium",
    scope="small_change",
    risk="low",
    coupling="low",
)


def _epoch(value: str) -> float:
    return datetime.fromisoformat(value).timestamp()


def _event_for(task_id: str, outcome: str, minute: int, *, attempt_id: str | None = None,
               verdict_id: str | None = None, route_id: str = ROUTE_ID,
               application_status: str = "applied"):
    attempt_id = attempt_id or f"attempt:{task_id}"
    decision_id = hashlib.sha256(f"decision:{task_id}".encode()).hexdigest()
    attempt_state = {
        "pass": "accepted",
        "fail": "rejected",
        "cancelled": "cancelled",
        "infrastructure_failure": "failed",
    }[outcome]
    attempt = {
        "plan_id": "REQ-020",
        "revision": 3,
        "task_id": task_id,
        "attempt_id": attempt_id,
        "executor_ref": f"route:m2:v1:{decision_id}:{route_id}",
        "state": attempt_state,
        "synthetic": False,
    }
    decision = {
        "schema_version": "1.2.0",
        "decision_id": decision_id,
        "plan_id": "REQ-020",
        "revision": 3,
        "task_id": task_id,
        "selected_route_id": route_id,
    }
    verdict = None
    if outcome in ("pass", "fail"):
        verdict = {
            "verdict_id": verdict_id or f"verdict:{task_id}",
            "plan_id": "REQ-020",
            "revision": 3,
            "task_id": task_id,
            "attempt_id": attempt_id,
            "accepted": outcome == "pass",
            "verifier": "independent-reviewer",
            "evidence_present": True,
            "application_status": application_status,
            "synthetic": False,
            "applied_at": f"2026-10-15T20:{minute:02d}:00Z",
        }
    event = normalize_performance_event(attempt, decision, verdict)
    return event, {("REQ-020", 3, task_id): TARGET}


def _aggregate(rows, cutoffs):
    events = [event for event, _ in rows]
    contexts = {key: value for _, mapping in rows for key, value in mapping.items()}
    return evaluate_prequential_history(
        events, contexts, route_id=ROUTE_ID, target_context=TARGET, cutoffs=cutoffs,
    )


class PerformanceTemporalTests(unittest.TestCase):
    def test_cutoff_uses_only_past_outcomes_and_fingerprint_excludes_future_facts(self):
        training = [_event_for(f"past-{index}", "pass", 30 + index) for index in range(5)]
        future = [
            _event_for("future-0", "pass", 40),
            _event_for("future-1", "fail", 41),
            _event_for("future-2", "pass", 42),
        ]
        cutoff = _epoch("2026-10-15T20:35:00Z")
        first = _aggregate([*training, *future, training[0]], (cutoff,))[0]
        changed_future = [
            _event_for("future-0", "fail", 40),
            _event_for("future-1", "fail", 41),
            _event_for("future-2", "fail", 42),
        ]
        second = _aggregate([*training, *changed_future], (cutoff,))[0]

        self.assertEqual(first.training_route_attempts, 5)
        self.assertEqual(first.training_route_verified_samples, 5)
        self.assertEqual(first.selected_level, "exact_context")
        self.assertEqual(first.history_feature_samples, 5)
        self.assertEqual(first.history_ranking_feature, 7 / 9)
        self.assertEqual(first.evaluation_attempts, 3)
        self.assertEqual(first.evaluation_verified_samples, 3)
        self.assertEqual((first.evaluation_successes, first.evaluation_failures), (2, 1))
        self.assertAlmostEqual(first.evaluation_observed_rate, 2 / 3)
        self.assertEqual(first.history_feature_coverage, 1.0)
        self.assertEqual(first.source_fingerprint, second.source_fingerprint)
        self.assertNotEqual(first.evaluation_observed_rate, second.evaluation_observed_rate)
        self.assertFalse(first.is_future_success_probability)
        self.assertFalse(first.to_dict()["is_future_success_probability"])

    def test_cutoff_is_inclusive_and_future_attempts_do_not_overlap_training(self):
        at_cutoff = _event_for("at-cutoff", "pass", 35)
        after_cutoff = _event_for("after-cutoff", "fail", 36)
        result = _aggregate([at_cutoff, after_cutoff], (_epoch("2026-10-15T20:35:00Z"),))[0]
        self.assertEqual(result.training_route_attempts, 1)
        self.assertEqual(result.training_route_verified_samples, 1)
        self.assertIsNone(result.history_ranking_feature)
        self.assertEqual(result.evaluation_attempts, 1)
        self.assertEqual(result.evaluation_failures, 1)

    def test_later_conflicting_verdict_cannot_change_an_earlier_cutoff(self):
        first = _event_for("same-task", "pass", 30, attempt_id="same-attempt", verdict_id="verdict-first")
        later = _event_for("same-task", "fail", 40, attempt_id="same-attempt", verdict_id="verdict-later")
        early_cutoff = _aggregate([first, later], (_epoch("2026-10-15T20:35:00Z"),))[0]
        late_cutoff = _aggregate([first, later], (_epoch("2026-10-15T20:45:00Z"),))[0]
        self.assertEqual(early_cutoff.training_route_verified_samples, 1)
        self.assertEqual(early_cutoff.evaluation_attempts, 0)
        self.assertEqual(late_cutoff.training_route_attempts, 1)
        self.assertEqual(late_cutoff.training_route_verified_samples, 0)
        self.assertEqual(late_cutoff.history_feature_coverage, None)

    def test_conflicting_applied_route_projections_are_reduced_before_route_filtering(self):
        target_route = _event_for("shared-attempt", "pass", 30, attempt_id="shared",
                                  verdict_id="shared-verdict")
        other_route = _event_for("shared-attempt", "pass", 30, attempt_id="shared",
                                 verdict_id="shared-verdict", route_id="c" * 64)
        result = _aggregate((target_route, other_route), (_epoch("2026-10-15T20:35:00Z"),))[0]
        self.assertEqual(result.training_route_verified_samples, 0)
        self.assertIsNone(result.history_ranking_feature)

    def test_nonapplied_timestamp_cannot_hide_a_later_applied_outcome(self):
        stale = _event_for("retry-applied", "pass", 30, attempt_id="retry-attempt",
                           verdict_id="retry-verdict", application_status="stale")
        applied = _event_for("retry-applied", "pass", 40, attempt_id="retry-attempt",
                             verdict_id="retry-verdict")
        result = _aggregate((stale, applied), (_epoch("2026-10-15T20:35:00Z"),))[0]
        self.assertEqual(result.training_route_attempts, 0)
        self.assertEqual(result.evaluation_attempts, 1)
        self.assertEqual(result.evaluation_successes, 1)
        self.assertEqual(result.untimed_attempts, 0)

    def test_untimed_attempts_are_reported_but_never_assigned_to_a_cutoff(self):
        training = [_event_for(f"past-{index}", "pass", 30 + index) for index in range(5)]
        future = _event_for("future", "pass", 40)
        untimed = _event_for("cancelled", "cancelled", 0)
        result = _aggregate([*training, future, untimed], (_epoch("2026-10-15T20:35:00Z"),))[0]
        self.assertEqual(result.training_route_attempts, 5)
        self.assertEqual(result.evaluation_attempts, 1)
        self.assertEqual(result.untimed_attempts, 1)

    def test_cutoffs_must_be_finite_unique_and_sorted(self):
        event = _event_for("one", "pass", 30)
        for cutoffs in ((2.0, 1.0), (1.0, 1.0), (float("nan"),)):
            with self.subTest(cutoffs=cutoffs), self.assertRaises(TemporalEvaluationError):
                _aggregate([event], cutoffs)

    def test_contract_declares_past_only_training_and_descriptive_future_outcomes(self):
        contract_path = Path(__file__).resolve().parents[1] / "api-contract.json"
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        temporal = contract["performance_temporal"]
        self.assertEqual(temporal["cutoff_field"],
                         "M1 applied_at on application_status=applied event, UTC epoch seconds")
        self.assertFalse(temporal["is_future_success_probability"])
        self.assertIn("<= cutoff", temporal["training_rule"])
        self.assertIn("> cutoff", temporal["evaluation_rule"])
        self.assertIn("across all routes", temporal["training_rule"])


if __name__ == "__main__":
    unittest.main()
