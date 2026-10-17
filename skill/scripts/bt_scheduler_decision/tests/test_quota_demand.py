from __future__ import annotations

import unittest

from bt_scheduler_decision.contracts import DecisionInputError
from bt_scheduler_decision.demand import (
    QUOTA_DELTA_SOURCE,
    DemandEstimate,
    DemandSample,
    attribute_quota_delta,
    estimate_demand,
    observed_token_usage,
)
from bt_scheduler_decision.quota import QuotaObservation, normalize_cached_windows

NOW = 1_800_000_000.0
ACCOUNT = "acct:" + "a" * 64
CONTEXT = "b" * 64


def quota_observation(used: float, observed_at: float, *, resets_at: float | None = NOW + 10_000,
                      valid_for: float = 7200) -> QuotaObservation:
    raw = {
        "five_hour": {"used_percent": used, "resets_at": resets_at, "window_minutes": 300},
    }
    return normalize_cached_windows(
        account_ref=ACCOUNT, provider="claude", model="sonnet", source="subscription_cache",
        source_status="ok", windows=raw, observed_at=observed_at, now=NOW,
        valid_for_seconds=valid_for, required_windows={"five_hour": 300},
        unknown_reset_windows=("five_hour",) if resets_at is None else (),
    )[0]


def token_estimate(tokens: object = 100, *, observed_at: float = NOW - 10):
    return observed_token_usage(
        provider="claude", account_ref=ACCOUNT, model="sonnet", context_ref=CONTEXT,
        source="claude-stream-json", tokens=tokens, observed_at=observed_at, now=NOW,
    )


def sample(sample_no: int, value: int, *, context_ref: str = CONTEXT, observed_at: float = NOW - 100,
           unit: str = "provider_tokens", window_id: str | None = None, source: str = "claude-stream-json",
           attribution: str = "provider_reported") -> DemandSample:
    return DemandSample(
        sample_id=f"{sample_no:064x}", provider="claude", account_ref=ACCOUNT, model="sonnet",
        window_id=window_id, context_ref=context_ref, unit=unit, value=value,
        source=source, observed_at=observed_at, attribution=attribution,
    )


class QuotaDemandTests(unittest.TestCase):
    def test_provider_reported_tokens_remain_observed_tokens(self):
        estimate = token_estimate(987)
        self.assertEqual(estimate.state, "observed")
        self.assertEqual(estimate.unit, "provider_tokens")
        self.assertEqual(estimate.value, 987)
        self.assertIsNone(estimate.valid_until)
        self.assertEqual(DemandEstimate.from_dict(estimate.to_dict()), estimate)
        with self.assertRaises(DecisionInputError):
            DemandEstimate.from_dict({**estimate.to_dict(), "schema_version": "1.1.0"})

    def test_missing_or_invalid_token_usage_stays_unknown(self):
        missing = token_estimate(None)
        invalid = token_estimate(True)
        self.assertEqual(missing.reason_code, "provider_usage_missing")
        self.assertEqual(invalid.reason_code, "invalid_provider_usage")
        self.assertIsNone(missing.value)
        self.assertIsNone(invalid.value)

    def test_clean_single_task_quota_delta_is_observed_percentage_points(self):
        result = attribute_quota_delta(
            before=quota_observation(25, NOW - 100), after=quota_observation(39.5, NOW - 20),
            context_ref=CONTEXT, active_task_count=1, external_usage=False, now=NOW,
        )
        self.assertEqual(result.state, "observed")
        self.assertEqual(result.unit, "quota_percentage_points")
        self.assertEqual(result.value, 14.5)
        self.assertEqual(result.source, QUOTA_DELTA_SOURCE)
        sample_value = DemandSample.from_estimate("a" * 64, result)
        self.assertEqual(sample_value.attribution, "account_window_attributed")
        estimate = estimate_demand(
            (sample_value,), provider="claude", account_ref=ACCOUNT, model="sonnet", window_id="five_hour",
            context_ref=CONTEXT, unit="quota_percentage_points", source=QUOTA_DELTA_SOURCE,
            now=NOW, valid_for_seconds=1800,
        )
        self.assertEqual(estimate.value, 14.5)

    def test_parallel_execution_external_noise_and_missing_noise_evidence_are_unattributed(self):
        for active_count, external_usage in ((2, False), (1, True), (1, None), (0, False)):
            with self.subTest(active_count=active_count, external_usage=external_usage):
                result = attribute_quota_delta(
                    before=quota_observation(25, NOW - 100), after=quota_observation(39, NOW - 20),
                    context_ref=CONTEXT, active_task_count=active_count,
                    external_usage=external_usage, now=NOW,
                )
                self.assertEqual(result.state, "unknown")
                self.assertEqual(result.reason_code, "attribution_unknown")
                self.assertIsNone(result.value)

    def test_reset_change_unknown_reset_and_counter_decrease_are_unattributed(self):
        reset_crossed_before = QuotaObservation(
            schema_version="1.2.0", account_ref=ACCOUNT, provider="claude", model="sonnet",
            window_id="five_hour", source="subscription_cache", state="available",
            observed_at=NOW - 1000, valid_until=NOW + 3000, resets_at=NOW + 10,
            reset_confidence="reported", used_percent=25, reason_code=None,
        )
        reset_crossed_after = QuotaObservation(
            schema_version="1.2.0", account_ref=ACCOUNT, provider="claude", model="sonnet",
            window_id="five_hour", source="subscription_cache", state="available",
            observed_at=NOW + 20, valid_until=NOW + 5000, resets_at=NOW + 3600,
            reset_confidence="reported", used_percent=4, reason_code=None,
        )
        cases = (
            (reset_crossed_before, reset_crossed_after),
            (quota_observation(25, NOW - 100, resets_at=NOW + 9000),
             quota_observation(39, NOW - 20, resets_at=NOW + 8000)),
            (quota_observation(25, NOW - 100, resets_at=None), quota_observation(39, NOW - 20, resets_at=None)),
            (quota_observation(39, NOW - 100), quota_observation(25, NOW - 20)),
        )
        for before, after in cases:
            with self.subTest(before=before.resets_at, after=after.resets_at):
                result = attribute_quota_delta(
                    before=before, after=after, context_ref=CONTEXT,
                    active_task_count=1, external_usage=False,
                    now=NOW + 30 if before is reset_crossed_before else NOW,
                )
                self.assertEqual(result.state, "unknown")
                self.assertEqual(result.reason_code, "attribution_unknown")

    def test_stale_unknown_and_incomparable_windows_never_create_deltas(self):
        stale = quota_observation(20, NOW - 100, valid_for=30)
        fresh = quota_observation(25, NOW - 20)
        stale_result = attribute_quota_delta(
            before=stale, after=fresh, context_ref=CONTEXT,
            active_task_count=1, external_usage=False, now=NOW,
        )
        mismatch = attribute_quota_delta(
            before=quota_observation(20, NOW - 100),
            after=normalize_cached_windows(
                account_ref=ACCOUNT, provider="claude", model="opus", source="subscription_cache",
                source_status="ok", windows={"five_hour": {"used_percent": 30, "resets_at": NOW + 10_000,
                                                               "window_minutes": 300}},
                observed_at=NOW - 20, now=NOW, valid_for_seconds=7200,
                required_windows={"five_hour": 300},
            )[0],
            context_ref=CONTEXT, active_task_count=1, external_usage=False, now=NOW,
        )
        self.assertEqual(stale_result.state, "unknown")
        self.assertEqual(stale_result.reason_code, "stale_observation")
        self.assertEqual(mismatch.reason_code, "identity_mismatch")

    def test_estimate_uses_only_exact_context_and_reports_empirical_range_and_ttl(self):
        samples = (sample(1, 100), sample(2, 200), sample(3, 300),
                   sample(4, 999, context_ref="c" * 64))
        result = estimate_demand(
            samples, provider="claude", account_ref=ACCOUNT, model="sonnet", window_id=None,
            context_ref=CONTEXT, unit="provider_tokens", source="claude-stream-json",
            now=NOW, valid_for_seconds=3600,
        )
        self.assertEqual(result.state, "estimated")
        self.assertEqual(result.value, 200)
        self.assertEqual((result.lower_bound, result.upper_bound), (100, 300))
        self.assertEqual(result.sample_count, 3)
        self.assertEqual(result.valid_until, NOW + 3600)
        observation = DemandSample.from_estimate("f" * 64, token_estimate(220))
        self.assertEqual(DemandSample.from_dict(observation.to_dict()), observation)

    def test_token_and_percentage_samples_are_never_combined(self):
        percentage = sample(
            5, 12, unit="quota_percentage_points", window_id="five_hour",
            source=QUOTA_DELTA_SOURCE, attribution="account_window_attributed",
        )
        result = estimate_demand(
            (percentage,), provider="claude", account_ref=ACCOUNT, model="sonnet", window_id=None,
            context_ref=CONTEXT, unit="provider_tokens", source="claude-stream-json",
            now=NOW, valid_for_seconds=60,
        )
        self.assertEqual(result.state, "unknown")
        self.assertEqual(result.reason_code, "no_comparable_samples")
        self.assertIsNone(result.value)

    def test_only_observed_estimates_can_become_training_samples(self):
        observed = DemandSample.from_estimate("d" * 64, token_estimate(40))
        self.assertEqual(observed.attribution, "provider_reported")
        unknown = observed_token_usage(
            provider="claude", account_ref=ACCOUNT, model="sonnet", context_ref=CONTEXT,
            source="claude-stream-json", tokens=None, observed_at=NOW - 10, now=NOW,
        )
        with self.assertRaises(DecisionInputError):
            DemandSample.from_estimate("e" * 64, unknown)

    def test_duplicate_ids_future_stale_and_invalid_ttl_are_handled_conservatively(self):
        duplicated = sample(1, 100)
        with self.assertRaises(DecisionInputError):
            estimate_demand(
                (duplicated, duplicated), provider="claude", account_ref=ACCOUNT, model="sonnet", window_id=None,
                context_ref=CONTEXT, unit="provider_tokens", source="claude-stream-json",
                now=NOW, valid_for_seconds=3600,
            )
        future = estimate_demand(
            (sample(2, 100, observed_at=NOW + 1),), provider="claude", account_ref=ACCOUNT,
            model="sonnet", window_id=None, context_ref=CONTEXT, unit="provider_tokens",
            source="claude-stream-json", now=NOW, valid_for_seconds=3600,
        )
        stale = estimate_demand(
            (sample(3, 100, observed_at=NOW - 31_536_001),), provider="claude", account_ref=ACCOUNT,
            model="sonnet", window_id=None, context_ref=CONTEXT, unit="provider_tokens",
            source="claude-stream-json", now=NOW, valid_for_seconds=3600,
        )
        self.assertEqual(future.reason_code, "future_sample")
        self.assertEqual(stale.reason_code, "stale_samples")
        with self.assertRaises(DecisionInputError):
            estimate_demand(
                (sample(4, 100),), provider="claude", account_ref=ACCOUNT, model="sonnet", window_id=None,
                context_ref=CONTEXT, unit="provider_tokens", source="claude-stream-json",
                now=NOW, valid_for_seconds=86_401,
            )
        too_many = tuple(sample(index + 10, 100) for index in range(1001))
        with self.assertRaises(DecisionInputError):
            estimate_demand(
                too_many, provider="claude", account_ref=ACCOUNT, model="sonnet", window_id=None,
                context_ref=CONTEXT, unit="provider_tokens", source="claude-stream-json",
                now=NOW, valid_for_seconds=60,
            )


if __name__ == "__main__":
    unittest.main()
