from __future__ import annotations

import unittest

from bt_scheduler_decision import RouteHistory, assess_history
from bt_scheduler_decision.tests.support import candidate, request


def assessment(history: RouteHistory):
    route = candidate(history=history)
    return assess_history(request(candidates=(route,)), route.route_id)


class HistoryAssessmentTests(unittest.TestCase):
    def test_missing_history_stays_unknown_and_is_not_zero_success(self):
        score = assessment(RouteHistory())
        self.assertIsNone(score.verified_rate)
        self.assertIsNone(score.shrunk_verified_score)
        self.assertEqual(score.sample_weight, 0.0)
        self.assertIn("history_no_verified_samples", score.factor_codes)

    def test_sparse_successes_are_shrunk_and_claimed_attempts_are_not_successes(self):
        score = assessment(RouteHistory("sparse", verified_successes=1, claimed_unverified=9))
        self.assertEqual(score.verified_rate, 1.0)
        self.assertEqual(score.shrunk_verified_score, 0.6)
        self.assertEqual(score.sample_weight, 0.2)
        self.assertIn("history_sparse", score.factor_codes)

    def test_observed_history_keeps_duration_and_token_coverage_separate(self):
        score = assessment(RouteHistory(
            "observed", verified_successes=4, verified_failures=1,
            duration_samples=5, median_duration_seconds=42.0,
        ))
        self.assertEqual(score.verified_rate, 0.8)
        self.assertEqual(score.shrunk_verified_score, 2 / 3)
        self.assertEqual(score.median_duration_seconds, 42.0)
        self.assertEqual(score.token_samples, 0)
        self.assertIsNone(score.median_total_tokens)
        self.assertIn("duration_measured", score.factor_codes)
        self.assertNotIn("tokens_measured", score.factor_codes)

    def test_estimated_history_source_remains_tagged_and_never_becomes_verified_outcomes(self):
        score = assessment(RouteHistory("estimated", duration_samples=1, median_duration_seconds=90.0,
                                        token_samples=1, median_total_tokens=800))
        self.assertEqual(score.source_quality, "estimated")
        self.assertIsNone(score.verified_rate)
        self.assertIsNone(score.shrunk_verified_score)
        self.assertEqual(score.median_duration_seconds, 90.0)
        self.assertEqual(score.median_total_tokens, 800)


if __name__ == "__main__":
    unittest.main()
