"""Deterministic adversarial checks across M2 quota/batch and M5 retry contracts."""
from __future__ import annotations

import dataclasses
import unittest

from bt_scheduler_decision.batch import (
    AccountConcurrency,
    RouteQuotaRequirement,
    assess_batch_quota,
    plan_ready_batch,
)
from bt_scheduler_decision.demand import attribute_quota_delta
from bt_scheduler_decision.identity import account_reference
from bt_scheduler_decision.quota import QuotaObservation, normalize_cached_windows
from bt_scheduler_decision.tests.support import candidate, task_facts
from bt_scheduler_decision.tests.support import request as make_request
from bt_scheduler_recovery import HistorySummary, Policy, RecoveryCase, propose

NOW = 1_800_000_000.0
ACCOUNT = account_reference("claude:shared-adversarial-account")
PLAN_SHA = "a" * 64
CONTEXT = "b" * 64


def quota_observations(*, windows: dict[str, object] | None = None, source_status: str = "ok",
                       observed_at: float = NOW - 30, now: float = NOW) -> tuple[QuotaObservation, ...]:
    selected = windows if windows is not None else {
        "five_hour": {"used_percent": 25, "resets_at": NOW + 300, "window_minutes": 300},
        "seven_day": {"used_percent": 35, "resets_at": NOW + 86_400, "window_minutes": 10_080},
    }
    return normalize_cached_windows(
        account_ref=ACCOUNT,
        provider="claude",
        model=None,
        source="subscription_cache",
        source_status=source_status,
        windows=selected,
        observed_at=observed_at,
        now=now,
        valid_for_seconds=3600,
        required_windows={"five_hour": 300, "seven_day": 10_080},
    )


def quota_requirement(route_number: int) -> RouteQuotaRequirement:
    return RouteQuotaRequirement(
        route_id=f"{route_number:064x}",
        provider="claude",
        account_ref=ACCOUNT,
        required_windows=((None, "five_hour"), (None, "seven_day")),
    )


def route_candidate(profile: str, account: str, *, rank: int = 0):
    return dataclasses.replace(
        candidate(profile=profile, rank=rank),
        account_ref=account_reference(f"claude:{account}"),
    )


def batch_request(task_id: str, candidates: tuple):
    facts = task_facts(task_id=task_id, classifications={"risk": "low"})
    return dataclasses.replace(make_request(task=facts, candidates=candidates), free_slots=2)


def valid_recovery_case(**changes: object) -> RecoveryCase:
    base = RecoveryCase(
        run_id="run-adversarial",
        plan_id="plan-adversarial",
        revision=1,
        plan_sha256=PLAN_SHA,
        task_id="T-adversarial",
        attempt_id="A-adversarial",
        token=1,
        core_cause="execution_failed",
        technical_cause="connection_lost",
        confidence="confirmed",
        evidence_refs=("ledger:" + "c" * 64,),
        handoff_sha="d" * 64,
        execution_state="failed",
        current=True,
        identity_verified=True,
        transient_confirmed=True,
        max_attempts=3,
        failure_at=NOW - 10,
        now=NOW,
    )
    return dataclasses.replace(base, **changes)


class AdversarialQuotaMatrixTests(unittest.TestCase):
    def test_auth_unknown_missing_window_elapsed_reset_and_weekly_exhaustion_never_route(self):
        cases = (
            ("auth_error", quota_observations(source_status="auth_error"), "unknown"),
            ("missing_weekly", quota_observations(windows={
                "five_hour": {"used_percent": 25, "resets_at": NOW + 300, "window_minutes": 300},
            }), "unknown"),
            ("elapsed_reset", quota_observations(windows={
                "five_hour": {"used_percent": 25, "resets_at": NOW - 1, "window_minutes": 300},
                "seven_day": {"used_percent": 35, "resets_at": NOW + 86_400, "window_minutes": 10_080},
            }), "unknown"),
            ("expired_observation", quota_observations(observed_at=NOW - 7200), "not_available"),
            ("exhausted_weekly_near_short_reset", quota_observations(windows={
                "five_hour": {"used_percent": 70, "resets_at": NOW + 1, "window_minutes": 300},
                "seven_day": {"used_percent": 100, "resets_at": NOW + 86_400, "window_minutes": 10_080},
            }), "exhausted"),
        )

        for name, observations, expected_state in cases:
            with self.subTest(case=name):
                result = assess_batch_quota(
                    (quota_requirement(1), quota_requirement(2)),
                    observations,
                    now=NOW,
                )
                self.assertEqual(result.unique_account_count, 1)
                self.assertEqual(result.eligible_route_ids, ())
                self.assertEqual(len(result.routes), 2)
                if expected_state == "not_available":
                    self.assertTrue(all(row.assessment.state in ("stale", "unknown") for row in result.routes))
                else:
                    self.assertEqual({row.assessment.state for row in result.routes}, {expected_state})
                self.assertEqual(result.routes[0].assessment, result.routes[1].assessment)

    def test_aliases_cannot_overbook_account_and_replay_is_order_independent(self):
        shared = "shared-account"
        alternate = "alternate-account"
        flexible = batch_request(
            "T-flexible",
            (route_candidate("alias-a", shared), route_candidate("alternate", alternate, rank=1)),
        )
        constrained = batch_request("T-constrained", (route_candidate("alias-b", shared),))
        limits = (
            AccountConcurrency(account_reference(f"claude:{shared}"), active_assignments=0, max_concurrent=1),
            AccountConcurrency(account_reference(f"claude:{alternate}"), active_assignments=0, max_concurrent=1),
        )

        result = plan_ready_batch((flexible, constrained), account_concurrency=limits)
        replay = plan_ready_batch((constrained, flexible), account_concurrency=limits)

        self.assertEqual(result, replay)
        by_task = {row.task_id: row for row in result.assignments}
        self.assertEqual(set(by_task), {"T-flexible", "T-constrained"})
        self.assertEqual(by_task["T-flexible"].account_ref, account_reference(f"claude:{alternate}"))
        self.assertEqual(by_task["T-constrained"].account_ref, account_reference(f"claude:{shared}"))
        self.assertEqual(sum(row.account_ref == account_reference(f"claude:{shared}")
                             for row in result.assignments), 1)


class AdversarialQuotaAttributionTests(unittest.TestCase):
    def _observation(self, used: float, observed_at: float, reset_at: float, *, now: float = NOW):
        return quota_observations(windows={
            "five_hour": {"used_percent": used, "resets_at": reset_at, "window_minutes": 300},
            "seven_day": {"used_percent": 35, "resets_at": NOW + 86_400, "window_minutes": 10_080},
        }, observed_at=observed_at, now=now)[0]

    def test_external_or_parallel_activity_never_becomes_task_demand(self):
        before = self._observation(20, NOW - 100, NOW + 300)
        after = self._observation(28, NOW - 20, NOW + 300)
        for active_count, external_usage in ((1, True), (1, None), (2, False), (0, False)):
            with self.subTest(active_count=active_count, external_usage=external_usage):
                estimate = attribute_quota_delta(
                    before=before,
                    after=after,
                    context_ref=CONTEXT,
                    active_task_count=active_count,
                    external_usage=external_usage,
                    now=NOW,
                )
                self.assertEqual((estimate.state, estimate.reason_code), ("unknown", "attribution_unknown"))
                self.assertIsNone(estimate.value)

    def test_crossed_reset_and_reset_identity_change_never_create_delta(self):
        cases = (
            (self._observation(20, NOW - 100, NOW + 10),
             self._observation(2, NOW + 20, NOW + 3600, now=NOW + 30), NOW + 30),
            (self._observation(20, NOW - 100, NOW + 300), self._observation(28, NOW - 20, NOW + 3600), NOW),
        )
        for before, after, now in cases:
            with self.subTest(before_reset=before.resets_at, after_reset=after.resets_at):
                estimate = attribute_quota_delta(
                    before=before,
                    after=after,
                    context_ref=CONTEXT,
                    active_task_count=1,
                    external_usage=False,
                    now=now,
                )
                self.assertEqual((estimate.state, estimate.reason_code), ("unknown", "attribution_unknown"))
                self.assertIsNone(estimate.value)


class AdversarialRetryTests(unittest.TestCase):
    def test_unknown_cause_unconfirmed_transience_unknown_reset_and_repeated_retry_block(self):
        cases = (
            ("unknown_cause", valid_recovery_case(technical_cause="unknown"), HistorySummary(), "permanent_or_unknown_cause"),
            ("unconfirmed", valid_recovery_case(transient_confirmed=False), HistorySummary(), "transience_unconfirmed"),
            ("unknown_reset", valid_recovery_case(technical_cause="quota_exhausted", reset_epoch=None),
             HistorySummary(), "quota_reset_unknown"),
            ("repeated_cause", valid_recovery_case(), HistorySummary(same_cause_attempts=2), "same_cause_limit"),
        )
        policy = Policy(max_same_cause=2)
        for name, recovery_case, history, expected_reason in cases:
            with self.subTest(case=name):
                result = propose(recovery_case, policy, history)
                self.assertEqual((result.action, result.reason_code), ("block", expected_reason))
                self.assertTrue(result.human_required)

    def test_confirmed_retry_has_one_bounded_action_then_repeated_timeout_blocks(self):
        timeout = valid_recovery_case(technical_cause="timeout")
        first = propose(timeout, Policy(base_backoff_seconds=1, max_backoff_seconds=1))
        repeated = propose(timeout, history=HistorySummary(same_cause_attempts=1))

        self.assertEqual(first.action, "retry")
        self.assertEqual(first.retry_budget_remaining, 2)
        self.assertEqual((repeated.action, repeated.reason_code), ("block", "timeout_repeated"))


if __name__ == "__main__":
    unittest.main()
