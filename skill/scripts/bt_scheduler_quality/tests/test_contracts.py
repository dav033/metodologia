from __future__ import annotations

import json
import unittest
from pathlib import Path

from bt_scheduler_quality import QualityError, VerifyRequest
from bt_scheduler_quality.evidence import read_reason_code, read_result, reason_for_outcome, validate_result_contract

FIXTURES = Path(__file__).parent / "fixtures"


class VerifyRequestTests(unittest.TestCase):
    def test_parses_the_frozen_m1_order_and_hashes_canonical_input(self):
        raw = json.loads(
            (FIXTURES / "verify-order-pass.json").read_text(encoding="utf-8")
        )

        order = VerifyRequest.from_mapping(raw)

        self.assertEqual(order.plan_id, "PLAN-TEST")
        self.assertEqual(order.task_id, "T-001")
        self.assertEqual(order.acceptance_criteria, ("unit tests pass",))
        self.assertEqual(order.verification[0].purpose, "unit tests pass")
        self.assertEqual(len(order.input_hash), 64)
        self.assertEqual(order.input_hash, VerifyRequest.from_mapping(raw).input_hash)

    def test_rejects_boolean_revision_instead_of_treating_it_as_integer_one(self):
        raw = json.loads(
            (FIXTURES / "verify-order-pass.json").read_text(encoding="utf-8")
        )
        raw["revision"] = True

        with self.assertRaises(QualityError) as raised:
            VerifyRequest.from_mapping(raw)

        self.assertEqual(raised.exception.code, "ORDER_INVALID")

    def test_rejects_unapproved_verification_fields(self):
        raw = json.loads(
            (FIXTURES / "verify-order-pass.json").read_text(encoding="utf-8")
        )
        raw["verification"][0]["env"] = {"TOKEN": "untrusted"}

        with self.assertRaises(QualityError) as raised:
            VerifyRequest.from_mapping(raw)

        self.assertEqual(raised.exception.code, "ORDER_INVALID")

    def test_accepts_optional_composition_contract_and_environment_identities(self):
        raw = json.loads((FIXTURES / "verify-order-pass.json").read_text(encoding="utf-8"))
        raw.update({"composition_id": "C7", "manifest_sha256": "a" * 64,
                    "contract_identities": {"api@1": "b" * 64},
                    "environment_fingerprint": "c" * 64})
        order = VerifyRequest.from_mapping(raw)
        self.assertEqual(order.composition_id, "C7")
        self.assertEqual(order.manifest_sha256, "a" * 64)
        self.assertEqual(order.contract_identities, (("api@1", "b" * 64),))

    def test_rejects_duplicate_acceptance_criteria_that_make_coverage_ambiguous(self):
        raw = json.loads(
            (FIXTURES / "verify-order-pass.json").read_text(encoding="utf-8")
        )
        raw["acceptance_criteria"] = ["unit tests pass", "unit tests pass"]

        with self.assertRaises(QualityError) as raised:
            VerifyRequest.from_mapping(raw)

        self.assertEqual(raised.exception.code, "ORDER_INVALID")


class ResultContractTests(unittest.TestCase):
    def test_versioned_result_fixtures_match_the_runtime_contract(self):
        for name in ("result-pass.json", "result-needs-review.json"):
            with self.subTest(name=name):
                result = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
                validate_result_contract(result)

        schema = json.loads(
            (FIXTURES.parents[1] / "api-contract.json").read_text(encoding="utf-8")
        )
        self.assertEqual(schema["$id"], "m6.verify-result/1.1")

    def test_legacy_stored_result_reads_as_unclassified_without_mutating_record(self):
        result = json.loads((FIXTURES / "result-pass.json").read_text(encoding="utf-8"))
        validate_result_contract(result)
        self.assertEqual(read_reason_code(result["checks"][0]), "UNCLASSIFIED")
        self.assertNotIn("reason_code", result["checks"][0])
        loaded = read_result(result)
        self.assertEqual(loaded["reason_code"], "UNCLASSIFIED")
        self.assertEqual(loaded["checks"][0]["reason_code"], "UNCLASSIFIED")
        self.assertNotIn("reason_code", result["checks"][0])

    def test_v2_reason_code_is_validated_and_classified(self):
        result = json.loads((FIXTURES / "result-pass.json").read_text(encoding="utf-8"))
        result["schema_version"] = "m6.verify-result/1.1"
        result["reason_code"] = "PASS"
        result["checks"][0]["reason_code"] = "PASS"
        validate_result_contract(result)
        self.assertEqual(read_reason_code(result["checks"][0]), "PASS")
        result["checks"][0]["reason_code"] = "MAYBE"
        with self.assertRaises(QualityError):
            validate_result_contract(result)

    def test_runner_outcomes_map_to_the_compatible_reason_taxonomy(self):
        cases = (("pass", None, "PASS"), ("fail", None, "FAIL_CODE"),
                 ("unknown", "CHECK_TIMEOUT", "TIMEOUT"),
                 ("unknown", "CHECK_UNAVAILABLE", "BLOCKED_EXTERNAL"),
                 ("unknown", "SANDBOX_UNAVAILABLE", "BLOCKED_ENV"),
                 ("unknown", "CHECK_NOT_RUN", "NOT_RUN"),
                 ("pass", "FLAKY_SUSPECTED", "FLAKY_SUSPECTED"))
        for status, issue, expected in cases:
            with self.subTest(issue=issue):
                self.assertEqual(reason_for_outcome(status, issue), expected)

    def test_result_rejects_malformed_per_check_issue_code(self):
        result = json.loads(
            (FIXTURES / "result-needs-review.json").read_text(encoding="utf-8")
        )
        result["checks"][0]["issue_code"] = "bad code"

        with self.assertRaises(QualityError) as raised:
            validate_result_contract(result)

        self.assertEqual(raised.exception.code, "RESULT_INVALID")


if __name__ == "__main__":
    unittest.main()
