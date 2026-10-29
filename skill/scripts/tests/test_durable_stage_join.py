"""A later stage joins a run the durable runtime owns (bt_durable.stage_join, D-149): pictures REQ-021 ran its first
stage (r15) on the durable runtime and «Ejecutar subplan» could not add SP-4 to it.

End to end with real git, the fake `claude` through the real driver, M6 and DBOS. Stage 1 runs T1 (accepted) and T2
(`fixlater`, one attempt: it stops and waits for the owner). Stage 2 adds T3 after T1. The join copies the run's lines,
inherits T1 without running it, continues T2 from its own snapshot and runs T3 on the copied line; the owner record and
the run pointer move to the new run. A join that would redo accepted work needs confirmation; a join while an attempt is
live pauses the run and the engine completes it once the attempt ends.

    PYTHONPATH=skill/scripts:skill/scripts/tests uv run python -m unittest test_durable_stage_join
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import bt_run_owner
import durable_support as lab_support
from bt_contracts.execution import RunRef
from bt_durable import stage_join
from durable_support import task, wait_until
from test_durable_e2e import FAST, EngineCase

ONE_ATTEMPT = FAST.model_copy(update={"max_parallel": 1, "budget": FAST.budget.model_copy(update={"max_attempts": 1})})


class StageJoin(EngineCase):
    def stage(self, tasks, revision: int) -> RunRef:
        return RunRef.model_validate(self.lab.freeze(tasks, revision=revision))

    def join(self, new: RunRef, **kwargs) -> dict:
        return stage_join.join(self.client, self.lab.rdir, state_dir=self.lab.state, new=new,
                               repositories={"app": self.lab.repo}, **kwargs)

    def ref(self, name: str) -> str:
        return lab_support.git(self.lab.repo, "rev-parse", "-q", "--verify", name)

    def test_a_later_stage_continues_the_run_without_running_accepted_work_again(self):
        first = [task("T1", scenario="own"), task("T2", scenario="fixlater", after=["T1"])]
        run1 = self.stage(first, 1)
        self.lab.own(run1.model_dump(mode="json"))
        self.start_engine()
        self.client.start(run1, ONE_ATTEMPT)
        wait_until(lambda: (self.client.status(run1)["tasks"].get("T2") or {}).get("decision"), 180, interval=0.5,
                   what="T2 to stop and ask the owner")
        launches_before = [item["task"] for item in self.lab.launches()]
        self.assertEqual(launches_before, ["T1", "T2"])

        # a stage that changes accepted work is refused before anything moves, unless confirmed
        changed = self.stage([{**first[0], "objective": "do T1 differently"}, first[1]], 3)
        with self.assertRaises(stage_join.JoinRefused) as refused:
            self.join(changed)
        self.assertEqual(refused.exception.code, "JOIN_NEEDS_CONFIRM")
        self.assertEqual(bt_run_owner.read(self.lab.rdir)["run_id"], run1.run_id)

        run2 = self.stage([*first, task("T3", scenario="own", after=["T1"])], 2)
        dry = self.join(run2, dry_run=True)
        self.assertEqual((dry["status"], dry["counts"]), ("dry_run", {"inherit": 1, "reconcile": 1, "redo": 1}), dry)
        self.assertEqual(bt_run_owner.read(self.lab.rdir)["run_id"], run1.run_id)        # a dry run moves nothing

        joined = self.join(run2, settings=FAST)
        self.assertEqual((joined["status"], joined["to"], joined["reconcile"]), ("joined", run2.run_id, ["T2"]), joined)
        owner = bt_run_owner.read(self.lab.rdir)
        self.assertEqual((owner["run_id"], owner["migrated_from"]), (run2.run_id, f"durable {run1.run_id}"))
        pointer = json.loads((self.lab.rdir / "RUN.durable-run.json").read_text())
        self.assertEqual(pointer["revision"], 2)
        line1, line2 = "refs/bt/line/proj/REQ-900/r1/app", "refs/bt/line/proj/REQ-900/r2/app"
        self.assertEqual(self.ref(f"{line2}-base"), self.ref(f"{line1}-base"))   # the copied lines share their base
        self.assertTrue(self.ref(line2))
        self.assertIn(f"app:{line2}", joined["lines"])

        status = self.settled(run2, timeout=300)
        self.assertEqual(status["summary"]["status"], "completed", status)
        self.assertEqual(status["summary"]["tasks"]["T1"], "inherited")
        launches = self.lab.launches()
        # T1 never ran again; T2 continued from its own snapshot (fixlater is right only then); T3 ran once
        self.assertEqual([item["task"] for item in launches].count("T1"), 1, launches)
        self.assertEqual([item["task"] for item in launches].count("T2"), 2, launches)
        self.assertEqual([item["task"] for item in launches].count("T3"), 1, launches)
        t3 = next(item for item in launches if item["task"] == "T3")
        self.assertIn("T1.task", t3["seen"])                    # T3 started on the line copied from the first stage
        rows = self.client.workflows(f"bt:{run1.run_id}")
        self.assertFalse([r.workflow_id for r in rows if r.status in ("PENDING", "ENQUEUED")])   # the old run ended
        events = [row["event"] for row in self.lab.telemetry()]
        self.assertNotIn("inherit_refused", events)

    def test_a_join_waits_for_live_attempts_and_the_engine_completes_it(self):
        first = [task("T1", scenario="slow")]
        run1 = self.stage(first, 1)
        self.lab.own(run1.model_dump(mode="json"))
        self.start_engine()
        self.client.start(run1, FAST)
        wait_until(lambda: self.lab.launches(), 120, interval=0.5, what="T1 to start")
        run2 = self.stage([*first, task("T2", scenario="own", after=["T1"])], 2)
        waiting = self.join(run2, settings=FAST)
        self.assertEqual((waiting["status"], waiting["live"]), ("waiting", ["T1"]), waiting)
        self.assertTrue((self.lab.rdir / stage_join.PENDING).is_file())
        # the engine finishes the join once T1 has ended (its reaper pass drains pending joins)
        wait_until(lambda: bt_run_owner.read(self.lab.rdir)["run_id"] == run2.run_id, 240, interval=1.0,
                   what="the engine to complete the join")
        self.assertFalse((self.lab.rdir / stage_join.PENDING).exists())
        status = self.settled(run2, timeout=240)
        self.assertEqual(status["summary"]["status"], "completed", status)
        self.assertEqual([item["task"] for item in self.lab.launches()], ["T1", "T2"])

    def test_the_owners_pause_carries_into_the_new_stage(self):
        """pictures REQ-021: the owner paused r15 from the web while T94 waited for a decision; a stage joined then must
        not start anything until the owner resumes."""
        first = [task("T1", scenario="own"), task("T2", scenario="fixlater", after=["T1"])]
        run1 = self.stage(first, 1)
        self.lab.own(run1.model_dump(mode="json"))
        self.start_engine()
        self.client.start(run1, ONE_ATTEMPT)
        wait_until(lambda: (self.client.status(run1)["tasks"].get("T2") or {}).get("decision"), 180, interval=0.5,
                   what="T2 to stop and ask the owner")
        self.client.command(run1, "pause")
        wait_until(lambda: (self.client.status(run1)["summary"] or {}).get("status") == "paused", 60, interval=0.5,
                   what="the run to pause")
        run2 = self.stage([*first, task("T3", scenario="own", after=["T1"])], 2)
        joined = self.join(run2, settings=FAST)
        self.assertEqual((joined["status"], joined["paused"]), ("joined", True), joined)
        wait_until(lambda: (self.client.status(run2)["summary"] or {}).get("status") == "paused", 60, interval=0.5,
                   what="the new run to start paused")
        self.assertEqual([item["task"] for item in self.lab.launches()], ["T1", "T2"])   # nothing started while paused
        self.client.command(run2, "resume")
        status = self.settled(run2, timeout=240)
        self.assertEqual(status["summary"]["status"], "completed", status)
        self.assertEqual(sorted(item["task"] for item in self.lab.launches()), ["T1", "T2", "T2", "T3"])

if __name__ == "__main__":
    unittest.main()
