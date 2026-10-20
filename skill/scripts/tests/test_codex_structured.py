"""Codex runs under the scheduler in `--json` mode: the events carry tool activity and the token split."""
import unittest
from pathlib import Path

import bt_driver
import bt_runprompt
import bt_runsettle

START = '{"type":"thread.started","thread_id":"t"}\n{"type":"turn.started"}\n'
TOOL = ('{"type":"item.started","item":{"id":"i0","type":"command_execution","command":"echo hi","status":"in_progress"}}\n'
        '{"type":"item.completed","item":{"id":"i0","type":"command_execution","command":"echo hi","exit_code":0}}\n')
ANSWER = '{"type":"item.completed","item":{"id":"i1","type":"agent_message","text":"done: all tests pass"}}\n'
USAGE = ('{"type":"turn.completed","usage":{"input_tokens":47020,"cached_input_tokens":23296,'
         '"cache_write_input_tokens":0,"output_tokens":38,"reasoning_output_tokens":0}}\n')
LIMIT = "You hit your usage limit. Try again at Oct 21st, 2026 1:08 AM."


def codex(raw, rc=0):
    return bt_driver.driver_for("codex").normalize(raw, rc)


class CodexLaunch(unittest.TestCase):
    def argv(self, structured):
        argv, stdin = bt_runprompt.agent_argv({"agent": "codex"}, Path("/w"), "prompt", "gpt-6-luna", "high",
                                              structured=structured)
        return argv, stdin

    def test_json_flag_only_when_the_caller_needs_the_event_stream(self):
        self.assertNotIn("--json", self.argv(False)[0])
        argv, stdin = self.argv(True)
        self.assertIn("--json", argv)
        self.assertEqual((argv[-1], stdin), ("-", "prompt"))

    def test_other_providers_are_unchanged_by_the_flag(self):
        for agent in ("claude",):
            plain = bt_runprompt.agent_argv({"agent": agent}, Path("/w"), "p", "opus", "high")[0]
            structured = bt_runprompt.agent_argv({"agent": agent}, Path("/w"), "p", "opus", "high", structured=True)[0]
            self.assertEqual(plain, structured)

    def test_the_driver_passes_it_through_the_invocation(self):
        invocation = bt_driver.driver_for("codex").invocation("p", Path("/w"), "gpt-6-luna", "high", structured=True)
        self.assertIn("--json", invocation.argv)
        self.assertNotIn("--json", bt_driver.driver_for("codex").invocation("p", Path("/w"), "gpt-6-luna", "high").argv)


class CodexEvents(unittest.TestCase):
    def test_a_completed_turn_gives_the_final_message_the_split_usage_and_a_real_terminal_event(self):
        outcome = codex(START + TOOL + ANSWER + USAGE)
        self.assertEqual((outcome.status, outcome.terminal_event, outcome.text), ("completed", True, "done: all tests pass"))
        self.assertEqual(outcome.usage, {"input_tokens": 47020, "output_tokens": 38, "cache_read_tokens": 23296,
                                         "total_tokens": 47058})

    def test_a_clean_exit_without_the_end_of_turn_event_is_partial_not_completed(self):
        outcome = codex(START + TOOL + ANSWER)
        self.assertEqual((outcome.status, outcome.terminal_event), ("partial", False))

    def test_a_failed_turn_is_a_failure_and_a_usage_limit_is_a_limit_with_its_reset(self):
        failed = codex(START + '{"type":"turn.failed","error":{"message":"model unavailable"}}\n', 1)
        self.assertEqual((failed.status, failed.text), ("failed", "model unavailable"))
        limited = codex(START + '{"type":"error","message":"%s"}\n{"type":"turn.failed","error":{"message":"%s"}}\n'
                        % (LIMIT, LIMIT), 1)
        self.assertEqual(limited.status, "limit")
        self.assertEqual(limited.reset_epoch, 1792562880)

    def test_a_transient_error_followed_by_a_completed_turn_is_not_a_failure(self):
        outcome = codex(START + '{"type":"error","message":"Reconnecting... 1/5"}\n' + ANSWER + USAGE)
        self.assertEqual((outcome.status, outcome.text), ("completed", "done: all tests pass"))

    def test_text_mode_output_keeps_working(self):
        outcome = codex("did the work\ntokens used\n1,234\n")
        self.assertEqual((outcome.status, outcome.usage), ("completed", {"total_tokens": 1234}))
        self.assertEqual(bt_runsettle.codex_events("did the work\n"), [])
        self.assertEqual(bt_runsettle.codex_turn(START + TOOL), None)


if __name__ == "__main__":
    unittest.main()
