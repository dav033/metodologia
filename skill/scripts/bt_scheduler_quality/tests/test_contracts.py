from __future__ import annotations

import json
import unittest
from pathlib import Path

from bt_scheduler_quality import QualityError, VerifyRequest
from bt_scheduler_quality.evidence import validate_result_contract

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
        self.assertEqual(schema["$id"], "m6.verify-result/1")

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
