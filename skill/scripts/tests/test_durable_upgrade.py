"""Upgrading the engine under a live run (REQ-030 iteration 2, the pictures REQ-021 situation), with real code trees.

A 1.3.0 run starts under the PREVIOUS engine code (exported from git: it ignores subplans, has no `reverify`), gets two
tasks waiting for the owner and its run loop waiting for news, and the engine is SIGKILLed. The CURRENT engine
recovers the same workflows from the same database: their recorded steps replay unchanged (the three new patches return
False where history already holds a step), and only what happens next takes the new paths — the subplan lines appear,
an old open decision accepts `reverify`, and a classic `retry` still works. No workflow may end in ERROR."""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import durable_support as lab_support
from bt_contracts.execution import RunRef
from bt_contracts.owner import OwnerAnswer
from durable_support import subplan, task, wait_until
from test_durable_e2e import FAST, EngineCase

PREVIOUS = os.environ.get("BT_PREVIOUS_ENGINE_COMMIT", "366cbf372")    # main before iteration 2 (live engine code)


def export_previous(into: Path) -> Path:
    """`git archive` of the previous engine's skill/scripts into a private directory (no worktree, no checkout)."""
    repo = HERE.parents[2]
    archive = subprocess.run(["git", "-C", str(repo), "archive", PREVIOUS, "skill/scripts"], capture_output=True,
                             check=True).stdout
    subprocess.run(["tar", "-x", "-C", str(into)], input=archive, check=True)
    return into / "skill" / "scripts"


class EngineUpgrade(EngineCase):
    def events(self) -> list[str]:
        path = self.lab.state / "telemetry.jsonl"
        return [json.loads(line)["event"] for line in path.read_text().splitlines()] if path.exists() else []

    def spawn_previous(self, scripts: Path) -> subprocess.Popen:
        log = open(self.lab.root / "engine-previous.log", "ab")  # noqa: SIM115 - handed to the child process
        env = {**os.environ, **self.lab.env(), "PYTHONPATH": f"{scripts}:{scripts / 'tests'}"}
        proc = subprocess.Popen([sys.executable, str(scripts / "tests" / "durable_support.py"), "serve",
                                 str(self.lab.write_config())], env=env, stdout=log, stderr=subprocess.STDOUT,
                                start_new_session=True)
        self.addCleanup(self._stop_engine, proc)
        return proc

    def test_a_run_started_by_the_previous_engine_continues_on_the_new_one(self):
        from bt_durable.client import Client
        scripts = export_previous(Path(tempfile.mkdtemp(prefix="bt-previous-", dir=self.lab.root)))
        tasks = [task("T1", subplan="SP-1", kind="implement"),
                 task("T2", scenario="fixlater", subplan="SP-1", kind="implement", after=["T1"]),
                 task("T1A", subplan="SP-1", kind="audit", after=["T2"]),
                 # own paths: a task waiting for the owner keeps its claims, and every lab task declares out.txt
                 task("T4", scenario="neverfix", subplan="SP-2", kind="implement", paths=["T4/**", "T4.task"]),
                 task("T4A", subplan="SP-2", kind="audit", after=["T4"])]
        run = RunRef.model_validate(self.lab.freeze(tasks, schema="1.3.0", subplans=[subplan("SP-1", "T2", "T1A"),
                                                                                     subplan("SP-2", "T4", "T4A")]))
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

        def open_decisions():
            tasks = self.client.status(run)["tasks"]
            found = {t: (row.get("decision") or {}).get("request_id") for t, row in tasks.items()}
            return found if found.get("T2") == "T2:d1" and found.get("T4") == "T4:d1" else None
        wait_until(open_decisions, 240, interval=0.5, what="both decisions under the previous engine")
        old_decision = self.client.status(run)["tasks"]["T4"]["decision"]
        self.assertNotIn("reverify", old_decision["options"])                  # the previous engine's request
        os.killpg(previous.pid, signal.SIGKILL)
        previous.wait(10)

        self.start_engine()                                                    # the current code, same database
        self.client.answer(run, "T4", OwnerAnswer(request_id="T4:d1", action="reverify"))   # new path, old workflow
        self.client.answer(run, "T2", OwnerAnswer(request_id="T2:d1", action="retry"))      # old path still works
        self.client.command(run, "resume", request_id="upgrade-wakes-the-run-loop")
        # the run line was made by the previous engine, which did not pin where it began: the subplan lines wait (the
        # run goes on) until the operator pins it, as the upgrade procedure says (README "Upgrading workflows")
        wait_until(lambda: "subplan_lines_unavailable" in self.events(), 120, what="the missing pin to be reported")
        initial = lab_support.git(self.lab.repo, "rev-list", "--max-parents=0", "HEAD")
        lab_support.git(self.lab.repo, "update-ref", "refs/bt/line/proj/REQ-900/r1/app-base", initial)
        second = wait_until(lambda: (self.client.status(run)["tasks"]["T4"].get("decision") or {}).get("request_id")
                            == "T4:d2" and self.client.status(run)["tasks"]["T4"]["decision"], 240, interval=0.5,
                            what="the re-verification of T4 and its new decision")
        self.assertIn("reverify", second["options"])
        self.client.answer(run, "T4", OwnerAnswer(request_id="T4:d2", action="stop"))
        status = self.settled(run, timeout=240)

        rows = self.client.workflows(f"bt:{run.run_id}")
        self.assertFalse([r.workflow_id for r in rows if r.status == "ERROR"], [(r.workflow_id, r.status) for r in rows])
        tasks_state = status["summary"]["tasks"]
        self.assertEqual((tasks_state["T1"], tasks_state["T2"], tasks_state["T1A"], tasks_state["T4"]),
                         ("completed", "completed", "completed", "blocked"), status)
        events = self.events()
        self.assertIn("subplans_enabled", events)
        self.assertIn("owner_reverify", events)
        line = "refs/bt/subplan/proj/REQ-900/r1/app/SP-1"
        tip = lab_support.git(self.lab.repo, "rev-parse", line)
        self.assertEqual(lab_support.git(self.lab.repo, "show", f"{tip}:out.txt"), "good")
        launches = [item.get("scenario") for item in self.lab.launches()]
        self.assertEqual(launches.count("neverfix"), 1)                         # reverify never relaunched T4
        self.assertEqual(launches.count("fixlater"), 2)                         # retry continued from its snapshot


if __name__ == "__main__":
    unittest.main()
