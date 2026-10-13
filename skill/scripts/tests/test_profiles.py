"""Account profiles: the work gate, environment overlay and launcher/supervisor enforcement."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import bt_profiles  # noqa: E402


class ProfileGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="profiles-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "bitacora"
        for name, data in (("pictures", {"work": True}), ("personal", {"work": False}), ("untagged", {})):
            (self.root / name).mkdir(parents=True)
            (self.root / name / "project.json").write_text(json.dumps(data))
        (self.root / "noproject").mkdir()
        for target in ("bt_profiles.ROOT", "bt_profiles.STATE"):
            patcher = patch(target, self.root if target.endswith("ROOT") else self.root / ".state")
            patcher.start()
            self.addCleanup(patcher.stop)
        # machine-local accounts: the built-ins are generic, named accounts come from .state/profiles.json
        bt_profiles.add("claude-personal", "claude")
        bt_profiles.add("claude-work", "claude", {"CLAUDE_CONFIG_DIR": "~/.claude-work"}, work_only=True)
        bt_profiles.add("codex-1", "codex")
        bt_profiles.add("codex-luis", "codex", {"CODEX_HOME": "~/.codex-luis"})

    def test_claude_work_only_runs_projects_marked_work(self):
        bt_profiles.authorize("claude-work", "pictures")
        for project in ("personal", "untagged", "noproject", "missing"):
            with self.subTest(project=project), self.assertRaises(SystemExit) as ctx:
                bt_profiles.authorize("claude-work", project)
            self.assertIn("restricted to work projects", str(ctx.exception))

    def test_every_other_profile_runs_any_project(self):
        for pid in ("claude-personal", "codex-1", "codex-luis", "claude", "codex", "antigravity"):
            for project in ("pictures", "personal", "untagged", "noproject"):
                bt_profiles.authorize(pid, project)

    def test_no_profile_is_never_gated(self):
        bt_profiles.authorize(None, "personal")

    def test_unknown_profile_is_rejected(self):
        with self.assertRaises(SystemExit):
            bt_profiles.authorize("claude-nope", "pictures")

    def test_work_flag_roundtrip_keeps_other_fields(self):
        path = self.root / "personal" / "project.json"
        path.write_text(json.dumps({"root": "~/dev/x", "work": False}))
        bt_profiles.set_work("personal", True)
        self.assertTrue(bt_profiles.is_work_project("personal"))
        self.assertEqual(json.loads(path.read_text())["root"], "~/dev/x")

    def test_environment_overlay_selects_the_account_without_secrets(self):
        env = bt_profiles.env_of("claude-work")
        self.assertTrue(env["CLAUDE_CONFIG_DIR"].endswith("/.claude-work"))
        self.assertEqual(bt_profiles.env_of(None), {})
        self.assertTrue(bt_profiles.env_of("codex-luis")["CODEX_HOME"].endswith("/.codex-luis"))

    def test_local_file_overrides_and_adds_profiles(self):
        bt_profiles.add("codex-luis", "codex", {"CODEX_HOME": "~/.codex-luis"}, work_only=True)
        bt_profiles.add("extra", "claude")
        with self.assertRaises(SystemExit):
            bt_profiles.authorize("codex-luis", "personal")
        self.assertEqual(bt_profiles.provider_of("extra"), "claude")

    def test_builtins_are_machine_independent(self):
        self.assertEqual(set(bt_profiles.DEFAULTS), {"claude", "codex", "antigravity"})
        self.assertTrue(all(not spec["work_only"] and not spec["env"] for spec in bt_profiles.DEFAULTS.values()))
        with self.assertRaises(SystemExit):
            bt_profiles.add("x", "gemini")

    def test_antigravity_is_registered_but_not_launchable_yet(self):
        with self.assertRaises(SystemExit):
            bt_profiles.require_launchable("antigravity")
        self.assertEqual(bt_profiles.require_launchable("codex-luis"), "codex")


if __name__ == "__main__":
    unittest.main()
