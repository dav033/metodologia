from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import bt_cli_plan
import bt_plan_history


class PlanningHistoryProjectionTests(unittest.TestCase):
    def test_projection_keeps_all_metrics_unknown_without_cross_route_sources(self):
        report = bt_plan_history.project_history(
            "implement",
            {"complexity": "high", "scope": "full_feature", "risk": "medium", "coupling": "low"},
        )

        self.assertEqual(report["schema_version"], "1.0.0")
        self.assertEqual(report["status"], "unknown")
        self.assertEqual(report["context"], {
            "complexity": "high", "scope": "full_feature", "risk": "medium", "coupling": "low",
        })
        self.assertEqual(set(report["metrics"]), {"quality", "duration", "retries", "consumption"})
        for metric in report["metrics"].values():
            self.assertEqual(metric["status"], "unknown")
            self.assertEqual(metric["source_quality"], "unknown")
            self.assertIsNone(metric["comparability_key"])
            self.assertTrue(metric["reason"])

        self.assertIsNone(report["metrics"]["quality"]["observed_rate"])
        self.assertIsNone(report["metrics"]["retries"]["count"])
        self.assertEqual(report["metrics"]["duration"]["unit"], "seconds")
        self.assertIsNone(report["metrics"]["consumption"]["unit"])

    def test_projection_rejects_invalid_external_context_without_echoing_values(self):
        with self.assertRaisesRegex(bt_plan_history.PlanningHistoryInputError, "history_kind_invalid"):
            bt_plan_history.project_history("secret-provider-model")
        with self.assertRaisesRegex(bt_plan_history.PlanningHistoryInputError, "history_context_invalid:risk"):
            bt_plan_history.project_history("implement", {"risk": "secret-value"})
        with self.assertRaisesRegex(bt_plan_history.PlanningHistoryInputError, "history_context_invalid:field"):
            bt_plan_history.project_history("implement", {"model": "secret-value"})

    def test_serialized_projection_contains_no_route_or_account_fields(self):
        report = bt_plan_history.project_history("test")
        forbidden = {"route", "route_id", "provider", "model", "account", "effort", "quota"}

        def keys(value):
            if isinstance(value, dict):
                yield from value.keys()
                for nested in value.values():
                    yield from keys(nested)
            elif isinstance(value, list):
                for nested in value:
                    yield from keys(nested)

        self.assertTrue(forbidden.isdisjoint({key.lower() for key in keys(report)}))
        json.dumps(report, sort_keys=True)

    def test_cli_command_is_read_only_json_and_does_not_require_a_requirement_id(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command", required=True)
        bt_cli_plan.add_parser(subparsers)
        args = parser.parse_args(["plan-json", "history", "--kind", "docs", "--scope", "small_change"])
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            status = bt_cli_plan.dispatch(args, Path("/unused"), "methodologia")

        self.assertEqual(status, 0)
        report = json.loads(stdout.getvalue())
        self.assertEqual(report["kind"], "docs")
        self.assertEqual(report["context"]["scope"], "small_change")

    def test_cli_rejects_missing_kind_and_requirement_id_for_other_actions(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command", required=True)
        bt_cli_plan.add_parser(subparsers)
        stdout = io.StringIO()
        args = parser.parse_args(["plan-json", "history"])
        with contextlib.redirect_stdout(stdout):
            status = bt_cli_plan.dispatch(args, Path("/unused"), "methodologia")
        self.assertEqual(status, 2)
        self.assertIn("requires --kind", stdout.getvalue())

        stdout = io.StringIO()
        args = parser.parse_args(["plan-json", "check"])
        with contextlib.redirect_stdout(stdout):
            status = bt_cli_plan.dispatch(args, Path("/unused"), "methodologia")
        self.assertEqual(status, 2)
        self.assertIn("requires REQ-NNN", stdout.getvalue())

        stdout = io.StringIO()
        args = parser.parse_args(["plan-json", "check", "REQ-024", "--kind", "implement"])
        with contextlib.redirect_stdout(stdout):
            status = bt_cli_plan.dispatch(args, Path("/unused"), "metodologia")
        self.assertEqual(status, 2)
        self.assertIn("only valid with plan-json history", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
