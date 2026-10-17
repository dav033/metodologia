from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
AGENTS = REPO / "skill" / "agents"
PROFILE = AGENTS / "planner.md"
PRIVATE_SKILLS = {
    "agents/planner/skills/socratic-elicitation/SKILL.md",
    "agents/planner/skills/wbs-dag-decomposition/SKILL.md",
    "agents/planner/skills/plan-mermaid-view/SKILL.md",
    "agents/planner/skills/adversarial-plan-review/SKILL.md",
}


class PlannerProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = PROFILE.read_text(encoding="utf-8")
        self.skills = {
            name: (AGENTS / name.removeprefix("agents/")).read_text(encoding="utf-8")
            for name in PRIVATE_SKILLS
        }

    def test_profile_references_exactly_its_four_private_skills(self):
        references = set(re.findall(r"`(agents/planner/skills/[^`]+)`", self.profile))
        self.assertEqual(references, PRIVATE_SKILLS)

        for path in AGENTS.rglob("*.md"):
            if path == PROFILE or "/planner/skills/" in path.as_posix():
                continue
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("agents/planner/skills/", text, str(path))

    def test_caller_owns_service_and_route_choices(self):
        self.assertIn("caller or launcher supplies the service, account, model and effort", self.profile)
        for choice in ("provider/service", "account", "model", "effort", "worker count", "quota"):
            self.assertIn(choice, self.profile)
        self.assertIn("Never choose or rank", self.profile)
        self.assertNotRegex(self.profile, r"(?im)^\s*(?:provider|service|account|model|effort):\s+\S+")

    def test_profile_names_schema_1_2_fields_and_history_command(self):
        for expected in (
            "schema 1.2.0", "`covers`", "`interfaces`", "`kind`", "`category`",
            "plan-json history --kind <kind>",
        ):
            self.assertIn(expected, self.profile)

    def test_review_findings_use_required_categories_and_provenance(self):
        review = self.skills["agents/planner/skills/adversarial-plan-review/SKILL.md"]
        for label in ("demonstrated defect", "plausible risk", "fact", "product decision", "provenance"):
            self.assertIn(label, review)
        for source in ("file/line", "decision ID", "reproducible behavior", "triggering condition"):
            self.assertIn(source, review)

    def test_private_skills_preserve_the_planners_routing_boundary(self):
        content = "\n".join(self.skills.values())
        for choice in ("providers", "accounts", "models", "effort", "quota", "worker count"):
            self.assertIn(choice, content)
        for boundary in ("Never choose", "does not choose", "Do not annotate", "Flag any Planner output"):
            self.assertIn(boundary, content)


if __name__ == "__main__":
    unittest.main()
