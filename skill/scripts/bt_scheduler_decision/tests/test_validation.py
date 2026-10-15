from __future__ import annotations

import dataclasses
import unittest

from bt_scheduler_decision import (
    Confidence,
    DecisionInputError,
    RouteHistory,
    TaskFacts,
    validate_request,
)
from bt_scheduler_decision.tests.support import candidate, request, task_facts


class RequestValidation(unittest.TestCase):
    def test_confidence_semantics_are_a_bounded_choice_measure_not_task_success_probability(self):
        accepted = Confidence(0.9, "laya_answer_confidence", "laya_calibrated_choice_score", "cal-v1", 0.8)
        self.assertEqual(accepted.semantics, "laya_calibrated_choice_score")
        with self.assertRaises(ValueError):
            Confidence(0.9, "laya_answer_confidence", "real_task_success_probability", "cal-v1", 0.8)
        with self.assertRaises(ValueError):
            Confidence(0.7, "laya_answer_confidence", "laya_calibrated_choice_score", "cal-v1", 0.8)
        with self.assertRaises(ValueError):
            Confidence(0.5, "deterministic_policy_margin", "real_task_success_probability")

    def test_valid_request_is_sorted_frozen_and_content_addressed(self):
        slower = candidate(provider="codex", model="sol", profile="team", rank=1)
        first = candidate()
        validated = validate_request(request(candidates=(slower, first)))
        self.assertEqual([item.route_id for item in validated.request.candidates],
                         sorted((slower.route_id, first.route_id)))
        self.assertEqual(len(validated.task_input_sha256), 64)
        self.assertEqual(len(validated.candidate_snapshot_sha256), 64)
        self.assertEqual(len(validated.quota_snapshot_sha256), 64)
        with self.assertRaises(TypeError):
            validated.request.task.classifications["risk"] = "high"

    def test_optional_classification_errors_become_unknown_with_stable_warnings(self):
        facts = task_facts(classifications={"risk": "critical", "unexpected": "value"}, evidence={})
        validated = validate_request(request(task=facts))
        self.assertIsNone(validated.request.task.classifications["risk"])
        self.assertEqual(validated.request.task.classifications["complexity"], "medium")
        self.assertIn("classification_risk_invalid", validated.classification_warnings)
        self.assertIn("classification_unknown_dimension", validated.classification_warnings)
        self.assertIn("evidence_risk_missing_or_malformed", validated.classification_warnings)

    def test_evidence_content_changes_the_input_fingerprint_without_surviving_normalization(self):
        one = task_facts()
        evidence = {name: dict(entry) for name, entry in one.classification_evidence.items()}
        evidence["risk"]["justification"] = "Inspected another independently verified risk factor here."
        two = dataclasses.replace(one, classification_evidence=evidence)
        a, b = validate_request(request(task=one)), validate_request(request(task=two))
        self.assertNotEqual(a.task_input_sha256, b.task_input_sha256)
        self.assertNotIn("Inspected concrete", repr(a.request.task.classification_evidence))
        self.assertEqual(a.request.task.classification_evidence["risk"]["reference_kinds"], ("spec",))

    def test_task_identity_brief_acceptance_and_verification_change_the_fingerprint(self):
        original = task_facts()
        changed = dataclasses.replace(original, task_id="T2", brief="Inspect another task safely.")
        changed_acceptance = dataclasses.replace(original, acceptance_criteria=("Different acceptance evidence exists.",))
        hashes = {validate_request(request(task=facts)).task_input_sha256
                  for facts in (original, changed, changed_acceptance)}
        self.assertEqual(len(hashes), 3)

    def test_missing_or_bad_classifications_are_conservative_not_fatal(self):
        facts = TaskFacts("T1", "", "not-an-object", "also-invalid")
        result = validate_request(request(task=facts))
        self.assertTrue(all(value is None for value in result.request.task.classifications.values()))
        self.assertIn("classification_object_malformed", result.classification_warnings)
        self.assertIn("classification_evidence_malformed", result.classification_warnings)

    def test_expired_future_or_exhausted_quota_never_stays_available(self):
        expired = candidate(profile="expired", valid_until=99.0)
        future = candidate(profile="future", observed_at=101.0)
        exhausted = candidate(profile="exhausted", used_percent=100.0)
        result = validate_request(request(candidates=(expired, future, exhausted)))
        status = {item.profile: item.quota_status for item in result.request.candidates}
        self.assertEqual(status[expired.profile], "stale")
        self.assertEqual(status[future.profile], "unknown")
        self.assertEqual(status[exhausted.profile], "exhausted")

    def test_invalid_source_states_are_normalized_to_unknown(self):
        item = candidate()
        invalid = dataclasses.replace(item, source_status="available-ish", auth_status="maybe", runtime_status="maybe",
                                      quota_status="unlimited")
        result = validate_request(request(candidates=(invalid,)))
        normalized = result.request.candidates[0]
        self.assertEqual((normalized.source_status, normalized.auth_status, normalized.runtime_status,
                          normalized.quota_status), ("unknown", "unknown", "unknown", "unknown"))

    def test_unknown_source_reason_codes_are_rejected_without_echoing_values(self):
        invalid = dataclasses.replace(candidate(), source_reason_codes=("private_account_value",))
        with self.assertRaisesRegex(DecisionInputError, "source_reason_codes:invalid_code") as caught:
            validate_request(request(candidates=(invalid,)))
        self.assertNotIn("private_account_value", str(caught.exception))

    def test_empty_route_inventory_is_valid_for_a_persisted_no_candidate_result(self):
        result = validate_request(request(candidates=()))
        self.assertEqual(result.request.candidates, ())
        self.assertEqual(result.candidate_snapshot_sha256,
                         validate_request(request(candidates=())).candidate_snapshot_sha256)

    def test_bad_identity_or_oversized_brief_is_rejected_without_echoing_input(self):
        invalid = dataclasses.replace(request(), plan_sha256="secret-invalid-input")
        with self.assertRaises(DecisionInputError) as caught:
            validate_request(invalid)
        self.assertEqual(caught.exception.code, "decision_input_invalid")
        self.assertNotIn("secret-invalid-input", str(caught.exception))
        with self.assertRaises(DecisionInputError):
            validate_request(request(task=task_facts(brief="x" * 2049)))
        with self.assertRaisesRegex(DecisionInputError, "task.brief:invalid_text"):
            validate_request(request(task=task_facts(brief=" " * 2049)))

    def test_nfc_expansion_cannot_exceed_normalized_text_limits(self):
        expanding_character = "\u0344"
        with self.assertRaisesRegex(DecisionInputError, "task.brief:invalid_text"):
            validate_request(request(task=task_facts(brief=expanding_character * 1025)))
        with self.assertRaisesRegex(DecisionInputError, "checkpoint_revision:invalid_text"):
            validate_request(dataclasses.replace(request(), checkpoint_revision=expanding_character * 129))
        nested = dataclasses.replace(task_facts(), verification=({"value": expanding_character * 2049},))
        with self.assertRaisesRegex(DecisionInputError, "too_long"):
            validate_request(request(task=nested))

    def test_history_coverage_and_non_finite_values_are_rejected(self):
        bad_history = RouteHistory("unknown", verified_successes=1)
        with self.assertRaises(DecisionInputError):
            validate_request(request(candidates=(candidate(history=bad_history),)))
        with self.assertRaises(DecisionInputError):
            validate_request(dataclasses.replace(request(), requested_at=float("nan")))
        with self.assertRaises(DecisionInputError):
            validate_request(dataclasses.replace(request(), requested_at=10 ** 10000))
        with self.assertRaisesRegex(DecisionInputError, "verified_successes:invalid_count"):
            validate_request(request(candidates=(candidate(history=RouteHistory(
                "observed", verified_successes=10 ** 10000)),)))
        with self.assertRaisesRegex(DecisionInputError, "median_total_tokens:invalid"):
            validate_request(request(candidates=(candidate(history=RouteHistory(
                "observed", token_samples=1, median_total_tokens=10 ** 13)),)))

    def test_nested_verification_node_budget_is_shared_and_bounded(self):
        verification = tuple({f"field-{index}": [0] * 32 for index in range(64)} for _ in range(8))
        facts = dataclasses.replace(task_facts(), verification=verification)
        with self.assertRaisesRegex(DecisionInputError, "too_many_nodes"):
            validate_request(request(task=facts))

    def test_raw_classification_and_evidence_mappings_share_a_byte_budget(self):
        large_dimensions = {f"unknown-{index}": "x" * 4096 for index in range(64)}
        large_evidence = {f"unknown-{index}": "x" * 4096 for index in range(64)}
        for facts in (dataclasses.replace(task_facts(), classifications=large_dimensions),
                      dataclasses.replace(task_facts(), classification_evidence=large_evidence)):
            with self.assertRaisesRegex(DecisionInputError, "request:too_large"):
                validate_request(request(task=facts))

    def test_invalid_unicode_evidence_is_downgraded_and_task_text_is_rejected(self):
        base = task_facts()
        for field in ("justification", "evidence"):
            evidence = {name: dict(value) for name, value in base.classification_evidence.items()}
            if field == "justification":
                evidence["risk"][field] = "invalid-\ud800-text"
            else:
                evidence["risk"][field] = ["spec:REQ-013\ud800"]
            validated = validate_request(request(task=dataclasses.replace(base, classification_evidence=evidence)))
            self.assertIn("classification_evidence_malformed", validated.classification_warnings)
            self.assertNotIn("risk", validated.request.task.classification_evidence)
        with self.assertRaises(DecisionInputError):
            validate_request(request(task=task_facts(brief="invalid-\ud800-text")))

    def test_verification_object_keys_are_bounded_normalized_and_redacted_from_errors(self):
        secret_key = "private-verification-label"
        malformed = dataclasses.replace(task_facts(), verification=({secret_key: object()},))
        with self.assertRaises(DecisionInputError) as caught:
            validate_request(request(task=malformed))
        self.assertNotIn(secret_key, str(caught.exception))

        oversized = dataclasses.replace(task_facts(), verification=({"k" * 129: "value"},))
        with self.assertRaisesRegex(DecisionInputError, "invalid_object_key"):
            validate_request(request(task=oversized))

        colliding = dataclasses.replace(task_facts(), verification=({"é": 1, "e\u0301": 2},))
        with self.assertRaisesRegex(DecisionInputError, "duplicate_object_key"):
            validate_request(request(task=colliding))


if __name__ == "__main__":
    unittest.main()
