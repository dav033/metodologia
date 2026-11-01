"""An answer recorded by the PREVIOUS engine replays its whole-task count; the next answer opens a window (D-269).

pictures REQ-021 r32 T3.91: once the attempt budget was spent, each answered decision bought exactly one attempt, so a
new, different failure went straight back to the owner. The previous engine (exported from git) runs a task with
`max_attempts` 2: a1, a2, d1; the owner's retry buys a3 only, which escalates d2 at once. The engine is SIGKILLed while
d2 is open. The current engine recovers the same workflow: the recorded decision after a3 (no
`bt-task-answer-opens-attempt-window` marker, `bt.emit_decision` recorded) replays as it was, and the answer given
after the upgrade opens a fresh window of two attempts, a4 and a5, before d3."""
from __future__ import annotations

import os
import signal
import tempfile
import unittest
from pathlib import Path

import test_durable_upgrade as upgrade
from bt_contracts.execution import RunRef
from bt_contracts.owner import OwnerAnswer
from durable_support import export_engine, task, wait_until
from test_durable_e2e import FAST

PREVIOUS = os.environ.get("BT_PREVIOUS_ANSWER_WINDOW_ENGINE_COMMIT", "2ac6c4031")   # main before D-269


class AnswerWindowAfterUpgrade(upgrade.EngineUpgrade):
    test_a_run_started_by_the_previous_engine_continues_on_the_new_one = None      # the parent's own scenario

    def decision(self, run, request_id: str) -> dict:
        return wait_until(lambda: ((self.client.status(run)["tasks"].get("T1") or {}).get("decision") or {})
                          .get("request_id") == request_id and self.client.status(run)["tasks"]["T1"]["decision"],
                          240, interval=0.5, what=f"decision {request_id}")

    def test_an_answer_recorded_by_the_previous_engine_replays_and_the_next_one_opens_a_window(self):
        from bt_durable.client import Client
        scripts = export_engine(PREVIOUS, Path(tempfile.mkdtemp(prefix="bt-previous-", dir=self.lab.root)))
        run = RunRef.model_validate(self.lab.freeze([task("T1", scenario="neverfix")]))
        two_attempts = FAST.model_copy(update={"budget": FAST.budget.model_copy(update={"max_attempts": 2})})
        previous = self.spawn_previous(scripts)
        wait_until(lambda: (self.lab.state / "dbos.sqlite3").exists(), 60, what="DBOS database")
        self.client = Client(self.lab.database_url)
        self.addCleanup(self.client.close)

        def started():
            try:                                  # the file exists before the engine finished creating the schema
                return self.client.start(run, two_attempts)
            except Exception:  # noqa: BLE001
                return None
        wait_until(started, 60, interval=0.5, what="the previous engine's schema")
        self.decision(run, "T1:d1")
        self.assertEqual(len(self.lab.launches()), 2)
        self.client.answer(run, "T1", OwnerAnswer(request_id="T1:d1", action="retry"))
        old = self.decision(run, "T1:d2")
        self.assertEqual(len(self.lab.launches()), 3)                          # the previous engine: one attempt
        self.assertEqual(old["reason"], "the task used its attempts")
        os.killpg(previous.pid, signal.SIGKILL)
        previous.wait(10)

        self.start_engine()                                                    # the current code, same database
        self.client.answer(run, "T1", OwnerAnswer(request_id="T1:d2", action="retry"))
        new = self.decision(run, "T1:d3")
        self.assertEqual(new["reason"], "the task used its attempts since the last answered decision")
        self.client.answer(run, "T1", OwnerAnswer(request_id="T1:d3", action="stop"))
        status = self.settled(run, timeout=240)

        rows = self.client.workflows(f"bt:{run.run_id}")
        self.assertFalse([r.workflow_id for r in rows if r.status == "ERROR"], [(r.workflow_id, r.status) for r in rows])
        self.assertEqual(status["summary"]["status"], "blocked", status)
        self.assertEqual(len(self.lab.launches()), 5)                # a4 and a5; the replay launched nothing again


if __name__ == "__main__":
    unittest.main()
