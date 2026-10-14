"""Inspecting the live checker must never start providers or create a run."""
import runpy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


class OperationalCliTests(unittest.TestCase):
    def test_help_and_missing_live_flag_do_not_create_state(self):
        script = Path(__file__).resolve().parent.parent / "ops_flow_check.py"
        for args, expected in ((["--help"], 0), ([], 2)):
            with self.subTest(args=args), patch.object(sys, "argv", [str(script), *args]), \
                    patch("tempfile.mkdtemp", side_effect=AssertionError("live state created")), \
                    patch("subprocess.run", side_effect=AssertionError("subprocess launched")):
                with self.assertRaises(SystemExit) as stopped:
                    runpy.run_path(str(script), run_name="__main__")
                self.assertEqual(stopped.exception.code, expected)
