"""The engine stops on SIGTERM in seconds, without losing work (REQ-030 audit).

Every restart of bt-durable.service on 2026-10-28/29 ended in «State 'stop-sigterm' timed out. Killing»: DBOS was
destroyed at once, but the interpreter then joined DBOS's non-daemon workflow threads, and a run workflow waits in
`DBOS.recv` for up to `run_poll_seconds` (an open owner decision for `owner_wait_seconds`, 24 h). The test holds a run in
exactly that wait while its agent runs, stops the engine, and proves the process is gone long before the wait ends, and
that the next engine finishes the run with the same agent process (adopted, not launched again)."""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from bt_contracts.execution import RunRef
from bt_durable.settings import Settings
from durable_support import task, wait_until
from test_durable_e2e import EngineCase

# the run loop waits 10 min for news and a decision a day: far longer than any acceptable stop
WAITING = Settings(max_parallel=1, poll_seconds=0.5, run_poll_seconds=600, owner_wait_seconds=24 * 3600)
STOP_SECONDS = 15


class EngineStops(EngineCase):
    def test_sigterm_ends_the_engine_in_seconds_and_the_next_engine_finishes_the_run(self):
        run = RunRef.model_validate(self.lab.freeze([task("T1", scenario="slow")]))
        with mock.patch.dict(os.environ, {"FAKE_SLOW_SECONDS": "12"}):
            self.start_engine()
        self.client.start(run, WAITING)
        wait_until(lambda: len(self.lab.launches()) >= 1, 90, what="the agent to start")
        time.sleep(1.0)                                   # the run workflow is now in DBOS.recv(600)
        started = time.monotonic()
        self.engine.send_signal(signal.SIGTERM)
        try:
            code = self.engine.wait(60)
        except subprocess.TimeoutExpired:
            self.fail("the engine did not exit within 60 s of SIGTERM: " +
                      (self.lab.root / "engine.log").read_text()[-3000:])
        elapsed = time.monotonic() - started
        self.assertLess(elapsed, STOP_SECONDS, f"the engine took {elapsed:.1f} s to stop")
        self.assertEqual(code, 0, (self.lab.root / "engine.log").read_text()[-3000:])

        self.start_engine()                               # recovery: the same run, the same agent process
        status = self.settled(run, timeout=180)
        self.assertEqual(status["summary"]["status"], "completed", status)
        self.assertEqual(len(self.lab.launches()), 1, "the agent must be adopted after the restart, not started again"
                         + why_launched(self.lab))


def why_launched(lab) -> str:
    """What a second launch needs to be explained: each start and the engine's decisions about its attempts. The one
    loaded-regression failure of this test (2026-10-30) left only «2 != 1» and a deleted lab."""
    events = [{k: e.get(k) for k in ("event", "attempt_key", "action", "code", "reason", "workflow_status") if e.get(k)}
              for e in lab.telemetry()
              if e.get("event") in ("attempt_started", "recovery_decision", "orphan_reaped", "decision_requested")]
    starts = [{k: x.get(k) for k in ("task", "at", "has_note", "remediation", "cwd")} for x in lab.launches()]
    return f"\nlaunches: {starts}\nevents: {events}\nengine log: {(lab.root / 'engine.log').read_text()[-2000:]}"


class ManyRestarts(EngineCase):
    """DBOS counts every dispatch of a workflow, recoveries included, and never resets the count; past
    `max_recovery_attempts` (100 by default) it dead-letters the workflow. bt.run and bt.task live for days through
    every deploy (pictures REQ-021 r25 was at 7 after one day, 2026-10-29), so they must not have that limit."""

    def test_a_run_recovered_more_than_a_hundred_times_still_runs(self):
        run = RunRef.model_validate(self.lab.freeze([task("T1", scenario="slow")]))
        with mock.patch.dict(os.environ, {"FAKE_SLOW_SECONDS": "10"}):
            self.start_engine()
        self.client.start(run, WAITING)
        wait_until(lambda: len(self.lab.launches()) >= 1, 90, what="the agent to start")
        self.engine.send_signal(signal.SIGTERM)
        self.engine.wait(60)
        import sqlite3
        with sqlite3.connect(self.lab.state / "dbos.sqlite3") as db:   # as after 150 deploys
            changed = db.execute("UPDATE workflow_status SET recovery_attempts = 150 WHERE status = 'PENDING' "
                                 "AND name IN ('bt.run', 'bt.task')").rowcount
        self.assertEqual(changed, 2)
        self.start_engine()

        def ended():
            row = self.client.client.list_workflows(workflow_ids=[f"bt:{run.run_id}"], load_input=False,
                                                    load_output=False)[0]
            return row.status if row.status not in ("PENDING", "ENQUEUED") else None
        self.assertEqual(wait_until(ended, 180, interval=0.5, what="the run to end"), "SUCCESS")
        self.assertEqual(self.client.status(run)["summary"]["status"], "completed")


if __name__ == "__main__":
    unittest.main()
