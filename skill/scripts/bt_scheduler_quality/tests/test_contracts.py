from __future__ import annotations

import json
import unittest
from pathlib import Path

from bt_scheduler_quality import QualityError, VerifyRequest
from bt_scheduler_quality.evidence import read_reason_code, read_result, reason_for_outcome, validate_result_contract

FIXTURES = Path(__file__).parent / "fixtures"


class VerifyRequestTests(unittest.TestCase):
    def test_m6_declares_schema_13_after_consuming_verification_metadata(self):
        from bt_scheduler_quality import PLAN_SCHEMA_CAPABILITIES

        self.assertIn("1.3.0", PLAN_SCHEMA_CAPABILITIES)

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

    def test_verification_environment_metadata_round_trips_without_changing_legacy_hashes(self):
        raw = json.loads((FIXTURES / "verify-order-pass.json").read_text(encoding="utf-8"))
        legacy = VerifyRequest.from_mapping(raw)
        self.assertNotIn("environment", legacy.to_dict()["verification"][0])
        self.assertNotIn("requires", legacy.to_dict()["verification"][0])
        self.assertEqual(legacy.input_hash, "0a1fbb8a208701a0029f073187bc16229111db8ce252281ff46557e6e9eaef3f")
        cases = (
            ("sandbox", ["DB_URL", "service:postgres"], None),
            ("external_authorized", [], "Owner authorizes the staging smoke"),
            ("production", [], "Owner authorizes the release verification"),
        )
        for environment, requires, authorization in cases:
            with self.subTest(environment=environment):
                item = {**raw["verification"][0], "environment": environment, "requires": requires}
                if authorization:
                    item["authorization_needed"] = authorization
                raw_case = {**raw, "verification": [item]}
                parsed = VerifyRequest.from_mapping(raw_case)
                self.assertEqual(parsed.to_dict()["verification"][0], item)
        manual = {"type": "manual", "value": "inspect", "purpose": "unit tests pass",
                  "expected": "owner confirms expected result", "environment": "human_attestation"}
        self.assertEqual(VerifyRequest.from_mapping({**raw, "verification": [manual]}).to_dict()["verification"][0], manual)

    def test_verification_metadata_rejects_values_raw_maps_and_secret_authorization(self):
        raw = json.loads((FIXTURES / "verify-order-pass.json").read_text(encoding="utf-8"))
        invalid_items = (
            {"environment": "staging"},
            {"requires": ["DB_URL=postgres://user:password@host/db"]},
            {"requires": [{"DB_URL": "secret"}]},
            {"authorization_needed": "Owner supplies token: abc123"},
            {"environment": "production"},
            {"environment": "human_attestation"},
        )
        for fields in invalid_items:
            with self.subTest(fields=fields):
                raw["verification"] = [{**raw["verification"][0], **fields}]
                with self.assertRaises(QualityError):
                    VerifyRequest.from_mapping(raw)

    def test_secret_shaped_authorization_is_refused_one_shape_at_a_time(self):
        for text in ("Use Bearer eyJabc.def", "key sk-live-4f9a8b7c6d5e", "aws AKIAIOSFODNN7EXAMPLE",
                     "ghp_abcdefghijklmnopqrstuvwxyz0123456789", "pass=hunter2", "opaque " + "a1B2c3D4" * 5):
            with self.subTest(text=text):
                raw = json.loads((FIXTURES / "verify-order-pass.json").read_text(encoding="utf-8"))
                raw["verification"] = [{**raw["verification"][0], "environment": "production",
                                        "authorization_needed": text}]
                with self.assertRaises(QualityError):
                    VerifyRequest.from_mapping(raw)

    def test_plain_authorization_descriptions_stay_accepted(self):
        raw = json.loads((FIXTURES / "verify-order-pass.json").read_text(encoding="utf-8"))
        for text in ("Owner authorizes the staging smoke on the payments sandbox account",
                     "Operator permits read-only production checks for REQ-020 during the release window"):
            with self.subTest(text=text):
                raw["verification"] = [{**raw["verification"][0], "environment": "production",
                                        "authorization_needed": text}]
                self.assertEqual(VerifyRequest.from_mapping(raw).to_dict()["verification"][0]["authorization_needed"], text)

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
        verification = schema["$defs"]["verification"]
        self.assertEqual(set(verification["properties"]) - {"type", "value", "purpose", "expected", "created_by", "category"},
                         {"environment", "requires", "authorization_needed"})
        self.assertEqual(schema["properties"]["input"]["dependentRequired"], {
            "composition_id": ["manifest_sha256"],
            "manifest_sha256": ["composition_id"],
        })

    def test_legacy_stored_result_reads_as_unclassified_without_mutating_record(self):
        result = json.loads((FIXTURES / "result-pass.json").read_text(encoding="utf-8"))
        normalized = read_result(result)
        validate_result_contract(normalized)
        self.assertEqual(read_reason_code(result["checks"][0]), "UNCLASSIFIED")
        self.assertNotIn("reason_code", result["checks"][0])
        loaded = read_result(result)
        self.assertEqual(loaded["reason_code"], "UNCLASSIFIED")
        self.assertEqual(loaded["checks"][0]["reason_code"], "UNCLASSIFIED")
        self.assertNotIn("reason_code", result["checks"][0])

    def test_current_result_rejects_unclassified_reason_codes(self):
        result = json.loads((FIXTURES / "result-pass.json").read_text(encoding="utf-8"))
        result.update(schema_version="m6.verify-result/1.1", reason_code="UNCLASSIFIED")
        result["checks"][0]["reason_code"] = "UNCLASSIFIED"
        with self.assertRaises(QualityError):
            validate_result_contract(result)

    def test_runtime_rejects_partial_composition_identity(self):
        raw = json.loads((FIXTURES / "verify-order-pass.json").read_text(encoding="utf-8"))
        raw["composition_id"] = "C7"
        with self.assertRaises(QualityError):
            VerifyRequest.from_mapping(raw)

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
