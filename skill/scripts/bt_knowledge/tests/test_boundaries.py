"""Architecture checks for the standalone package and its own suite."""
from __future__ import annotations

import ast
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]
STDLIB = set(sys.stdlib_module_names)
ALLOWED = {"bt_knowledge"}
FORBIDDEN = re.compile(r"bitacora|RUN\.json|~/|/home/|\.claude|\.codex", re.I)


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            found.add(node.module.split(".")[0])
    return found


class Boundaries(unittest.TestCase):
    def test_package_and_tests_import_only_standard_library_and_the_package(self):
        for source in sorted(PACKAGE.rglob("*.py")):
            if "__pycache__" in source.parts:
                continue
            with self.subTest(source=source.relative_to(PACKAGE)):
                self.assertLessEqual(imported_modules(source), STDLIB | ALLOWED)

    def test_package_names_no_methodology_paths_or_modules(self):
        for source in sorted(p for p in PACKAGE.rglob("*.py") if "tests" not in p.parts):
            content = source.read_text(encoding="utf-8")
            self.assertIsNone(FORBIDDEN.search(content), source.name)
            for node in ast.walk(ast.parse(content)):
                if isinstance(node, ast.ImportFrom) and node.level:
                    self.assertEqual(node.level, 1, f"{source.name}:{node.lineno}")

    def test_package_has_no_environment_or_dynamic_code_access(self):
        banned = {"getenv", "environ", "environb", "putenv", "eval", "exec", "__import__", "import_module",
                  "load_module", "find_spec", "ctypes", "system", "popen"}
        for source in sorted(p for p in PACKAGE.rglob("*.py") if "tests" not in p.parts):
            for node in ast.walk(ast.parse(source.read_text(encoding="utf-8"))):
                name = node.id if isinstance(node, ast.Name) else node.attr if isinstance(node, ast.Attribute) else ""
                self.assertNotIn(name, banned, f"{source.name}:{getattr(node, 'lineno', '?')}: {name}")

    def test_readme_documents_stable_api_and_errors(self):
        text = (PACKAGE / "README.md").read_text(encoding="utf-8")
        for term in ("knowledge-delta/1", "content_fingerprint", "BEGIN IMMEDIATE", "ingest", "query", "stats", "export",
                     "INVALID_DELTA", "SECRET_SHAPE", "historical", "unchanged_since:"):
            self.assertIn(term, text)

    def test_package_copy_passes_its_own_suite_from_an_unrelated_directory(self):
        if os.environ.get("BT_KNOWLEDGE_ISOLATED_COPY"):
            self.skipTest("copy verification runs only once")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copied = root / "bt_knowledge"
            shutil.copytree(PACKAGE, copied, ignore=shutil.ignore_patterns("__pycache__"))
            outside = root / "outside"
            outside.mkdir()
            result = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(copied / "tests")],
                                    cwd=outside, env={"PATH": "/usr/bin:/bin", "PYTHONPATH": str(root),
                                                     "BT_KNOWLEDGE_ISOLATED_COPY": "1"},
                                    text=True, capture_output=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
