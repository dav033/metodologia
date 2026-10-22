from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_recovery_conflicts import _conflict, _source_records

from bt_recovery_conflicts import collect_conflict_evidence
from bt_scheduler_recovery_adapter import RecoveryAdapter
from bt_scheduler_recovery_lifecycle import (
    _two_verified_unchanged,
    _verified_cycle_success,
    strategy_identity,
)


class RecoveryRuntimeContracts(unittest.TestCase):
    def test_structural_lineage_identity_survives_revision_and_plan_hash_changes(self):
        original = {
            "run_id": "run-1", "revision": 5, "plan_sha256": "a" * 64,
            "conflict_lineage": "lineage-1", "source_digests": ["b" * 64],
            "snapshot_digests": ["c" * 64], "changed_paths_digest": "d" * 64,
            "check_digests": ["e" * 64], "accepted_attempts": ["att-1"],
            "merge_base_digest": "f" * 64, "carry_digest": "1" * 64,
        }
        revised = {**original, "revision": 6, "plan_sha256": "2" * 64}
        self.assertEqual(RecoveryAdapter._lineage_id(original), RecoveryAdapter._lineage_id(revised))
        self.assertNotEqual(RecoveryAdapter._lineage_id(original),
                            RecoveryAdapter._lineage_id({**revised, "source_digests": ["3" * 64]}))

    def test_missing_identity_or_source_evidence_cannot_create_a_lineage(self):
        with self.assertRaises(ValueError):
            RecoveryAdapter._lineage_id({"run_id": "run-1", "revision": 1, "plan_sha256": "a" * 64})

    def test_only_two_verified_semantic_source_and_check_matches_trigger_early_diagnosis(self):
        fact = {"verified": True, "semantic_digest": "a" * 64, "source_digest": "b" * 64,
                "check_digest": "c" * 64}
        self.assertTrue(_two_verified_unchanged([fact, dict(fact)]))
        self.assertFalse(_two_verified_unchanged([{**fact, "verified": False}, fact]))
        self.assertFalse(_two_verified_unchanged([fact, {**fact, "source_digest": "d" * 64}]))

    def test_strategy_identity_uses_dag_paths_outcomes_checks_and_evidence_not_wording(self):
        action = {"task_id": "T-fix", "kind": "implement", "depends_on": ["T1"],
                  "owner_paths": ["src/a.py"], "expected_outcomes": ["finding-fixed"],
                  "checks": [{"command_digest": "c" * 64}]}
        evidence = {"semantic_digest": "a" * 64, "source_digest": "b" * 64, "check_digest": "c" * 64,
                    "source_digests": ["d" * 64], "snapshot_digests": ["e" * 64]}
        first = strategy_identity({"actions": [action], "title": "Repair import"}, evidence)
        second = strategy_identity({"actions": [{**action, "title": "Fix module boundary"}],
                                    "title": "Different prose"}, evidence)
        self.assertEqual(first, second)
        self.assertNotEqual(first, strategy_identity(
            {"actions": [{**action, "owner_paths": ["src/b.py"]}]}, evidence))

    def test_phase_booleans_and_claimed_progress_are_not_cycle_success(self):
        self.assertFalse(_verified_cycle_success({"phases": {"diagnosed": True, "applied": True,
                                                             "audited": True},
                                                  "progress": {"verified": True, "unresolved": False}}))

    def test_success_requires_corrections_and_independent_proof_of_one_resulting_tree(self):
        tree = "a" * 64
        proof = {key: {"status": "verified", "resulting_tree_digest": tree, "evidence_ref": f"{key}:receipt"}
                 for key in ("m1_revision", "m3_snapshot", "m6_verdict", "independent_audit",
                             "independent_cross_check")}
        value = {"corrective_tasks": [{"task_id": "T-fix", "state": "accepted"}],
                 "resulting_tree_digest": tree, "independent_evidence": proof,
                 "progress": {"verified": True, "unresolved": False}}
        self.assertTrue(_verified_cycle_success(value))
        value["independent_evidence"] = {**proof, "m6_verdict": {**proof["m6_verdict"],
                                                                    "resulting_tree_digest": "b" * 64}}
        self.assertFalse(_verified_cycle_success(value))

    def test_m5_cycle_status_is_read_only_and_versioned(self):
        with tempfile.TemporaryDirectory() as temp:
            adapter = RecoveryAdapter(Path(temp) / "m5.db", scheduler=None, run_id="run-1", describe=lambda _: None)
            status = adapter.recovery_status()
            self.assertEqual(status["schema_version"], "recovery-status/1")
            self.assertEqual(status["cycles"], [])
            adapter.close()

    def test_preview_reads_sources_without_enabling_or_creating_cycle_state(self):
        identity = {"plan_id": "P", "revision": 1, "source_sha256": "a" * 64,
                    "stop_generation": 0, "accepted_map_digest": "b" * 64, "paused": False,
                    "cancelled": False, "live_attempts": []}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            adapter = RecoveryAdapter(root / "m5.db", scheduler=None, run_id="run-1", describe=lambda _: None,
                                      rdir=root, recovery_sources=lambda: {"source_sha256": "c" * 64})
            with patch("bt_scheduler_recovery_adapter.sched.revision_identity", return_value=identity):
                preview = adapter.preview_recovery()
                self.assertEqual(preview["schema_version"], "recovery-preview/1")
                self.assertFalse(preview["activation_present"])
                self.assertFalse((root / "RUN.recovery-policy.json").exists())
                self.assertFalse((root / "m5.db").exists())

    def test_activation_rejects_stale_preview_and_missing_authorization(self):
        identity = {"plan_id": "P", "revision": 1, "source_sha256": "a" * 64,
                    "stop_generation": 3, "accepted_map_digest": "b" * 64, "paused": False,
                    "cancelled": False, "live_attempts": []}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            adapter = RecoveryAdapter(root / "m5.db", scheduler=None, run_id="run-1", describe=lambda _: None,
                                      rdir=root)
            with patch("bt_scheduler_recovery_adapter.sched.revision_identity", return_value=identity):
                preview = adapter.preview_recovery()
                stale = adapter.enable_diagnostic_recovery("run-1", "0" * 64, 3, "owner-control:1")
                unauthorized = adapter.enable_diagnostic_recovery("run-1", preview["preview_digest"], 3, " ")
                self.assertFalse(stale["enabled"])
                self.assertFalse(unauthorized["enabled"])
                self.assertFalse((root / "RUN.recovery-policy.json").exists())

    def test_duplicate_ticks_after_failure_reuse_one_durable_cycle(self):
        identity = {"plan_id": "P", "revision": 5, "source_sha256": "a" * 64,
                    "stop_generation": 0, "accepted_map_digest": "b" * 64, "paused": False,
                    "cancelled": False, "live_attempts": []}
        sources = {"run_id": "run-1", "conflict_lineage": "conflict-1", "ordinary_exhausted": True,
                   "source_digests": ["c" * 64], "snapshot_digests": ["d" * 64],
                   "changed_paths_digest": "e" * 64, "check_digests": ["f" * 64],
                   "accepted_attempts": ["att-1"], "merge_base_digest": "1" * 64, "carry_digest": "2" * 64,
                   "planner_route": {"role": "planner", "verified": True, "provider": "codex",
                                     "profile": "codex", "model": "model", "authorization_ref": "route:1"},
                   "evidence_available": True, "conflict_observations": []}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            calls = []
            adapter = RecoveryAdapter(root / "m5.db", scheduler=None, run_id="run-1", describe=lambda _: None,
                                      rdir=root, recovery_sources=lambda: sources,
                                      diagnostic_pipeline=lambda _context: calls.append("called") or {
                                          "state": "blocked", "blocker": "hypothesis_failed"})
            (root / "RUN.recovery-policy.json").write_text('{"schema_version":"recovery-policy/1",'
                                                           '"run_id":"run-1","identity":{"stop_generation":0}}')
            with (patch("bt_scheduler_recovery_adapter.sched.revision_identity", return_value=identity),
                  patch("bt_scheduler_decisions.open_requests", return_value=[])):
                first = adapter.tick_diagnostic_recovery()
                second = adapter.tick_diagnostic_recovery()
            self.assertEqual(first["state"], "blocked")
            self.assertEqual(second["state"], "blocked")
            self.assertTrue(second["duplicate"])
            self.assertEqual(calls, ["called"])
            self.assertEqual(len(adapter.recovery_status()["cycles"]), 1)
            adapter.close()

    def test_conflict_observation_uses_the_m5_boundary_and_trusted_immutable_store(self):
        observation = collect_conflict_evidence(_source_records(), source_type="start", conflict=_conflict())
        with tempfile.TemporaryDirectory() as temp:
            adapter = RecoveryAdapter(Path(temp) / "m5.db", scheduler=None, run_id="run-1", describe=lambda _: None)
            reference = adapter.publish_conflict_observation(observation)
            self.assertEqual(adapter.read_conflict_observation(reference), observation)
            self.assertIsNone(adapter.read_conflict_observation("conflict:" + "0" * 64))
            adapter.close()


if __name__ == "__main__":
    unittest.main()
