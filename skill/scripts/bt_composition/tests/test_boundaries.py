from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = {"subprocess", "socket"}
ENVIRONMENT = {"environ", "getenv", "putenv", "unsetenv"}


class BoundaryTests(unittest.TestCase):
    def test_production_code_is_stdlib_and_self_only(self):
        findings = []
        for path in ROOT.rglob("*.py"):
            if "tests" in path.relative_to(ROOT).parts:
                continue
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        top = alias.name.split(".", 1)[0]
                        if top in FORBIDDEN or (top.startswith("bt_") and top != "bt_composition"):
                            findings.append(f"{path}: {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    top = (node.module or "").split(".", 1)[0]
                    if node.level == 0 and (top in FORBIDDEN or (top.startswith("bt_") and top != "bt_composition")):
                        findings.append(f"{path}: {node.module}")
                    if node.module == "os" and any(alias.name in ENVIRONMENT for alias in node.names):
                        findings.append(f"{path}: environment access")
        self.assertEqual(findings, [])

    def test_readme_tracks_public_api_and_states(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        api = (ROOT / "__init__.py").read_text(encoding="utf-8")
        for name in ("GitPort", "Store", "CompositionEngine", "EvidenceKey", "propagate", "reusable"):
            self.assertIn(name, api)
            self.assertIn(name, readme)
        for state in ("candidate", "verifying", "published", "rejected"):
            self.assertIn(f"`{state}`", readme)
        for code in ("INVALID_IDENTIFIER", "git_text_conflict", "COMPOSITION_CURRENT_MOVED",
                     "SUBPLAN_VERSION_CONFLICT", "PUBLISHED_COMPOSITION_IMMUTABLE"):
            self.assertIn(code, readme)


if __name__ == "__main__":
    unittest.main()
