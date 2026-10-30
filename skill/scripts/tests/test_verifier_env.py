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

    def test_inherit_env_hands_over_the_owners_environment_and_every_secret_file_variable_apart_from_the_explicit_ones(self):
        import os
        from unittest.mock import patch
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / "verifier.env").write_text("MODE=test\n", encoding="utf-8")
        (root / "secrets.env").write_text("DB_URL=postgres://u:pw@localhost:55433/db\nBOT_TOKEN=t0ken\nMODE=prod\n", encoding="utf-8")
        config = {"verifier.env_file": str(root / "verifier.env"), "verifier.secret_files": [str(root / "secrets.env")],
                  "verifier.inherit_env": ["*"]}
        owner = {"PICTURES_FLAG": "1", "PATH": "/evil", "LD_PRELOAD": "x", "GIT_DIR": "/x", "PYTHONPATH": "/p", "EMPTY": ""}
        with patch("bt_config.get", side_effect=lambda key, default=None: config.get(key, default)), \
                patch.dict(os.environ, owner, clear=True):
            explicit, _ = venv.for_run("p", None)
            ambient, secrets = venv.ambient_for_run("p", {name for name, _ in explicit})
            config["verifier.inherit_env"] = ["PICTURES_*"]
            narrowed = dict(venv.ambient_for_run("p", {name for name, _ in explicit})[0])
        self.assertEqual(dict(explicit), {"MODE": "test"})                      # what the evidence fingerprint sees: unchanged
        env = dict(ambient)
        self.assertNotIn("MODE", env)                                            # the project's file wins over a secret file
        self.assertEqual(env["PICTURES_FLAG"], "1")
        self.assertEqual({env["DB_URL"], env["BOT_TOKEN"]}, {"postgres://u:pw@localhost:55433/db", "t0ken"})
        for protected in ("PATH", "LD_PRELOAD", "GIT_DIR", "PYTHONPATH", "EMPTY"):
            self.assertNotIn(protected, env)                                    # what the sandbox protects is never inherited
        self.assertIn("t0ken", secrets)                                          # secret-looking values stay redacted
        self.assertEqual(narrowed, {"PICTURES_FLAG": "1"})                      # a glob list narrows what is inherited

    def test_inherited_variables_never_change_the_evidence_fingerprint_but_reach_the_sandbox(self):
        from bt_scheduler_quality import reuse
        from bt_scheduler_quality.policy import QualityPolicy
        from bt_scheduler_quality.runner_sandbox_process import _environment
        explicit = (("MODE", "test"),)
        plain = QualityPolicy(environment=explicit)
        ambient = QualityPolicy(environment=explicit, ambient_environment=(("PICTURES_FLAG", "1"), ("MODE", "ignored")))
        self.assertEqual(reuse.environment_fingerprint(plain), reuse.environment_fingerprint(ambient))
        sent = dict(_environment(ambient))
        self.assertEqual((sent["PICTURES_FLAG"], sent["MODE"]), ("1", "test"))    # reaches the check; the explicit value wins

    def test_a_legacy_fingerprint_the_owner_listed_is_accepted_and_nothing_else_is(self):
        import json
        import tempfile as tf
        from pathlib import Path as P
        import bt_scheduler_executor_wiring as wiring
        import bt_scheduler_quality_owner_adapter as adapter
        from bt_scheduler_quality import reuse
        from bt_scheduler_quality.policy import QualityPolicy
        with tf.TemporaryDirectory() as tmp:
            (P(tmp) / wiring.LEGACY_FILE).write_text(json.dumps({"fingerprints": ["151b329d1689a325ffd13aa4", "bad", 7]}), encoding="utf-8")
            legacy = wiring._legacy_fingerprints(P(tmp))
            self.assertEqual(legacy, ("151b329d1689a325ffd13aa4",))
            self.assertEqual(wiring._legacy_fingerprints(P(tmp) / "nowhere"), ())
        plain = QualityPolicy(environment=(("MODE", "test"),))
        policy = QualityPolicy(environment=(("MODE", "test"),), accepted_environment_fingerprints=legacy)
        current = reuse.environment_fingerprint(plain)
        self.assertTrue(adapter.environment_fingerprint_matches(policy, {}, None, current))
        self.assertTrue(adapter.environment_fingerprint_matches(policy, {}, None, "151b329d1689a325ffd13aa4"))
        self.assertFalse(adapter.environment_fingerprint_matches(plain, {}, None, "151b329d1689a325ffd13aa4"))
        self.assertFalse(adapter.environment_fingerprint_matches(policy, {}, None, "0" * 24))
        with self.assertRaises(ValueError):
            QualityPolicy(accepted_environment_fingerprints=("nope",))

    def test_inherit_env_is_off_by_default(self):
        from unittest.mock import patch
        with patch("bt_config.get", side_effect=lambda key, default=None: default):
            self.assertEqual((venv.for_run("p", None), venv.ambient_for_run("p", set())), (((), ()), ((), ())))

    def test_declared_reads_the_requires_of_the_latest_frozen_revision(self):
        from unittest.mock import patch
        plan = {"tasks": [{"verification": [{"requires": ["DB_URL", "service:x", "bad name"]}]}, {"verification": []}]}
        with patch("bt_plan_adapter.latest_plan", return_value=plan):
            self.assertEqual(venv.declared("/r"), {"DB_URL"})
        self.assertEqual(venv.declared(None), set())


if __name__ == "__main__":
    unittest.main()
