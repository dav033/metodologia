"""Version-gated 1.2.0 report fields and unchanged legacy summaries."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from bt_planner import cli, quality

GOLDEN = Path(__file__).with_name("golden")


class PlannerReport(unittest.TestCase):
    def run_report(self, version: str) -> tuple[dict, dict]:
        plan = json.loads((GOLDEN / f"input-{version}.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "PLAN.json").write_text(json.dumps(plan), encoding="utf-8")
            lines: list[str] = []
            self.assertEqual(cli.run("report", directory, emit=lines.append), 0, lines)
        return plan, json.loads(lines[0])

    def test_legacy_report_shapes_remain_unchanged(self):
        for version in ("1.0.0", "1.1.0"):
            with self.subTest(version=version):
                plan, report = self.run_report(version)
                self.assertEqual(report, quality.analyze(plan))

    def test_schema_1_2_report_adds_declared_quality_projections(self):
        plan, report = self.run_report("1.2.0")
        legacy = quality.analyze(plan)
        self.assertEqual({key: report[key] for key in legacy}, legacy)
        self.assertEqual(report["coverage"], {"R1": ["T1", "T2"]})
        self.assertEqual(report["interfaces"][0]["id"], "IF-1")
        self.assertEqual(report["verification_categories"]["R1"]["categories"], ["functional", "regression"])
        self.assertIsInstance(report["criteria_without_command"], list)
        self.assertNotIn("product_acceptance", report)


if __name__ == "__main__":
    unittest.main()
