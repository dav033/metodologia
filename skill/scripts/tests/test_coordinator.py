"""P-157: the coordinator runs the live commands a plan leaves to «the coordinator» when the owner authorized the project, on the snapshot of
the attempt being verified, redacts every secret, and attests only when they all passed."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bt_config
import bt_coordinator as coord
import bt_interventions
import bt_recovery_export as export
import bt_scheduler_decisions as decisions
import bt_scheduler_ops as ops

T14A = ("Coordinator runs `npx tsx --conditions=react-server scripts/e2e/asesor/run.ts --start --live --milestone M1` and then "
        "`--milestone M2` with .env.local (live Gemini/Supabase/credentials) and records redacted evidence.")
SECRET = "fixture-value-not-a-credential-123"


class Parsing(unittest.TestCase):
    def test_a_later_flag_snippet_is_the_same_command_with_that_flag_changed(self):
        self.assertEqual(coord.commands_of(T14A), [
            "npx tsx --conditions=react-server scripts/e2e/asesor/run.ts --start --live --milestone M1",
            "npx tsx --conditions=react-server scripts/e2e/asesor/run.ts --start --live --milestone M2"])

    def test_text_that_is_not_a_command_gives_none(self):
        self.assertEqual(coord.commands_of("Use the deployed advisor on a phone; record permission, keyboard, reload."), [])
        self.assertEqual(coord.commands_of("Coordinator runs `rm -rf /` with .env.local"), [])             # only known runners

    def test_secret_values_are_removed_from_what_is_kept(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = Path(tmp) / ".env.local"
            env.write_text(f"# comment\nSUPABASE_KEY={SECRET}\nMODE='live'\nTOKEN=\"abcdef-token-value\"\n")
            secrets = coord.env_secrets(env)
        self.assertEqual(secrets, sorted([SECRET, "abcdef-token-value"], key=len, reverse=True))     # longest first: no partial leftovers
        self.assertEqual(coord.redact(f"key {SECRET} and abcdef-token-value", secrets), "key *** and ***")


class Attest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.repo = root / "repo"
        self.repo.mkdir()
        self.git("init", "-q")
        (self.repo / "app.txt").write_text("code\n")
        self.git("add", "app.txt")
        self.git("-c", "user.name=T", "-c", "user.email=t@t", "commit", "-qm", "base")
        self.sha = self.git("rev-parse", "HEAD")
        (self.repo / ".env.local").write_text(f"SUPABASE_KEY={SECRET}\n")
        self.rdir = root / "REQ-001-x"
        self.rdir.mkdir()
        manifest = root / "manifest.json"
        manifest.write_text(json.dumps({"repository": str(self.repo), "snapshot_sha": self.sha}))
        self.attested = []
        plan = SimpleNamespace(task=lambda tid: SimpleNamespace(verification=[
            {"type": "manual", "value": T14A, "purpose": "live flow", "expected": "evidence"}]))
        for target, name, value in ((ops, "bound_plan", plan), (export, "_manifest_path", manifest)):
            patcher = patch.object(target, name, return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch.object(ops, "attest", side_effect=lambda *a, **k: self.attested.append((a, k)) or ["attested"])
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch("bt_scheduler_quality.store.QualityStore")
        store = patcher.start()
        self.addCleanup(patcher.stop)
        store.return_value.open_review_attempts.return_value = ("att-7",)
        patcher = patch.object(bt_config, "get", side_effect=lambda key, default=None: {"coordinator.projects": ["pictures"],
                                                                                      "coordinator.command_seconds": 60}.get(key, default))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.notes = []
        patcher = patch.object(decisions, "write_verify_notes", side_effect=lambda rdir, task, text: self.notes.append((task, text)))
        patcher.start()
        self.addCleanup(patcher.stop)

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args], capture_output=True, text=True, check=True).stdout.strip()

    def runner(self, codes):
        calls = []

        def run(command, root, timeout, secrets):
            calls.append((command, (Path(root) / ".env.local").read_text(), (Path(root) / "app.txt").read_text()))
            return {"command": command, "exit_code": codes[len(calls) - 1], "seconds": 1.0,
                    "tail": [coord.redact(f"printed {SECRET}", secrets), "M done"]}
        return run, calls

    def test_all_live_commands_passing_attest_the_attempt_with_redacted_evidence(self):
        run, calls = self.runner([0, 0])
        lines = coord.attest_task("pictures", "REQ-001", self.rdir, "T14a", runner=run)
        self.assertEqual(len(calls), 2)
        self.assertIn(SECRET, calls[0][1])                                                  # it ran WITH the project's env file ...
        self.assertEqual(calls[0][2], "code\n")                                              # ... on the attempt's snapshot
        (args, _), = self.attested
        self.assertEqual(args[3], "T14a")
        self.assertNotIn(SECRET, args[5])                                                    # ... and the evidence says none of it
        self.assertIn("***", args[5])
        self.assertIn("milestone M2", args[5])
        self.assertTrue(any("passed" in line for line in lines))

    def test_a_failing_command_attests_nothing_and_leaves_the_failure_in_the_note(self):
        run, calls = self.runner([0, 1])
        lines = coord.attest_task("pictures", "REQ-001", self.rdir, "T14a", runner=run)
        self.assertEqual(self.attested, [])
        self.assertEqual(self.notes[0][0], "T14a")
        self.assertIn("FAILED", self.notes[0][1])
        self.assertNotIn(SECRET, self.notes[0][1])
        self.assertIn("not attested", lines[0])
        self.assertEqual(list(bt_interventions.read(self.rdir))[-1]["result"], "failed")

    def test_the_first_failure_stops_the_rest(self):
        run, calls = self.runner([2, 0])
        coord.attest_task("pictures", "REQ-001", self.rdir, "T14a", runner=run)
        self.assertEqual(len(calls), 1)

    def test_a_project_the_owner_did_not_name_is_refused_and_nothing_runs(self):
        run, calls = self.runner([0])
        with self.assertRaises(ops.core.SchedulerError):
            coord.attest_task("other", "REQ-001", self.rdir, "T14a", runner=run)
        self.assertEqual(calls, [])

    def test_a_task_with_a_human_manual_check_is_left_to_its_owner(self):
        plan = SimpleNamespace(task=lambda tid: SimpleNamespace(verification=[
            {"type": "manual", "value": T14A, "purpose": "live flow", "expected": "x"},
            {"type": "manual", "value": "Use the deployed advisor on a phone.", "purpose": "phone", "expected": "x"}]))
        run, calls = self.runner([0])
        with patch.object(ops, "bound_plan", return_value=plan):
            lines = coord.attest_task("pictures", "REQ-001", self.rdir, "T14a", runner=run)
        self.assertEqual((calls, self.attested), ([], []))
        self.assertIn("stays for its owner", lines[0])


class Turn(Attest):
    def test_each_open_review_gets_one_live_run_and_a_hold_stops_it(self):
        review = {"id": "REQ-001:r1:att-7:verify", "source": "review", "task": "T14a"}
        run, calls = self.runner([0, 0])
        with patch.object(decisions, "open_requests", return_value=[review, {"id": "T1:1", "source": "task", "task": "T1"}]), \
                patch.object(ops, "on_hold", return_value=False), patch.object(ops, "resume", return_value="resumed"):
            logs = []
            self.assertTrue(coord.cycle("pictures", "REQ-001", self.rdir, log=logs.append, runner=run))
            self.assertFalse(coord.cycle("pictures", "REQ-001", self.rdir, runner=run))            # the same review is never run twice
        self.assertEqual(len(calls), 2)
        self.assertEqual(len(self.attested), 1)
        with patch.object(decisions, "open_requests", return_value=[{**review, "id": "REQ-001:r1:att-8:verify"}]), \
                patch.object(ops, "on_hold", return_value=True):
            self.assertFalse(coord.cycle("pictures", "REQ-001", self.rdir, runner=run))            # an operator hold wins
        self.assertEqual(len(calls), 2)

    def test_an_unauthorized_project_is_never_touched(self):
        with patch.object(decisions, "open_requests", side_effect=AssertionError("must not even look")):
            self.assertFalse(coord.cycle("other", "REQ-001", self.rdir))


if __name__ == "__main__":
    unittest.main()


class Prepare(unittest.TestCase):
    """The snapshot tree the live commands run in: the attempt's files, the env file, and a node_modules Next/Turbopack accepts."""

    def test_the_tree_has_the_snapshot_the_env_file_and_a_hard_linked_node_modules_not_a_symlink(self):
        import subprocess
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory(dir=Path.home() / ".cache") as base:
            repo, work = Path(base) / "repo", Path(base) / "work"
            (repo / "node_modules" / "dep").mkdir(parents=True)
            work.mkdir()
            (repo / "app.txt").write_text("v1")
            (repo / "node_modules" / "dep" / "index.js").write_text("module.exports = 1")
            env = Path(base) / "env"
            env.write_text("KEY=secret-value\n")
            subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
            subprocess.run(["git", "-C", str(repo), "add", "app.txt"], check=True)
            subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x"], check=True)
            sha = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
            root = coord.prepare(repo, sha, work, env)
            self.assertEqual((root / "app.txt").read_text(), "v1")
            self.assertEqual((root / ".env.local").read_text(), "KEY=secret-value\n")
            self.assertEqual(oct((root / ".env.local").stat().st_mode & 0o777), "0o600")
            modules = root / "node_modules"
            self.assertTrue(modules.is_dir() and not modules.is_symlink())
            self.assertEqual((modules / "dep" / "index.js").stat().st_ino, (repo / "node_modules" / "dep" / "index.js").stat().st_ino)
