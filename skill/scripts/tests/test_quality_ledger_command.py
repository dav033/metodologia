"""The command required by the planner runs without installing the engine in product sandboxes."""
import json
import tempfile
import unittest
from pathlib import Path

from bitacora_platform.quality_audit_evidence import EvidenceRunner
from bt_scheduler_quality.policy import CheckSpec, QualityPolicy
from bt_scheduler_quality.runner import SandboxRunner


class EngineLedgerCommandTests(unittest.TestCase):
    def run_check(self, root, ledger="audit.findings.json"):
        argv = ("bitacora.py", "audit-ledger", "check", ledger)
        spec = CheckSpec("C1", "command", " ".join(argv), argv, ".", "ledger")
        runner = EvidenceRunner(SandboxRunner(QualityPolicy()), lambda *_: False, lambda: None)
        return runner.run(spec, root)

    def test_engine_command_uses_the_shared_contract_on_the_immutable_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "audit.findings.json").write_text(json.dumps({"schema": "audit-findings/1", "findings": [
                {"id": "F1", "severity": "high", "status": "open", "summary": "wrong", "tasks": ["T1"]}]}))
            outcome = self.run_check(root)
        self.assertEqual((outcome.status, outcome.exit_code), ("pass", 0), outcome.stderr)

    def test_missing_malformed_and_outside_snapshot_ledgers_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for text in [None, "{", "{}"]:
                if text is not None:
                    (root / "audit.findings.json").write_text(text)
                outcome = self.run_check(root)
                self.assertEqual((outcome.status, outcome.exit_code), ("fail", 2))
            self.assertEqual(self.run_check(root, "../audit.findings.json").status, "fail")
