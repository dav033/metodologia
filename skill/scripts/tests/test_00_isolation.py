"""Runs first (alphabetical discovery): points BITACORA_ROOT at a throwaway directory BEFORE any module imports bt_core,
which freezes ROOT at import time. Every other test file may therefore import bt_* modules freely, whatever its name.
A single test file run on its own must still set BITACORA_ROOT itself or patch the module's paths."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

if not os.environ.get("BITACORA_TEST_ROOT"):
    _tmp = Path(tempfile.mkdtemp(prefix="marathon-test-"))
    os.environ["BITACORA_TEST_ROOT"] = str(_tmp)
    os.environ["BITACORA_ROOT"] = str(_tmp / "bitacora")
    os.environ.setdefault("BITACORA_PORT", "8797")
    os.environ.setdefault("BITACORA_RUN_BACKOFF_SEC", "1")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bt_core  # noqa: E402


class IsolationTests(unittest.TestCase):
    def test_root_is_the_throwaway_directory(self):
        self.assertEqual(Path(bt_core.ROOT).resolve(),
                         (Path(os.environ["BITACORA_TEST_ROOT"]) / "bitacora").resolve())
        self.assertNotEqual(Path(bt_core.ROOT).resolve(), (Path.home() / "bitacora").resolve())


if __name__ == "__main__":
    unittest.main()
