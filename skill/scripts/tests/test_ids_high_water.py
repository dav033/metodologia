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

    def test_a_reserved_number_is_never_handed_out_twice(self):
        """D-209: five sessions and agents picked the same D-NNN from DECISIONS.md on 2026-10-29/30."""
        (self.pdir / "DECISIONS.md").write_text("# demo — Decisions\n\n## D-205 — taken\n", encoding="utf-8")
        self.assertEqual(bt_core.next_id(self.pdir, "D", reserve="engine race fix"), "D-206")
        self.assertEqual(bt_core.next_id(self.pdir, "D", reserve="stage join"), "D-207")
        self.assertEqual(bt_core.next_id(self.pdir, "D"), "D-208")          # a plain read skips them too
        with open(self.pdir / "DECISIONS.md", "a", encoding="utf-8") as f:
            f.write("\n## D-210 — written past the reservations\n")
        self.assertEqual(bt_core.next_id(self.pdir, "D", reserve="later"), "D-211")

    def test_parallel_reservations_get_distinct_numbers(self):
        import concurrent.futures
        (self.pdir / "DECISIONS.md").write_text("# demo\n\n## D-001 — one\n", encoding="utf-8")
        with concurrent.futures.ThreadPoolExecutor(8) as pool:
            got = list(pool.map(lambda n: bt_core.next_id(self.pdir, "D", reserve=f"caller {n}"), range(16)))
        self.assertEqual(len(set(got)), 16)
        self.assertEqual(sorted(got)[0], "D-002")


if __name__ == "__main__":
    unittest.main()
