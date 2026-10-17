from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


class PackageIsolationTests(unittest.TestCase):
    @unittest.skipIf(os.environ.get("BT_M4_ISOLATION_CHILD") == "1", "avoid nested isolation subprocesses")
    def test_package_suite_and_cli_work_when_copied_alone(self) -> None:
        with tempfile.TemporaryDirectory(prefix="m4-isolation-") as directory:
            isolated_root = Path(directory)
            isolated_package = isolated_root / "bt_scheduler_monitor"
            shutil.copytree(PACKAGE_ROOT, isolated_package,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            environment = {
                "PATH": os.environ.get("PATH", os.defpath),
                "PYTHONPATH": str(isolated_root),
                "PYTHONDONTWRITEBYTECODE": "1",
                "BT_M4_ISOLATION_CHILD": "1",
            }
            suite = subprocess.run(
                [sys.executable, "-m", "unittest", "discover", "-s", str(isolated_package / "tests"), "-v"],
                cwd=isolated_root, env=environment, capture_output=True, text=True, timeout=60,
            )
            self.assertEqual(suite.returncode, 0, suite.stdout + suite.stderr)
            cli = subprocess.run(
                [sys.executable, "-m", "bt_scheduler_monitor", "--help"], cwd=isolated_root,
                env=environment, capture_output=True, text=True, timeout=10,
            )
            self.assertEqual(cli.returncode, 0, cli.stdout + cli.stderr)
            self.assertIn("usage:", cli.stdout.lower())


if __name__ == "__main__":
    unittest.main()
