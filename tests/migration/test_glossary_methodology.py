"""GLOSSARY.md is an on-demand central document; the methodology references load only on their trigger (T14/T15)."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SKILL = REPO / "skill"
SCRIPT = SKILL / "scripts" / "bitacora.py"
NEW_REFERENCES = ("design-vocabulary", "improve-architecture", "domain-glossary", "glossary-conventions",
                  "test-seams", "diagnosing-bugs", "retro-feedback", "writing-for-agents", "wait-what")


class GlossaryTests(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory(prefix="glossary-")
        self.addCleanup(temp.cleanup)
        self.tmp = Path(temp.name)
        self.env = {"PATH": os.environ["PATH"], "HOME": str(self.tmp), "BITACORA_ROOT": str(self.tmp / "bit"),
                    "PYTHONDONTWRITEBYTECODE": "1"}

    def cli(self, *args: str):
        return subprocess.run([sys.executable, str(SCRIPT), "--project", "demo", *args], capture_output=True,
                              text=True, env=self.env, cwd=self.tmp, timeout=60)

    def test_init_does_not_create_an_empty_glossary_and_the_command_does_once(self) -> None:
        self.assertEqual(self.cli("init").returncode, 0)
        glossary = self.tmp / "bit" / "demo" / "GLOSSARY.md"
        self.assertFalse(glossary.exists())
        index = (self.tmp / "bit" / "demo" / "INDEX.md").read_text()
        self.assertNotIn("GLOSSARY.md", index)
        done = self.cli("glossary")
        self.assertEqual((done.returncode, Path(done.stdout.strip())), (0, glossary), done.stderr)
        self.assertIn("# demo", glossary.read_text())
        glossary.write_text(glossary.read_text() + "\n**Order**: a purchase.\n")
        self.cli("glossary")  # idempotent: never overwrites edits
        self.assertIn("**Order**", glossary.read_text())
        self.assertIn("[Glossary](GLOSSARY.md)", (self.tmp / "bit" / "demo" / "INDEX.md").read_text())


class ReferenceHygieneTests(unittest.TestCase):
    def test_every_new_reference_is_attributed_and_has_a_load_condition(self) -> None:
        for name in NEW_REFERENCES:
            text = (SKILL / "references" / f"{name}.md").read_text(encoding="utf-8")
            with self.subTest(reference=name):
                self.assertRegex(text, r"Source: mattpocock/skills@49dd158 \(MIT\)")
                if name != "glossary-conventions":  # a format file, loaded from domain-glossary.md
                    self.assertRegex(text, r"(?i)load when|cargar cuando|load (this )?(only )?when")

    def test_router_rows_point_to_existing_files_and_notices_name_every_adaptation(self) -> None:
        router = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for target in re.findall(r"`(references/[a-z\-]+\.md)`", router):
            self.assertTrue((SKILL / target).is_file(), target)
        notices = (SKILL / "references" / "third-party-notices.md").read_text(encoding="utf-8")
        for name in NEW_REFERENCES:
            self.assertIn(f"references/{name}.md", notices)
        # 13000 was the budget before the scheduler routing rows; HEAD already measured 13652
        self.assertLess(len(router.encode()), 14000, "the always-on router grew past the recorded budget")

    def test_governance_rules_were_not_replaced(self) -> None:
        engineering = (SKILL / "references" / "engineering.md").read_text(encoding="utf-8")
        requirements = (SKILL / "references" / "requirements.md").read_text(encoding="utf-8")
        for needle in ("No \"done\" without fresh evidence", "TDD for business logic and bugs"):
            self.assertIn(needle, engineering)
        self.assertIn("Grill Me", requirements)
        wait = (SKILL / "references" / "wait-what.md").read_text(encoding="utf-8")
        self.assertRegex(wait, r"(?i)cinco|five|5")

    def test_new_evals_parse_and_name_their_expected_reference(self) -> None:
        cases = sorted((REPO / "evals" / "cases").glob("m6-*.json"))
        self.assertGreaterEqual(len(cases), 4)
        for case in cases:
            json.loads(case.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
