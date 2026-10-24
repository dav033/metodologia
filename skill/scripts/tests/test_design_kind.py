"""Classification and CLI exposure for Designer work."""
from __future__ import annotations

import argparse
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bt_agent_models
import bt_agents
import bt_cli_accounts
import bt_cli_delegate
import bt_efficiency
import bt_events
from unittest.mock import patch


class DesignKindTests(unittest.TestCase):
    def test_design_is_a_supported_kind_and_classifies_contract_tasks(self):
        self.assertIn("design", bt_agent_models.KINDS)
        self.assertEqual(bt_agent_models.infer_kind("Author UI design contract"), "design")
        self.assertEqual(bt_agent_models.infer_kind("Review the UI contract", "design"), "design")

    def test_design_is_selectable_by_delegate_and_agents_clis(self):
        delegate_sub = argparse.ArgumentParser().add_subparsers()
        bt_cli_delegate.register(delegate_sub)
        delegate = delegate_sub.choices["delegate"].parse_args(["start", "Author UI design contract", "--kind", "design"])
        self.assertEqual(delegate.kind, "design")

        machine_sub = argparse.ArgumentParser().add_subparsers()
        bt_cli_accounts.register(machine_sub)
        agents = machine_sub.choices["agents"].parse_args(["route", "--kind", "design"])
        self.assertEqual(agents.kind, "design")

    def test_telemetry_preserves_design_as_a_distinct_kind(self):
        details = bt_events.detail_for([{"id": "T1", "kind": "design"}], "done")
        self.assertEqual(details["task_outcomes"][0]["kind"], "design")
        self.assertEqual(bt_efficiency._key({"kind": "design"}, ("kind",)), ("design",))

    def test_agent_brief_mentions_designer_and_preview_configuration(self):
        with patch("bt_agents._catalog_brief", return_value="catalog"):
            text = bt_agents.brief()
        self.assertIn("Designer", text)
        self.assertIn("owner-approved contract", text)
        self.assertIn("`design.preview`", text)


if __name__ == "__main__":
    unittest.main()
