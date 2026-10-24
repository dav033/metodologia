from __future__ import annotations

import hashlib
import json
import tempfile
import concurrent.futures
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

    def _plan(self, design_role="app"):
        (self.rdir / "PLAN.json").write_text(json.dumps({
            "subplans": [{"id": "SP-1", "ui": {"contract": "checkout", "version": 1,
                                                   "design_task": "D1"}}],
            "tasks": [{"id": "D1", "subplan_id": "SP-1", "repository": design_role}],
        }))

    def _run_line(self, root, project="demo", requirement="REQ-001", identity="r1-a1-1", subplan="SP-1"):
        import bt_scheduler_executor_adapter as executor
        base = executor.executor_root(root / project / "requirements" / requirement)
        run_root = Path(f"{base}-{identity}")
        run_root.mkdir(parents=True, exist_ok=True)
        revision = f"refs/m3/line/{identity}/app/{subplan}"
        return run_root, revision

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

    def test_web_digest_must_match_clean_regular_head_blob(self):
        with self.assertRaises(approval.DesignApprovalError):
            approval.decide(self.rdir, self.repo, "checkout@v1", True, "", "owner", "web",
                            submitted_sha256="0" * 64)
        (self.repo / "design/contracts/checkout@v1.md").write_text("dirty\n")
        with self.assertRaisesRegex(approval.DesignApprovalError, "working tree"):
            approval.decide(self.rdir, self.repo, "checkout@v1", True, "", "owner", "web")

    def test_approval_snapshot_and_gate_use_the_requirement_run_subplan_line(self):
        root = self.rdir / "root"
        project = "demo"
        rdir = root / project / "requirements" / "REQ-001"
        rdir.mkdir(parents=True)
        self.rdir = rdir
        self._plan()
        line_blob = b"# Contract produced on the design line\n"
        contract = self.repo / "design/contracts/checkout@v1.md"
        contract.write_bytes(line_blob)
        self._git("add", ".")
        self._git("commit", "-qm", "design task output")
        _, revision = self._run_line(root, project, "REQ-001")
        self._git("update-ref", revision, "HEAD")
        contract.unlink()
        self._git("add", "-u")
        self._git("commit", "-qm", "contract not in HEAD")

        selected = approval.revision_for_contract(root, project, rdir, "checkout@v1", self.repo)
        self.assertEqual(selected, revision)
        snapshot = approval.contract_snapshot(self.repo, "design/contracts/checkout@v1.md", selected)
        self.assertEqual(snapshot, (line_blob.decode(), hashlib.sha256(line_blob).hexdigest()))
        self.assertEqual(approval.contract_snapshot_for(root, project, rdir, "checkout@v1", self.repo), snapshot)
        record = approval.decide(rdir, self.repo, "checkout@v1", True, "", "owner", "cli")
        self.assertEqual(record["sha256"], hashlib.sha256(line_blob).hexdigest())
        self.assertEqual(approval.check_tree(rdir, self.repo, revision,
                         "design/contracts/checkout@v1.md")["state"], "approved")

    def test_revision_resolution_is_scoped_to_the_requirement_run(self):
        root = self.rdir / "root"
        project = "demo"
        first = root / project / "requirements/REQ-001"
        second = root / project / "requirements/REQ-002"
        first.mkdir(parents=True)
        second.mkdir(parents=True)
        self.rdir = first
        self._plan()
        (second / "PLAN.json").write_text((first / "PLAN.json").read_text())
        _, other_line = self._run_line(root, project, "REQ-002", "r1-other-2")
        self.assertEqual(approval.revision_for_contract(root, project, first, "checkout@v1", self.repo), "HEAD")
        self.assertNotEqual(other_line, "HEAD")

    def test_revision_resolution_falls_back_to_head_before_a_run_exists(self):
        root = self.rdir / "root"
        self._plan()
        self.assertEqual(approval.revision_for_contract(root, "demo", self.rdir, "checkout@v1", self.repo), "HEAD")

    def test_contract_symlink_is_refused(self):
        path = self.repo / "design/contracts/checkout@v1.md"
        path.unlink()
        (self.repo / "elsewhere.md").write_text("contract\n")
        path.symlink_to("../../elsewhere.md")
        with self.assertRaisesRegex(approval.DesignApprovalError, "symlink"):
            approval.decide(self.rdir, self.repo, "checkout@v1", True, "", "owner", "web")

    def test_concurrent_decisions_serialize_immutable_transition(self):
        def decide():
            try:
                return approval.decide(self.rdir, self.repo, "checkout@v1", True, "", "owner", "cli")["status"]
            except approval.DesignApprovalError:
                return "rejected"
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: decide(), range(2)))
        self.assertEqual(sorted(results), ["approved", "rejected"])


if __name__ == "__main__":
    unittest.main()
