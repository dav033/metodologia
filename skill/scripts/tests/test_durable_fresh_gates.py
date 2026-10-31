"""A passed composition gate is composed again when a member's line takes newer work after it (pictures REQ-021 r29,
2026-10-31: «¿los subplanes subsecuentes reciben el arreglo de SP-2?»).

A repair a later stage adds to a subplan integrates into that subplan's own line; a gate that already passed, and that no
later gate supersedes, never saw it. Real git, the real provider driver with a fake `claude`, the M6 sandbox and DBOS on
SQLite: a first revision runs SP-1, SP-2 and the gate CG-1; a second revision inherits all of it and adds T2B to SP-2
(nothing depends on it, like T2.55). Once T2B is accepted, CG-1 is composed again and its gate task G1 runs on the new
candidate, which holds T2B."""
from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import durable_support as lab_support
from bt_contracts.execution import LegacyProgress, LegacyTask, RunRef
from durable_support import gate, subplan, task
from test_durable_e2e import FAST, EngineCase

SERIAL = FAST.model_copy(update={"max_parallel": 1})


def first_tasks():
    return [task("T1", scenario="own", subplan="SP-1", kind="implement"),
            task("T2", scenario="own", subplan="SP-2", kind="implement", after=["T1"]),
            task("G1", scenario="own", kind="test", after=["T1", "T2"])]


SUBPLANS = [subplan("SP-1", "T1", "T1"), subplan("SP-2", "T2", "T2")]
GATES = [gate("CG-1", ["SP-1", "SP-2"], "G1")]


class FreshGatesEndToEnd(EngineCase):
    def telemetry(self) -> list[dict]:
        path = self.lab.state / "telemetry.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def inherited(self, task_ids) -> list[LegacyTask]:
        out = []
        for task_id in task_ids:
            manifest = next(self.lab.state.glob(f"attempts-root/attempts/*r1-{task_id}-a1-*/handoff/manifest.json"))
            data = json.loads(manifest.read_text())
            out.append(LegacyTask(task_id=task_id, verdict="inherit", snapshot_sha=data["snapshot_sha"],
                                  base_sha=data["base_sha"], repository=Path(data["repository"]),
                                  attempt_dir=manifest.parent.parent, manifest_path=manifest,
                                  provenance=f"legacy first-run-{task_id}"))
        return out

    def test_a_passed_gate_runs_again_on_a_candidate_with_the_new_member_work(self):
        first = RunRef.model_validate(self.lab.freeze(first_tasks(), schema="1.3.0", revision=1, subplans=SUBPLANS,
                                                      composition_gates=GATES))
        self.start_engine()
        self.client.start(first, SERIAL)
        self.assertEqual(self.settled(first, timeout=300)["summary"]["status"], "completed")
        self.assertEqual([row["event"] for row in self.telemetry()].count("gate_stale"), 0)   # nothing changed after it

        repaired = first_tasks() + [task("T2B", scenario="own", subplan="SP-2", kind="implement", after=["T2"])]
        second = RunRef.model_validate(self.lab.freeze(repaired, schema="1.3.0", revision=2, subplans=SUBPLANS,
                                                       composition_gates=GATES))
        self.client.start(second, SERIAL, LegacyProgress(tasks=tuple(self.inherited(("T1", "T2", "G1")))))
        status = self.settled(second, timeout=300)
        self.assertEqual(status["summary"]["status"], "completed", status)
        later = self.lab.launches()[3:]
        self.assertEqual([item["task"] for item in later], ["T2B", "G1"])        # the gate task ran again, once
        self.assertEqual(set(later[1]["seen"]), {"T1.task", "T2.task", "T2B.task"})   # on the candidate with T2B
        stale = [row for row in self.telemetry() if row.get("event") == "gate_stale"]
        self.assertEqual([(row["gate"], row["members"]) for row in stale], [("CG-1", ["SP-2"])])
        self.assertEqual(status["summary"]["tasks"]["G1"], "completed")
        self.assertEqual(status["summary"]["gates"]["composed"], {"CG-1": "C1"})


class FreshGateAfterARepairRound(EngineCase):
    """The member's line changes WITHOUT a new task: a later audit's coordinated repair is a new round of a member that
    the gate already passed with (pictures REQ-021 r27: SP-2's T2.3/T2.5/T2.7 rounds after the gates holding SP-2)."""

    def setUp(self):
        super().setUp()
        self.lab.configure(gates=lab_support.REAL_AUDIT_POLICY)

    def test_a_new_round_of_a_member_after_the_gate_passed_runs_the_gate_again(self):
        tasks = [task("T1", scenario="fixk", subplan="SP-1", kind="implement"),
                 task("G1", scenario="own", kind="test", after=["T1"]),
                 task("TA", scenario="auditk", kind="audit", after=["G1"], paths=["docs/TA.md", "docs/TA.findings.json"])]
        run = RunRef.model_validate(self.lab.freeze(tasks, schema="1.3.0", subplans=[subplan("SP-1", "T1", "T1")],
                                                    composition_gates=[gate("CG-1", ["SP-1"], "G1")]))
        self.start_engine()
        self.client.start(run, SERIAL)
        status = self.settled(run, timeout=420)
        self.assertEqual(status["summary"]["status"], "completed", status)
        counts: dict[str, int] = {}
        for item in self.lab.launches():
            counts[item["task"]] = counts.get(item["task"], 0) + 1
        self.assertEqual(counts, {"T1": 2, "G1": 2, "TA": 2})             # the repair, the gate again, the re-audit
        gate_tree = lab_support.git(self.lab.repo, "ls-tree", "--name-only",
                                    status["summary"]["results"]["G1"]["snapshot_sha"]).split()
        self.assertIn("fixed-k.txt", gate_tree)                           # the gate passed on the repaired member
        rows = [json.loads(line) for line in (self.lab.state / "telemetry.jsonl").read_text().splitlines()]
        self.assertEqual([(r["gate"], r["members"]) for r in rows if r.get("event") == "gate_stale"], [("CG-1", ["SP-1"])])


class FreshTargets(unittest.TestCase):
    """Which passed gates a newer member version concerns (pure)."""

    def plan(self, gates):
        from bt_durable.legacy import load_plan
        tasks = [task("T1", subplan="SP-1", kind="implement"), task("T2", subplan="SP-2", kind="implement", after=["T1"]),
                 task("T3", subplan="SP-3", kind="implement", after=["T2"]), task("G1", kind="test", after=["T1", "T2"]),
                 task("G2", kind="test", after=["G1", "T3"])]
        text = json.dumps({"schema_version": "1.3.0", "plan_id": "REQ-900", "revision": 1, "tasks": tasks,
                           "subplans": [subplan("SP-1", "T1", "T1"), subplan("SP-2", "T2", "T2"),
                                        subplan("SP-3", "T3", "T3")], "composition_gates": gates})
        return load_plan(text, approved_sha256=hashlib.sha256(text.encode()).hexdigest(), plan_id="REQ-900", revision=1)

    def test_only_the_last_cumulative_gate_and_only_once_it_passed(self):
        from bt_durable.control import subplans
        plan = self.plan([gate("CG-1", ["SP-1", "SP-2"], "G1"), gate("CG-2", ["SP-1", "SP-2", "SP-3"], "G2")])
        done = {t: "completed" for t in ("T1", "T2", "T3", "G1")}
        # CG-2 is not composed yet: it composes from the current lines; CG-1 is superseded by it
        self.assertEqual(subplans.fresh_targets(plan, done, subplans.Gates()), ())
        self.assertEqual([g.id for g in subplans.fresh_targets(plan, {**done, "G2": "inherited"}, subplans.Gates())],
                         ["CG-2"])
        self.assertEqual(subplans.fresh_targets(plan, {**done, "G2": "inherited"},
                                                subplans.Gates(rejected={"CG-2": "git_text_conflict"})), ())
        self.assertEqual(subplans.fresh_targets(plan, {**done, "G2": "inherited", "T3": "running"}, subplans.Gates()),
                         ())                                       # a member being repaired is not complete yet

    def test_a_gate_no_later_gate_holds_is_its_own_target(self):
        from bt_durable.control import subplans
        plan = self.plan([gate("CG-1", ["SP-1", "SP-2"], "G1"), gate("CG-2", ["SP-2", "SP-3"], "G2")])
        done = {t: "completed" for t in ("T1", "T2", "T3", "G1")}
        self.assertEqual([g.id for g in subplans.fresh_targets(plan, done, subplans.Gates())], ["CG-1"])


if __name__ == "__main__":
    unittest.main()
