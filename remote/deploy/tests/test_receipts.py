"""Offline validation for production deployment receipts."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

DEPLOY = Path(__file__).resolve().parents[1]
VERIFIER = DEPLOY / "verify_receipt.py"
REQUIRED_STEPS = [
    "snapshot-before",
    "caddy-backup",
    "service-layout",
    "systemd-verify",
    "caddy-validate",
    "caddy-reload",
    "other-hosts-check",
    "rollback-rehearsal",
]
REQUIRED_CHECKS = {
    "snapshot-before",
    "service-layout",
    "other-hosts-unchanged",
    "rollback-rehearsed",
}


def head_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=DEPLOY, text=True).strip()


def valid_receipt() -> dict:
    return {
        "schema_version": 1,
        "name": "advin-provision",
        "deployed_git_sha": head_sha(),
        "steps": [
            {"name": name, "command": "sudo <redacted deployment command>", "exit_code": 0}
            for name in REQUIRED_STEPS
        ],
        "checks": {
            name: {"ok": True, "detail": "Recorded offline evidence: passed"}
            for name in REQUIRED_CHECKS
        },
    }


class ReceiptVerifierTest(unittest.TestCase):
    def run_verifier(self, receipt: dict, *args: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "receipt.json"
            path.write_text(json.dumps(receipt), encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(VERIFIER), str(path), *args],
                cwd=DEPLOY,
                capture_output=True,
                text=True,
            )

    def test_accepts_valid_receipt_and_named_check(self):
        result = self.run_verifier(valid_receipt(), "--check", "snapshot-before")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("snapshot-before: ok", result.stdout)

    def test_rejects_failed_check(self):
        receipt = valid_receipt()
        receipt["checks"]["service-layout"] = {"ok": False, "detail": "systemd verification failed"}
        result = self.run_verifier(receipt)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("service-layout", result.stderr)

    def test_rejects_missing_required_step(self):
        receipt = valid_receipt()
        receipt["steps"] = [step for step in receipt["steps"] if step["name"] != "caddy-backup"]
        result = self.run_verifier(receipt)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("caddy-backup", result.stderr)

    def test_rejects_missing_required_check(self):
        receipt = valid_receipt()
        del receipt["checks"]["rollback-rehearsed"]
        result = self.run_verifier(receipt)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("rollback-rehearsed", result.stderr)

    def test_rejects_secret_looking_values(self):
        receipt = valid_receipt()
        receipt["steps"][0]["command"] = "sudo env SESSION_SECRET=sample-value deploy"
        result = self.run_verifier(receipt)
        self.assertNotEqual(result.returncode, 0)
        self.assertRegex(result.stderr.lower(), "secret|credential|redact")

    def test_rejects_commit_that_is_not_an_ancestor_of_head(self):
        receipt = valid_receipt()
        receipt["deployed_git_sha"] = "0" * 40
        result = self.run_verifier(receipt)
        self.assertNotEqual(result.returncode, 0)
        self.assertRegex(result.stderr.lower(), "ancestor|commit|sha")

    def test_rejects_nonzero_step_exit_code(self):
        receipt = valid_receipt()
        receipt["steps"][2]["exit_code"] = 1
        result = self.run_verifier(receipt)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("service-layout", result.stderr)


if __name__ == "__main__":
    unittest.main()
