"""P-165: a manual criterion written as prose is judged from read-only evidence the engine gathers, not left for a person."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bt_manual_reviewer as reviewer  # noqa: E402


class Vetting(unittest.TestCase):
    def setUp(self):
        self.snap, self.repo = Path("/tmp/snap"), Path("/tmp/repo")
        self.roots = [self.snap, self.repo]

    def vet(self, command):
        return reviewer.vet(command, self.roots, self.snap, self.repo)

    def test_reads_are_allowed_and_run_where_they_belong(self):
        self.assertEqual(self.vet("gh repo view dav033/david-ui --json visibility")[1], self.repo)
        self.assertEqual(self.vet("git log --oneline -3")[1], self.repo)
        self.assertEqual(self.vet("gh api repos/a/b/commits")[1], self.repo)
        self.assertEqual(self.vet("cat docs/a.md")[1], self.snap)
        self.assertEqual(self.vet("grep -n R1 docs/a.md")[1], self.snap)

    def test_nothing_that_writes_deletes_or_leaves_the_roots_is_allowed(self):
        for command in ("gh repo delete x", "gh api repos/a/b -X DELETE", "gh api repos/a/b -f x=1", "git push origin main",
                        "git branch -D x", "git remote add x y", "git config user.name x", "git log --output=/tmp/x", "rm -rf x",
                        "cat /etc/passwd", "cat ../x", "echo $(id)", "curl http://x", "rm -rf x"):
            self.assertIsNone(self.vet(command), command)


class LiteralArguments(unittest.TestCase):
    def test_a_pipe_inside_an_argument_is_a_grep_pattern_not_a_shell(self):
        """The first real run refused `grep -rniE "license|clean-room"`: nothing here goes through a shell, so it is literal text."""
        snap, repo = Path("/tmp/snap"), Path("/tmp/repo")
        argv, cwd = reviewer.vet('grep -rniE "license|clean-room" docs', [snap, repo], snap, repo)
        self.assertEqual(argv[-2:], ["license|clean-room", "docs"])
        self.assertEqual(cwd, snap)


class Judging(unittest.TestCase):
    check = {"purpose": "repo is private", "value": "inspect gh", "expected": "PRIVATE"}
    results = [{"command": "gh repo view x", "exit_code": 0, "output": "PRIVATE"}]

    def test_a_verdict_the_reviewer_doubts_is_not_a_verdict(self):
        sure = reviewer.judge("T1", self.check, self.results, lambda p: '{"verdict": "pass", "confidence": "alta", "evidence": "PRIVATE"}')
        doubt = reviewer.judge("T1", self.check, self.results, lambda p: '{"verdict": "pass", "confidence": "baja", "evidence": "?"}')
        self.assertEqual((sure["verdict"], doubt["verdict"]), ("pass", "unsure"))
        self.assertEqual(reviewer.judge("T1", self.check, self.results, lambda p: '{"verdict": "maybe"}')["verdict"], "unsure")


class Review(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.rdir = Path(self.tmp.name)
        self.repo = self.rdir / "repo"
        self.repo.mkdir()
        self.manifest = self.rdir / "manifest.json"
        self.manifest.write_text(json.dumps({"repository": str(self.repo), "snapshot_sha": "abc"}))
        self.check = {"purpose": "repo is private", "value": "inspect gh", "expected": "PRIVATE"}

    def run_review(self, answers, outputs=None):
        queue = list(answers)
        ran = []

        def run(argv, cwd, secrets):
            ran.append(argv)
            return {"exit_code": 0, "output": (outputs or "PRIVATE")}

        with patch("bt_scheduler_ops.bound_plan", return_value=object()), \
                patch("bt_attestation.manual_checks", return_value=[self.check]), \
                patch("bt_scheduler_ops.review_attempts", return_value=("att-1",)), \
                patch("bt_recovery_export._manifest_path", return_value=self.manifest), \
                patch("bt_manual_reviewer._extract"), \
                patch("bt_manual_reviewer.Path.home", return_value=Path(self.tmp.name)), \
                patch("bt_scheduler_ops.attest", return_value=["attested T1@att-1: «repo is private» -> x.json"]) as attest, \
                patch("bt_scheduler_decisions.write_verify_notes") as note, \
                patch("bt_interventions.record") as record:
            (Path(self.tmp.name) / ".cache").mkdir(exist_ok=True)
            lines = reviewer.review_task("p", "REQ-1", self.rdir, "T1", ask_model=lambda prompt: queue.pop(0), run=run)
        return lines, attest, note, record, ran

    def test_a_criterion_that_holds_is_attested_with_the_reviewers_evidence(self):
        lines, attest, note, record, ran = self.run_review(['{"commands": ["gh repo view dav033/david-ui"]}',
                                                           '{"verdict": "pass", "confidence": "alta", "evidence": "visibility PRIVATE"}'])
        attest.assert_called_once()
        self.assertEqual(attest.call_args.kwargs["by"], "manual-reviewer-auto")
        self.assertIn("visibility PRIVATE", attest.call_args.args[5])
        note.assert_not_called()
        self.assertEqual(ran[0][:3], ["gh", "repo", "view"])
        self.assertTrue(lines[0].startswith("attested"))

    def test_an_unsure_judge_that_names_what_is_missing_gets_it_and_then_decides(self):
        lines, attest, note, record, ran = self.run_review([
            '{"commands": ["cat a.md"]}',
            '{"verdict": "unsure", "confidence": "media", "evidence": "the file is cut", "more_commands": ["grep -n license a.md"]}',
            '{"verdict": "pass", "confidence": "alta", "evidence": "license text found"}'])
        attest.assert_called_once()
        self.assertEqual([a[0] for a in ran], ["cat", "grep"])

    def test_a_criterion_that_does_not_hold_goes_to_the_agent_as_a_verification_note_not_as_an_attestation(self):
        lines, attest, note, record, _ = self.run_review(['{"commands": ["gh repo view x"]}',
                                                         '{"verdict": "fail", "confidence": "alta", "evidence": "repository is empty"}'],
                                                        outputs="409 Git Repository is empty")
        attest.assert_not_called()
        self.assertIn("repository is empty", note.call_args.args[2])
        self.assertIn("does not hold", lines[0])

    def test_a_commandless_or_refused_plan_and_an_unsure_judge_leave_the_review_for_a_person(self):
        for answers in (['{"commands": []}'], ['{"commands": ["rm -rf /"]}'],
                        ['{"commands": ["git log"]}', '{"verdict": "unsure", "confidence": "alta", "evidence": "?"}']):
            lines, attest, note, _, _ = self.run_review(answers)
            attest.assert_not_called()
            note.assert_not_called()
            self.assertIn("stays for its owner", lines[0])


class Cycle(unittest.TestCase):
    def test_a_review_gets_one_pass_and_the_owner_resumes_only_after_an_attestation(self):
        with tempfile.TemporaryDirectory() as tmp:
            rdir = Path(tmp)
            request = {"id": "R:1", "source": "review", "task": "T1"}
            with patch("bt_scheduler_decisions.open_requests", return_value=[request]), \
                    patch("bt_scheduler_ops.on_hold", return_value=False), \
                    patch("bt_scheduler_ops.resume") as resume, \
                    patch("bt_manual_reviewer.review_task", return_value=["attested T1@a: x"]) as review:
                self.assertTrue(reviewer.cycle("p", "REQ-1", rdir))
                self.assertFalse(reviewer.cycle("p", "REQ-1", rdir))       # the same request is never reviewed twice
            review.assert_called_once()
            resume.assert_called_once()

    def test_it_can_be_switched_off(self):
        with patch("bt_config.get", return_value=False):
            self.assertFalse(reviewer.enabled())


if __name__ == "__main__":
    unittest.main()
