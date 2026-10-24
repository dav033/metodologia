"""Contract checks for the D-10 benchmark's real-core measurement path."""
from __future__ import annotations

import unittest

import bt_engine_benchmark as benchmark


class EngineBenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = benchmark.run_engine_benchmark()

    def test_clean_legacy_parity_is_measured_from_m1(self):
        old = self.report["scenarios"]["legacy"]["clean"]
        new = self.report["scenarios"]["subplans"]["clean"]
        self.assertTrue(old["accepted"])
        self.assertTrue(new["accepted"])
        self.assertEqual((old["attempts"], old["simulated_wall_seconds"]),
                         (new["attempts"], new["simulated_wall_seconds"]))
        self.assertEqual((old["redone_tasks"], new["redone_tasks"]), (0, 0))

    def test_first_exposure_comes_from_fixture_barriers_and_dependency_graph(self):
        old = self.report["scenarios"]["legacy"]
        new = self.report["scenarios"]["subplans"]
        self.assertEqual(set(old["derived_barriers"].values()), {"T24"})
        self.assertEqual(new["derived_barriers"], {"F1": "T7", "F2": "T7", "F3": "T7",
                                                   "F4": "T14", "F5": "T14"})
        self.assertEqual(new["derived_barriers"], new["with_defects"]["first_exposure"])

    def test_defects_execute_rework_and_locality_against_actual_acceptances(self):
        old = self.report["scenarios"]["legacy"]["with_defects"]
        new = self.report["scenarios"]["subplans"]["with_defects"]
        self.assertTrue(old["accepted"])
        self.assertTrue(new["accepted"])
        self.assertGreater(old["attempts"], 24)
        self.assertGreater(new["attempts"], 24)
        self.assertGreater(old["rework_transitions"], 0)
        self.assertGreater(new["rework_transitions"], 0)
        self.assertEqual(old["redone_tasks"], 24)
        self.assertLess(new["redone_tasks"], old["redone_tasks"])
        self.assertLess(new["accepted_estimated_minutes_discarded"], old["accepted_estimated_minutes_discarded"])
        self.assertEqual(new["token_proxy"]["fixed_proxy_tokens_per_attempt_minute"],
                         old["token_proxy"]["fixed_proxy_tokens_per_attempt_minute"])

    def test_token_proxy_never_claims_observed_provider_usage(self):
        for group in self.report["scenarios"].values():
            for name in ("clean", "with_defects"):
                proxy = group[name]["token_proxy"]
                self.assertIn("no provider tokens observed", proxy["label"])
                self.assertEqual(proxy["value"], group[name]["attempt_minutes"] *
                                 benchmark.TOKEN_PROXY_PER_ATTEMPT_MINUTE)

    def test_replay_is_deterministic(self):
        self.assertEqual(self.report, benchmark.run_engine_benchmark())


if __name__ == "__main__":
    unittest.main()
