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
ENV_FLAG = "BT_SCHEDULER_CORE_ISOLATED_COPY"  # set in the child so the copy does not copy itself forever


@unittest.skipIf(os.environ.get(ENV_FLAG) == "1", "already running inside the isolated copy")
class IsolatedCopy(unittest.TestCase):
    def test_suite_passes_from_a_lone_copy(self):
        with tempfile.TemporaryDirectory(prefix="sched-lone-") as tmp:
            root = Path(tmp) / "only-this"
            shutil.copytree(MODULE, root / "bt_scheduler_core", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            cwd = Path(tmp) / "unrelated-cwd"
            cwd.mkdir()
            done = subprocess.run([sys.executable, "-I", "-m", "unittest", "discover", "-s",
                                   str(root / "bt_scheduler_core" / "tests")],
                                  capture_output=True, text=True, check=False, cwd=cwd, timeout=600,
                                  env={"PATH": "/usr/bin:/bin", ENV_FLAG: "1", "PYTHONDONTWRITEBYTECODE": "1"})
            tail = (done.stderr or done.stdout)[-1500:]
            self.assertEqual(done.returncode, 0, tail)
            self.assertIn("OK", done.stderr)
            ran = [line for line in done.stderr.splitlines() if line.startswith("Ran ")]
            self.assertTrue(ran and int(ran[0].split()[1]) >= 150, ran)   # the suite really ran, not an empty discovery

    def test_the_copy_really_has_no_methodology_around_it(self):
        with tempfile.TemporaryDirectory(prefix="sched-lone-") as tmp:
            shutil.copytree(MODULE, Path(tmp) / "bt_scheduler_core", ignore=shutil.ignore_patterns("__pycache__"))
            probe = ("import sys; sys.path.insert(0, sys.argv[1]); import bt_scheduler_core\n"
                     "import importlib.util as u\n"
                     "print([m for m in ('bt_core', 'bt_runstate', 'bt_lock', 'bitacora') "
                     "if u.find_spec(m) is not None])")
            out = subprocess.run([sys.executable, "-I", "-c", probe, tmp], capture_output=True, text=True, check=False, timeout=60)
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertEqual(out.stdout.strip(), "[]")


if __name__ == "__main__":
    unittest.main()
