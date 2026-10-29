from __future__ import annotations

import contextlib
import io
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[3]
SKILL_ROOT = REPO / "skill"
AGENTS = SKILL_ROOT / "agents"
SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import install_agents  # noqa: E402


class AgentSkillStaticTests(unittest.TestCase):
    def test_role_and_skill_frontmatter_matches_skill_folder(self):
        role_prompts = sorted(AGENTS.glob("*.md"))
        skill_files = sorted(AGENTS.glob("*/skills/*/SKILL.md"))
        for source in [*role_prompts, *skill_files]:
            expected_name = source.stem if source.parent == AGENTS else source.parent.name
            with self.subTest(path=source.relative_to(REPO)):
                match = re.match(r"^---\n(.*?)\n---\n", source.read_text(encoding="utf-8"), re.S)
                self.assertIsNotNone(match, "missing YAML frontmatter")
                metadata = _frontmatter(match.group(1))
                self.assertEqual(metadata.get("name"), expected_name)
                self.assertTrue(metadata.get("description", "").strip())

    def test_every_role_skill_is_conditionally_referenced_by_its_prompt(self):
        for prompt in sorted(AGENTS.glob("*.md")):
            role = prompt.stem
            metadata, lines, body = install_agents.parse(prompt)
            content = install_agents.generated_claude(metadata, lines, body)
            for skill_file in sorted((AGENTS / role / "skills").glob("*/SKILL.md")):
                relative = skill_file.relative_to(SKILL_ROOT).as_posix()
                with self.subTest(role=role, skill=relative):
                    self.assertIn(relative, content, "prompt must name the private skill path")
                    self.assertIn(relative, body, "source role prompt must name the private skill path")
                    self.assertRegex(body, r"(?i)load[\s\S]*\b(?:when|for|only)\b")
                    self.assertIn("load a skill only when its task condition", content)

    def test_role_and_skill_resource_paths_resolve_from_skill_root(self):
        path_pattern = re.compile(r"(?:agents/[\w.-]+/(?:skills|references)/|references/)[\w./-]+")
        for source in sorted([*AGENTS.glob("*.md"), *AGENTS.glob("**/skills/*/SKILL.md")]):
            content = source.read_text(encoding="utf-8")
            for value in set(path_pattern.findall(content)):
                normalized = value.rstrip(".,;:)")
                role_reference = re.match(r"agents/([\w.-]+)/references/(.*)", normalized)
                if role_reference:
                    role_target = AGENTS / role_reference.group(1) / "references" / role_reference.group(2)
                    target = role_target if role_target.exists() else SKILL_ROOT / normalized
                elif normalized.startswith("references/"):
                    suffix = normalized.removeprefix("references/")
                    role_dir = source.parents[2] if source.name == "SKILL.md" else AGENTS / source.stem
                    candidates = [role_dir / "references" / suffix]
                    target = next((candidate for candidate in candidates if candidate.exists()),
                                  SKILL_ROOT / normalized)
                else:
                    target = SKILL_ROOT / normalized
                with self.subTest(source=source.relative_to(REPO), path=normalized):
                    self.assertTrue(target.exists(), f"unresolvable resource path: {normalized}")

    def test_runner_protocol_and_implementer_exclusions_remain_explicit(self):
        runner = (AGENTS / "runner.md").read_text(encoding="utf-8")
        implementer = (AGENTS / "implementer.md").read_text(encoding="utf-8")
        self.assertIn("STATUS: PASS | FAIL | BLOCKED", runner)
        for excluded in ("systematic-debugging", "verification-before-completion", "receiving-code-review"):
            with self.subTest(excluded=excluded):
                self.assertIn(excluded, implementer)
        self.assertRegex(implementer, r"(?i)do not load.{0,160}systematic-debugging.{0,100}verification-before-completion"
                         r".{0,100}receiving-code-review")

    def test_skills_contain_no_obvious_secret_shapes(self):
        patterns = (
            re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
            re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
            re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
            re.compile(r"\bsk-[A-Za-z0-9_-]{24,}\b"),
        )
        for skill_file in sorted(AGENTS.glob("*/skills/*/SKILL.md")):
            content = skill_file.read_text(encoding="utf-8")
            for pattern in patterns:
                with self.subTest(path=skill_file.relative_to(REPO), pattern=pattern.pattern):
                    self.assertIsNone(pattern.search(content), "possible secret-shaped value")


class InstallerPrivateSkillTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="agent-skills-install-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.resources = self.base / "skill"
        (self.resources / "templates").mkdir(parents=True)
        self.sources = self.resources / "agents"
        self.role = self.sources / "fixture-role"
        (self.role / "skills" / "fixture-skill").mkdir(parents=True)
        (self.sources / "fixture-role.md").write_text(
            "---\nname: fixture-role\ndescription: fixture role\ntools: Read\n---\nLoad when needed.\n",
            encoding="utf-8")
        (self.role / "skills" / "fixture-skill" / "SKILL.md").write_text(
            "---\nname: fixture-skill\ndescription: fixture private skill\n---\nSkill body.\n", encoding="utf-8")
        self.claude = self.base / "claude" / "agents"
        self.codex = self.base / "codex" / "agents"
        self.antigravity = self.base / "antigravity" / "agents"

    def run_installer(self, *args):
        output = io.StringIO()
        errors = io.StringIO()
        with patch.object(install_agents, "SRC", self.sources), \
                patch.object(install_agents, "resource_root", return_value=self.resources), \
                patch.object(sys, "argv", ["install_agents.py", "--agent", "fixture-role", "--claude-dir",
                                            str(self.claude), "--codex-dir", str(self.codex),
                                            "--antigravity-dir", str(self.antigravity), *args]), \
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            install_agents.main()
        return output.getvalue(), errors.getvalue()

    def test_fixture_role_skills_are_addressable_for_all_providers(self):
        self.run_installer()
        claude = (self.claude / "fixture-role.md").read_text(encoding="utf-8")
        codex = (self.codex / "fixture-role.toml").read_text(encoding="utf-8")
        antigravity = (self.antigravity / "fixture-role" / "agent.md").read_text(encoding="utf-8")
        self.assertIn(str(self.resources.resolve()), claude)
        self.assertIn(str(self.resources.resolve()), codex)
        self.assertIn("SKILL_UNAVAILABLE", claude)
        self.assertIn("SKILL_UNAVAILABLE", codex)
        self.assertIn(str(self.resources.resolve()), antigravity)
        self.assertIn("SKILL_UNAVAILABLE", antigravity)
        self.assertTrue((self.antigravity / "fixture-role" / "skills" / "fixture-skill" / "SKILL.md").is_file())
        self.assertIn('"skills/fixture-skill"', antigravity)

    def test_hand_authored_agent_and_skill_paths_are_skipped_with_messages(self):
        self.claude.mkdir(parents=True)
        hand_agent = self.claude / "fixture-role.md"
        hand_agent.write_text("my agent", encoding="utf-8")
        skill_target = self.antigravity / "fixture-role" / "skills" / "fixture-skill" / "SKILL.md"
        skill_target.parent.mkdir(parents=True)
        skill_target.write_text("my skill", encoding="utf-8")
        _out, errors = self.run_installer()
        self.assertIn(str(hand_agent), errors)
        self.assertIn(str(skill_target), errors)
        self.assertEqual(hand_agent.read_text(encoding="utf-8"), "my agent")
        self.assertEqual(skill_target.read_text(encoding="utf-8"), "my skill")

    def test_force_keeps_overwrite_behavior_for_agent_and_skill_paths(self):
        self.claude.mkdir(parents=True)
        (self.claude / "fixture-role.md").write_text("my agent", encoding="utf-8")
        skill_target = self.antigravity / "fixture-role" / "skills" / "fixture-skill" / "SKILL.md"
        skill_target.parent.mkdir(parents=True)
        skill_target.write_text("my skill", encoding="utf-8")
        self.run_installer("--force")
        self.assertIn(install_agents.MARKER, (self.claude / "fixture-role.md").read_text(encoding="utf-8"))
        self.assertIn(install_agents.MARKER, skill_target.read_text(encoding="utf-8"))

    def test_designer_installs_in_default_claude_codex_run_and_selected_antigravity_run(self):
        real_claude = self.base / "real-claude" / "agents"
        real_codex = self.base / "real-codex" / "agents"
        real_antigravity = self.base / "real-antigravity" / "agents"

        def invoke(*args):
            argv = ["install_agents.py", "--claude-dir", str(real_claude), "--codex-dir", str(real_codex),
                    "--antigravity-dir", str(real_antigravity), *args]
            with patch.object(sys, "argv", argv):
                install_agents.main()

        with patch.object(install_agents, "SRC", AGENTS):
            invoke()
            self.assertTrue((real_claude / "designer.md").is_file())
            self.assertTrue((real_codex / "designer.toml").is_file())
            self.assertIn('model = "gpt-6.1-terra"',
                          (real_codex / "designer.toml").read_text(encoding="utf-8"))
            self.assertEqual(len(list(real_claude.glob("*.md"))), 8)
            self.assertTrue((real_antigravity / "planner" / "agent.md").is_file())
            self.assertFalse((real_antigravity / "designer" / "agent.md").exists())
            invoke("--agent", "designer")
        self.assertTrue((real_claude / "designer.md").is_file())
        self.assertTrue((real_codex / "designer.toml").is_file())
        self.assertTrue((real_antigravity / "designer" / "agent.md").is_file())
        self.assertTrue((real_antigravity / "designer" / "skills" / "ui-ux-contract-authoring" /
                         "SKILL.md").is_file())


def _frontmatter(content: str) -> dict[str, str]:
    result = {}
    for line in content.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip().strip("\"'")
    return result


if __name__ == "__main__":
    unittest.main()
