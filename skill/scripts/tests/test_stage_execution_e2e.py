"""D-134 end to end: «Ejecutar subplan» runs a stage through the real Scheduler owner (M1–M6, fake agent), the plan keeps
being planned, a second stage joins the same run keeping accepted work, approved scope cannot drift, and the
requirement cannot be closed while subplans are missing."""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bt_config
import bt_plan_adapter
import bt_review
import bt_scheduler_adapter as scheduler_adapter
import bt_scheduler_run as scheduler_run
import bt_stages
import bt_verification
import owner_e2e_support as support
from test_scheduler_owner_e2e_subplans import OwnerM2Port, SuccessfulAgent
from test_stages import write_draft

REAL_SLEEP = time.sleep
OWNER_TIME = SimpleNamespace(sleep=lambda seconds: REAL_SLEEP(min(seconds, 0.5)), monotonic=time.monotonic, time=time.time)
SPEC = """# Spec
## Requirements
- R1. One
- R2. Two
- R3. Three
- R4. Together

## Pruebas

| Subplan | Dónde | Cómo | Qué debes ver |
|---|---|---|---|
| SP-1 | Local | run it | one works |
| SP-2 | Local | run it | two works |
| SP-3 | Local | run it | three works |
"""


class StagedExecution(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="stage-e2e-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for item in (patch.object(bt_config, "STATE", self.root / ".state"),
                     patch.dict(os.environ, {"BITACORA_ROOT": str(self.root / "bitacora"), "HOME": str(self.root),
                                             "PATH": os.pathsep.join((str(Path(sys.executable).parent), "/usr/bin", "/bin"))})):
            item.start()
            self.addCleanup(item.stop)
        self.repo = support.make_repository(self.root / "app")
        support.add_designer_contract(self.repo)
        self.rdir = self.root / "REQ-900-staged"
        self.rdir.mkdir()
        self.draft = support.three_subplan_plan()
        write_draft(self.rdir, self.draft)
        (self.rdir / "SPEC.md").write_text(SPEC, encoding="utf-8")
        self.captured: dict = {}
        self.owner_runs = 0
        for item in (patch("bt_stages.eligibility", return_value=[]),          # the owner's confirmations: test_stages
                     patch("bt_plan_adapter.repo_roots", return_value={"app": self.repo}),
                     patch("bt_scheduler_ops.owner_pids", return_value=[])):
            item.start()
            self.addCleanup(item.stop)

    # ---- the real owner process, in this process, with a fake agent ----------------------------------------------
    def owner(self, project: str, req: str, rdir: Path) -> bool:
        self.owner_runs += 1
        original_wire, original_run = scheduler_run._wire, scheduler_run.run

        def make_assignment(project, ledger_path, *, laya_root):
            return OwnerM2Port(ledger_path, lambda _task: [("claude", "sonnet", "claude", "low")])

        def capture_wire(project, rdir):
            wiring, assignment, run_id = original_wire(project, rdir)
            close = wiring.close

            def close_after_agents():
                wiring.executor.wait_idle(10)
                if wiring.verification_runtime is not None:
                    wiring.verification_runtime.close(wait=True)
                self.captured.update(
                    run_id=run_id, snapshot=wiring.scheduler.snapshot(),
                    status=scheduler_adapter.subplan_status(wiring.scheduler),
                    publications=scheduler_adapter.subplan_publication_facts(wiring.scheduler),
                    attempts={tid: [a.id for a in wiring.scheduler.read(lambda ctx: tuple(ctx.state.attempts.values()))
                                    if a.task_id == tid] for tid in wiring.scheduler.plan.ids()})
                close()

            wiring.close = close_after_agents
            return wiring, assignment, run_id

        with patch.object(scheduler_run.bt_core, "ROOT", self.root), \
                patch("bt_workspace.repos", return_value={"app": self.repo}), \
                patch.object(scheduler_adapter, "DecisionAssignmentPort", side_effect=make_assignment), \
                patch.object(scheduler_run, "_wire", side_effect=capture_wire), \
                patch.object(scheduler_run, "run", side_effect=lambda *a, **k: original_run(*a, **{**k, "max_steps": 300})), \
                patch("bt_scheduler_executor_wiring.api.MethodologyDriver", return_value=SuccessfulAgent()), \
                patch.object(scheduler_run, "time", OWNER_TIME), \
                patch.object(scheduler_run, "_remove_autostart"), patch.object(scheduler_run, "_install_autostart"), \
                patch.object(scheduler_run.bt_notify, "notify"):
            resume = scheduler_adapter.authority(rdir) == scheduler_adapter.AUTHORITY
            self.assertEqual(scheduler_run.dispatch(project, req, rdir, resume=resume, no_autostart=True), 0)
        return True

    def run_stage(self, sid: str) -> str:
        with patch.object(scheduler_run.bt_core, "ROOT", self.root):
            return bt_stages.run("proj", self.rdir, [sid], start=self.owner)

    def lines(self) -> list[str]:
        out = subprocess.run(["git", "for-each-ref", "--format=%(refname)", "refs/m3/line/"], cwd=self.repo,
                             capture_output=True, text=True, check=True).stdout
        return out.split()

    def test_two_stages_run_through_one_scheduler_run(self):
        # ---- SP-1 holds one audit: with the policy on, the click would add its cross-check (test_stages
        # GatesAndRevisions); this run keeps the fixture's task list, so the policy is off -------------------------
        bt_config.set_value("gates.second_auditor", False)

        # ---- stage 1: SP-1 alone, while SP-2 and SP-3 are still a draft -----------------------------------------
        message = self.run_stage("SP-1")
        self.assertIn("Etapa r1 aprobada con SP-1", message)
        self.assertEqual(bt_plan_adapter.stage_subplans(self.rdir, 1), ["SP-1"])
        first = dict(self.captured)
        self.assertEqual(first["snapshot"].status, "completed")
        self.assertEqual(sorted(first["snapshot"].tasks), ["T1", "T2", "T3"])          # nothing outside the stage runs
        self.assertEqual(first["status"], {"SP-1": "published"})
        sp1 = first["publications"]["SP-1"]
        self.assertTrue(any(ref.endswith("/SP-1") for ref in self.lines()))
        projection = json.loads((self.rdir / "RUN.projection.json").read_text(encoding="utf-8"))
        self.assertEqual((projection["stage"]["subplans"], projection["stage"]["outside"]), (["SP-1"], ["SP-2", "SP-3"]))
        self.assertIn("status: draft", (self.rdir / "PLAN.md").read_text(encoding="utf-8"))   # still being planned

        # ---- the Planner keeps editing the rest; an edit to approved scope is refused -----------------------------
        planning = copy.deepcopy(self.draft)
        next(t for t in planning["tasks"] if t["id"] == "T5")["objective"] += " (redefined with the owner)"
        write_draft(self.rdir, planning)
        report = scheduler_adapter.plan_compatibility_report(self.rdir)
        self.assertIsNone(bt_plan_adapter.launch_problem(self.rdir, forced=True, compatibility_report=report))
        drifted = copy.deepcopy(planning)
        next(t for t in drifted["tasks"] if t["id"] == "T1")["acceptance_criteria"] = ["T1 does something else"]
        write_draft(self.rdir, drifted)
        self.assertTrue(bt_plan_adapter.launch_problem(self.rdir, forced=True, compatibility_report=report)
                        .startswith("PLAN_DRIFT"))
        with self.assertRaises(bt_stages.StageError) as refused:
            bt_stages.start_or_join("proj", self.rdir, start=self.owner)
        self.assertEqual(refused.exception.code, "PLAN_DRIFT")
        write_draft(self.rdir, planning)

        # ---- stage 2: SP-3 joins the same run by rebase ------------------------------------------------------------
        runs_before = self.owner_runs
        message = self.run_stage("SP-3")
        self.assertIn("Etapa r2 aprobada con SP-1, SP-3", message)
        self.assertIn("se unió", message)
        self.assertEqual(self.owner_runs, runs_before + 1)
        second = dict(self.captured)
        self.assertEqual(second["run_id"], first["run_id"])                            # the same run, resumed
        self.assertEqual(second["snapshot"].revision, 2)
        self.assertEqual(second["snapshot"].status, "completed")
        self.assertEqual(sorted(second["snapshot"].tasks), ["T1", "T10", "T11", "T2", "T3", "T9"])
        for task in ("T1", "T2", "T3"):                                                 # accepted work was kept
            self.assertEqual(second["attempts"][task], first["attempts"][task], task)
        self.assertEqual(second["status"], {"SP-1": "published", "SP-3": "published"})
        self.assertEqual((second["publications"]["SP-1"]["version"], second["publications"]["SP-1"]["commit"]),
                         (sp1["version"], sp1["commit"]))
        self.assertEqual(second["publications"]["SP-3"]["version"], 1)
        self.assertTrue(any(ref.endswith("/SP-3") for ref in self.lines()))
        self.assertNotIn("T12", second["snapshot"].tasks)              # CG-1 composes SP-2 too: it waits for its stage
        manifest = bt_plan_adapter.revisions(self.rdir)
        self.assertEqual([(r["revision"], r["stage"]["subplans"]) for r in manifest], [(1, ["SP-1"]), (2, ["SP-1", "SP-3"])])

        # ---- closing: D-131 and the stage gate both refuse while SP-2 is missing --------------------------------
        for sid in ("SP-1", "SP-3"):
            self.assertIn("aprobado", bt_verification.decide("proj", self.rdir, sid, "approved"))
        self.assertEqual(bt_verification.gate(self.rdir), ["SP-2: se está construyendo"])
        self.assertIn("faltan SP-2", bt_review.stage_gap(self.rdir))
        with patch("bt_verification.gate", return_value=[]):
            self.assertIn("STAGE_INCOMPLETE", bt_review.merge("proj", self.rdir, push=False)[0])


if __name__ == "__main__":
    unittest.main()
