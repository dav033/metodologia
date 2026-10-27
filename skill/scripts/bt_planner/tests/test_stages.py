"""Stages (D-134): projection of the draft onto approved subplans, its freeze and the drift gate."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from bt_planner import contract as pc
from bt_planner import revisions as rev
from bt_planner import stages, sync

GOLDEN = Path(__file__).with_name("golden")


def _task(template: dict, tid: str, sp: str | None, kind: str, after: list[str], covers: str) -> dict:
    task = copy.deepcopy(template)
    criterion = f"{tid} behaves as specified"
    category = {"implement": "functional", "test": "integration", "audit": "static"}[kind]
    value = f"engine audit-ledger check docs/{tid}.findings.json" if kind == "audit" else f"pytest tests/{tid.lower()} -q"
    task.update(id=tid, title=f"Task {tid}", objective=f"Deliver the behaviour of {tid} and keep tests passing",
                after=after, kind=kind, covers=[covers], milestone_id="M1",
                expected_paths=[f"docs/{tid}.findings.json"] if kind == "audit" else [f"src/{tid.lower()}.py"],
                acceptance_criteria=[criterion],
                verification=[{"type": "command", "value": value, "purpose": criterion, "category": category}])
    task.pop("subplan_id", None)
    if sp:
        task["subplan_id"] = sp
    return task


def draft() -> dict:
    """SP-1 and SP-3 independent, SP-2 consumes SP-1's contract; T10 composes all three; T11 audits it."""
    plan = json.loads((GOLDEN / "input-1.2.0.json").read_text(encoding="utf-8"))
    template = plan["tasks"][0]
    plan.update(schema_version="1.3.0", requirements=["R1", "R2", "R3", "R4"], revision=1)
    tasks, subplans = [], []
    for n, (sp, req, first) in enumerate((("SP-1", "R1", 1), ("SP-2", "R2", 4), ("SP-3", "R3", 7)), start=1):
        build, test, audit = (f"T{first + i}" for i in range(3))
        after = ["T3"] if sp == "SP-2" else []
        tasks += [_task(template, build, sp, "implement", after, req), _task(template, test, sp, "test", [build], req),
                  _task(template, audit, sp, "audit", [test], req)]
        item = {"id": sp, "milestone_id": "M1", "title": f"Slice {n}", "outcome": f"Slice {n} is delivered and verified",
                "covers": [req], "acceptance_criteria": [f"{build} behaves as specified"],
                "produces": [{"contract": f"c{n}", "version": 1, "defined_by": build}], "consumes": [],
                "checkpoints": [{"task": test, "purpose": "integration"}], "integration_test_task": test, "audit_task": audit}
        if sp == "SP-2":
            item["consumes"] = [{"contract": "c1", "version": 1, "from": "SP-1", "dependency": "implementation",
                                 "verified_by": [test]}]
        subplans.append(item)
    gate = _task(template, "T10", None, "test", ["T3", "T6", "T9"], "R4")
    tasks += [gate, _task(template, "T11", None, "audit", ["T10"], "R4")]
    plan.update(tasks=tasks, subplans=subplans, composition_gates=[
        {"id": "CG-1", "subplans": ["SP-1", "SP-2", "SP-3"], "task": "T10", "audit_task": "T11",
         "criteria": ["T10 behaves as specified"]}])
    plan["milestones"] = [{"id": "M1", "title": "Slices", "acceptance_criteria": ["Every slice works"]}]
    plan.pop("interfaces", None)
    return plan


SPEC = "# Spec\n## Requirements\n- R1. One\n- R2. Two\n- R3. Three\n- R4. All together\n"


def plan_md(plan: dict, status: str = "draft") -> str:
    lines = [f"---\nstatus: {status}\n---\n# Plan\n\n### M1 — Slices"]
    for t in plan["tasks"]:
        after = f" · after: {', '.join(t['after'])}" if t["after"] else ""
        sp = f" · subplan: {t['subplan_id']}" if t.get("subplan_id") else ""
        lines.append(f"- [ ] {t['id']} — {t['title']} · repo: {t['repository']}{after}{sp}")
    return "\n".join(lines) + "\n"


class Projection(unittest.TestCase):
    def test_the_draft_is_valid_as_a_whole(self):
        self.assertEqual(pc.validate(draft(), strict_publication=True).errors, [])

    def test_a_stage_keeps_its_subplans_and_what_they_need_and_is_a_valid_plan(self):
        one = stages.project(draft(), ["SP-1"])
        self.assertEqual([t["id"] for t in one["tasks"]], ["T1", "T2", "T3"])
        self.assertEqual(one["requirements"], ["R1"])
        self.assertEqual(one["composition_gates"], [])
        self.assertEqual(one["stage"], {"version": 1, "subplans": ["SP-1"]})
        self.assertEqual(pc.validate(one, strict_publication=True).errors, [])
        both = stages.project(draft(), ["SP-3", "SP-1"])
        self.assertEqual(both["stage"]["subplans"], ["SP-1", "SP-3"])          # plan order
        self.assertNotIn("T10", [t["id"] for t in both["tasks"]])                # the gate waits for SP-2

    def test_a_subplan_that_consumes_another_cannot_run_without_it(self):
        with self.assertRaises(pc.PlanContractError) as ctx:
            stages.project(draft(), ["SP-2"])
        self.assertEqual(ctx.exception.code, "STAGE_NOT_CLOSED")
        self.assertIn("add SP-1 to the stage", " ".join(ctx.exception.issues))

    def test_every_subplan_is_the_whole_plan_and_gates_enter_with_their_members(self):
        whole = stages.project(draft(), ["SP-1", "SP-2", "SP-3"])
        self.assertTrue(stages.complete(draft(), whole))
        self.assertEqual([g["id"] for g in whole["composition_gates"]], ["CG-1"])
        expected = {k: v for k, v in draft().items()}
        self.assertEqual({k: v for k, v in whole.items() if k != "stage"}, expected)

    def test_unknown_subplans_and_plans_without_subplans(self):
        with self.assertRaises(pc.PlanContractError) as ctx:
            stages.project(draft(), ["SP-9"])
        self.assertEqual(ctx.exception.code, "STAGE_INVALID")
        flat = draft()
        flat.pop("subplans")
        self.assertNotIn("stage", stages.project(flat, []))

    def test_the_stage_field_is_validated(self):
        one = stages.project(draft(), ["SP-1"])
        bad = copy.deepcopy(one)
        bad["stage"]["subplans"] = ["SP-1", "SP-2"]
        self.assertTrue(any(e.startswith("STAGE_INVALID") for e in pc.validate(bad).errors))
        bad = copy.deepcopy(one)
        bad["stage"]["version"] = 2
        self.assertTrue(any("unsupported stage contract" in e for e in pc.validate(bad).errors))

    def test_splice_carries_a_scheduler_revision_into_the_draft(self):
        full = draft()
        old = stages.project(full, ["SP-1"])
        new = copy.deepcopy(old)
        extra = copy.deepcopy(new["tasks"][0])
        extra.update(id="T1.1", after=["T1"], title="Repair")
        new["tasks"].insert(1, extra)
        new["tasks"][2]["after"] = ["T1", "T1.1"]
        spliced = stages.splice(full, old, new)
        self.assertEqual([t["id"] for t in spliced["tasks"]][:4], ["T1", "T1.1", "T2", "T3"])
        self.assertEqual(pc.dumps({**stages.project(spliced, ["SP-1"]), "revision": new["revision"]}), pc.dumps(new))
        self.assertIn("T4", [t["id"] for t in spliced["tasks"]])                 # the rest of the draft is kept


class StagedDirectory(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.rdir = Path(self.tmp.name) / "REQ-077-staged"
        self.rdir.mkdir()
        (self.rdir / "SPEC.md").write_text(SPEC, encoding="utf-8")
        self.plan = draft()
        self.plan["plan_id"] = "REQ-077"
        self.write(self.plan)

    def write(self, plan: dict, status: str = "draft") -> None:
        (self.rdir / "PLAN.json").write_text(pc.dumps(plan), encoding="utf-8")
        (self.rdir / "PLAN.md").write_text(plan_md(plan, status), encoding="utf-8")

    def code(self, call) -> str:
        with self.assertRaises(pc.PlanContractError) as ctx:
            call()
        return ctx.exception.code

    def test_a_stage_freezes_while_the_rest_of_the_draft_is_unfinished(self):
        unfinished = copy.deepcopy(self.plan)
        unfinished["tasks"] = [t for t in unfinished["tasks"] if t.get("subplan_id") == "SP-1"]   # SP-2/3 have no tasks
        self.write(unfinished)
        self.assertFalse(sync.check(self.rdir).ok)                              # the whole draft is not publishable
        entry = sync.freeze_stage(self.rdir, ["SP-1"])
        self.assertEqual((entry["revision"], entry["source"]), (1, "approval"))
        self.assertEqual(entry["stage"]["pending_subplans"], ["SP-2", "SP-3"])
        self.assertFalse(entry["stage"]["complete"])
        self.assertEqual(rev.load_revision(self.rdir, 1)["stage"]["subplans"], ["SP-1"])
        self.assertEqual(sync.freeze_stage(self.rdir, ["SP-1"])["revision"], 1)   # idempotent
        self.assertEqual(sync.bind_approved(self.rdir, forced=True)["revision"], 1)
        self.assertEqual(self.code(lambda: sync.bind_approved(self.rdir)), "PLAN_NOT_APPROVED")

    def test_drift_is_judged_only_on_approved_scope(self):
        sync.freeze_stage(self.rdir, ["SP-1"])
        edited = copy.deepcopy(self.plan)
        edited["tasks"][4]["objective"] = "SP-2 is redefined while SP-1 runs, which is fine"
        edited["subplans"][2]["title"] = "Renamed later slice"
        (self.rdir / "PLAN.json").write_text(pc.dumps(edited), encoding="utf-8")
        with (self.rdir / "PLAN.md").open("a", encoding="utf-8") as handle:
            handle.write("\nNotes for SP-3.\n")
        self.assertEqual(sync.bind_approved(self.rdir, forced=True)["revision"], 1)
        edited["tasks"][0]["acceptance_criteria"] = ["T1 behaves differently"]
        (self.rdir / "PLAN.json").write_text(pc.dumps(edited), encoding="utf-8")
        self.assertEqual(self.code(lambda: sync.bind_approved(self.rdir, forced=True)), "PLAN_DRIFT")
        (self.rdir / "PLAN.json").write_text(pc.dumps(self.plan), encoding="utf-8")
        md = (self.rdir / "PLAN.md").read_text(encoding="utf-8").replace("T2 — Task T2", "T2 — Another task")
        (self.rdir / "PLAN.md").write_text(md, encoding="utf-8")
        self.assertEqual(self.code(lambda: sync.bind_approved(self.rdir, forced=True)), "PLAN_PROSE_DRIFT")
        self.write(self.plan)
        (self.rdir / "SPEC.md").write_text(SPEC.replace("R1. One", "R1. One, but faster") + "- R5. Later\n", encoding="utf-8")
        self.assertEqual(self.code(lambda: sync.bind_approved(self.rdir, forced=True)), "PLAN_REQUIREMENTS_DRIFT")
        (self.rdir / "SPEC.md").write_text(SPEC.replace("R2. Two", "R2. Two, revised"), encoding="utf-8")
        self.assertEqual(sync.bind_approved(self.rdir, forced=True)["revision"], 1)   # R2 is not approved yet
        (self.rdir / "PLAN.json").write_text("{", encoding="utf-8")
        self.assertEqual(self.code(lambda: sync.bind_approved(self.rdir, forced=True)), "PLAN_INVALID")

    def test_stages_grow_into_the_whole_plan_and_the_final_approval_needs_everything(self):
        sync.freeze_stage(self.rdir, ["SP-1"])
        second = sync.freeze_stage(self.rdir, ["SP-3"])
        self.assertEqual((second["revision"], second["stage"]["subplans"]), (2, ["SP-1", "SP-3"]))
        self.write(self.plan, "approved")
        whole = sync.approve_freeze(self.rdir)
        self.assertTrue(whole["stage"]["complete"])
        self.assertEqual(rev.load_revision(self.rdir, 3)["stage"]["subplans"], ["SP-1", "SP-2", "SP-3"])
        self.assertEqual(sync.bind_approved(self.rdir)["revision"], 3)
        shrunk = copy.deepcopy(self.plan)
        shrunk["subplans"] = shrunk["subplans"][:2]
        shrunk["tasks"] = [t for t in shrunk["tasks"] if t.get("subplan_id") != "SP-3"]
        (self.rdir / "PLAN.json").write_text(pc.dumps(shrunk), encoding="utf-8")
        self.assertEqual(self.code(lambda: sync.freeze_stage(self.rdir, [])), "STAGE_NOT_CUMULATIVE")

    def test_reapproval_of_changed_covered_spec_refreshes_pins_in_a_new_revision(self):
        sync.freeze_stage(self.rdir, ["SP-1"])
        (self.rdir / "SPEC.md").write_text(SPEC.replace("R1. One", "R1. One, revised"), encoding="utf-8")
        self.assertEqual(self.code(lambda: sync.bind_approved(self.rdir, forced=True)), "PLAN_REQUIREMENTS_DRIFT")
        self.assertEqual(sync.freeze_stage(self.rdir, ["SP-1"])["revision"], 2)
        self.assertEqual(sync.bind_approved(self.rdir, forced=True)["revision"], 2)
        self.assertEqual(sync.freeze_stage(self.rdir, ["SP-1"])["revision"], 2)

    def test_closed_markdown_requirement_heading_still_protects_approved_text(self):
        text = SPEC.replace("## Requirements", "## Requirements ##")
        (self.rdir / "SPEC.md").write_text(text, encoding="utf-8")
        sync.freeze_stage(self.rdir, ["SP-1"])
        (self.rdir / "SPEC.md").write_text(text.replace("R1. One", "R1. Changed"), encoding="utf-8")
        self.assertEqual(self.code(lambda: sync.bind_approved(self.rdir, forced=True)), "PLAN_REQUIREMENTS_DRIFT")

    def test_complete_reapproval_and_binding_detect_a_new_uncovered_spec_requirement(self):
        self.write(self.plan, "approved")
        sync.approve_freeze(self.rdir)
        (self.rdir / "SPEC.md").write_text(SPEC + "- R5. Forgotten requirement\n", encoding="utf-8")
        self.assertEqual(self.code(lambda: sync.approve_freeze(self.rdir)), "PLAN_INVALID")
        self.assertEqual(self.code(lambda: sync.bind_approved(self.rdir)), "PLAN_REQUIREMENTS_DRIFT")
        self.assertEqual(len(rev.list_revisions(self.rdir)), 1)

    def test_final_approval_requires_every_spec_requirement_even_without_draft_tasks(self):
        self.write(self.plan, "approved")
        (self.rdir / "SPEC.md").write_text(SPEC + "- R5. Forgotten requirement\n", encoding="utf-8")
        with self.assertRaises(pc.PlanContractError) as ctx:
            sync.approve_freeze(self.rdir)
        self.assertEqual(ctx.exception.code, "PLAN_INVALID")
        self.assertTrue(any("R5" in issue for issue in ctx.exception.issues))
        self.assertEqual(rev.list_revisions(self.rdir), [])

    def test_an_invalid_stage_is_refused_with_the_validator_errors(self):
        broken = copy.deepcopy(self.plan)
        del broken["tasks"][0]["risk"]
        self.write(broken)
        self.assertEqual(self.code(lambda: sync.freeze_stage(self.rdir, ["SP-1"])), "PLAN_INVALID")
        self.assertFalse((self.rdir / "plan-revisions" / "PLAN.r1.json").exists())
        self.write(self.plan)
        md = (self.rdir / "PLAN.md").read_text(encoding="utf-8").replace("after: T1 · subplan: SP-1", "subplan: SP-1")
        (self.rdir / "PLAN.md").write_text(md, encoding="utf-8")
        with self.assertRaises(pc.PlanContractError) as ctx:
            sync.freeze_stage(self.rdir, ["SP-1"])
        self.assertTrue(any("T2.after" in issue for issue in ctx.exception.issues))

    def test_the_final_approval_refuses_a_stage_short_of_the_draft(self):
        orphan = copy.deepcopy(self.plan)
        lone = copy.deepcopy(orphan["tasks"][0])
        lone.update(id="T12", after=["T11"], subplan_id="SP-9")
        orphan["tasks"].append(lone)                   # a task of a subplan nobody declared can never be approved
        self.write(orphan, "approved")
        self.assertEqual(self.code(lambda: sync.approve_freeze(self.rdir)), "STAGE_INCOMPLETE")


if __name__ == "__main__":
    unittest.main()
