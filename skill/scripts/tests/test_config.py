"""Machine-local configuration defaults, validation, persistence, and CLI parsing."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import bt_config  # noqa: E402


class ConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="config-test-")
        self.addCleanup(self.tmp.cleanup)
        self.state = Path(self.tmp.name) / ".state"
        patcher = patch("bt_config.STATE", self.state)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_defaults(self):
        self.assertEqual(bt_config.load(), bt_config.DEFAULTS)
        self.assertEqual(bt_config.get("routing.pool"), [])
        self.assertIsNone(bt_config.get("unknown"))
        self.assertEqual(bt_config.get("unknown", "fallback"), "fallback")
        self.assertFalse(bt_config.get("design.preview"))
        self.assertEqual(bt_config.get("design.preview_projects"), [])

    def test_design_preview_configuration_roundtrips_and_validates(self):
        bt_config.set_value("design.preview", True)
        bt_config.set_value("design.preview_projects", ["alpha", "beta"])
        self.assertTrue(bt_config.get("design.preview"))
        self.assertEqual(bt_config.get("design.preview_projects"), ["alpha", "beta"])
        for key, value in (("design.preview", 1), ("design.preview_projects", ["alpha", 3]),
                           ("design.preview_projects", "alpha")):
            with self.subTest(key=key, value=value), self.assertRaises(bt_config.ConfigError):
                bt_config.set_value(key, value)

    def test_set_get_roundtrip_for_each_type(self):
        values = {"executor.display": "window", "approval.auto": False, "approval.max_tasks": 0,
                  "routing.pool": ["claude", "codex"]}
        for key, value in values.items():
            with self.subTest(key=key):
                bt_config.set_value(key, value)
                self.assertEqual(bt_config.get(key), value)

    def test_unknown_key_is_refused(self):
        with self.assertRaisesRegex(bt_config.ConfigError, "Unknown configuration key"):
            bt_config.set_value("unknown.key", True)

    def test_wrong_type_is_refused(self):
        for key, value in (("approval.auto", 1), ("approval.max_tasks", "4"), ("routing.pool", ["ok", 3]),
                           ("routing.pool", "claude"), ("approval.max_tasks", -1)):
            with self.subTest(key=key, value=value):
                with self.assertRaises(bt_config.ConfigError):
                    bt_config.set_value(key, value)

    def test_bool_is_not_accepted_as_an_integer(self):
        with self.assertRaises(bt_config.ConfigError):
            bt_config.set_value("approval.max_tasks", True)

    def test_enumerated_value_is_refused(self):
        for key, value in (("executor.display", "terminal"), ("routing.mode", "random"),
                           ("audit.mode", "always")):
            with self.subTest(key=key):
                with self.assertRaises(bt_config.ConfigError):
                    bt_config.set_value(key, value)

    def test_corrupt_file_and_wrong_typed_stored_values_fall_back(self):
        self.state.mkdir(parents=True)
        path = self.state / "config.json"
        path.write_text("{broken", encoding="utf-8")
        self.assertEqual(bt_config.load(), bt_config.DEFAULTS)
        path.write_text(json.dumps({"approval": {"auto": "yes", "max_tasks": True},
                                    "routing": {"pool": ["valid", 2]}}), encoding="utf-8")
        self.assertEqual(bt_config.load(), bt_config.DEFAULTS)

    def test_file_contains_only_overrides(self):
        path = bt_config.set_value("approval.max_tasks", 12)
        self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"approval": {"max_tasks": 12}})
        bt_config.set_value("approval.max_tasks", 40)
        self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {})

    def test_unset_removes_override(self):
        bt_config.set_value("routing.mode", "fixed")
        path = bt_config.unset("routing.mode")
        self.assertEqual(bt_config.get("routing.mode"), "auto")
        self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {})

    def test_cli_get_set_unset_and_comma_list(self):
        self.assertEqual(json.loads(bt_config.cli("get", "approval.auto", None)), True)
        self.assertEqual(json.loads(bt_config.cli("get", None, None)), bt_config.DEFAULTS)
        self.assertEqual(bt_config.cli("set", "routing.pool", "claude,codex"), "Set routing.pool.")
        self.assertEqual(bt_config.get("routing.pool"), ["claude", "codex"])
        bt_config.cli("set", "approval.max_tasks", "3")
        self.assertEqual(bt_config.get("approval.max_tasks"), 3)
        self.assertEqual(bt_config.cli("unset", "approval.max_tasks", None), "Unset approval.max_tasks.")
        self.assertEqual(bt_config.get("approval.max_tasks"), 40)

    def test_parse_cli_value(self):
        self.assertIs(bt_config.parse_cli_value("true"), True)
        self.assertEqual(bt_config.parse_cli_value("3"), 3)
        self.assertEqual(bt_config.parse_cli_value('["a"]'), ["a"])
        self.assertEqual(bt_config.parse_cli_value("plain text"), "plain text")


if __name__ == "__main__":
    unittest.main()
