"""Installer targets: every account's config dir gets the skill; platform sleep inhibitors."""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parent.parent
REPO = SCRIPTS.parent.parent
sys.path.insert(0, str(SCRIPTS))

# Do not import bt_core (directly or via bt_profiles/bt_runutil) in this module: it freezes ROOT at import time and
# this file runs before the marathon tests, which then would write projects into the real ~/bitacora.
import bt_platform  # noqa: E402


def load_installer():
    spec = importlib.util.spec_from_file_location("metodologia_install", REPO / "install.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class InstallerTargetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="install-test-")
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.install = load_installer()
        for name in ("HOME", "CLAUDE_HOME", "CODEX_HOME"):
            patcher = patch.object(self.install, name, self.home / {"HOME": "", "CLAUDE_HOME": ".claude",
                                                                    "CODEX_HOME": ".codex"}[name])
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_account_dirs_include_existing_profile_dirs_once(self):
        (self.home / ".claude-work").mkdir()
        profiles = {"a": {"env": {"CLAUDE_CONFIG_DIR": str(self.home / ".claude-work")}},
                    "b": {"env": {"CLAUDE_CONFIG_DIR": str(self.home / ".claude-work")}},
                    "c": {"env": {"CODEX_HOME": str(self.home / ".codex-missing")}},
                    "d": {"env": {}}}
        fake = types.ModuleType("bt_profiles")
        fake.load = lambda: profiles
        with patch.dict(sys.modules, {"bt_profiles": fake}):
            claude, codex = self.install.account_dirs()
        self.assertEqual(claude, [self.home / ".claude", self.home / ".claude-work"])
        self.assertEqual(codex, [self.home / ".codex"])

    def test_tilde_form_for_imports(self):
        self.assertEqual(self.install.tilde(self.home / ".claude-work"), "~/.claude-work")
        self.assertTrue(self.install.tilde(Path("/elsewhere/x")).startswith("/"))

    def test_live_bitacora_root_is_never_linked_into_the_repo(self):
        source = (REPO / "install.py").read_text(encoding="utf-8")
        self.assertNotIn('REPO / "bitacora")', source)


class SleepInhibitorTests(unittest.TestCase):
    def test_each_host_gets_a_self_releasing_inhibitor(self):
        with patch("bt_platform.shutil.which", side_effect=lambda n: f"/usr/bin/{n}"):
            mac = bt_platform.sleep_inhibitor_argv("darwin", 42)
            linux = bt_platform.sleep_inhibitor_argv("linux", 42)
        self.assertEqual(mac, ["caffeinate", "-i", "-w", "42"])
        self.assertEqual(linux[0], "systemd-inhibit")
        self.assertIn("--pid=42", linux)
        with patch("bt_platform.shutil.which", return_value=None):
            self.assertIsNone(bt_platform.sleep_inhibitor_argv("linux", 42))
            self.assertIsNone(bt_platform.sleep_inhibitor_argv("darwin", 42))
        self.assertIsNone(bt_platform.sleep_inhibitor_argv("freebsd", 42))


if __name__ == "__main__":
    unittest.main()
