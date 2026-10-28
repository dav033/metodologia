"""The /flow failure log reads M6 evidence manifests through a versioned reader (m6.evidence-manifest/1 and /1.1)."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bt_page_flow_review as review
from bt_scheduler_quality.evidence import MANIFEST_VERSION

STATUS = {"run": {"authority": "scheduler"}, "plan": {"plan_id": "REQ-001", "revision": 2},
          "milestones": [{"tasks": [{"id": "T1", "history": [{"id": "A-1", "state": "rejected"}]}]}]}


class ManifestVersionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "m6.sqlite3"
        with sqlite3.connect(self.db) as connection:
            connection.execute("CREATE TABLE artifacts (digest TEXT PRIMARY KEY, content BLOB NOT NULL)")

    def store(self, content: bytes) -> str:
        digest = hashlib.sha256(content).hexdigest()
        with sqlite3.connect(self.db) as connection:
            connection.execute("INSERT OR IGNORE INTO artifacts VALUES (?, ?)", (digest, content))
        return digest

    def page(self, version: str) -> str:
        stdout = self.store(b"FAILED test_login\n")
        manifest = {"schema_version": version,
                    "request": {"plan_id": "REQ-001", "task_id": "T1", "attempt_id": "A-1", "revision": 2},
                    "checks": [{"id": "C1", "command": "pytest -q", "status": "failed", "exit_code": 1,
                                "issue_code": None, "stdout_ref": f"m6://artifact/{stdout}",
                                "stderr_ref": f"m6://artifact/{stdout}"}],
                    "criteria": [{"criterion": "Login works", "status": "fail"}], "issues": []}
        if version.endswith("/1.1"):
            manifest["checks"][0].update({"reason_code": "FAIL_CODE", "tree_digest": None, "argv": ["pytest", "-q"]})
        digest = self.store(json.dumps(manifest).encode())
        query = {"project": "demo", "req": "REQ-001", "task": "T1", "attempt": "A-1", "ref": f"m6://result/{digest}"}
        with patch("bt_plans_api.req_dir", return_value=Path(self.temp.name)), \
                patch("bt_planstatus.plan_status", return_value=STATUS), \
                patch("bt_run_stores.paths", return_value={"m6": self.db}):
            return review.review_page(Path(self.temp.name), query)

    def test_current_producer_manifest_version_is_read(self):
        self.assertEqual(MANIFEST_VERSION, "m6.evidence-manifest/1.1")
        html = self.page(MANIFEST_VERSION)
        self.assertNotIn("El manifiesto no corresponde", html)
        self.assertIn("pytest -q", html)
        self.assertIn("FAILED test_login", html)

    def test_legacy_manifest_version_is_still_read(self):
        html = self.page("m6.evidence-manifest/1")
        self.assertIn("pytest -q", html)

    def test_unknown_manifest_version_is_refused(self):
        html = self.page("m6.evidence-manifest/2")
        self.assertIn("El manifiesto no corresponde", html)
        self.assertNotIn("pytest -q", html)


if __name__ == "__main__":
    unittest.main()
