"""Version-gated validator hooks and legacy report compatibility for PLAN.json."""
from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from bt_planner import contract as pc
from bt_planner import quality

GOLDEN = Path(__file__).with_name("golden")
BASELINE_REPORT_SHA256 = {
    "1.0.0": "0be1c76d923d752e95bec7d18737a0c40cfe35b9f4ec3816af6931a92567babd",
    "1.1.0": "812d5587fbf9c7e17b73ee7aaac39ddd9ae6bcc39da3c1051a273dd2126838f2",
}


def load_plan(version: str) -> dict:
    return json.loads((GOLDEN / f"input-{version}.json").read_bytes())


def report_bytes(report: pc.Report) -> bytes:
    value = {"errors": report.errors, "warnings": report.warnings}
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


class ValidatorExtensions(unittest.TestCase):
    def test_legacy_validation_reports_match_the_pre_extension_baseline(self):
        for version in ("1.0.0", "1.1.0"):
            with self.subTest(version=version):
                expected = (GOLDEN / f"validation-{version}.json").read_bytes()
                self.assertEqual(hashlib.sha256(expected).hexdigest(), BASELINE_REPORT_SHA256[version])
                self.assertEqual(report_bytes(pc.validate(load_plan(version))), expected)

    def test_extensions_are_not_called_for_legacy_or_unsupported_versions(self):
        for version in ("1.0.0", "1.1.0", "2.0.0"):
            with self.subTest(version=version):
                with (
                    patch("bt_planner.contract.traceability.check") as traceability_check,
                    patch("bt_planner.contract.interfaces.check") as interfaces_check,
                    patch("bt_planner.contract.quality.verification_findings") as verification_findings,
                ):
                    plan = load_plan("1.1.0")
                    plan["schema_version"] = version
                    pc.validate(plan)
                traceability_check.assert_not_called()
                interfaces_check.assert_not_called()
                verification_findings.assert_not_called()

    def test_schema_1_2_calls_each_extension_and_merges_findings(self):
        plan = load_plan("1.2.0")
        with (
            patch("bt_planner.contract.traceability.check", return_value=(
                ["traceability error"], ["traceability warning"]
            )) as traceability_check,
            patch("bt_planner.contract.interfaces.check", return_value=(
                ["interface error"], ["interface warning"]
            )) as interfaces_check,
            patch("bt_planner.contract.quality.verification_findings", return_value=[
                "verification warning"
            ]) as verification_findings,
        ):
            report = pc.validate(plan)

        traceability_check.assert_called_once_with(plan, None)
        interfaces_check.assert_called_once_with(plan, quality.ancestors(plan))
        verification_findings.assert_called_once_with(plan)
        self.assertIn("traceability error", report.errors)
        self.assertIn("interface error", report.errors)
        self.assertIn("traceability warning", report.warnings)
        self.assertIn("interface warning", report.warnings)
        self.assertIn("verification warning", report.warnings)

    def test_schema_1_2_requires_supported_kind_and_verification_category(self):
        plan = load_plan("1.2.0")
        plan["tasks"][0].pop("kind")
        plan["tasks"][0]["verification"][0].pop("category")
        report = pc.validate(plan)
        self.assertTrue(any("T1.kind: missing" in error for error in report.errors), report.errors)
        self.assertTrue(any("T1.verification[0].category: missing" in error for error in report.errors), report.errors)

        plan = load_plan("1.2.0")
        plan["tasks"][0]["kind"] = "specialist"
        report = pc.validate(plan)
        self.assertTrue(any("T1.kind: 'specialist' is not one of" in error for error in report.errors), report.errors)

if __name__ == "__main__":
    unittest.main()
