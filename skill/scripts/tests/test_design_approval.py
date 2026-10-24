from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import bt_design_approval as approval


class DesignApprovalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rdir = Path(self.tmp.name) / "REQ-001-demo"
        self.rdir.mkdir()
        self.repo = self.rdir / "repo"
        self.repo.mkdir()
        self._git("init", "-q")
        self._git("config", "user.email", "test@example.com")
        self._git("config", "user.name", "Test")
        contract = self.repo / "design/contracts/checkout@v1.md"
        contract.parent.mkdir(parents=True)
        contract.write_text("# Approved contract\n", encoding="utf-8")
        self._git("add", ".")
        self._git("commit", "-qm", "contract")

    def tearDown(self):
        self.tmp.cleanup()

    def _git(self, *args):
        import subprocess
        return subprocess.run(["git", *args], cwd=self.repo, check=True, capture_output=True).stdout.decode().strip()

    def test_approval_pins_head_blob_and_is_immutable(self):
        record = approval.decide(self.rdir, self.repo, "checkout@v1", True, "Looks good", "david", "cli")
        self.assertEqual(record["status"], "approved")
        self.assertEqual(record["sha256"], hashlib.sha256(b"# Approved contract\n").hexdigest())
        with self.assertRaises(approval.DesignApprovalError):
            approval.decide(self.rdir, self.repo, "checkout@v1", False, "Actually change it", "david", "cli")
        data = json.loads((self.rdir / "design-approvals.json").read_text())
        self.assertEqual(data["approvals"]["checkout@v1"]["status"], "approved")

    def test_approval_requires_contract_blob_but_changes_request_does_not(self):
        with self.assertRaises(approval.DesignApprovalError):
            approval.decide(self.rdir, self.repo, "missing@v2", True, "", "david", "cli")
        record = approval.decide(self.rdir, self.repo, "missing@v2", False, "Add interaction states", "david", "web")
        self.assertEqual(record["status"], "changes-requested")
        self.assertIsNone(record["sha256"])

    def test_gate_compares_selected_tree_hash_to_approval(self):
        approval.decide(self.rdir, self.repo, "checkout@v1", True, "", "david", "cli")
        head = self._git("rev-parse", "HEAD")
        self.assertEqual(approval.check_tree(self.rdir, self.repo, head, "design/contracts/checkout@v1.md")["state"],
                         "approved")
        changed = self.repo / "design/contracts/checkout@v1.md"
        changed.write_text("# Changed\n", encoding="utf-8")
        self._git("add", ".")
        self._git("commit", "-qm", "change")
        next_head = self._git("rev-parse", "HEAD")
        self.assertEqual(approval.check_tree(self.rdir, self.repo, next_head, "design/contracts/checkout@v1.md")["state"],
                         "hash-mismatch")


if __name__ == "__main__":
    unittest.main()
