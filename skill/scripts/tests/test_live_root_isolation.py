"""The owner's per-user live resources belong to the live bitácora alone (D-256).

A process whose root is anything else (a test, a lab, a scratch folder) must never reach them by falling back to a default
when a variable is missing: the tmux socket `bitacora` (D-252 covered only bt_regress), the owner's secret and agent env
files (config defaults), the live root itself under a test runner (D-247: a hand-run suite wrote into the live feed).
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import bt_agent_terminal
import bt_config
import bt_core

PROBE = textwrap.dedent("""
    import os, sys, unittest
    sys.path.insert(0, os.environ["SCRIPTS"])
    import bt_core

    class Probe(unittest.TestCase):
        def test_root(self):
            print("ROOT=" + str(bt_core.ROOT))
            print("ENV=" + os.environ.get("BITACORA_ROOT", ""))
""")


class TestRunnerRoot(unittest.TestCase):
    """A test process never runs on the live root, whether BITACORA_ROOT is missing or names it."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="bt-live-root-"))
        self.home = self.tmp / "home"
        (self.home / "bitacora").mkdir(parents=True)
        (self.tmp / "probe_root.py").write_text(PROBE)

    def run_probe(self, *argv: str, root: str | None) -> dict[str, str]:
        env = {k: v for k, v in os.environ.items() if k not in ("BITACORA_ROOT", "BITACORA_TEST_ROOT")}
        env.update(HOME=str(self.home), SCRIPTS=str(SCRIPTS), PYTHONPATH=str(SCRIPTS))
        if root is not None:
            env["BITACORA_ROOT"] = root
        done = subprocess.run([sys.executable, *argv], cwd=self.tmp, env=env, capture_output=True, text=True, timeout=120,
                              check=False)
        self.assertEqual(done.returncode, 0, done.stderr[-2000:])
        return dict(line.split("=", 1) for line in (done.stdout + done.stderr).splitlines()
                    if line.startswith(("ROOT=", "ENV=")))

    def assert_not_live(self, seen: dict[str, str]):
        live = (self.home / "bitacora").resolve()
        self.assertNotEqual(Path(seen["ROOT"]).resolve(), live)
        self.assertEqual(seen["ENV"], seen["ROOT"])                  # exported: its subprocesses inherit the scratch root

    def test_a_unittest_run_without_the_variable_gets_a_throwaway_root(self):
        self.assert_not_live(self.run_probe("-m", "unittest", "probe_root", root=None))

    def test_a_unittest_run_that_names_the_live_root_gets_a_throwaway_root(self):
        """An agent spawned by bt-durable.service inherits BITACORA_ROOT=~/bitacora and may run a suite by hand."""
        self.assert_not_live(self.run_probe("-m", "unittest", "probe_root", root=str(self.home / "bitacora")))

    def test_a_scratch_root_is_kept(self):
        scratch = self.tmp / "scratch"
        seen = self.run_probe("-m", "unittest", "probe_root", root=str(scratch))
        self.assertEqual(Path(seen["ROOT"]), scratch)

    def test_the_cli_still_defaults_to_the_live_root(self):
        code = f"import sys; sys.path.insert(0, {str(SCRIPTS)!r}); import bt_core; print('ROOT=' + str(bt_core.ROOT))"
        seen = self.run_probe("-c", code, root=None)
        self.assertEqual(Path(seen["ROOT"]), self.home / "bitacora")


class TmuxSocket(unittest.TestCase):
    def test_only_the_live_root_defaults_to_the_live_socket(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("BITACORA_TMUX_SOCKET", None)
            with patch.object(bt_core, "ROOT", Path(tempfile.mkdtemp(prefix="bt-sock-")) / "bitacora"):
                scratch = bt_agent_terminal.socket()
                self.assertTrue(scratch.startswith("bitacora-"), scratch)
                self.assertEqual(bt_agent_terminal.socket(), scratch)          # stable for one root
            with patch.object(bt_core, "ROOT", Path(tempfile.mkdtemp(prefix="bt-sock-")) / "bitacora"):
                self.assertNotEqual(bt_agent_terminal.socket(), scratch)       # and different for another
            with patch.object(bt_core, "ROOT", bt_core.LIVE_ROOT):
                self.assertEqual(bt_agent_terminal.socket(), "bitacora")

    def test_the_variable_wins(self):
        with patch.dict(os.environ, {"BITACORA_TMUX_SOCKET": "btr-x"}):
            self.assertEqual(bt_agent_terminal.socket(), "btr-x")


class OwnerFileDefaults(unittest.TestCase):
    """`verifier.secret_files` and `execution.agent_env_file` name the owner's own files: a scratch root starts without
    them (a plan's `requires` copied the owner's real secrets into a test policy before)."""

    def setUp(self):
        self.state = Path(tempfile.mkdtemp(prefix="bt-cfg-")) / ".state"
        patcher = patch("bt_config.STATE", self.state)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_a_scratch_root_has_no_owner_files_by_default(self):
        with patch.object(bt_core, "ROOT", self.state.parent):
            self.assertEqual(bt_config.get("verifier.secret_files"), [])
            self.assertEqual(bt_config.get("execution.agent_env_file"), "")
            bt_config.set_value("verifier.secret_files", ["/lab/secrets.env"])      # its own config still names files
            self.assertEqual(bt_config.get("verifier.secret_files"), ["/lab/secrets.env"])

    def test_the_live_root_keeps_them(self):
        with patch.object(bt_core, "ROOT", bt_core.LIVE_ROOT):
            self.assertEqual(bt_config.get("verifier.secret_files"), ["~/.config/flow/secrets.env"])
            self.assertEqual(bt_config.get("execution.agent_env_file"), "~/.config/metodologia/agent-{project}.env")

    def test_a_scratch_root_never_copies_the_owners_secret_into_a_check(self):
        import bt_verifier_env
        home = self.state.parent / "home"
        (home / ".config" / "flow").mkdir(parents=True)
        (home / ".config" / "flow" / "secrets.env").write_text("PICTURES_TEST_PASSWORD=owner-real-value\n")
        with patch.object(bt_core, "ROOT", self.state.parent), \
                patch.object(bt_verifier_env, "declared", return_value={"PICTURES_TEST_PASSWORD"}), \
                patch.dict(os.environ, {"HOME": str(home)}):
            environment, secrets = bt_verifier_env.for_run("pictures", self.state.parent)
        self.assertEqual((environment, secrets), ((), ()))


if __name__ == "__main__":
    unittest.main()
