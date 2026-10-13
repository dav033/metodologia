"""Usage-limit detection: reset announcements are honoured, wrong parses are bounded."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import bt_runsettle as settle  # noqa: E402  (imports bt_core: this file must sort after test_marathon.py)

AGY_QUOTA = json.dumps({"event": "result", "result": {
    "status": "ERROR", "error": "Individual quota reached. Please upgrade your subscription to increase your limits. "
                                "Resets in 166h43m25s."}})


class ResetParsing(unittest.TestCase):
    def test_relative_resets(self):
        self.assertEqual(settle.reset_epoch("Resets in 166h43m25s.", now=1000), 1000 + 166 * 3600 + 43 * 60 + 25)
        self.assertEqual(settle.reset_epoch("limit resets in 45m", now=0), 45 * 60)
        self.assertEqual(settle.reset_epoch("Resets in 2 days 3 hours", now=0), 2 * 86400 + 3 * 3600)

    def test_no_announcement_is_zero(self):
        self.assertEqual(settle.reset_epoch("something unrelated", now=5), 0)
        self.assertEqual(settle.reset_epoch("", now=5), 0)

    def test_antigravity_quota_error_is_a_limit_with_its_reset(self):
        info = {"rc": 1, "text": AGY_QUOTA, "seconds": 6, "timed_out": False, "stopped": False}
        epoch = settle.detect_limit(info)
        self.assertIsNotNone(epoch)
        self.assertGreater(epoch - __import__("time").time(), 165 * 3600)

    def test_a_successful_run_mentioning_a_quota_is_not_a_limit(self):
        ok = json.dumps({"event": "result", "result": {"status": "SUCCESS", "response": "quota resets in 3h"}})
        self.assertIsNone(settle.detect_limit({"rc": 0, "text": ok, "seconds": 1, "timed_out": False, "stopped": False}))


if __name__ == "__main__":
    unittest.main()
