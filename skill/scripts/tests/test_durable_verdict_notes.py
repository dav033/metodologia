"""One history line per verdict (REQ-030 audit, 2026-10-29). The durable verify step that runs again after an engine
restart gets M6's stored verdict back (M6Verifier.verify -> on_verdict once more), and every such re-run appended the
same failure to `RUN.notes/<task>.history.jsonl`, which the next attempt's brief and the healing read as one more
failed attempt. Real files; the outcome is the shape M6Verifier hands over."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from bt_contracts.execution import AttemptRef, RunRef, VerifyOutcome, VerifyStatus
from bt_durable.service import record_verdict

DIGEST = "FAIL python3 checks/check_out.py\nout.txt is missing"


class VerdictNotes(unittest.TestCase):
    def setUp(self):
        self.rdir = Path(tempfile.mkdtemp(prefix="bt-verdict-notes-")) / "REQ-900-x"
        (self.rdir / "plan-revisions").mkdir(parents=True)
        run = RunRef(project="proj", req="REQ-900", plan_id="REQ-900", revision=1, plan_sha256="0" * 64,
                     plan_path=self.rdir / "plan-revisions" / "PLAN.r1.json")
        self.attempt = AttemptRef(run=run, task_id="T1", number=1, workflow_id="bt:proj:REQ-900:r1:T1:k1")
        self.history = self.rdir / "RUN.notes" / "T1.history.jsonl"

    def fail(self, ref: str) -> VerifyOutcome:
        return VerifyOutcome(status=VerifyStatus.FAIL, reason_code="CHECK_FAILED", result_ref=ref, digest=DIGEST)

    def rows(self) -> list[dict]:
        return [json.loads(line) for line in self.history.read_text().splitlines()]

    def test_a_verify_step_run_again_reports_its_stored_verdict_once(self):
        record_verdict(self.attempt, self.fail("m6://evidence/1"))
        record_verdict(self.attempt, self.fail("m6://evidence/1"))          # the step again, after a restart
        self.assertEqual(len(self.rows()), 1)

    def test_other_verdicts_of_the_same_attempt_are_each_recorded(self):
        record_verdict(self.attempt, self.fail("m6://evidence/1"))
        record_verdict(self.attempt, self.fail("m6://evidence/2"), "relaxed")    # the bounded environment repair
        record_verdict(self.attempt, self.fail("m6://evidence/3"), "owner2")     # the owner's re-verification
        self.assertEqual(len(self.rows()), 3)
        self.assertEqual({row["attempt"] for row in self.rows()}, {self.attempt.attempt_key})


if __name__ == "__main__":
    unittest.main()
