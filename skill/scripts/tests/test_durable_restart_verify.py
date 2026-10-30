"""D-171 end to end: an engine killed in the middle of a verification is followed by an engine that verifies the same
snapshot again, without an owner decision and without a new agent attempt (REQ-030 audit, 2026-10-29).

test_durable_m6_restart proves the store rule (an interrupted request is queued once again); this proves the wiring: the
engine recovers the store before DBOS re-runs the verify step. A slow check (8 s) holds M6's request in `running`; the
engine is SIGKILLed then, with its sandbox."""
from __future__ import annotations

import sqlite3
import sys
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import durable_support as lab_support
from bt_contracts.execution import RunRef
from durable_support import task, wait_until
from test_durable_e2e import FAST, EngineCase

SLOW_CHECK = ("import pathlib, sys, time\ntime.sleep(8)\n"
              "sys.exit(0 if pathlib.Path('out.txt').read_text() == 'good\\n' else 1)\n")


class RestartMidVerification(EngineCase):
    def retried_running_verifications(self) -> int:
        store = self.lab.state / "m6-quality.sqlite3"
        if not store.exists():
            return 0
        with sqlite3.connect(f"file:{store}?mode=ro", uri=True) as db:
            return db.execute("SELECT count(*) FROM requests r JOIN verification_retries v "
                              "ON r.idempotency_key=v.request_key WHERE r.state='running'").fetchone()[0]

    def running_verifications(self) -> int:
        store = self.lab.state / "m6-quality.sqlite3"
        if not store.exists():
            return 0
        with sqlite3.connect(f"file:{store}?mode=ro", uri=True) as db:
            return db.execute("SELECT count(*) FROM requests WHERE state = 'running'").fetchone()[0]

    def test_a_verification_cut_by_an_engine_kill_runs_again_in_the_next_engine(self):
        (self.lab.repo / "checks" / "check_slow.py").write_text(SLOW_CHECK)
        lab_support.git(self.lab.repo, "add", "-A")
        lab_support.git(self.lab.repo, "commit", "-q", "-m", "a slow check")
        run = RunRef.model_validate(self.lab.freeze([task("T1", check="python3 checks/check_slow.py")]))
        self.start_engine()
        self.client.start(run, FAST)
        wait_until(lambda: self.running_verifications() == 1, 120, interval=0.2, what="the verification to run")
        time.sleep(1.0)
        self.kill_engine()                                   # the whole process group: the engine and its sandbox
        self.assertEqual(self.running_verifications(), 1)    # what a killed engine leaves behind
        self.start_engine()
        status = self.settled(run, timeout=240)
        self.assertEqual(status["summary"]["status"], "completed", status)
        self.assertFalse(status["tasks"]["T1"]["decision"])
        self.assertEqual(len(self.lab.launches()), 1)        # verified again, not run again
        with sqlite3.connect(f"file:{self.lab.state / 'm6-quality.sqlite3'}?mode=ro", uri=True) as db:
            retried = db.execute("SELECT count(*) FROM verification_retries").fetchone()[0]
        self.assertEqual(retried, 1)                         # recovered once by the engine's start (D-171)

    def test_two_engine_cuts_reverify_the_same_snapshot_within_the_task_repair_budget(self):
        (self.lab.repo / "checks" / "check_slow.py").write_text(SLOW_CHECK)
        lab_support.git(self.lab.repo, "add", "-A")
        lab_support.git(self.lab.repo, "commit", "-q", "-m", "a slow check")
        run = RunRef.model_validate(self.lab.freeze([task("T1", check="python3 checks/check_slow.py")]))
        self.start_engine()
        self.client.start(run, FAST)
        wait_until(lambda: self.running_verifications() == 1, 120, interval=0.2, what="first verification")
        self.kill_engine()
        self.start_engine()
        wait_until(lambda: self.retried_running_verifications() == 1, 120, interval=0.2,
                   what="same request running after startup recovery")
        self.kill_engine()
        self.start_engine()
        status = self.settled(run, timeout=240)
        self.assertEqual(status["summary"]["status"], "completed", status)
        self.assertFalse(status["tasks"]["T1"]["decision"])
        self.assertEqual(len(self.lab.launches()), 1)
        with sqlite3.connect(f"file:{self.lab.state / 'm6-quality.sqlite3'}?mode=ro", uri=True) as db:
            rows = db.execute("SELECT idempotency_key,state FROM requests ORDER BY idempotency_key").fetchall()
        self.assertEqual(len(rows), 2, rows)
        self.assertEqual([state for _, state in rows], ["needs_review", "complete"])
        self.assertTrue(rows[1][0].endswith(":relaxed"), rows)


if __name__ == "__main__":
    unittest.main()
