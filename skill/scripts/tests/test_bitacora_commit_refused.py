"""A bitácora commit the repository's pre-commit hook refuses leaves nothing staged and says why (2026-10-29: gitleaks
refused every bitácora commit from 13:46 on a translation-cache false positive; `bitacora.py commit` printed «nothing
to commit», the files stayed staged and a later `git merge` in that checkout reset the live bitácora)."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bt_secrets
import bt_vcs


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout


class RefusedCommit(unittest.TestCase):
    def setUp(self):
        self.repo = Path(tempfile.mkdtemp(prefix="bt-commit-refused-"))
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "config", "user.email", "t@t")
        git(self.repo, "config", "user.name", "T")
        self.root = self.repo / "bitacora"
        self.root.mkdir()
        (self.root / "log.md").write_text("one\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "base")
        self.hook = self.repo / ".git" / "hooks" / "pre-commit"
        patcher = patch.object(bt_secrets, "scan_staged", return_value=(True, ""))
        patcher.start()
        self.addCleanup(patcher.stop)

    def refuse_with(self, text: str) -> None:
        self.hook.write_text(f"#!/bin/sh\necho '{text}'\nexit 1\n")
        self.hook.chmod(0o755)

    def test_a_gitleaks_refusal_unstages_and_leaves_the_alert(self):
        self.refuse_with("WRN leaks found: 1\ngitleaks: posible secreto en este commit")
        (self.root / "log.md").write_text("two\n")
        self.assertFalse(bt_vcs.commit(self.root, "log", push=False))
        self.assertEqual(git(self.repo, "diff", "--cached", "--name-only"), "")
        self.assertEqual((self.root / "log.md").read_text(), "two\n")           # the work stays on disk
        self.assertIn("leaks found: 1", bt_secrets.alert(self.root))
        self.hook.unlink()
        self.assertTrue(bt_vcs.commit(self.root, "log", push=False))
        self.assertEqual(bt_secrets.alert(self.root), "")

    def test_another_refusal_unstages_without_claiming_a_secret(self):
        self.refuse_with("metodologia: este commit mezcla bitacora/ con otros archivos")
        (self.root / "log.md").write_text("three\n")
        self.assertFalse(bt_vcs.commit(self.root, "log", push=False))
        self.assertEqual(git(self.repo, "diff", "--cached", "--name-only"), "")
        self.assertEqual(bt_secrets.alert(self.root), "")


if __name__ == "__main__":
    unittest.main()
