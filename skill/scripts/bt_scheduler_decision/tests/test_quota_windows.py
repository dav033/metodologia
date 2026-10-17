from __future__ import annotations

import unittest

from bt_scheduler_decision.contracts import DecisionInputError
from bt_scheduler_decision.quota import (
    QUOTA_SCHEMA_VERSION,
    QuotaObservation,
    assess_required_windows,
    normalize_cached_windows,
)

ACCOUNT = "acct:" + "a" * 64
NOW = 1_800_000_000.0
REQUIRED = {"five_hour": 300, "seven_day": 10080}


def window(used: object = 20, reset: object = NOW + 3600, minutes: int = 300) -> dict[str, object]:
    return {"used_percent": used, "resets_at": reset, "window_minutes": minutes}


def normalized(windows: object | None = None, **kwargs: object) -> tuple[QuotaObservation, ...]:
    options = dict(kwargs)
    required = options.pop("required_windows", REQUIRED)
    return normalize_cached_windows(
        account_ref=ACCOUNT, provider="claude", model="sonnet", source="subscription_cache",
        source_status="ok", windows=windows if windows is not None else {
            "five_hour": window(), "seven_day": window(35, NOW + 7200, 10080)},
        observed_at=NOW - 60, now=NOW, valid_for_seconds=7200,
        required_windows=required, **options,
    )


class QuotaWindowTests(unittest.TestCase):
    def test_observation_round_trip_keeps_version_account_window_and_provenance(self):
        observation = normalized()[0]
        self.assertEqual(observation.schema_version, QUOTA_SCHEMA_VERSION)
        self.assertEqual(observation.to_dict()["account_ref"], ACCOUNT)
        self.assertEqual(QuotaObservation.from_dict(observation.to_dict()), observation)

    def test_decoder_rejects_unknown_fields_old_versions_and_boolean_percentages(self):
        data = normalized()[0].to_dict()
        with self.assertRaises(DecisionInputError):
            QuotaObservation.from_dict({**data, "schema_version": "1.1.0"})
        with self.assertRaises(DecisionInputError):
            QuotaObservation.from_dict({**data, "unexpected": "ignored fields are unsafe"})
        with self.assertRaises(DecisionInputError):
            QuotaObservation.from_dict({**data, "used_percent": True})

    def test_fresh_cached_windows_preserve_each_window_and_bottleneck(self):
        observations = normalized()
        result = assess_required_windows(
            observations, account_ref=ACCOUNT, provider="claude", model="sonnet",
            required_windows=("five_hour", "seven_day"), now=NOW,
        )
        self.assertEqual(result.state, "available")
        self.assertEqual(result.pressure_percent, 35)
        self.assertEqual(result.checked_windows, ("five_hour", "seven_day"))

    def test_missing_required_window_remains_unknown(self):
        observations = normalized({"five_hour": window()})
        self.assertEqual(observations[1].state, "unknown")
        result = assess_required_windows(
            observations, account_ref=ACCOUNT, provider="claude", model="sonnet",
            required_windows=("five_hour", "seven_day"), now=NOW,
        )
        self.assertEqual(result.state, "unknown")
        self.assertEqual(result.unavailable_windows, ("seven_day",))

    def test_stale_and_future_observations_do_not_create_capacity(self):
        stale = normalize_cached_windows(
            account_ref=ACCOUNT, provider="claude", model="sonnet", source="subscription_cache",
            source_status="ok", windows={"five_hour": window()}, observed_at=NOW - 7200,
            now=NOW, valid_for_seconds=7200, required_windows={"five_hour": 300},
        )[0]
        future = normalize_cached_windows(
            account_ref=ACCOUNT, provider="claude", model="sonnet", source="subscription_cache",
            source_status="ok", windows={"five_hour": window()}, observed_at=NOW + 1,
            now=NOW, valid_for_seconds=7200, required_windows={"five_hour": 300},
        )[0]
        self.assertEqual(stale.state, "stale")
        self.assertEqual(future.state, "unknown")
        for observation in (stale, future):
            assessment = assess_required_windows(
                (observation,), account_ref=ACCOUNT, provider="claude", model="sonnet",
                required_windows=("five_hour",), now=NOW,
            )
            self.assertNotEqual(assessment.state, "available")

    def test_source_error_and_elapsed_reset_keep_usage_unknown(self):
        failed = normalize_cached_windows(
            account_ref=ACCOUNT, provider="codex", model="gpt-6.1-sol", source="subscription_cache",
            source_status="network_unavailable", windows={"five_hour": window()}, observed_at=NOW - 5,
            now=NOW, valid_for_seconds=7200, required_windows={"five_hour": 300},
        )[0]
        reset = normalize_cached_windows(
            account_ref=ACCOUNT, provider="codex", model="gpt-6.1-sol", source="subscription_cache",
            source_status="ok", windows={"five_hour": window(70, NOW - 1)}, observed_at=NOW - 5,
            now=NOW, valid_for_seconds=7200, required_windows={"five_hour": 300},
        )[0]
        self.assertEqual(failed.state, "unknown")
        self.assertEqual(failed.reason_code, "source_unavailable")
        self.assertEqual(reset.state, "unknown")
        self.assertEqual(reset.reason_code, "reset_elapsed")

    def test_auth_error_and_other_providers_cannot_use_claude_unknown_reset_policy(self):
        auth_error = normalize_cached_windows(
            account_ref=ACCOUNT, provider="antigravity", model="gemini-3.8-flash-low",
            source="antigravity_cache", source_status="auth_error", windows={"five_hour": window()},
            observed_at=NOW - 5, now=NOW, valid_for_seconds=7200, required_windows={"five_hour": 300},
        )[0]
        self.assertEqual(auth_error.state, "unknown")
        self.assertEqual(auth_error.reason_code, "source_unavailable")
        with self.assertRaises(DecisionInputError):
            normalize_cached_windows(
                account_ref=ACCOUNT, provider="codex", model="gpt-6.1-sol", source="subscription_cache",
                source_status="ok", windows={"five_hour": window(25, None)}, observed_at=NOW - 5,
                now=NOW, valid_for_seconds=7200, required_windows={"five_hour": 300},
                unknown_reset_windows=("five_hour",),
            )

    def test_claude_null_reset_requires_explicit_source_allowance_and_freshness(self):
        windows = {"five_hour": window(25, None)}
        refused = normalized(windows, unknown_reset_windows=())
        allowed = normalized(windows, unknown_reset_windows=("five_hour",))
        self.assertEqual(refused[0].state, "unknown")
        self.assertEqual(allowed[0].state, "available")
        self.assertEqual(allowed[0].reset_confidence, "source_allows_unknown")

    def test_exhausted_window_blocks_even_when_other_window_is_unknown(self):
        observations = normalized({
            "five_hour": window(100, NOW + 300),
            "seven_day": {"used_percent": 10, "window_minutes": 10080},
        })
        result = assess_required_windows(
            observations, account_ref=ACCOUNT, provider="claude", model="sonnet",
            required_windows=("five_hour", "seven_day"), now=NOW,
        )
        self.assertEqual(result.state, "exhausted")
        self.assertEqual(result.exhausted_windows, ("five_hour",))

    def test_duplicate_observations_and_cross_account_windows_cannot_satisfy_batch(self):
        observations = normalized()
        duplicate = (*observations, observations[0])
        result = assess_required_windows(
            duplicate, account_ref=ACCOUNT, provider="claude", model="sonnet",
            required_windows=("five_hour", "seven_day"), now=NOW,
        )
        self.assertEqual(result.state, "unknown")
        foreign = normalized()
        result = assess_required_windows(
            foreign, account_ref="acct:" + "b" * 64, provider="claude", model="sonnet",
            required_windows=("five_hour", "seven_day"), now=NOW,
        )
        self.assertEqual(result.unavailable_windows, ("five_hour", "seven_day"))
        self.assertEqual(result.reason_code, "identity_mismatch")

    def test_invalid_contract_configuration_is_rejected_at_the_boundary(self):
        with self.assertRaises(DecisionInputError):
            normalize_cached_windows(
                account_ref="raw-account-secret", provider="claude", model="sonnet",
                source="subscription_cache", source_status="ok", windows={}, observed_at=NOW,
                now=NOW, valid_for_seconds=7200, required_windows={"five_hour": 300},
            )
        with self.assertRaises(DecisionInputError):
            normalized(required_windows={"five_hour": True})
        with self.assertRaises(DecisionInputError):
            normalize_cached_windows(
                account_ref=ACCOUNT, provider="antigravity", model="gemini-3.8-flash-low",
                source="subscription_cache", source_status="ok", windows={"five_hour": window()},
                observed_at=NOW, now=NOW, valid_for_seconds=7200, required_windows={"five_hour": 300},
            )

    def test_assessment_revalidates_public_observation_instances(self):
        invalid = QuotaObservation(
            schema_version=QUOTA_SCHEMA_VERSION, account_ref=ACCOUNT, provider="codex", model="gpt-6.1-sol",
            window_id="five_hour", source="subscription_cache", state="available", observed_at=NOW - 5,
            valid_until=NOW + 90_000, resets_at=NOW + 3600, reset_confidence="reported", used_percent=20,
        )
        with self.assertRaises(DecisionInputError):
            assess_required_windows(
                (invalid,), account_ref=ACCOUNT, provider="codex", model="gpt-6.1-sol",
                required_windows=("five_hour",), now=NOW,
            )


if __name__ == "__main__":
    unittest.main()
