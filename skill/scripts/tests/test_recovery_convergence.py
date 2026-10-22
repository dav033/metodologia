from __future__ import annotations

import hashlib
import json
import copy
import subprocess
import tempfile
import unittest
from pathlib import Path

import bt_scheduler_integrator as integrator
from bt_recovery_convergence import ConvergenceError, plan_conflict_convergence
from bt_scheduler_recovery.conflict_contracts import ConflictStrategy
from test_scheduler_integrator import FakePlan, snapshot


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def text_digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


class RecoveryConvergenceTests(unittest.TestCase):
    def setUp(self):
        self.paths = ["src/shared.py"]
        self.sides = [
            {"role": "accepted", "task_id": "T1", "attempt_id": "att-1", "base_sha": "1" * 40,
             "snapshot_sha": "2" * 40, "tree_sha": "3" * 40},
            {"role": "candidate", "task_id": "T2", "attempt_id": "att-2", "base_sha": "4" * 40,
             "snapshot_sha": "5" * 40, "tree_sha": "6" * 40},
        ]
        self.accepted_map = {"T0": "att-0", "T1": "att-1", "T2": "att-2"}
        self.accepted_map_digest = digest(self.accepted_map)
        self.current_base_manifest = {"attempt_id": "att-0", "snapshot_sha": "7" * 40, "tree_sha": "8" * 40}
        self.evidence_digests = [self.accepted_map_digest, digest(self.current_base_manifest)]
        self.checks = [
            {"type": "command", "value": "python -m unittest tests.test_left", "purpose": "left contract",
             "category": "contract"},
            {"type": "command", "value": "python -m unittest tests.test_right", "purpose": "right contract",
             "category": "contract"},
        ]
        self.plan = {"plan_id": "plan-1", "revision": 4, "sha256": "c" * 64,
                     "tasks": [{"id": "T0", "after": [], "repository": "app", "milestone_id": "M1",
                                "covers": [], "expected_paths": []},
                               {"id": "T1", "after": ["T0"], "repository": "app", "milestone_id": "M1",
                                "covers": ["REQ-1"], "expected_paths": self.paths,
                                "verification": [self.checks[0]], "acceptance_criteria": ["T1 prior behavior"]},
                               {"id": "T2", "after": ["T0"], "repository": "app", "milestone_id": "M1",
                                "covers": ["REQ-2"], "expected_paths": self.paths,
                                "verification": [self.checks[1]], "acceptance_criteria": ["T2 prior behavior"]},
                               {"id": "T3", "after": ["T0", "T1", "T2"], "repository": "app", "milestone_id": "M1",
                                "covers": ["REQ-3"],
                                "expected_paths": [*self.paths, "src/downstream.py"],
                                "verification": [self.checks[0], self.checks[1]], "acceptance_criteria": ["integration"]}]}
        observation = {"schema_version": "conflict-observation/1", "source_type": "integration_gate",
            "run_id": "run-1", "plan_id": "plan-1", "revision": 4, "plan_sha256": "c" * 64,
            "task_id": "T2", "attempt_id": "att-2", "token": "token-3", "consumer_id": "m6-3",
            "repository_id": "app", "paths": self.paths,
            "sides": [{"ordinal": index, "role": item["role"], "task_id": item["task_id"], "attempt_id": item["attempt_id"],
                       "base_digest": text_digest(item["base_sha"]),
                       "snapshot_digest": text_digest(item["snapshot_sha"]),
                       "tree_digest": text_digest(item["tree_sha"])} for index, item in enumerate(self.sides)],
            "original_merge_base": "d" * 64, "carry_ancestry": ["e" * 64],
            "evidence_digests": self.evidence_digests,
            "ordinary_rework_refusal": "ordinary_rework_refused", "ordinary_rework_refusal_detail": "busy"}
        self.envelope = {"observation": observation,
            "plan_facts": {"schema_version": "conflict-plan-facts/1", "source_type": "integration_gate",
                "run_id": "run-1", "plan_id": "plan-1", "revision": 4, "plan_sha256": "c" * 64,
                "task_id": "T2", "attempt_id": "att-2",
                "token": "token-3", "consumer_id": "m6-3", "repository_id": "app",
                "approved_start_paths": [], "approved_integration_paths": self.paths, "authority_status": "authorized"},
            "lineage_facts": {"schema_version": "conflict-lineage-facts/1", "status": "current",
                "evidence_complete": True, "semantic_conflict": False, "incompatible_requirements": [],
                "ownership_or_order_defect": True, "demonstrated_future_defect": False, "aliases": []},
            "sources": self.sides, "owners": {"T1": {"paths": self.paths, "requirements": ["Requirement from T1"]},
                "T2": {"paths": self.paths, "requirements": ["Requirement from T2"]}},
            "current_base": {"app": {"accepted_attempt_id": "att-0", "snapshot_sha": "7" * 40,
                                        "task_id": "T0", "accepted_map_digest": self.accepted_map_digest,
                                        "m3_manifest": self.current_base_manifest}},
            "accepted_map": self.accepted_map,
            "delta_paths": {"att-1": ["src/shared.py"], "att-2": ["src/shared.py"]},
            "convergence_task_id": "T4", "nonconflicting_predecessor_closure": ["T0"],
            "marker_paths": self.paths, "affected_consumers": ["T3"],
            "symptom_oracle": {"path": "src/shared.py", "command": "python -m unittest tests.test_conflict",
                               "red_command": "python -m unittest tests.test_conflict_on_captured_tree",
                               "owner_task_id": "T1", "red_on_conflict": True, "green_on_result": True,
                               "red_provenance": {"captured_attempt_id": "att-2", "failure_kind": "symptom",
                                                   "source_digest": text_digest(self.sides[1]["tree_sha"]),
                                                   "command_digest": digest("python -m unittest tests.test_conflict_on_captured_tree")}},
            "marker_check": {"type": "command", "value": "python -m unittest tests.test_no_markers"}}
        receipt = {"schema_version": "conflict-lineage-receipt/1", "source_digests": self.evidence_digests,
                   "affected_consumers": ["T3"], "obsolete_edges": [
                       {"consumer_id": "T3", "source_task_id": "T1"},
                       {"consumer_id": "T3", "source_task_id": "T2"}]}
        self.envelope["lineage_receipt"] = {**receipt, "sha256": digest(receipt)}
        self.strategy = ConflictStrategy(source_digests=tuple(self.evidence_digests),
            accepted_map_digest=self.accepted_map_digest, path_digests=(digest("src/shared.py"),),
            check_digests=tuple(digest({**check, "owner_task_id": owner})
                for check, owner in zip(self.checks, ("T1", "T2"))),
            actions=("converge_owned_paths", "inherit_additive_checks"),
            action_edges=(("converge_owned_paths", "inherit_additive_checks"),)).to_dict()

    def compile(self):
        return plan_conflict_convergence(self.plan, self.envelope, self.strategy)

    def test_compiles_single_writer_with_both_snapshots_and_union_checks(self):
        work = self.compile()
        task = work["convergence_task"]
        self.assertEqual(work["schema_version"], "convergence-work/1")
        self.assertEqual(task["expected_paths"], self.paths)
        self.assertEqual(task["after"], ["T0"])
        self.assertEqual(task["requirements"], [
            {"owner_task_id": "T1", "text": "Requirement from T1"},
            {"owner_task_id": "T2", "text": "Requirement from T2"}])
        self.assertEqual(task["bootstrap"]["parents"], ["2" * 40, "5" * 40])
        self.assertEqual([row["owner_task_id"] for row in work["bootstrap"]["verification_scope"][:2]], ["T1", "T2"])
        self.assertEqual(work["bootstrap"]["retained_acceptance"], ["T1", "T2"])
        self.assertEqual(work["bootstrap"]["consumer_task_ids"], ["T3"])
        self.assertEqual(work["consumer_updates"][0]["after"], ["T0", "T4"])
        self.assertEqual(work["bootstrap"]["result_base"], {"kind": "accepted_convergence_attempt", "task_id": "T4",
            "lookup": "M1.accepted_attempt -> M3.snapshot", "pre_acceptance_pointer": None})
        self.assertEqual(set(work), {"schema_version", "convergence_task", "rebuilt_tasks", "consumer_updates",
                                     "bootstrap", "replaced_task_ids", "evidence_refs", "actions"})
        self.assertEqual(work["actions"], [])

    def test_start_conflict_without_candidate_or_m6_and_without_carry_is_compilable(self):
        envelope = copy.deepcopy(self.envelope)
        observation = envelope["observation"]
        observation["source_type"] = "start"
        observation["sides"][1]["role"] = "accepted"
        observation["carry_ancestry"] = []
        plan_facts = envelope["plan_facts"]
        plan_facts["source_type"] = "start"
        plan_facts["approved_start_paths"] = self.paths
        plan_facts["approved_integration_paths"] = []
        envelope["sources"][1]["role"] = "accepted"
        strategy = ConflictStrategy(
            source_digests=tuple(self.evidence_digests),
            accepted_map_digest=self.accepted_map_digest,
            path_digests=(digest("src/shared.py"),),
            check_digests=tuple(digest({**check, "owner_task_id": owner})
                                for check, owner in zip(self.checks, ("T1", "T2"))),
            actions=("converge_owned_paths", "inherit_additive_checks"),
            action_edges=(("converge_owned_paths", "inherit_additive_checks"),),
        ).to_dict()

        work = plan_conflict_convergence(self.plan, envelope, strategy)

        self.assertEqual([side["role"] for side in work["bootstrap"]["source_snapshots"]], ["accepted", "accepted"])
        self.assertEqual(work["bootstrap"]["source_snapshots"][1]["snapshot_sha"], "5" * 40)

    def test_rejects_edge_only_and_single_side_convenience_strategies(self):
        self.strategy = ConflictStrategy(source_digests=tuple(self.evidence_digests),
            accepted_map_digest=self.accepted_map_digest, path_digests=(digest("src/shared.py"),),
            check_digests=tuple(digest({**check, "owner_task_id": owner})
                for check, owner in zip(self.checks, ("T1", "T2"))),
            actions=("converge_owned_paths", "inherit_additive_checks"),
            action_edges=(("converge_owned_paths", "inherit_additive_checks"),)).to_dict()
        self.strategy["actions"] = ["inherit_additive_checks"]
        self.strategy.pop("strategy_id", None)
        with self.assertRaisesRegex(ConvergenceError, "strategy"):
            self.compile()

    def test_rejects_scope_widening_stale_evidence_and_semantic_conflict(self):
        self.envelope["marker_paths"] = ["src/shared.py", "src/extra.py"]
        with self.assertRaisesRegex(ConvergenceError, "marker paths"):
            self.compile()
        self.envelope["marker_paths"] = self.paths
        self.strategy["source_digests"] = ["f" * 64]
        self.strategy.pop("strategy_id", None)
        with self.assertRaisesRegex(ConvergenceError, "strategy is not bound"):
            self.compile()
        self.strategy = ConflictStrategy(source_digests=tuple(self.evidence_digests),
            accepted_map_digest=self.accepted_map_digest, path_digests=(digest("src/shared.py"),),
            check_digests=tuple(digest({**check, "owner_task_id": owner})
                for check, owner in zip(self.checks, ("T1", "T2"))),
            actions=("converge_owned_paths", "inherit_additive_checks"),
            action_edges=(("converge_owned_paths", "inherit_additive_checks"),)).to_dict()
        self.envelope["lineage_facts"]["semantic_conflict"] = True
        self.envelope["lineage_facts"]["incompatible_requirements"] = ["A contradicts B"]
        with self.assertRaisesRegex(ConvergenceError, "product-semantic"):
            self.compile()

    def test_rejects_tampered_lineage_receipt_and_stale_current_base_manifest(self):
        self.envelope["lineage_receipt"]["obsolete_edges"] = []
        with self.assertRaisesRegex(ConvergenceError, "lineage receipt"):
            self.compile()
        receipt = {key: value for key, value in self.envelope["lineage_receipt"].items() if key != "sha256"}
        self.envelope["lineage_receipt"]["sha256"] = digest(receipt)
        self.envelope["current_base"]["app"]["m3_manifest"]["snapshot_sha"] = "tampered"
        with self.assertRaisesRegex(ConvergenceError, "accepted predecessor base"):
            self.compile()

    def test_rebuild_uses_exact_prior_delta_and_revalidates_on_converged_base(self):
        self.envelope["lineage_facts"].update({"status": "stale", "demonstrated_future_defect": True})
        self.envelope["demonstrated_future_order"] = {"T5": ["T4"]}
        self.envelope["stale_descendant_task_id"] = "T3"
        self.envelope["stale_descendant_attempt_id"] = "att-3"
        self.envelope["stale_descendant_base_sha"] = "1" * 40
        self.envelope["stale_descendant_snapshot_sha"] = "2" * 40
        self.envelope["stale_descendant_delta_paths"] = ["src/downstream.py"]
        self.envelope["lineage_facts"]["ownership_or_order_defect"] = True
        self.strategy = ConflictStrategy(source_digests=tuple(self.evidence_digests),
            accepted_map_digest=self.accepted_map_digest, path_digests=(digest("src/shared.py"),),
            check_digests=tuple(digest({**check, "owner_task_id": owner})
                for check, owner in zip(self.checks, ("T1", "T2"))),
            actions=("rebuild_stale_descendant", "converge_owned_paths",
                     "repair_demonstrated_future_ownership_order", "inherit_additive_checks"),
            action_edges=(("rebuild_stale_descendant", "converge_owned_paths"),
                          ("converge_owned_paths", "repair_demonstrated_future_ownership_order"),
                          ("repair_demonstrated_future_ownership_order", "inherit_additive_checks"))).to_dict()
        work = self.compile()
        self.assertEqual(work["rebuilt_tasks"][0]["preservation_input"], {
            "base_sha": "1" * 40, "snapshot_sha": "2" * 40, "snapshot_attempt_id": "att-3",
            "paths": ["src/downstream.py"]})
        self.assertEqual(work["rebuilt_tasks"][0]["after"], ["T4"])
        self.assertEqual(work["rebuilt_tasks"][0]["id"], "T5")
        self.assertEqual(work["bootstrap"]["future_order"], {"T5": ["T4"]})

    def test_integrator_uses_only_m1_accepted_mapping_for_convergence_lineage(self):
        with tempfile.TemporaryDirectory(prefix="convergence-integrator-") as directory:
            repo = Path(directory) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "tests"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "tests@localhost"], cwd=repo, check=True)
            (repo / "shared.py").write_text("base\n")
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)
            head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, check=True,
                                  capture_output=True, text=True).stdout.strip()
            left = snapshot(repo, head, {"shared.py": "left requirement\n"})
            right = snapshot(repo, head, {"shared.py": "right requirement\n"})
            accepted = {"T1": "att-1", "T2": "att-2"}
            snapshots = {"att-1": left, "att-2": right}
            failed = integrator.PredecessorIntegrator()
            failed.bind(plan=FakePlan({"T1": ([], "app"), "T2": ([], "app"), "T3": (["T1", "T2"], "app")}),
                        accepted=lambda: dict(accepted), snapshot_of=lambda attempt: snapshots.get(attempt),
                        repo_of=lambda _role: repo, default_repository="app", identity="pre-authorized")
            with self.assertRaises(integrator.IntegrationError):
                failed.base_ref("T3")

            converged = snapshot(repo, head, {"shared.py": "left requirement + right requirement\n"})
            accepted["T4"] = "att-4"
            snapshots["att-4"] = converged
            accepted["T0"] = "att-0"
            snapshots["att-0"] = head
            downstream = integrator.PredecessorIntegrator()
            downstream.bind(plan=FakePlan({"T0": ([], "app"), "T1": ([], "app"), "T2": ([], "app"),
                                           "T4": (["T0"], "app"),
                                           "T5": (["T4"], "app")}),
                            accepted=lambda: dict(accepted), snapshot_of=lambda attempt: snapshots.get(attempt),
                            repo_of=lambda _role: repo, default_repository="app", identity="accepted-convergence")
            self.assertEqual(downstream.base_ref("T5"), converged)


if __name__ == "__main__":
    unittest.main()
