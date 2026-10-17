"""Golden-byte regression for PLAN.json 1.0.0 and 1.1.0 canonicalization."""
from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from bt_planner import contract as pc

GOLDEN = Path(__file__).with_name("golden")
EXPECTED = {
    "1.0.0": {
        "input": "50e171f5526fa69b6028051c1a8c10750eaf95bd171c9da4ba431f4609e06038",
        "canonical": "be7bf5e1770ca310204bbc3e5d54098bb9169d6c0af154465d69907a568d5581",
    },
    "1.1.0": {
        "input": "70d724c3d713683288f9600bbb1ca6ec9bb9e197de8196453f4f89f9810f5a0e",
        "canonical": "b25c04d10ffbfa4afd85fabb314bba753a395d13253235c26aa09216b40db68d",
    },
    "1.2.0": {
        "input": "d142ef9433287d6ee72feddda4fcf2cdfefe4cb5d439dcfc996bb2854d3d56dc",
        "canonical": "c4e548ff1f5fc7e7686323fcff2b55d2c008f03fc8f780d90b45cc86daef170b",
    },
}


class CanonicalGolden(unittest.TestCase):
    def assert_golden(self, version: str) -> str:
        input_path = GOLDEN / f"input-{version}.json"
        output_path = GOLDEN / f"canonical-{version}.json"
        input_bytes = input_path.read_bytes()
        expected_bytes = output_path.read_bytes()
        self.assertEqual(hashlib.sha256(input_bytes).hexdigest(), EXPECTED[version]["input"])
        self.assertEqual(hashlib.sha256(expected_bytes).hexdigest(), EXPECTED[version]["canonical"])
        plan = json.loads(input_bytes)
        self.assertEqual(plan["schema_version"], version)
        if version in ("1.0.0", "1.1.0"):
            self.assertEqual(pc.validate(plan).errors, [])
        actual = pc.dumps(plan).encode("utf-8")
        self.assertEqual(actual, expected_bytes)
        return actual.decode("utf-8")

    def test_1_0_0_preserves_legacy_nested_extension_order(self):
        text = self.assert_golden("1.0.0")
        self.assertLess(text.index('"reason"'), text.index('"owner"'))
        self.assertLess(text.index('"owner"'), text.index('"approved_by"'))
        self.assertLess(text.index('"second"'), text.index('"first"'))

    def test_1_1_0_deep_sorts_nested_extensions_and_evidence(self):
        text = self.assert_golden("1.1.0")
        self.assertLess(text.index('"approved_by"'), text.index('"owner"'))
        self.assertLess(text.index('"first"'), text.index('"second"'))

    def test_1_2_0_proposed_keys_have_a_pre_change_hash(self):
        self.assert_golden("1.2.0")
        plan = json.loads((GOLDEN / "input-1.2.0.json").read_bytes())
        self.assertEqual(plan["requirements"], ["R1"])
        self.assertEqual(plan["tasks"][0]["covers"], ["R1"])
        self.assertEqual(plan["tasks"][0]["kind"], "implement")
        self.assertEqual(plan["tasks"][0]["verification"][0]["category"], "functional")
        self.assertEqual(plan["interfaces"][0]["id"], "IF-1")
