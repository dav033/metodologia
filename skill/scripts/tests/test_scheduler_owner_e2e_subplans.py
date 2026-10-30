"""Acceptance 7 owner coverage for PLAN.json 1.3.0 functional subplans."""
from __future__ import annotations

import sys
import tempfile
import unittest
import json
import threading
import time
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bt_scheduler_adapter as scheduler_adapter
import bt_scheduler_run as scheduler_run
import bt_config
import bt_design_approval
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


class ContractProducingAgent(SuccessfulAgent):
    """Create the UI contract from the actual design task workspace, leaving HEAD unchanged."""

    def prepare(self, route, prompt, workspace, timeout_seconds):
        if "## Task T4:" in prompt:
            contract = Path(workspace.path) / "design/contracts/interface@v1.md"
            contract.parent.mkdir(parents=True, exist_ok=True)
            contract.write_text("# Interface contract v1\n\nProduced by the design task.\n", encoding="utf-8")
        return super().prepare(route, prompt, workspace, timeout_seconds)


class ConflictingAgent(SuccessfulAgent):
    """Create incompatible changes from two member subplans on their real M3 worktrees."""

    def prepare(self, route, prompt, workspace, timeout_seconds):
        for task_id, content in (("T1", "subplan one\n"), ("T9", "subplan three\n")):
            if f"## Task {task_id}:" in prompt:
                (Path(workspace.path) / "src" / "shared-contract.txt").write_text(content, encoding="utf-8")
        return super().prepare(route, prompt, workspace, timeout_seconds)


class OwnerM2Port(chain.M2Port):
    def close(self):
        pass


class OwnerSubplanEntryPoint(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="scheduler-owner-subplans-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self._config_state = patch.object(bt_config, "STATE", self.root / ".state")
        self._config_state.start()
        self.addCleanup(self._config_state.stop)
        self._root_env = patch.dict(os.environ, {
            "BITACORA_ROOT": str(self.root / "bitacora"),
            "HOME": str(self.root),
            "PATH": os.pathsep.join((str(Path(sys.executable).parent), "/usr/bin", "/bin")),
        })
        self._root_env.start()
        self.addCleanup(self._root_env.stop)
        self.repo = support.make_repository(self.root / "app")
        self.contract = support.add_designer_contract(self.repo)
        self.rdir = self.root / "REQ-900-owner-e2e"
        self.rdir.mkdir()

    def _run_13_owner(self, plan=None, *, max_steps=300, resume=False, agent_factory=SuccessfulAgent,
                      approve_before_run=True):
        plan = plan or support.three_subplan_plan()
        support.freeze_plan(self.rdir, plan)
        ui = next((item.get("ui") for item in plan.get("subplans", [])
                   if isinstance(item, dict) and isinstance(item.get("ui"), dict)), None)
        if approve_before_run and ui is not None and self.contract is not None:
            ref = f"{ui['contract']}@v{ui['version']}"
            if bt_design_approval.approvals(self.rdir).get(ref, {}).get("status") != "approved":
                bt_design_approval.decide(self.rdir, self.repo, ref, True, "E2E fixture approval",
                                          "fixture-owner", "test")
        captured = {}
        original_wire = scheduler_run._wire

        def make_assignment(project, ledger_path, *, laya_root):
            return OwnerM2Port(ledger_path, lambda _task: [("claude", "sonnet", "claude", "low")])

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
            captured["m6_manifests"] = {
                attempt.task_id: wiring.verification_store.get_result_manifest(attempt.evidence).decode("utf-8")
                for attempt in attempts if isinstance(attempt.evidence, str)
                and attempt.evidence.startswith("m6://result/")}
            if wiring.composition_runtime is not None:
                captured["current_composition"] = wiring.composition_runtime.git.rev_parse(
                    f"refs/compositions/{wiring.scheduler.plan.plan_id}/current")
            captured["retry_budget"] = wiring.scheduler.read(lambda ctx: ctx.config.max_attempts)

        with patch.object(scheduler_run.bt_core, "ROOT", self.root), \
                patch("bt_requirements_gate.require_ready"), \
                patch("bt_workspace.repos", return_value={"app": self.repo}), \
                patch.object(scheduler_adapter, "DecisionAssignmentPort", side_effect=make_assignment), \
                patch.object(scheduler_run, "_wire", side_effect=capture_wire), \
                patch("bt_scheduler_executor_wiring.api.MethodologyDriver", return_value=agent_factory()), \
                patch.object(scheduler_run, "time", OWNER_TIME), \
                patch.object(scheduler_run, "_remove_autostart"), \
                patch.object(scheduler_run, "_install_autostart"), \
                patch.object(scheduler_run.bt_notify, "notify"):
            result = scheduler_run.run("proj", "REQ-900", self.rdir, resume=resume,
                                      no_autostart=True, max_steps=max_steps)
            return result, captured

    def test_owner_publishes_three_subplans_and_composition_through_real_entrypoint(self):
        self.assertTrue(self.contract.is_file())
        self.assertEqual(support.git(self.repo, "show", "HEAD:design/contracts/interface@v1.md"),
                         "# Interface contract v1\n\nBase-tree fixture for the owner E2E.")
        result, captured = self._run_13_owner()
        self.assertEqual(result, 0)
        self.assertEqual(captured["wiring"].scheduler.plan.schema_version, "1.3.0")
        self.assertEqual(captured["subplan_status"], {"SP-1": "published", "SP-2": "published", "SP-3": "published"})
        self.assertEqual(len(captured["compositions"]), 1)
        self.assertEqual(next(iter(captured["compositions"].values()))["state"], "published")

    def test_design_task_line_contract_is_approved_before_ui_task_starts(self):
        self.repo = support.make_repository(self.root / "app-produced-contract")
        self.contract = None
        original = bt_design_approval.check_tree
        approval_seen = {}

        def owner_approves_when_gate_sees_design_output(rdir, repo, base, path):
            if path == "design/contracts/interface@v1.md" and "approved" not in approval_seen:
                revision = bt_design_approval.revision_for_contract(
                    self.root, "proj", rdir, "interface@v1", repo)
                snapshot = bt_design_approval.contract_snapshot(repo, path, revision)
                if snapshot:
                    record = bt_design_approval.decide(rdir, repo, "interface@v1", True,
                                                       "Approved after design task", "fixture-owner", "test",
                                                       revision=revision)
                    approval_seen.update(revision=revision, digest=record["sha256"], base=base)
            return original(rdir, repo, base, path)

        with patch.object(bt_design_approval, "check_tree", side_effect=owner_approves_when_gate_sees_design_output):
            result, state = self._run_13_owner(agent_factory=ContractProducingAgent,
                                               approve_before_run=False)
        self.assertEqual(result, 0)
        self.assertIn("revision", approval_seen, "the owner gate never saw the design task's contract")
        self.assertNotIn("design/contracts/interface@v1.md",
                         support.git(self.repo, "ls-tree", "-r", "--name-only", "HEAD"))
        self.assertEqual(approval_seen["digest"], bt_design_approval.approvals(self.rdir)["interface@v1"]["sha256"])
        self.assertEqual(state["snapshot"].tasks["T5"]["state"], "completed")

    def test_legacy_plan_remains_loadable_with_unchanged_task_shape(self):
        plan = support.legacy_plan()
        support.freeze_plan(self.rdir, plan)
        accepted = scheduler_adapter.approved_plan(self.rdir)
        self.assertEqual(accepted.schema_version, "1.2.0")
        self.assertEqual(accepted.ids(), tuple(task["id"] for task in plan["tasks"]))
        self.assertFalse(OwnerCompositionRuntime.supports(accepted))

    def test_subplan_revision_publishes_new_version_without_changing_other_members(self):
        _, first = self._run_13_owner()
        original = first["publications"]
        plan = support.three_subplan_plan(revision=2)
        next(task for task in plan["tasks"] if task["id"] == "T1")["objective"] += " after the subplan revision"
        support.freeze_plan(self.rdir, plan)
        with patch.object(scheduler_run.bt_core, "ROOT", self.root):
            scheduler_adapter.rebase_to_latest(self.rdir)
            scheduler_run.rebind_runtime(self.rdir)
        _, second = self._run_13_owner(plan, resume=True)
        self.assertEqual(second["publications"]["SP-1"]["version"], original["SP-1"]["version"] + 1)
        for subplan_id in ("SP-2", "SP-3"):
            with self.subTest(subplan_id=subplan_id):
                self.assertEqual(second["publications"][subplan_id]["version"], original[subplan_id]["version"])
                self.assertEqual(second["publications"][subplan_id]["commit"], original[subplan_id]["commit"])

    def test_incompatible_candidate_is_rejected_and_current_composition_is_preserved(self):
        _, first = self._run_13_owner()
        current = first["current_composition"]
        plan = support.three_subplan_plan(revision=2)
        for task_id in ("T1", "T9"):
            task = next(item for item in plan["tasks"] if item["id"] == task_id)
            task["objective"] = f"{task_id} makes the forced incompatible contract edit"
        support.freeze_plan(self.rdir, plan)
        with patch.object(scheduler_run.bt_core, "ROOT", self.root):
            scheduler_adapter.rebase_to_latest(self.rdir)
            scheduler_run.rebind_runtime(self.rdir)
        _, state = self._run_13_owner(plan, resume=True, agent_factory=ConflictingAgent)
        rejected = [fact for fact in state["compositions"].values() if fact["state"] == "rejected"]
        self.assertTrue(rejected, "forced incompatibility did not record a rejected candidate")
        self.assertEqual(state["current_composition"], current,
                         "rejected candidate changed the previously published current composition")

    def test_restart_boundaries_reconcile_reservation_reference_and_m1_fact_idempotently(self):
        _, first = self._run_13_owner(max_steps=1)
        first_ids = set(first["compositions"])
        _, resumed = self._run_13_owner(max_steps=1, resume=True)
        _, resumed = self._run_13_owner(max_steps=300, resume=True)
        self.assertTrue(first_ids.issubset(resumed["compositions"]))
        self.assertEqual(len(resumed["publications"]), 3)
        self.assertEqual(len(resumed["compositions"]), 1)
        self.assertEqual(next(iter(resumed["compositions"].values()))["state"], "published")

    def _run_with_verdict_after_owner_pass(self, held_task: str, completed_first: set[str]):
        """Land `held_task`'s M6 verdict after the owner's reconcile pass and before its terminal snapshot.

        Under load the last verdict reached M1 in that window and the owner judged the run by a snapshot its pass
        had not seen: it ended `blocked` with SP-2 accepted but unpublished, or `completed` with the composition
        still a candidate. The verdict is held in its M6 thread until every task in `completed_first` is done,
        then released from inside `reconcile_compositions` (the pass's last reader) and awaited there.
        """
        held, release, landed, released_in_window = (threading.Event() for _ in range(4))
        original_submit = scheduler_adapter.core.SchedulerCore.submit_verdict
        original_reconcile = OwnerCompositionRuntime.reconcile_compositions

        def submit_verdict(core, verdict):
            if verdict.task_id == held_task and not release.is_set():
                held.set()
                release.wait(120)              # bounded: on a timeout the verdict lands anyway and the test fails below
                try:
                    return original_submit(core, verdict)
                finally:
                    landed.set()
            return original_submit(core, verdict)

        def reconcile_compositions(runtime):
            published = original_reconcile(runtime)
            if held.is_set() and not release.is_set():
                tasks = runtime.scheduler.snapshot().tasks
                if all(tasks[task_id]["state"] == "completed" for task_id in completed_first):
                    release.set()
                    if landed.wait(120):
                        released_in_window.set()
            return published

        with patch.object(scheduler_adapter.core.SchedulerCore, "submit_verdict", submit_verdict), \
                patch.object(OwnerCompositionRuntime, "reconcile_compositions", reconcile_compositions):
            result, state = self._run_13_owner()
        self.assertTrue(released_in_window.is_set(), f"{held_task}'s verdict never landed inside the window")
        return result, state

    def test_subplan_verdict_landing_after_owner_pass_is_published_before_the_run_ends(self):
        others = {f"T{number}" for number in range(1, 12)} - {"T8"}
        result, state = self._run_with_verdict_after_owner_pass("T8", others)
        self.assertEqual(result, 0)
        self.assertEqual(state["subplan_status"], {"SP-1": "published", "SP-2": "published", "SP-3": "published"})
        self.assertEqual(state["snapshot"].status, "completed")

    def test_composition_audit_verdict_landing_after_owner_pass_is_published_before_the_run_ends(self):
        result, state = self._run_with_verdict_after_owner_pass("T13", {f"T{number}" for number in range(1, 13)})
        self.assertEqual(result, 0)
        self.assertEqual(state["snapshot"].status, "completed")
        self.assertEqual(len(state["compositions"]), 1)
        self.assertEqual(next(iter(state["compositions"].values()))["state"], "published")

    def test_old_verdict_and_candidate_are_stale_until_next_subplan_revision(self):
        _, first = self._run_13_owner()
        old_version = first["publications"].get("SP-1", {}).get("version")
        plan = support.three_subplan_plan(revision=2)
        next(task for task in plan["tasks"] if task["id"] == "T1")["objective"] += " after the subplan revision"
        support.freeze_plan(self.rdir, plan)
        with patch.object(scheduler_run.bt_core, "ROOT", self.root):
            scheduler_adapter.rebase_to_latest(self.rdir)
            scheduler_run.rebind_runtime(self.rdir)
        _, state = self._run_13_owner(plan, resume=True)
        next_version = state["publications"].get("SP-1", {}).get("version")
        self.assertIsNotNone(old_version, "revision 1 did not publish the fact needed for stale-verdict refusal")
        self.assertEqual(next_version, old_version + 1)

    def test_missing_required_credential_blocks_without_spending_code_retry(self):
        plan = support.three_subplan_plan()
        for task in plan["tasks"]:
            task["verification"][0]["requires"] = ["OWNER_E2E_REQUIRED_SECRET"]
        with patch.dict(os.environ, {"OWNER_E2E_REQUIRED_SECRET": ""}):
            _, state = self._run_13_owner(plan)
        results = [result for result in state["m6_results"] if result is not None]
        self.assertTrue(results, "missing-credential verification produced no M6 result")
        self.assertTrue(all(result["reason_code"] == "BLOCKED_EXTERNAL" for result in results))
        self.assertEqual(state["snapshot"].tasks["T1"]["attempts"], 1)
        self.assertEqual(state["retry_budget"], 3)

    def test_ui_subplan_without_base_designer_contract_blocks_before_publication(self):
        self.repo = support.make_repository(self.root / "repo-without-ui-contract")
        self.contract = None
        plan = support.three_subplan_plan()
        for task in plan["tasks"]:
            if task.get("subplan_id") in {"SP-1", "SP-3"}:
                task["verification"][0]["requires"] = ["OWNER_E2E_REQUIRED_SECRET"]
        _, state = self._run_13_owner(plan)
        self.assertEqual(state["subplan_status"]["SP-2"], "blocked")
        self.assertNotIn("SP-2", state["publications"])

    def test_legacy_plan_keeps_runtime_refs_stores_and_states_through_owner(self):
        plan = support.legacy_plan()
        _, state = self._run_13_owner(plan)
        self.assertEqual(state["snapshot"].status, "completed")
        self.assertEqual(OwnerCompositionRuntime.supports(state["wiring"].scheduler.plan), False)
        self.assertEqual(len(state["wiring"].executor.ledger.all_ids()), 1)


if __name__ == "__main__":
    unittest.main()
