from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipIf(os.environ.get("BT_COMPOSITION_ISOLATION_CHILD") == "1", "avoid nested isolated copies")
class IsolationTests(unittest.TestCase):
    def test_package_copy_runs_its_suite_and_cli_alone(self):
        with tempfile.TemporaryDirectory(prefix="composition-isolation-") as directory:
            root = Path(directory)
            package = root / "bt_composition"
            shutil.copytree(ROOT, package, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            env = {"PATH": os.environ.get("PATH", os.defpath), "PYTHONPATH": str(root),
                   "PYTHONDONTWRITEBYTECODE": "1", "BT_COMPOSITION_ISOLATION_CHILD": "1"}
            suite = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(package / "tests")],
                                   cwd=root, env=env, capture_output=True, text=True, timeout=60)
            self.assertEqual(suite.returncode, 0, suite.stdout + suite.stderr)
            cli = subprocess.run([sys.executable, "-m", "bt_composition", "--help"], cwd=root,
                                 env=env, capture_output=True, text=True, timeout=10)
            self.assertEqual(cli.returncode, 0, cli.stdout + cli.stderr)
            self.assertIn("usage:", cli.stdout.lower())


if __name__ == "__main__":
    unittest.main()
