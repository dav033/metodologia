"""Command verification lint, independent of repository access."""
from __future__ import annotations

import unittest

from bt_planner import command_checks, contract
from support import PlanDir


class Commands(PlanDir):
    def test_malformed_verification_remains_a_contract_error_instead_of_crashing_the_lint(self):
        plan = self.good()
        plan["tasks"][0].update(kind="audit", verification=None)
        report = contract.validate(plan, ignored_path=lambda repo, path: True)
        self.assertTrue(any("verification" in p for p in report.errors))

    def test_the_publication_gate_refuses_a_known_ignored_input(self):
        plan = self.good()
        plan["tasks"][0]["verification"][0]["value"] = "cat reports/result.json"
        self.write(plan)
        ignored = lambda repo, path: path == "reports/result.json"
        report = self.sync.check(self.rdir, ignored_path=ignored)
        self.assertTrue(any("git-ignored" in p for p in report.errors))
        with self.assertRaises(contract.PlanContractError):
            self.sync.approve_freeze(self.rdir, ignored_path=ignored)

    def test_a_declared_path_is_not_a_command_that_produces_it(self):
        plan = {"tasks": [{"id": "T1", "expected_paths": ["reports/r.json"], "repository": "repo",
                           "verification": [{"type": "command", "value": "cat reports/r.json"}]}]}
        self.assertTrue(command_checks.input_findings(plan, lambda repo, path: True)[0])

    def test_unknown_script_argument_semantics_warn_instead_of_refusing_approval(self):
        plan = self.good()
        plan["tasks"][0]["verification"][0]["value"] = "npx tsx check.ts reports/results.json"
        report = contract.validate(plan, ignored_path=lambda repo, path: path.startswith("reports/"))
        self.assertFalse(any("git-ignored" in p for p in report.errors))
        self.assertTrue(any("git-ignored" in p for p in report.warnings))

    def test_copying_the_input_into_place_is_a_producer(self):
        plan = {"tasks": [{"id": "T1", "repository": "app", "verification": [
            {"type": "command", "value": "cp fixture.json reports/results.json"},
            {"type": "command", "value": "cat reports/results.json"}]}]}
        self.assertEqual(command_checks.input_findings(plan, lambda repo, path: path.startswith("reports/")), ([], []))

    def test_an_audit_using_a_private_ledger_checker_gets_advice_but_no_error(self):
        plan = self.good()
        task = plan["tasks"][0]
        task["kind"] = "audit"
        task["verification"][0]["value"] = "npx tsx scripts/check.ts docs/T1.findings.json"
        warnings = contract.validate(plan).warnings
        self.assertTrue(any("audit-ledger check" in p for p in warnings))
        task["verification"][0]["value"] = "engine audit-ledger check docs/T1.findings.json"
        self.assertFalse(command_checks.project_ledger_checks(plan))
        task["kind"] = "implement"
        task["verification"][0]["value"] = "python check.py audit-findings"
        self.assertFalse(command_checks.project_ledger_checks(plan))

    def test_publication_refuses_private_ledger_checks_but_runtime_still_loads_them(self):
        plan = self.good()
        plan["tasks"][0].update(kind="test")
        plan["tasks"][0]["verification"][0]["category"] = "integration"
        task = plan["tasks"][2]
        task.update(kind="audit", expected_paths=["docs/T3.findings.json"])
        task["verification"][0]["value"] = "npx tsx scripts/check.ts docs/T3.findings.json"
        self.write(plan)
        self.md(text=(self.rdir / "PLAN.md").read_text().replace("pytest -q", task["verification"][0]["value"]))
        self.assertTrue(contract.load(self.rdir / "PLAN.json"))
        report = self.sync.check(self.rdir)
        self.assertTrue(any("engine audit-ledger check docs/T3.findings.json" in p for p in report.errors))
        with self.assertRaises(contract.PlanContractError):
            self.sync.approve_freeze(self.rdir)

    def test_only_the_engine_command_is_exempt(self):
        plan = {"tasks": [{"id": "T1", "kind": "audit", "expected_paths": ["docs/audit.findings.json"],
                           "verification": [{"type": "command", "value": ""}]}]}
        for command in ("python check.py docs/audit.findings.json audit-ledger check",
                        "other audit-ledger check docs/audit.findings.json", "npx check '*.findings.json'",
                        "npm run check -- docs/audit.findings.json", "cat docs/audit.findings.json"):
            plan["tasks"][0]["verification"][0]["value"] = command
            self.assertTrue(command_checks.project_ledger_checks(plan), command)

    def test_engine_command_in_one_shell_segment_does_not_exempt_a_private_checker(self):
        plan = self.good()
        task = plan["tasks"][0]
        task["kind"] = "audit"
        task["verification"][0]["value"] = ("engine audit-ledger check docs/T1.findings.json && "
                                               "python check.py docs/T1.findings.json")
        self.assertTrue(command_checks.project_ledger_checks(plan))


if __name__ == "__main__":
    unittest.main()
