"""The audit gate judges the findings ledger, never the prose of the report."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bt_audit_gate as gate

PLAN = ["T1", "T2", "T3", "T9"]


def ledger(*findings):
    return json.dumps({"schema": gate.SCHEMA, "findings": list(findings)})


def finding(fid="F1", severity="high", status="open", tasks=("T1",), **extra):
    return {"id": fid, "severity": severity, "status": status, "summary": f"{fid} is wrong", "tasks": list(tasks), **extra}


class Evaluate(unittest.TestCase):
    def test_semantic_fingerprint_canonicalization_is_stable(self):
        left = gate.semantic_fingerprint(" API  ", "Race Condition", "when X", ["T2", "T1", "T1"])
        right = gate.semantic_fingerprint("api", "race condition", "WHEN   x", ["t1", "t2"])
        self.assertEqual(left, right)
        self.assertEqual(len(left), 64)

    def test_task_references_and_closed_are_compatible_spellings_of_tasks_and_fixed(self):
        canonical = finding(status="fixed", evidence="pytest: passed")
        alias = {**canonical, "status": "closed", "taskReferences": canonical["tasks"]}
        del alias["tasks"]
        for item in (canonical, alias):
            self.assertEqual(gate.validate_ledger(json.loads(ledger(item))), [])
        self.assertEqual(self.judge(ledger(canonical)), self.judge(ledger(alias)))
        canonical["status"], alias["status"] = "open", "open"
        self.assertEqual(self.judge(ledger(canonical)), self.judge(ledger(alias)))
        self.assertEqual(self.judge(ledger(alias)).rework, ("T1",))

    def test_info_is_valid_and_closed_requires_the_same_evidence_as_fixed(self):
        self.assertEqual(gate.validate_ledger(json.loads(ledger(finding(severity="info")))), [])
        self.assertTrue(self.judge(ledger(finding(severity="info"))).ok)
        self.assertEqual(self.judge(ledger(finding(status="fixed"))).problems,
                         self.judge(ledger(finding(status="closed"))).problems)
        invalid_alias = finding(taskReferences="T1")
        del invalid_alias["tasks"]
        self.assertTrue(gate.validate_ledger(json.loads(ledger(invalid_alias))))

    def test_the_public_validator_accepts_a_valid_ledger_without_applying_blocking_policy(self):
        self.assertEqual(gate.validate_ledger(json.loads(ledger(finding()))), [])

    def test_the_public_validator_reports_the_same_schema_problems_as_the_gate(self):
        for data in ([], {}, {"schema": gate.SCHEMA, "findings": [finding(status="fixed")]},
                     {"schema": gate.SCHEMA, "findings": [finding(), finding()]}):
            with self.subTest(data=data):
                self.assertEqual(gate.validate_ledger(data)[:20], list(self.judge(json.dumps(data)).problems))

    def judge(self, raw):
        return gate.evaluate(raw, PLAN, "T9")

    def test_no_findings_passes(self):
        self.assertTrue(self.judge(ledger()).ok)

    def test_an_open_high_or_critical_finding_rejects_and_names_the_tasks(self):
        result = self.judge(ledger(finding("F1", "critical", tasks=("T2",)), finding("F2", "high", tasks=("T1", "T2"))))
        self.assertFalse(result.ok)
        self.assertEqual(result.problems, ())
        self.assertEqual([f["id"] for f in result.blocking], ["F1", "F2"])
        self.assertEqual(result.rework, ("T2", "T1"))

    def test_low_fixed_and_owner_accepted_findings_do_not_block(self):
        result = self.judge(ledger(
            finding("F2", "low"),
            finding("F3", "critical", "fixed", evidence="regression test test_x"),
            finding("F4", "high", "accepted", accepted_by="owner", reason="known; shipped behind a flag")))
        self.assertTrue(result.ok, result.summary())

    def test_a_confirmed_medium_finding_blocks_by_default_so_it_is_repaired(self):
        # D-233, owner 2026-10-30: «los hallazgos son reales y son un problema … el sistema debería poder hacerlo sin
        # mi intervención» (pictures T2.7: six medium contract mismatches would otherwise stay open)
        result = self.judge(ledger(finding("F1", "medium")))
        self.assertFalse(result.ok)
        self.assertEqual([f["id"] for f in result.blocking], ["F1"])

    def test_an_auditor_cannot_accept_its_own_finding(self):
        result = self.judge(ledger(finding("F1", "high", "accepted", accepted_by="auditor", reason="minor")))
        self.assertFalse(result.ok)
        self.assertTrue(any("accepted" in p for p in result.problems))

    def test_fixed_needs_evidence(self):
        self.assertFalse(self.judge(ledger(finding("F1", "high", "fixed"))).ok)

    def test_unknown_tasks_and_the_audit_itself_are_not_sent_back(self):
        result = self.judge(ledger(finding("F1", "high", tasks=("T404", "T9", "T3"))))
        self.assertFalse(result.ok)
        self.assertEqual(result.rework, ("T3",))

    def test_a_blocking_finding_without_known_tasks_rejects_without_rework(self):
        result = self.judge(ledger(finding("F1", "high", tasks=())))
        self.assertEqual((result.ok, result.rework), (False, ()))

    def test_missing_malformed_or_foreign_ledgers_reject(self):
        for raw in (None, b"\xff\xfe", "not json", "[]", json.dumps({"schema": "x", "findings": []}),
                    json.dumps({"schema": gate.SCHEMA, "findings": "none"}), b"x" * (gate.MAX_BYTES + 1)):
            with self.subTest(raw=str(raw)[:20]):
                result = self.judge(raw)
                self.assertFalse(result.ok)
                self.assertTrue(result.problems)
                self.assertEqual(result.rework, ())

    def test_invalid_findings_are_reported_with_their_position(self):
        result = self.judge(ledger(finding("F1", severity="urgent"), finding("F1", status="maybe")))
        text = " ".join(result.problems)
        self.assertIn("findings[0].severity", text)
        self.assertIn("findings[1].status", text)
        self.assertIn("duplicate", text)

    def test_the_digest_is_stable_and_changes_with_the_outcome(self):
        a = self.judge(ledger(finding("F1")))
        self.assertEqual(a.digest(), self.judge(ledger(finding("F1"))).digest())
        self.assertNotEqual(a.digest(), self.judge(ledger(finding("F2"))).digest())

    def test_fingerprint_is_shape_checked_and_duplicate_open_findings_merge_evidence(self):
        one = finding("F1", tasks=("T1",), semantic_fingerprint="a" * 64, evidence_refs=["e1"])
        two = finding("F2", tasks=("T2",), semantic_fingerprint="a" * 64, evidence_refs=["e2"])
        result = self.judge(ledger(one, two))
        self.assertEqual(len(result.blocking), 1)
        self.assertEqual(result.rework, ("T1", "T2"))
        self.assertEqual(result.blocking[0]["evidence_refs"], ("e1", "e2"))
        self.assertEqual(gate.validate_ledger(json.loads(ledger(finding(semantic_fingerprint="A" * 64)))) != [], True)

    def test_unfingerprinted_findings_and_distinct_same_line_fingerprints_stay_separate(self):
        rows = [finding("F1"), finding("F2"),
                finding("F3", semantic_fingerprint="a" * 64, location="x.py:9"),
                finding("F4", semantic_fingerprint="b" * 64, location="x.py:9")]
        result = self.judge(ledger(*rows))
        self.assertEqual(len(result.blocking), 4)

    def test_same_fingerprint_across_independent_ledgers_counts_once(self):
        rows = [ledger(finding("F1", tasks=("T1",), semantic_fingerprint="a" * 64)),
                ledger(finding("F2", tasks=("T2",), semantic_fingerprint="a" * 64))]
        result = gate.evaluate_many(rows, PLAN, "T9")
        self.assertEqual(len(result.blocking), 1)
        self.assertEqual(result.rework, ("T1", "T2"))


class Configured(unittest.TestCase):
    def test_the_blocking_severities_come_from_the_policy(self):
        medium = ledger(finding("F1", "medium"))
        self.assertFalse(gate.evaluate(medium, PLAN, "T9").ok)                       # the default blocks it (D-233)
        self.assertTrue(gate.evaluate(medium, PLAN, "T9", gate.Policy(blocking=("critical", "high"))).ok)

    def test_policy_from_reads_config_and_falls_back_on_garbage(self):
        values = {"gates.audit_blocking": ["high", "medium"], "gates.audit_ledger_required": False}
        policy = gate.policy_from(lambda key, default=None: values.get(key, default))
        self.assertEqual((policy.blocking, policy.ledger_required), (("high", "medium"), False))
        for bad in ([], ["urgent"], "high", None):
            policy = gate.policy_from(lambda key, default=None, bad=bad: bad if key == "gates.audit_blocking" else "no")
            self.assertEqual((policy.blocking, policy.ledger_required), (gate.BLOCKING_SEVERITIES, True))

    def test_the_real_config_defaults_and_validation(self):
        import bt_config
        self.assertEqual(gate.policy_from(lambda key, default=None: bt_config.DEFAULTS["gates"][key.split(".")[1]]),
                         gate.Policy())
        self.assertTrue(bt_config._valid("gates.audit_blocking", ["critical"]))
        self.assertFalse(bt_config._valid("gates.audit_blocking", []))
        self.assertFalse(bt_config._valid("gates.audit_blocking", ["urgent"]))
        self.assertFalse(bt_config._valid("gates.max_reworks", 0))
        self.assertTrue(bt_config._valid("gates.audit_ledger_required", False))


class Paths(unittest.TestCase):
    def test_exactly_one_ledger_is_found(self):
        self.assertEqual(gate.ledger_path(["a.md", "docs/x.findings.json"]), "docs/x.findings.json")
        self.assertIsNone(gate.ledger_path(["a.md"]))
        self.assertIsNone(gate.ledger_path(["a.findings.json", "b.findings.json"]))


class Notes(unittest.TestCase):
    def test_a_named_task_reads_its_findings_and_a_dependent_reads_why_it_was_reset(self):
        result = gate.evaluate(ledger(finding("F1", "critical", tasks=("T1",))), PLAN, "T9")
        self.assertIn("F1 (critical)", gate.note_for(result, "T1", "T9"))
        self.assertIn("depends on", gate.note_for(result, "T2", "T9"))


class ReadOnly(unittest.TestCase):
    def test_only_the_declared_files_are_allowed(self):
        declared = ["docs/audit.md", "docs/audit.findings.json"]
        self.assertEqual(gate.stray_changes(["docs/audit.md", "/docs/audit.findings.json"], declared), ())
        self.assertEqual(gate.stray_changes(["remote/a.py", "docs/audit.md", "b.txt"], declared),
                         ("b.txt", "remote/a.py"))

    def test_the_message_names_the_files_and_what_to_do(self):
        text = gate.scope_problem(tuple(f"f{i}.py" for i in range(7)))
        self.assertIn("7 file(s)", text)
        self.assertIn("2 more", text)
        self.assertIn("open finding", text)

    def test_policy_reads_the_flag_and_defaults_to_on(self):
        self.assertTrue(gate.policy_from(lambda key, default: default).read_only)
        self.assertFalse(gate.policy_from(
            lambda key, default: False if key == "gates.audit_read_only" else default).read_only)
        self.assertTrue(gate.policy_from(
            lambda key, default: "no" if key == "gates.audit_read_only" else default).read_only)

    def test_rework_scope_defaults_to_named_and_ignores_unknown_values(self):
        self.assertEqual(gate.policy_from(lambda key, default: default).rework_scope, "named")
        pick = lambda value: gate.policy_from(lambda key, default: value if key == "gates.rework_scope" else default)
        self.assertEqual(pick("downstream").rework_scope, "downstream")
        self.assertEqual(pick("everything").rework_scope, "named")


if __name__ == "__main__":
    unittest.main()
