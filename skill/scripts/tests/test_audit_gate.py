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

    def test_medium_low_fixed_and_owner_accepted_findings_do_not_block(self):
        result = self.judge(ledger(
            finding("F1", "medium"), finding("F2", "low"),
            finding("F3", "critical", "fixed", evidence="regression test test_x"),
            finding("F4", "high", "accepted", accepted_by="owner", reason="known; shipped behind a flag")))
        self.assertTrue(result.ok, result.summary())

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


class Configured(unittest.TestCase):
    def test_the_blocking_severities_come_from_the_policy(self):
        medium = ledger(finding("F1", "medium"))
        self.assertTrue(gate.evaluate(medium, PLAN, "T9").ok)
        self.assertFalse(gate.evaluate(medium, PLAN, "T9", gate.Policy(blocking=("critical", "high", "medium"))).ok)

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

    def test_the_planner_and_the_gate_agree_on_the_ledger_suffix(self):
        from bt_planner import quality
        self.assertEqual(quality.LEDGER_SUFFIX, gate.LEDGER_SUFFIX)


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


if __name__ == "__main__":
    unittest.main()
