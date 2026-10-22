from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from bt_recovery_conflicts import ConflictEvidenceError, collect_conflict_evidence
from bt_scheduler_recovery.conflict_contracts import ConflictObservation
from bt_scheduler_recovery.conflict_policy import classify_conflict
from bt_scheduler_recovery.conflict_delivery import EvidenceUnavailable, integration_problem, publish_or_raise


def _source_records(*, include_m6: bool = False):
    order = {"run_id": "run-1", "plan_id": "plan-1", "revision": 1, "task_id": "T3",
             "attempt_id": "A3", "plan_sha256": "a" * 64, "token": "token-1",
             "consumer_id": "T4", "repository_id": "repo-1"}
    names = ["m1_attempts", "m1_accepted", "frozen_plan", "current_plan", "m3_manifest", "m3_order"]
    if include_m6:
        names.append("m6_verdict")
    records = {}
    for name in names:
        value = dict(order)
        if name == "m1_accepted":
            value["accepted"] = {"T1": "A1", "T2": "A2"}
        if name == "frozen_plan":
            value["dag"] = {"T3": ["T1", "T2"]}
            value["task_scopes"] = {"old": ["src/"], "current": ["src/"]}
        if name == "m3_manifest":
            value["base_sha"] = "b" * 40
            value["snapshot_sha"] = "c" * 40
            value["tree_sha"] = "d" * 40
            value["paths"] = [f"src/long-{index:02d}-" + "x" * 40 + ".py" for index in range(8)]
        records[name] = {"record": value, "sha256": hashlib.sha256(
            __import__("json").dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        ).hexdigest()}
    return records


def _conflict(paths=None):
    paths = paths or [f"src/long-{index:02d}-" + "x" * 40 + ".py" for index in range(8)]
    return {"paths": paths, "merge_base": "e" * 40,
            "sides": [{"role": "accepted", "task_id": "T1", "attempt_id": "A1", "base_sha": "b" * 40,
                       "snapshot_sha": "c" * 40, "tree_sha": "d" * 40},
                      {"role": "accepted", "task_id": "T2", "attempt_id": "A2", "base_sha": "b" * 40,
                       "snapshot_sha": "f" * 40, "tree_sha": "1" * 40}],
            "carry_ancestry": [], "ordinary_rework_refusal": "ordinary_rework_refused",
            "ordinary_rework_refusal_detail": "limit: T1 was already sent back 2 time(s)"}


class ConflictEvidenceTests(unittest.TestCase):
    def test_start_conflict_uses_four_stage_sources_without_future_m6_candidate(self):
        observation = collect_conflict_evidence(_source_records(), source_type="start", conflict=_conflict())
        self.assertEqual(observation["schema_version"], "conflict-observation/1")
        self.assertEqual(len(observation["paths"]), 8)
        self.assertGreater(len(", ".join(observation["paths"])), 170)
        self.assertEqual(observation["ordinary_rework_refusal_detail"],
                         "limit: T1 was already sent back 2 time(s)")
        ConflictObservation.from_dict(observation)

    def test_integration_gate_requires_matching_m6_record(self):
        with self.assertRaisesRegex(ConflictEvidenceError, "required official conflict source"):
            collect_conflict_evidence(_source_records(), source_type="integration_gate", conflict=_conflict())

    def test_official_source_digest_mismatch_blocks_collection(self):
        sources = _source_records()
        sources["m1_accepted"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ConflictEvidenceError, "digest mismatch"):
            collect_conflict_evidence(sources, source_type="start", conflict=_conflict())

    def test_unsafe_conflict_paths_block_collection(self):
        with self.assertRaisesRegex(ConflictEvidenceError, "unsafe conflict path"):
            collect_conflict_evidence(_source_records(), source_type="start",
                                     conflict=_conflict(["../escape.py"]))

    def test_symlink_conflict_path_blocks_collection(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "src").mkdir()
            (root / "src" / "alias.py").symlink_to(root / "src" / "target.py")
            with self.assertRaisesRegex(ConflictEvidenceError, "symlink conflict path"):
                collect_conflict_evidence(_source_records(), source_type="start",
                                          conflict=_conflict(["src/alias.py"]), repository_root=root)

    def test_stale_accepted_descendant_blocks_collection(self):
        sources = _source_records()
        value = sources["m1_accepted"]["record"]
        value["accepted"]["T1"] = "A-old"
        sources["m1_accepted"]["sha256"] = hashlib.sha256(
            __import__("json").dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        ).hexdigest()
        with self.assertRaisesRegex(ConflictEvidenceError, "accepted conflict side is stale"):
            collect_conflict_evidence(sources, source_type="start", conflict=_conflict())

    def test_missing_manifest_and_throwing_publication_are_explicitly_unavailable(self):
        with self.assertRaisesRegex(EvidenceUnavailable, "manifest is missing"):
            integration_problem(lambda: None, "T3", "A3", lambda *_: "", None)
        with self.assertRaisesRegex(EvidenceUnavailable, "publication failed"):
            publish_or_raise(lambda *_: (_ for _ in ()).throw(OSError("disk unavailable")),
                             object(), "T1 vs T3 for T4: src/file.py",
                             "ordinary_rework_refused", "limit: T1 rework limit")

    def test_ordinary_no_carry_integration_gate_remains_classifiable(self):
        observation = {
            "schema_version": "conflict-observation/1", "source_type": "integration_gate",
            "run_id": "run-1", "plan_id": "plan-1", "revision": 1, "plan_sha256": "a" * 64,
            "task_id": "T3", "attempt_id": "A3", "token": "token-1", "consumer_id": "T4",
            "repository_id": "repo-1", "paths": ["src/file.py"],
            "sides": [
                {"ordinal": 0, "role": "accepted", "task_id": "T1", "attempt_id": "A1",
                 "base_digest": "b" * 64, "snapshot_digest": "c" * 64, "tree_digest": "d" * 64},
                {"ordinal": 1, "role": "candidate", "task_id": "T3", "attempt_id": "A3",
                 "base_digest": "e" * 64, "snapshot_digest": "f" * 64, "tree_digest": "1" * 64}],
            "original_merge_base": "2" * 64, "carry_ancestry": [], "evidence_digests": ["3" * 64],
            "ordinary_rework_refusal": "ordinary_rework_refused",
            "ordinary_rework_refusal_detail": "limit: T1 was already sent back 2 time(s)"}
        facts = {"schema_version": "conflict-plan-facts/1", "source_type": "integration_gate",
                 "run_id": "run-1", "plan_id": "plan-1", "revision": 1, "plan_sha256": "a" * 64,
                 "task_id": "T3", "attempt_id": "A3", "token": "token-1", "consumer_id": "T4",
                 "repository_id": "repo-1", "approved_start_paths": [], "approved_integration_paths": ["src/file.py"],
                 "authority_status": "authorized"}
        lineage = {"schema_version": "conflict-lineage-facts/1", "status": "stale", "evidence_complete": True,
                   "semantic_conflict": False, "incompatible_requirements": [], "ownership_or_order_defect": False,
                   "demonstrated_future_defect": False, "aliases": []}
        result = classify_conflict(observation, facts, lineage)
        self.assertEqual(result["dominant"], "stale_lineage")


if __name__ == "__main__":
    unittest.main()
