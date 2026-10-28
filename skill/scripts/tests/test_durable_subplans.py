"""Plan 1.3.0 subplans and composition gates in the durable runtime (REQ-030 item 1), end to end: real git, the real
provider driver with a fake `claude`, systemd units (or process groups), the M6 sandbox and DBOS on SQLite.

The plan: SP-1 (T1, audit T1A), SP-2 (T2 after T1, audit T2A), SP-3 (T3, unrelated, audit T3A), gate CG-1 over SP-1 and
SP-2 run by G1, and T9 after the gate. Each fake agent leaves `<task>.task`, and records which task files were already in
the tree it was given, so the test reads which line or candidate every task started from."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import durable_support as lab_support
from bt_contracts.execution import RunRef
from durable_support import gate, subplan, task
from test_durable_e2e import FAST, EngineCase

SERIAL = FAST.model_copy(update={"max_parallel": 1})


def plan_tasks():
    return [task("T1", scenario="own", subplan="SP-1", kind="implement"),
            task("T3", scenario="own", subplan="SP-3", kind="implement"),
            task("T1A", scenario="own", subplan="SP-1", kind="audit", after=["T1"]),
            task("T2", scenario="own", subplan="SP-2", kind="implement", after=["T1"]),
            task("T2A", scenario="own", subplan="SP-2", kind="audit", after=["T2"]),
            task("T3A", scenario="own", subplan="SP-3", kind="audit", after=["T3"]),
            task("G1", scenario="own", kind="test", after=["T1A", "T2A"]),
            task("T9", scenario="own", kind="implement", after=["G1"])]


class DurableSubplans(EngineCase):
    def freeze_subplan_plan(self):
        return RunRef.model_validate(self.lab.freeze(
            plan_tasks(), schema="1.3.0",
            subplans=[subplan("SP-1", "T1", "T1A"), subplan("SP-2", "T2", "T2A"), subplan("SP-3", "T3", "T3A")],
            composition_gates=[gate("CG-1", ["SP-1", "SP-2"], "G1")]))

    def files(self, ref: str) -> set[str]:
        out = lab_support.git(self.lab.repo, "ls-tree", "--name-only", ref)
        return {name for name in out.splitlines() if name.endswith(".task")}

    def test_subplan_lines_and_a_gate(self):
        run = self.freeze_subplan_plan()
        self.start_engine()
        self.client.start(run, SERIAL)
        status = self.settled(run, timeout=300)
        self.assertEqual(status["summary"]["status"], "completed", status)
        launches = {item["task"]: item for item in self.lab.launches()}
        self.assertEqual(len(self.lab.launches()), 8, self.lab.launches())        # one agent per task, no retries

        # per-subplan lines: each holds its scope (members + their frozen-plan ancestors) and nothing else
        prefix = "refs/bt/subplan/proj/REQ-900/r1/app"
        self.assertEqual(self.files(f"{prefix}/SP-1"), {"T1.task", "T1A.task"})
        self.assertEqual(self.files(f"{prefix}/SP-2"), {"T1.task", "T2.task", "T2A.task"})
        self.assertEqual(self.files(f"{prefix}/SP-3"), {"T3.task", "T3A.task"})
        self.assertEqual(self.files("refs/bt/line/proj/REQ-900/r1/app"),
                         {f"{t}.task" for t in ("T1", "T3", "T1A", "T2", "T2A", "T3A", "G1", "T9")})

        # a member starts from its own subplan line: T2 ran after T3 was accepted, without T3's work in its tree
        self.assertLess(launches["T3"]["at"], launches["T2"]["at"])
        self.assertEqual(launches["T2"]["seen"], ["T1.task"])
        # the gate task starts on the composition candidate of SP-1 + SP-2 (not SP-3), after both are complete
        self.assertEqual(set(launches["G1"]["seen"]), {"T1.task", "T1A.task", "T2.task", "T2A.task"})
        self.assertGreater(launches["G1"]["at"], max(launches[t]["at"] for t in ("T1", "T1A", "T2", "T2A")))
        candidates = lab_support.git(self.lab.repo, "for-each-ref", "--format=%(refname)",
                                     "refs/compositions/REQ-900.bt-r1/candidates/")
        self.assertTrue(candidates.strip(), "the gate's candidate is a ref of the composition engine")
        versions = lab_support.git(self.lab.repo, "for-each-ref", "--format=%(refname)", "refs/subplans/REQ-900.bt-r1/")
        self.assertEqual(sorted(versions.split()), ["refs/subplans/REQ-900.bt-r1/SP-1/v1", "refs/subplans/REQ-900.bt-r1/SP-2/v1"])
        # work after the gate never starts before the gate passed
        g1_settled = self._settled_at("G1")
        self.assertGreater(launches["T9"]["at"], g1_settled)
        self.assertEqual(status["summary"]["gates"]["composed"], {"CG-1": "C1"})

    def _settled_at(self, task_id: str) -> float:
        import json
        for line in (self.lab.state / "telemetry.jsonl").read_text().splitlines():
            row = json.loads(line)
            if row.get("event") == "task_settled" and row.get("task_id") == task_id and row.get("status") == "completed":
                return row["ts"]
        raise AssertionError(f"{task_id} never settled")


class SubplanFrontier(unittest.TestCase):
    """The gate rules alone (pure): what may start, and why not."""

    def plan(self):
        import hashlib
        import json

        from bt_durable.legacy import load_plan
        text = json.dumps({"schema_version": "1.3.0", "plan_id": "REQ-900", "revision": 1, "tasks": plan_tasks(),
                           "subplans": [subplan("SP-1", "T1", "T1A"), subplan("SP-2", "T2", "T2A"),
                                        subplan("SP-3", "T3", "T3A")],
                           "composition_gates": [gate("CG-1", ["SP-1", "SP-2"], "G1")]})
        return load_plan(text, approved_sha256=hashlib.sha256(text.encode()).hexdigest(), plan_id="REQ-900", revision=1)

    def test_a_gate_task_waits_for_complete_members_and_a_candidate(self):
        from bt_durable.control import frontier, subplans
        plan = self.plan()
        done = {t: "completed" for t in ("T1", "T1A", "T2", "T2A", "T3", "T3A")}
        no_candidate = frontier.compute(plan, done, max_parallel=4, gates=subplans.Gates())
        self.assertNotIn("G1", no_candidate.ready)
        self.assertEqual([g.id for g in subplans.to_compose(plan, done, subplans.Gates())], ["CG-1"])
        ready = frontier.compute(plan, done, max_parallel=4, gates=subplans.Gates(composed={"CG-1": "C1"}))
        self.assertEqual(ready.ready, ("G1",))
        rejected = subplans.Gates(rejected={"CG-1": "git_text_conflict"})
        self.assertIn("candidate rejected", subplans.held(plan, done, rejected, "G1"))
        # an incomplete member (its audit not done) holds the gate even with its dependencies met
        partial = {**done, "T2A": "running"}
        self.assertIn("not complete", subplans.held(plan, {k: v for k, v in partial.items() if k != "T2A"},
                                                    subplans.Gates(composed={"CG-1": "C1"}), "G1"))

    def test_scopes_are_the_legacy_subplan_line_scopes(self):
        from bt_durable.control import subplans
        from bt_durable.legacy import scoped_task_ids
        plan = self.plan()
        self.assertEqual(subplans.scopes(plan)["SP-2"], scoped_task_ids(plan, "SP-2"))
        self.assertEqual(subplans.scopes(plan)["SP-2"], frozenset({"T1", "T2", "T2A"}))
        self.assertEqual(subplans.lines_of(plan, "T1"), ("SP-1", "SP-2"))
        self.assertEqual(subplans.home(plan, "G1"), "gate:CG-1")
        self.assertEqual(subplans.home(plan, "T9"), "")

    def test_a_plan_without_subplans_keeps_the_old_frontier(self):
        from bt_durable.control import frontier, subplans
        plan = self.plan()
        self.assertFalse(subplans.enabled(type("P", (), {"schema_version": "1.0.0", "subplans": ()})()))
        done = {t: "completed" for t in ("T1", "T1A", "T2", "T2A", "T3", "T3A")}
        self.assertIn("G1", frontier.compute(plan, done, max_parallel=4).ready)    # gates=None: pre-patch behaviour


if __name__ == "__main__":
    unittest.main()

