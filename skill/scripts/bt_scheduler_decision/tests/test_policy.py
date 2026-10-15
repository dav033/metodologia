from __future__ import annotations

import dataclasses
import unittest

from bt_scheduler_decision import (
    deterministic_reference,
    rank_candidates,
    validate_request,
)
from bt_scheduler_decision.tests.support import candidate, request


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


if __name__ == "__main__":
    unittest.main()
