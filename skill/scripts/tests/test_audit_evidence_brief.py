"""An audit's brief says to keep screenshots and logs outside the repository (pictures REQ-021 T2.7 and T5.5)."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bt_audit_gate
import bt_scheduler_executor_wiring as wiring


class Plan:
    def __init__(self, tasks):
        self.tasks = tasks

    def task(self, task_id):
        return self.tasks[task_id]


class AuditEvidence(unittest.TestCase):
    def test_an_audit_is_told_where_its_evidence_goes_and_a_builder_is_not(self):
        rdir = Path(tempfile.mkdtemp(prefix="bt-audit-evidence-")) / "REQ-021-x"
        rdir.mkdir()
        plan = Plan({
            "T5.5": SimpleNamespace(meta={"kind": "audit"}, expected_paths=(".evidence/REQ-021/SP-5.visual.md",
                                                                            ".evidence/REQ-021/SP-5.visual.findings.json")),
            "T5.3": SimpleNamespace(meta={"kind": "implement"}, expected_paths=("src/x.ts",)),
        })
        notes = wiring.owner_notes(rdir, plan, None, state=lambda task_id: {}, verify=False)
        audit = notes(SimpleNamespace(task_id="T5.5"))
        self.assertIn(f"`{rdir / 'evidence' / 'T5.5'}`", audit)
        self.assertIn("Inside the repository write only the report and the ledger", audit)
        self.assertIn(".evidence/REQ-021/SP-5.visual.findings.json", audit)
        self.assertNotIn("OUTSIDE it", notes(SimpleNamespace(task_id="T5.3")))

    def test_the_rule_matches_what_the_gate_rejects(self):
        stray = bt_audit_gate.stray_changes([".evidence/REQ-021/SP-5.visual/captures/desktop.png",
                                             ".evidence/REQ-021/SP-5.visual.md"], [".evidence/REQ-021/SP-5.visual.md"])
        self.assertEqual(stray, (".evidence/REQ-021/SP-5.visual/captures/desktop.png",))


if __name__ == "__main__":
    unittest.main()
