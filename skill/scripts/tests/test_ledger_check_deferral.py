"""REQ-020 T15: an audit whose only real failures are its ledger checks must reach the audit gate even when an expensive check was deferred."""
import unittest
from types import SimpleNamespace

from bt_scheduler_quality_adapter import QualityVerificationPort

LEDGER = "docs/req-020/T15.findings.json"


def port(kind="audit"):
    task = SimpleNamespace(meta={"kind": kind}, expected_paths=(LEDGER, "docs/req-020/T15.md"))
    self = QualityVerificationPort.__new__(QualityVerificationPort)
    self.core = SimpleNamespace(plan=SimpleNamespace(task=lambda _tid: task))
    return self


def check(command, status, issue=None):
    return {"command": command, "status": status, "issue_code": issue}


class LedgerOnly(unittest.TestCase):
    order = SimpleNamespace(task_id="T15")

    def test_a_deferred_whole_suite_does_not_hide_that_only_the_ledger_checks_failed(self):
        result = {"checks": [check(f"npx tsx check-findings.ts {LEDGER}", "fail"),
                             check(f"npx tsx check-findings.ts {LEDGER} --check-audit-diff", "fail"),
                             check("npm run gate", "unknown", "CHECK_DEFERRED")]}
        self.assertTrue(port()._only_ledger_checks_failed(self.order, result))

    def test_a_real_failure_of_another_check_or_a_non_audit_task_still_keeps_the_gate_out(self):
        other = {"checks": [check(f"npx tsx check-findings.ts {LEDGER}", "fail"), check("npm run lint", "fail")]}
        self.assertFalse(port()._only_ledger_checks_failed(self.order, other))
        self.assertFalse(port("implement")._only_ledger_checks_failed(self.order, {"checks": [check(f"x {LEDGER}", "fail")]}))
        self.assertFalse(port()._only_ledger_checks_failed(self.order, {"checks": [check("npm run gate", "unknown", "CHECK_DEFERRED")]}))


if __name__ == "__main__":
    unittest.main()
