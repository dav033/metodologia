"""Every task of a UI subplan that touches the contract is told which contract and approval state applies."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bt_scheduler_executor_wiring import contract_notes  # noqa: E402


def _plan():
    tasks = {"T1": {"kind": "design", "subplan_id": "SP-1"}, "T2": {"kind": "implement", "ui": True, "subplan_id": "SP-1"},
             "T3": {"kind": "audit", "subplan_id": "SP-1"}, "T4": {"kind": "implement", "subplan_id": "SP-2"}}
    ui = SimpleNamespace(contract="checkout", version=2, design_task="T1", visual_review_task="T3")
    subplans = (SimpleNamespace(id="SP-1", ui=ui), SimpleNamespace(id="SP-2", ui=None))
    return SimpleNamespace(subplans=subplans, task=lambda tid: SimpleNamespace(meta=tasks[tid], repository="app"))


class ContractNotes(unittest.TestCase):
    def notes(self, task_id):
        approval = lambda repo, base, path: {"state": "approved", "sha256": "a" * 64}  # noqa: E731
        return contract_notes(_plan(), SimpleNamespace(task_id=task_id, base_ref="b"), lambda task: "repo", approval)

    def test_design_ui_and_visual_review_tasks_name_the_contract_and_approval(self):
        for task_id in ("T1", "T2", "T3"):
            with self.subTest(task=task_id):
                notes = self.notes(task_id)
                self.assertIn("Design contract: design/contracts/checkout@v2.md", notes)
                self.assertIn("Approval: approved", notes)
        self.assertIn("UI task: true", self.notes("T2"))

    def test_tasks_outside_ui_subplans_get_no_contract_notes(self):
        self.assertEqual(self.notes("T4"), "")


if __name__ == "__main__":
    unittest.main()
