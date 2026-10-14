"""Discovery must not move the environment away from bt_core's frozen test root."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class DiscoveryIsolationTests(unittest.TestCase):
    def test_isolated_run_import_preserves_an_existing_test_root(self):
        repo = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as scratch:
            env = {**os.environ, "BITACORA_TEST_ROOT": scratch,
                   "BITACORA_ROOT": str(Path(scratch) / "bitacora")}
            code = (
                "import os, sys; from pathlib import Path; "
                "sys.path[:0] = ['skill/scripts', 'tests']; "
                "import bt_core; before = bt_core.ROOT; "
                "import migration.test_isolated_run; "
                "assert Path(os.environ['BITACORA_ROOT']) == before, "
                "(before, os.environ['BITACORA_ROOT'])"
            )
            done = subprocess.run([sys.executable, "-c", code], cwd=repo, env=env,
                                  capture_output=True, text=True, timeout=15, check=False)
            self.assertEqual(done.returncode, 0, done.stderr)
