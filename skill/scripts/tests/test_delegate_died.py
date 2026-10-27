import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bt_delegate


class DeadClaimant(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        patcher = patch.object(bt_delegate, "DIR", Path(self.tmp.name))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.d = Path(self.tmp.name) / "D-1"
        self.d.mkdir()
        (self.d / "TASK.json").write_text(json.dumps({"id": "D-1", "agent": "codex"}))
        (self.d / "session.log").write_text("")

    def test_a_claim_whose_process_is_gone_and_left_no_outcome_is_a_failure_not_a_wait(self):
        (self.d / "CLAIMED").write_text(str(2 ** 22 + 4321))                    # nobody has this pid
        out = bt_delegate.summary("D-1")
        self.assertEqual(out["status"], "failed")
        self.assertIn("process died", out["summary"])

    def test_a_live_or_unclaimed_delegation_keeps_waiting(self):
        self.assertEqual(bt_delegate.summary("D-1")["status"], "running_or_pending")        # queued, never claimed
        (self.d / "CLAIMED").write_text(str(os.getpid()))
        self.assertEqual(bt_delegate.summary("D-1")["status"], "running_or_pending")
        (self.d / "CLAIMED").write_text("garbage")
        self.assertEqual(bt_delegate.summary("D-1")["status"], "running_or_pending")

    def test_an_outcome_always_wins_over_a_dead_claim(self):
        (self.d / "CLAIMED").write_text(str(2 ** 22 + 4321))
        (self.d / "OUTCOME.json").write_text(json.dumps({"id": "D-1", "status": "claimed", "rc": 0}))
        self.assertEqual(bt_delegate.summary("D-1")["status"], "claimed")


if __name__ == "__main__":
    unittest.main()
