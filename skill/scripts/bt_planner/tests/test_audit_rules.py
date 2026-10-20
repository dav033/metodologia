"""An audit must declare a findings ledger and follow an end-to-end test over the real entry points."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from bt_planner import quality


def task(tid, kind, after=(), paths=(), category="functional"):
    return {"id": tid, "kind": kind, "after": list(after), "expected_paths": list(paths),
            "verification": [{"type": "command", "value": "true", "purpose": "p", "category": category}]}


def plan(*tasks):
    return {"tasks": list(tasks)}


LEDGER = "docs/audit.findings.json"


class AuditRules(unittest.TestCase):
    def test_a_plan_without_audit_has_nothing_to_check(self):
        self.assertEqual(quality.audit_findings(plan(task("T1", "implement"))), [])

    def test_a_complete_audit_passes(self):
        found = quality.audit_findings(plan(
            task("T1", "implement"), task("T2", "test", ["T1"], category="integration"),
            task("T3", "audit", ["T2"], [LEDGER, "docs/audit.md"])))
        self.assertEqual(found, [])

    def test_an_audit_without_a_ledger_is_refused(self):
        found = quality.audit_findings(plan(
            task("T2", "test", [], category="integration"), task("T3", "audit", ["T2"], ["docs/audit.md"])))
        self.assertEqual(len(found), 1)
        self.assertIn("T3.expected_paths", found[0])

    def test_two_ledgers_are_ambiguous(self):
        found = quality.audit_findings(plan(
            task("T2", "test", [], category="integration"),
            task("T3", "audit", ["T2"], [LEDGER, "other.findings.json"])))
        self.assertTrue(any("exactly one findings ledger" in item for item in found))

    def test_an_audit_needs_an_integration_test_before_it(self):
        found = quality.audit_findings(plan(
            task("T1", "implement"), task("T2", "test", ["T1"], category="functional"),
            task("T3", "audit", ["T2"], [LEDGER])))
        self.assertTrue(any("integration" in item and item.startswith("T3") for item in found))

    def test_an_integration_test_that_does_not_precede_the_audit_does_not_count(self):
        found = quality.audit_findings(plan(
            task("T1", "implement"), task("T3", "audit", ["T1"], [LEDGER]),
            task("T4", "test", ["T3"], category="integration")))
        self.assertTrue(any(item.startswith("T3") and "integration" in item for item in found))

    def test_the_integration_test_may_be_transitively_earlier(self):
        found = quality.audit_findings(plan(
            task("T1", "test", [], category="integration"), task("T2", "implement", ["T1"]),
            task("T3", "audit", ["T2"], [LEDGER])))
        self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()


class Retrofit(unittest.TestCase):
    """A plan written before the audit gate is brought in line without the author editing it by hand."""

    def setUp(self):
        import tempfile

        from bt_planner import contract as pc
        from bt_planner import revisions as rev
        self.pc, self.rev = pc, rev
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        self.plan = {
            "schema_version": "1.2.0", "plan_id": "REQ-1", "revision": 1,
            "tasks": [
                {"id": "T1", "kind": "test", "after": [], "expected_paths": ["e2e/**"]},
                {"id": "T2", "kind": "audit", "after": ["T1"], "expected_paths": ["docs/audit.md"]},
                {"id": "T3", "kind": "audit", "after": ["T2"], "expected_paths": ["src/x.py"]},
            ],
        }
        (self.dir / "PLAN.json").write_text(pc.dumps(self.plan), encoding="utf-8")
        (self.dir / "PLAN.md").write_text(
            "---\nstatus: launched\n---\n- [ ] T2 — Audit · repo: r · files: docs/audit.md · after: T1\n"
            "- [ ] T3 — Second audit · repo: r · files: src/x.py · after: T2\n", encoding="utf-8")

    def test_every_audit_gets_one_ledger_in_json_and_markdown(self):
        from bt_planner import sync
        changed = sync.retrofit_audit(self.dir)
        self.assertEqual(len(changed), 2)
        plan = self.pc.loads((self.dir / "PLAN.json").read_text(encoding="utf-8"))
        self.assertEqual(plan["tasks"][1]["expected_paths"], ["docs/audit.md", "docs/audit.findings.json"])
        self.assertEqual(plan["tasks"][2]["expected_paths"], ["src/x.py", "src/t3.findings.json"])
        self.assertEqual(plan["tasks"][0]["expected_paths"], ["e2e/**"])
        text = (self.dir / "PLAN.md").read_text(encoding="utf-8")
        self.assertIn("files: docs/audit.md, docs/audit.findings.json · after: T1", text)
        self.assertIn("files: src/x.py, src/t3.findings.json · after: T2", text)

    def test_it_is_idempotent_and_leaves_compliant_plans_alone(self):
        from bt_planner import sync
        sync.retrofit_audit(self.dir)
        before = (self.dir / "PLAN.json").read_text(encoding="utf-8")
        self.assertEqual(sync.retrofit_audit(self.dir), [])
        self.assertEqual((self.dir / "PLAN.json").read_text(encoding="utf-8"), before)

    def test_the_new_working_revision_follows_the_last_frozen_one(self):
        from bt_planner import sync
        self.plan["tasks"][1]["expected_paths"].append("docs/audit.findings.json")
        self.plan["tasks"][2]["expected_paths"].append("src/t3.findings.json")
        (self.dir / "PLAN.json").write_text(self.pc.dumps(self.plan), encoding="utf-8")
        self.assertEqual(sync.retrofit_audit(self.dir), [])
        # an old plan: pretend revision 1 is frozen, drop the ledger of T3, and retrofit
        self.plan["tasks"][2]["expected_paths"] = ["src/x.py"]
        (self.dir / "PLAN.json").write_text(self.pc.dumps(self.plan), encoding="utf-8")
        import bt_planner.revisions as rev
        original = rev.latest
        rev.latest = lambda directory: {"revision": 3}
        try:
            sync.retrofit_audit(self.dir)
        finally:
            rev.latest = original
        self.assertEqual(self.pc.loads((self.dir / "PLAN.json").read_text(encoding="utf-8"))["revision"], 4)
