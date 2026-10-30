"""Durable runs in the panels and under remote commands (REQ-030 M7).

Real lab (durable_support): real git, DBOS on SQLite, the engine as a separate process, the fake provider through the
real driver, M6 verification. Remote commands go through the real ledger and handlers of the remote API, the stdlib
bridge (`bt_durable_panel.dispatch`) and the `bt-durable remote` CLI in the uv environment. The replay test records a
run history with the engine of the commit that recorded the live runs (old command format), then recovers it with
this code.

    PYTHONPATH=skill/scripts:skill/scripts/tests uv run python -m unittest test_durable_remote
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
# the stdlib modules read the machine config of BITACORA_ROOT: never the real bitácora in a test
os.environ.setdefault("BITACORA_ROOT", tempfile.mkdtemp(prefix="bt-remote-root-", dir=os.environ.get("BT_LAB_DIR")))

import bt_core
import bt_durable_panel as panel
import bt_remote_api
import bt_remote_commands as commands
from bt_contracts import remote
from bt_contracts.execution import RunRef
from bt_contracts.owner import RunCommand
from bt_durable import projection
from bt_durable.execution.workflows import _stale_command
from bt_durable.settings import Settings
from durable_support import SYSTEMD, Lab, engine_client, task, wait_until

FAST = Settings(max_parallel=2, poll_seconds=0.5, run_poll_seconds=5, owner_wait_seconds=5)
ONE_ATTEMPT = FAST.model_copy(update={"budget": FAST.budget.model_copy(update={"max_attempts": 1})})
REPO = HERE.parents[2]
# The commit whose bt.run recorded the live durable histories (pictures REQ-021): commands without expect_* fields.
RECORDED_BY = os.environ.get("BT_REPLAY_BASE", "003b7d6fc442dfc346f5d80b68a01384d8275d05")


def projected(lab: Lab, predicate, timeout: float, what: str) -> dict:
    def check():
        doc = panel.read(lab.rdir)
        return doc if doc and predicate(doc) else None
    return wait_until(check, timeout, interval=0.5, what=what)


def task_of(doc: dict, task_id: str) -> dict:
    return next(t for t in doc["tasks"] if t["id"] == task_id)


def telemetry(lab: Lab) -> list[dict]:
    try:
        return [json.loads(line) for line in (lab.state / "telemetry.jsonl").read_text().splitlines() if line.strip()]
    except OSError:
        return []


class Sequencing(unittest.TestCase):
    """The projection's sequence is monotonic, survives a rebuild, and tracks each subject's last change."""

    @staticmethod
    def content(t1="running", status="running"):
        return {"schema": panel.SCHEMA, "status": status, "workflow_status": "PENDING", "run_id": "p:REQ-900:r1",
                "tasks": [{"id": "T1", "state": t1, "round": 1}, {"id": "T2", "state": "queued", "round": None}],
                "decisions": []}

    def test_unchanged_content_keeps_the_document_and_a_change_bumps_only_its_subject(self):
        first = projection.sequence(self.content(), None, now=1000.0)
        self.assertEqual(first["sequence"], 1_000_000)                 # a rebuild starts from the time in ms
        self.assertIs(projection.sequence(self.content(), first, now=1001.0), first)
        second = projection.sequence(self.content(t1="needs_decision"), first, now=1002.0)
        self.assertEqual(second["sequence"], first["sequence"] + 1)
        self.assertEqual(task_of(second, "T1")["seq"], second["sequence"])
        self.assertEqual(task_of(second, "T2")["seq"], first["sequence"])
        self.assertEqual(second["status_seq"], first["status_seq"])
        third = projection.sequence(self.content(t1="needs_decision", status="paused"), second, now=1003.0)
        self.assertEqual(third["status_seq"], third["sequence"])

    def test_a_rebuild_without_the_file_never_reuses_a_sequence(self):
        old = projection.sequence(self.content(), None, now=1000.0)
        for _ in range(5):
            old = projection.sequence(self.content(t1=str(uuid.uuid4())), old, now=1000.0)
        rebuilt = projection.sequence(self.content(), None, now=1001.0)
        self.assertGreater(rebuilt["sequence"], old["sequence"])


class RunCommandGuard(unittest.TestCase):
    def test_a_command_without_expectations_takes_the_old_path(self):
        old = RunCommand.model_validate({"kind": "pause", "request_id": "legacy-0001", "task_id": None, "note": "",
                                         "by": "owner"})                      # the shape the M2 CLI sent
        self.assertEqual(_stale_command(old, paused=True, rounds={}), "")
        self.assertEqual(_stale_command(old, paused=False, rounds={}), "")

    def test_a_command_built_against_an_older_state_is_stale(self):
        pause = RunCommand(kind="pause", request_id="remote-0001", expect_paused=False)
        self.assertIn("stale", _stale_command(pause, paused=True, rounds={}))
        self.assertEqual(_stale_command(pause, paused=False, rounds={}), "")
        retry = RunCommand(kind="retry_task", request_id="remote-0002", task_id="T1", expect_round=1)
        self.assertIn("round 2", _stale_command(retry, paused=False, rounds={"T1": 2}))
        self.assertEqual(_stale_command(retry, paused=False, rounds={"T1": 1}), "")


class EngineMarker(unittest.TestCase):
    """`expect_*` fields go only to an engine whose code checks them: an older bt.run would refuse the message as
    invalid and record a step this code would not replay."""

    def test_features_come_only_from_a_live_engine_marker(self):
        from bt_durable import remote as bridge
        folder = Path(tempfile.mkdtemp(dir=os.environ.get("BT_LAB_DIR")))
        marker = folder / "engine.json"
        self.assertEqual(bridge.engine_features(marker), frozenset())                    # no marker: older engine
        bridge.write_marker(marker)
        self.assertEqual(bridge.engine_features(marker), frozenset({bridge.EXPECT}))
        self.assertEqual(oct(marker.stat().st_mode & 0o777), "0o600")
        dead = subprocess.run([sys.executable, "-c", "import os; print(os.getpid())"], capture_output=True,
                              text=True, check=True).stdout.strip()
        marker.write_text(json.dumps({"pid": int(dead), "features": [bridge.EXPECT]}))
        self.assertEqual(bridge.engine_features(marker), frozenset())                    # its engine is gone


class PanelMapping(unittest.TestCase):
    def test_every_projection_state_maps_into_the_snapshot_vocabulary(self):
        self.assertEqual(set(panel.TASK_STATE.values()) - set(remote.SNAPSHOT_TASK_STATES), set())
        for state in ("waiting_quota", "recovering", "needs_decision", "failed"):
            tasks = {"T1": {"id": "T1", "state": "pending", "history": []}}
            panel.overlay(tasks, {"tasks": [{"id": "T1", "state": state, "seq": 7, "until": 1_800_000_000,
                                             "decision_id": "T1:d1@k1", "workflow_status": "ERROR"}]})
            self.assertIn(tasks["T1"]["state"], remote.SNAPSHOT_TASK_STATES)
            self.assertEqual(tasks["T1"]["revision"], 7)
            self.assertTrue(tasks["T1"]["reason"], state)            # the panel still tells which one it is


    def test_the_bridge_uses_the_configured_cli_or_this_checkout(self):
        with patch("bt_config.get", return_value=["/opt/bt/bin/bt-durable"]):
            self.assertEqual(panel.cli(), ["/opt/bt/bin/bt-durable"])
        with patch("bt_config.get", return_value=[]):
            self.assertEqual(panel.cli()[-4:], ["--quiet", "--project", str(REPO), "bt-durable"])


class DurableRemoteCommands(unittest.TestCase):
    backend = "systemd" if SYSTEMD else "pgroup"

    def setUp(self):
        self.lab = Lab(backend=self.backend)
        self.addCleanup(self.lab.cleanup)
        root = patch.object(bt_core, "ROOT", self.lab.bitacora.resolve())
        root.start()
        self.addCleanup(root.stop)
        self.ledger = commands.Ledger(self.lab.root / "commands.db")

    def submit(self, key: str, command: str, precondition: dict, **params) -> dict:
        return self.ledger.submit({"idempotency_key": key, "command": command, "target": "proj/REQ-900",
                                   "origin": "web", "params": params, "precondition": precondition},
                                  bt_remote_api.HANDLERS, bt_remote_api._target_state)

    def snapshot(self) -> remote.RemoteSnapshot:
        from bt_remote_snapshot import build_snapshot
        return remote.RemoteSnapshot.model_validate_json(json.dumps(build_snapshot(self.lab.bitacora)))

    def web_dashboard_shows_the_run(self):
        """The local web dashboard reads the same projection: plan list, plan page, run tab, live attempts."""
        import bt_live_api
        import bt_page_run
        import bt_plans_api
        import bt_planstatus
        root = self.lab.bitacora.resolve()
        row = next(p for p in bt_planstatus.list_plans(root) if p["req_id"] == "REQ-900")
        self.assertEqual((row["run_status"], row["active"], row["asks"]), ("running", True, 1))
        status = bt_plans_api.status_of(root, "proj", "REQ-900")
        self.assertEqual((status["run"]["authority"], [d["id"] for d in status["decisions"]]), ("dbos", ["T1:d1@k1"]))
        html = bt_page_run.run_panel("proj", "REQ-900", self.lab.rdir, "token")
        self.assertIn("autoridad durable (DBOS)", html)
        self.assertIn("needs_decision", html)
        self.assertIn("T1:d1@k1", html)
        live = [item for item in bt_live_api.now_items(root) if item["req_id"] == "REQ-900"]
        self.assertEqual([item["task"] for item in live], ["T2"])
        with self.assertRaises(bt_plans_api.PlanError):                 # the web form path refuses a stale id too
            bt_plans_api.decide(root, "proj", "REQ-900", "T1:d1@k7", "retry", "")
        with self.assertRaises(SystemExit):                             # stopping stays `bt-durable cancel`
            bt_page_run.apply_control(self.lab.rdir, "stop")
        with self.assertRaises(SystemExit):                             # resume of a running run does not apply
            bt_page_run.apply_control(self.lab.rdir, "resume")

    def test_remote_commands_are_durable_idempotent_and_refuse_stale_views(self):
        os.environ["FAKE_SLOW_SECONDS"] = "300"
        self.addCleanup(os.environ.pop, "FAKE_SLOW_SECONDS", None)
        data = self.lab.freeze([task("T1", scenario="neverfix"),
                                task("T2", scenario="slow", paths=["T2/**", "heartbeat.txt"])])
        self.lab.own(data)
        run = RunRef.model_validate(data)
        _, client = engine_client(self, self.lab)
        client.start(run, ONE_ATTEMPT)
        doc = projected(self.lab, lambda d: task_of(d, "T1")["state"] == "needs_decision"
                        and task_of(d, "T2")["state"] == "running", 180, "T1 to ask the owner while T2 runs")
        self.assertEqual([d["id"] for d in doc["decisions"]], ["T1:d1@k1"])
        shown = self.snapshot()
        run_view = next(r for r in shown.runs if r.req == "REQ-900")
        self.assertEqual((run_view.state, run_view.revision), ("running", doc["status_seq"]))
        self.assertEqual({t.id: t.state for t in run_view.tasks}, {"T1": "rejected", "T2": "running"})
        t2_view = next(t for t in run_view.tasks if t.id == "T2")
        self.assertTrue(t2_view.active_attempt and t2_view.active_attempt.live)
        self.assertEqual([d.id for d in shown.decision_requests], ["T1:d1@k1"])
        first_revision = run_view.revision
        self.web_dashboard_shows_the_run()

        # pause, applied once; the same key again is a replay, not a second effect
        paused = self.submit("lab-pause-000001", "pause", {"state": "running", "revision": first_revision})
        self.assertEqual(paused["status"], "OK", paused)
        self.assertTrue(paused["outcome"]["durable"]["workflow_checked"])   # the lab engine checks expect_paused
        doc = projected(self.lab, lambda d: d["status"] == "paused", 60, "the run to pause")
        again = self.submit("lab-pause-000001", "pause", {"state": "running", "revision": first_revision})
        self.assertEqual((again["status"], again["replayed"]), ("OK", True))
        resumed = self.submit("lab-resume-00001", "resume", {"state": "paused", "revision": doc["status_seq"]})
        self.assertEqual(resumed["status"], "OK", resumed)
        projected(self.lab, lambda d: d["status"] == "running", 60, "the run to resume")

        # a pause built against the first view is stale now (the run was paused and resumed since)
        stale = self.submit("lab-pause-000002", "pause", {"state": "running", "revision": first_revision})
        self.assertEqual((stale["status"], stale["code"]), ("REJECTED", "STALE_PRECONDITION"))
        with self.assertRaises(panel.DurableRejected) as refused:          # the bridge checks DBOS itself too
            panel.dispatch("proj", "REQ-900", self.lab.rdir, "pause", {}, key="lab-pause-000003",
                           precondition={"state": "running", "revision": first_revision})
        self.assertIn("stale", str(refused.exception))
        time.sleep(3)
        self.assertEqual(panel.read(self.lab.rdir)["status"], "running")

        # answers: an id that is not open is refused at the ledger and at the bridge; the open one is applied
        launches = len(self.lab.launches())
        self.assertEqual(self.submit("lab-answer-00001", "answer-decision", {"state": "open"},
                                     request_id="T1:d1@k9", option="retry")["code"], "STALE_PRECONDITION")
        with self.assertRaises(panel.DurableRejected):
            panel.dispatch("proj", "REQ-900", self.lab.rdir, "answer-decision",
                           {"request_id": "T1:d0@k1", "option": "retry"}, key="lab-answer-00002")
        stop = self.submit("lab-answer-00003", "answer-decision", {"state": "open"}, request_id="T1:d1@k1",
                           option="stop", reason="lab")
        self.assertEqual(stop["status"], "OK", stop)
        doc = projected(self.lab, lambda d: task_of(d, "T1")["state"] == "blocked", 60, "T1 to stop")
        self.assertEqual(len(self.lab.launches()), launches)

        # reopen (a new round), once per key: the ledger replays it and DBOS drops the same key sent again
        t1 = task_of(doc, "T1")
        reopen = self.submit("lab-reopen-00001", "reopen", {"state": "blocked", "revision": t1["seq"]}, task="T1")
        self.assertEqual(reopen["status"], "OK", reopen)
        self.assertTrue(self.submit("lab-reopen-00001", "reopen", {"state": "blocked", "revision": t1["seq"]},
                                    task="T1")["replayed"])
        client.command(run, "retry_task", task_id="T1", request_id="lab-reopen-00001", expect_round=1)
        doc = projected(self.lab, lambda d: task_of(d, "T1")["decision_id"] == "T1:d1@k2", 180,
                        "T1's second round to ask the owner")
        with self.assertRaises(panel.DurableRejected) as old_round:       # round 1's decision id is stale now
            panel.dispatch("proj", "REQ-900", self.lab.rdir, "answer-decision",
                           {"request_id": "T1:d1@k1", "option": "retry"}, key="lab-answer-00004")
        self.assertIn("no longer open", str(old_round.exception))
        self.assertEqual(self.submit("lab-answer-00005", "answer-decision", {"state": "open"},
                                     request_id="T1:d1@k2", option="stop")["status"], "OK")
        doc = projected(self.lab, lambda d: task_of(d, "T1")["state"] == "blocked", 60, "T1 to stop again")

        # a retry built for round 1 that reaches the run workflow directly is refused there (no round 3)
        client.command(run, "retry_task", task_id="T1", request_id="lab-stale-round1", expect_round=1)
        refusal = wait_until(lambda: [e for e in telemetry(self.lab) if e["event"] == "command_refused"
                                      and e.get("request_id") == "lab-stale-round1"], 60, what="the refusal")
        self.assertIn("round 2", refusal[0]["reason"])
        time.sleep(2)
        doc = panel.read(self.lab.rdir)
        self.assertEqual((task_of(doc, "T1")["round"], task_of(doc, "T1")["state"]), (2, "blocked"))
        self.assertEqual(sum(1 for item in self.lab.launches() if item["scenario"] == "neverfix"), 2)
        self.assertFalse([e for e in telemetry(self.lab) if e["event"] == "command_refused"
                          and e.get("request_id") == "lab-reopen-00001"])   # the duplicate never reached it

        # the snapshot follows the run to the end
        shown = self.snapshot()
        t1_view = next(t for r in shown.runs for t in r.tasks if t.id == "T1")
        self.assertEqual((t1_view.state, t1_view.revision), ("blocked", task_of(doc, "T1")["seq"]))
        client.cancel(run)
        projected(self.lab, lambda d: d["status"] == "cancelled", 60, "the run to be cancelled")
        self.assertEqual(next(r for r in self.snapshot().runs if r.req == "REQ-900").state, "cancelled")


class OldCommandReplay(unittest.TestCase):
    """A history recorded by the engine of RECORDED_BY, with a command in the old format, is recovered by this code
    with the same steps: no DBOSUnexpectedStepError, the pause is kept, and the run completes after a resume."""
    backend = "systemd" if SYSTEMD else "pgroup"

    def setUp(self):
        self.lab = Lab(backend=self.backend)
        self.addCleanup(self.lab.cleanup)
        self.old = self.lab.root / "recorded-by"
        self.old.mkdir()
        archive = subprocess.run(["git", "-C", str(REPO), "archive", RECORDED_BY, "skill/scripts"],
                                 capture_output=True, check=True).stdout
        subprocess.run(["tar", "-x", "-C", str(self.old)], input=archive, check=True)

    def spawn_old(self) -> subprocess.Popen:
        scripts = self.old / "skill" / "scripts"
        log = open(self.lab.root / "engine-old.log", "ab")  # noqa: SIM115 - owned by the child process
        return subprocess.Popen([sys.executable, str(scripts / "tests" / "durable_support.py"), "serve",
                                 str(self.lab.write_config())],
                                env={**os.environ, **self.lab.env(), "PYTHONPATH": f"{scripts}:{scripts / 'tests'}"},
                                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)

    def test_a_recorded_old_pause_replays_under_this_code(self):
        from bt_durable.client import Client
        os.environ["FAKE_SLOW_SECONDS"] = "4"
        self.addCleanup(os.environ.pop, "FAKE_SLOW_SECONDS", None)
        run = RunRef.model_validate(self.lab.freeze([task("T1", scenario="slow"),
                                                     task("T2", after=["T1"], paths=["T2/**"])]))
        old = self.spawn_old()
        self.addCleanup(lambda: old.poll() is None and os.killpg(old.pid, signal.SIGKILL))
        wait_until(lambda: (self.lab.state / "dbos.sqlite3").exists() or old.poll() is not None, 60, what="old engine")
        time.sleep(1.0)
        client = Client(self.lab.database_url)
        self.addCleanup(client.close)
        client.start(run, FAST)
        wait_until(lambda: self.lab.launches(), 60, what="T1 to start")
        legacy_pause = {"kind": "pause", "request_id": "recorded-pause-01", "task_id": None, "note": "", "by": "owner"}
        client.client.send(f"bt:{run.run_id}", legacy_pause, "run", idempotency_key="command:recorded-pause-01")
        wait_until(lambda: (client.summary(run) or {}).get("status") == "paused"
                   and (client.summary(run) or {}).get("tasks", {}).get("T1") == "completed", 240,
                   what="the old engine to apply the pause and finish T1")   # its relaunch waits 30 s (see below)
        os.killpg(old.pid, signal.SIGKILL)                        # interrupted: the history holds the old pause
        old.wait(10)
        # T1's launches under the old engine: 1, or 2 when an unanswered `systemctl show` under load made that code kill
        # and relaunch a healthy agent (fixed since in adapters/runtime.py; stress run of 2026-10-29: 4 of 10)
        recorded = len(self.lab.launches())
        self.assertEqual({x["scenario"] for x in self.lab.launches()}, {"slow"})      # T1 only
        engine_client(self, self.lab)                             # this code recovers the run from its history
        time.sleep(4)
        self.assertEqual((client.summary(run) or {}).get("status"), "paused")
        self.assertEqual(len(self.lab.launches()), recorded)      # paused: T2 has not started
        client.command(run, "resume", request_id="replayed-resume-1", expect_paused=True)

        def settled():
            status = client.status(run)
            return status if status["workflow_status"] in ("SUCCESS", "ERROR") else None
        status = wait_until(settled, 180, interval=0.5, what="the run to settle")
        log = (self.lab.root / "engine.log").read_text(errors="replace")
        self.assertNotIn("DBOSUnexpectedStepError", log)
        self.assertEqual((status["workflow_status"], status["summary"]["status"]), ("SUCCESS", "completed"), status)
        self.assertEqual(len(self.lab.launches()), recorded + 1)  # this code launched T2 only


if __name__ == "__main__":
    unittest.main()
