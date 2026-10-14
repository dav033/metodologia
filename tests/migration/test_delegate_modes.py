"""Opt-in delegation modes use throwaway state and real temporary Git repositories."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
import importlib
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[2] / "skill" / "scripts"


STUB = r'''import json, pathlib, sys
result = pathlib.Path(sys.argv[1])
mode = sys.argv[2]
cwd = pathlib.Path.cwd()
counter = cwd / ".attempt-count"
if mode.startswith("review"):
    n = 1
else:
    n = int(counter.read_text()) + 1 if counter.exists() else 1
    counter.write_text(str(n))
if mode == "retry":
    if n == 1:
        print("same boom")
        sys.exit(1)
    pathlib.Path("product.txt").write_text("done")
    result.write_text(json.dumps({"task_id": "x", "status": "done", "summary": "implemented"}))
elif mode == "repeat":
    print("same boom")
    sys.exit(1)
elif mode == "limit":
    print("usage limit reached")
    sys.exit(1)
elif mode.startswith("review"):
    seen = pathlib.Path("tracked.txt").read_text() == "working" and pathlib.Path("new.txt").read_text() == "untracked"
    payload = {"verdict": "findings" if seen else "incomplete",
               "findings": [{"severity": "med", "file": "new.txt", "line": 1}] if seen else []}
    result.write_text(json.dumps({"task_id": "x", "status": "done", "summary": json.dumps(payload),
                                  "evidence": str(seen)}))
    if mode == "review-edit":
        pathlib.Path("reviewer.txt").write_text("must be discarded")
else:
    pathlib.Path("product.txt").write_text("done")
    result.write_text(json.dumps({"task_id": "x", "status": "done", "summary": "implemented"}))
'''


class DelegateModeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="delegate-modes-")
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        if str(SCRIPTS) not in sys.path:
            sys.path.insert(0, str(SCRIPTS))
        old_home, old_root = os.environ.get("HOME"), os.environ.get("BITACORA_ROOT")
        os.environ["HOME"] = str(base / "home")
        os.environ["BITACORA_ROOT"] = str(base / "bitacora")
        (base / "home").mkdir()
        (base / "bitacora").mkdir()
        global bt_code_review, bt_delegate, bt_delegate_modes, bt_events
        bt_code_review = importlib.import_module("bt_code_review")
        bt_delegate = importlib.import_module("bt_delegate")
        bt_delegate_modes = importlib.import_module("bt_delegate_modes")
        bt_events = importlib.import_module("bt_events")
        importlib.import_module("bt_profiles")
        if old_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = old_home
        if old_root is None:
            os.environ.pop("BITACORA_ROOT", None)
        else:
            os.environ["BITACORA_ROOT"] = old_root
        self.repo = base / "repo"
        self.repo.mkdir()
        self.git(self.repo, "init", "-q", "-b", "main")
        self.git(self.repo, "config", "user.name", "Test")
        self.git(self.repo, "config", "user.email", "test@example.invalid")
        (self.repo / "tracked.txt").write_text("base\n")
        self.git(self.repo, "add", "tracked.txt")
        self.git(self.repo, "commit", "-qm", "base")
        self.stub = base / "stub.py"
        self.stub.write_text(STUB)
        state = base / "state"
        for target, value in (("bt_delegate.DIR", base / "delegations"),
                              ("bt_delegate.STATE", base / "bitacora" / ".state"),
                              ("bt_events.STATE", state),
                              ("bt_profiles.STATE", state)):
            patcher = patch(target, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.no_auth = patch("bt_profiles.authorize_ambient")
        self.no_auth.start()
        self.addCleanup(self.no_auth.stop)
        self.record = patch("bt_events.record_attempt")
        self.record.start()
        self.addCleanup(self.record.stop)

    @staticmethod
    def git(cwd: Path, *args: str) -> str:
        return subprocess.run(["git", *args], cwd=cwd, check=True, text=True, capture_output=True).stdout.strip()

    def make_order(self, verify: str | None = None, allow: list[str] | None = None) -> dict:
        return bt_delegate.create("demo", "Implement one change", None, "claude", self.repo, allow or [],
                                  verify, 1, None, None, tier=0)

    def command(self, mode: str) -> str:
        return f'"{sys.executable}" "{self.stub}" "{{result}}" {mode}'

    def test_retries_climb_once_and_stop_on_repeated_normalized_error(self) -> None:
        verify = f'"{sys.executable}" -c "import pathlib,sys; sys.exit(0 if pathlib.Path(\'product.txt\').exists() else 1)"'
        order = self.make_order(verify=verify)
        tiers: list[int] = []
        avoided: list[set[str]] = []
        def route(row: dict, tier: int, avoid: set[str]) -> dict:
            tiers.append(tier)
            avoided.append(set(avoid))
            return {"agent": "codex", "model": "gpt-6-luna", "effort": "medium"}

        with patch.object(bt_delegate_modes, "_route", side_effect=route):
            result = bt_delegate_modes.execute(order["id"], self.command("retry"), retries=1)
        self.assertEqual(tiers, [1])
        self.assertEqual(avoided, [{"claude"}])
        self.assertEqual(result["status"], "verified")
        self.assertEqual([row["result"] for row in result["attempts"]], ["verify_failed", "verified"])
        prompt = (bt_delegate.path_of(order["id"]) / "prompt.txt").read_text()
        self.assertIn("Previous attempt", prompt)
        self.assertIn("same boom", prompt)

        repeated = self.make_order()
        with patch.object(bt_delegate_modes, "_route", return_value={"agent": "claude", "model": "sonnet"}):
            stopped = bt_delegate_modes.execute(repeated["id"], self.command("repeat"), retries=3)
        self.assertEqual(stopped["status"], "blocked")
        self.assertEqual(len(stopped["attempts"]), 2)

    def test_usage_limit_does_not_climb_or_consume_a_retry(self) -> None:
        order = self.make_order()
        with patch.object(bt_delegate, "_next_route", return_value=None), \
                patch.object(bt_delegate_modes, "_route", side_effect=AssertionError("must not climb")):
            result = bt_delegate_modes.execute(order["id"], self.command("limit"), retries=2)
        self.assertEqual(result["status"], "usage_limit")
        self.assertEqual(result["attempts"], [])

    def test_worktree_isolated_verify_and_cleanup_refuses_dirty_tree(self) -> None:
        verify = f'"{sys.executable}" -c "import pathlib; pathlib.Path(\'verified-in\').write_text(str(pathlib.Path.cwd()))"'
        order = self.make_order(verify=verify)
        before_head = self.git(self.repo, "rev-parse", "HEAD")
        before_branch = self.git(self.repo, "branch", "--show-current")
        result = bt_delegate_modes.execute(order["id"], self.command("done"), worktree=True)
        self.assertEqual(result["status"], "verified")
        self.assertNotEqual(result["candidate_sha"], result["base_sha"])
        self.assertTrue((Path(result["worktree"]) / "verified-in").exists())
        self.assertEqual(self.git(self.repo, "rev-parse", "HEAD"), before_head)
        self.assertEqual(self.git(self.repo, "branch", "--show-current"), before_branch)
        self.assertEqual(self.git(self.repo, "status", "--porcelain"), "")
        (Path(result["worktree"]) / "uncommitted.txt").write_text("dirty")
        with self.assertRaisesRegex(SystemExit, "worktree is dirty"):
            bt_delegate_modes.cleanup(order["id"])
        (Path(result["worktree"]) / "uncommitted.txt").unlink()
        self.assertIn("branch_kept", bt_delegate_modes.cleanup(order["id"]))

    def test_review_snapshots_dirty_and_untracked_and_reports_reviewer_edits(self) -> None:
        (self.repo / "tracked.txt").write_text("working")
        (self.repo / "new.txt").write_text("untracked")
        before = self.git(self.repo, "status", "--porcelain")
        with patch.object(bt_code_review, "_provider", return_value=("claude", "claude")):
            result = bt_code_review.review(self.repo, project="demo", agent_cmd=self.command("review-edit"))
        self.assertEqual(result["verdict"], "findings")
        self.assertTrue(result["modified_tree"])
        self.assertTrue(Path(result["throwaway_worktree"]).exists())
        self.assertEqual(self.git(self.repo, "status", "--porcelain"), before)
        self.assertEqual((self.repo / "tracked.txt").read_text(), "working")
        self.assertTrue((self.repo / "new.txt").exists())

    def test_resume_skips_verified_and_restarts_interrupted_id(self) -> None:
        verified = self.make_order(verify="true")
        d = bt_delegate.path_of(verified["id"])
        (d / "session.log").write_text("")
        (d / "OUTCOME.json").write_text(json.dumps({"id": verified["id"], "status": "verified", "rc": 0}))
        marker = self.repo / "should-not-run"
        no_run = f'"{sys.executable}" -c "open(\'{marker}\', \'w\').write(\'bad\')"'
        result = bt_delegate_modes.resume(verified["id"], no_run)
        self.assertEqual(result["status"], "verified")
        self.assertFalse(marker.exists())

        interrupted = self.make_order()
        stale = bt_delegate.path_of(interrupted["id"])
        interrupted["retries"] = 2
        interrupted["attempt_history"] = [{"attempt": 1, "route": "claude", "provider": "claude",
                                            "result": "failed", "seconds": 2, "error": "old error"}]
        (stale / "TASK.json").write_text(json.dumps(interrupted))
        (stale / "CLAIMED").write_text("99999999")
        with patch.object(bt_delegate_modes, "_route", return_value={"agent": "codex", "model": "gpt-6-luna"}):
            resumed = bt_delegate_modes.resume(interrupted["id"], self.command("done"))
        self.assertEqual(resumed["id"], interrupted["id"])
        self.assertEqual(resumed["status"], "claimed")
        self.assertEqual([row["attempt"] for row in resumed["attempts"]], [1, 2])

    def test_default_execution_keeps_legacy_unverified_status(self) -> None:
        order = self.make_order()
        result = bt_delegate_modes.execute(order["id"], self.command("done"))
        self.assertEqual(result["status"], "claimed")
        self.assertNotIn("attempts", result)


if __name__ == "__main__":
    unittest.main()
