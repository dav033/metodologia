"""A run that ended blocked is reopened by the owner's retry (REQ-030; pictures REQ-021 ended blocked on its T2.7 audit
and a retry sent to its ended run workflow would never have been read).

End to end with real git, the fake `claude` through the real driver, M6 and DBOS: T1 cannot pass without the owner's
help, the owner stops it, the run ends blocked with T2 never started. `retry_task` forks the ended run workflow at its
final summary into `bt:<run>@2` (client.reopen); the new incarnation replays the history, waits for the command instead
of ending (`bt-run-reopened`), retries T1 with the owner's note, runs T2 and completes. Status and the panels' projection
follow the current incarnation.

    PYTHONPATH=skill/scripts:skill/scripts/tests uv run python -m unittest test_durable_reopen
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from bt_contracts.execution import RunRef
from bt_contracts.owner import OwnerAnswer
from durable_support import task, wait_until
from test_durable_e2e import FAST, EngineCase

ONE_ATTEMPT = FAST.model_copy(update={"max_parallel": 1, "budget": FAST.budget.model_copy(update={"max_attempts": 1})})


class ReopenEndedRun(EngineCase):
    def telemetry(self) -> list[dict]:
        path = self.lab.state / "telemetry.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def test_a_retry_reopens_a_run_that_ended_blocked_and_it_completes(self):
        run = RunRef.model_validate(self.lab.freeze([task("T1", scenario="needsowner"),
                                                     task("T2", scenario="own", after=["T1"])]))
        self.start_engine()
        self.client.start(run, ONE_ATTEMPT)
        decision = wait_until(lambda: (self.client.status(run)["tasks"].get("T1") or {}).get("decision"), 180,
                              interval=0.5, what="T1 to ask the owner")
        self.client.answer(run, "T1", OwnerAnswer(request_id=decision["request_id"], action="stop"))
        ended = self.settled(run, timeout=180)
        self.assertEqual((ended["workflow_id"], ended["summary"]["status"]), (f"bt:{run.run_id}", "blocked"), ended)
        self.assertNotIn("T2", ended["summary"]["tasks"])

        self.client.command(run, "retry_task", task_id="T1", note="OWNER-RETRY: write the good output this time")
        reopened = f"bt:{run.run_id}@2"
        self.assertEqual(self.client.current_run_workflow(run), reopened)
        status = wait_until(lambda: (lambda s: s if s["workflow_status"] == "SUCCESS" else None)(self.client.status(run)),
                            240, interval=0.5, what="the reopened run to finish")
        self.assertEqual((status["workflow_id"], status["summary"]["status"]), (reopened, "completed"), status)
        self.assertEqual([item["task"] for item in self.lab.launches()], ["T1", "T1", "T2"])
        events = [row["event"] for row in self.telemetry()]
        self.assertEqual(events.count("run_reopened"), 1)
        rows = self.client.workflows(f"bt:{run.run_id}")
        self.assertFalse([r.workflow_id for r in rows if r.status == "ERROR"], [(r.workflow_id, r.status) for r in rows])
        # the panels' projection reads the current incarnation
        from bt_durable import projection
        doc = projection.build(self.client.client, run, projection.load_plan(run))
        self.assertEqual((doc["workflow_id"], doc["status"]), (reopened, "completed"))
        self.assertEqual({t["id"]: t["state"] for t in doc["tasks"]}, {"T1": "completed", "T2": "completed"})

    def test_a_retry_of_a_live_run_does_not_fork_it(self):
        run = RunRef.model_validate(self.lab.freeze([task("T1", scenario="needsowner")]))
        self.start_engine()
        self.client.start(run, ONE_ATTEMPT)
        wait_until(lambda: (self.client.status(run)["tasks"].get("T1") or {}).get("decision"), 180, interval=0.5,
                   what="T1 to ask the owner")
        self.assertEqual(self.client.reopen(run), f"bt:{run.run_id}")          # still running: nothing to reopen
        self.assertEqual(self.client.current_run_workflow(run), f"bt:{run.run_id}")


if __name__ == "__main__":
    unittest.main()
