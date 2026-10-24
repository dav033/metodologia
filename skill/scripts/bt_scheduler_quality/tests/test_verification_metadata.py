from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from bt_scheduler_quality.authority import VerificationAuthority
from bt_scheduler_quality.contracts import VerifyRequest
from bt_scheduler_quality.engine import QualityEngine
from bt_scheduler_quality.policy import QualityPolicy
from bt_scheduler_quality.runner import CommandOutcome
from bt_scheduler_quality.store import QualityStore
from test_snapshot import _make_snapshot

FIXTURE = Path(__file__).parent / "fixtures" / "verify-order-pass.json"


class RecordingRunner:
    def __init__(self, outcome=None):
        self.calls = []
        self.outcome = outcome or CommandOutcome("pass", 0, 1, b"stub verification\n", b"", None, True)

    def run(self, check, snapshot_root, *, timeout_seconds=None, mounts=()):
        self.calls.append(check.id)
        return self.outcome


class VerificationMetadataExecutionTests(unittest.TestCase):
    def setUp(self):
        self.raw = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_missing_declared_resources_block_before_the_runner(self):
        cases = ((["DB_URL", "service:postgres"], VerificationAuthority()),
                 (["service:postgres"], VerificationAuthority(resource_available=lambda _name: False)))
        for resources, authority in cases:
            with self.subTest(resources=resources), tempfile.TemporaryDirectory() as temporary, QualityStore(":memory:") as store:
                _, source, _, _ = _make_snapshot(Path(temporary))
                self.raw["verification"][0].update(environment="sandbox", requires=resources)
                runner = RecordingRunner()
                result = QualityEngine(QualityPolicy(), store, runner=runner,
                                       verification_authority=authority).verify(
                                           {**self.raw, "idempotency_key": self.raw["idempotency_key"] + str(resources)}, source)
            self.assertEqual(result["status"], "NEEDS_REVIEW")
            self.assertEqual(result["reason_code"], "BLOCKED_EXTERNAL")
            self.assertEqual(result["checks"][0]["reason_code"], "BLOCKED_EXTERNAL")
            self.assertEqual(runner.calls, [])

    def test_explicit_sandbox_runs_and_sandbox_refusal_stays_blocked_environment(self):
        for outcome, reason in ((CommandOutcome("pass", 0, 1, b"ok", b"", None, True), "PASS"),
                                (CommandOutcome("unknown", None, 0, b"", b"", "SANDBOX_UNAVAILABLE", False),
                                 "BLOCKED_ENV")):
            with self.subTest(reason=reason), tempfile.TemporaryDirectory() as temporary, QualityStore(":memory:") as store:
                _, source, _, _ = _make_snapshot(Path(temporary))
                self.raw["verification"][0]["environment"] = "sandbox"
                runner = RecordingRunner(outcome)
                result = QualityEngine(QualityPolicy(), store, runner=runner).verify(
                    {**self.raw, "idempotency_key": self.raw["idempotency_key"] + reason}, source)
            self.assertEqual(result["reason_code"], reason)
            self.assertEqual(len(runner.calls), 1)

    def test_trusted_resource_probe_and_authorization_gate_external_and_production(self):
        for environment in ("external_authorized", "production"):
            with self.subTest(environment=environment), tempfile.TemporaryDirectory() as temporary, QualityStore(":memory:") as store:
                _, source, _, _ = _make_snapshot(Path(temporary))
                self.raw["verification"][0].update(environment=environment, requires=["service:postgres"],
                                                     authorization_needed="Operator permits verification")
                denied_runner = RecordingRunner()
                denied = QualityEngine(QualityPolicy(), store, runner=denied_runner,
                                       verification_authority=VerificationAuthority(
                                           resource_available=lambda _name: True,
                                           authorize_environment=lambda _environment, _reason: False)).verify(self.raw, source)
                self.assertEqual(denied["reason_code"], "BLOCKED_EXTERNAL")
                self.assertEqual(denied["status"], "NEEDS_REVIEW")
                self.assertEqual(denied_runner.calls, [])
                allowed_runner = RecordingRunner()
                allowed = QualityEngine(QualityPolicy(), store, runner=allowed_runner,
                                        verification_authority=VerificationAuthority(
                                            resource_available=lambda _name: True,
                                            authorize_environment=lambda _environment, _reason: True)).verify(
                                                {**self.raw, "idempotency_key": self.raw["idempotency_key"] + environment}, source)
                self.assertEqual(allowed["reason_code"], "PASS")
                self.assertEqual(len(allowed_runner.calls), 1)

    def test_external_classification_without_a_trusted_authorization_port_blocks(self):
        with tempfile.TemporaryDirectory() as temporary, QualityStore(":memory:") as store:
            _, source, _, _ = _make_snapshot(Path(temporary))
            self.raw["verification"][0].update(environment="external_authorized",
                                                authorization_needed="Operator permits staging verification")
            runner = RecordingRunner()
            result = QualityEngine(QualityPolicy(), store, runner=runner).verify(self.raw, source)
        self.assertEqual(result["reason_code"], "BLOCKED_EXTERNAL")
        self.assertEqual(result["status"], "NEEDS_REVIEW")
        self.assertEqual(runner.calls, [])

    def test_external_checks_with_declared_resources_are_not_reused_as_cached_passes(self):
        with tempfile.TemporaryDirectory() as temporary, QualityStore(":memory:") as store:
            _, source, _, _ = _make_snapshot(Path(temporary))
            self.raw["verification"][0].update(environment="external_authorized", requires=["service:postgres"],
                                                authorization_needed="Operator permits this smoke")
            runner = RecordingRunner()
            authority = VerificationAuthority(resource_available=lambda _name: True,
                                              authorize_environment=lambda _environment, _reason: True)
            engine = QualityEngine(QualityPolicy(), store, runner=runner, verification_authority=authority)
            first = engine.verify(self.raw, source)
            second_order = {**self.raw, "idempotency_key": self.raw["idempotency_key"] + "second"}
            second = engine.verify(second_order, source)
        self.assertEqual((first["reason_code"], second["reason_code"]), ("PASS", "PASS"))
        self.assertEqual(len(runner.calls), 2)

    def test_human_attestation_is_never_run_as_a_command(self):
        for receipt, expected in (("sha256:approved", "PASS"), (None, "NEEDS_REVIEW")):
            with self.subTest(receipt=receipt), tempfile.TemporaryDirectory() as temporary, QualityStore(":memory:") as store:
                _, source, _, _ = _make_snapshot(Path(temporary))
                manual = {"type": "manual", "value": "review the service", "purpose": "unit tests pass",
                          "expected": "operator confirms the expected state", "environment": "human_attestation"}
                raw = {**self.raw, "verification": [manual], "idempotency_key": self.raw["idempotency_key"] + str(receipt)}
                runner = RecordingRunner()
                result = QualityEngine(QualityPolicy(), store, runner=runner,
                                       attestations=lambda _order, _spec: receipt).verify(raw, source)
            self.assertEqual(result["status"], expected)
            self.assertEqual(runner.calls, [])


if __name__ == "__main__":
    unittest.main()
