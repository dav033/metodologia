"""PENDING.md normalization: guidance never accumulates in Notes, the example is not a real ID, user notes survive,
and the file is a fixed point of the template."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import bt_pending  # noqa: E402

# A PENDING.md as the old code left it: the guidance lines copied into "## Notes" again and again, and the example
# ID P-012 that the bitácora lint reads as a real (undefined) reference.
LEGACY = """# demo — Pending

_Sorted automatically by `bitacora.py pending` (urgency high → low, then complexity S → L).
One line per item: `P-012 · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`._

## Open
- P-001 · Ship the thing · urgency: high · complexity: S · added 2026-10-13 · session

## Blocked
_None_

## Recently closed
_None_

## Notes
One line per item: `P-012 · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`._
One line per item: `P-012 · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Move items between sections as they change; closed items keep 14 days in "Recently closed", then go to the
month summary._
"""


class PendingNotesTests(unittest.TestCase):
    def test_guidance_is_dropped_and_example_is_not_a_real_id(self):
        out = bt_pending.normalize(LEGACY, "demo")
        self.assertNotIn("## Notes", out)
        self.assertNotIn("P-012", out)
        self.assertIn("P-NNN", out)
        self.assertIn("- P-001 · Ship the thing", out)

    def test_normalize_is_idempotent(self):
        once = bt_pending.normalize(LEGACY, "demo")
        twice = bt_pending.normalize(once, "demo")
        self.assertEqual(once, twice)

    def test_user_notes_that_only_resemble_guidance_are_kept(self):
        notes = ("Owner note: keep the staging URL in TOOLS.md.\n"
                 "One line per item: keep titles under 90 chars, the dashboard truncates them.\n"
                 "Indented lines under an item are not shown in the web dashboard.\n"
                 "Indented lines under an item are its details, so put links there.\n"
                 "Move items between sections only after the owner signs off.\n")
        out = bt_pending.normalize(LEGACY + notes, "demo")
        self.assertIn("## Notes\n" + notes, out)
        self.assertEqual(out.count("One line per item: `P-"), 1)  # the header's own line, never copied into Notes

    def test_closed_items_rule_is_kept_exactly_once(self):
        out = bt_pending.normalize(LEGACY, "demo")
        self.assertEqual(out.count("closed items keep 14 days"), 1)
        self.assertEqual(bt_pending.normalize(out, "demo").count("closed items keep 14 days"), 1)

    def test_closed_items_keep_only_the_metadata_they_had(self):
        bare = "- P-002 · closed 2026-10-10 by abc123: shipped the thing"
        explicit = "- P-003 · Old thing · urgency: med · complexity: S · closed 2026-10-09 · 15c74eb7"
        out = bt_pending.normalize(LEGACY.replace("## Recently closed\n_None_\n",
                                                  f"## Recently closed\n{bare}\n{explicit}\n"), "demo")
        self.assertIn(bare + "\n", out)  # no urgency or complexity invented for a closed item
        self.assertIn(explicit + "\n", out)
        self.assertEqual(bt_pending.normalize(out, "demo"), out)

    def test_template_is_a_fixed_point_of_normalize(self):
        template = (SCRIPTS.parent / "templates" / "PENDING.md").read_text(encoding="utf-8").replace("{{project}}", "demo")
        self.assertEqual(bt_pending.normalize(template, "demo"), template)


if __name__ == "__main__":
    unittest.main()
