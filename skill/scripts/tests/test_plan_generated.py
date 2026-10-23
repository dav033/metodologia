"""The plan adapter and the standalone runtime agree on generated output declarations."""
import hashlib
import json
import unittest
from pathlib import Path

import bt_plan_adapter as adapter
from scheduler_executor_support import core


class GeneratedContract(unittest.TestCase):
    def test_adapter_and_runtime_path_validation_have_parity(self):
        fixture = Path(__file__).parents[1] / "bt_planner" / "tests" / "golden" / "canonical-1.0.0.json"
        original = json.loads(fixture.read_text())
        cases = (["registry.json", "registry/**/registry.json"], [], ["a" * 1024], ["x"] * 256,
                 None, "x", ["../x"], ["x/../y"], ["/x"], ["C:\\x"], ["x\\..\\y"], ["x\0y"],
                 ["x\n"], [" x"], ["x//y"], ["./x"], ["x/"], [False], ["a" * 1025], ["x"] * 257)
        for paths in cases:
            with self.subTest(paths=str(paths)[:50]):
                body = {**original, "generated_paths": paths}
                errors = adapter.plan_errors(body)
                raw = json.dumps(body)
                if any("generated_paths" in error for error in errors):
                    with self.assertRaises(core.SchedulerError):
                        core.load_plan(raw, approved_sha256=hashlib.sha256(raw.encode()).hexdigest())
                else:
                    self.assertEqual(errors, [])
                    loaded = core.load_plan(raw, approved_sha256=hashlib.sha256(raw.encode()).hexdigest())
                    self.assertEqual(loaded.generated_paths, tuple(paths))

    def test_adapter_rejects_invalid_command_metadata(self):
        body = {"generated_command": {"app": 12}, "tasks": []}
        self.assertTrue(any("generated_command" in error for error in adapter.plan_errors(body)))
