"""One-task delegation: independent verification, compact results, gate before any prompt, outside-scope detection."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import bt_delegate  # noqa: E402  (imports bt_core: test_00_isolation establishes the disposable root)
import bt_profiles  # noqa: E402

STUB = """
import json, pathlib, sys, time
result, mode = pathlib.Path(sys.argv[1]), sys.argv[2]
if mode == "sleep":
    time.sleep(60)
pathlib.Path("out.txt").write_text("hello")
pathlib.Path("elsewhere.txt").write_text("x")
if mode in ("done", "done_bad"):
    result.write_text(json.dumps({"task_id": "x", "status": "done", "summary": "S" * 900,
                                  "changed_files": ["out.txt"], "followups": ["look at y"]}))
print("session log noise " * 50)
"""


class DelegationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="delegate-test-")
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.work = base / "repo"
        self.work.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=self.work, check=True)
        self.stub = base / "stub.py"
        self.stub.write_text(STUB)
        for target, value in (("bt_delegate.DIR", base / "delegations"), ("bt_events.STATE", base / ".state"),
                              ("bt_profiles.STATE", base / ".state"),
                              ("bt_profiles.is_work_project", lambda project: project == "pictures"),
                              ("bt_profiles.ws.project_for_path", lambda root, cwd: "pictures")):
            patcher = patch(target, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        bt_profiles.add("claude-work", "claude", {"CLAUDE_CONFIG_DIR": str(base / "cw")}, work_only=True)

    def run_delegation(self, mode, verify=None, allow=None, timeout=1, project="pictures", profile=None):
        order = bt_delegate.create(project, "Create out.txt", profile, None if profile else "claude", self.work,
                                   allow or [], verify, timeout, None, None)
        cmd = f'"{sys.executable}" "{self.stub}" "{{result}}" {mode}'
        return bt_delegate.execute(order["id"], cmd)

    def test_verified_only_when_the_independent_check_passes(self):
        check = f'"{sys.executable}" -c "import pathlib,sys; sys.exit(0 if pathlib.Path(\'out.txt\').exists() else 1)"'
        out = self.run_delegation("done", verify=check)
        self.assertEqual(out["status"], "verified")
        self.assertTrue(out["claimed_done"])
        self.assertIn("out.txt", out["changed_files"])
        self.assertEqual(out["verify"]["exit"], 0)

    def test_claim_with_failing_check_is_not_success(self):
        fail = f'"{sys.executable}" -c "import sys; sys.exit(3)"'
        out = self.run_delegation("done_bad", verify=fail)
        self.assertEqual(out["status"], "verify_failed")
        self.assertTrue(out["claimed_done"])
        self.assertFalse(out["verified"])

    def test_claim_without_a_check_stays_claimed(self):
        out = self.run_delegation("done")
        self.assertEqual(out["status"], "claimed")
        self.assertIsNone(out["verified"])

    def test_no_report_is_a_failure(self):
        out = self.run_delegation("silent")
        self.assertEqual(out["status"], "failed")
        self.assertFalse(out["claimed_done"])

    def test_timeout_kills_the_session(self):
        with patch.object(bt_delegate, "VERIFY_TIMEOUT_SEC", 5):
            out = self.run_delegation("sleep", timeout=0.03)
        self.assertEqual(out["status"], "timeout")

    def test_result_is_compact_and_flags_changes_outside_the_allowed_paths(self):
        out = self.run_delegation("done", allow=["out.txt"])
        self.assertLessEqual(len(out["summary"]), bt_delegate.SUMMARY_MAX)
        self.assertEqual(out["outside_allowed"], ["elsewhere.txt"])
        self.assertNotIn("session log noise", json.dumps(out))  # the full log stays on disk
        self.assertEqual(out["followups"], ["look at y"])

    def test_gate_stops_a_work_only_profile_before_anything_is_written(self):
        with patch("bt_profiles.is_work_project", lambda project: False), self.assertRaises(SystemExit):
            bt_delegate.create("maros", "x", "claude-work", None, self.work, [], None, 1, None, None)
        self.assertFalse(list(bt_delegate.DIR.glob("D-*")))

    def test_gate_also_checks_the_folder(self):
        with patch("bt_profiles.ws.project_for_path", lambda root, cwd: "maros"), self.assertRaises(SystemExit):
            bt_delegate.create("pictures", "x", "claude-work", None, self.work, [], None, 1, None, None)

    def test_each_delegation_is_recorded_as_an_attempt(self):
        import bt_events
        self.run_delegation("done")
        rows = bt_events.read_all()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["result"], "claimed")


if __name__ == "__main__":
    unittest.main()
