from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from bt_scheduler_quality import VerifyRequest
from bt_scheduler_quality.policy import QualityPolicy, compile_verification

FIXTURE = Path(__file__).parent / "fixtures" / "verify-order-pass.json"


class VerificationPolicyTests(unittest.TestCase):
    def setUp(self):
        self.raw = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_compiles_plan_command_to_argv_without_a_shell(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            order = VerifyRequest.from_mapping(self.raw)

            check = compile_verification(order, root, QualityPolicy())[0]

        self.assertEqual(check.argv, ("python3", "-m", "unittest", "-q"))
        self.assertEqual(check.cwd, ".")
        self.assertEqual(check.purpose, "unit tests pass")

    def test_supports_only_a_leading_snapshot_relative_cd(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "skill" / "scripts").mkdir(parents=True)
            self.raw["verification"][0]["value"] = (
                "cd skill/scripts && python3 -m unittest -q"
            )

            check = compile_verification(
                VerifyRequest.from_mapping(self.raw), root, QualityPolicy()
            )[0]

        self.assertEqual(check.cwd, "skill/scripts")
        self.assertEqual(check.argv[0], "python3")

    def test_refuses_shell_chains_without_executing_any_part(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.raw["verification"][0]["value"] = (
                "python3 -m unittest -q && echo unsafe"
            )

            with self.assertRaises(ValueError):
                compile_verification(
                    VerifyRequest.from_mapping(self.raw), root, QualityPolicy()
                )

    def test_a_leading_variable_assignment_runs_through_env_without_a_shell(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "web").mkdir()
            self.raw["verification"][0]["value"] = (
                "cd web && DB_URL=postgresql://u:p@127.0.0.1:5432/db npx tsx --test a.ts"
            )
            check = compile_verification(VerifyRequest.from_mapping(self.raw), root, QualityPolicy())[0]
            self.assertEqual(check.argv, ("env", "DB_URL=postgresql://u:p@127.0.0.1:5432/db", "npx", "tsx", "--test", "a.ts"))
            self.assertEqual(check.cwd, "web")
            for value in ("PATH=/tmp npm test", "LD_PRELOAD=x.so npm test", "DB_URL=x"):
                self.raw["verification"][0]["value"] = value
                with self.assertRaises(ValueError):
                    compile_verification(VerifyRequest.from_mapping(self.raw), root, QualityPolicy())

    def test_refuses_working_directories_that_escape_the_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.raw["verification"][0]["value"] = "cd ../../ && python3 -m unittest -q"

            with self.assertRaises(ValueError):
                compile_verification(
                    VerifyRequest.from_mapping(self.raw), root, QualityPolicy()
                )

    def test_manual_check_is_preserved_for_review_not_made_runnable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.raw["verification"] = [
                {
                    "type": "manual",
                    "value": "photo review",
                    "purpose": "unit tests pass",
                    "expected": "the render matches the approved photo",
                }
            ]

            check = compile_verification(
                VerifyRequest.from_mapping(self.raw), root, QualityPolicy()
            )[0]

        self.assertEqual(check.kind, "manual")
        self.assertEqual(check.argv, ())
        self.assertEqual(check.expected, "the render matches the approved photo")

    def test_secret_cannot_be_embedded_in_a_plan_command(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.raw["verification"][0]["value"] = "python3 check.py m6-private-token"
            policy = QualityPolicy(secret_values=("m6-private-token",))

            with self.assertRaisesRegex(ValueError, "configured secret"):
                compile_verification(VerifyRequest.from_mapping(self.raw), root, policy)

    def test_sensitive_environment_value_requires_redaction_registration(self):
        with self.assertRaisesRegex(ValueError, "registered for redaction"):
            QualityPolicy(environment=(("SERVICE_API_KEY", "m6-private-token"),))

        policy = QualityPolicy(
            environment=(("SERVICE_API_KEY", "m6-private-token"),),
            secret_values=("m6-private-token",),
        )

        self.assertEqual(policy.environment[0][1], "m6-private-token")

    def test_runtime_environment_cannot_replace_sandbox_controls(self):
        with self.assertRaisesRegex(ValueError, "protected or invalid"):
            QualityPolicy(environment=(("PYTHONPATH", "/tmp/host-modules"),))


if __name__ == "__main__":
    unittest.main()
