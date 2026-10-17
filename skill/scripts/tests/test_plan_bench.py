from __future__ import annotations

import json
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path

from bt_planner import resources
from plan_bench import (
    RUBRIC_SHA256,
    load_rubric,
    parse_check_output,
    parse_quality_report,
)

SCRIPTS = Path(__file__).resolve().parents[1]


class PlannerBenchmarkEntryPointTests(unittest.TestCase):
    def test_rubric_cli_runs_from_an_unrelated_working_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run(["python3", str(SCRIPTS / "bt_plan_bench.py"), "rubric"], cwd=temporary,
                                    capture_output=True, text=True, timeout=10, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), load_rubric())

    def test_parsers_accept_actual_planner_check_and_report_json_shapes(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "REQ-042-example"
            target.mkdir()
            (target / "PLAN.json").write_text(resources.example_text(), encoding="utf-8")
            check = subprocess.run(["python3", "-m", "bt_planner", "check", str(target), "--json"],
                                   cwd=SCRIPTS, capture_output=True, text=True, timeout=10, check=False)
            report = subprocess.run(["python3", "-m", "bt_planner", "report", str(target)],
                                    cwd=SCRIPTS, capture_output=True, text=True, timeout=10, check=False)
        self.assertEqual(check.returncode, 2)  # fixture has no matching PLAN.md; JSON remains machine-readable
        self.assertIsInstance(parse_check_output(check.stdout)["errors"], list)
        self.assertEqual(report.returncode, 0, report.stderr)
        parsed = parse_quality_report(report.stdout)
        self.assertTrue({"coverage", "interfaces", "verification_categories", "criteria_without_command"}
                        <= set(parsed))

    def test_packaging_registers_the_harness_and_pinned_rubric(self):
        config = tomllib.loads((SCRIPTS.parents[1] / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertIn("plan_bench", config["tool"]["setuptools"]["packages"])
        self.assertIn("bt_plan_bench", config["tool"]["setuptools"]["py-modules"])
        self.assertEqual(config["tool"]["setuptools"]["package-data"]["plan_bench"], ["data/*.json", "README.md"])
        self.assertEqual(len(RUBRIC_SHA256), 64)


if __name__ == "__main__":
    unittest.main()
