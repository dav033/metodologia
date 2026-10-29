"""Every module of skill/scripts travels in the distribution (`pyproject.toml` lists them by hand in `py-modules`).

A module left out installs a package that fails at import time: the remote API of an installed distribution died on
`bt_flow_durable` (D-150), and thirteen planning modules had drifted out unnoticed. Standalone scripts are named here."""
from __future__ import annotations

import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
NOT_MODULES = {"ops_check": "operator script run by path", "ops_matrix_check": "operator script run by path",
               "setup_bt_scheduler_laya": "one-off setup script run by path"}


class PackageModules(unittest.TestCase):
    def test_every_script_module_is_listed_and_nothing_listed_is_gone(self):
        listed = set(tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
                     ["tool"]["setuptools"]["py-modules"])
        real = {path.stem for path in (ROOT / "skill" / "scripts").glob("*.py")}
        self.assertEqual(sorted(real - listed - set(NOT_MODULES)), [], "add these to py-modules in pyproject.toml")
        self.assertEqual(sorted(listed - real), [], "these py-modules no longer exist")
        self.assertEqual(sorted(set(NOT_MODULES) - real), [], "NOT_MODULES names a script that is gone")


if __name__ == "__main__":
    unittest.main()
