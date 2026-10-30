"""Scenario I (REQ-030 M9): a workflow interrupted under code v1 is recovered by code v2, which added a step behind
`DBOS.patch`. The recovered workflow keeps the v1 step sequence; a workflow started under v2 takes the new step.
Real processes, a real SQLite system database, SIGKILL between versions."""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROBE = Path(os.environ.get("BT_VERSION_PROBE") or HERE / "durable_version_probe.py")


def wait(predicate, timeout=60):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.2)
    raise AssertionError("timed out")


class Versioning(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="bt-version-", dir=os.environ.get("BT_LAB_DIR") or None))
        self.url = f"sqlite:///{self.dir / 'dbos.sqlite3'}"
        self.procs = []
        self.addCleanup(self._kill_all)

    def _kill_all(self):
        for proc in self.procs:
            if proc.poll() is None:
                os.killpg(proc.pid, signal.SIGKILL)

    def spawn(self, version, *start):
        (self.dir / f"ready-{version}").unlink(missing_ok=True)
        proc = subprocess.Popen([os.environ.get("BT_VERSION_PYTHON") or sys.executable, str(PROBE), self.url, str(self.dir), version, *start],
                                start_new_session=True, stdout=subprocess.DEVNULL,
                                stderr=open(self.dir / f"{version}.log", "ab"))  # noqa: SIM115 - owned by the child
        self.procs.append(proc)
        wait(lambda: (self.dir / f"ready-{version}").exists())
        return proc

    def trace(self):
        path = self.dir / "trace.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    @staticmethod
    def checkpointed(client, workflow: str, step: str) -> None:
        """Kill only after the step's checkpoint is written: a step killed between its effect and its checkpoint runs
        again (at least once), which made this test fail under load with ['a', 'a', 'extra', 'b', 'c']."""
        wait(lambda: any(row["function_name"].endswith(step) for row in client.list_workflow_steps(workflow)))

    def test_patch_applies_only_to_workflows_that_had_not_passed_it(self):
        old = self.spawn("v1", "start", "wf-passed")
        wait(lambda: any(t["step"] == "a" for t in self.trace()))
        from dbos import DBOSClient
        client = DBOSClient(system_database_url=self.url)
        self.addCleanup(client.destroy)
        client.send("wf-passed", "go", "go1")                       # wf-passed goes beyond the patch point (step b)
        wait(lambda: any(t["workflow"] == "wf-passed" and t["step"] == "b" for t in self.trace()))
        self.checkpointed(client, "wf-passed", "step_b")
        os.killpg(old.pid, signal.SIGKILL)                          # interrupted under v1, waiting for go2
        old.wait(10)
        early = self.spawn("v1", "start", "wf-early")               # a second v1 workflow stops before the point
        wait(lambda: any(t["workflow"] == "wf-early" and t["step"] == "a" for t in self.trace()))
        self.checkpointed(client, "wf-early", "step_a")
        os.killpg(early.pid, signal.SIGKILL)
        early.wait(10)
        self.spawn("v2", "start", "wf-new")                         # the upgraded engine recovers both
        wait(lambda: any(t["workflow"] == "wf-new" and t["step"] == "a" for t in self.trace()))
        for workflow in ("wf-passed", "wf-early", "wf-new"):
            client.send(workflow, "go", "go1")
            client.send(workflow, "go", "go2")
        wait(lambda: {t["workflow"] for t in self.trace() if t["step"] == "c"} == {"wf-passed", "wf-early", "wf-new"},
             120)
        steps = {w: [t["step"] for t in self.trace() if t["workflow"] == w] for w in ("wf-passed", "wf-early", "wf-new")}
        self.assertEqual(steps["wf-passed"], ["a", "b", "c"])       # past the patch point: v1's sequence, kept
        self.assertEqual(steps["wf-early"], ["a", "extra", "b", "c"])   # had not reached it: takes the patch safely
        self.assertEqual(steps["wf-new"], ["a", "extra", "b", "c"])
        # step c is traced before the workflow records its result: wait for the status, do not sample it
        wait(lambda: {client.retrieve_workflow(w).get_status().status for w in steps} == {"SUCCESS"})

if __name__ == "__main__":
    unittest.main()
