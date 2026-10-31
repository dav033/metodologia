"""An overnight engine stop is not observed task inactivity (pictures r29 T10.441, D-242)."""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
START = 1_000_000.0
BOOT = START + 12 * 3600
CHILD = """
import json, sys
from types import SimpleNamespace
from bt_durable import solver
data = json.load(sys.stdin)
state = data['state']
run = SimpleNamespace(run_id='proj:REQ-900:r1')
cfg = {'stuck_minutes': 45, 'attempt_minutes': 120}
watch = getattr(solver, data['kind'] + '_triggers')
events = [watch(run, data['status'], state, now, cfg) for now in data['times']]
print(json.dumps({'state': state, 'events': events}))
"""


def observe(kind: str, status: dict, times: list[float], state: dict | None = None) -> dict:
    child = subprocess.run([sys.executable, "-c", CHILD], cwd=SCRIPTS, text=True, capture_output=True,
                           input=json.dumps({"kind": kind, "status": status, "times": times, "state": state or {}}),
                           timeout=30, check=True)
    return json.loads(child.stdout)


def pending(name: str = "running", **event) -> dict:
    return {"workflow_status": "PENDING", "tasks": {"T7.4": {
        "workflow_id": "bt:proj:REQ-900:r1:T7.4:k1", "workflow_status": "PENDING",
        "state": {"state": name, **event}, "decision": None}}}


class RestartClocks(unittest.TestCase):
    def test_recovered_task_gets_its_window_without_changing_its_trigger_key(self):
        status = pending(attempt="a1")
        first = observe("stuck", status, [START])
        mature = observe("stuck", status, [START, START + 165 * 60])
        recovered = observe("stuck", status, [BOOT, BOOT + 165 * 60 - 1, BOOT + 165 * 60], first["state"])
        self.assertEqual(recovered["events"][:2], [[], []])
        self.assertEqual(recovered["events"][2][0]["key"], mature["events"][1][0]["key"])

    def test_stalled_run_is_observed_again_after_restart(self):
        status = {"workflow_id": "bt:proj:REQ-900:r1", "workflow_status": "PENDING", "tasks": {},
                  "summary": {"status": "running", "tasks": {}, "gates": {"rejected": {}, "composed": {}}}}
        first = observe("stalled", status, [START])
        mature = observe("stalled", status, [START, START + 45 * 60])
        recovered = observe("stalled", status, [BOOT, BOOT + 45 * 60 - 1, BOOT + 45 * 60], first["state"])
        self.assertEqual(recovered["events"][:2], [[], []])
        self.assertEqual(recovered["events"][2][0]["key"], mature["events"][1][0]["key"])

    def test_repeated_restarts_preserve_accumulated_observation(self):
        status = pending("routing")
        first = observe("stuck", status, [START, START + 20 * 60])
        second = observe("stuck", status, [BOOT, BOOT + 10 * 60], first["state"])
        self.assertEqual(second["events"], [[], []])
        third = observe("stuck", status, [BOOT * 2, BOOT * 2 + 15 * 60 - 1, BOOT * 2 + 15 * 60], second["state"])
        self.assertEqual(third["events"][:2], [[], []])
        self.assertEqual(len(third["events"][2]), 1)
        self.assertIn("2700 observed seconds", third["events"][2][0]["reason"])

    def test_known_wait_that_expires_offline_gets_its_unobserved_grace(self):
        status = pending("waiting_quota", until=START + 2 * 3600)
        first = observe("stuck", status, [START, START + 3600])
        recovered = observe("stuck", status, [BOOT, BOOT + 45 * 60 - 1, BOOT + 45 * 60], first["state"])
        self.assertEqual(recovered["events"][:2], [[], []])
        self.assertEqual(len(recovered["events"][2]), 1)

    def test_already_observed_stuck_task_is_still_due_after_restart(self):
        status = pending("routing")
        first = observe("stuck", status, [START, START + 45 * 60])
        recovered = observe("stuck", status, [BOOT], first["state"])
        self.assertEqual(recovered["events"][0][0]["key"], first["events"][1][0]["key"])

    def test_known_wait_deadline_stays_later_than_the_restarted_clock(self):
        for name in ("waiting_quota", "recovering"):
            with self.subTest(name=name):
                until = BOOT + 2 * 3600
                status = pending(name, until=until)
                first = observe("stuck", status, [START])
                recovered = observe("stuck", status, [BOOT, until + 45 * 60 - 1, until + 45 * 60], first["state"])
                self.assertEqual(recovered["events"][:2], [[], []])
                self.assertEqual(len(recovered["events"][2]), 1)

    def test_completed_recovery_and_owner_waits_never_fire(self):
        status = pending()
        first = observe("stuck", status, [START])
        for name in ("completed", "paused", "needs_decision"):
            with self.subTest(name=name):
                current = pending(name)
                if name == "completed":
                    current["tasks"]["T7.4"]["workflow_status"] = "SUCCESS"
                recovered = observe("stuck", current, [BOOT, BOOT + 24 * 3600], first["state"])
                self.assertEqual(recovered["events"], [[], []])

    def test_legacy_marks_and_new_solver_instances_keep_real_stuck_detection(self):
        status = pending("routing")
        first = observe("stuck", status, [START])
        # Old state has no engine epoch; it must also start a fresh observation window once.
        first["state"]["watch"]["T7.4"].pop("epoch", None)
        recovered = observe("stuck", status, [BOOT, BOOT + 45 * 60], first["state"])
        self.assertEqual(recovered["events"][0], [])
        self.assertEqual(len(recovered["events"][1]), 1)


if __name__ == "__main__":
    unittest.main()
