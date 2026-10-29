"""A gate rejected by the previous composer is composed again on the owner's retry (REQ-030; pictures REQ-021 CG-1).

A 1.3.0 run starts under the PREVIOUS engine (exported from git: its composer folds every member from the run line's
base), whose candidate for CG-1 is rejected (SP-2 contains SP-1 and edits the same file); with nothing else to run the
run ends blocked. The CURRENT engine takes over the same database; the owner's `retry_task` of the gate task reopens the
ended run (`bt:<run>@2`), composes the gate again (`bt-run-recompose-gate`) with members measured from their merge
base, and the gate task runs on the new candidate."""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

import test_durable_upgrade as upgrade
from bt_contracts.execution import RunRef
from durable_support import wait_until
from test_durable_e2e import FAST
from test_durable_subplans import dependent_subplans_on_one_file

upgrade.PREVIOUS = os.environ.get("BT_PREVIOUS_COMPOSE_ENGINE_COMMIT", "08a1c7bc7")    # main before the composer fix
SERIAL = FAST.model_copy(update={"max_parallel": 1})


class RecomposeAfterUpgrade(upgrade.EngineUpgrade):
    test_a_run_started_by_the_previous_engine_continues_on_the_new_one = None      # the parent's own scenario

    def telemetry(self) -> list[dict]:
        path = self.lab.state / "telemetry.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def ended(self, run, timeout: float, what: str) -> dict:
        def check():
            status = self.client.status(run)
            return status if status["workflow_status"] == "SUCCESS" else None
        return wait_until(check, timeout, interval=0.5, what=what)

    def test_a_gate_rejected_by_the_previous_composer_is_composed_on_the_owner_retry(self):
        from bt_durable.client import Client
        tasks, subplans_, gates = dependent_subplans_on_one_file()
        run = RunRef.model_validate(self.lab.freeze(tasks, schema="1.3.0", subplans=subplans_, composition_gates=gates))
        scripts = upgrade.export_previous(Path(tempfile.mkdtemp(prefix="bt-previous-", dir=self.lab.root)))
        previous = self.spawn_previous(scripts)
        wait_until(lambda: (self.lab.state / "dbos.sqlite3").exists(), 60, what="DBOS database")
        self.client = Client(self.lab.database_url)
        self.addCleanup(self.client.close)

        def started():
            try:
                return self.client.start(run, SERIAL)
            except Exception:  # noqa: BLE001 - the schema may still be in creation
                return None
        wait_until(started, 60, interval=0.5, what="the previous engine's schema")
        ended = self.ended(run, 240, "the previous engine's run to end blocked on its rejected gate")
        self.assertEqual(ended["summary"]["status"], "blocked", ended)
        self.assertEqual(list(ended["summary"]["gates"]["rejected"]), ["CG-1"])
        previous.terminate()
        previous.wait(30)
        self.start_engine()                                       # the current code, same database

        self.client.command(run, "retry_task", task_id="G1", note="compose the gate again")
        done = self.ended(run, 300, "the reopened run to finish")
        self.assertEqual((done["workflow_id"], done["summary"]["status"]), (f"bt:{run.run_id}@2", "completed"), done)
        events = self.telemetry()
        self.assertEqual([row["state"] for row in events if row.get("event") == "gate_composed"], ["rejected", "candidate"])
        self.assertEqual([row["event"] for row in events].count("gate_recompose"), 1)
        self.assertEqual(sorted(item["task"] for item in self.lab.launches()), ["G1", "T1", "T2"])


if __name__ == "__main__":
    unittest.main()
