"""A launch step re-run after an engine restart adopts its agent even while the user manager does not answer.

test_durable_shutdown failed once under a loaded regression (2026-10-30, 2 launches instead of 1). The engine exits
right after DBOS is destroyed (D-181), so a `bt.launch` still running then (here: its final observation waiting out
D-188's grace for an unanswered `systemctl --user show`) runs again after recovery. The re-run's own `systemctl show`
failed too, DBOS's 3 tries were spent in seconds, the agent workflow ended in ERROR and the task asked the owner about
a runtime defect while the first agent ran on; the reaper then killed it, and an answer would launch a second agent.
Here a `systemctl` shim fails every `show` of the lab's units once the agent has reported its start, until the test
lifts it, so the step is cut and re-run exactly in that window."""
from __future__ import annotations

import os
import shutil
import signal
import sqlite3
import stat
import sys
import threading
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from bt_contracts.execution import RunRef
from durable_support import task, wait_until
from test_durable_e2e import SYSTEMD, EngineCase
from test_durable_shutdown import WAITING

SHIM = """#!/bin/sh
# fails `systemctl --user show` of a lab unit while armed and once the attempt reported its start (started.json): the
# launch itself goes through, everything after it meets a manager that does not answer
if [ "$2" = "show" ] && [ -e "{flag}" ] && echo "$*" | grep -q "{prefix}" \\
   && [ -n "$(find "{attempts}" -name started.json -print -quit 2>/dev/null)" ]; then
  echo "Failed to connect to bus: Connection timed out" >&2; exit 1
fi
exec {real} "$@"
"""
OUTAGE_SECONDS = 10.0          # longer than DBOS's 3 tries of the step, shorter than the 30 s grace (D-188)


def agent_rows(db: Path) -> list[tuple[str, str]]:
    with sqlite3.connect(db) as conn:
        return conn.execute("SELECT workflow_uuid, status FROM workflow_status WHERE workflow_uuid LIKE '%:agent'").fetchall()


def recorded_steps(db: Path) -> list[str]:
    with sqlite3.connect(db) as conn:
        return [r[0] for r in conn.execute("SELECT function_name FROM operation_outputs WHERE workflow_uuid LIKE "
                                           "'%:agent' ORDER BY function_id")]


@unittest.skipUnless(SYSTEMD, "needs a systemd user manager")
class LaunchHiccup(EngineCase):
    def test_a_launch_cut_by_a_restart_adopts_its_agent_while_the_manager_does_not_answer(self):
        flag = self.lab.root / "fail-show"
        shim = self.lab.bin / "systemctl"
        shim.write_text(SHIM.format(flag=flag, prefix=self.lab.unit_prefix, real=shutil.which("systemctl"),
                                    attempts=self.lab.state / "supervisor" / "attempts"))
        shim.chmod(shim.stat().st_mode | stat.S_IXUSR)
        flag.write_text("1")
        run = RunRef.model_validate(self.lab.freeze([task("T1", scenario="slow")]))
        with mock.patch.dict(os.environ, {"FAKE_SLOW_SECONDS": "30"}):
            self.start_engine()
        self.client.start(run, WAITING)
        wait_until(lambda: len(self.lab.launches()) >= 1, 90, what="the agent to start")
        db = self.lab.state / "dbos.sqlite3"
        self.assertNotIn("bt.launch", recorded_steps(db), "the launch step must still be running (its observation "
                                                          "waits for the manager)")
        self.engine.send_signal(signal.SIGTERM)
        self.assertEqual(self.engine.wait(60), 0)

        self.start_engine()                               # the re-run launch meets the same silent manager
        lift = threading.Timer(OUTAGE_SECONDS, lambda: flag.unlink(missing_ok=True))
        lift.start()
        self.addCleanup(lift.cancel)
        ended = wait_until(lambda: [s for _, s in agent_rows(db) if s not in ("PENDING", "ENQUEUED")], 180,
                           interval=0.5, what="the agent workflow to end")
        self.assertEqual(ended, ["SUCCESS"], (self.lab.root / "engine.log").read_text()[-3000:])
        status = self.settled(run, timeout=180)
        self.assertEqual(status["summary"]["status"], "completed", status)
        self.assertEqual(len(self.lab.launches()), 1, "the agent must be adopted after the restart, not started again")


if __name__ == "__main__":
    unittest.main()
