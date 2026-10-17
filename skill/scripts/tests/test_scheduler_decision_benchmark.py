from __future__ import annotations

import unittest

from bt_scheduler_decision_benchmark import build_report


class OfflineDecisionBenchmarkTests(unittest.TestCase):
    def test_all_methods_use_the_same_frozen_heldout_snapshot_and_report_separate_coverage(self):
        report = build_report()

        self.assertTrue(report["synthetic_diagnostic_only"])
        self.assertTrue(report["same_frozen_input_for_all_methods"])
        self.assertEqual(report["evaluation_split"], "held_out")
        self.assertEqual(report["inputs"]["case_count"], 100)
        self.assertEqual(report["inputs"]["verified_quality_history_cases"], 0)
        self.assertEqual(report["inputs"]["real_quota_window_observations"], 0)
        self.assertEqual(report["inputs"]["attributable_usage_delta_observations"], 0)

        methods = {item["method_id"]: item for item in report["methods"]}
        self.assertEqual(set(methods), {
            "fifo_first_eligible",
            "eligible_round_robin",
            "legacy_router_frozen_output",
            "m2_deterministic",
            "m2_contextual_missing_history_fallback",
        })
        snapshot_hashes = {item["input_snapshot_sha256"] for item in methods.values()}
        self.assertEqual(snapshot_hashes, {report["inputs"]["snapshot_sha256"]})
        self.assertEqual({item["eligible_candidate_count"] for item in methods.values()},
                         {report["inputs"]["eligible_candidate_count"]})

        deterministic = methods["m2_deterministic"]["metrics"]
        legacy = methods["legacy_router_frozen_output"]["metrics"]
        contextual = methods["m2_contextual_missing_history_fallback"]["metrics"]
        self.assertEqual(deterministic["selected_output_sha256"], legacy["selected_output_sha256"])
        self.assertEqual(contextual["selected_output_sha256"], deterministic["selected_output_sha256"])
        self.assertEqual(contextual["contextual_fallbacks"], {"quality_evidence_unavailable": 100})
        self.assertEqual(contextual["quality"]["verified_acceptance_coverage"], 0.0)
        self.assertEqual(contextual["quota"]["observed_account_window_coverage"], 0.0)
        self.assertEqual(contextual["attribution"]["attributed_usage_coverage"], 0.0)
        self.assertEqual(contextual["human_intervention"]["rate"], None)

    def test_selection_outputs_replay_even_though_local_timings_are_measurements(self):
        first = build_report()
        second = build_report()
        methods_first = {item["method_id"]: item for item in first["methods"]}
        methods_second = {item["method_id"]: item for item in second["methods"]}

        self.assertEqual(first["inputs"]["snapshot_sha256"], second["inputs"]["snapshot_sha256"])
        for method in methods_first:
            with self.subTest(method=method):
                self.assertEqual(methods_first[method]["metrics"]["selected_output_sha256"],
                                 methods_second[method]["metrics"]["selected_output_sha256"])
                self.assertEqual(methods_first[method]["selections"], methods_second[method]["selections"])


if __name__ == "__main__":
    unittest.main()
