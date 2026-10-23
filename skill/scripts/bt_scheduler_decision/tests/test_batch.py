from __future__ import annotations

import dataclasses
import unittest

from bt_scheduler_decision.batch import (
    AccountConcurrency,
    BatchUnassignment,
    RouteQuotaRequirement,
    assess_batch_quota,
    plan_ready_batch,
)
from bt_scheduler_decision.contracts import DecisionInputError
from bt_scheduler_decision.identity import account_reference
from bt_scheduler_decision.policy import RoutePolicyConfig
from bt_scheduler_decision.quota import QuotaObservation, normalize_cached_windows
from bt_scheduler_decision.tests.support import candidate, task_facts
from bt_scheduler_decision.tests.support import request as make_request

NOW = 1_800_000_000.0
ACCOUNT = "acct:" + "a" * 64


def observations(model: str | None, windows: dict[str, tuple[float, float | None, int]], *,
                 observed_at: float = NOW - 60, valid_for: float = 7200) -> tuple[QuotaObservation, ...]:
    raw = {
        name: {"used_percent": used, "resets_at": reset, "window_minutes": duration}
        for name, (used, reset, duration) in windows.items()
    }
    unknown_resets = tuple(name for name, (_, reset, _) in windows.items() if reset is None)
    return normalize_cached_windows(
        account_ref=ACCOUNT, provider="claude", model=model, source="subscription_cache", source_status="ok",
        windows=raw, observed_at=observed_at, now=NOW, valid_for_seconds=valid_for,
        required_windows={name: duration for name, (_, _, duration) in windows.items()},
        unknown_reset_windows=unknown_resets,
    )


def route(route_number: int, windows: tuple[tuple[str | None, str], ...]) -> RouteQuotaRequirement:
    return RouteQuotaRequirement(f"{route_number:064x}", "claude", ACCOUNT, windows)


def candidate_for(profile: str, account: str, *, rank: int = 0, runtime_status: str = "available"):
    item = candidate(profile=profile, rank=rank)
    return dataclasses.replace(
        item,
        account_ref=account_reference(f"claude:{account}"),
        runtime_status=runtime_status,
    )


def ready_request(task_id: str, candidates: tuple, *, free_slots: int = 2, risk: str = "low"):
    facts = task_facts(task_id=task_id, classifications={"risk": risk})
    return dataclasses.replace(make_request(task=facts, candidates=candidates), free_slots=free_slots)


class BatchQuotaTests(unittest.TestCase):
    def test_alias_routes_share_one_account_pressure_without_summing_profile_budgets(self):
        required = ((None, "five_hour"), (None, "seven_day"))
        cache = observations(None, {
            "five_hour": (45, NOW + 3600, 300),
            "seven_day": (20, NOW + 86400, 10080),
        })
        result = assess_batch_quota(
            (route(1, required), route(2, required)), (*cache, *cache), now=NOW,
        )
        self.assertEqual(result.schema_version, "1.2.0")
        self.assertEqual(result.unique_account_count, 1)
        self.assertEqual(result.eligible_route_ids, (f"{1:064x}", f"{2:064x}"))
        self.assertEqual(result.routes[0].assessment.pressure_percent, 45)
        self.assertEqual(result.routes[0].assessment, result.routes[1].assessment)

    def test_near_short_reset_does_not_release_exhausted_weekly_window(self):
        required = ((None, "five_hour"), (None, "seven_day"))
        cache = observations(None, {
            "five_hour": (75, NOW + 60, 300),
            "seven_day": (100, NOW + 500_000, 10080),
        })
        result = assess_batch_quota((route(1, required),), cache, now=NOW)
        self.assertEqual(result.eligible_route_ids, ())
        self.assertEqual(result.excluded_route_ids, (f"{1:064x}",))
        self.assertEqual(result.routes[0].assessment.state, "exhausted")
        self.assertEqual(result.routes[0].assessment.exhausted_windows, ("base:seven_day",))

    def test_all_base_and_model_specific_windows_are_required(self):
        required = ((None, "five_hour"), (None, "seven_day"), ("sonnet", "seven_day_sonnet"))
        base = observations(None, {
            "five_hour": (30, NOW + 3600, 300), "seven_day": (40, NOW + 86400, 10080),
        })
        specific = observations("sonnet", {"seven_day_sonnet": (55, NOW + 172800, 10080)})
        result = assess_batch_quota((route(1, required),), (*base, *specific), now=NOW)
        self.assertEqual(result.eligible_route_ids, (f"{1:064x}",))
        self.assertEqual(result.routes[0].assessment.pressure_percent, 55)
        missing_model_window = assess_batch_quota((route(2, required),), base, now=NOW)
        self.assertEqual(missing_model_window.routes[0].assessment.state, "unknown")
        self.assertIn("sonnet:seven_day_sonnet", missing_model_window.routes[0].assessment.unavailable_windows)

    def test_stale_or_unknown_shared_window_excludes_only_routes_requiring_it(self):
        base = observations(None, {
            "five_hour": (15, NOW + 3600, 300), "seven_day": (25, NOW + 86400, 10080),
        })
        stale_model = observations("opus", {"seven_day_opus": (20, NOW + 172800, 10080)},
                                   observed_at=NOW - 8000, valid_for=7200)
        base_req = route(1, ((None, "five_hour"), (None, "seven_day")))
        opus_req = route(2, ((None, "five_hour"), (None, "seven_day"), ("opus", "seven_day_opus")))
        result = assess_batch_quota((base_req, opus_req), (*base, *stale_model), now=NOW)
        self.assertEqual(result.eligible_route_ids, (f"{1:064x}",))
        self.assertEqual(result.routes[1].assessment.state, "unknown")

    def test_duplicate_route_ids_and_duplicate_window_requirements_fail_closed(self):
        requirement = route(1, ((None, "five_hour"),))
        with self.assertRaises(ValueError):
            assess_batch_quota((requirement, requirement), observations(None, {
                "five_hour": (10, NOW + 3600, 300),
            }), now=NOW)
        with self.assertRaises(ValueError):
            assess_batch_quota((route(2, ((None, "five_hour"), (None, "five_hour"))),),
                               observations(None, {"five_hour": (10, NOW + 3600, 300)}), now=NOW)

    def test_conflicting_reads_of_one_shared_window_make_the_route_unknown(self):
        first = observations(None, {"five_hour": (10, NOW + 3600, 300)})
        second = observations(None, {"five_hour": (12, NOW + 3600, 300)})
        result = assess_batch_quota(
            (route(1, ((None, "five_hour"),)),), (*first, *second), now=NOW,
        )
        self.assertEqual(result.routes[0].assessment.state, "unknown")
        self.assertEqual(result.routes[0].assessment.reason_code, "duplicate_window")


class ReadyBatchPlanningTests(unittest.TestCase):
    def test_plan_is_bounded_stable_and_independent_of_input_order(self):
        requests = (
            ready_request("T3", (candidate_for("profile-c", "account-c"),)),
            ready_request("T1", (candidate_for("profile-a", "account-a"),)),
            ready_request("T2", (candidate_for("profile-b", "account-b"),)),
        )

        first = plan_ready_batch(requests)
        replay = plan_ready_batch(tuple(reversed(requests)))

        self.assertEqual(first, replay)
        self.assertEqual(first.batch_policy_version, "m2-bounded-batch-v1")
        self.assertEqual(len(first.assignments), 2)
        self.assertEqual(tuple(row.task_id for row in first.assignments), ("T1", "T2"))
        self.assertEqual(tuple(row.reason_code for row in first.unassigned), ("free_slots_exhausted",))
        self.assertEqual(first.batch_id, replay.batch_id)
        self.assertEqual(len(first.batch_id), 64)

    def test_shared_account_capacity_counts_active_work_and_profile_aliases_once(self):
        shared_account = account_reference("claude:one-effective-account")
        first = dataclasses.replace(candidate(profile="profile-a"), account_ref=shared_account)
        alias = dataclasses.replace(candidate(profile="profile-b"), account_ref=shared_account)
        requests = (
            ready_request("T1", (first,)),
            ready_request("T2", (alias,)),
        )

        result = plan_ready_batch(
            requests,
            account_concurrency=(AccountConcurrency(shared_account, active_assignments=1, max_concurrent=2),),
        )

        self.assertEqual(tuple(row.task_id for row in result.assignments), ("T1",))
        self.assertEqual(result.assignments[0].account_ref, shared_account)
        self.assertEqual(result.unassigned, (BatchUnassignment("T2", "account_concurrency_exhausted"),))

    def test_flexible_task_moves_to_an_alternate_account_for_a_constrained_task(self):
        account_a = account_reference("claude:account-a")
        account_b = account_reference("claude:account-b")
        flexible_a = candidate_for("flexible-a", "account-a", rank=0)
        flexible_b = candidate_for("flexible-b", "account-b", rank=1)
        constrained_a = candidate_for("constrained-a", "account-a", rank=0)
        requests = (
            ready_request("T1-flexible", (flexible_a, flexible_b)),
            ready_request("T2-constrained", (constrained_a,)),
        )

        result = plan_ready_batch(
            requests,
            account_concurrency=(
                AccountConcurrency(account_a, active_assignments=0, max_concurrent=1),
                AccountConcurrency(account_b, active_assignments=0, max_concurrent=1),
            ),
        )

        by_task = {row.task_id: row for row in result.assignments}
        self.assertEqual(by_task["T1-flexible"].account_ref, account_b)
        self.assertEqual(by_task["T2-constrained"].account_ref, account_a)
        self.assertEqual(by_task["T1-flexible"].reason_code, "account_capacity_alternative")
        self.assertEqual(by_task["T2-constrained"].reason_code, "route_policy_preferred")
        self.assertEqual(len(result.assignments), 2)

    def test_unroutable_ready_task_does_not_block_a_later_assignment(self):
        unavailable = candidate_for("unavailable", "account-a", runtime_status="unavailable")
        requests = (
            ready_request("T1-unroutable", (unavailable,)),
            ready_request("T2-routable", (candidate_for("available", "account-b"),)),
        )

        result = plan_ready_batch(requests)

        self.assertEqual(tuple(row.task_id for row in result.assignments), ("T2-routable",))
        self.assertEqual(result.unassigned[0].task_id, "T1-unroutable")
        self.assertEqual(result.unassigned[0].reason_code, "no_eligible_route")
        self.assertEqual(result.route_exclusions[0].task_id, "T1-unroutable")
        self.assertEqual(result.route_exclusions[0].reason_codes, ("runtime_unavailable",))

    def test_route_policy_floor_runs_before_batch_capacity_selection(self):
        requests = (ready_request("T1", (candidate_for("only-route", "account-a"),), risk="high"),)

        result = plan_ready_batch(
            requests,
            policy=RoutePolicyConfig(quality_floors_by_risk=(("high", 0.7),)),
        )

        self.assertEqual(result.assignments, ())
        self.assertEqual(result.unassigned[0].reason_code, "quality_floor_no_supported_route")
        self.assertEqual(result.route_exclusions[0].reason_codes, ("quality_evidence_insufficient",))

    def test_inconsistent_batch_snapshots_and_duplicate_account_limits_fail_closed(self):
        one = ready_request("T1", (candidate_for("one", "account-a"),))
        other_snapshot = dataclasses.replace(one, revision=2,
                                               task=task_facts(task_id="T2"))
        account = one.candidates[0].account_ref

        with self.assertRaises(DecisionInputError):
            plan_ready_batch((one, other_snapshot))
        with self.assertRaises(DecisionInputError):
            plan_ready_batch((one,), account_concurrency=(
                AccountConcurrency(account, 0, 1), AccountConcurrency(account, 0, 2),
            ))


if __name__ == "__main__":
    unittest.main()
