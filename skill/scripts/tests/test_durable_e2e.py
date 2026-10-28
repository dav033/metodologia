"""End-to-end runs of the durable runtime with real processes, worktrees, sandboxed verification and DBOS (REQ-030
M2/M9). The engine is a separate process: tests SIGKILL it mid-run and prove recovery without duplicate launches."""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import durable_support as lab_support
from bt_contracts.execution import RunRef
from bt_contracts.owner import OwnerAnswer
from bt_durable.client import Client
from bt_durable.settings import Settings
from durable_support import Lab, task, wait_until

FAST = Settings(max_parallel=2, poll_seconds=0.5, run_poll_seconds=5, owner_wait_seconds=5)
SYSTEMD = subprocess.run(["systemctl", "--user", "is-system-running"], capture_output=True, text=True,
                         check=False).stdout.strip() in ("running", "degraded")


class EngineCase(unittest.TestCase):
    """A lab, an engine process the test can kill, and a client (no tests of its own: other suites subclass it)."""
    backend = "systemd" if SYSTEMD else "pgroup"

    def setUp(self):
        self.lab = Lab(backend=self.backend)
        self.addCleanup(self.lab.cleanup)
        self.engine = None
        self.client = None

    def start_engine(self):
        self.engine = self.lab.spawn_engine()
        self.addCleanup(self._stop_engine, self.engine)
        if self.client is None:
            try:
                wait_until(lambda: (self.lab.state / "dbos.sqlite3").exists() or self.engine.poll() is not None, 60,
                           what="DBOS database")
            finally:
                if self.engine.poll() is not None:
                    raise AssertionError("engine exited: " + (self.lab.root / "engine.log").read_text()[-3000:])
            time.sleep(1.0)
            self.client = Client(self.lab.database_url)
            self.addCleanup(self.client.close)
        return self.engine

    def _stop_engine(self, proc):
        if proc.poll() is None:
            proc.send_signal(signal.SIGTERM)
            try:
                proc.wait(20)
            except subprocess.TimeoutExpired:
                proc.kill()

    def kill_engine(self):
        os.killpg(self.engine.pid, signal.SIGKILL)
        self.engine.wait(10)

    def settled(self, run, timeout=180):
        def check():
            status = self.client.status(run)
            return status if status["workflow_status"] in ("SUCCESS", "ERROR") else None
        try:
            return wait_until(check, timeout, interval=0.5, what="run to settle")
        except AssertionError:
            print((self.lab.root / "engine.log").read_text()[-4000:])
            raise


class DurableRuns(EngineCase):
    def test_a_dependent_plan_runs_verifies_and_integrates(self):
        run = RunRef.model_validate(self.lab.freeze([task("T1"), task("T2", after=["T1"]), task("T3")]))
        self.start_engine()
        self.client.start(run, FAST)
        status = self.settled(run)
        self.assertEqual(status["summary"]["status"], "completed", status)
        self.assertEqual(len(self.lab.launches()), 3)                     # one agent process per task
        line = lab_support.git(self.lab.repo, "rev-parse", "refs/bt/line/proj/REQ-900/r1/app")
        self.assertEqual(lab_support.git(self.lab.repo, "show", f"{line}:out.txt"), "good")

    def test_an_implementation_failure_is_retried_from_its_snapshot_with_the_decisive_lines(self):
        run = RunRef.model_validate(self.lab.freeze([task("T1", scenario="fixlater")]))
        self.start_engine()
        self.client.start(run, FAST)
        status = self.settled(run)
        self.assertEqual(status["summary"]["status"], "completed", status)
        launches = self.lab.launches()
        self.assertEqual(len(launches), 2)
        self.assertTrue(launches[1]["has_note"], "the retry prompt must carry the failure's decisive lines")

    def test_an_environment_failure_is_repaired_without_a_new_agent_attempt(self):
        run = RunRef.model_validate(self.lab.freeze([task("T1", check=lab_support.CHECK_HEAP)]))
        self.start_engine()
        self.client.start(run, FAST)
        status = self.settled(run)
        self.assertEqual(status["summary"]["status"], "completed", status)
        self.assertEqual(len(self.lab.launches()), 1)                     # re-verified, not re-run

    def test_engine_sigkill_mid_attempt_recovers_without_a_duplicate_launch(self):
        os.environ["FAKE_SLOW_SECONDS"] = "6"
        self.addCleanup(os.environ.pop, "FAKE_SLOW_SECONDS", None)
        run = RunRef.model_validate(self.lab.freeze([task("T1", scenario="slow")]))
        self.start_engine()
        self.client.start(run, FAST)
        wait_until(lambda: self.lab.launches(), 60, what="the agent to start")
        self.kill_engine()                                                # the agent keeps running in its unit
        time.sleep(2)
        self.start_engine()
        status = self.settled(run)
        self.assertEqual(status["summary"]["status"], "completed", status)
        self.assertEqual(len(self.lab.launches()), 1, self.lab.launches())

    def test_repeated_failure_escalates_and_a_stale_answer_cannot_change_the_decision(self):
        run = RunRef.model_validate(self.lab.freeze([task("T1", scenario="neverfix")]))
        settings = FAST.model_copy(update={"budget": FAST.budget.model_copy(update={"max_attempts": 3})})
        self.start_engine()
        self.client.start(run, settings)
        decision = wait_until(lambda: (self.client.status(run)["tasks"].get("T1") or {}).get("decision"), 240,
                              interval=1, what="an owner decision")
        self.assertIn(decision["request_id"], ("T1:d1",))
        launched = len(self.lab.launches())
        self.assertLessEqual(launched, 3)                                  # bounded: never more than the budget
        self.client.answer(run, "T1", OwnerAnswer(request_id="T1:d0", action="retry"))   # stale: refused
        time.sleep(3)
        self.assertEqual(len(self.lab.launches()), launched)
        self.client.answer(run, "T1", OwnerAnswer(request_id=decision["request_id"], action="stop"))
        status = self.settled(run)
        self.assertEqual(status["summary"]["status"], "blocked")


    def _legacy_from_first_run(self, verdict):
        """Run T1 once, then describe its real snapshot as legacy progress for a second plan revision."""
        from bt_contracts.execution import LegacyProgress, LegacyTask
        first = RunRef.model_validate(self.lab.freeze([task("T1")], revision=1))
        self.start_engine()
        self.client.start(first, FAST)
        self.assertEqual(self.settled(first)["summary"]["status"], "completed")
        manifest = next(self.lab.state.glob("attempts-root/attempts/*T1-a1*/handoff/manifest.json"))
        data = json.loads(manifest.read_text())
        legacy = LegacyProgress(tasks=(LegacyTask(task_id="T1", verdict=verdict, snapshot_sha=data["snapshot_sha"],
                                                  base_sha=data["base_sha"], repository=Path(data["repository"]),
                                                  attempt_dir=manifest.parent.parent, manifest_path=manifest,
                                                  worktree=None, provenance="first run"),))
        second = RunRef.model_validate(self.lab.freeze([task("T1"), task("T2", after=["T1"], paths=["T2/**"])],
                                                       revision=2))
        return second, legacy

    def test_migrated_progress_is_integrated_not_rerun_and_dependents_build_on_it(self):
        run, legacy = self._legacy_from_first_run("inherit")
        self.client.start(run, FAST, legacy)
        status = self.settled(run)
        self.assertEqual(status["summary"]["status"], "completed", status)
        self.assertEqual(status["summary"]["tasks"]["T1"], "inherited")
        self.assertEqual(len(self.lab.launches()), 2)            # T1 in the first run, T2 now: T1 never re-ran
        t2 = self.lab.launches()[-1]
        self.assertEqual(Path(t2["cwd"]).joinpath("out.txt").read_text(), "good\n")   # T2 started on T1's work

    def test_reconcilable_progress_is_verified_again_before_it_counts(self):
        run, legacy = self._legacy_from_first_run("reconcile")
        self.client.start(run, FAST, legacy)
        status = self.settled(run)
        self.assertEqual(status["summary"]["status"], "completed", status)
        self.assertEqual(status["summary"]["tasks"]["T1"], "completed")
        self.assertIn("reconciled", status["summary"]["results"]["T1"]["provenance"])
        self.assertEqual(len(self.lab.launches()), 2)            # verified again, not re-run


    def test_cancelling_a_run_stops_every_writer(self):
        os.environ["FAKE_SLOW_SECONDS"] = "60"
        self.addCleanup(os.environ.pop, "FAKE_SLOW_SECONDS", None)
        run = RunRef.model_validate(self.lab.freeze([task("T1", scenario="slow")]))
        self.start_engine()
        self.client.start(run, FAST)
        launch = wait_until(lambda: self.lab.launches(), 60, what="the agent to start")[0]
        beat = Path(launch["cwd"]) / "heartbeat.txt"
        wait_until(lambda: beat.exists() and beat.stat().st_size > 0, 30, what="the agent to write")
        cancelled = self.client.cancel(run)
        self.assertTrue(cancelled)
        def stopped():
            size = beat.stat().st_size
            time.sleep(1.0)
            return beat.stat().st_size == size
        wait_until(stopped, 30, interval=0.5, what="the agent to stop writing")   # the reaper terminated its unit
        alive = [p for p in Path("/proc").iterdir() if p.name.isdigit() and _marked(p, launch["pid"])]
        self.assertEqual(alive, [])

    def test_no_capacity_waits_durably_for_the_reset_then_runs(self):
        run = RunRef.model_validate(self.lab.freeze([task("T1", scenario="quotaonce")]))
        self.start_engine()
        self.client.start(run, FAST)
        status = self.settled(run)
        self.assertEqual(status["summary"]["status"], "completed", status)
        self.assertEqual(len(self.lab.launches()), 2)
        events = [json.loads(line) for line in (self.lab.state / "telemetry.jsonl").read_text().splitlines()]
        decisions = [e for e in events if e["event"] == "recovery_decision"]
        self.assertEqual([(d["failure_class"], d["action"]) for d in decisions], [("quota", "wait")])

    def test_duplicate_concurrent_answers_start_one_attempt(self):
        import threading
        run = RunRef.model_validate(self.lab.freeze([task("T1", scenario="neverfix")]))
        settings = FAST.model_copy(update={"budget": FAST.budget.model_copy(update={"max_attempts": 1})})
        self.start_engine()
        self.client.start(run, settings)
        first = wait_until(lambda: (self.client.status(run)["tasks"].get("T1") or {}).get("decision"), 120,
                           interval=1, what="an owner decision")
        before = len(self.lab.launches())
        answers = [threading.Thread(target=self.client.answer,
                                    args=(run, "T1", OwnerAnswer(request_id=first["request_id"], action="retry")))
                   for _ in range(4)]
        [a.start() for a in answers]
        [a.join() for a in answers]
        second = wait_until(lambda: ((self.client.status(run)["tasks"].get("T1") or {}).get("decision") or {})
                            .get("request_id") not in (None, first["request_id"]) and
                            self.client.status(run)["tasks"]["T1"]["decision"], 120, interval=1,
                            what="the next decision")
        self.assertEqual(len(self.lab.launches()), before + 1)       # four answers, one new attempt
        self.client.answer(run, "T1", OwnerAnswer(request_id=second["request_id"], action="stop"))
        self.assertEqual(self.settled(run)["summary"]["status"], "blocked")


def _marked(proc: Path, agent_pid: int) -> bool:
    """A live process of the cancelled attempt: its own pid or one carrying the attempt marker in its environment."""
    try:
        if int(proc.name) == agent_pid:
            return True
        return b"BT_ATTEMPT_KEY=proj-REQ-900" in (proc / "environ").read_bytes()
    except OSError:
        return False


if __name__ == "__main__":
    unittest.main()
