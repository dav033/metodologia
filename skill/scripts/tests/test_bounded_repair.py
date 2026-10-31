"""D-241: a bounded repair of a confirmed defect keeps the owner's confirmation, freezes and joins without the owner.

pictures REQ-021 r28 (2026-10-30): T10.45 failed five times on a real product defect; the Solucionador and the Planner
prepared T10.441 (after T10.44, before T10.45, nothing else changed) and the run sat idle 18:36→20:02 because the stage
freeze refused SP-10 as «cambió después de confirmarlo» until the owner re-confirmed it by hand.
"""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bt_plan_adapter
import bt_planning_activity as activity
import bt_planning_flow as flow
import bt_planning_notes as notes
import bt_stages
import bt_subplan_status
import owner_e2e_support as support
import test_stages as ts

planner = bt_plan_adapter.planner
classify = planner.repairs.classify


def tasks(plan: dict) -> dict:
    return {t["id"]: t for t in plan["tasks"]}


def with_repair(plan: dict, *, kind: str = "implement", before: str = "T2", subplan: str = "SP-1") -> dict:
    """The live shape: a new repair task after the producer T1, and the approved task that found the defect (T2) now
    waits for it instead of for T1 directly."""
    out = copy.deepcopy(plan)
    repair = support.plan_task("T1.1", "Repair the confirmed defect", subplan=subplan, kind=kind, after=("T1",))
    index = next(i for i, t in enumerate(out["tasks"]) if t["id"] == before)
    out["tasks"].insert(index, repair)
    tasks(out)[before]["after"] = ["T1.1"]
    return out


class Classifier(unittest.TestCase):
    def setUp(self):
        self.plan = support.three_subplan_plan()
        self.frozen = {**planner.stages.project(self.plan, ["SP-1", "SP-2", "SP-3"]), "revision": 1}

    def verdict(self, draft: dict) -> dict:
        return classify(self.frozen, draft)

    def test_only_adding_a_repair_that_an_approved_task_waits_for_is_bounded(self):
        verdict = self.verdict(with_repair(self.plan))
        self.assertEqual((verdict["bounded"], verdict["added"], verdict["detectors"], verdict["subplans"]),
                         (True, ["T1.1"], ["T2"], ["SP-1"]), verdict["reasons"])
        also = with_repair(self.plan)
        tasks(also)["T2"]["after"] = ["T1", "T1.1"]                 # keeping the direct dependency is also fine
        self.assertTrue(self.verdict(also)["bounded"])
        test_kind = self.verdict(with_repair(self.plan, kind="test"))
        self.assertTrue(test_kind["bounded"], test_kind["reasons"])

    def test_an_unchanged_draft_is_no_repair(self):
        self.assertFalse(self.verdict(self.plan)["bounded"])

    def test_any_change_to_an_approved_task_needs_the_owner(self):
        for field, value in (("acceptance_criteria", ["T2 passes whatever happens"]),
                             ("verification", [{**tasks(self.plan)["T2"]["verification"][0], "value": "true"}]),
                             ("expected_paths", ["src/elsewhere.txt"]), ("objective", "Something else"),
                             ("kind", "implement")):
            draft = with_repair(self.plan)
            tasks(draft)["T2"][field] = value
            verdict = self.verdict(draft)
            self.assertFalse(verdict["bounded"], field)
            self.assertIn(f"T2: approved task changed ({field})", verdict["reasons"])

    def test_a_removed_task_or_a_lost_dependency_needs_the_owner(self):
        draft = with_repair(self.plan)
        draft["tasks"] = [t for t in draft["tasks"] if t["id"] != "T3"]
        for t in draft["tasks"]:
            t["after"] = [d for d in t["after"] if d != "T3"]
        sp1 = next(s for s in draft["subplans"] if s["id"] == "SP-1")
        sp1["audit_task"] = "T2"
        self.assertIn("T3: removed", self.verdict(draft)["reasons"])
        lost = with_repair(self.plan)
        tasks(lost)["T1.1"]["after"] = []                          # T2 no longer waits for T1 at all
        self.assertIn("T2: approved task no longer waits for T1", self.verdict(lost)["reasons"])

    def test_a_new_dependency_of_an_approved_task_on_an_approved_task_needs_the_owner(self):
        draft = with_repair(self.plan)
        tasks(draft)["T2"]["after"] = ["T1.1", "T4"]
        verdict = self.verdict(draft)
        self.assertFalse(verdict["bounded"])
        self.assertIn("T2: approved task now waits for approved task(s) T4", verdict["reasons"])

    def test_a_new_task_nothing_waits_for_or_of_another_kind_is_not_a_repair(self):
        loose = copy.deepcopy(self.plan)
        loose["tasks"].insert(1, support.plan_task("T1.1", "Extra feature", subplan="SP-1", kind="implement",
                                                   after=("T1",)))
        self.assertIn("T1.1: no approved task waits for it (new scope, not a repair)", self.verdict(loose)["reasons"])
        audit = self.verdict(with_repair(self.plan, kind="audit"))
        self.assertFalse(audit["bounded"])
        ui = with_repair(self.plan)
        tasks(ui)["T1.1"]["ui"] = True
        self.assertIn("T1.1: a UI task changes the approved design", self.verdict(ui)["reasons"])

    def test_gates_criteria_and_subplan_definitions_must_stay_as_approved(self):
        gate = with_repair(self.plan)
        gate["composition_gates"][0]["criteria"] = ["Anything composes"]
        self.assertIn("plan-level composition_gates of the stage changed", self.verdict(gate)["reasons"])
        criteria = with_repair(self.plan)
        criteria["subplans"][0]["acceptance_criteria"] = ["Weaker"]
        self.assertIn("SP-1: subplan definition changed (acceptance_criteria)", self.verdict(criteria)["reasons"])
        dropped = with_repair(self.plan)
        dropped["subplans"][0]["checkpoints"] = []
        self.assertIn("SP-1: a checkpoint was changed or removed", self.verdict(dropped)["reasons"])
        grown = with_repair(self.plan)
        grown["subplans"][0]["checkpoints"].append({"task": "T2", "purpose": "after the repair"})
        self.assertTrue(self.verdict(grown)["bounded"], self.verdict(grown)["reasons"])
        milestone = with_repair(self.plan)
        milestone["milestones"][0]["acceptance_criteria"] = ["Weaker"]
        self.assertIn("plan-level milestones of the stage changed", self.verdict(milestone)["reasons"])

    def test_a_repair_outside_the_approved_subplans_is_not_bounded(self):
        frozen = {**planner.stages.project(self.plan, ["SP-1"]), "revision": 1}
        draft = with_repair(self.plan, before="T7", subplan="SP-3")
        tasks(draft)["T1.1"]["after"] = ["T6"]
        verdict = classify(frozen, draft)                           # SP-3 is not approved: its tasks are not compared
        self.assertFalse(verdict["bounded"])


class StageFreeze(unittest.TestCase):
    """The stage freeze keeps the confirmation for a bounded repair with evidence and refuses everything else."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.repo = support.make_repository(root / "app")
        (self.repo / "src" / "T1.1_check.py").write_text((self.repo / "src" / "T1_check.py").read_text())
        support.git(self.repo, "add", "-A")
        support.git(self.repo, "commit", "-qm", "repair check")
        self.rdir = ts.staged_dir(root)
        with (self.rdir / "SPEC.md").open("a") as handle:
            handle.write("\n## Pruebas\n\n| Subplan | Dónde | Cómo | Qué debes ver |\n|---|---|---|---|\n"
                         "| SP-1 | Local | run | one works |\n")
        for item in (patch.object(flow, "_design", return_value=""),
                     patch.object(bt_plan_adapter, "repo_roots", return_value={"app": self.repo}),
                     patch("bt_config.get", side_effect=lambda key, default=None:
                           False if key == "gates.second_auditor" else default)):
            item.start()
            self.addCleanup(item.stop)
        flow.start(self.rdir)
        flow.confirm_outline("proj", self.rdir)
        flow.confirm("proj", self.rdir, "SP-1")
        self.first = bt_stages.freeze("proj", self.rdir, ["SP-1"])
        notes_dir = self.rdir / "RUN.notes"
        notes_dir.mkdir()
        (notes_dir / "T2.verify.md").write_text("T2 failed: the producer T1 renders Spanish in English\n")

    def draft(self, plan: dict) -> None:
        ts.write_draft(self.rdir, plan)

    def plan(self) -> dict:
        return json.loads((self.rdir / "PLAN.json").read_text())

    def test_a_bounded_repair_with_evidence_freezes_without_the_owner_and_says_so(self):
        self.draft(with_repair(self.plan()))
        with self.assertRaises(bt_stages.StageError) as ctx:          # without the evidence: the owner, as before
            bt_stages.freeze("proj", self.rdir, [])
        self.assertEqual(ctx.exception.code, "STAGE_SUBPLAN_UNCONFIRMED")
        entry = bt_stages.freeze("proj", self.rdir, [], repair_evidence=["RUN.notes/T2.verify.md"], by="solver")
        self.assertEqual(entry["revision"], self.first["revision"] + 1)
        frozen = planner.load_revision(self.rdir, entry["revision"])
        self.assertIn("T1.1", tasks(frozen))
        st = flow.state(self.rdir)["subplans"]["SP-1"]
        self.assertEqual((st["state"], st["by"], st["policy"]["rule"], st["policy"]["repair"], st["policy"]["requested_by"]),
                         ("confirmed", "policy", "D-241", ["T1.1"], "solver"))
        self.assertEqual(st["policy"]["previous"]["by"], "owner")
        self.assertEqual(st["policy"]["evidence"], ["RUN.notes/T2.verify.md"])
        said = activity.events(self.rdir)
        self.assertTrue(any(e["who"] == "Política" and "D-241" in e["text"] and "T1.1" in e["text"] for e in said))
        self.assertTrue(any(n["by"] == "policy" and n["kind"] == "decision" for n in notes.notes(self.rdir)))
        ctx_flow = {"flow": flow.state(self.rdir), "rows": {}}
        shown = bt_subplan_status.status(ctx_flow, {"id": "SP-1", "ref": None, "tasks": [1]},
                                         {"rounds": (None, []), "inputs": {}, "tasks": {}, "held": ["SP-1"], "queued": {},
                                          "decided": set(), "decisions": [], "gates": {}, "verified": {},
                                          "events": []})
        self.assertTrue(any("regla D-241" in d["text"] for d in shown["decisions"]), shown["decisions"])
        planner.stages.bind(self.rdir, self.plan())               # the run can join: no drift against the new stage

    def test_more_than_a_bounded_repair_still_needs_the_owner_and_nothing_is_frozen(self):
        draft = with_repair(self.plan())
        tasks(draft)["T2"]["acceptance_criteria"] = ["T2 passes whatever happens"]
        tasks(draft)["T2"]["verification"][0]["purpose"] = "T2 passes whatever happens"
        self.draft(draft)
        with self.assertRaises(bt_stages.StageError) as ctx:
            bt_stages.freeze("proj", self.rdir, [], repair_evidence=["RUN.notes/T2.verify.md"], by="solver")
        self.assertEqual(ctx.exception.code, "STAGE_REPAIR_UNBOUNDED")
        self.assertIn("acceptance_criteria", ctx.exception.message)
        self.assertEqual([r["revision"] for r in planner.list_revisions(self.rdir)], [self.first["revision"]])
        self.assertEqual(flow.state(self.rdir)["subplans"]["SP-1"]["state"], "changed")

    def test_a_change_to_the_confirmed_tests_or_requirements_is_not_a_bounded_repair(self):
        self.draft(with_repair(self.plan()))
        spec = (self.rdir / "SPEC.md").read_text()
        (self.rdir / "SPEC.md").write_text(spec.replace("| one works |", "| anything |"))
        with self.assertRaises(bt_stages.StageError) as ctx:
            bt_stages.freeze("proj", self.rdir, [], repair_evidence=["RUN.notes/T2.verify.md"], by="planner")
        self.assertEqual(ctx.exception.code, "STAGE_REPAIR_UNBOUNDED")
        self.assertIn("lo que confirmó el propietario no es lo aprobado", ctx.exception.message)
        (self.rdir / "SPEC.md").write_text(spec.replace("- R1. One", "- R1. One, or not"))
        with self.assertRaises(bt_stages.StageError) as ctx:
            bt_stages.freeze("proj", self.rdir, [], repair_evidence=["RUN.notes/T2.verify.md"], by="planner")
        self.assertIn("cambió un requisito de SPEC", ctx.exception.message)

    def test_the_evidence_is_run_evidence_that_names_the_task_that_found_the_defect(self):
        self.draft(with_repair(self.plan()))
        (self.rdir / "RUN.notes" / "T9.verify.md").write_text("T9 failed somewhere else\n")
        for refs in ([], ["SPEC.md"], ["../outside.md"], ["RUN.notes/missing.md"], ["RUN.notes/T9.verify.md"]):
            with self.assertRaises(bt_stages.StageError, msg=refs) as ctx:
                bt_stages.freeze("proj", self.rdir, [], repair_evidence=refs, by="solver")
            self.assertEqual(ctx.exception.code, "STAGE_REPAIR_EVIDENCE", refs)
        self.assertEqual(flow.state(self.rdir)["subplans"]["SP-1"]["state"], "changed")

    def test_the_run_joins_the_repaired_stage(self):
        self.draft(with_repair(self.plan()))
        frozen = bt_stages.freeze("proj", self.rdir, [], repair_evidence=["RUN.notes/T2.verify.md"], by="planner")
        (self.rdir / "RUN.owner.json").write_text(json.dumps({"run_id": "proj:REQ-900:r1", "backend": "dbos"}))
        joined = []
        message = bt_stages.run("proj", self.rdir, [], by="solver", via="cli",
                                repair_evidence=["RUN.notes/T2.verify.md"],
                                join=lambda: joined.append(1) or {"status": "joined", "to": "proj:REQ-900:r2",
                                                                  "counts": {"inherit": 2, "redo": 1}})
        self.assertEqual(joined, [1])                              # the Planner froze it; the Solucionador joins
        self.assertIn("El runtime durable sigue en la etapa", message)
        self.assertEqual(planner.latest(self.rdir)["revision"], frozen["revision"])   # the same stage, not a new one


if __name__ == "__main__":
    unittest.main()
