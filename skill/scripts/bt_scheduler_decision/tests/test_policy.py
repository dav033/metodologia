from __future__ import annotations

import dataclasses
import math
import unittest

from bt_scheduler_decision import (
    deterministic_reference,
    rank_candidates,
    validate_request,
)
from bt_scheduler_decision.contracts import API_VERSION
from bt_scheduler_decision.history import (
    ContextualHistoryAssessment,
    PerformanceMeasurement,
)
from bt_scheduler_decision.policy import (
    DEFAULT_ROUTE_POLICY,
    OBJECTIVE_ORDER,
    ROUTE_POLICY_VERSION,
    QuotaWindowPreference,
    RoutePolicyConfig,
    RoutePolicyEvidence,
    rank_with_route_policy,
)
from bt_scheduler_decision.tests.support import candidate, request


def _quality_assessment(route_id: str, successes: int, failures: int) -> ContextualHistoryAssessment:
    samples = successes + failures
    observed_rate = successes / samples if samples else None
    z = 1.959963984540054
    denominator = 1 + z * z / samples
    center = (observed_rate + z * z / (2 * samples)) / denominator
    margin = z * math.sqrt(observed_rate * (1 - observed_rate) / samples + z * z / (4 * samples * samples)) / denominator
    interval = (max(0.0, center - margin), min(1.0, center + margin))
    measurement = PerformanceMeasurement(
        API_VERSION, "route", samples, samples, successes, failures, 0, 0, 0, 0, 1.0, observed_rate,
        interval, (successes + 2) / (samples + 4), "observed" if samples >= 5 else "sparse",
    )
    return ContextualHistoryAssessment(
        API_VERSION, route_id, 5, (measurement,), "route", measurement.shrunk_feature, (),
    )


class CandidatePolicyTests(unittest.TestCase):
    def test_hard_filters_exclude_unknown_quota_auth_and_unauthorized_profiles(self):
        candidates = (
            candidate(profile="authorized"),
            candidate(profile="unknown-quota", quota_status="unknown"),
            dataclasses.replace(candidate(profile="bad-auth"), auth_status="invalid"),
            dataclasses.replace(candidate(profile="unauthorized"), profile_authorized=False),
        )
        result = rank_candidates(request(candidates=candidates))
        self.assertEqual([item.profile for item in result.eligible], ["authorized"])
        reasons = {item.profile: item.reason_codes for item in result.exclusions}
        self.assertIn("quota_unknown", reasons["unknown-quota"])
        self.assertIn("auth_invalid", reasons["bad-auth"])
        self.assertIn("profile_not_authorized", reasons["unauthorized"])

    def test_reference_uses_router_rank_then_stable_route_id_not_input_order(self):
        slow = candidate(provider="codex", model="sol", profile="later", rank=2)
        first = candidate(profile="first", rank=1)
        tied = candidate(provider="codex", model="luna", profile="tied", rank=1)
        one = rank_candidates(request(candidates=(slow, first, tied)))
        two = rank_candidates(request(candidates=(tied, slow, first)))
        self.assertEqual(tuple(item.route_id for item in one.eligible), tuple(item.route_id for item in two.eligible))
        self.assertEqual(one.selected, min((first, tied), key=lambda item: item.route_id))
        self.assertEqual(deterministic_reference(request(candidates=(slow, first, tied))), one.selected)

    def test_no_eligible_route_returns_no_assignment(self):
        unavailable = dataclasses.replace(candidate(), runtime_status="unavailable")
        result = rank_candidates(request(candidates=(unavailable,)))
        self.assertIsNone(result.selected)
        self.assertEqual(result.eligible, ())
        self.assertIn("runtime_unavailable", result.exclusions[0].reason_codes)

    def test_capacity_blocking_source_codes_win_over_contradictory_available_status(self):
        unknown = dataclasses.replace(candidate(profile="unknown-capacity"),
                                      source_reason_codes=("capacity_unknown",))
        exhausted_code = dataclasses.replace(candidate(profile="exhausted-capacity-code"),
                                             source_reason_codes=("capacity_exhausted",))
        cooling = dataclasses.replace(candidate(profile="cooling"), source_reason_codes=("cooldown_active",))
        exhausted_state = dataclasses.replace(candidate(profile="exhausted-capacity-state"),
                                        source_status="capacity_exhausted")
        result = rank_candidates(request(candidates=(unknown, exhausted_code, cooling, exhausted_state)))
        self.assertEqual(result.eligible, ())
        by_profile = {item.profile: item.reason_codes for item in result.exclusions}
        self.assertIn("capacity_unknown", by_profile["unknown-capacity"])
        self.assertIn("capacity_exhausted", by_profile["exhausted-capacity-code"])
        self.assertIn("route_cooling_down", by_profile["cooling"])
        self.assertIn("capacity_exhausted", by_profile["exhausted-capacity-state"])

    def test_forged_validated_wrapper_is_revalidated_at_policy_boundary(self):
        valid = validate_request(request())
        forged = dataclasses.replace(valid, request=dataclasses.replace(valid.request, candidates=()))
        self.assertIsNone(deterministic_reference(forged))

    def test_multiobjective_policy_never_reintroduces_a_hard_excluded_route(self):
        quality_route = candidate(profile="quality", rank=1)
        quota_route = candidate(provider="codex", model="sol", profile="quota", rank=0)
        ineligible = candidate(profile="ineligible", rank=0, quota_status="unknown")
        evidence = {
            quality_route.route_id: RoutePolicyEvidence(
                _quality_assessment(quality_route.route_id, 90, 10),
                (QuotaWindowPreference("weekly", 85, 86_400),), 120, 8, "relative-v1",
            ),
            quota_route.route_id: RoutePolicyEvidence(
                _quality_assessment(quota_route.route_id, 65, 35),
                (QuotaWindowPreference("weekly", 25, 86_400),), 60, 1, "relative-v1",
            ),
            ineligible.route_id: RoutePolicyEvidence(
                _quality_assessment(ineligible.route_id, 100, 0),
                (QuotaWindowPreference("weekly", 0, 86_400),), 1, 0, "relative-v1",
            ),
        }
        policy = RoutePolicyConfig(quality_floors_by_risk=(("high", 0.50),))

        result = rank_with_route_policy(request(candidates=(quota_route, ineligible, quality_route)), evidence,
                                        risk="high", policy=policy)

        self.assertEqual([item.route_id for item in result.eligible], [quality_route.route_id, quota_route.route_id])
        self.assertEqual(result.selected, quality_route)
        self.assertEqual([item.route_id for item in result.hard_exclusions], [ineligible.route_id])
        self.assertEqual(result.quality_exclusions, ())
        self.assertEqual(result.policy_version, ROUTE_POLICY_VERSION)

    def test_quality_floor_requires_correlated_history_and_minimum_samples(self):
        insufficient = candidate(profile="few-samples", rank=0)
        weak = candidate(profile="below-floor", rank=1)
        enough = candidate(profile="above-floor", rank=2)
        policy = RoutePolicyConfig(quality_floors_by_risk=(("high", 0.60),))
        evidence = {
            insufficient.route_id: RoutePolicyEvidence(_quality_assessment(insufficient.route_id, 2, 2)),
            weak.route_id: RoutePolicyEvidence(_quality_assessment(weak.route_id, 55, 45)),
            enough.route_id: RoutePolicyEvidence(_quality_assessment(enough.route_id, 85, 15)),
        }

        result = rank_with_route_policy(request(candidates=(insufficient, weak, enough)), evidence, risk="high",
                                        policy=policy)

        self.assertEqual(result.eligible, (enough,))
        self.assertEqual(result.selected, enough)
        self.assertEqual({item.route_id: item.reason_code for item in result.quality_exclusions}, {
            insufficient.route_id: "quality_evidence_insufficient",
            weak.route_id: "quality_floor_not_met",
        })

    def test_unknown_quality_evidence_keeps_the_deterministic_baseline(self):
        baseline = candidate(profile="baseline", rank=0)
        lower_quota = candidate(provider="codex", model="sol", profile="lower-quota", rank=1)
        evidence = {
            baseline.route_id: RoutePolicyEvidence(quota_windows=(QuotaWindowPreference("weekly", 70, 900),)),
            lower_quota.route_id: RoutePolicyEvidence(
                quota_windows=(QuotaWindowPreference("weekly", 10, 900),), relative_cost=0.1,
                relative_cost_scale="relative-v1",
            ),
        }

        result = rank_with_route_policy(request(candidates=(lower_quota, baseline)), evidence)

        self.assertEqual(result.eligible, (baseline, lower_quota))
        self.assertEqual(result.selected, baseline)
        self.assertEqual(result.fallback_reason, "quality_evidence_unavailable")

    def test_quota_pressure_precedes_reset_preference_and_other_windows_remain_controlling(self):
        high_pressure = candidate(profile="high-pressure", rank=0)
        lower_pressure = candidate(provider="codex", model="sol", profile="lower-pressure", rank=1)
        same_pressure_far_reset = candidate(provider="codex", model="luna", profile="same-pressure", rank=2)

        def common_quality(route):
            return RoutePolicyEvidence(
                _quality_assessment(route.route_id, 80, 20), duration_seconds=30, relative_cost=1,
                relative_cost_scale="relative-v1",
            )

        evidence = {
            high_pressure.route_id: dataclasses.replace(
                common_quality(high_pressure),
                quota_windows=(QuotaWindowPreference("five-hour", 95, 600),
                               QuotaWindowPreference("weekly", 70, 90_000)),
            ),
            lower_pressure.route_id: dataclasses.replace(
                common_quality(lower_pressure),
                quota_windows=(QuotaWindowPreference("weekly", 75, 90_000),),
            ),
            same_pressure_far_reset.route_id: dataclasses.replace(
                common_quality(same_pressure_far_reset),
                quota_windows=(QuotaWindowPreference("five-hour", 95, 90_000),
                               QuotaWindowPreference("weekly", 70, 600)),
            ),
        }

        result = rank_with_route_policy(request(candidates=(high_pressure, lower_pressure, same_pressure_far_reset)),
                                        evidence)

        self.assertEqual(result.selected, lower_pressure)
        self.assertLess(result.eligible.index(lower_pressure), result.eligible.index(high_pressure))
        self.assertLess(result.eligible.index(high_pressure), result.eligible.index(same_pressure_far_reset))

    def test_comparable_cost_is_used_after_quality_quota_and_duration(self):
        expensive = candidate(profile="expensive", rank=0)
        cheap = candidate(provider="codex", model="sol", profile="cheap", rank=1)
        evidence = {
            expensive.route_id: RoutePolicyEvidence(
                _quality_assessment(expensive.route_id, 80, 20),
                (QuotaWindowPreference("weekly", 45, 90_000),), 50, 9, "relative-v1", True,
            ),
            cheap.route_id: RoutePolicyEvidence(
                _quality_assessment(cheap.route_id, 80, 20),
                (QuotaWindowPreference("weekly", 45, 90_000),), 50, 1, "relative-v1", True,
            ),
        }

        result = rank_with_route_policy(request(candidates=(expensive, cheap)), evidence)

        self.assertEqual(result.selected, cheap)

    def test_strategic_reserve_precedes_a_soon_reset(self):
        reserved = candidate(profile="reserved", rank=0)
        available = candidate(provider="codex", model="sol", profile="available", rank=1)
        evidence = {
            reserved.route_id: RoutePolicyEvidence(
                _quality_assessment(reserved.route_id, 80, 20),
                (QuotaWindowPreference("weekly", 50, 600),), 50, 1, "relative-v1", True,
            ),
            available.route_id: RoutePolicyEvidence(
                _quality_assessment(available.route_id, 80, 20),
                (QuotaWindowPreference("weekly", 50, 90_000),), 50, 1, "relative-v1", False,
            ),
        }

        result = rank_with_route_policy(request(candidates=(reserved, available)), evidence)

        self.assertEqual(result.selected, available)

    def test_policy_order_is_versioned_and_default_has_no_unapproved_numeric_floor(self):
        self.assertEqual(DEFAULT_ROUTE_POLICY.version, ROUTE_POLICY_VERSION)
        self.assertEqual(DEFAULT_ROUTE_POLICY.quality_floors_by_risk, ())
        self.assertEqual(OBJECTIVE_ORDER[0], "hard_eligibility")
        self.assertEqual(OBJECTIVE_ORDER[1:4], (
            "quality_floor", "verified_quality_lower_bound", "quality_uncertainty",
        ))
        with self.assertRaises(ValueError):
            RoutePolicyConfig(quality_floors_by_risk=(("high", 1.1),))


if __name__ == "__main__":
    unittest.main()
