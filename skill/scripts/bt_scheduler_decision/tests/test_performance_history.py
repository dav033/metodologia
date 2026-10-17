from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from bt_scheduler_decision import (
    PerformanceContext,
    PerformanceHistoryError,
    aggregate_performance_history,
    normalize_performance_event,
)

ROUTE_ID = "b" * 64
OTHER_ROUTE_ID = "c" * 64
PLAN_ID = "REQ-020"
REVISION = 3
TARGET = PerformanceContext(
    task_family="implementation",
    complexity="medium",
    scope="small_change",
    risk="low",
    coupling="low",
)


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def event_for(task_id: str, outcome: str, *, context: PerformanceContext | None = TARGET,
              route_id: str = ROUTE_ID, application_status: str = "applied"):
    decision_id = _hash(f"decision:{task_id}")
    attempt_id = f"attempt:{task_id}"
    attempt_state = {
        "pass": "accepted",
        "fail": "rejected",
        "claimed_unverified": "claimed",
        "cancelled": "cancelled",
        "infrastructure_failure": "failed",
        "unknown": "accepted",
    }[outcome]
    attempt = {
        "plan_id": PLAN_ID,
        "revision": REVISION,
        "task_id": task_id,
        "attempt_id": attempt_id,
        "executor_ref": f"route:m2:v1:{decision_id}:{route_id}",
        "state": attempt_state,
        "synthetic": False,
    }
    decision = {
        "schema_version": "1.2.0",
        "decision_id": decision_id,
        "plan_id": PLAN_ID,
        "revision": REVISION,
        "task_id": task_id,
        "selected_route_id": route_id,
    }
    verdict = None
    if outcome in ("pass", "fail", "unknown"):
        verdict_status = "stale" if outcome == "unknown" and application_status == "applied" else application_status
        verdict = {
            "verdict_id": f"verdict:{task_id}",
            "plan_id": PLAN_ID,
            "revision": REVISION,
            "task_id": task_id,
            "attempt_id": attempt_id,
            "accepted": outcome != "fail",
            "verifier": "independent-reviewer",
            "evidence_present": True,
            "application_status": verdict_status,
            "synthetic": False,
            "applied_at": "2026-10-15T20:30:00Z" if verdict_status == "applied" else "",
        }
    normalized = normalize_performance_event(attempt, decision, verdict)
    contexts = {(PLAN_ID, REVISION, task_id): context} if context is not None else {}
    return normalized, contexts


def aggregate(rows, *, target: PerformanceContext = TARGET, route_id: str = ROUTE_ID):
    events = [event for event, _ in rows]
    contexts = {key: value for _, mapping in rows for key, value in mapping.items()}
    return aggregate_performance_history(events, contexts, route_id=route_id, target_context=target)


class PerformanceHistoryTests(unittest.TestCase):
    def test_exact_context_reports_verified_counts_coverage_and_descriptive_uncertainty(self):
        rows = [event_for(f"exact-{index}", "pass" if index < 3 else "fail") for index in range(5)]
        result = aggregate(rows)
        exact = result.measurements[0]
        self.assertEqual(result.selected_level, "exact_context")
        self.assertEqual(result.selected_shrunk_feature, 5 / 9)
        self.assertEqual((exact.attempt_count, exact.verified_samples, exact.verified_successes,
                          exact.verified_failures), (5, 5, 3, 2))
        self.assertEqual(exact.coverage, 1.0)
        self.assertEqual(exact.observed_rate, 0.6)
        self.assertLess(exact.uncertainty_interval_95[0], exact.observed_rate)
        self.assertGreater(exact.uncertainty_interval_95[1], exact.observed_rate)
        self.assertEqual(exact.source_quality, "observed")
        self.assertEqual(result.fallback_reasons, ())

    def test_nonquality_outcomes_reduce_coverage_without_counting_as_quality_failures(self):
        outcomes = ("pass", "pass", "fail", "infrastructure_failure", "cancelled", "claimed_unverified", "unknown")
        result = aggregate([event_for(f"mixed-{index}", outcome) for index, outcome in enumerate(outcomes)])
        exact = result.measurements[0]
        self.assertEqual(exact.attempt_count, 7)
        self.assertEqual((exact.verified_samples, exact.verified_successes, exact.verified_failures), (3, 2, 1))
        self.assertEqual((exact.infrastructure_failures, exact.cancelled, exact.claimed_unverified, exact.unknown),
                         (1, 1, 1, 1))
        self.assertAlmostEqual(exact.coverage, 3 / 7)
        self.assertEqual(exact.source_quality, "sparse")
        self.assertEqual(result.selected_level, "baseline")
        self.assertIsNone(result.selected_shrunk_feature)

    def test_sparse_exact_and_class_fall_back_to_task_family(self):
        rows = [event_for(f"exact-{index}", "pass") for index in range(2)]
        rows.extend(event_for(f"class-{index}", "fail", context=PerformanceContext(
            task_family=f"other-{index}", complexity="medium", scope="large_change", risk="high", coupling="high",
        )) for index in range(2))
        rows.extend(event_for(f"family-{index}", "pass", context=PerformanceContext(
            task_family="implementation", complexity="high", scope="large_change", risk="high", coupling="high",
        )) for index in range(5))
        result = aggregate(rows)
        self.assertEqual(result.selected_level, "task_family")
        self.assertEqual(result.measurements[0].verified_samples, 2)
        self.assertEqual(result.measurements[1].verified_samples, 4)
        self.assertEqual(result.measurements[2].verified_samples, 7)
        self.assertEqual(result.fallback_reasons, ("exact_context_sparse", "complexity_class_sparse"))

    def test_route_aggregate_is_last_measurement_before_the_existing_baseline(self):
        rows = [event_for(f"route-{index}", "fail", context=PerformanceContext(
            task_family="review", complexity="high", scope="full_feature", risk="high", coupling="high",
        )) for index in range(5)]
        result = aggregate(rows)
        self.assertEqual(result.selected_level, "route")
        self.assertEqual(result.selected_shrunk_feature, 2 / 9)
        self.assertEqual(result.fallback_reasons, (
            "exact_context_missing", "complexity_class_missing", "task_family_missing",
        ))

    def test_sparse_route_history_falls_back_to_baseline_without_exposing_a_selected_feature(self):
        result = aggregate([event_for(f"sparse-{index}", "pass") for index in range(4)])
        self.assertEqual(result.selected_level, "baseline")
        self.assertIsNone(result.selected_shrunk_feature)
        self.assertEqual(result.measurements[-1].verified_samples, 4)
        self.assertEqual(result.fallback_reasons[-1], "route_sparse")

    def test_missing_context_still_counts_at_route_level_and_uses_the_route_fallback(self):
        rows = [event_for(f"missing-context-{index}", "pass", context=None) for index in range(5)]
        result = aggregate(rows)
        self.assertEqual(result.selected_level, "route")
        self.assertEqual([item.attempt_count for item in result.measurements], [0, 0, 0, 5])
        self.assertEqual(result.fallback_reasons[:3], (
            "exact_context_missing", "complexity_class_missing", "task_family_missing",
        ))

    def test_nonapplied_outcome_is_unknown_and_does_not_become_a_failure(self):
        event, context = event_for("stale", "unknown", application_status="stale")
        result = aggregate(((event, context),))
        exact = result.measurements[0]
        self.assertEqual((exact.verified_samples, exact.verified_failures, exact.unknown), (0, 0, 1))
        self.assertEqual(result.selected_level, "baseline")

    def test_other_routes_do_not_enter_the_target_route_aggregate(self):
        rows = [event_for(f"other-route-{index}", "pass", route_id=OTHER_ROUTE_ID) for index in range(5)]
        result = aggregate(rows)
        self.assertEqual(result.selected_level, "baseline")
        self.assertEqual(result.measurements[-1].attempt_count, 0)
        self.assertEqual(result.fallback_reasons[-1], "route_missing")

    def test_replays_and_conflicting_duplicates_count_one_attempt(self):
        first, context = event_for("duplicate", "pass")
        deduped = aggregate(((first, context), (first, context)))
        self.assertEqual(deduped.measurements[-1].attempt_count, 1)
        conflicting, _ = event_for("duplicate", "fail")
        conflicted = aggregate(((first, context), (conflicting, context)))
        self.assertEqual(conflicted.measurements[-1].attempt_count, 1)
        self.assertEqual(conflicted.measurements[-1].unknown, 1)
        self.assertEqual(conflicted.measurements[-1].verified_samples, 0)

    def test_contextual_snapshot_is_deterministic_and_redacted(self):
        rows = [event_for(f"stable-{index}", "pass" if index % 2 == 0 else "fail") for index in range(5)]
        first = aggregate(rows).to_dict()
        second = aggregate(list(reversed(rows))).to_dict()
        self.assertEqual(first, second)
        serialized = json.dumps(first)
        self.assertNotIn("brief", serialized)
        self.assertNotIn("verifier", serialized)
        self.assertNotIn("raw_output", serialized)

    def test_context_dimensions_reject_free_text_and_identity_alias_collisions(self):
        with self.assertRaises(PerformanceHistoryError):
            PerformanceContext.from_dict({
                "schema_version": "1.2.0", "task_family": "build task", "complexity": "medium",
                "scope": "small_change", "risk": "low", "coupling": "low",
            })
        first, context_map = event_for("unicode", "pass")
        context = context_map[(PLAN_ID, REVISION, "unicode")]
        colliding_contexts = {
            (PLAN_ID, REVISION, "cafe\u0301"): context,
            (PLAN_ID, REVISION, "café"): context,
        }
        with self.assertRaises(PerformanceHistoryError):
            aggregate_performance_history(
                (first,), colliding_contexts, route_id=ROUTE_ID, target_context=TARGET,
            )

    def test_contract_declares_hierarchy_uncertainty_and_nonprobability_semantics(self):
        contract_path = Path(__file__).resolve().parents[1] / "api-contract.json"
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        history = contract["performance_history"]
        self.assertEqual(history["fallback_levels"], ["exact_context", "complexity_class", "task_family", "route", "baseline"])
        self.assertEqual(history["minimum_verified_samples"], 5)
        self.assertFalse(history["is_future_success_probability"])
        self.assertIn("uncertainty_interval_95", history["measurement_fields"])
        self.assertIn("coverage", history["measurement_fields"])


if __name__ == "__main__":
    unittest.main()
