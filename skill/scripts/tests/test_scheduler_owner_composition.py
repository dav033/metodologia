"""Owner composition identities and supported repository topology."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
import hashlib
import json
from unittest.mock import patch
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bt_scheduler_owner_composition import CompositionRuntimeError, OwnerCompositionRuntime, composition_store_path
from bt_scheduler_owner_workspace import bind_owner_marker, ensure_owner_marker
import bt_scheduler_adapter as m1_adapter
from bt_scheduler_recovery_adapter import RecoveryAdapter
from bt_composition_adapter import PropagationChange
from bt_composition_adapter import GitSubprocessPort

m1 = m1_adapter.core


class OwnerCompositionRuntimeTests(unittest.TestCase):
    def test_store_version_counter_is_reconciled_before_next_publication(self):
        owner = SimpleNamespace(plan=SimpleNamespace(plan_id="REQ-1", subplans=(SimpleNamespace(id="SP-1"),)),
                                scheduler=object(), store=SimpleNamespace(list_versions=lambda *_: (
                                    SimpleNamespace(version=1, commit="a" * 40, manifest_sha256="b" * 64),)),
                                _line_commits=lambda _subplan: ("c" * 40, "a" * 40))
        with patch("bt_scheduler_owner_reconciliation.version_adapter.version_facts", return_value={}), \
             patch("bt_scheduler_owner_reconciliation.m1_adapter.record_subplan_version",
                   side_effect=RuntimeError("accepted identity is stale")) as record, \
             patch("bt_scheduler_owner_reconciliation.version_adapter.record_stale_version") as stale:
            OwnerCompositionRuntime._reconcile_store_version_counters(owner)
        record.assert_called_once_with(owner.scheduler, "SP-1", 1, "a" * 40, "b" * 64)
        stale.assert_called_once_with(owner.scheduler, "SP-1", 1, "a" * 40, "b" * 64)

    def test_store_version_whose_commit_is_not_the_line_tip_is_recorded_stale(self):
        owner = SimpleNamespace(plan=SimpleNamespace(plan_id="REQ-1", subplans=(SimpleNamespace(id="SP-1"),)),
                                scheduler=object(), store=SimpleNamespace(list_versions=lambda *_: (
                                    SimpleNamespace(version=1, commit="a" * 40, manifest_sha256="b" * 64),)),
                                _line_commits=lambda _subplan: ("c" * 40, "e" * 40))
        with patch("bt_scheduler_owner_reconciliation.version_adapter.version_facts", return_value={}), \
             patch("bt_scheduler_owner_reconciliation.m1_adapter.record_subplan_version") as record, \
             patch("bt_scheduler_owner_reconciliation.version_adapter.record_stale_version") as stale:
            OwnerCompositionRuntime._reconcile_store_version_counters(owner)
        record.assert_not_called()
        stale.assert_called_once_with(owner.scheduler, "SP-1", 1, "a" * 40, "b" * 64)

    def test_completed_published_gate_is_rebound_and_not_rebuilt(self):
        gate = SimpleNamespace(task="T4", subplans=("SP-1",))
        owner = OwnerCompositionRuntime.__new__(OwnerCompositionRuntime)
        owner.plan = SimpleNamespace(composition_gates=(gate,), subplans=(SimpleNamespace(id="SP-1"),), revision=2)
        owner.scheduler = SimpleNamespace(snapshot=lambda: SimpleNamespace(tasks={"T4": {"state": "completed"}}))
        owner.store = object()
        owner.git = SimpleNamespace(tree_oid=lambda _commit: "d" * 40)
        candidate = SimpleNamespace(state="published", members={"SP-1": 1}, manifest_sha256="c" * 64,
                                    integrated_commit="e" * 40)
        fact = {"state": "published", "members": {"SP-1": 1}, "revision": 1}
        with patch("bt_scheduler_owner_composition.m1_adapter.accepted_attempt_facts", return_value={}), \
             patch("bt_scheduler_owner_composition.m1_adapter.composition_facts", return_value={"C1": fact}), \
             patch("bt_scheduler_owner_composition.m1_adapter.subplan_publication_facts",
                   return_value={"SP-1": {"version": 1, "revision": 2}}), \
             patch("bt_scheduler_owner_composition.bt_composition_adapter.get_candidate", return_value=candidate), \
             patch("bt_scheduler_owner_composition.m1_adapter.record_composition") as rebind:
            self.assertEqual(OwnerCompositionRuntime.reconcile_compositions(owner), ())
        rebind.assert_called_once_with(owner.scheduler, "published", "C1", candidate.members,
                                       candidate.manifest_sha256, tree_digest="d" * 40)

    def test_candidate_gate_fact_is_rebound_after_revision_without_rebuild(self):
        gate = SimpleNamespace(task="T4", subplans=("SP-1",))
        owner = OwnerCompositionRuntime.__new__(OwnerCompositionRuntime)
        owner.plan = SimpleNamespace(composition_gates=(gate,), subplans=(SimpleNamespace(id="SP-1"),), revision=2)
        owner.scheduler = SimpleNamespace(snapshot=lambda: SimpleNamespace(tasks={"T4": {"state": "completed"}}))
        owner.store = object()
        owner.git = SimpleNamespace(tree_oid=lambda _commit: "d" * 40)
        candidate = SimpleNamespace(state="candidate", members={"SP-1": 1}, manifest_sha256="c" * 64,
                                    integrated_commit="e" * 40)
        fact = {"state": "candidate", "members": {"SP-1": 1}, "revision": 1}
        with patch("bt_scheduler_owner_reconciliation.m1_adapter.accepted_attempt_facts", return_value={}), \
             patch("bt_scheduler_owner_reconciliation.m1_adapter.composition_facts", return_value={"C1": fact}), \
             patch("bt_scheduler_owner_composition.m1_adapter.subplan_publication_facts",
                   return_value={"SP-1": {"version": 1, "revision": 2}}), \
             patch("bt_scheduler_owner_reconciliation.version_adapter.version_facts",
                   return_value={"SP-1": {"version": 1, "revision": 2}}), \
             patch("bt_scheduler_owner_reconciliation.bt_composition_adapter.get_candidate", return_value=candidate), \
             patch("bt_scheduler_owner_reconciliation.m1_adapter.record_composition") as rebind:
            self.assertEqual(OwnerCompositionRuntime.reconcile_compositions(owner), ())
        rebind.assert_called_once_with(owner.scheduler, "candidate", "C1", candidate.members,
                                       candidate.manifest_sha256, tree_digest="d" * 40)

    def _repo(self, path: Path) -> Path:
        path.mkdir()
        subprocess.run(["git", "-C", str(path), "init", "-q"], check=True)
        subprocess.run(["git", "-C", str(path), "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                        "commit", "--allow-empty", "-qm", "base"], check=True)
        return path

    def _plan(self, roles=("main",)):
        return SimpleNamespace(schema_version="1.3.0", subplans=(object(),), plan_id="REQ-1", revision=1,
                               sha256="a" * 64,
                               tasks=tuple(SimpleNamespace(repository=role) for role in roles))

    def test_store_path_uses_dedicated_project_requirement_namespace(self):
        with tempfile.TemporaryDirectory() as directory:
            rdir = Path(directory) / "bitacora" / "metodologia" / "requirements" / "REQ-123-sample"
            self.assertEqual(composition_store_path(rdir, "metodologia", "REQ-123"),
                             Path(directory) / "bitacora" / ".state" / "composition" / "metodologia-REQ-123.db")

    def test_multi_repository_plan_is_refused_with_exact_topology_blocker(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self._repo(Path(directory) / "repo")
            with self.assertRaisesRegex(CompositionRuntimeError,
                                        "OWNER_COMPOSITION_MULTI_REPOSITORY_UNSUPPORTED.*main, web"):
                OwnerCompositionRuntime.create(rdir=Path(directory) / "bitacora", project="p", req="REQ-1",
                                               plan=self._plan(("main", "web")), repositories={"main": repo},
                                               verifier_id="m6")

    def test_create_refuses_non_file_contract_paths_and_non_cumulative_gate_chains(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self._repo(Path(directory) / "repo")
            plan = self._plan()
            producer = SimpleNamespace(expected_paths=("contracts/**",))
            plan.task = lambda _task_id: producer
            plan.subplans = (SimpleNamespace(id="SP-1", produces=({"contract": "api", "version": 1,
                                                                      "defined_by": "T1"},), ui=None),)
            plan.composition_gates = ()
            with self.assertRaisesRegex(CompositionRuntimeError, "DEFINED_BY_PATHS_NOT_EXACT_FILES"):
                OwnerCompositionRuntime.create(rdir=Path(directory) / "bitacora", project="p", req="REQ-1",
                                               plan=plan, repositories={"main": repo}, verifier_id="m6")

            plan.subplans = (SimpleNamespace(id="SP-1", produces=({"contract": "api", "version": 1,
                                                                      "defined_by": "T1"},), ui=None),
                             SimpleNamespace(id="SP-2", produces=(), ui=None))
            plan.tasks = (SimpleNamespace(id="T1", repository="main", expected_paths=("src/api.md",)),)
            plan.task = lambda _task_id: plan.tasks[0]
            plan.composition_gates = (SimpleNamespace(subplans=("SP-1", "SP-2"), task="G1"),
                                      SimpleNamespace(subplans=("SP-2",), task="G2"))
            with self.assertRaisesRegex(CompositionRuntimeError, "GATE_CHAIN_UNSUPPORTED"):
                OwnerCompositionRuntime.create(rdir=Path(directory) / "bitacora", project="p", req="REQ-1",
                                               plan=plan, repositories={"main": repo}, verifier_id="m6")

    def test_workspace_lives_under_owned_run_state_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = self._repo(root / "repo")
            rdir = root / "bitacora" / "p" / "requirements" / "REQ-1-name"
            owner = OwnerCompositionRuntime.create(rdir=rdir, project="p", req="REQ-1", plan=self._plan(),
                                                   repositories={"main": repo}, verifier_id="m6")
            self.assertEqual(owner.workspace_root, rdir.parents[2] / ".state" / "composition" / "workspaces" / "p-REQ-1")
            marker = json.loads((owner.workspace_root / ".owner.json").read_text(encoding="utf-8"))
            self.assertEqual(marker["plan_id"], "REQ-1")
            owner.close()

    def test_a_bitacora_root_reached_through_a_symlink_keeps_the_workspace_inside_the_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = self._repo(root / "repo")
            (root / "real-bitacora" / "p" / "requirements" / "REQ-1-name").mkdir(parents=True)
            (root / "bitacora").symlink_to(root / "real-bitacora")          # ~/bitacora -> ~/dev/metodologia/bitacora
            rdir = root / "bitacora" / "p" / "requirements" / "REQ-1-name"
            owner = OwnerCompositionRuntime.create(rdir=rdir, project="p", req="REQ-1", plan=self._plan(),
                                                   repositories={"main": repo}, verifier_id="m6")
            self.assertTrue((root / "real-bitacora" / ".state" / "composition" / "workspaces" / "p-REQ-1"
                             / ".owner.json").is_file())
            owner.close()

    def test_owner_marker_update_is_atomic_when_replace_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / ".owner.json"
            ensure_owner_marker(marker, project="p", req="REQ-1", plan_id="REQ-1", revision=1,
                                plan_sha256="a" * 64)
            original = marker.read_bytes()
            with patch("bt_scheduler_owner_workspace.os.replace", side_effect=OSError("crash")):
                with self.assertRaises(OSError):
                    bind_owner_marker(marker, project="p", req="REQ-1", plan_id="REQ-1", revision=2,
                                      plan_sha256="b" * 64, run_id="run-1")
            self.assertEqual(marker.read_bytes(), original)

    def test_blob_sha256_preserves_non_utf8_blob_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self._repo(Path(directory) / "repo")
            (repo / "binary-contract").write_bytes(b"contract\xff\r\n")
            subprocess.run(["git", "-C", str(repo), "add", "binary-contract"], check=True)
            subprocess.run(["git", "-C", str(repo), "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                            "commit", "-qm", "binary"], check=True)
            port = GitSubprocessPort(repo, Path(directory) / "workspaces")
            head = port.rev_parse("HEAD")
            self.assertEqual(port.blob_sha256(head, "binary-contract"),
                             hashlib.sha256(b"contract\xff\r\n").hexdigest())

    def test_identity_query_loads_the_manifest_reservation_without_building(self):
        candidate = SimpleNamespace(id="C1", integrated_commit="1" * 40, members={"SP-1": 1},
                                    manifest_sha256="2" * 64)
        owner = OwnerCompositionRuntime.__new__(OwnerCompositionRuntime)
        owner.scheduler = object()
        owner.plan = SimpleNamespace(revision=2, subplans=(SimpleNamespace(id="SP-1"),),
                                      composition_gates=(SimpleNamespace(task="G1", subplans=("SP-1",)),))
        owner.store = SimpleNamespace(get_candidate=lambda _id: candidate)
        owner.candidates = {}
        with patch("bt_scheduler_owner_composition.m1_adapter.subplan_publication_facts",
                   return_value={"SP-1": {"version": 1, "revision": 2}}), \
             patch("bt_scheduler_owner_composition.m1_adapter.composition_facts",
                   return_value={"C1": {"members": {"SP-1": 1}, "state": "candidate"}}), \
             patch("bt_scheduler_owner_composition.bt_composition_adapter.get_candidate",
                   return_value=candidate), \
             patch.object(OwnerCompositionRuntime, "_members_for_gate", return_value=({"SP-1": 1}, ("SP-1",))):
            self.assertEqual(owner.composition_base("G1"), "1" * 40)

    def test_stale_publication_version_is_not_used_for_candidate_reservation(self):
        owner = OwnerCompositionRuntime.__new__(OwnerCompositionRuntime)
        owner.scheduler = object()
        owner.plan = SimpleNamespace(revision=2, subplans=(SimpleNamespace(id="SP-1"),),
                                      composition_gates=(SimpleNamespace(task="G1", subplans=("SP-1",)),))
        with patch("bt_scheduler_owner_composition.m1_adapter.subplan_publication_facts",
                   return_value={"SP-1": {"version": 1, "revision": 1}}):
            self.assertEqual(owner._members_for_gate(owner.plan.composition_gates[0]), ({}, ()))

    def test_proof_mismatch_durably_holds_the_completed_composition_gate(self):
        gate = SimpleNamespace(task="G1", subplans=("SP-1",), audit_task=None)
        candidate = SimpleNamespace(id="C1", state="candidate", members={"SP-1": 1}, manifest_sha256="2" * 64)
        owner = OwnerCompositionRuntime.__new__(OwnerCompositionRuntime)
        owner.scheduler = object()
        owner.plan = SimpleNamespace(composition_gates=(gate,), revision=1)
        owner.store = object()
        owner.verifier_id = "m6"
        owner.engine = object()
        owner._attend = lambda *args: None
        owner._manifest_candidate_id = lambda _reference: "C1"
        owner._members_for_gate = lambda _gate: ({"SP-1": 1}, ("SP-1",))
        owner._composition_proof = lambda *_args: None
        with patch("bt_scheduler_owner_composition.m1_adapter.accepted_attempt_facts",
                   return_value={"G1": {"verdict_id": "m6://result/" + "a" * 64}}), \
             patch("bt_scheduler_owner_composition.m1_adapter.composition_facts",
                   return_value={"C1": {"state": "candidate", "members": {"SP-1": 1}, "revision": 1}}), \
             patch("bt_scheduler_owner_composition.bt_composition_adapter.get_candidate",
                   return_value=candidate), \
             patch("bt_scheduler_owner_composition.m1_adapter.hold_composition_gate") as hold:
            self.assertEqual(owner.reconcile_compositions(), ())
        hold.assert_called_once_with(owner.scheduler, "G1", "C1", "OWNER_COMPOSITION_PROOF_MISMATCH")

    def test_same_run_revision_cannot_rebind_composition_store_to_another_repo(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = self._repo(root / "repo-one")
            second = self._repo(root / "repo-two")
            rdir = root / "bitacora" / "p" / "requirements" / "REQ-1-name"
            args = dict(rdir=rdir, project="p", req="REQ-1", plan=self._plan(),
                        verifier_id="m6")
            owner = OwnerCompositionRuntime.create(**args, repositories={"main": first})
            scheduler = SimpleNamespace(snapshot=lambda: SimpleNamespace(revision=1, plan_sha256="a" * 64),
                                        audit_log=lambda: [])
            owner.bind_scheduler(scheduler)
            owner.close()
            resumed = OwnerCompositionRuntime.create(**args, repositories={"main": first})
            resumed.bind_scheduler(scheduler)
            resumed.close()
            other = OwnerCompositionRuntime.create(**args, repositories={"main": second})
            with self.assertRaisesRegex(CompositionRuntimeError, "OWNER_COMPOSITION_STORE_IDENTITY_MISMATCH"):
                other.bind_scheduler(scheduler)
            other.close()

    def _frontier_runtime(self, *, composition_propagation=None):
        task = lambda tid, after, kind, subplan=None: {
            "id": tid, "milestone_id": "M1", "repository": "main", "after": after,
            "shared_resources": [], "expected_paths": [f"{tid}/**"], "acceptance_criteria": [f"{tid} works"],
            "verification": [{"type": "command", "value": "true", "category": "functional"}], "kind": kind,
            **({"subplan_id": subplan} if subplan else {})}
        data = {"schema_version": "1.3.0", "plan_id": "P", "revision": 1, "tasks": [
            task("T1", [], "implement", "SP-1"), task("T2", ["T1"], "audit", "SP-1"),
            task("T3", ["T2"], "test")], "subplans": [{"id": "SP-1", "milestone_id": "M1", "title": "SP",
            "outcome": "Outcome", "covers": ["R1"], "acceptance_criteria": ["T1 works"],
            "produces": [{"contract": "api", "version": 1, "defined_by": "T1", "interfaces": ["IF-1"]}],
            "consumes": [], "checkpoints": [], "integration_test_task": "T1", "audit_task": "T2"}],
            "composition_gates": [{"id": "CG-1", "subplans": ["SP-1"], "task": "T3", "criteria": ["T3 works"]}]}
        text = json.dumps(data)
        plan = m1.load_plan(text, approved_sha256=hashlib.sha256(text.encode()).hexdigest())
        core = m1.SchedulerCore(plan, m1.InMemoryRepository())
        core.start()
        for task_id in ("T1", "T2"):
            core.claim(m1.Assignment(task_id, "worker"))
            attempt = core.snapshot().tasks[task_id]["attempt"]
            core.ingest(m1.Event("done-" + task_id, "P", 1, task_id, attempt, "worker", "execution_finished"))
            core.step()
            core.submit_verdict(m1.Verdict("verdict-" + task_id, "P", 1, task_id, attempt, True,
                                           "m6", "m6://result/" + ("a" if task_id == "T1" else "b") * 64))
        core.record_subplan_version("SP-1", 1, "1" * 40, "2" * 64)
        core.claim(m1.Assignment("T3", "worker"))
        attempt = core.snapshot().tasks["T3"]["attempt"]
        core.ingest(m1.Event("done-T3", "P", 1, "T3", attempt, "worker", "execution_finished"))
        core.step()
        core.submit_verdict(m1.Verdict("verdict-T3", "P", 1, "T3", attempt, True, "m6", "accepted"))
        core.record_composition("candidate", "C1", {"SP-1": 1}, "3" * 64, tree_digest="4" * 40)
        core.record_composition("published", "C1", {"SP-1": 1}, "3" * 64, tree_digest="4" * 40)
        runtime = OwnerCompositionRuntime.__new__(OwnerCompositionRuntime)
        runtime.scheduler, runtime.plan = core, plan
        runtime._frontier_proposals = {}
        recovery = RecoveryAdapter(Path(tempfile.mkdtemp()) / "m5.db", scheduler=core, run_id="run",
                                   describe=lambda _attempt: {}, composition_propagation=runtime.demonstrated_frontier)
        core.ports.recovery = recovery
        self.addCleanup(recovery.close)
        return runtime, core

    def test_real_propagate_actions_keep_each_operation_distinct_and_apply_only_the_consumer_frontier(self):
        from bt_composition_adapter import EvidenceKey

        cases = {
            "reverify": (PropagationChange("SP-0", ancestry_only=True), [], []),
            "reintegrate": (PropagationChange("SP-0", git_conflict=True, conflicting_members=("SP-1",)), [], []),
            "audit": (PropagationChange("SP-0", public_surface_changed=True),
                      [{"old_evidence_key": EvidenceKey("a", {"api": "1"}, "env", ("x",)),
                        "new_evidence_key": EvidenceKey("b", {"api": "2"}, "env", ("x",))}], []),
            "adapt_contract": (PropagationChange("SP-0", producer_broke_declared_major=True),
                               [{"contract_test_executed": True, "contract_test_failed": True,
                                 "current_producer_version": 2, "evidence_producer_version": 2,
                                 "current_producer_manifest": "m", "evidence_producer_manifest": "m"}], []),
            "modify": (PropagationChange("SP-0"), [{"contract_test_executed": True, "contract_test_failed": True,
                       "current_producer_version": 2, "evidence_producer_version": 2,
                       "current_producer_manifest": "m", "evidence_producer_manifest": "m"}], []),
            "reimplement": (PropagationChange("SP-0"), [], [{"consumer": "SP-1", "demonstrated": True,
                             "design_cannot_meet_contract": True, "evidence_id": "m6://result/" + "e" * 64}]),
        }
        for operation, (change, extra_consumer, evidence) in cases.items():
            with self.subTest(operation=operation):
                runtime, core = self._frontier_runtime()
                consumer = {"id": "SP-1", "task_ids": ["T1", "T2"], **(extra_consumer[0] if extra_consumer else {})}
                evidence = evidence or [{"evidence_id": "m6://result/" + "e" * 64}]
                moved = runtime.propagate(change, [consumer], evidence, composition_id="C1",
                                          manifest_sha256="3" * 64, tree_digest="4" * 40, source_task_id="T3")
                self.assertEqual(moved, ("T1", "T2"))
                self.assertEqual(core.snapshot().tasks["T1"]["state"], "pending")
                applied = [entry.detail["action"] for entry in core.audit_log()
                           if entry.kind == "demonstrated_frontier_applied"]
                self.assertIn(operation, applied)
                self.assertNotIn("T3", core.read(lambda ctx: ctx.state.frontier_applications[next(iter(ctx.state.frontier_applications))]["task_ids"]))

    def test_frontier_replay_is_idempotent_and_m5_refuses_a_stale_change_id(self):
        runtime, core = self._frontier_runtime()
        change = PropagationChange("SP-0", git_conflict=True, conflicting_members=("SP-1",))
        consumers = [{"id": "SP-1", "task_ids": ["T1", "T2"]}]
        evidence = [{"evidence_id": "m6://result/" + "e" * 64}]
        kwargs = dict(composition_id="C1", manifest_sha256="3" * 64, tree_digest="4" * 40, source_task_id="T3")
        moved = runtime.propagate(change, consumers, evidence, **kwargs)
        before = core.snapshot().tasks
        self.assertEqual(runtime.propagate(change, consumers, evidence, **kwargs), moved)
        self.assertEqual(core.snapshot().tasks, before)
        change_id = next(iter(runtime._frontier_proposals))
        runtime._frontier_proposals[change_id]["change_id"] = "stale-change"
        with self.assertRaises(Exception):
            core.ports.recovery.demonstrated_frontier(change_id)


if __name__ == "__main__":
    unittest.main()
