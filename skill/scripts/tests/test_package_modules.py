"""Every module of skill/scripts travels in the distribution (`pyproject.toml` lists them by hand in `py-modules`).

A module left out installs a package that fails at import time: the remote API of an installed distribution died on
`bt_flow_durable` (D-150), and thirteen planning modules had drifted out unnoticed; five more on 2026-10-31 stopped the
engine (D-277). Standalone scripts are named in `bt_package_modules.NOT_MODULES`."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bt_package_modules as pm

ROOT = Path(__file__).resolve().parents[3]


class PackageModules(unittest.TestCase):
    def test_every_script_module_is_listed_and_nothing_listed_is_gone(self):
        files = [path.name for path in (ROOT / pm.SCRIPTS).glob("*.py")]
        unlisted, gone = pm.drift(files, (ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(unlisted, [], "add these to py-modules in pyproject.toml")
        self.assertEqual(gone, [], "these py-modules no longer exist")
        real = {Path(name).stem for name in files}
        self.assertEqual(sorted(set(pm.NOT_MODULES) - real), [], "NOT_MODULES names a script that is gone")


if __name__ == "__main__":
    unittest.main()
