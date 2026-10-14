"""Cutover rehearsal against representative restored state (REQ-007 T18, gates G3 and G12).

The M0 preservation backup holds the real tree and state as they were before the migration. Two independent copies
are restored into temp roots; the OLD runtime (the captured source) and the NEW runtime (this checkout) are run
against their own copy, outputs are compared after normalizing paths and clocks, then the new runtime writes and the
old one must still read the result (backward readability), and a runtime switch-back keeps the newer records.
Skipped, not passed, when the private backup is not present on this machine.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "skill" / "scripts"))

import migration_inventory as inventory  # noqa: E402

BACKUP = Path(os.environ.get("METODOLOGIA_M0_BACKUP",
                             Path.home() / ".local/share/metodologia-migration/baseline-m0-01"))
NEW_SCRIPT = REPO / "skill" / "scripts" / "bitacora.py"


@unittest.skipUnless((BACKUP / "manifest.json").exists(), "M0 preservation backup not on this machine")
class CutoverRehearsalTests(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory(prefix="cutover-")
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        for label in ("old", "new"):  # two independent restores of the same preserved state
            target = self.base / label
            inventory.restore(BACKUP, target)
            root = target / "source" / "bitacora"
            shutil.rmtree(root / ".state", ignore_errors=True)
            shutil.copytree(target / "state", root / ".state", symlinks=True)
        self.old_script = self.base / "old" / "source" / "skill" / "scripts" / "bitacora.py"
        self.roots = {label: self.base / label / "source" / "bitacora" for label in ("old", "new")}

    def run_cli(self, which: str, *args: str, project: str | None = "metodologia", root: str | None = None):
        """`which` picks the runtime (old/new code); `root` picks whose restored state it works on (default: its own)."""
        script = self.old_script if which == "old" else NEW_SCRIPT
        env = {"PATH": os.environ["PATH"], "HOME": str(self.base / f"home-{which}"),
               "BITACORA_ROOT": str(self.roots[root or which]), "PYTHONDONTWRITEBYTECODE": "1"}
        Path(env["HOME"]).mkdir(exist_ok=True)
        command = [sys.executable, str(script)] + (["--project", project] if project else []) + list(args)
        return subprocess.run(command, capture_output=True, text=True, env=env, cwd=self.base, timeout=180)

    def normalize(self, text: str, which: str) -> str:
        text = text.replace(str(self.base / which), "<RESTORED>").replace(str(REPO), "<REPO>")
        text = re.sub(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2})?", "<TS>", text)
        text = re.sub(r"\b1[78]\d{8}(\.\d+)?\b", "<EPOCH>", text)
        return text

    def test_restored_state_has_the_expected_shape(self) -> None:
        state = self.roots["new"] / ".state"
        self.assertTrue(state.is_dir())
        self.assertTrue((self.roots["new"] / "metodologia" / "DECISIONS.md").is_file())
        self.assertTrue((self.roots["new"] / "metodologia" / "requirements").is_dir())

    def test_old_and_new_runtimes_read_the_same_state_identically(self) -> None:
        for args in (("trace",), ("pending", "--help"), ("learn", "list"), ("id", "D"), ("id", "P"),
                     ("config", "get", "audit.provider")):
            with self.subTest(args=args):
                old, new = self.run_cli("old", *args), self.run_cli("new", *args)
                self.assertEqual(old.returncode, new.returncode, (old.stderr[-300:], new.stderr[-300:]))
                self.assertEqual(self.normalize(old.stdout, "old"), self.normalize(new.stdout, "new"))

    def test_new_writes_remain_readable_by_the_old_runtime_and_survive_switch_back(self) -> None:
        added = self.run_cli("new", "learn", "add", "cutover rehearsal marker learning",
                             "--evidence", "written by the new runtime during the rehearsal", root="new")
        self.assertEqual(added.returncode, 0, added.stderr)
        listed_old = self.run_cli("old", "learn", "list", root="new")  # old code, state the new code wrote
        self.assertEqual(listed_old.returncode, 0, listed_old.stderr)
        self.assertIn("cutover rehearsal marker learning", listed_old.stdout)
        # switch back to the old runtime as the writer, then read with the new one: nothing newer was lost
        again = self.run_cli("old", "learn", "add", "second marker written by the old runtime",
                             "--evidence", "rollback rehearsal", root="new")
        self.assertEqual(again.returncode, 0, again.stderr)
        listed_new = self.run_cli("new", "learn", "list", root="new").stdout
        self.assertIn("cutover rehearsal marker learning", listed_new)
        self.assertIn("second marker written by the old runtime", listed_new)

    def test_ids_never_go_down_across_the_runtime_switch(self) -> None:
        before = self.run_cli("old", "id", "D").stdout.strip()
        after = self.run_cli("new", "id", "D").stdout.strip()
        self.assertEqual(before, after)
        number = lambda text: int(text.split("-")[1])  # noqa: E731
        self.assertGreaterEqual(number(after), 13)  # D-012 was the highest at baseline


if __name__ == "__main__":
    unittest.main()
