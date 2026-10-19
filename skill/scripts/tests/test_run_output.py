"""Provider stream output parsing."""
import json
import unittest
from run_case_support import SCRIPTS  # noqa: F401

class StreamJson(unittest.TestCase):
    def test_result_event_is_parsed_and_tool_output_is_not_a_limit(self):
        from bt_runsettle import detect_limit, parse_output
        events = [{"type": "system", "subtype": "init"},
                  {"type": "user", "message": {"content": "tool said: 429 quota exceeded"}},
                  {"type": "result", "subtype": "success", "is_error": False, "result": "all good",
                   "total_cost_usd": 0.42}]
        text = "\n".join(json.dumps(x) for x in events)
        self.assertEqual(parse_output(text), {"text": "all good", "is_error": False, "cost": 0.42, "limit": False})
        self.assertIsNone(detect_limit({"text": text, "rc": 1}))
        limit = text.rsplit("\n", 1)[0] + "\n" + json.dumps(
            {"type": "result", "is_error": True, "result": "Claude AI usage limit reached|1900000000"})
        self.assertEqual(detect_limit({"text": limit, "rc": 1}), 1900000000)
        cut = "\n".join(json.dumps(x) for x in events[:2]) + "\nError: rate limit hit"
        self.assertEqual(parse_output(cut)["text"], "Error: rate limit hit")
        killed = "\n".join(json.dumps(x) for x in events[:2]) + '\n{"type": "user", "message": "got 429 fr'
        self.assertIsNone(detect_limit({"text": killed, "rc": 1}))
