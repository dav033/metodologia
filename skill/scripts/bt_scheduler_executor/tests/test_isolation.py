"""Proof of isolation: the package, copied ALONE to an empty temp directory, passes its own suite in an isolated
interpreter started from an unrelated cwd. Nothing else of the methodology is reachable from there."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1]
ENV_FLAG = "BT_SCHEDULER_EXECUTOR_ISOLATED_COPY"


@unittest.skipIf(os.environ.get(ENV_FLAG) == "1", "already running inside the isolated copy")
class IsolatedCopy(unittest.TestCase):
    def test_suite_passes_from_a_lone_copy(self):
        with tempfile.TemporaryDirectory(prefix="m3-lone-") as tmp:
            root = Path(tmp) / "only-this"
            shutil.copytree(MODULE, root / "bt_scheduler_executor", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            cwd = Path(tmp) / "unrelated-cwd"
            cwd.mkdir()
            done = subprocess.run([sys.executable, "-I", "-m", "unittest", "discover", "-s",
                                   str(root / "bt_scheduler_executor" / "tests")],
                                  capture_output=True, text=True, check=False, cwd=cwd, timeout=900,
                                  env={"PATH": "/usr/bin:/bin", ENV_FLAG: "1", "PYTHONDONTWRITEBYTECODE": "1",
                                       "HOME": str(Path(tmp) / "home")})
            tail = (done.stderr or done.stdout)[-1500:]
            self.assertEqual(done.returncode, 0, tail)
            self.assertIn("OK", done.stderr)
            ran = [line for line in done.stderr.splitlines() if line.startswith("Ran ")]
            self.assertTrue(ran and int(ran[0].split()[1]) >= 180, ran)

    def test_the_copy_really_has_no_methodology_around_it(self):
        with tempfile.TemporaryDirectory(prefix="m3-lone-") as tmp:
            shutil.copytree(MODULE, Path(tmp) / "bt_scheduler_executor", ignore=shutil.ignore_patterns("__pycache__"))
            probe = ("import sys; sys.path.insert(0, sys.argv[1]); import bt_scheduler_executor\n"
                     "import importlib.util as u\n"
                     "print([m for m in ('bt_core', 'bt_runstate', 'bt_scheduler_core', 'bt_driver', 'bitacora') "
                     "if u.find_spec(m)])")
            done = subprocess.run([sys.executable, "-I", "-c", probe, tmp], capture_output=True, text=True, check=False,
                                  cwd=tmp, timeout=60)
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertEqual(done.stdout.strip(), "[]")

    def test_importing_the_package_loads_no_other_bt_module(self):
        probe = ("import sys; sys.path.insert(0, sys.argv[1]); import bt_scheduler_executor\n"
                 "print(sorted(m for m in sys.modules if m.startswith('bt_') and not m.startswith('bt_scheduler_executor')))")
        done = subprocess.run([sys.executable, "-I", "-c", probe, str(MODULE.parent)], capture_output=True, text=True,
                              check=False, timeout=60)
        self.assertEqual(done.stdout.strip(), "[]", done.stderr)


if __name__ == "__main__":
    unittest.main()
