"""Earlier engines run by the upgrade and replay tests never kill another lab's agents.

Every lab hands out the same attempt keys (proj-REQ-900-r1-T1-a1-5667e64e), and an engine older than e2d961ee5 put
every process of the user carrying the key on its kill list. test_durable_shutdown failed with «2 != 1» while a
parallel regression ran test_durable_remote's old engine (2026-10-30): its T1 was terminated, and with it the other
lab's healthy T1 agent, which that lab read as cancelled, waited 30 s for and launched again; in a stressed round, 10
of 14 labs lost their agent in the same second. `durable_support.export_engine` keeps an old engine's scan to its own
processes; here each old engine the suites run is asked for its kill list while a newer lab's agent carries the key."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from durable_support import _OLD_SCAN, export_engine
from test_durable_remote import RECORDED_BY
from test_durable_upgrade import PREVIOUS

AUDIT_PREVIOUS = os.environ.get("BT_PREVIOUS_AUDIT_ENGINE_COMMIT", "58fc34f52")   # test_durable_audits_upgrade
SHARED_ATTEMPT = "proj-REQ-900-r1-T1-a1-5667e64e"
SCAN = "import json, sys; from bt_supervisor import procs; print(json.dumps(sorted(procs.marked(sys.argv[1]))))"


class OldEngineKillList(unittest.TestCase):
    def setUp(self):
        sleeper = [sys.executable, "-c", "import time; time.sleep(60)"]
        base = {k: v for k, v in os.environ.items() if k not in ("BT_ATTEMPT_KEY", "BT_SUPERVISOR_ID")}
        # an agent of a current lab (its supervisor marks it) and one of the old engine itself (no supervisor mark)
        self.other = subprocess.Popen(sleeper, env={**base, "BT_ATTEMPT_KEY": SHARED_ATTEMPT, "BT_SUPERVISOR_ID": "0123abcd"})
        self.own = subprocess.Popen(sleeper, env={**base, "BT_ATTEMPT_KEY": SHARED_ATTEMPT})
        for proc in (self.other, self.own):
            self.addCleanup(proc.wait)
            self.addCleanup(proc.kill)

    def kill_list(self, scripts: Path) -> set[int]:
        done = subprocess.run([sys.executable, "-c", SCAN, SHARED_ATTEMPT], cwd=scripts, capture_output=True, text=True,
                              env={**os.environ, "PYTHONPATH": str(scripts)}, timeout=60, check=True)
        return set(json.loads(done.stdout))

    def test_each_old_engine_kills_only_its_own_agents(self):
        for commit in sorted({RECORDED_BY, PREVIOUS, AUDIT_PREVIOUS}):
            with self.subTest(commit=commit), tempfile.TemporaryDirectory() as tmp:
                scripts = export_engine(commit, Path(tmp))
                found = self.kill_list(scripts)
                self.assertNotIn(self.other.pid, found, "an old engine would kill another lab's agent")
                self.assertIn(self.own.pid, found, "an old engine must still find its own agents")

    def test_the_unscoped_scan_is_what_killed_them(self):
        with tempfile.TemporaryDirectory() as tmp:
            scripts = export_engine(RECORDED_BY, Path(tmp))
            procs = scripts / "bt_supervisor" / "procs.py"
            original = subprocess.run(["git", "-C", str(HERE.parents[2]), "show",
                                       f"{RECORDED_BY}:skill/scripts/bt_supervisor/procs.py"],
                                      capture_output=True, text=True, check=True).stdout
            self.assertIn(_OLD_SCAN, original)
            procs.write_text(original, encoding="utf-8")                   # the recorded engine as it was
            self.assertIn(self.other.pid, self.kill_list(scripts))


if __name__ == "__main__":
    unittest.main()
