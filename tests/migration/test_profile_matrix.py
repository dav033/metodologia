from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "skill" / "scripts"
PROBE = r'''
import json, os, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import bt_profiles
import bt_profile_matrix as matrix
home = Path.home()
work = sys.argv[2]
bt_profiles.set_work(work, True)
bt_profiles.add("claude-personal", "claude", {"CLAUDE_CONFIG_DIR": str(home / "missing-claude"),
                                                "PROFILE_SECRET": "sentinel-profile-secret"})
bt_profiles.add("claude-work", "claude", {"CLAUDE_CONFIG_DIR": str(home / "claude-work")}, work_only=True)
bt_profiles.add("codex-1", "codex", {"CODEX_HOME": str(home / "shared-codex")})
bt_profiles.add("codex-luis", "codex", {"CODEX_HOME": str(home / "shared-codex")})
bt_profiles.add("antigravity", "antigravity", {"PROFILE_SECRET": "sentinel-profile-secret"})
profiles = bt_profiles.load()
env = {"PATH": sys.argv[3]}
results = {
    "identities": matrix.matrix("personal", profiles),
    "personal": matrix.diagnose("claude-work", "personal", home, env),
    "work": matrix.diagnose("claude-work", work, home, env),
    "missing": matrix.diagnose("claude-personal", "personal", home, env),
    "with_binary": matrix.diagnose("codex-1", "personal", home, env),
    "without_binary": matrix.diagnose("codex-1", "personal", home, {"PATH": sys.argv[4]}),
}
print(json.dumps(results))
'''


class ProfileMatrixTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="profile-matrix-")
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)
        self.root = self.home / "bitacora"
        self.bin = self.home / "bin"
        self.bin.mkdir()
        binary = self.bin / "codex"
        binary.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        binary.chmod(0o755)
        self.work = "registered-work-project"

    def results(self) -> dict:
        env = {"HOME": str(self.home), "BITACORA_ROOT": str(self.root),
               "PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"}
        done = subprocess.run([sys.executable, "-I", "-c", PROBE, str(SCRIPTS), self.work,
                               str(self.bin), str(self.home / "empty-path")],
                              capture_output=True, text=True, env=env, timeout=30)
        self.assertEqual(done.returncode, 0, done.stderr)
        return json.loads(done.stdout)

    def test_five_identities_work_gate_missing_auth_and_binary_detection(self) -> None:
        result = self.results()
        rows = result["identities"]
        self.assertEqual([row["identity"] for row in rows],
                         ["claude-personal", "claude-work", "codex-1", "codex-luis", "antigravity"])
        self.assertEqual(len(rows), 5)
        self.assertFalse(result["personal"]["authorized_for_project"])
        self.assertTrue(result["work"]["authorized_for_project"])
        self.assertFalse(result["missing"]["directory_provisioned"])
        self.assertIsNone(result["missing"]["authenticated"])
        self.assertTrue(result["with_binary"]["binary_found"])
        self.assertFalse(result["without_binary"]["binary_found"])
        self.assertIsNone(result["missing"]["smoke_verified"])

    def test_shared_account_is_reported_as_duplicate_not_extra_capacity(self) -> None:
        rows = self.results()["identities"]
        by_id = {row["identity"]: row for row in rows}
        self.assertIsNone(by_id["codex-1"]["duplicate_of"])
        self.assertEqual(by_id["codex-luis"]["duplicate_of"], "codex-1")

    def test_profile_environment_secrets_never_appear_in_diagnostics(self) -> None:
        exposed = json.dumps(self.results(), ensure_ascii=False)
        self.assertNotIn("sentinel-profile-secret", exposed)

    def test_matrix_accepts_injected_home_environment_and_path(self) -> None:
        done = subprocess.run([sys.executable, "-I", "-c", r'''
import os, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import bt_profile_matrix as m
profiles = {name: {"provider": provider, "bin": "missing", "env": {}}
            for name, provider in [("claude-personal", "claude"), ("claude-work", "claude"),
            ("codex-1", "codex"), ("codex-luis", "codex"), ("antigravity", "antigravity")]}
rows = m.matrix("project", profiles, home=Path(os.environ["HOME"]), environ={}, path="")
assert len(rows) == 5
assert all(not row["directory_provisioned"] for row in rows)
''', str(SCRIPTS)], capture_output=True, text=True,
            env={"HOME": str(self.root / "nonexistent"), "BITACORA_ROOT": str(self.root / "bitacora"),
                 "PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"},
            timeout=30)
        self.assertEqual(done.returncode, 0, done.stderr)


if __name__ == "__main__":
    unittest.main()
