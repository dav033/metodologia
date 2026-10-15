"""The M2 core remains a standard-library-only, copyable package."""
from __future__ import annotations

import ast
import re
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1]
STDLIB = set(sys.stdlib_module_names)
DYNAMIC_NAMES = {"eval", "exec", "__import__", "import_module", "getenv", "environ", "environb", "putenv",
                 "system", "popen", "ctypes", "load_module", "find_spec"}


class Boundaries(unittest.TestCase):
    def package_sources(self):
        return [path for path in MODULE.rglob("*.py") if "tests" not in path.relative_to(MODULE).parts]

    def all_sources(self):
        return [path for path in MODULE.rglob("*.py") if "__pycache__" not in path.parts]

    def test_package_imports_only_standard_library_and_itself(self):
        for path in self.all_sources():
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.Import):
                    names = [alias.name.split(".")[0] for alias in node.names]
                    levels = [0] * len(names)
                elif isinstance(node, ast.ImportFrom):
                    names, levels = [(node.module or "").split(".")[0]], [node.level]
                else:
                    continue
                for name, level in zip(names, levels):
                    self.assertTrue(level == 1 or name in STDLIB or name == "bt_scheduler_decision",
                                    f"{path.name}:{node.lineno} imports {name!r}")

    def test_no_dynamic_import_environment_or_process_escape(self):
        for path in self.package_sources():
            source = path.read_text(encoding="utf-8")
            for node in ast.walk(ast.parse(source)):
                names = []
                if isinstance(node, ast.Name):
                    names = [node.id]
                elif isinstance(node, ast.Attribute):
                    names = [node.attr]
                elif isinstance(node, ast.alias):
                    names = [node.name.split(".")[-1]]
                for name in names:
                    self.assertNotIn(name, DYNAMIC_NAMES, f"{path.name}:{getattr(node, 'lineno', '?')}: {name}")
            self.assertNotRegex(source, re.compile(r"\b(subprocess|socket|urllib|httpx|requests)\b"))

    def test_readme_lists_the_single_public_surface(self):
        readme = (MODULE / "README.md").read_text(encoding="utf-8")
        init = (MODULE / "__init__.py").read_text(encoding="utf-8")
        self.assertIn("__all__", init)
        for name in ("DecisionRequest", "TaskFacts", "Candidate", "RouteHistory", "LayaChoice", "DecisionRecord",
                     "validate_request", "executor_reference", "parse_executor_reference", "DecisionLedger",
                     "idempotency_key", "decision_id_for", "resolve_executor_reference"):
            self.assertIn(f"`{name}`", readme)
        self.assertIn("api-contract.json", readme)


if __name__ == "__main__":
    unittest.main()
