"""«Ejecutar subplan» through the Scheduler (D-134): eligibility, start or join, gates and labels."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bt_page_now
import bt_page_run
import bt_plan_adapter
import bt_planning_flow as flow
import bt_requirements_gate as gate
import bt_review
import bt_scheduler_run
import bt_stages
import bt_subplan_sessions as sessions
import owner_e2e_support as support
import test_planning_flow as pf

planner = bt_plan_adapter.planner


def staged_dir(root: Path) -> Path:
    """A requirement whose draft is the three-subplan fixture, with SPEC and PLAN.md that agree with it."""
    rdir = root / "REQ-900-staged"
    rdir.mkdir()
    plan = support.three_subplan_plan()
    write_draft(rdir, plan)
    (rdir / "SPEC.md").write_text("# Spec\n## Requirements\n- R1. One\n- R2. Two\n- R3. Three\n- R4. Together\n",
                                  encoding="utf-8")
    return rdir


def write_draft(rdir: Path, plan: dict, status: str = "draft") -> None:
    (rdir / "PLAN.json").write_text(planner.dumps(plan), encoding="utf-8")
    lines = [f"---\nstatus: {status}\n---\n# Plan\n\n### M1 — Owner E2E"]
    for t in plan["tasks"]:
        after = f" · after: {', '.join(t['after'])}" if t["after"] else ""
        sp = f" · subplan: {t['subplan_id']}" if t.get("subplan_id") else ""
        ui = " · ui: yes" if t.get("ui") else ""
        lines.append(f"- [ ] {t['id']} — {t['title']} · repo: app{after}{sp}{ui}")
    (rdir / "PLAN.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def freeze(rdir: Path, repo: Path, add: list[str]) -> dict:
    return planner.freeze_stage(rdir, add, "REQ-900", {"app": repo}, True)


class Eligibility(unittest.TestCase):
    setUp = pf.FlowTests.setUp
    write_plan = pf.FlowTests.write_plan
    create = pf.FlowTests.create
    spec = pf.FlowTests.spec

    def test_only_confirmed_and_unchanged_subplans_on_the_flow_can_form_a_stage(self):
        self.assertIn("planificación conjunta", bt_stages.eligibility(self.rdir, ["SP-1"])[0])
        self.spec("location given")
        self.write_plan(pf.PLAN)
        flow.start(self.rdir)
        self.assertEqual(bt_stages.eligibility(self.rdir, ["SP-1"]), ["falta confirmar el esqueleto de hitos y subplanes"])
        flow.confirm_outline("demo", self.rdir)
        flow.confirm("demo", self.rdir, "SP-1")
        self.assertEqual(bt_stages.eligibility(self.rdir, ["SP-1"]), [])
        refused = bt_stages.eligibility(self.rdir, ["SP-1", "SP-2"])
        self.assertEqual(len(refused), 1)
        self.assertIn("SP-2: sin confirmar", refused[0])
        changed = copy.deepcopy(pf.PLAN)
        changed["tasks"][0]["acceptance_criteria"] = ["Orders persist forever."]
        self.write_plan(changed)
        self.assertIn("SP-1: cambió después de confirmarlo", bt_stages.eligibility(self.rdir, ["SP-1"])[0])

    def test_an_unconfirmed_subplan_is_refused_before_anything_is_written(self):
        self.spec("location given")
        self.write_plan(pf.PLAN)
        flow.start(self.rdir)
        flow.confirm_outline("demo", self.rdir)
        with self.assertRaises(bt_stages.StageError) as ctx:
            bt_stages.run("demo", self.rdir, ["SP-1"], start=lambda *a: self.fail("nothing may start"))
        self.assertEqual(ctx.exception.code, "STAGE_SUBPLAN_UNCONFIRMED")
        self.assertFalse((self.rdir / "plan-revisions").exists())

    def test_a_plan_run_by_the_durable_runtime_is_refused_before_anything_is_frozen(self):
        self.spec("location given")
        self.write_plan(pf.PLAN)
        flow.start(self.rdir)
        flow.confirm_outline("demo", self.rdir)
        flow.confirm("demo", self.rdir, "SP-1")
        (self.rdir / "RUN.owner.json").write_text(json.dumps({"run_id": "demo:REQ-001:r1", "backend": "dbos"}),
                                                  encoding="utf-8")
        with self.assertRaises(bt_stages.StageError) as ctx:
            bt_stages.run("demo", self.rdir, ["SP-1"], start=lambda *a: self.fail("nothing may start"))
        self.assertEqual(ctx.exception.code, "DURABLE_OWNER")
        self.assertFalse((self.rdir / "plan-revisions").exists())
        with self.assertRaises(bt_stages.StageError):
            bt_stages.start_or_join("demo", self.rdir, start=lambda *a: self.fail("nothing may start"))


class StartOrJoin(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.rdir = Path(self.tmp.name) / "REQ-900-staged"
        self.rdir.mkdir()
        self.started = []
        for item in (patch("bt_plan_adapter.launch_problem", return_value=None),
                     patch("bt_scheduler_adapter.plan_compatibility_report", return_value=None)):
            item.start()
            self.addCleanup(item.stop)

    def start(self, project, req, rdir):
        self.started.append(req)
        return True

    def test_a_requirement_without_a_run_starts_one(self):
        with patch("bt_scheduler_adapter.authority", return_value="none"):
            self.assertIn("empezó", bt_stages.start_or_join("proj", self.rdir, start=self.start))
        self.assertEqual(self.started, ["REQ-900"])

    def test_a_running_owner_joins_at_its_next_quiet_point_and_nothing_else_starts(self):
        with patch("bt_scheduler_adapter.authority", return_value="scheduler"), \
                patch("bt_scheduler_ops.owner_pids", return_value=[4242]), \
                patch.object(bt_scheduler_run, "join", side_effect=AssertionError("never rebased under an owner")):
            self.assertIn("en cuanto terminen", bt_stages.start_or_join("proj", self.rdir, start=self.start))
        self.assertEqual(self.started, [])

    def test_an_idle_run_joins_now_and_resumes(self):
        with patch("bt_scheduler_adapter.authority", return_value="scheduler"), \
                patch("bt_scheduler_ops.owner_pids", return_value=[]), \
                patch.object(bt_scheduler_run, "join", return_value="r1 → r2: kept 3, redo 0, new 3, removed 0"):
            self.assertIn("se unió", bt_stages.start_or_join("proj", self.rdir, start=self.start))
        self.assertEqual(self.started, ["REQ-900"])

    def test_a_costly_join_asks_for_confirmation_and_a_drift_is_refused(self):
        error = bt_scheduler_run.adapter.core.SchedulerError("JOIN_NEEDS_CONFIRM", "would redo 5 accepted task(s)")
        with patch("bt_scheduler_adapter.authority", return_value="scheduler"), \
                patch("bt_scheduler_ops.owner_pids", return_value=[]), \
                patch.object(bt_scheduler_run, "join", side_effect=error):
            self.assertIn("revise --confirm", bt_stages.start_or_join("proj", self.rdir, start=self.start))
        with patch("bt_plan_adapter.launch_problem", return_value="PLAN_DRIFT: T1: changed"), \
                patch("bt_scheduler_adapter.authority", return_value="none"), \
                self.assertRaises(bt_stages.StageError) as ctx:
            bt_stages.start_or_join("proj", self.rdir, start=self.start)
        self.assertEqual(ctx.exception.code, "PLAN_DRIFT")
        with patch("bt_scheduler_adapter.authority", return_value="legacy"), \
                self.assertRaises(bt_stages.StageError) as ctx:
            bt_stages.start_or_join("proj", self.rdir, start=self.start)
        self.assertEqual(ctx.exception.code, "AUTHORITY_CONFLICT")


class OwnerJoin(unittest.TestCase):
    """The owner loop pauses dispatch once while a newer approved revision waits, and stops only when nothing is alive."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.rdir = Path(self.tmp.name) / "REQ-900-x"
        self.rdir.mkdir()
        self.db = self.rdir / "SCHEDULER.db"
        self.pauses = []
        self.scheduler = SimpleNamespace(pause=lambda by, reason: self.pauses.append(by))
        bt_scheduler_run._JOIN_NOTED.clear()

    def ready(self, *, paused=False, live=False):
        snap = SimpleNamespace(revision=1, paused=paused)
        wiring = object()
        with patch("bt_scheduler_adapter.run_db_path", return_value=self.db), \
                patch.object(bt_scheduler_run.m4_runtime, "has_live_attempts", return_value=live), \
                patch.object(bt_scheduler_run.m4_runtime, "has_pending_streams", return_value=False):
            return bt_scheduler_run._join_ready(self.rdir, wiring, self.scheduler, snap)

    def test_pause_once_wait_for_live_attempts_then_stop(self):
        with patch("bt_scheduler_adapter.join_target", return_value=2), \
                patch("bt_scheduler_adapter.join_cost", return_value=()):
            self.assertFalse(self.ready(live=True))
            self.assertFalse(self.ready(paused=True, live=True))
            self.assertTrue(self.ready(paused=True))
        self.assertEqual(self.pauses, ["stage-join"])
        marker = json.loads(self.db.with_name(self.db.stem + ".join.json").read_text(encoding="utf-8"))
        self.assertEqual(marker, {"target": 2, "paused_by_join": True})

    def test_a_newer_target_preserves_the_join_pause(self):
        with patch("bt_scheduler_adapter.join_target", side_effect=[2, 3]), \
                patch("bt_scheduler_adapter.join_cost", return_value=()):
            self.assertFalse(self.ready(live=True))
            self.assertTrue(self.ready(paused=True))
        marker = json.loads(self.db.with_name(self.db.stem + ".join.json").read_text())
        self.assertTrue(marker["paused_by_join"])
        self.assertEqual(marker["target"], 3)

    def test_recovery_after_marker_write_before_pause_still_drains_dispatch(self):
        self.db.with_name(self.db.stem + ".join.json").write_text(
            json.dumps({"target": 2, "paused_by_join": True}))
        with patch("bt_scheduler_adapter.join_target", return_value=2), \
                patch("bt_scheduler_adapter.join_cost", return_value=()):
            self.assertFalse(self.ready(live=True))
        self.assertEqual(self.pauses, ["stage-join"])

    def test_crash_after_rebase_reconciles_runtime_and_releases_join_pause(self):
        marker = self.db.with_name(self.db.stem + ".join.json")
        marker.write_text(json.dumps({"target": 2, "paused_by_join": True}))
        with patch("bt_scheduler_adapter.run_db_path", return_value=self.db), \
                patch("bt_scheduler_adapter.run_identity", return_value={"revision": 2}), \
                patch("bt_scheduler_adapter.join_target", return_value=None), \
                patch("bt_scheduler_adapter.rebase_to_latest") as rebase, \
                patch.object(bt_scheduler_run, "rebind_runtime") as rebind, \
                patch("bt_scheduler_adapter.apply_control") as control:
            bt_scheduler_run.join(self.rdir)
        rebase.assert_not_called()
        rebind.assert_called_once_with(self.rdir)
        control.assert_called_once_with(self.rdir, "resume", by="stage-join")
        self.assertFalse(marker.exists())

    def test_an_operator_pause_is_not_released_by_the_join_and_nothing_waits_without_a_target(self):
        with patch("bt_scheduler_adapter.join_target", return_value=None):
            self.assertFalse(self.ready())
        with patch("bt_scheduler_adapter.join_target", return_value=3), \
                patch("bt_scheduler_adapter.join_cost", return_value=()):
            self.assertTrue(self.ready(paused=True))
        self.assertEqual(self.pauses, [])
        self.assertFalse(json.loads(self.db.with_name(self.db.stem + ".join.json").read_text())["paused_by_join"])

    def test_a_join_that_redoes_too_much_accepted_work_never_pauses_the_run(self):
        with patch("bt_scheduler_adapter.join_target", return_value=2), \
                patch("bt_scheduler_adapter.join_cost", return_value=("T1", "T2", "T3", "T4", "T5")), \
                patch("bt_rework_impact.ceiling", return_value=3):
            self.assertFalse(self.ready())
        self.assertEqual(self.pauses, [])
        self.assertFalse(self.db.with_name(self.db.stem + ".join.json").exists())

    def test_automatic_join_refuses_drift_after_the_stage_was_frozen(self):
        with patch("bt_scheduler_adapter.join_target", return_value=2), \
                patch("bt_plan_adapter.launch_problem", return_value="PLAN_DRIFT: approved task changed"), \
                patch("bt_scheduler_adapter.join_cost") as cost:
            self.assertFalse(self.ready())
        cost.assert_not_called()
        self.assertEqual(self.pauses, [])


class GatesAndRevisions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.repo = support.make_repository(root / "app")
        self.rdir = staged_dir(root)

    def test_edit_between_confirmation_check_and_freeze_never_publishes_unconfirmed_content(self):
        with (self.rdir / "SPEC.md").open("a") as handle:
            handle.write("\n## Pruebas\n\n| Subplan | Dónde | Cómo | Qué debes ver |\n|---|---|---|---|\n"
                         "| SP-1 | Local | run | one works |\n")
        with patch.object(flow, "_design", return_value=""):
            flow.start(self.rdir)
            flow.confirm_outline("proj", self.rdir)
            flow.confirm("proj", self.rdir, "SP-1")
        self.assertEqual(bt_stages.eligibility(self.rdir, ["SP-1"]), [])
        original = bt_plan_adapter.stage_problem

        def edit_after_check(*args, **kwargs):
            result = original(*args, **kwargs)
            changed = json.loads((self.rdir / "PLAN.json").read_text())
            changed["tasks"][0]["objective"] = "Unconfirmed concurrent edit"
            (self.rdir / "PLAN.json").write_text(planner.dumps(changed))
            return result

        with patch.object(bt_plan_adapter, "repo_roots", return_value={"app": self.repo}), \
                patch("bt_config.get", side_effect=lambda key, default=None: False if key == "gates.second_auditor" else default), \
                patch.object(bt_plan_adapter, "stage_problem", side_effect=edit_after_check), \
                self.assertRaises(bt_stages.StageError) as ctx:
            bt_stages.freeze("proj", self.rdir, ["SP-1"])
        self.assertEqual(ctx.exception.code, "STAGE_APPROVAL_CHANGED")
        self.assertEqual(bt_plan_adapter.revisions(self.rdir), [])
        self.assertIn("cambió después", bt_stages.eligibility(self.rdir, ["SP-1"])[0])

    def test_a_stage_with_one_audit_gets_its_cross_check_and_keeps_the_confirmations(self):
        with (self.rdir / "SPEC.md").open("a") as handle:
            handle.write("\n## Pruebas\n\n| Subplan | Dónde | Cómo | Qué debes ver |\n|---|---|---|---|\n"
                         "| SP-1 | Local | run | one works |\n")
        with patch.object(flow, "_design", return_value=""):
            flow.start(self.rdir)
            flow.confirm_outline("proj", self.rdir)
            flow.confirm("proj", self.rdir, "SP-1")
        audit = next(s["audit_task"] for s in json.loads((self.rdir / "PLAN.json").read_text())["subplans"]
                     if s["id"] == "SP-1")
        with patch.object(bt_plan_adapter, "repo_roots", return_value={"app": self.repo}), \
                patch("bt_config.get", side_effect=lambda key, default=None: True if key == "gates.second_auditor" else default):
            entry = bt_stages.freeze("proj", self.rdir, ["SP-1"])
        tasks = {t["id"]: t for t in json.loads((self.rdir / "PLAN.json").read_text())["tasks"]}
        cross = tasks[f"{audit}b"]
        self.assertEqual((cross["kind"], cross["subplan_id"], cross["after"]), ("audit", "SP-1", [audit]))
        sp1 = next(s for s in json.loads((self.rdir / "PLAN.json").read_text())["subplans"] if s["id"] == "SP-1")
        self.assertEqual(sp1["audit_task"], f"{audit}b")                    # the cross-check now closes the subplan
        self.assertTrue(all(f"{audit}b" in t["after"] for t in tasks.values() if audit in t["after"] and t is not cross))
        self.assertIn(f"{audit}b —", (self.rdir / "PLAN.md").read_text())
        self.assertEqual(entry["stage"]["subplans"], ["SP-1"])
        self.assertEqual(flow.state(self.rdir)["subplans"]["SP-1"]["state"], "confirmed")
        others = [t for t in tasks.values() if t.get("subplan_id") != "SP-1" and t["kind"] == "audit"]
        self.assertTrue(all(not t["id"].endswith("b") for t in others))    # only the stage's audit is cross-checked

    def test_the_review_merge_refuses_until_the_approved_stage_holds_the_whole_plan(self):
        freeze(self.rdir, self.repo, ["SP-1"])
        self.assertIn("faltan SP-2, SP-3", bt_review.stage_gap(self.rdir))
        with patch("bt_verification.gate", return_value=[]):
            self.assertIn("STAGE_INCOMPLETE", bt_review.merge("proj", self.rdir, push=False)[0])
        freeze(self.rdir, self.repo, ["SP-2", "SP-3"])
        self.assertIn("ejecutada", bt_review.stage_gap(self.rdir))
        changed = json.loads((self.rdir / "PLAN.json").read_text())
        changed["tasks"].append({**changed["tasks"][0], "id": "T99"})
        (self.rdir / "PLAN.json").write_text(planner.dumps(changed))
        self.assertIn("PLAN_DRIFT", bt_review.stage_gap(self.rdir))
        (self.rdir / "PLAN.json").write_text("{", encoding="utf-8")
        self.assertIn("no se puede leer", bt_review.stage_gap(self.rdir))           # fail closed

    def test_closing_waits_for_the_latest_approved_revision_to_finish(self):
        entry = freeze(self.rdir, self.repo, ["SP-1", "SP-2", "SP-3"])
        identity = {"revision": entry["revision"], "plan_sha256": entry["sha256"]}
        tasks = {t["id"]: "completed" for t in bt_plan_adapter.latest_plan(self.rdir)["tasks"]}
        with patch("bt_scheduler_adapter.run_identity", return_value=identity), \
                patch("bt_scheduler_ops.status", return_value={"task_states": tasks}):
            self.assertEqual(bt_review.stage_gap(self.rdir), "")
            identity["revision"] = 0
            self.assertIn("ejecutada", bt_review.stage_gap(self.rdir))
            identity["revision"] = entry["revision"]
            tasks["T1"] = "active"
            self.assertIn("T1", bt_review.stage_gap(self.rdir))

    def test_a_scheduler_revision_is_spliced_into_the_draft_never_over_it(self):
        freeze(self.rdir, self.repo, ["SP-1"])
        base = bt_plan_adapter.latest_plan(self.rdir)
        revised = copy.deepcopy(base)
        repair = copy.deepcopy(next(t for t in revised["tasks"] if t["id"] == "T1"))
        repair.update(id="T1.1", after=["T1"], title="Repair from evidence")
        revised["tasks"].insert(1, repair)
        next(t for t in revised["tasks"] if t["id"] == "T2")["after"] = ["T1", "T1.1"]
        revised["revision"] = 2
        bt_plan_adapter.freeze_revision(self.rdir, revised, "healing")
        draft = json.loads((self.rdir / "PLAN.json").read_text(encoding="utf-8"))
        ids = [t["id"] for t in draft["tasks"]]
        self.assertEqual(ids[:4], ["T1", "T1.1", "T2", "T3"])
        self.assertIn("T4", ids)                                           # SP-2 is still being planned
        self.assertEqual(bt_plan_adapter.stage_subplans(self.rdir), ["SP-1"])
        self.assertEqual(planner.stages.project(draft, ["SP-1"])["tasks"],
                         bt_plan_adapter.latest_plan(self.rdir)["tasks"])

    def test_resume_needs_an_approved_revision_not_the_newest_one(self):
        first = freeze(self.rdir, self.repo, ["SP-1"])
        freeze(self.rdir, self.repo, ["SP-3"])
        ref = {"plan_id": "REQ-900", "revision": 1, "sha256": first["sha256"]}
        with patch("bt_plan_adapter.plan_consumer_problem", return_value=None):
            self.assertIsNone(bt_plan_adapter.resume_problem(self.rdir, {"plan_ref": ref}))
            self.assertIn("PLAN_REF_MISMATCH",
                          bt_plan_adapter.resume_problem(self.rdir, {"plan_ref": {**ref, "sha256": "0" * 64}}))


class RequirementsWaiver(unittest.TestCase):
    def test_planning_files_are_waived_for_the_scheduler_and_other_evidence_still_blocks(self):
        with tempfile.TemporaryDirectory() as temp:
            rdir = Path(temp)
            (rdir / "SPEC.md").write_text("# Scope\n", encoding="utf-8")
            (rdir / "PLAN.md").write_text("---\nstatus: draft\nexecution_contract: requirements-v1\n---\n# Plan\n",
                                          encoding="utf-8")
            (rdir / "NOTES.md").write_text("limits\n", encoding="utf-8")
            gate.record(rdir, {"goal": "g", "scope": "s", "requirements": "r", "limits": "l", "acceptance": "a",
                               "approval": "owner", "evidence": ["NOTES.md"], "unresolved": []})
            (rdir / "SPEC.md").write_text("# Scope\n## Pruebas\n| SP-2 | Local | x | y |\n", encoding="utf-8")
            self.assertEqual(gate.check(rdir)["status"], "needs_revalidation")
            self.assertEqual(gate.check(rdir, gate.PLANNING_FILES)["status"], "ready")
            (rdir / "NOTES.md").write_text("other limits\n", encoding="utf-8")
            self.assertEqual(gate.check(rdir, gate.PLANNING_FILES)["status"], "needs_revalidation")


class Labels(unittest.TestCase):
    def test_run_page_and_now_card_show_the_stage(self):
        run = {"stage": {"revision": 2, "subplans": ["SP-1", "SP-3"], "outside": ["SP-2"], "complete": False,
                         "joining": None}}
        self.assertIn("etapa SP-1, SP-3 · faltan 1 subplanes", bt_page_run._stage_kpi(run))
        self.assertEqual(bt_page_run._stage_kpi({}), "")
        self.assertIn("faltan 1 subplanes", bt_page_now._stage({"stage": run["stage"]}))
        self.assertEqual(bt_page_now._stage({"stage": {**run["stage"], "complete": True}}), "")


class SessionsStayHandsOn(unittest.TestCase):
    def test_the_autonomous_session_mode_is_retired(self):
        self.assertEqual(sessions.MODES, ("hands",))


if __name__ == "__main__":
    unittest.main()
