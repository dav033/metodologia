from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]


class PackageBoundaryTests(unittest.TestCase):
    def test_check_history_persistence_stays_in_a_small_private_module(self):
        path = PACKAGE / "check_history.py"
        self.assertLess(len(path.read_text(encoding="utf-8").splitlines()), 500)
        self.assertGreaterEqual(len(path.read_text(encoding="utf-8").splitlines()), 1)

    def test_package_imports_only_its_own_modules_and_the_standard_library(self):
        violations = []
        for path in sorted(PACKAGE.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for item in node.names:
                        root = item.name.split(".", 1)[0]
                        if root not in sys.stdlib_module_names and root != PACKAGE.name:
                            violations.append(f"{path.name}: import {item.name}")
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    root = (node.module or "").split(".", 1)[0]
                    if root not in sys.stdlib_module_names and root != PACKAGE.name:
                        violations.append(f"{path.name}: from {node.module}")

        self.assertEqual(violations, [])


if __name__ == "__main__":
    unittest.main()
