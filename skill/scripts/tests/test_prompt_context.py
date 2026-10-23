"""Prompt compression preserves exact evidence and can be disabled."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bt_attempt_history as history
import bt_config


class ConciseHistory(unittest.TestCase):
    def test_exact_failures_keep_first_latest_and_every_distinct_failure(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(bt_config, "STATE", Path(temp) / "state"):
            root = Path(temp)
            failure = "$ npm test -- --path /a/2\nexit code 2\n[FAIL] expected 3, not 4"
            texts = [failure] * 8 + [failure.replace("exit code 2", "exit code 3")]
            attempts = [f"a-{i}" for i in range(len(texts))]
            doc = {"tasks": {"T1": {"attempts": attempts}},
                   "attempts": {a: {"state": "rejected", "failure": "m6://x"} for a in attempts}}
            for attempt, text in zip(attempts, texts):
                history.record(root, "T1", attempt, text)
            text = history.prompt(root, "T1", doc)
            self.assertIn("same failure ×8", text)
            self.assertEqual(text.count(failure), 2)
            self.assertIn(texts[-1], text)
            self.assertIn("#1 a-0", text)
            self.assertIn("#8 a-7", text)
            bt_config.set_value("prompts.concise", False)
            self.assertNotIn("same failure ×8", history.prompt(root, "T1", doc))

    def test_line_budget_never_cuts_distinct_evidence_or_long_commands(self):
        from bt_prompt_context import compact

        command = "$ npm test " + "a/long/path/" * 200
        evidence = command + "\nexit code 29\n" + "\n".join(f"[FAIL] case {i}: not accepted" for i in range(300))
        self.assertEqual(compact(evidence), evidence)
        repeated = "[FAIL] not ready /a/2, exit code 7\n" * 100
        result = compact(repeated)
        self.assertIn("[FAIL] not ready /a/2, exit code 7", result)
        self.assertIn("×100", result)
        self.assertLess(len(result), len(repeated) // 10)


class PromptSwitches(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        patcher = patch.object(bt_config, "STATE", self.root / "state")
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_both_boolean_switches_default_on_validate_and_roundtrip(self):
        for key in ("prompts.rtk", "prompts.concise"):
            self.assertIs(bt_config.get(key), True)
            bt_config.set_value(key, False)
            self.assertIs(bt_config.get(key), False)
            with self.assertRaises(bt_config.ConfigError):
                bt_config.set_value(key, "false")

    def test_model_instructions_shorten_without_changing_schema_or_system_rules(self):
        import bt_attempt_analyst as analyst
        import bt_block_agent as diagnosis
        import bt_manual_reviewer as reviewer
        from bt_prompt_context import instruction

        for original, shorter in ((analyst.PROMPT, analyst.CONCISE_PROMPT),
                                  (diagnosis.PROMPT, diagnosis.CONCISE_PROMPT),
                                  (reviewer.PLAN_PROMPT, reviewer.CONCISE_PLAN_PROMPT),
                                  (reviewer.JUDGE_PROMPT, reviewer.CONCISE_JUDGE_PROMPT)):
            bt_config.set_value("prompts.concise", True)
            self.assertLess(len(instruction(original, shorter)), len(original))
            bt_config.set_value("prompts.concise", False)
            self.assertEqual(instruction(original, shorter), original)
        self.assertEqual(diagnosis.PROMPT.split("How the system works")[1],
                         diagnosis.CONCISE_PROMPT.split("How the system works")[1])

    def test_analyst_preserves_evidence_past_old_total_budget(self):
        import bt_attempt_analyst as analyst
        import bt_scheduler_decisions as decisions

        evidence = "unique context\n" * 1200 + "$ python3 /a/test.py\nexit code 17\n[FAIL] not ready"
        decisions.write_verify_notes(self.root, "T1", evidence)
        result = analyst.bundle(self.root, "T1", {}, {})
        self.assertIn("$ python3 /a/test.py\nexit code 17\n[FAIL] not ready", result)
        bt_config.set_value("prompts.concise", False)
        self.assertLessEqual(len(analyst.bundle(self.root, "T1", {}, {})), analyst.MAX_CONTEXT)

    def test_history_records_complete_new_failures(self):
        evidence = "context\n" * 500 + "$ npm test\nexit code 19\n[FAIL] not ready /src/a.py"
        history.record(self.root, "T1", "a1", evidence)
        run = {"tasks": {"T1": {"attempts": ["a1"]}}, "attempts": {"a1": {"state": "rejected"}}}
        self.assertIn(evidence, history.prompt(self.root, "T1", run))

    def test_reviewer_evidence_stays_exact_in_both_modes(self):
        import bt_manual_reviewer as reviewer

        outputs = "[FAIL] not ready /a/2, exit code 7\n" * 200
        results = [{"command": "python3 /a/test.py", "exit_code": 7, "output": outputs}]
        captured = []
        def ask(prompt):
            captured.append(prompt)
            return '{"verdict":"fail","confidence":"alta","evidence":"not ready"}'
        for value in (True, False):
            bt_config.set_value("prompts.concise", value)
            reviewer.judge("T1", {"purpose": "ready", "expected": "yes"}, results, ask)
            self.assertIn("$ python3 /a/test.py\n(exit 7)\n" + outputs, captured[-1])
        self.assertLess(len(captured[0]), len(captured[1]))

    def test_repair_excerpt_keeps_long_commands_and_each_distinct_error(self):
        import bt_scheduler_healing as healing

        command = "$ python3 " + "/a/" * 100 + "test.py"
        errors = [f"[FAIL] not ready {i}: /src/a.py" for i in range(30)]
        evidence = command + "\nexit code 27\n" + "\n".join(errors + errors)
        result = healing.excerpt(evidence)
        self.assertIn(command, result)
        self.assertIn("exit code 27", result)
        for error in errors:
            self.assertEqual(result.splitlines().count(error), 1)
        bt_config.set_value("prompts.concise", False)
        self.assertLessEqual(len(healing.excerpt(evidence)), 700)

    def test_legacy_retry_log_deduplicates_only_identical_text(self):
        from bt_runprompt import _recent_log

        state = {"log": [{"task": "T1", "session": i, "result": "fail", "summary": text}
                         for i, text in enumerate(("exit code 2", "exit code 2", "exit code 3"), 1)]}
        text = "\n".join(_recent_log(state, "T1"))
        self.assertIn("same as session 1", text)
        self.assertIn("exit code 3", text)
        bt_config.set_value("prompts.concise", False)
        self.assertEqual("\n".join(_recent_log(state, "T1")).count("exit code 2"), 2)

    def test_repair_excerpt_preserves_multiline_diagnostic_context(self):
        import bt_scheduler_healing as healing

        evidence = ('$ python3 scripts/test_policy.py\nexit code 1\nTraceback (most recent call last):\n'
                    '  File "/src/policy.py", line 42, in check\n    assert allowed is False\n'
                    'expected: permission denied\nactual: allowed\nAssertionError: mismatch')
        self.assertEqual(healing.excerpt(evidence), evidence)

    def test_line_compaction_never_expands_short_repetitions(self):
        from bt_prompt_context import compact

        evidence = "\n".join(f"line {i}\n\n" for i in range(50))
        self.assertLessEqual(len(compact(evidence)), len(evidence))
