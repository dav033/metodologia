"""The audit-remediation patch (`bt-run-audit-remediation`, REQ-030 item 4) under a live engine upgrade, with real code
trees: a run starts on the PREVIOUS engine (exported from git, without the audit gate) and is SIGKILLed while an agent
runs; the CURRENT engine recovers it from the same database.

A. An audit whose `task_done` the previous engine already processed replays unchanged (the patch returns False where
   history holds a step): it is not judged, nothing is repaired, the run completes and no workflow ends in ERROR.
B. An audit that finishes after the upgrade takes the new path in the same run: its blocking findings become one
   coordinated repair, the audit runs again and its dependent starts only after it passes."""
from __future__ import annotations

import json
import os
import signal
import tempfile
import unittest
from pathlib import Path

import test_durable_upgrade as upgrade
from bt_contracts.execution import RunRef
from durable_support import REAL_AUDIT_POLICY, subplan, task, wait_until
from test_durable_e2e import FAST

upgrade.PREVIOUS = os.environ.get("BT_PREVIOUS_AUDIT_ENGINE_COMMIT", "58fc34f52")   # iteration 2 before item 4
SERIAL = FAST.model_copy(update={"max_parallel": 1})


class AuditPatchUpgrade(upgrade.EngineUpgrade):
    test_a_run_started_by_the_previous_engine_continues_on_the_new_one = None      # the parent's own scenario

    def setUp(self):
        super().setUp()
        self.lab.configure(gates=REAL_AUDIT_POLICY)
        os.environ["FAKE_SLOW_SECONDS"] = "8"
        self.addCleanup(os.environ.pop, "FAKE_SLOW_SECONDS", None)

    def telemetry(self) -> list[dict]:
        path = self.lab.state / "telemetry.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def start_on_previous(self, run: RunRef, slow_task: str):
        """Start `run` on the previous engine, wait until `slow_task`'s agent runs, then SIGKILL that engine."""
        from bt_durable.client import Client
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
        wait_until(lambda: any(item.get("task") == slow_task for item in self.lab.launches()), 240, interval=0.5,
                   what=f"{slow_task} to run under the previous engine")
        os.killpg(previous.pid, signal.SIGKILL)
        previous.wait(10)
        self.start_engine()                       # the current code, same database: recovery replays the history

    def assert_no_error(self, run: RunRef):
        rows = self.client.workflows(f"bt:{run.run_id}")
        self.assertFalse([r.workflow_id for r in rows if r.status == "ERROR"], [(r.workflow_id, r.status) for r in rows])

    def test_an_audit_processed_by_the_previous_engine_replays_unjudged(self):
        tasks = [task("T1", subplan="SP-1", kind="implement"),
                 task("TA", subplan="SP-1", kind="audit", after=["T1"]),        # no ledger: the new gate would block it
                 task("T9", scenario="slow", kind="implement", after=["TA"])]
        run = RunRef.model_validate(self.lab.freeze(tasks, schema="1.3.0", subplans=[subplan("SP-1", "T1", "TA")]))
        self.start_on_previous(run, "T9")
        status = self.settled(run, timeout=300)
        self.assertEqual(status["summary"]["status"], "completed", status)
        self.assert_no_error(run)
        events = [row["event"] for row in self.telemetry()]
        self.assertNotIn("audit_blocked", events)                               # old history: never judged
        self.assertNotIn("audit_passed", events)
        self.assertEqual([item["task"] for item in self.lab.launches()].count("T9"), 1)   # adopted, not relaunched

    def test_an_audit_finished_after_the_upgrade_is_judged_and_repaired(self):
        tasks = [task("T0", scenario="slow", subplan="SP-1", kind="implement"),
                 task("T1", scenario="fixk", subplan="SP-1", kind="implement", after=["T0"]),
                 task("TA", scenario="auditk", subplan="SP-1", kind="audit", after=["T1"],
                      paths=["docs/TA.md", "docs/TA.findings.json"]),
                 task("T9", scenario="own", kind="implement", after=["TA"])]
        run = RunRef.model_validate(self.lab.freeze(tasks, schema="1.3.0", subplans=[subplan("SP-1", "T1", "TA")]))
        self.start_on_previous(run, "T0")
        status = self.settled(run, timeout=420)
        self.assertEqual(status["summary"]["status"], "completed", status)
        self.assert_no_error(run)
        per_task: dict[str, int] = {}
        for item in self.lab.launches():
            per_task[item["task"]] = per_task.get(item["task"], 0) + 1
        self.assertEqual(per_task, {"T0": 1, "T1": 2, "TA": 2, "T9": 1})
        blocked = [row for row in self.telemetry() if row["event"] == "audit_blocked"]
        self.assertEqual([row["repairs"] for row in blocked], [[{"owner": "T1", "findings": ["F1", "F2"]}]])


if __name__ == "__main__":
    unittest.main()
