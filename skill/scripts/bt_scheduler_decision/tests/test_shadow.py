from __future__ import annotations

import dataclasses
import unittest
from unittest.mock import patch

from bt_scheduler_decision import (
    AccountConcurrency,
    DecisionInputError,
    QuotaWindowPreference,
    RoutePolicyEvidence,
    account_reference,
    batch,
    canonical_json,
    compare_shadow_batch,
    plan_ready_batch,
)
from bt_scheduler_decision.tests.support import candidate, request, task_facts


def _candidate(profile: str, account: str, rank: int):
    value = candidate(profile=profile, rank=rank)
    return dataclasses.replace(value, account_ref=account_reference(f"claude:{account}"))


def _request(task_id: str, candidates: tuple):
    facts = task_facts(task_id=task_id, classifications={"risk": "low"})
    return dataclasses.replace(request(task=facts, candidates=candidates), free_slots=2)


class ShadowComparisonTests(unittest.TestCase):
    def test_disabled_shadow_returns_before_reading_requests_or_running_planners(self):
        with patch("bt_scheduler_decision.shadow._plan_prepared_batch",
                   side_effect=AssertionError("planner called")):
            result = compare_shadow_batch((), enabled=False)

        self.assertIsNone(result)

    def test_opt_in_compares_route_and_capacity_choices_without_dispatch_side_effects(self):
        account_a = account_reference("claude:account-a")
        account_b = account_reference("claude:account-b")
        requests = (
            _request("T1-flexible", (
                _candidate("flexible-a", "account-a", 0),
                _candidate("flexible-b", "account-b", 1),
            )),
            _request("T2-constrained", (_candidate("constrained-a", "account-a", 0),)),
        )
        comparison = compare_shadow_batch(
            requests,
            enabled=True,
            account_concurrency=(
                AccountConcurrency(account_a, active_assignments=0, max_concurrent=1),
                AccountConcurrency(account_b, active_assignments=0, max_concurrent=1),
            ),
        )

        self.assertIsNotNone(comparison)
        assert comparison is not None
        baseline = {row.task_id: row for row in comparison.baseline_assignments}
        proposed = {row.task_id: row for row in comparison.proposed_plan.assignments}
        self.assertEqual(baseline["T1-flexible"].account_ref, account_a)
        self.assertEqual(comparison.baseline_unassigned[0].task_id, "T2-constrained")
        self.assertEqual(comparison.baseline_unassigned[0].reason_code, "account_concurrency_exhausted")
        self.assertEqual(proposed["T1-flexible"].account_ref, account_b)
        self.assertEqual(proposed["T2-constrained"].account_ref, account_a)
        self.assertEqual(
            tuple(row.difference_code for row in comparison.task_comparisons),
            ("route_changed", "assignment_added"),
        )
        self.assertFalse(comparison.dispatch_performed)
        self.assertFalse(comparison.reservations_created)
        self.assertFalse(comparison.task_state_changed)
        self.assertFalse(comparison.ledger_written)
        self.assertFalse(comparison.provider_called)
        serialized = canonical_json(comparison)
        self.assertNotIn("Update the validated scheduler route safely.", serialized)
        self.assertNotEqual(comparison.snapshot_sha256, comparison.comparison_sha256)

    def test_comparison_is_replayable_and_ready_order_is_bound(self):
        requests = (
            _request("T1", (_candidate("first", "account-a", 0),)),
            _request("T2", (_candidate("second", "account-b", 0),)),
        )

        first = compare_shadow_batch(requests, enabled=True)
        replay = compare_shadow_batch(requests, enabled=True)
        reversed_order = compare_shadow_batch(tuple(reversed(requests)), enabled=True)

        self.assertEqual(first, replay)
        self.assertIsNotNone(first)
        self.assertIsNotNone(reversed_order)
        assert first is not None and reversed_order is not None
        self.assertNotEqual(first.snapshot_sha256, reversed_order.snapshot_sha256)
        self.assertNotEqual(first.comparison_sha256, reversed_order.comparison_sha256)

    def test_proposed_plan_and_baseline_share_one_normalized_evidence_snapshot(self):
        route = _candidate("only", "account-a", 0)
        requests = (_request("T1", (route,)),)
        evidence = {"T1": {}}
        expected = compare_shadow_batch(requests, enabled=True, route_evidence_by_task=evidence)
        assert expected is not None

        original = batch._validated_evidence
        calls = 0

        def mutate_after_normalization(raw_evidence, requests_by_task):
            nonlocal calls
            normalized = original(raw_evidence, requests_by_task)
            calls += 1
            if calls == 1:
                evidence["T1"] = {
                    route.route_id: RoutePolicyEvidence(
                        quota_windows=(QuotaWindowPreference("weekly", 25, 3600),),
                    ),
                }
            return normalized

        with patch("bt_scheduler_decision.batch._validated_evidence", side_effect=mutate_after_normalization):
            comparison = compare_shadow_batch(requests, enabled=True, route_evidence_by_task=evidence)

        self.assertEqual(calls, 1)
        self.assertEqual(comparison, expected)
        self.assertEqual(
            comparison.proposed_plan,
            plan_ready_batch(requests, route_evidence_by_task={"T1": {}}),
        )

    def test_no_eligible_routes_and_reasons_are_recorded_without_task_text(self):
        unavailable = dataclasses.replace(candidate(profile="unavailable"), runtime_status="unavailable")
        comparison = compare_shadow_batch(
            (_request("T1", (unavailable,)),), enabled=True,
        )

        self.assertIsNotNone(comparison)
        assert comparison is not None
        self.assertEqual(comparison.baseline_unassigned[0].reason_code, "no_eligible_route")
        self.assertEqual(comparison.baseline_route_exclusions[0].reason_codes, ("runtime_unavailable",))
        self.assertEqual(comparison.proposed_plan.unassigned[0].reason_code, "no_eligible_route")
        self.assertEqual(comparison.task_comparisons[0].difference_code, "same_unassignment")
        self.assertNotIn("Update the validated scheduler route safely.", canonical_json(comparison))

    def test_invalid_opt_in_value_fails_closed(self):
        with self.assertRaisesRegex(DecisionInputError, "shadow.enabled"):
            compare_shadow_batch((), enabled=1)

    def test_invalid_policy_fails_with_stable_input_error(self):
        with self.assertRaisesRegex(DecisionInputError, "batch.policy"):
            compare_shadow_batch(
                (_request("T1", (_candidate("only", "account-a", 0),)),),
                enabled=True,
                policy=object(),
            )


if __name__ == "__main__":
    unittest.main()
