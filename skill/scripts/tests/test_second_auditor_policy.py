"""`gates.second_auditor`: the owner's policy, enforced where the consumer gate already is."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bt_config
import bt_plan_adapter as adapter


def write(audits: int) -> Path:
    tmp = Path(tempfile.mkdtemp())
    tasks = [{"id": f"T{n}", "kind": "audit"} for n in range(1, audits + 1)] + [{"id": "T9", "kind": "implement"}]
    path = tmp / "PLAN.json"
    path.write_text(json.dumps({"schema_version": "1.2.0", "plan_id": "REQ-1", "revision": 1, "tasks": tasks}))
    return path


class SecondAuditor(unittest.TestCase):
    def test_a_single_audit_is_refused_by_default_and_names_the_fix(self):
        problem = adapter.second_auditor_problem(write(1))
        self.assertIn("SECOND_AUDITOR_MISSING", problem)
        self.assertIn("retrofit-audit REQ --cross-check", problem)
        self.assertIn("gates.second_auditor false", problem)

    def test_two_audits_or_none_pass(self):
        self.assertIsNone(adapter.second_auditor_problem(write(2)))
        self.assertIsNone(adapter.second_auditor_problem(write(0)))

    def test_the_owner_can_turn_it_off(self):
        with patch.object(bt_config, "get", side_effect=lambda key, default=None: False if key == "gates.second_auditor" else default):
            self.assertIsNone(adapter.second_auditor_problem(write(1)))

    def test_older_schemas_are_left_alone(self):
        path = write(1)
        path.write_text(json.dumps({"schema_version": "1.1.0", "plan_id": "REQ-1", "revision": 1,
                                    "tasks": [{"id": "T1", "kind": "audit"}]}))
        self.assertIsNone(adapter.second_auditor_problem(path))

    def test_the_consumer_gate_includes_it(self):
        path = write(1)
        report = {"required_schema_version": "1.2.0", "supported": True}
        self.assertIn("SECOND_AUDITOR_MISSING",
                      adapter.plan_consumer_problem(path.parent, compatibility_report=report, plan_path=path))

    def test_the_config_default_and_validation(self):
        self.assertIs(bt_config.DEFAULTS["gates"]["second_auditor"], True)
        self.assertTrue(bt_config._valid("gates.second_auditor", False))
        self.assertFalse(bt_config._valid("gates.second_auditor", "no"))


if __name__ == "__main__":
    unittest.main()
