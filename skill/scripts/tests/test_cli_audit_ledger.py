"""The public ledger checker is read-only and does not need a bound project."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class LedgerCLI(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path = self.root / "audit.findings.json"

    def run_check(self, raw):
        if raw is not None:
            self.path.write_bytes(raw)
        script = Path(__file__).resolve().parents[1] / "bitacora.py"
        return subprocess.run([sys.executable, str(script), "audit-ledger", "check", str(self.path)],
                              cwd=self.root, env={**os.environ, "BITACORA_ROOT": str(self.root / "unused")},
                              text=True, capture_output=True, timeout=15)

    def test_a_valid_ledger_with_open_findings_is_valid_json_contract_not_a_passing_audit(self):
        data = {"schema": "audit-findings/1", "findings": [{"id": "F1", "severity": "high", "status": "open",
                                                          "summary": "wrong behavior", "tasks": ["T1"]}]}
        result = self.run_check(json.dumps(data).encode())
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse((self.root / "unused").exists())

    def test_invalid_json_missing_file_and_contract_errors_exit_two_with_problems(self):
        for raw, message in ((None, "unreadable"), (b"{", "JSON"), (b"\xff", "JSON"), (b"{}", "schema")):
            with self.subTest(raw=raw):
                result = self.run_check(raw)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn(message, result.stdout)

    def test_compatible_ledger_spellings_use_the_same_cli(self):
        for status, field in (("fixed", "tasks"), ("closed", "taskReferences"), ("accepted", "tasks")):
            item = {"id": "F1", "severity": "info", "status": status, "summary": "confirmed finding",
                    field: ["T1"], "evidence": "test passed", "accepted_by": "owner", "reason": "known risk"}
            result = self.run_check(json.dumps({"schema": "audit-findings/1", "findings": [item]}).encode())
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_tree_digest_reads_the_plan_and_excludes_explicit_evidence_without_creating_state(self):
        import bt_audit_gate
        from scheduler_executor_support import make_repo

        repo = make_repo(self.root / "app")
        plan = {"tasks": [{"id": "T1", "repository": "app", "kind": "implement", "expected_paths": ["result.json"]}]}
        path = self.root / "PLAN.json"
        path.write_text(json.dumps(plan))
        script = Path(__file__).resolve().parents[1] / "bitacora.py"
        result = subprocess.run([sys.executable, str(script), "audit-ledger", "tree-digest", str(path),
                                 "--repository", str(repo), "--role", "app", "--evidence", "result.json"],
                                cwd=self.root, env={**os.environ, "BITACORA_ROOT": str(self.root / "unused")},
                                text=True, capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.strip(), bt_audit_gate.tree_digest(repo, "HEAD", ["result.json"]))
        self.assertFalse((self.root / "unused").exists())


if __name__ == "__main__":
    unittest.main()
