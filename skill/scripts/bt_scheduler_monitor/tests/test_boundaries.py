from __future__ import annotations

import ast
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_MODULES = frozenset({"socket", "subprocess"})
ENVIRONMENT_NAMES = frozenset({"environ", "getenv", "putenv", "unsetenv"})


def _attribute_path(node: ast.AST) -> tuple[str, ...]:
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return tuple(reversed(parts))


class PackageBoundaryTests(unittest.TestCase):
    def test_production_package_uses_only_stdlib_and_its_own_modules(self) -> None:
        findings: list[str] = []
        for path in sorted(PACKAGE_ROOT.rglob("*.py")):
            if "tests" in path.relative_to(PACKAGE_ROOT).parts:
                continue
            relative = path.relative_to(PACKAGE_ROOT)
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(relative))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for imported in node.names:
                        module = imported.name.split(".", 1)[0]
                        if module in FORBIDDEN_MODULES or (module.startswith("bt_") and module != "bt_scheduler_monitor"):
                            findings.append(f"{relative}: forbidden import {imported.name}")
                elif isinstance(node, ast.ImportFrom):
                    module = (node.module or "").split(".", 1)[0]
                    if node.level == 0 and (module in FORBIDDEN_MODULES or
                            (module.startswith("bt_") and module != "bt_scheduler_monitor")):
                        findings.append(f"{relative}: forbidden import from {node.module}")
                    if node.module == "os" and any(alias.name in ENVIRONMENT_NAMES for alias in node.names):
                        findings.append(f"{relative}: imports environment access from os")
                elif isinstance(node, ast.Attribute):
                    parts = _attribute_path(node)
                    if len(parts) >= 2 and parts[0] == "os" and parts[1] in ENVIRONMENT_NAMES:
                        findings.append(f"{relative}: accesses os.{parts[1]}")
        self.assertEqual(findings, [], "M4 production package must remain isolated from runtime integrations")


if __name__ == "__main__":
    unittest.main()
