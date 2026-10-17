from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]


class PackageIsolationTests(unittest.TestCase):
    def test_package_alone_runs_its_suite_under_python_isolated_mode(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            copied = root / "plan_bench"
            shutil.copytree(PACKAGE, copied, ignore=shutil.ignore_patterns("__pycache__"))
            code = (
                "import sys,unittest; sys.path.insert(0,sys.argv[1]); "
                "suite=unittest.defaultTestLoader.discover(sys.argv[2],pattern='test_module.py'); "
                "result=unittest.TextTestRunner(verbosity=0).run(suite); sys.exit(0 if result.wasSuccessful() else 1)"
            )
            result = subprocess.run([sys.executable, "-I", "-c", code, str(root), str(copied / "tests")],
                                    cwd="/", capture_output=True, text=True, timeout=30, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
