"""Restarts at random points never cost a run anything (D-210, the owner's goal of 2026-10-30: «no importa que se
reinicie el motor, éste debería ser capaz de continuar sin problemas autónomamente»).

A plan 1.3.0 run with three subplans, audits and a composition gate (the test_durable_subplans plan) runs while the
engine is stopped and started again RESTARTS times at seeded random points spread over the run: while an agent runs,
while M6 verifies, or a seeded moment after the engine came up; one verification is cut twice in a row. One stop is a
SIGKILL of the engine's process group (a crash: no stop record), the others SIGTERM (deploys). The run must complete
with no decision for the owner, no retry of any task, and every attempt launched once (adopted across restarts, never
started again). `BT_CHAOS_SEED` replays a schedule; the failure message carries the seed, the schedule and what each
cut met."""
from __future__ import annotations

import json
import os
import random
import signal
import sqlite3
import sys
import time
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import durable_support as lab_support
from bt_contracts.execution import RunRef
from durable_support import gate, subplan, task, wait_until
from test_durable_e2e import FAST, EngineCase

SEED = int(os.environ.get("BT_CHAOS_SEED", "20261030"))
RESTARTS = 5
CUTS = ("agent", "verify", "moment")
CHECK = ("import pathlib, sys, time\ntime.sleep(3)\n"
         "sys.exit(0 if pathlib.Path('out.txt').read_text() == 'good\\n' else 1)\n")
SETTINGS = FAST.model_copy(update={"max_parallel": 2})


def chaos_plan(check: str) -> tuple[list, list, list]:
    def t(tid, subplan_id=None, kind="implement", after=()):
        return task(tid, scenario="own", subplan=subplan_id, kind=kind, after=list(after), check=check)
    tasks = [t("T1", "SP-1"), t("T3", "SP-3"), t("T1A", "SP-1", "audit", ["T1"]), t("T2", "SP-2", after=["T1"]),
             t("T2A", "SP-2", "audit", ["T2"]), t("T3A", "SP-3", "audit", ["T3"]), t("G1", kind="test", after=["T1A", "T2A"]),
             t("T9", after=["G1"])]
    return (tasks, [subplan("SP-1", "T1", "T1A"), subplan("SP-2", "T2", "T2A"), subplan("SP-3", "T3", "T3A")],
            [gate("CG-1", ["SP-1", "SP-2"], "G1")])


class EngineChaos(EngineCase):
    def m6_running(self) -> bool:
        store = self.lab.state / "m6-quality.sqlite3"
        if not store.exists():
            return False
        try:
            with sqlite3.connect(f"file:{store}?mode=ro", uri=True, timeout=1) as db:
                return bool(db.execute("SELECT count(*) FROM requests WHERE state = 'running'").fetchone()[0])
        except sqlite3.Error:
            return False

    def agent_running(self) -> bool:
        for launch in self.lab.launches():
            try:
                os.kill(int(launch["pid"]), 0)
                return True
            except OSError:
                continue
        return False

    def ended(self, run) -> bool:
        return self.client.status(run)["workflow_status"] in ("SUCCESS", "ERROR")

    def test_a_run_survives_random_restarts_without_a_decision_or_a_second_launch(self):
        rng = random.Random(SEED)
        schedule = [(rng.choice(CUTS), round(rng.uniform(0.2, 3.0), 2)) for _ in range(RESTARTS)]
        crash = rng.randrange(RESTARTS)
        # one verification is cut twice in a row, as two deploys 35 min apart cut pictures REQ-021 r26 T10.45
        twice = rng.randrange(1, RESTARTS)
        schedule[twice - 1:twice + 1] = [("verify", schedule[twice - 1][1]), ("again", schedule[twice][1])]
        log: list[str] = [f"seed {SEED}, crash at cut {crash + 1}, schedule {schedule}"]
        (self.lab.repo / "checks" / "check_chaos.py").write_text(CHECK)
        lab_support.git(self.lab.repo, "add", "-A")
        lab_support.git(self.lab.repo, "commit", "-q", "-m", "a check that takes a moment")
        tasks, subplans, gates = chaos_plan("python3 checks/check_chaos.py")
        run = RunRef.model_validate(self.lab.freeze(tasks, schema="1.3.0", subplans=subplans,
                                                    composition_gates=gates))
        with mock.patch.dict(os.environ, {"FAKE_OWN_DELAY": "3"}):
            self.start_engine()
            self.client.start(run, SETTINGS)
            for number, (cut, moment) in enumerate(schedule, start=1):
                # spread over the run: cut N comes once N/(RESTARTS+1) of the tasks have started (the gate included)
                started = -(-number * len(tasks) // (RESTARTS + 1)) if cut != "again" else 0
                wait_until(lambda started=started: len(self.lab.launches()) >= started or self.ended(run), 300,
                           interval=0.2, what=f"cut {number}: {started} tasks started")
                met = {"agent": self.agent_running, "verify": self.m6_running, "again": self.m6_running}.get(cut)
                if met is not None:
                    wait_until(lambda met=met: met() or self.ended(run), 180, interval=0.1, what=f"cut {number}: {cut}")
                else:
                    time.sleep(moment)                    # a seeded moment, anywhere in the run
                if self.ended(run):
                    log.append(f"cut {number}: the run had ended")
                    break
                how = "SIGKILL" if number - 1 == crash else "SIGTERM"
                log.append(f"cut {number}: {how} during {cut} (agent {self.agent_running()}, m6 {self.m6_running()}, "
                           f"launches {len(self.lab.launches())})")
                if how == "SIGKILL":
                    self.kill_engine()
                else:
                    self.engine.send_signal(signal.SIGTERM)
                    self.assertEqual(self.engine.wait(60), 0, "\n".join(log))
                engine = self.start_engine()
                wait_until(lambda engine=engine: self.lab.engine_ready(engine), 120, what="the next engine")
            status = self.settled(run, timeout=600)
        report = "\n".join(log) + f"\nlaunches: {[(x['task'], Path(x['cwd']).name[:40]) for x in self.lab.launches()]}"
        print("\n" + report, file=sys.stderr)              # the schedule a green run met, for the regression log
        self.assertGreaterEqual(sum(line.startswith("cut") and "SIG" in line for line in log), 3, report)
        self.assertEqual(status["summary"]["status"], "completed", report + "\n" + json.dumps(status)[:3000])
        decisions = {tid: t.get("decision") for tid, t in status["tasks"].items() if t.get("decision")}
        self.assertEqual(decisions, {}, report)
        events = [e for e in self.lab.telemetry() if e.get("event") in ("decision_requested", "recovery_decision")]
        self.assertEqual(events, [], report)
        attempts = [Path(x["cwd"]).name for x in self.lab.launches()]
        self.assertEqual(len(attempts), len(set(attempts)), "an attempt was started twice\n" + report)
        self.assertEqual(sorted(x["task"] for x in self.lab.launches()), sorted(t["id"] for t in tasks),
                         "one attempt per task: a restart must not cost a retry\n" + report)
        self.assertEqual(status["summary"]["gates"]["composed"], {"CG-1": "C1"}, report)


if __name__ == "__main__":
    unittest.main()
