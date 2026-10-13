import json
import tempfile
import unittest
from pathlib import Path

from collect import parse_session


class UsageCollectionTests(unittest.TestCase):
    def make_session(self, completed=True, duplicate=False, bad_total=False):
        root = Path(tempfile.mkdtemp(prefix="metodologia-usage-fixture-"))
        path = root / "session.jsonl"
        usage = {"input_tokens": 100, "cached_input_tokens": 70, "output_tokens": 20,
                 "reasoning_output_tokens": 4, "total_tokens": 121 if bad_total else 120}
        token = {"type": "event_msg", "payload": {"type": "token_count", "info": {
            "total_token_usage": usage, "last_token_usage": usage}}}
        events = [
            {"type": "session_meta", "payload": {"agent_path": "/root/trial"}},
            {"type": "response_item", "payload": {"type": "custom_tool_call", "name": "exec", "input": "read"}},
            token,
            {"type": "response_item", "payload": {"type": "message", "role": "assistant", "phase": "final_answer",
             "content": [{"type": "output_text", "text": "Saved evidence failed."}]}},
        ]
        if duplicate:
            events.append(token)
        if completed:
            events.append({"type": "event_msg", "payload": {"type": "task_complete"}})
        path.write_text("\n".join(json.dumps(event) for event in events))
        return path

    def test_extracts_actual_usage_without_adding_cached_input_twice(self):
        result = parse_session(self.make_session(), {"/root/trial"})
        self.assertEqual(result["usage"]["total_tokens"], 120)
        self.assertEqual(result["uncached_input"], 30)
        self.assertEqual(result["call_count"], 1)
        self.assertEqual(result["answer"], "Saved evidence failed.")

    def test_duplicate_usage_event_does_not_double_count(self):
        result = parse_session(self.make_session(duplicate=True), {"/root/trial"})
        self.assertEqual(len(result["records"]), 1)

    def test_incomplete_run_is_not_reported_complete(self):
        self.assertFalse(parse_session(self.make_session(completed=False), {"/root/trial"})["completed"])

    def test_invalid_totals_fail_loudly(self):
        with self.assertRaises(ValueError):
            parse_session(self.make_session(bad_total=True), {"/root/trial"})

    def test_unrelated_sessions_are_excluded(self):
        self.assertIsNone(parse_session(self.make_session(), {"/root/other"}))


if __name__ == "__main__":
    unittest.main()
