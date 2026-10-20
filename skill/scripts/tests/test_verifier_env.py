"""The owner's dotenv file for the independent checks: what it hands to the sandbox, and what it never does."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bt_verifier_env as venv
from bt_scheduler_quality.policy import QualityPolicy


class Load(unittest.TestCase):
    def write(self, text):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "verifier.env"
        path.write_text(text, encoding="utf-8")
        return path

    def test_reads_values_registers_the_secret_ones_and_skips_what_the_sandbox_protects(self):
        path = self.write('# comment\nexport DB_URL="postgres://user:p4ss@host/db"\nMODE=test # inline\nPATH=/evil\n'
                          "API_KEY='abc123'\nGIT_DIR=/x\nEMPTY=\nbad line\n")
        environment, secrets = venv.load(path)
        self.assertEqual(dict(environment), {"DB_URL": "postgres://user:p4ss@host/db", "MODE": "test", "API_KEY": "abc123"})
        self.assertEqual(set(secrets), {"postgres://user:p4ss@host/db", "abc123"})
        QualityPolicy(environment=environment, secret_values=secrets)         # the policy accepts what was loaded

    def test_the_path_is_per_project(self):
        self.assertEqual(venv.path_for("~/.config/m/verifier-{project}.env", "pictures"), "~/.config/m/verifier-pictures.env")
        self.assertEqual(venv.path_for("~/x/{project}.env", "../etc"), "~/x/..etc.env")
        self.assertEqual((venv.path_for("", "p"), venv.path_for(None, "p")), ("", ""))

    def test_an_unset_missing_or_unreadable_file_gives_nothing(self):
        self.assertEqual(venv.load(""), ((), ()))
        self.assertEqual(venv.load(None), ((), ()))
        self.assertEqual(venv.load("/nonexistent/verifier.env"), ((), ()))
        binary = self.write("")
        binary.write_bytes(b"\xff\xfe\x00")
        self.assertEqual(venv.load(binary), ((), ()))


if __name__ == "__main__":
    unittest.main()
