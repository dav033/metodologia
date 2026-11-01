"""A new working folder must not stop an unattended Claude account on the «trust this folder» questions."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bt_agent_terminal as terminal


class TrustFolder(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.home = Path(self._tmp.name) / "acct"
        self.home.mkdir()
        self.cwd = Path(self._tmp.name) / "work" / "s1"
        self.cwd.mkdir(parents=True)

    def _settings(self, unattended: bool):
        (self.home / "settings.json").write_text(json.dumps({"skipDangerousModePermissionPrompt": unattended}))

    def _entry(self):
        return json.loads((self.home / ".claude.json").read_text())["projects"][str(self.cwd.resolve())]

    def test_unattended_account_gets_the_folder_accepted_and_other_projects_kept(self):
        self._settings(True)
        (self.home / ".claude.json").write_text(json.dumps({"projects": {"/x": {"hasTrustDialogAccepted": True}}, "k": 1}))
        self.assertTrue(terminal.trust_folder(str(self.home), self.cwd))
        entry = self._entry()
        self.assertTrue(entry["hasTrustDialogAccepted"] and entry["hasClaudeMdExternalIncludesApproved"])
        data = json.loads((self.home / ".claude.json").read_text())
        self.assertEqual((data["k"], data["projects"]["/x"]), (1, {"hasTrustDialogAccepted": True}))
        self.assertFalse(terminal.trust_folder(str(self.home), self.cwd), "already accepted: nothing to write")

    def test_account_that_still_asks_the_owner_keeps_asking(self):
        self._settings(False)
        self.assertFalse(terminal.trust_folder(str(self.home), self.cwd))
        self.assertFalse((self.home / ".claude.json").exists())

    def test_unreadable_record_is_left_alone(self):
        self._settings(True)
        (self.home / ".claude.json").write_text("{not json")
        self.assertFalse(terminal.trust_folder(str(self.home), self.cwd))
        self.assertEqual((self.home / ".claude.json").read_text(), "{not json")

    def test_start_trusts_only_claude_commands(self):
        calls = []
        with patch.object(terminal, "trust_folder", lambda h, c: calls.append((h, str(c)))), \
                patch.object(terminal, "exists", return_value=False), \
                patch.object(terminal, "_run", side_effect=RuntimeError("stop")):
            for command in ("claude --model sonnet 'x'", "codex run"):
                with self.assertRaises(RuntimeError):
                    terminal.start("bit-p-REQ-1-solver", self.cwd, command, {"CLAUDE_CONFIG_DIR": "/h"})
        self.assertEqual(calls, [("/h", str(self.cwd))])


if __name__ == "__main__":
    unittest.main()
