from __future__ import annotations

import dataclasses
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from bt_scheduler_decision import (
    ChooserFailure,
    DecisionEngine,
    DecisionLedger,
    LayaChoice,
    QualityGate,
)
from bt_scheduler_decision.quality_evidence import QualityEvidenceError
from bt_scheduler_decision.tests.support import (
    candidate,
    request,
    synthetic_quality_artifacts,
    task_facts,
)


class FixedChooser:
    def __init__(self, result=None, failure=None):
        self.result = result
        self.failure = failure
        self.calls = 0

    def choose(self, request, candidates):
        self.calls += 1
        if self.failure:
            raise self.failure
        return self.result


class AuthorizedTestGate:
    enabled = True
    answer_confidence_cutoff = 0.8
    calibration_version = "test-only"

    def __init__(self, checkpoint_revision):
        self.checkpoint_revision = checkpoint_revision

    def authorizes(self, checkpoint_revision):
        return checkpoint_revision == self.checkpoint_revision


class DecisionEngineTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.ledger = DecisionLedger(Path(self.temporary.name) / "m2.sqlite3")
        self.routes = (
            candidate(profile="baseline", rank=0),
            candidate(provider="codex", model="sol", profile="alternative", rank=1),
        )
        self.request = request(candidates=self.routes)

    def tearDown(self):
        self.temporary.cleanup()

    def approved_gate(self):
        return AuthorizedTestGate("revision-a")

    def test_easy_task_skips_inference_even_when_gate_is_enabled(self):
        simple = dataclasses.replace(
            task_facts(classifications={"complexity": "low", "scope": "isolated_fix", "risk": "low",
                                       "coupling": "low", "confidence": "high"}),
            dependencies=(), shared_resources=(), expected_paths=(),
        )
        request_value = dataclasses.replace(self.request, task=simple, checkpoint_revision="revision-a")
        chooser = FixedChooser(LayaChoice(self.routes[1].route_id, 0.99, "revision-a"))
        engine = DecisionEngine(self.ledger, chooser=chooser,
                                 quality_gate=self.approved_gate())

        result = engine.decide(request_value)

        self.assertEqual(chooser.calls, 0)
        self.assertEqual(result.method, "deterministic")
        self.assertEqual(result.selected.route_id, self.routes[0].route_id)
        self.assertIn("task_unambiguous", result.factor_codes)

    def test_ambiguous_task_accepts_only_eligible_choice_above_calibrated_cutoff(self):
        request_value = dataclasses.replace(self.request, checkpoint_revision="revision-a")
        chooser = FixedChooser(LayaChoice(self.routes[1].route_id, 0.82, "revision-a"))
        engine = DecisionEngine(self.ledger, chooser=chooser,
                                 quality_gate=self.approved_gate())

        result = engine.decide(request_value)

        self.assertEqual(result.method, "laya")
        self.assertEqual(result.selected.route_id, self.routes[1].route_id)
        self.assertEqual(result.confidence.accepted_cutoff, 0.8)
        self.assertEqual(result.confidence.semantics, "laya_calibrated_choice_score")
        self.assertEqual(chooser.calls, 1)

    def test_low_confidence_uses_the_deterministic_reference(self):
        request_value = dataclasses.replace(self.request, checkpoint_revision="revision-a")
        chooser = FixedChooser(LayaChoice(self.routes[1].route_id, 0.79, "revision-a"))
        engine = DecisionEngine(self.ledger, chooser=chooser,
                                 quality_gate=self.approved_gate())

        result = engine.decide(request_value)

        self.assertEqual(result.method, "deterministic_fallback")
        self.assertEqual(result.fallback_reason, "laya_low_confidence")
        self.assertEqual(result.selected.route_id, self.routes[0].route_id)

    def test_timeout_failure_falls_back_without_persisting_exception_text(self):
        request_value = dataclasses.replace(self.request, checkpoint_revision="revision-a")
        chooser = FixedChooser(failure=ChooserFailure("laya_timeout"))
        engine = DecisionEngine(self.ledger, chooser=chooser,
                                 quality_gate=self.approved_gate())

        result = engine.decide(request_value)

        self.assertEqual(result.method, "deterministic_fallback")
        self.assertEqual(result.fallback_reason, "laya_timeout")
        self.assertNotIn("timeout", result.rationale)
        self.assertEqual(self.ledger.lookup(request_value), result)

    def test_choice_outside_eligible_set_is_rejected(self):
        request_value = dataclasses.replace(self.request, checkpoint_revision="revision-a")
        invalid = "f" * 64
        chooser = FixedChooser(LayaChoice(invalid, 0.99, "revision-a"))
        engine = DecisionEngine(self.ledger, chooser=chooser,
                                 quality_gate=self.approved_gate())

        result = engine.decide(request_value)

        self.assertEqual(result.fallback_reason, "laya_invalid_output")
        self.assertEqual(result.selected.route_id, self.routes[0].route_id)

    def test_quality_gate_disabled_never_calls_chooser(self):
        chooser = FixedChooser()
        engine = DecisionEngine(self.ledger, chooser=chooser, quality_gate=QualityGate())

        result = engine.decide(self.request)

        self.assertEqual(chooser.calls, 0)
        self.assertEqual(result.method, "deterministic_fallback")
        self.assertEqual(result.fallback_reason, "laya_quality_gate_disabled")

    def test_gate_cannot_be_enabled_without_verified_calibration_and_heldout_artifacts(self):
        with self.assertRaises(TypeError):
            QualityGate(True, 0.8, "unverified")
        artifacts = synthetic_quality_artifacts(self.temporary.name, "revision-a")
        _, _, held_out, _, _ = artifacts
        report = json.loads(held_out.read_text(encoding="utf-8"))
        report["laya_gate_authorized"] = False
        held_out.write_text(json.dumps(report), encoding="utf-8")
        with self.assertRaises(QualityEvidenceError):
            QualityGate.from_artifacts(*artifacts)

    def test_quality_gate_rejects_incomplete_held_out_sample(self):
        artifacts = synthetic_quality_artifacts(self.temporary.name, "revision-a")
        held_out = artifacts[2]
        report = json.loads(held_out.read_text(encoding="utf-8"))
        report["cases"] = report["cases"][:50]
        report["summary"]["cases"] = 50
        report["summary"]["valid_choices"] = 50
        held_out.write_text(json.dumps(report), encoding="utf-8")
        with self.assertRaisesRegex(QualityEvidenceError, "full frozen sample"):
            QualityGate.from_artifacts(*artifacts)

    def test_quality_gate_rejects_calibration_with_malformed_checkpoint_gate(self):
        artifacts = synthetic_quality_artifacts(self.temporary.name, "revision-a")
        calibration = artifacts[0]
        report = json.loads(calibration.read_text(encoding="utf-8"))
        report["checkpoint_results"][0]["confidence_gate"] = None
        calibration.write_text(json.dumps(report), encoding="utf-8")
        with self.assertRaises(QualityEvidenceError):
            QualityGate.from_artifacts(*artifacts)

    def test_quality_gate_rejects_incomplete_frozen_family_strata(self):
        artifacts = synthetic_quality_artifacts(self.temporary.name, "revision-a")
        manifest = artifacts[4]
        report = json.loads(manifest.read_text(encoding="utf-8"))
        report["family_minimum_counts_per_split"]["held_out"]["history"] = 19
        manifest.write_text(json.dumps(report), encoding="utf-8")
        with self.assertRaisesRegex(QualityEvidenceError, "does not match its manifest"):
            QualityGate.from_artifacts(*artifacts)

    def test_quality_gate_rejects_a_fabricated_or_modified_canonical_corpus(self):
        artifacts = synthetic_quality_artifacts(self.temporary.name, "revision-a")
        corpus = artifacts[3]
        corpus.write_bytes(corpus.read_bytes().replace(b'"family": "history"', b'"family": {}', 1))
        manifest = artifacts[4]
        report = json.loads(manifest.read_text(encoding="utf-8"))
        report["dataset_sha256"] = hashlib.sha256(corpus.read_bytes()).hexdigest()
        manifest.write_text(json.dumps(report), encoding="utf-8")
        with self.assertRaisesRegex(QualityEvidenceError, "does not match its manifest"):
            QualityGate.from_artifacts(*artifacts)

    def test_quality_gate_recalculates_the_held_out_paired_bootstrap(self):
        artifacts = synthetic_quality_artifacts(self.temporary.name, "revision-a")
        held_out = artifacts[2]
        report = json.loads(held_out.read_text(encoding="utf-8"))
        report["summary"]["production_hybrid_paired_delta_95ci"] = [0.01, 0.5]
        held_out.write_text(json.dumps(report), encoding="utf-8")
        with self.assertRaisesRegex(QualityEvidenceError, "recalculated held-out"):
            QualityGate.from_artifacts(*artifacts)

    def test_gate_is_bound_to_the_checkpoint_revision_in_its_artifacts(self):
        chooser = FixedChooser(LayaChoice(self.routes[1].route_id, 0.99, "revision-a"))
        request_value = dataclasses.replace(self.request, checkpoint_revision="revision-b")
        engine = DecisionEngine(self.ledger, chooser=chooser, quality_gate=self.approved_gate())

        result = engine.decide(request_value)

        self.assertEqual(chooser.calls, 0)
        self.assertEqual(result.method, "deterministic_fallback")
        self.assertEqual(result.fallback_reason, "laya_quality_gate_disabled")

    def test_synthetic_benchmark_artifacts_cannot_authorize_production_laya(self):
        artifacts = synthetic_quality_artifacts(self.temporary.name, "revision-a")

        with self.assertRaisesRegex(QualityEvidenceError, "not explicitly approved"):
            QualityGate.from_artifacts(*artifacts)

    def test_exact_replay_does_not_call_chooser_again(self):
        request_value = dataclasses.replace(self.request, checkpoint_revision="revision-a")
        chooser = FixedChooser(LayaChoice(self.routes[1].route_id, 0.82, "revision-a"))
        engine = DecisionEngine(self.ledger, chooser=chooser,
                                 quality_gate=self.approved_gate())

        first = engine.decide(request_value)
        second = engine.decide(request_value)

        self.assertEqual(second, first)
        self.assertEqual(chooser.calls, 1)


if __name__ == "__main__":
    unittest.main()
