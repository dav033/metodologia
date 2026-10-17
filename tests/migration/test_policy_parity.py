"""No instruction disappears unnoticed (REQ-007 T14, gate G10).

Compares the working tree with the committed baseline (`git show HEAD:...`): every router row and every heading of
every committed reference must still exist unless the removal is listed here with its reason. Skipped (not passed)
without git or without a baseline.
"""
from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SKILL = REPO / "skill"

# Reviewed removals/renames: "<path>#<heading or row prefix>" -> reason.
ALLOWED_REMOVALS: dict[str, str] = {
    "skill/references/subagents.md### The five roles":
        "D-055 adds Planner to the six existing helper roles; the heading now names all seven roles.",
}


def head(path: str) -> str | None:
    done = subprocess.run(["git", "-C", str(REPO), "show", f"HEAD:{path}"], capture_output=True, text=True)
    return done.stdout if done.returncode == 0 else None


def tracked(prefix: str) -> list[str]:
    done = subprocess.run(["git", "-C", str(REPO), "ls-tree", "-r", "--name-only", "HEAD", prefix],
                          capture_output=True, text=True)
    return [line for line in done.stdout.splitlines() if line.endswith(".md")] if done.returncode == 0 else []


class PolicyParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True).returncode != 0:
            raise unittest.SkipTest("no git baseline")

    def test_router_rows_of_the_baseline_are_all_still_present(self) -> None:
        old = head("skill/SKILL.md") or ""
        new = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        rows = [line for line in old.splitlines() if line.startswith("| ") and "`references/" in line]
        self.assertGreater(len(rows), 8)
        missing = [row for row in rows if row not in new and f"SKILL.md#{row[:40]}" not in ALLOWED_REMOVALS]
        self.assertEqual(missing, [], "router rows removed or edited; list reviewed changes in ALLOWED_REMOVALS")

    def test_headings_of_every_baseline_reference_still_exist(self) -> None:
        problems = []
        for path in tracked("skill/references"):
            old = head(path) or ""
            current_path = REPO / path
            if not current_path.exists():
                problems.append(f"{path}: file removed")
                continue
            new = current_path.read_text(encoding="utf-8")
            old_headings = {re.sub(r"\s+", " ", m.group(0)).strip() for m in re.finditer(r"^#{1,4} .+$", old, re.M)}
            new_headings = {re.sub(r"\s+", " ", m.group(0)).strip() for m in re.finditer(r"^#{1,4} .+$", new, re.M)}
            for heading in sorted(old_headings - new_headings):
                if f"{path}#{heading}" not in ALLOWED_REMOVALS:
                    problems.append(f"{path}: heading removed or renamed: {heading}")
        self.assertEqual(problems, [])

    def test_the_six_agent_roles_and_skill_front_matter_are_unchanged(self) -> None:
        for path in tracked("skill/agents"):
            self.assertTrue((REPO / path).exists(), path)
        old = head("skill/SKILL.md") or ""
        new = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for text in (old, new):
            self.assertTrue(text.startswith("---\n"))
        old_name = re.search(r"^name:\s*(.+)$", old, re.M).group(1)
        self.assertEqual(re.search(r"^name:\s*(.+)$", new, re.M).group(1), old_name)

    def test_always_on_router_growth_is_recorded_and_bounded(self) -> None:
        old = len((head("skill/SKILL.md") or "").encode())
        new = len((SKILL / "SKILL.md").read_bytes())
        self.assertLess(new - old, 2500, f"always-on SKILL.md grew by {new - old} bytes; justify or move content")

    def test_new_references_do_not_contradict_governance_anchors(self) -> None:
        anchors = {"engineering.md": ["No \"done\" without fresh evidence"],
                   "requirements.md": ["Grill Me"],
                   "subagents.md": ["explorer"]}
        for name, needles in anchors.items():
            text = (SKILL / "references" / name).read_text(encoding="utf-8")
            for needle in needles:
                self.assertIn(needle, text, f"{name} lost governance anchor {needle!r}")


if __name__ == "__main__":
    unittest.main()
