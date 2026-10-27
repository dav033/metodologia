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


class ForRun(unittest.TestCase):
    """A variable a check declares in `requires` comes from the owner's secret files when the env file lacks it."""

    def test_only_declared_names_are_taken_from_the_secret_files(self):
        from unittest.mock import patch
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / "verifier.env").write_text("MODE=test\n", encoding="utf-8")
        (root / "secrets.env").write_text("DB_URL=postgres://u:pw@localhost:55433/db\nBOT_TOKEN=t0ken\nMODE=prod\n",
                                          encoding="utf-8")
        config = {"verifier.env_file": str(root / "verifier.env"), "verifier.secret_files": [str(root / "secrets.env")]}
        with patch("bt_config.get", side_effect=lambda key, default=None: config.get(key, default)), \
                patch.object(venv, "declared", return_value={"DB_URL", "MODE", "service:db"}):
            environment, secrets = venv.for_run("p", root)
        self.assertEqual(dict(environment), {"MODE": "test", "DB_URL": "postgres://u:pw@localhost:55433/db"})
        self.assertEqual(secrets, ("postgres://u:pw@localhost:55433/db",))   # redacted from every output
        with patch("bt_config.get", side_effect=lambda key, default=None: config.get(key, default)):
            self.assertEqual(dict(venv.for_run("p", None)[0]), {"MODE": "test"})   # no frozen plan: nothing declared

    def test_declared_reads_the_requires_of_the_latest_frozen_revision(self):
        from unittest.mock import patch
        plan = {"tasks": [{"verification": [{"requires": ["DB_URL", "service:x", "bad name"]}]}, {"verification": []}]}
        with patch("bt_planner.revisions.latest", return_value={"revision": 1}), \
                patch("bt_planner.revisions.load_revision", return_value=plan):
            self.assertEqual(venv.declared("/r"), {"DB_URL"})
        self.assertEqual(venv.declared(None), set())


if __name__ == "__main__":
    unittest.main()
