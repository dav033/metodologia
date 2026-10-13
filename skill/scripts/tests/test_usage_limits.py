"""Usage-limit detection: reset announcements are honoured, wrong parses are bounded."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import bt_runsettle as settle  # noqa: E402  (imports bt_core: this file must sort after test_marathon.py)

QUOTA_ERROR = json.dumps({"event": "result", "result": {
    "status": "ERROR", "error": "Individual quota reached. Please upgrade your subscription to increase your limits. "
                                "Resets in 166h43m25s."}})


class ResetParsing(unittest.TestCase):
    def test_relative_resets(self):
        self.assertEqual(settle.reset_epoch("Resets in 166h43m25s.", now=1000), 1000 + 166 * 3600 + 43 * 60 + 25)
        self.assertEqual(settle.reset_epoch("limit resets in 45m", now=0), 45 * 60)
        self.assertEqual(settle.reset_epoch("Resets in 2 days 3 hours", now=0), 2 * 86400 + 3 * 3600)

    def test_absolute_resets_in_local_time(self):
        import datetime as dt
        now = dt.datetime(2026, 10, 12, 22, 36).timestamp()
        at = lambda text: dt.datetime.fromtimestamp(settle.absolute_reset_epoch(text, now))  # noqa: E731
        codex = ("ERROR: You've hit your usage limit. Upgrade to Pro, visit the usage page to purchase more credits or "
                 "try again at Oct 13th, 2026 1:08 AM.")
        self.assertEqual(at(codex), dt.datetime(2026, 10, 13, 1, 8))
        self.assertEqual(at("limit reached, try again at 3pm"), dt.datetime(2026, 10, 13, 15, 0))  # next occurrence
        self.assertEqual(at("resets at 11:30 PM"), dt.datetime(2026, 10, 12, 23, 30))
        self.assertEqual(at("Your limit will reset at Oct 20, 9am"), dt.datetime(2026, 10, 20, 9, 0))
        for text in ("try again at 5", "look at 3 files", "", "try again at Foo 99th 1:08 AM"):
            self.assertEqual(settle.absolute_reset_epoch(text, now), 0, text)

    def test_a_failed_codex_session_with_an_absolute_reset_is_a_limit_until_then(self):
        import time
        text = ("lots of transcript\nERROR: You've hit your usage limit. Upgrade to Pro or try again at "
                + time.strftime("%b %d, %Y %I:%M %p", time.localtime(time.time() + 3 * 3600)) + ".\ntokens used\n31,792\n")
        epoch = settle.detect_limit({"rc": 1, "text": text, "seconds": 42, "timed_out": False, "stopped": False})
        self.assertTrue(2.9 * 3600 < epoch - time.time() < 3.1 * 3600)
        self.assertIn("usage limit", settle.limit_line(text))
        self.assertNotIn("tokens used", settle.limit_line(text))

    def test_claude_session_limit_message_is_a_limit_with_its_reset(self):
        """Seen for real (maros-lab REQ-001): it was read as a plain failure, burned attempts, climbed tiers and
        blocked an audit."""
        import datetime as dt
        text = "You've hit your session limit · resets 12:50am (America/Bogota)"
        now = dt.datetime(2026, 10, 12, 23, 40).timestamp()
        self.assertEqual(dt.datetime.fromtimestamp(settle.absolute_reset_epoch(text, now)), dt.datetime(2026, 10, 13, 0, 50))
        result = json.dumps({"type": "result", "subtype": "success", "is_error": True, "result": text})
        epoch = settle.detect_limit({"rc": 1, "text": result, "seconds": 3, "timed_out": False, "stopped": False})
        self.assertTrue(epoch and epoch > 0)
        for other in ("You've hit your weekly limit · resets Oct 20, 9am", "Opus limit reached", "5-hour limit · resets 3pm"):
            self.assertIsNotNone(settle.detect_limit({"rc": 1, "text": other, "seconds": 1, "timed_out": False,
                                                      "stopped": False}), other)
        self.assertEqual(settle.absolute_reset_epoch("the cache resets 3 files", now), 0)

    def test_structured_usage_limit_verdict_is_enough_whatever_the_wording(self):
        result = json.dumps({"type": "result", "is_error": True, "api_error_status": 429,
                             "api_error": "usage_limit_reached", "result": "Come back later."})
        self.assertIsNotNone(settle.detect_limit({"rc": 1, "text": result, "seconds": 1, "timed_out": False,
                                                  "stopped": False}))

    def test_provider_capacity_error_is_not_the_agents_failure(self):
        """Seen for real (maros-lab FINAL on Codex): counted as a failed attempt. It is the account's problem for a
        while, so it cools that account down with the default cooldown and the router moves on."""
        text = "work\nERROR: Selected model is at capacity. Please try a different model.\ntokens used\n105,080\n"
        self.assertEqual(settle.detect_limit({"rc": 1, "text": text, "seconds": 509, "timed_out": False,
                                              "stopped": False}), 0)

    def test_no_announcement_is_zero(self):
        self.assertEqual(settle.reset_epoch("something unrelated", now=5), 0)
        self.assertEqual(settle.reset_epoch("", now=5), 0)

    def test_provider_quota_error_is_a_limit_with_its_reset(self):
        info = {"rc": 1, "text": QUOTA_ERROR, "seconds": 6, "timed_out": False, "stopped": False}
        epoch = settle.detect_limit(info)
        self.assertIsNotNone(epoch)
        self.assertGreater(epoch - __import__("time").time(), 165 * 3600)

    def test_a_successful_run_mentioning_a_quota_is_not_a_limit(self):
        ok = json.dumps({"event": "result", "result": {"status": "SUCCESS", "response": "quota resets in 3h"}})
        self.assertIsNone(settle.detect_limit({"rc": 0, "text": ok, "seconds": 1, "timed_out": False, "stopped": False}))


if __name__ == "__main__":
    unittest.main()
