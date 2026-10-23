"""Tracked build outputs: bounded declarations and advice for unordered writers."""
import unittest

from bt_planner import contract
from bt_planner.tests.test_contract import plan, task


class Generated(unittest.TestCase):
    def test_optional_declarations_and_commands(self):
        for command in ("npm run registry:build", {"backend": "npm run registry:build"}):
            proposed = plan()
            proposed.update(generated_paths=["registry.json", "registry/**/registry.json"], generated_command=command)
            self.assertEqual(contract.validate(proposed).errors, [])

    def test_invalid_declarations(self):
        for paths in (None, "x", [""], ["/tmp/x"], ["../x"], ["a/../x"], ["C:\\x"],
                      ["a\\..\\x"], ["x\n"], ["x" * 1025], ["x"] * 257):
            with self.subTest(paths=str(paths)[:60]):
                proposed = plan()
                proposed["generated_paths"] = paths
                self.assertTrue(any("generated_paths" in e for e in contract.validate(proposed).errors))
        for command in (None, "", "x" * 4097, {}, {"backend": ""}, {"backend": 1}):
            proposed = plan()
            proposed["generated_command"] = command
            self.assertTrue(any("generated_command" in e for e in contract.validate(proposed).errors))

    def test_advice_respects_transitive_order_roles_and_declarations(self):
        for name in ("registry.json", "package.lock", "ui.snap", "catalog/resolved.ts", "generated/x.ts", "dist/a.js"):
            proposed = plan(task(expected_paths=[name]), task("T2", milestone_id="M2", expected_paths=[name]))
            warnings = contract.validate(proposed).warnings
            self.assertTrue(any("generated_paths" in w and name in w for w in warnings), warnings)
            proposed["generated_paths"] = [name]
            self.assertFalse(any("generated_paths" in w for w in contract.validate(proposed).warnings))
            del proposed["generated_paths"]
            proposed["tasks"][1]["after"] = ["T1"]
            self.assertFalse(any("generated_paths" in w for w in contract.validate(proposed).warnings))
            proposed["tasks"][1].update(after=[], repository="other")
            self.assertFalse(any("generated_paths" in w for w in contract.validate(proposed).warnings))

    def test_generated_declarations_exempt_only_generated_path_coupling(self):
        proposed = plan(task(coupling="low", shared_resources=[], expected_paths=["registry.json"]),
                        task("T2", milestone_id="M2", coupling="low", shared_resources=[], expected_paths=["registry.json"]))
        proposed["schema_version"] = "1.1.0"
        proposed["generated_paths"] = ["registry.json"]
        self.assertFalse(any("coupling low" in e for e in contract.validate(proposed).errors))
        for row in proposed["tasks"]:
            row["expected_paths"].append("source.ts")
        self.assertTrue(any("source.ts" in e and "coupling low" in e for e in contract.validate(proposed).errors))
