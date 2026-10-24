from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from bt_composition import (
    CompositionEngine, EvidenceKey, GitResult, PropagationChange, Store,
    propagate, reusable,
)


class FakeGit:
    def __init__(self):
        self.refs: dict[str, str] = {}
        self.parents: dict[str, tuple[str, ...]] = {}
        self.deltas: dict[str, tuple[str, ...]] = {}
        self.counter = 0
        self.fail_updates = False
        self.update_hook = None
        self.merges = {}
        self.commits = {}

    def rev_parse(self, revision):
        return self.refs.get(revision, revision if revision in self.parents else None)

    def merge_tree(self, base, ours, theirs):
        changed = tuple(set(self.deltas.get(theirs, ())) - set(self.deltas.get(base, ())))
        conflicts = tuple(path for path in changed if path in self.deltas.get(ours, ()))
        if conflicts:
            return GitResult(None, conflicts)
        signature = (base, ours, theirs)
        if signature in self.merges:
            return self.merges[signature]
        self.counter += 1
        tree = f"tree-{self.counter}"
        self.parents[tree] = ()
        self.deltas[tree] = tuple(sorted(set(self.deltas.get(ours, ())) | set(changed)))
        result = GitResult(tree)
        self.merges[signature] = result
        return result

    def commit_tree(self, tree, parents, message):
        signature = (tree, tuple(parents), message)
        if signature in self.commits:
            return self.commits[signature]
        self.counter += 1
        commit = f"commit-{self.counter}"
        self.parents[commit] = tuple(parents)
        self.deltas[commit] = self.deltas.get(tree, ())
        self.commits[signature] = commit
        return commit

    def update_refs(self, updates):
        if self.fail_updates:
            raise RuntimeError("git_update_ref_failed")
        for ref, new, expected in updates:
            if self.refs.get(ref) != expected:
                raise RuntimeError("git_ref_cas_failed")
        for ref, new, _ in updates:
            if new is None:
                self.refs.pop(ref, None)
            else:
                self.refs[ref] = new
        if self.update_hook:
            self.update_hook()

    def tree_digest(self, commit, paths):
        return ":".join((commit, *sorted(paths)))

    def diff_paths(self, a, b):
        return tuple(sorted(set(self.deltas.get(a, ())) ^ set(self.deltas.get(b, ()))))

    def add_worktree(self, commit, parent):
        return str(Path(parent) / commit)

    def remove_worktree(self, path):
        return None

    def prune_workspaces(self):
        return ()


class CompositionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.git = FakeGit()
        self.store = Store(Path(self.temp.name) / "run.db")
        self.engine = CompositionEngine(self.git, self.store, self.temp.name)
        self.git.parents.update({"base": (), "s1v1": (), "s2v1": (), "s3v1": (), "s1v2": (),
                                 "different": (), "another": ()})
        self.git.deltas.update({"base": (), "s1v1": ("one",), "s2v1": ("two",),
                                "s3v1": ("three",), "s1v2": ("one", "new")})

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def publish_version(self, sp, commit, base):
        return self.engine.publish_subplan_version("P1", "r1", sp, commit, base,
                                                    {"api@1": "declared"}, [])

    def initial_composition(self):
        for sp, commit in (("S1", "s1v1"), ("S2", "s2v1"), ("S3", "s3v1")):
            self.publish_version(sp, commit, "base")
        c1 = self.engine.build_candidate("P1", {"S1": 1, "S2": 1, "S3": 1})
        self.engine.publish(c1.id, {"M6": "PASS"})
        return c1

    def test_version_publish_is_immutable_and_idempotent(self):
        first = self.engine.publish_subplan_version("P1", "r1", "S1", "s1v1", "base", {}, [])
        same = self.engine.publish_subplan_version("P1", "r1", "S1", "s1v1", "base", {}, [])
        self.assertEqual(first, same)
        second = self.engine.publish_subplan_version("P1", "r2", "S1", "different", "base", {}, [])
        self.assertEqual(second.version, 2)
        self.git.refs["refs/subplans/P1/S1/v3"] = "occupied"
        with self.assertRaisesRegex(ValueError, "SUBPLAN_VERSION_CONFLICT"):
            self.engine.publish_subplan_version("P1", "r3", "S1", "another", "base", {}, [])

    def test_selective_candidate_publish_preserves_other_versions(self):
        c1 = self.initial_composition()
        self.publish_version("S1", "s1v2", "s1v1")
        c2 = self.engine.build_candidate("P1", {"S1": 2, "S2": 1, "S3": 1})
        self.engine.publish(c2.id, {"M6": "PASS"})
        self.assertEqual(self.git.refs["refs/compositions/P1/current"], c2.integrated_commit)
        self.assertEqual(c2.members, {"S1": 2, "S2": 1, "S3": 1})
        self.assertEqual(self.git.refs["refs/subplans/P1/S2/v1"], "s2v1")
        self.assertEqual(self.git.refs["refs/compositions/P1/C1"], c1.integrated_commit)
        self.assertEqual(self.engine.build_candidate("P1", {"S1": 2, "S2": 1, "S3": 1}).id, "C2")

    def test_failed_verdict_leaves_current_intact(self):
        c1 = self.initial_composition()
        self.publish_version("S1", "s1v2", "s1v1")
        c2 = self.engine.build_candidate("P1", {"S1": 2, "S2": 1, "S3": 1})
        self.assertFalse(self.engine.publish(c2.id, {"M6": "FAIL"}))
        self.assertEqual(self.git.refs["refs/compositions/P1/current"], c1.integrated_commit)

    def test_publish_ref_failure_leaves_current_and_candidate_retryable(self):
        c1 = self.initial_composition()
        self.publish_version("S1", "s1v2", "s1v1")
        c2 = self.engine.build_candidate("P1", {"S1": 2, "S2": 1, "S3": 1})
        self.git.fail_updates = True
        with self.assertRaisesRegex(RuntimeError, "git_update_ref_failed"):
            self.engine.publish(c2.id, {"M6": "PASS"})
        self.assertEqual(self.git.refs["refs/compositions/P1/current"], c1.integrated_commit)
        self.git.fail_updates = False
        self.assertEqual(self.engine.build_candidate("P1", {"S1": 2, "S2": 1, "S3": 1}).id, c2.id)
        self.assertTrue(self.engine.publish(c2.id, {"M6": "PASS"}))

    def test_publish_reconciles_store_failure_after_refs_move(self):
        c1 = self.initial_composition()
        self.publish_version("S1", "s1v2", "s1v1")
        c2 = self.engine.build_candidate("P1", {"S1": 2, "S2": 1, "S3": 1})
        original = self.store.update_candidate
        self.store.update_candidate = lambda candidate: (_ for _ in ()).throw(RuntimeError("store write failed"))
        with self.assertRaisesRegex(RuntimeError, "store write failed"):
            self.engine.publish(c2.id, {"M6": "PASS"})
        self.store.update_candidate = original
        self.assertTrue(self.engine.publish(c2.id, {"M6": "PASS"}))
        self.assertEqual(self.git.refs["refs/compositions/P1/current"], c2.integrated_commit)

    def test_version_and_candidate_store_failure_after_ref_are_reconciled(self):
        original_put_version = self.store.put_version
        self.store.put_version = lambda version, request: (_ for _ in ()).throw(RuntimeError("version row failed"))
        with self.assertRaisesRegex(RuntimeError, "version row failed"):
            self.publish_version("S1", "s1v1", "base")
        self.store.put_version = original_put_version
        adopted = self.publish_version("S1", "s1v1", "base")
        self.assertEqual(adopted.version, 1)

        for sp, commit in (("S2", "s2v1"), ("S3", "s3v1")):
            self.publish_version(sp, commit, "base")
        original_put_candidate = self.store.put_candidate
        self.store.put_candidate = lambda candidate, request: (_ for _ in ()).throw(RuntimeError("candidate row failed"))
        with self.assertRaisesRegex(RuntimeError, "candidate row failed"):
            self.engine.build_candidate("P1", {"S1": 1, "S2": 1, "S3": 1})
        self.store.put_candidate = original_put_candidate
        candidate = self.engine.build_candidate("P1", {"S1": 1, "S2": 1, "S3": 1})
        self.assertEqual(candidate.id, "C1")

    def test_rejected_candidate_does_not_suppress_next_attempt(self):
        c1 = self.initial_composition()
        self.publish_version("S1", "s1v2", "s1v1")
        c2 = self.engine.build_candidate("P1", {"S1": 2, "S2": 1, "S3": 1})
        self.engine.reject(c2.id, {"reason": "retry"})
        c3 = self.engine.build_candidate("P1", {"S1": 2, "S2": 1, "S3": 1})
        self.assertEqual(c3.id, "C3")
        self.assertEqual(self.git.refs["refs/compositions/P1/current"], c1.integrated_commit)

    def test_candidate_workspace_enters_verifying_state(self):
        self.initial_composition()
        self.publish_version("S1", "s1v2", "s1v1")
        candidate = self.engine.build_candidate("P1", {"S1": 2, "S2": 1, "S3": 1})
        self.engine.open_workspace(candidate.id)
        self.assertEqual(self.store.get_candidate(candidate.id).state, "verifying")

    def test_textual_conflict_rejects_without_moving_current(self):
        c1 = self.initial_composition()
        self.git.deltas["s1v2"] = ("two",)
        self.publish_version("S1", "s1v2", "s1v1")
        c2 = self.engine.build_candidate("P1", {"S1": 2, "S2": 1, "S3": 1})
        self.assertEqual(c2.state, "rejected")
        self.assertEqual(c2.reason_code, "git_text_conflict")
        self.assertEqual(c2.conflict_paths, ("two",))
        self.assertEqual(c2.conflicts, {"S1": ("two",)})
        self.assertEqual(self.git.refs["refs/compositions/P1/current"], c1.integrated_commit)

    def test_conflict_report_collects_paths_from_every_conflicting_member(self):
        self.initial_composition()
        self.git.deltas["different"] = ("two",)
        self.git.deltas["another"] = ("three",)
        self.publish_version("S1", "different", "s1v1")
        self.publish_version("S2", "another", "s2v1")
        candidate = self.engine.build_candidate("P1", {"S1": 2, "S2": 2, "S3": 1},
                                                member_order=("S1", "S2", "S3"))
        self.assertEqual(candidate.conflicts, {"S1": ("two",), "S2": ("three",)})

    def test_evidence_reuse_requires_full_key_equality(self):
        key = EvidenceKey("d", {"api@1": "hash"}, "env")
        self.assertTrue(reusable(key, EvidenceKey("d", {"api@1": "hash"}, "env")))
        self.assertFalse(reusable(key, EvidenceKey("x", {"api@1": "hash"}, "env")))
        self.assertFalse(reusable(EvidenceKey("d", {"api@1": "hash"}, "env", ("a",)),
                                 EvidenceKey("d", {"api@1": "hash"}, "env", ("b",))))

    def test_propagation_derives_reuse_and_contract_changes_from_keys(self):
        previous = EvidenceKey("tree-a", {"api@1": "old"}, "env", ("src/a.py",))
        current = EvidenceKey("tree-b", {"api@1": "new"}, "env", ("src/a.py",))
        actions = propagate(PropagationChange("S1", public_surface_changed=True), [{"id": "S2", "old_evidence_key": previous,
                                                          "new_evidence_key": current}], [])
        self.assertEqual([action.operation for action in actions], ["reverify", "audit"])

    def test_stale_producer_evidence_cannot_drive_contract_repair(self):
        old = EvidenceKey("tree", {"api@1": "v1"}, "env", ("src",))
        actions = propagate(PropagationChange("S1", public_surface_changed=True),
                            [{"id": "S2", "contract_test_executed": True, "contract_test_failed": True,
                              "evidence_producer_version": 1, "current_producer_version": 2,
                              "evidence_producer_manifest": "manifest-1", "current_producer_manifest": "manifest-2",
                              "old_evidence_key": old, "new_evidence_key": EvidenceKey("tree", {"api@1": "v2"},
                                                                                          "env", ("src",))}], [])
        self.assertEqual([action.operation for action in actions], ["reverify", "audit"])

    def test_contract_test_executed_field_is_used(self):
        actions = propagate(PropagationChange("S1"), [{"id": "S2", "contract_test_executed": True,
                                                          "contract_test_failed": True}], [])
        self.assertTrue(actions)

    def test_internal_change_and_reusable_evidence_need_no_action(self):
        key = EvidenceKey("tree", {"api@1": "same"}, "env", ("src",))
        self.assertEqual(propagate(PropagationChange("S1", ancestry_only=True), [{"id": "S2", "old_evidence_key": key,
                                                                "new_evidence_key": key}], []), ())

    def test_fold_uses_requested_plan_order_and_rejects_backwards_members(self):
        self.initial_composition()
        self.publish_version("S2", "different", "s2v1")
        ordered = self.engine.build_candidate("P1", {"S2": 2, "S1": 1, "S3": 1}, member_order=("S3", "S2", "S1"))
        self.assertEqual(ordered.member_order, ("S3", "S2", "S1"))
        with self.assertRaisesRegex(ValueError, "INVALID_MEMBERS"):
            self.engine.build_candidate("P1", {"S1": 1})

    def test_ancestry_only_change_only_reverifies_and_reimplement_needs_finding(self):
        consumers = [{"id": "S2", "contract_test_executed": False}]
        actions = propagate(PropagationChange("S1", ancestry_only=True, contract_major_changed=True,
                                               git_conflict=True),
                            [{"id": "S2", "contract_test_executed": True, "contract_test_failed": True}],
                            [{"demonstrated": True, "consumer": "S2", "design_cannot_meet_contract": True}])
        self.assertEqual([action.operation for action in actions], ["reverify"])
        actions = propagate(PropagationChange("S1", contract_major_changed=True),
                            [{"id": "S2", "contract_test_executed": True, "contract_test_failed": True}],
                            [{"demonstrated": True, "consumer": "S2", "design_cannot_meet_contract": True}])
        self.assertIn("reimplement", [action.operation for action in actions])
        actions = propagate(PropagationChange("S1", contract_major_changed=True),
                            [{"id": "S2", "contract_test_executed": True, "contract_test_failed": True}], [])
        self.assertNotIn("reimplement", [action.operation for action in actions])

    def test_candidate_workspace_uses_and_removes_git_port_allocation(self):
        for sp, commit in (("S1", "s1v1"), ("S2", "s2v1"), ("S3", "s3v1")):
            self.publish_version(sp, commit, "base")
        self.publish_version("S1", "s1v2", "s1v1")
        candidate = self.engine.build_candidate("P1", {"S1": 2, "S2": 1, "S3": 1})
        path = self.engine.open_workspace(candidate.id)
        self.assertTrue(path.endswith(candidate.integrated_commit))
        self.engine.close_workspace(path)

    def test_propagation_classifies_contract_conflict_and_explicit_design_failure(self):
        consumer = {"id": "S2", "contract_test_executed": True, "contract_test_failed": True,
                    "evidence_producer_version": 2, "current_producer_version": 2,
                    "evidence_producer_manifest": "manifest-2", "current_producer_manifest": "manifest-2"}
        self.assertEqual(propagate(PropagationChange("S1", git_conflict=True, conflicting_members=("S2",)),
                                  [consumer], [])[0].operation,
                         "reintegrate")
        unaffected = propagate(PropagationChange("S1", git_conflict=True), [{"id": "S3"}], [])
        self.assertNotIn("reintegrate", [action.operation for action in unaffected])
        self.assertEqual(propagate(PropagationChange("S1", contract_major_changed=True,
                                                       producer_broke_declared_major=True),
                                   [consumer], [])[0].operation, "adapt_contract")
        self.assertEqual(propagate(PropagationChange("S1", contract_major_changed=True), [consumer], [])[0].operation,
                         "modify")
        actions = propagate(PropagationChange("S1", public_surface_changed=True),
                            [{"id": "S2", "old_evidence_key": EvidenceKey("a", {"api@1": "old"}, "env"),
                              "new_evidence_key": EvidenceKey("b", {"api@1": "new"}, "env")}], [])
        self.assertEqual([action.operation for action in actions], ["reverify", "audit"])


if __name__ == "__main__":
    unittest.main()
