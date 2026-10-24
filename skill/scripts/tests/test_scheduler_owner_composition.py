"""Owner composition identities and supported repository topology."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bt_scheduler_owner_composition import CompositionRuntimeError, OwnerCompositionRuntime, composition_store_path
import bt_scheduler_adapter as m1_adapter
from bt_scheduler_recovery_adapter import RecoveryAdapter
from bt_composition_adapter import PropagationChange

m1 = m1_adapter.core


class OwnerCompositionRuntimeTests(unittest.TestCase):
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
