"""The detached `relay launch` helper must be a command line the real CLI accepts.

Regression (2026-10-14): `--cwd` was placed after the subcommand, argparse exited with status 2 and no relay ever
relaunched anything, while `relay handoff` still reported success. The old tests mocked the spawn, so nothing ran
the real parser."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bt_relay_handoff


class LaunchArgvTests(unittest.TestCase):
    def run_cli(self, argv: list[str]) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory(prefix="relay-argv-") as tmp:
            env = {"PATH": "/usr/bin:/bin", "HOME": tmp, "BITACORA_ROOT": str(Path(tmp) / "bit"),
                   "PYTHONDONTWRITEBYTECODE": "1"}
            return subprocess.run(argv, capture_output=True, text=True, env=env, timeout=60, check=False)

    def test_the_helper_command_line_is_accepted_by_the_real_parser(self) -> None:
        for wrapper, agent, mux in ((None, None, None), ({"pid": 11, "start": 22}, (33, 44), None),
                                    (None, (33, 44), {"kind": "kitty", "target": "1", "env": {"A": "b"}})):
            with self.subTest(wrapper=bool(wrapper), mux=bool(mux)):
                argv = bt_relay_handoff.launch_argv("/nonexistent/RELAY-1.md", "codex-1", "/tmp", "session-1",
                                                   wrapper, agent, mux, True)
                done = self.run_cli(argv)
                self.assertNotIn("unrecognized arguments", done.stderr)
                self.assertNotEqual(done.returncode, 2, done.stderr)  # 2 = argparse refused the command line

    def test_cwd_precedes_the_subcommand(self) -> None:
        argv = bt_relay_handoff.launch_argv("/h.md", "codex-1", "/work", "s", None, None, None, False)
        self.assertLess(argv.index("--cwd"), argv.index("relay"))
        self.assertEqual(argv[argv.index("--exit-current") + 1], "0")


if __name__ == "__main__":
    unittest.main()
