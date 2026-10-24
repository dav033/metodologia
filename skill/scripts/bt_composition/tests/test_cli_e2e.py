from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def test_manifest_cli_from_unrelated_directory_and_isolated_mode(self):
        value = {"members": {"S1": 1}, "state": "candidate"}
        canonical = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        with tempfile.TemporaryDirectory(prefix="composition-cli-") as directory:
            cwd = Path(directory)
            manifest = cwd / "manifest.json"
            manifest.write_text(json.dumps(value), encoding="utf-8")
            code = ("import sys; sys.path.insert(0, " + repr(str(ROOT.parent)) + "); "
                    "from bt_composition.cli import main; raise SystemExit(main(['manifest-sha256', "
                    + repr(str(manifest)) + "]))")
            result = subprocess.run([sys.executable, "-I", "-c", code], cwd=cwd,
                                    env={"PATH": os.environ.get("PATH", os.defpath),
                                         "PYTHONDONTWRITEBYTECODE": "1"},
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), hashlib.sha256(canonical).hexdigest())


if __name__ == "__main__":
    unittest.main()
