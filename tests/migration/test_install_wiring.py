"""install.py steps 1-3 run through the transaction layer (REQ-007 T9 wiring, gate G5): dry run, idempotence,
foreign/relay hooks preserved, rollback. Everything happens in a throwaway HOME."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


class InstallWiringTests(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory(prefix="install-wiring-")
        self.addCleanup(temp.cleanup)
        self.home = Path(temp.name) / "home with space"
        (self.home / ".claude").mkdir(parents=True)
        (self.home / ".codex").mkdir(parents=True)
        self.env = {"PATH": os.environ["PATH"], "HOME": str(self.home), "BITACORA_ROOT": str(self.home / "bit"),
                    "PYTHONDONTWRITEBYTECODE": "1"}
        self.foreign = {"type": "command", "command": "node /opt/other-tool/hook.js", "timeout": 5}
        self.relay = {"type": "command",
                      "command": "python3 /somewhere/metodologia/skill/scripts/bitacora.py hook relay"}
        (self.home / ".claude" / "settings.json").write_text(json.dumps({
            "theme": "dark", "unknownKey": {"keep": [1, None]},
            "hooks": {"Stop": [{"hooks": [self.foreign]}, {"hooks": [self.relay]}]}}))

    def install(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(REPO / "install.py"), *args], capture_output=True, text=True,
                              env=self.env, cwd=self.home, timeout=120)

    def settings(self) -> dict:
        return json.loads((self.home / ".claude" / "settings.json").read_text())

    def test_dry_run_writes_nothing(self) -> None:
        before = (self.home / ".claude" / "settings.json").read_bytes()
        done = self.install("--dry-run")
        self.assertEqual(done.returncode, 0, done.stderr)
        report = json.loads(done.stdout[done.stdout.index("{"):])
        self.assertTrue(report["changed"])
        self.assertEqual((self.home / ".claude" / "settings.json").read_bytes(), before)
        self.assertFalse((self.home / ".claude" / "skills").exists())
        self.assertFalse((self.home / ".local").exists())

    def test_apply_is_idempotent_and_keeps_foreign_and_relay_hooks(self) -> None:
        first = self.install("--core-only")
        self.assertEqual(first.returncode, 0, first.stderr + first.stdout)
        once = (self.home / ".claude" / "settings.json").read_bytes()
        second = self.install("--core-only")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual((self.home / ".claude" / "settings.json").read_bytes(), once)
        data = self.settings()
        self.assertEqual(data["theme"], "dark")
        self.assertEqual(data["unknownKey"], {"keep": [1, None]})
        commands = [h["command"] for g in data["hooks"]["Stop"] for h in g["hooks"]]
        self.assertIn(self.foreign["command"], commands)
        self.assertIn(self.relay["command"], commands)
        self.assertEqual(sum("/skills/metodologia/scripts/" in c and " hook stop" in c for c in commands), 1)
        self.assertTrue((self.home / ".claude" / "skills" / "metodologia").is_symlink())

    def test_rollback_restores_the_preimage_and_refuses_foreign_edits(self) -> None:
        settings = self.home / ".claude" / "settings.json"
        original = settings.read_bytes()
        self.install("--core-only")
        journals = sorted((self.home / ".local" / "share" / "metodologia-migration" / "installs").glob("*/journal.jsonl"))
        self.assertTrue(journals)
        undone = self.install("--rollback", str(journals[-1]))
        self.assertEqual(undone.returncode, 0, undone.stderr)
        self.assertEqual(settings.read_bytes(), original)
        self.assertFalse((self.home / ".claude" / "skills" / "metodologia").exists())
        # a file edited by someone else after the install is reported, not overwritten
        self.install("--core-only")
        journals = sorted((self.home / ".local" / "share" / "metodologia-migration" / "installs").glob("*/journal.jsonl"))
        data = self.settings()
        data["editedLater"] = True
        settings.write_text(json.dumps(data))
        report = json.loads(self.install("--rollback", str(journals[-1])).stdout)
        self.assertIn("editedLater", settings.read_text())
        self.assertTrue(json.dumps(report).lower().count("conflict") >= 1)

    def test_real_folder_in_place_of_the_link_aborts_without_changes(self) -> None:
        blocker = self.home / ".claude" / "skills" / "metodologia"
        blocker.mkdir(parents=True)
        (blocker / "mine.txt").write_text("keep")
        before = (self.home / ".claude" / "settings.json").read_bytes()
        done = self.install("--core-only")
        self.assertNotEqual(done.returncode, 0)
        self.assertEqual((blocker / "mine.txt").read_text(), "keep")
        self.assertEqual((self.home / ".claude" / "settings.json").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
