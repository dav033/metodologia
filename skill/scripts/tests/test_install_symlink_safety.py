from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))
import install_agents  # noqa: E402


class InstallerSymlinkSafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="install-symlink-test-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.sources = self.base / "source" / "agents"
        self.resources = self.base / "resources"
        self.sources.mkdir(parents=True)
        self.resources.mkdir()
        self.agent = self.sources / "fixture-role.md"
        self.agent.write_text("---\nname: fixture-role\ndescription: fixture\ntools: Read\n---\nbody\n",
                             encoding="utf-8")
        self.skill = self.sources / "fixture-role" / "skills" / "fixture-skill" / "SKILL.md"
        self.skill.parent.mkdir(parents=True)
        self.skill.write_text("---\nname: fixture-skill\n---\nskill\n", encoding="utf-8")
        self.claude = self.base / "claude" / "agents"
        self.codex = self.base / "codex" / "agents"
        self.antigravity = self.base / "antigravity" / "agents"

    def run_install(self, *args: str) -> str:
        output = io.StringIO()
        with patch.object(install_agents, "SRC", self.sources), \
                patch.object(install_agents, "resource_root", return_value=self.resources), \
                patch.object(sys, "argv", ["install_agents.py", "--agent", "fixture-role",
                                            "--claude-dir", str(self.claude), "--codex-dir", str(self.codex),
                                            "--antigravity-dir", str(self.antigravity), *args]), \
                contextlib.redirect_stderr(output):
            install_agents.main()
        return output.getvalue()

    def test_antigravity_marked_external_leaf_symlink_is_refused_even_with_force(self):
        for force in (False, True):
            with self.subTest(force=force):
                target = self.antigravity / "fixture-role" / "skills" / "fixture-skill" / "SKILL.md"
                external = self.base / f"external-{force}.md"
                external.write_text(f"<!-- {install_agents.MARKER} -->\nkeep\n", encoding="utf-8")
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.is_symlink():
                    target.unlink()
                target.symlink_to(external)
                errors = self.run_install("--only", "antigravity", *( ["--force"] if force else []))
                self.assertEqual(external.read_text(encoding="utf-8"),
                                 f"<!-- {install_agents.MARKER} -->\nkeep\n")
                self.assertIn(str(target), errors)
                self.assertTrue("symlink" in errors.lower() or "link" in errors.lower())
                target.unlink()

    def test_dangling_antigravity_leaf_symlink_creates_nothing_outside(self):
        target = self.antigravity / "fixture-role" / "skills" / "fixture-skill" / "SKILL.md"
        outside = self.base / "missing" / "created.md"
        target.parent.mkdir(parents=True)
        target.symlink_to(outside)
        errors = self.run_install("--only", "antigravity", "--force")
        self.assertFalse(outside.exists())
        self.assertIn(str(target), errors)

    def test_antigravity_agent_leaf_symlink_is_refused(self):
        target = self.antigravity / "fixture-role" / "agent.md"
        external = self.base / "external-agent.md"
        external.write_text(f"<!-- {install_agents.MARKER} -->\nkeep\n", encoding="utf-8")
        target.parent.mkdir(parents=True)
        target.symlink_to(external)
        errors = self.run_install("--only", "antigravity", "--force")
        self.assertEqual(external.read_text(encoding="utf-8"), f"<!-- {install_agents.MARKER} -->\nkeep\n")
        self.assertIn(str(target), errors)

    @unittest.skipUnless(hasattr(install_agents.os, "O_NOFOLLOW"), "requires POSIX O_NOFOLLOW")
    def test_leaf_symlink_created_after_validation_is_not_followed(self):
        target = self.claude / "agent.md"
        external = self.base / "external-race.md"
        external.write_text("keep\n", encoding="utf-8")
        original_open = install_agents.os.open

        def link_before_open(path, flags, mode=0o777):
            Path(path).symlink_to(external)
            return original_open(path, flags, mode)

        with patch.object(install_agents.os, "open", side_effect=link_before_open):
            problem = install_agents.write_text_safely(self.claude, target, "overwrite\n")
        self.assertIsNotNone(problem)
        self.assertTrue(target.is_symlink())
        self.assertEqual(external.read_text(encoding="utf-8"), "keep\n")

    def test_refused_claude_role_does_not_block_other_roles(self):
        other = self.sources / "other-role.md"
        other.write_text("---\nname: other-role\ndescription: other\n---\nbody\n", encoding="utf-8")
        external = self.base / "external-role.md"
        external.write_text(f"<!-- {install_agents.MARKER} -->\nkeep\n", encoding="utf-8")
        blocked = self.claude / "fixture-role.md"
        blocked.parent.mkdir(parents=True)
        blocked.symlink_to(external)
        errors = io.StringIO()
        with patch.object(install_agents, "SRC", self.sources), \
                patch.object(install_agents, "resource_root", return_value=self.resources), \
                patch.object(sys, "argv", ["install_agents.py", "--only", "claude", "--claude-dir",
                                            str(self.claude)]), \
                contextlib.redirect_stderr(errors):
            install_agents.main()
        self.assertTrue((self.claude / "other-role.md").is_file())
        self.assertEqual(external.read_text(encoding="utf-8"), f"<!-- {install_agents.MARKER} -->\nkeep\n")
        self.assertIn(str(blocked), errors.getvalue())

    def test_symlinked_skill_ancestor_is_refused(self):
        external = self.base / "external-skills"
        external.mkdir()
        target = self.antigravity / "fixture-role" / "skills"
        target.parent.mkdir(parents=True)
        target.symlink_to(external, target_is_directory=True)
        errors = self.run_install("--only", "antigravity", "--force")
        self.assertFalse((external / "fixture-skill" / "SKILL.md").exists())
        self.assertIn(str(target), errors)

    def test_symlinked_skill_name_ancestor_is_refused(self):
        external = self.base / "external-skill"
        external.mkdir()
        skills = self.antigravity / "fixture-role" / "skills"
        skills.mkdir(parents=True)
        linked = skills / "fixture-skill"
        linked.symlink_to(external, target_is_directory=True)
        errors = self.run_install("--only", "antigravity", "--force")
        self.assertFalse((external / "SKILL.md").exists())
        self.assertIn(str(linked), errors)

    def test_claude_and_codex_role_leaf_symlinks_are_refused_even_with_force(self):
        for directory, suffix in ((self.claude, ".md"), (self.codex, ".toml")):
            target = directory / f"fixture-role{suffix}"
            external = self.base / f"external{suffix}"
            external.write_text(f"# {install_agents.MARKER}\nkeep\n", encoding="utf-8")
            target.parent.mkdir(parents=True)
            target.symlink_to(external)
            errors = self.run_install("--only", "claude" if suffix == ".md" else "codex", "--force")
            self.assertEqual(external.read_text(encoding="utf-8"), f"# {install_agents.MARKER}\nkeep\n")
            self.assertIn(str(target), errors)

    def test_configured_top_level_agent_directory_alias_still_installs(self):
        actual = self.base / "actual-agents"
        actual.mkdir()
        alias = self.base / "agents-alias"
        alias.symlink_to(actual, target_is_directory=True)
        errors = io.StringIO()
        with patch.object(install_agents, "SRC", self.sources), \
                patch.object(install_agents, "resource_root", return_value=self.resources), \
                patch.object(sys, "argv", ["install_agents.py", "--agent", "fixture-role", "--only", "claude",
                                            "--claude-dir", str(alias)]), \
                contextlib.redirect_stderr(errors):
            install_agents.main()
        self.assertTrue((actual / "fixture-role.md").is_file())
        self.assertEqual(errors.getvalue(), "")

    def test_planner_methodology_link_is_created_and_wrong_target_is_refused(self):
        planner = self.sources / "planner.md"
        planner.write_text("---\nname: planner\ndescription: planner\ntools: Read\n---\nbody\n",
                           encoding="utf-8")
        (self.sources / "planner" / "skills" / "fixture-skill").mkdir(parents=True)
        (self.sources / "planner" / "skills" / "fixture-skill" / "SKILL.md").write_text(
            "---\nname: fixture-skill\n---\nskill\n", encoding="utf-8")
        with patch.object(install_agents, "SRC", self.sources), \
                patch.object(install_agents, "resource_root", return_value=self.resources), \
                patch.object(sys, "argv", ["install_agents.py", "--only", "antigravity", "--agent", "planner",
                                            "--antigravity-dir", str(self.antigravity)]):
            install_agents.main()
        methodology = self.antigravity / "planner" / "skills" / "metodologia"
        self.assertTrue(methodology.is_symlink())
        self.assertEqual(methodology.resolve(), self.resources.resolve())

        wrong = self.base / "wrong-methodology"
        wrong.mkdir()
        methodology.unlink()
        methodology.symlink_to(wrong, target_is_directory=True)
        errors = io.StringIO()
        with patch.object(install_agents, "SRC", self.sources), \
                patch.object(install_agents, "resource_root", return_value=self.resources), \
                patch.object(sys, "argv", ["install_agents.py", "--only", "antigravity", "--agent", "planner",
                                            "--antigravity-dir", str(self.antigravity), "--force"]), \
                contextlib.redirect_stderr(errors):
            install_agents.main()
        self.assertEqual(methodology.resolve(), wrong.resolve())
        self.assertIn(str(methodology), errors.getvalue())


if __name__ == "__main__":
    unittest.main()
