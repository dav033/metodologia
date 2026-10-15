from __future__ import annotations

import unittest

import bt_scheduler_bench_quality as quality
from bt_scheduler_decision.bench_local import route_regret, summarize_regrets
from bt_scheduler_laya import CHECKPOINTS


class CalibrationFreezeTests(unittest.TestCase):
    def _fixtures(self):
        ids = [f"calibration-{index:03d}" for index in range(100)]
        manifest = {
            "dataset_sha256": "a" * 64,
            "dataset_version": "scheduler-m2-synthetic-choice-v1",
            "calibration_case_ids": ids,
            "label_protocol": "synthetic independent utility oracle",
            "labeler_independence": "algorithmic synthetic labels; not human adjudication",
        }
        runs = []
        for name, correct in (("english", 24), ("multilingual", 27), ("typed-decisions", 30)):
            revision = CHECKPOINTS[name][1]
            digest = CHECKPOINTS[name][2]
            cases = [{
                "case_id": case_id,
                "predicted_route_id": f"r-{index}",
                "answer_confidence": 0.5,
                "matches_oracle": index < correct,
                "baseline_matches_oracle": index < 25,
                "matches_baseline": False,
                "eligible_choice": True,
                "inference_ms": 20.0,
            } for index, case_id in enumerate(ids)]
            runs.append({"checkpoint": name, "checkpoint_revision": revision, "checkpoint_sha256": digest,
                         "requested_device": "cuda", "cases": cases})
        results = {"dataset_sha256": manifest["dataset_sha256"], "dataset_version": manifest["dataset_version"],
                   "split": "calibration", "held_out_touched": False, "results": runs}
        return results, manifest

    def test_calibration_freezes_highest_raw_diagnostic_checkpoint_without_enabling_laya(self):
        results, manifest = self._fixtures()
        decision = quality.build_calibration_decision(results, source_sha256="b" * 64, manifest=manifest)

        self.assertEqual(decision["checkpoint"], "typed-decisions")
        self.assertEqual(decision["device"], "cuda")
        self.assertFalse(decision["held_out_touched"])
        self.assertFalse(decision["gate_enabled"])
        self.assertIsNone(decision["confidence_cutoff"])
        self.assertEqual(decision["gate_reason"], "no_checkpoint_cleared_calibrated_wilson_gate")

    def test_high_confidence_laya_choice_is_rejected_for_an_easy_task(self):
        classifications = {"complexity": "low", "scope": "isolated_fix", "estimated_minutes": 15,
                           "risk": "low", "coupling": "low", "confidence": "high"}
        ambiguous = quality.decision_facts_are_ambiguous(classifications, evidence_complete=True,
                                                         dependency_count=0, has_shared_resources=False)

        accepted = quality.laya_choice_passes_runtime_gate(
            quality_authorized=True, task_ambiguous=ambiguous, candidate_eligible=True,
            answer_confidence=0.99, cutoff=0.8)

        self.assertFalse(ambiguous)
        self.assertFalse(accepted)

    def test_laya_choice_gate_uses_the_same_ambiguity_and_confidence_thresholds(self):
        classifications = {"complexity": "medium", "scope": "small_change", "estimated_minutes": 60,
                           "risk": "low", "coupling": "low", "confidence": "high"}
        ambiguous = quality.decision_facts_are_ambiguous(classifications, evidence_complete=True,
                                                         dependency_count=0, has_shared_resources=False)

        self.assertTrue(quality.laya_choice_passes_runtime_gate(
            quality_authorized=True, task_ambiguous=ambiguous, candidate_eligible=True,
            answer_confidence=0.8, cutoff=0.8))
        self.assertFalse(quality.laya_choice_passes_runtime_gate(
            quality_authorized=True, task_ambiguous=ambiguous, candidate_eligible=True,
            answer_confidence=0.79, cutoff=0.8))

    def test_regret_is_oracle_utility_minus_selected_utility(self):
        utilities = {"best": 10.0, "selected": 7.5, "worse": 2.0}
        self.assertEqual(route_regret(utilities, "selected"), 2.5)
        self.assertIsNone(route_regret(utilities, None))
        rows = [{"laya_regret": 2.5, "baseline_regret": 0.0},
                {"laya_regret": 0.5, "baseline_regret": 1.0}]
        summary = summarize_regrets(rows, {"laya": "laya_regret", "baseline": "baseline_regret"})
        self.assertEqual(summary["laya"]["mean"], 1.5)
        self.assertEqual(summary["baseline"]["median"], 0.5)

    def test_calibration_refuses_wrong_split_or_checkpoint_revision(self):
        results, manifest = self._fixtures()
        results["split"] = "held_out"
        with self.assertRaisesRegex(quality.BenchmarkError, "calibration split"):
            quality.build_calibration_decision(results, source_sha256="b" * 64, manifest=manifest)
        results, manifest = self._fixtures()
        results["results"][0]["checkpoint_revision"] = "wrong"
        with self.assertRaisesRegex(quality.BenchmarkError, "revision or digest"):
            quality.build_calibration_decision(results, source_sha256="b" * 64, manifest=manifest)


if __name__ == "__main__":
    unittest.main()
