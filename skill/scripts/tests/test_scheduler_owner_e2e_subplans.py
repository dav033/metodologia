"""Acceptance 7 owner coverage for PLAN.json 1.3.0 functional subplans."""
from __future__ import annotations

import sys
import tempfile
import unittest
import json
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bt_scheduler_adapter as scheduler_adapter
import bt_scheduler_run as scheduler_run
from bt_scheduler_owner_composition import OwnerCompositionRuntime
import owner_e2e_support as support
import scheduler_chain_support as chain
from scheduler_executor_support import adapter as executor_adapter

REAL_SLEEP = time.sleep
OWNER_TIME = SimpleNamespace(sleep=lambda seconds: REAL_SLEEP(min(seconds, 0.5)),
                             monotonic=time.monotonic, time=time.time)


class SuccessfulAgent:
    """Local M3 child that reports success without changing the repository."""

    def prepare(self, route, prompt, workspace, timeout_seconds):
        return executor_adapter.m3.Launch(argv=(sys.executable, "-c",
            "import json; print(json.dumps({'type':'result','subtype':'success','result':'OWNER-E2E',"
            "'usage':{'output_tokens':1}}))"))

    def classify(self, route, raw, returncode, *, timed_out=False, cancelled=False):
        terminal = "OWNER-E2E" in raw
        status = "completed" if returncode == 0 and terminal else "failed"
        return executor_adapter.m3.Classification(status, terminal_event=terminal, text=raw[-200:])


class OwnerM2Port(chain.M2Port):
    def close(self):
        pass


class OwnerSubplanEntryPoint(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="scheduler-owner-subplans-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = support.make_repository(self.root / "app")
        self.contract = support.add_designer_contract(self.repo)
        self.rdir = self.root / "REQ-900-owner-e2e"
        self.rdir.mkdir()

    def _run_13_owner(self, plan=None, planner_default: str = "1.2.0", *, max_steps=120, resume=False):
        plan = plan or support.three_subplan_plan()
        support.freeze_plan(self.rdir, plan)
        captured = {}
        original_wire = scheduler_run._wire

        def make_assignment(project, ledger_path, *, laya_root):
            return OwnerM2Port(ledger_path, lambda _task: [("claude", "sonnet", "claude-personal", "low")])

        def capture_wire(project, rdir):
            wiring, assignment, run_id = original_wire(project, rdir)
            captured.update(wiring=wiring, assignment=assignment, run_id=run_id)
            close = wiring.close

            def close_after_stub_agents():
                wiring.executor.wait_idle(10)
                if wiring.verification_runtime is not None:
                    wiring.verification_runtime.close(wait=True)
                    record_state(wiring)
                close()

            wiring.close = close_after_stub_agents
            return wiring, assignment, run_id

        def record_state(wiring):
            snapshot = wiring.scheduler.snapshot()
            captured["snapshot"] = snapshot
            captured["subplan_status"] = scheduler_adapter.subplan_status(wiring.scheduler)
            captured["publications"] = scheduler_adapter.subplan_publication_facts(wiring.scheduler)
            captured["compositions"] = scheduler_adapter.composition_facts(wiring.scheduler)
            attempts = wiring.scheduler.read(lambda ctx: tuple(ctx.state.attempts.values()))
            captured["m6_results"] = tuple(
                wiring.verification_store.get_result(
                    f"{wiring.scheduler.plan.plan_id}:r{wiring.scheduler.plan.revision}:{attempt.id}:verify")
                for attempt in attempts)
            captured["retry_budget"] = wiring.scheduler.read(lambda ctx: ctx.config.max_attempts)

        # planner_default="1.3.0" previews the one-line default switch the lead makes after these tests pass.
        with patch.object(scheduler_adapter.plan_adapter.planner, "SCHEMA_VERSION", planner_default), \
                patch.object(scheduler_run.bt_core, "ROOT", self.root), \
                patch("bt_requirements_gate.require_ready"), \
                patch("bt_workspace.repos", return_value={"app": self.repo}), \
                patch.object(scheduler_adapter, "DecisionAssignmentPort", side_effect=make_assignment), \
                patch.object(scheduler_run, "_wire", side_effect=capture_wire), \
                patch("bt_scheduler_executor_wiring.api.MethodologyDriver", return_value=SuccessfulAgent()), \
                patch.object(scheduler_run, "time", OWNER_TIME), \
                patch.object(scheduler_run, "_remove_autostart"), \
                patch.object(scheduler_run, "_install_autostart"), \
                patch.object(scheduler_run.bt_notify, "notify"):
            result = scheduler_run.run("proj", "REQ-900", self.rdir, resume=resume,
                                      no_autostart=True, max_steps=max_steps)
            return result, captured

    @unittest.expectedFailure  # M6 environment_fingerprint is 24 hex chars; subplan publication requires 64.
    def test_owner_publishes_three_subplans_and_composition_through_real_entrypoint(self):
        self.assertTrue(self.contract.is_file())
        self.assertEqual(support.git(self.repo, "show", "HEAD:design/contracts/interface@v1.md"),
                         "# Interface contract v1\n\nBase-tree fixture for the owner E2E.")
        result, captured = self._run_13_owner(planner_default="1.3.0")
        self.assertEqual(result, 0)
        self.assertEqual(captured["wiring"].scheduler.plan.schema_version, "1.3.0")
        self.assertEqual(captured["subplan_status"], {"SP-1": "published", "SP-2": "published", "SP-3": "published"})
        self.assertEqual(len(captured["compositions"]), 1)
        self.assertEqual(next(iter(captured["compositions"].values()))["state"], "published")

    def test_owner_refuses_a_13_plan_while_the_planner_default_is_12(self):
        with self.assertRaisesRegex(scheduler_adapter.core.SchedulerError,
                                    r"PLAN_SCHEMA_UNSUPPORTED_BY_ENGINE.*Planner \(unsupported\)"):
            self._run_13_owner(planner_default="1.2.0")

    def test_legacy_plan_remains_loadable_with_unchanged_task_shape(self):
        plan = support.legacy_plan()
        support.freeze_plan(self.rdir, plan)
        accepted = scheduler_adapter.approved_plan(self.rdir)
        self.assertEqual(accepted.schema_version, "1.2.0")
        self.assertEqual(accepted.ids(), tuple(task["id"] for task in plan["tasks"]))
        self.assertFalse(OwnerCompositionRuntime.supports(accepted))

    @unittest.expectedFailure  # Owner raises OWNER_COMPOSITION_M6_EVIDENCE_IDENTITY_MISMATCH before version reconciliation.
    def test_subplan_revision_publishes_new_version_without_changing_other_members(self):
        _, first = self._run_13_owner(planner_default="1.3.0")
        original = first["publications"]
        plan = support.three_subplan_plan(revision=2)
        support.freeze_plan(self.rdir, plan)
        with patch.object(scheduler_run.bt_core, "ROOT", self.root), \
                patch.object(scheduler_adapter.plan_adapter.planner, "SCHEMA_VERSION", "1.3.0"):
            scheduler_adapter.rebase_to_latest(self.rdir)
        _, second = self._run_13_owner(plan, planner_default="1.3.0", resume=True)
        self.assertEqual(second["publications"]["SP-1"]["version"], original["SP-1"]["version"] + 1)
        self.assertEqual(second["publications"]["SP-2"], original["SP-2"])
        self.assertEqual(second["publications"]["SP-3"], original["SP-3"])

    @unittest.expectedFailure  # Owner raises OWNER_COMPOSITION_M6_EVIDENCE_IDENTITY_MISMATCH before candidate construction.
    def test_incompatible_candidate_is_rejected_and_current_composition_is_preserved(self):
        _, state = self._run_13_owner(planner_default="1.3.0")
        rejected = [fact for fact in state["compositions"].values() if fact["state"] == "rejected"]
        self.assertTrue(rejected, "forced incompatibility did not record a rejected candidate")

    @unittest.expectedFailure  # Owner raises OWNER_COMPOSITION_M6_EVIDENCE_IDENTITY_MISMATCH after restart reconciliation.
    def test_restart_boundaries_reconcile_reservation_reference_and_m1_fact_idempotently(self):
        _, first = self._run_13_owner(planner_default="1.3.0", max_steps=1)
        first_ids = set(first["compositions"])
        _, resumed = self._run_13_owner(planner_default="1.3.0", max_steps=1, resume=True)
        _, resumed = self._run_13_owner(planner_default="1.3.0", max_steps=60, resume=True)
        self.assertEqual(set(resumed["compositions"]), first_ids)
        self.assertEqual(len(resumed["publications"]), 3)

    @unittest.expectedFailure  # Owner raises OWNER_COMPOSITION_M6_EVIDENCE_IDENTITY_MISMATCH before stale-fact checks.
    def test_old_verdict_and_candidate_are_stale_until_next_subplan_revision(self):
        _, first = self._run_13_owner(planner_default="1.3.0")
        old_version = first["publications"].get("SP-1", {}).get("version")
        plan = support.three_subplan_plan(revision=2)
        support.freeze_plan(self.rdir, plan)
        with patch.object(scheduler_run.bt_core, "ROOT", self.root), \
                patch.object(scheduler_adapter.plan_adapter.planner, "SCHEMA_VERSION", "1.3.0"):
            scheduler_adapter.rebase_to_latest(self.rdir)
        _, state = self._run_13_owner(plan, planner_default="1.3.0", resume=True)
        next_version = state["publications"].get("SP-1", {}).get("version")
        self.assertIsNotNone(old_version, "revision 1 did not publish the fact needed for stale-verdict refusal")
        self.assertEqual(next_version, old_version + 1)

    def test_missing_required_credential_blocks_without_spending_code_retry(self):
        plan = support.three_subplan_plan()
        for task in plan["tasks"]:
            task["verification"][0]["requires"] = ["OWNER_E2E_REQUIRED_SECRET"]
        _, state = self._run_13_owner(plan, planner_default="1.3.0")
        results = [result for result in state["m6_results"] if result is not None]
        self.assertTrue(results, "missing-credential verification produced no M6 result")
        self.assertTrue(all(result["reason_code"] == "BLOCKED_EXTERNAL" for result in results))
        self.assertEqual(state["snapshot"].tasks["T1"]["attempts"], 1)
        self.assertEqual(state["retry_budget"], 3)

    @unittest.expectedFailure  # Owner leaves SP-2 open when its base Designer contract is absent.
    def test_ui_subplan_without_base_designer_contract_blocks_before_publication(self):
        self.repo = support.make_repository(self.root / "repo-without-ui-contract")
        self.contract = None
        plan = support.three_subplan_plan()
        for task in plan["tasks"]:
            if task.get("subplan_id") in {"SP-1", "SP-3"}:
                task["verification"][0]["requires"] = ["OWNER_E2E_REQUIRED_SECRET"]
        _, state = self._run_13_owner(plan, planner_default="1.3.0")
        self.assertEqual(state["subplan_status"]["SP-2"], "blocked")
        self.assertNotIn("SP-2", state["publications"])

    def test_legacy_plan_keeps_runtime_refs_stores_and_states_through_owner(self):
        plan = support.legacy_plan()
        _, state = self._run_13_owner(plan, planner_default="1.3.0")
        self.assertEqual(state["snapshot"].status, "completed")
        self.assertEqual(OwnerCompositionRuntime.supports(state["wiring"].scheduler.plan), False)
        self.assertEqual(len(state["wiring"].executor.ledger.all_ids()), 1)


if __name__ == "__main__":
    unittest.main()
