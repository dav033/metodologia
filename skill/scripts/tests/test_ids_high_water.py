"""Issued IDs never go back down: pruning a closed item from PENDING.md must not free its number."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import bt_core  # noqa: E402


class HighWaterIdTests(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory(prefix="ids-test-")
        self.addCleanup(tmp.cleanup)
        self.pdir = Path(tmp.name) / "demo"
        self.pdir.mkdir()
        patcher = patch("bt_vcs.pull", return_value="")  # next_id pulls the bitácora first; no git in tests
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_a_pruned_closed_item_does_not_free_its_number(self):
        (self.pdir / "PENDING.md").write_text(
            "# demo — Pending\n\n## Open\n- P-001 · open thing · urgency: med · complexity: S\n\n"
            "## Recently closed\n_None_\n", encoding="utf-8")
        day = self.pdir / "2026-10" / "W2"
        day.mkdir(parents=True)
        (day / "2026-10-08.md").write_text("- ✓ P-002 closed in the session\n", encoding="utf-8")
        self.assertEqual(bt_core.next_id(self.pdir, "P"), "P-003")

    def test_fresh_project_starts_at_one(self):
        self.assertEqual(bt_core.next_id(self.pdir, "P"), "P-001")


if __name__ == "__main__":
    unittest.main()
