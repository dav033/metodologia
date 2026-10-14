"""The PLAN.md grammar the module understands, on its own."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from bt_planner import markdown as md  # noqa: E402

DOC = """---
status: approved (phase 1)
---
# Plan
<!-- - [ ] T9 — example inside a comment · after: T1 -->
## Notes
### M1 — First
- [ ] T1 — Do it · repo: backend · files: src/a.py, tests/** · verify: `pytest -q -k "a · b"` · risk: HIGH
- [x] T2.1: Next · after: T1, T0a, junk · complexity: M · resources: db, queue
### M2 - Second
- [ ] T3a -- Other · files: ../secret
## Appendix
- [ ] T4 — Orphan after a plain heading
"""


class Grammar(unittest.TestCase):
    def setUp(self):
        self.tasks, self.stones = md.parse(DOC)
        self.by_id = {t["id"]: t for t in self.tasks}

    def test_tasks_milestones_and_comments(self):
        self.assertEqual([t["id"] for t in self.tasks], ["T1", "T2.1", "T3a", "T4"])
        self.assertEqual([m["id"] for m in self.stones], ["M1", "M2"])
        self.assertEqual(self.stones[0]["tasks"], ["T1", "T2.1"])
        self.assertEqual([m["title"] for m in self.stones], ["First", "Second"])
        self.assertIsNone(self.by_id["T4"]["milestone"])  # a plain heading ends the milestone
        self.assertNotIn("T9", self.by_id)

    def test_fields(self):
        t1, t2 = self.by_id["T1"], self.by_id["T2.1"]
        self.assertEqual((t1["repo"], t1["files"], t1["risk"]), ("backend", ["src/a.py", "tests/**"], "high"))
        self.assertEqual(t1["verify"], 'pytest -q -k "a · b"')  # a dot inside backticks is not a field separator
        self.assertEqual(t2["after"], ["T1", "T0a"])
        self.assertEqual((t2["complexity"], t2["resources"], t2["done"]), ("m", ["db", "queue"], True))

    def test_unsafe_files_are_dropped_as_a_whole(self):
        self.assertIsNone(self.by_id["T3a"]["files"])

    def test_status_first_word(self):
        self.assertEqual(md.status(DOC), "approved")
        self.assertEqual(md.status("no front matter"), "")
        self.assertEqual(md.status("status:\n"), "")

    def test_unreadable_file_gives_nothing(self):
        self.assertEqual(md.read(Path("/nonexistent/PLAN.md")), ([], []))


if __name__ == "__main__":
    unittest.main()
