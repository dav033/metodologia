"""The engine's reaper (`service.reap_once`): an agent unit whose workflow is no longer running is terminated and
released; one whose workflow still runs is never touched (REQ-030 audit, 2026-10-29: the reaper had no direct test).

Real DBOS on SQLite in this process, real workflow statuses (PENDING, SUCCESS, CANCELLED, absent); the runtime is a
recording stand-in, because what is under test is the reaper's decision, not systemd (bt_supervisor has its own)."""
from __future__ import annotations

import sys
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from dbos import DBOS, SetWorkflowID


@DBOS.workflow(name="test.reaper.waits")
def waits() -> str:
    DBOS.recv("go", timeout_seconds=120)
    return "done"


@DBOS.workflow(name="test.reaper.ends")
def ends() -> str:
    return "done"


class Runtime:
    """What the reaper sees of the units: every key is `running` until terminated."""

    def __init__(self, keys):
        self.keys, self.terminated, self.released = list(keys), [], []

    def owned(self, prefix):
        return [k for k in self.keys if k.startswith(prefix)]

    def observe(self, ref):
        return SimpleNamespace(state="exited" if ref.attempt_key in self.terminated else "running")

    def terminate(self, ref):
        self.terminated.append(ref.attempt_key)

    def release(self, ref):
        self.released.append(ref.attempt_key)


class Telemetry:
    def __init__(self):
        self.events = []

    def emit(self, event, **fields):
        self.events.append((event, fields))


class Reaper(unittest.TestCase):
    def setUp(self):
        from bt_durable.execution import engine
        from bt_durable.settings import EngineConfig
        state = Path(tempfile.mkdtemp(prefix="bt-reaper-"))
        self.runtime, self.telemetry = Runtime(["k-live", "k-done", "k-cancelled", "k-unknown"]), Telemetry()
        ports = SimpleNamespace(runtime=self.runtime, telemetry=self.telemetry)
        engine.start(EngineConfig(system_database_url=f"sqlite:///{state / 'dbos.sqlite3'}", state_dir=state), ports)
        self.addCleanup(engine.stop)
        with SetWorkflowID("bt:k-live:agent"):
            DBOS.start_workflow(waits)
        with SetWorkflowID("bt:k-done:agent"):
            DBOS.start_workflow(ends).get_result()
        with SetWorkflowID("bt:k-cancelled:agent"):
            DBOS.start_workflow(waits)
        DBOS.cancel_workflow("bt:k-cancelled:agent")
        deadline = time.monotonic() + 30
        while DBOS.get_workflow_status("bt:k-cancelled:agent").status != "CANCELLED" and time.monotonic() < deadline:
            time.sleep(0.1)

    def test_only_units_of_workflows_that_no_longer_run_are_terminated_and_released(self):
        from bt_durable.service import reap_once
        reaped = reap_once()
        self.assertEqual(sorted(reaped), ["k-cancelled", "k-done", "k-unknown"])
        self.assertEqual(sorted(self.runtime.terminated), ["k-cancelled", "k-done", "k-unknown"])
        self.assertEqual(sorted(self.runtime.released), ["k-cancelled", "k-done", "k-unknown"])
        self.assertNotIn("k-live", self.runtime.terminated + self.runtime.released)
        self.assertEqual({fields["attempt_key"]: fields["workflow_status"] for _, fields in self.telemetry.events},
                         {"k-done": "SUCCESS", "k-cancelled": "CANCELLED", "k-unknown": None})
        self.assertEqual(reap_once(), [])                 # a second pass finds nothing running any more
        DBOS.send("bt:k-live:agent", "go", "go")


if __name__ == "__main__":
    unittest.main()
