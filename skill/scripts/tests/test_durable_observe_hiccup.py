"""A user manager that does not answer once never kills a healthy agent (REQ-030 audit, 2026-10-29).

Under load `systemctl --user show` can fail or time out. The supervisor then reports the attempt `unknown`, and the
agent workflow, which polls while the state is `running`, terminated the healthy agent, read it as cancelled (a
transient failure) and launched it again: test_durable_postgres saw ['slow', 'slow', 'ok'] in a loaded regression.
Here a `systemctl` shim on the engine's PATH fails the next `show` of the lab's units once, while the agent runs."""
from __future__ import annotations

import os
import shutil
import stat
import sys
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from bt_contracts.execution import RunRef
from durable_support import task, wait_until
from test_durable_e2e import FAST, SYSTEMD, EngineCase

SHIM = """#!/bin/sh
# fails the next `systemctl --user show` of a lab unit once the test arms it (as a manager that does not answer)
if [ "$2" = "show" ] && [ -e "{flag}" ] && echo "$*" | grep -q "{prefix}"; then
  rm -f "{flag}"; echo "Failed to connect to bus: Connection timed out" >&2; exit 1
fi
exec {real} "$@"
"""


@unittest.skipUnless(SYSTEMD, "needs a systemd user manager")
class ObserveHiccup(EngineCase):
    def test_one_unanswered_observation_neither_kills_nor_relaunches_a_running_agent(self):
        flag = self.lab.root / "fail-next-show"
        shim = self.lab.bin / "systemctl"
        shim.write_text(SHIM.format(flag=flag, prefix=self.lab.unit_prefix, real=shutil.which("systemctl")))
        shim.chmod(shim.stat().st_mode | stat.S_IXUSR)
        run = RunRef.model_validate(self.lab.freeze([task("T1", scenario="slow")]))
        with mock.patch.dict(os.environ, {"FAKE_SLOW_SECONDS": "10"}):
            self.start_engine()
        self.client.start(run, FAST)
        wait_until(lambda: len(self.lab.launches()) >= 1, 90, what="the agent to start")
        flag.write_text("1")
        wait_until(lambda: not flag.exists(), 30, what="the engine to meet the failing observation")
        status = self.settled(run, timeout=180)
        self.assertEqual(status["summary"]["status"], "completed", status)
        self.assertEqual([x["scenario"] for x in self.lab.launches()], ["slow"], "a healthy agent was launched again")
        beats = sum(len(p.read_text().splitlines()) for p in self.lab.state.rglob("heartbeat.txt"))
        self.assertGreaterEqual(beats, 90, "the healthy agent was terminated before it finished (100 beats in 10 s)")


if __name__ == "__main__":
    unittest.main()
