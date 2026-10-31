"""A task workflow that answered the owner under the PREVIOUS engine replays unchanged on the current one (D-254).

The previous engine (exported from git) starts the owner's retry after an escalation from the base its last automatic
retry chose, here the run line. A task escalates, the owner answers, its second attempt starts from the line and
escalates again; the engine is SIGKILLed while that decision is open. The current engine recovers the same workflow:
the recorded loop pass (no `bt-task-continues-latest-tree` marker, `bt.base_ref` recorded) replays as it was, and only
the answer given after the upgrade takes the new path, continuing from the second attempt's snapshot."""
from __future__ import annotations

import json
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

PREVIOUS = os.environ.get("BT_PREVIOUS_LATEST_TREE_ENGINE_COMMIT", "de091646b")   # main before D-254


class LatestTreeAfterUpgrade(upgrade.EngineUpgrade):
    test_a_run_started_by_the_previous_engine_continues_on_the_new_one = None      # the parent's own scenario

    def decision(self, run, request_id: str) -> None:
        wait_until(lambda: ((self.client.status(run)["tasks"].get("T1") or {}).get("decision") or {})
                   .get("request_id") == request_id, 240, interval=0.5, what=f"decision {request_id}")

    def manifest(self, number: int) -> dict:
        path = next(self.lab.state.glob(f"attempts-root/attempts/*T1-a{number}-*/handoff/manifest.json"))
        return json.loads(path.read_text())

    def test_an_owner_retry_recorded_by_the_previous_engine_replays_and_the_next_one_continues(self):
        from bt_durable.client import Client
        scripts = export_engine(PREVIOUS, Path(tempfile.mkdtemp(prefix="bt-previous-", dir=self.lab.root)))
        # neverfix: a scenario the previous engine's fake agent knows (its lab writes its own wrapper), and every attempt
        # changes out.txt, so each snapshot differs from the tree it started from
        run = RunRef.model_validate(self.lab.freeze([task("T1", scenario="neverfix")]))
        one_attempt = FAST.model_copy(update={"budget": FAST.budget.model_copy(update={"max_attempts": 1})})
        previous = self.spawn_previous(scripts)
        wait_until(lambda: (self.lab.state / "dbos.sqlite3").exists(), 60, what="DBOS database")
        self.client = Client(self.lab.database_url)
        self.addCleanup(self.client.close)

        def started():
            try:                                  # the file exists before the engine finished creating the schema
                return self.client.start(run, one_attempt)
            except Exception:  # noqa: BLE001
                return None
        wait_until(started, 60, interval=0.5, what="the previous engine's schema")
        self.decision(run, "T1:d1")
        self.client.answer(run, "T1", OwnerAnswer(request_id="T1:d1", action="retry_with_note", note="first answer"))
        self.decision(run, "T1:d2")
        os.killpg(previous.pid, signal.SIGKILL)
        previous.wait(10)

        self.start_engine()                                                    # the current code, same database
        self.client.answer(run, "T1", OwnerAnswer(request_id="T1:d2", action="retry_with_note", note="second answer"))
        self.decision(run, "T1:d3")
        self.client.answer(run, "T1", OwnerAnswer(request_id="T1:d3", action="stop"))
        status = self.settled(run, timeout=240)

        rows = self.client.workflows(f"bt:{run.run_id}")
        self.assertFalse([r.workflow_id for r in rows if r.status == "ERROR"], [(r.workflow_id, r.status) for r in rows])
        self.assertEqual(status["summary"]["status"], "blocked", status)
        first, second, third = self.manifest(1), self.manifest(2), self.manifest(3)
        self.assertNotEqual(first["snapshot_sha"], first["base_sha"])
        self.assertNotEqual(second["snapshot_sha"], second["base_sha"])
        self.assertEqual(second["base_sha"], first["base_sha"])                # recorded by the previous engine: the line
        self.assertEqual(third["base_sha"], second["snapshot_sha"])            # after the upgrade: the latest attempt
        self.assertEqual(len(self.lab.launches()), 3)                          # the replay launched nothing again


if __name__ == "__main__":
    unittest.main()
