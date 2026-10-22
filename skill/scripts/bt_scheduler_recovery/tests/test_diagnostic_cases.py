import sqlite3
import tempfile
import unittest
from pathlib import Path

from bt_scheduler_recovery import DiagnosticStore, RecoveryError
from bt_scheduler_recovery.diagnostic_contracts import (
    DiagnosticCase,
    FindingOccurrence,
    FindingRelation,
    PrerequisiteCheck,
    ProgressSnapshot,
    RecoveryProposal,
    VerificationCheck,
    VerificationMap,
    VerificationPath,
)
from bt_scheduler_recovery.history import APP_ID, SCHEMA
from bt_scheduler_recovery.progress import assess_progress


def occurrence(ledger, finding, state="open", evidence=True):
    refs = ("ledger:" + "e" * 64,) if evidence else ()
    return FindingOccurrence(ledger, finding, state, refs)


def case(trigger="trigger-1", occurrences=(), relations=()):
    return DiagnosticCase(trigger, "run-1", "plan-1", 1, "a" * 64, "audit_regression",
                          tuple(occurrences), tuple(relations))


def proposal(trigger="trigger-1"):
    return RecoveryProposal(trigger, 0, "rework_findings", "audit_findings_open",
                            ("ledger:" + "e" * 64,), "confirmed")


class DiagnosticCaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "diagnostics.db"
        self.addCleanup(self.temp.cleanup)

    def test_trigger_replay_is_deduplicated_and_generation_is_fenced(self):
        with DiagnosticStore(self.path) as store:
            self.assertTrue(store.create_case(case(), proposal(), now=10)["created"])
            self.assertFalse(store.create_case(case(), proposal(), now=11)["created"])
            self.assertEqual(len(store.events("trigger-1")), 1)
            store.acquire_lease("trigger-1", 0, "worker-1", now=12, lease_seconds=20)
            self.assertTrue(store.checkpoint_application("trigger-1", 0, "worker-1", "apply-1",
                                                         {"status": "applied"}, now=13))
            self.assertFalse(store.checkpoint_application("trigger-1", 0, "worker-1", "apply-1",
                                                          {"status": "applied"}, now=14))
            self.assertEqual(store.transition("trigger-1", 0, "worker-1", "event-1", "rework_applied",
                                              {"task_ids": ["T-1"]}, now=15), 1)
            self.assertEqual(store.transition("trigger-1", 0, "worker-1", "event-1", "rework_applied",
                                              {"task_ids": ["T-1"]}, now=16), 1)
            with self.assertRaisesRegex(RecoveryError, "GENERATION_CONFLICT"):
                store.acquire_lease("trigger-1", 0, "worker-2", now=16, lease_seconds=20)
            self.assertEqual([item["generation"] for item in store.events("trigger-1")], [0, 0, 1])

    def test_renumbered_occurrence_requires_explicit_evidence_relation(self):
        old = occurrence("b" * 64, "F-014")
        renamed = occurrence("c" * 64, "F-002")
        unrelated = occurrence("d" * 64, "F-003")
        link = FindingRelation(old.occurrence_id, renamed.occurrence_id, "same_finding",
                               ("audit:" + "f" * 64,))
        result = assess_progress(ProgressSnapshot((old,)),
                                 ProgressSnapshot((renamed, unrelated), (link,)))
        self.assertEqual(result.persisted, (renamed.occurrence_id,))
        self.assertEqual(result.new, (unrelated.occurrence_id,))
        self.assertNotIn(unrelated.occurrence_id, result.persisted)

    def test_missing_evidence_stays_uncertain_and_prerequisites_are_explicit(self):
        prior = occurrence("b" * 64, "F-1")
        without_evidence = occurrence("c" * 64, "F-9", evidence=False)
        result = assess_progress(ProgressSnapshot((prior,)), ProgressSnapshot(
            (without_evidence,), (), (PrerequisiteCheck("check-schema", "blocked"),)))
        self.assertEqual(result.uncertain, tuple(sorted((prior.occurrence_id, without_evidence.occurrence_id))))
        self.assertEqual(result.blocked_prerequisites, ("check-schema",))

    def test_fixed_and_regressed_require_linked_occurrences(self):
        old_fixed = occurrence("b" * 64, "F-1", state="fixed")
        old_open = occurrence("c" * 64, "F-2")
        recurrence = occurrence("d" * 64, "F-9")
        fixed_now = occurrence("e" * 64, "F-10", state="fixed")
        links = (
            FindingRelation(old_fixed.occurrence_id, recurrence.occurrence_id, "same_finding",
                            ("audit:" + "f" * 64,)),
            FindingRelation(old_open.occurrence_id, fixed_now.occurrence_id, "same_finding",
                            ("audit:" + "a" * 64,)),
        )
        result = assess_progress(ProgressSnapshot((old_fixed, old_open)),
                                 ProgressSnapshot((recurrence, fixed_now), links))
        self.assertEqual(result.regressed, (recurrence.occurrence_id,))
        self.assertEqual(result.fixed, (fixed_now.occurrence_id,))

    def test_proposal_version_is_validated(self):
        raw = proposal().to_dict()
        self.assertEqual(RecoveryProposal.from_dict(raw), proposal())
        for invalid in ({**raw, "schema_version": "recovery-proposal/2"},
                        {**raw, "schema_version": None}, {key: value for key, value in raw.items()
                                                           if key != "schema_version"}):
            with self.subTest(invalid=invalid), self.assertRaises(RecoveryError):
                RecoveryProposal.from_dict(invalid)

    def test_schema_one_decision_rows_survive_transactional_migration(self):
        with sqlite3.connect(self.path) as connection:
            for statement in SCHEMA.split(";"):
                if statement.strip():
                    connection.execute(statement)
            connection.execute(f"PRAGMA application_id={APP_ID}")
            connection.execute("PRAGMA user_version=1")
            connection.execute("INSERT INTO decisions VALUES(1,?,?,?,?,?,?,?,?,?,?)",
                               ("decision-1", "run-1", "T-1", "A-1", "timeout", "{}", "{}", "{}", "{}", "retry"))
        self.path.chmod(0o600)
        with DiagnosticStore(self.path):
            pass
        with sqlite3.connect(self.path) as connection:
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 2)
            self.assertEqual(connection.execute("SELECT decision_id,action FROM decisions").fetchall(),
                             [("decision-1", "retry")])
            tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertTrue({"recovery_cases", "recovery_events", "recovery_leases", "application_checkpoints"} <= tables)

    def test_verification_map_preserves_uncovered_items_as_uncovered(self):
        value = VerificationMap(
            (VerificationPath("skill/scripts/example.py", "a" * 64, "T-1"),),
            (VerificationCheck("check-1", "T-1", "python3 -m unittest", "audit_regression",
                               "verdict:" + "b" * 64),),
            ("python3 -m unittest",), ("docs/unmapped.md",), ("check-unmapped",))
        parsed = VerificationMap.from_dict(value.to_dict())
        self.assertEqual(parsed, value)
        self.assertEqual(parsed.uncovered_paths, ("docs/unmapped.md",))
        self.assertEqual(parsed.uncovered_checks, ("check-unmapped",))


if __name__ == "__main__":
    unittest.main()
