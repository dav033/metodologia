import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from bt_scheduler_recovery import DiagnosticStore, RecoveryError
from bt_scheduler_recovery.conflict_contracts import (
    ConflictLineageFacts,
    ConflictObservation,
    ConflictPlanFacts,
    ConflictSide,
    ConflictStrategy,
)
from bt_scheduler_recovery.conflict_policy import (
    classify_conflict,
    conflict_case,
    conflict_envelope_payload,
    initial_conflict_advice,
)
from bt_scheduler_recovery.diagnostic_contracts import DiagnosticCase, RecoveryProposal


DIGEST = "a" * 64


def side(ordinal, role, task, attempt):
    return ConflictSide(ordinal, role, task, attempt, "b" * 64, "c" * 64, "d" * 64)


def observation(source_type="integration_gate", paths=("src/a.py",), carry=()):
    sides = ((side(0, "accepted", "T-1", "A-1"), side(1, "candidate", "T-2", "A-2"))
             if source_type == "integration_gate" else
             (side(0, "accepted", "T-1", "A-1"), side(1, "accepted", "T-3", "A-3")))
    return ConflictObservation(source_type, "run-1", "plan-1", 1, DIGEST, "T-2", "A-2", "tok-1", "consumer-1",
                               "repo-1", paths, sides, "e" * 64, carry, ("f" * 64,),
                               "overlap_requires_structural_recovery", "ordinary rework refused: structural overlap")


def plan(source_type="integration_gate", **changes):
    values = dict(source_type=source_type, run_id="run-1", plan_id="plan-1", revision=1,
                  plan_sha256=DIGEST, task_id="T-2", attempt_id="A-2", token="tok-1",
                  consumer_id="consumer-1", repository_id="repo-1",
                  approved_start_paths=("src/a.py", "src/b.py"),
                  approved_integration_paths=("src/a.py", "src/b.py"), authority_status="authorized")
    return ConflictPlanFacts(**(values | changes))


def lineage(**changes):
    values = dict(status="current", evidence_complete=True, semantic_conflict=False)
    return ConflictLineageFacts(**(values | changes))


class ConflictPolicyTests(unittest.TestCase):
    def test_start_source_allows_accepted_sides_without_a_candidate_attempt(self):
        value = observation("start")
        self.assertEqual(ConflictObservation.from_dict(value.to_dict()), value)
        result = classify_conflict(value, plan("start"), lineage())
        self.assertEqual(result["dominant"], "structural_conflict_unclassified")

    def test_integration_gate_allows_an_ordinary_merge_without_carry_ancestry(self):
        value = observation(carry=())
        self.assertEqual(ConflictObservation.from_dict(value.to_dict()), value)
        result = classify_conflict(value, plan(), lineage(status="stale"))
        self.assertEqual(result["dominant"], "stale_lineage")
        self.assertEqual(result["allowable_actions"], ["rebuild_stale_descendant", "inherit_additive_checks"])

    def test_schema_rejects_unknown_fields_duplicate_or_unsafe_paths_and_missing_sides(self):
        value = observation()
        raw = value.to_dict()
        invalid = [
            raw | {"extra": True},
            raw | {"paths": ["src/a.py", "src/a.py"]},
            raw | {"paths": ["../secret"]},
            raw | {"sides": []},
        ]
        for raw in invalid:
            with self.subTest(raw=raw), self.assertRaises(RecoveryError):
                ConflictObservation.from_dict(raw)

    def test_source_identity_mismatch_is_evidence_incomplete(self):
        actual = observation()
        facts = plan(repository_id="other-repository")
        result = classify_conflict(actual, facts, lineage(status="stale"))
        self.assertEqual((result["dominant"], result["allowable_actions"]), ("evidence_incomplete", []))

    def test_scope_escape_dominates_staleness_and_preserves_accepted_sources(self):
        actual = observation(paths=("src/a.py", "unapproved/new.py"))
        result = classify_conflict(actual, plan(), lineage(status="stale"))
        self.assertEqual((result["dominant"], result["allowable_actions"]), ("scope_escape", []))
        self.assertEqual(result["facts"]["out_of_scope_paths"], ["unapproved/new.py"])
        self.assertTrue(result["facts"]["candidate_rejected"])
        self.assertTrue(result["facts"]["accepted_sources_preserved"])
        self.assertFalse(result["facts"]["permission_expanded"])

    def test_semantic_conflict_and_missing_authority_dominate_staleness(self):
        actual = observation()
        semantic = lineage(status="stale", semantic_conflict=True,
                           incompatible_requirements=("R-12", "R-14"))
        result = classify_conflict(actual, plan(), semantic)
        self.assertEqual((result["dominant"], result["allowable_actions"]), ("semantic_conflict", []))
        missing = classify_conflict(actual, plan(authority_status="missing"), lineage(status="stale"))
        self.assertEqual((missing["dominant"], missing["allowable_actions"]), ("missing_authority", []))

    def test_owner_stop_precedes_incomplete_evidence(self):
        actual = observation()
        result = classify_conflict(actual, plan(authority_status="owner_stop"),
                                   lineage(status="unknown", evidence_complete=False))
        self.assertEqual((result["dominant"], result["allowable_actions"]), ("owner_stop", []))

    def test_expected_path_overlap_does_not_infer_an_ownership_defect(self):
        result = classify_conflict(observation(), plan(), lineage())
        self.assertEqual(result["dominant"], "structural_conflict_unclassified")
        self.assertEqual(result["allowable_actions"], [])

    def test_future_ownership_repair_requires_a_demonstrated_defect(self):
        result = classify_conflict(observation(), plan(), lineage(
            status="stale", ownership_or_order_defect=True, demonstrated_future_defect=True))
        self.assertEqual(result["allowable_actions"], ["rebuild_stale_descendant", "converge_owned_paths",
                                                       "repair_demonstrated_future_ownership_order",
                                                       "inherit_additive_checks"])

    def test_strategy_identity_binds_action_graph_and_all_source_maps(self):
        strategy = ConflictStrategy(("a" * 64,), "b" * 64, ("c" * 64,), ("d" * 64,),
                                    ("converge_owned_paths", "inherit_additive_checks"),
                                    (("converge_owned_paths", "inherit_additive_checks"),))
        self.assertEqual(ConflictStrategy.from_dict(strategy.to_dict()), strategy)
        changed = replace(strategy, source_digests=("e" * 64,), strategy_id="")
        self.assertNotEqual(changed.strategy_id, strategy.strategy_id)
        with self.assertRaises(RecoveryError):
            ConflictStrategy.from_dict(strategy.to_dict() | {"unapproved": 1})

    def test_case_and_alias_checkpoint_reuse_the_existing_cycle(self):
        first = observation()
        aliases = lineage(aliases=("audit-case-1", "integration-case-1"))
        case = conflict_case(first, lineage_facts=aliases)
        from_start_gate = conflict_case(observation("start"), lineage_facts=aliases)
        self.assertEqual(from_start_gate.trigger_id, case.trigger_id)
        later = replace(first, revision=2, plan_sha256="9" * 64)
        reused = conflict_case(later, lineage_facts=aliases, existing_case=case)
        self.assertIs(reused, case)
        self.assertEqual(case.symptom, "integration_conflict")
        self.assertEqual(case.occurrences, ())
        advice = initial_conflict_advice(case, "evidence:" + "a" * 64)
        self.assertIsInstance(advice, RecoveryProposal)
        self.assertEqual(advice.action, "block")
        payload = conflict_envelope_payload(later, aliases)
        self.assertEqual(payload["lineage_aliases"], ["audit-case-1", "integration-case-1"])

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "diagnostics.db"
            with DiagnosticStore(path) as store:
                store.create_case(case, advice, now=10)
                store.acquire_lease(case.trigger_id, 0, "worker-1", now=11, lease_seconds=30)
                self.assertTrue(store.checkpoint_application(
                    case.trigger_id, 0, "worker-1", "conflict-checkpoint-1", payload, now=12))
                event = store.events(case.trigger_id)[-1]
                self.assertEqual(event["payload"]["lineage_aliases"], ["audit-case-1", "integration-case-1"])

    def test_unknown_lineage_cannot_create_or_alias_a_new_cycle(self):
        actual = observation()
        unknown = lineage(status="unknown", evidence_complete=False, aliases=("unverified-alias",))
        with self.assertRaisesRegex(RecoveryError, "LINEAGE_UNKNOWN"):
            conflict_case(actual, lineage_facts=unknown)
        payload = conflict_envelope_payload(actual, unknown)
        self.assertEqual(payload["lineage_aliases"], [])


if __name__ == "__main__":
    unittest.main()
