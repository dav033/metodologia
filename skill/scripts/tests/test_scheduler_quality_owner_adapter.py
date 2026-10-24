"""Owner-facing M6 adapter contract for independent audit ledgers."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bt_audit_gate
from bt_scheduler_quality_owner_adapter import evaluate_audit_ledgers, expected_environment_fingerprint


class IndependentAuditLedgers(unittest.TestCase):
    def _ledger(self, finding):
        import json

        return json.dumps({"schema": bt_audit_gate.SCHEMA, "findings": [finding]}).encode()

    def _finding(self, identity, *, fingerprint=None, task="T1", evidence_ref="sha256:" + "a" * 64):
        finding = {"id": identity, "severity": "high", "status": "open", "summary": identity,
                   "tasks": [task], "evidence": identity + " diagnostic", "evidence_refs": [evidence_ref]}
        if fingerprint is not None:
            finding["semantic_fingerprint"] = fingerprint
        return finding

    def test_matching_fingerprints_merge_evidence_and_keep_distinct_defects(self):
        fingerprint = "b" * 64
        ledgers = [self._ledger(self._finding("F1", fingerprint=fingerprint, evidence_ref="sha256:" + "1" * 64)),
                   self._ledger(self._finding("F2", fingerprint=fingerprint, evidence_ref="sha256:" + "2" * 64)),
                   self._ledger(self._finding("F3", fingerprint="c" * 64, evidence_ref="sha256:" + "3" * 64))]

        gate = evaluate_audit_ledgers(ledgers, ["T1"], "T2")

        self.assertFalse(gate.ok)
        self.assertEqual(len(gate.blocking), 2)
        merged = gate.blocking[0]
        self.assertEqual(set(merged["tasks"]), {"T1"})
        self.assertEqual(set(merged["evidence_refs"]), {"sha256:" + "1" * 64, "sha256:" + "2" * 64})
        self.assertEqual(len(merged["evidence_entries"]), 2)

    def test_missing_or_oversized_ledgers_are_refused_before_evaluation(self):
        self.assertFalse(evaluate_audit_ledgers([None], ["T1"], "T2").ok)
        self.assertFalse(evaluate_audit_ledgers([b"x" * (bt_audit_gate.MAX_BYTES + 1)], ["T1"], "T2").ok)
        self.assertFalse(evaluate_audit_ledgers([b"{}"] * 65, ["T1"], "T2").ok)

    def test_environment_binding_matches_the_exact_m6_policy_and_order_identity(self):
        from bt_scheduler_quality.policy import QualityPolicy
        from bt_scheduler_quality.reuse import bound_environment_fingerprint

        policy = QualityPolicy()
        contracts = {"api@1": "a" * 64, "ui@1": "b" * 64}
        identity = "c" * 64

        self.assertEqual(expected_environment_fingerprint(policy, contracts, identity),
                         bound_environment_fingerprint(policy, tuple(sorted(contracts.items())), identity))


if __name__ == "__main__":
    unittest.main()
