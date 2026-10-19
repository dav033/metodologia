"""The module's isolation contract: standard library + itself only, no knowledge of the rest of the methodology."""
from __future__ import annotations

import ast
import re
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1]
# This file and test_isolation.py name the forbidden things on purpose, to check for their absence.
EXEMPT = {Path(__file__).resolve().name, "test_isolation.py"}
STDLIB = set(sys.stdlib_module_names)
ALLOWED_LOCAL = {"bt_planner", "support"}  # the package itself and the tests' own helper


def imports(path: Path) -> list[tuple[str, int, int]]:
    """(top-level module, relative level, line) for every import statement in a file."""
    found = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            found += [(alias.name.split(".")[0], 0, node.lineno) for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            found.append(((node.module or "").split(".")[0], node.level, node.lineno))
    return found


DYNAMIC_NAMES = {"eval", "exec", "__import__", "import_module", "getenv", "environ", "environb",
                 "putenv", "system", "popen", "ctypes", "load_module", "find_spec"}


def code_violations(source: str, *, allow_file_dir: bool = False) -> list[str]:
    """Things package code must not do, found on the AST so aliasing cannot hide them: environment access, dynamic
    imports/evaluation, subprocess-like calls, and reaching up the directory tree from __file__ (`parents[N]`)."""
    found = []
    for node in ast.walk(ast.parse(source)):
        names = []
        if isinstance(node, ast.Name):
            names = [node.id]
        elif isinstance(node, ast.Attribute):
            names = [node.attr]
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [a.name.split(".")[-1] for a in node.names] + [(getattr(node, "module", None) or "").split(".")[-1]]
        elif isinstance(node, ast.alias):
            names = [node.name.split(".")[-1]]
        found += [f"line {getattr(node, 'lineno', '?')}: {n}" for n in names if n in DYNAMIC_NAMES]
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "compile":
            found.append(f"line {node.lineno}: compile() builtin")  # re.compile is an attribute and is fine
        if isinstance(node, ast.Attribute) and node.attr == "parents":
            found.append(f"line {node.lineno}: .parents (climbs the directory tree)")
    return found


class Boundaries(unittest.TestCase):
    def sources(self) -> list[Path]:
        return sorted(p for p in MODULE.rglob("*.py") if "__pycache__" not in p.parts)

    def test_sources_exist(self):
        names = {p.name for p in self.sources()}
        self.assertTrue({"contract.py", "revisions.py", "sync.py", "markdown.py", "cli.py", "_lock.py"} <= names)

    def test_only_standard_library_and_the_package_itself_are_imported(self):
        for path in self.sources():
            for name, level, line in imports(path):
                where = f"{path.relative_to(MODULE)}:{line}"
                if level:
                    continue  # relative imports stay inside the package by construction
                self.assertTrue(name in STDLIB or name in ALLOWED_LOCAL, f"{where} imports {name!r}")

    def test_package_code_never_imports_its_own_tests_or_helpers(self):
        for path in self.sources():
            if "tests" in path.relative_to(MODULE).parts:
                continue
            for name, _level, line in imports(path):
                self.assertNotEqual(name, "support", f"{path.name}:{line}")

    def test_relative_imports_do_not_climb_out_of_the_package(self):
        for path in self.sources():
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.ImportFrom) and node.level:
                    self.assertEqual(node.level, 1, f"{path.name}:{node.lineno} climbs above the package")

    def test_no_knowledge_of_the_rest_of_the_methodology(self):
        forbidden = re.compile(r"bitacora|RUN\.json|HANDOFF|bt_(?!planner)\w+|~/|/home/|\.claude", re.I)
        for path in self.sources():
            if path.name in EXEMPT:
                continue
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                hit = forbidden.search(line)
                self.assertIsNone(hit, f"{path.relative_to(MODULE)}:{number} mentions {hit and hit.group(0)!r}")

    def test_no_environment_dynamic_import_or_tree_climbing_in_package_code(self):
        for path in self.sources():
            if "tests" in path.relative_to(MODULE).parts:
                continue
            self.assertEqual(code_violations(path.read_text(encoding="utf-8")), [], path.name)

    def test_no_network_or_process_modules_in_package_code(self):
        banned = {"socket", "urllib", "http", "subprocess", "multiprocessing", "ctypes", "importlib", "pickle"}
        for path in self.sources():
            if "tests" in path.relative_to(MODULE).parts:
                continue
            used = {name for name, _level, _line in imports(path)}
            self.assertEqual(used & banned, set(), path.name)

    def test_the_detector_itself_catches_each_known_evasion(self):
        samples = {
            "environ via os": "import os\nX = os.environ",
            "environ aliased": "from os import environ as E\nX = E",
            "getenv aliased": "from os import getenv\nX = getenv('A')",
            "eval": "X = eval('1')",
            "exec": "exec('pass')",
            "dunder import": "m = __import__('bt_core')",
            "import_module": "import importlib\nm = importlib.import_module('x')",
            "parents climb": "from pathlib import Path\nX = Path(__file__).parents[3]",
            "os.system": "import os\nos.system('ls')",
            "ctypes": "import ctypes",
            "compile builtin": "c = compile('1', 'x', 'eval')",
        }
        for label, source in samples.items():
            with self.subTest(label=label):
                self.assertTrue(code_violations(source), f"not detected: {label}")
        self.assertEqual(code_violations("from pathlib import Path\nX = Path(__file__).resolve().parent / 'data'"), [])
        self.assertEqual(code_violations("import re\nR = re.compile('a')"), [])

    def test_the_import_check_catches_third_party_and_foreign_modules(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            for source in ("import requests", "from bt_core import X", "import bt_runstate as r", "from numpy import a"):
                f = Path(tmp) / "m.py"
                f.write_text(source + "\n", encoding="utf-8")
                names = {n for n, level, _ in imports(f) if not level}
                self.assertFalse(names <= (STDLIB | ALLOWED_LOCAL), source)

    def test_writes_are_confined_to_the_documented_places(self):
        writers = {}
        for path in self.sources():
            if "tests" in path.relative_to(MODULE).parts:
                continue
            text = path.read_text(encoding="utf-8")
            writers[path.name] = [w for w in ("write_text", "os.replace", "open(", "unlink", "mkdir", "chmod")
                                  if w in text]
        self.assertEqual(sorted(name for name, hits in writers.items() if hits),
                         ["_lock.py", "amendments.py", "revisions.py", "sync.py"])   # amendments: PLAN.amendments.jsonl


if __name__ == "__main__":
    unittest.main()
