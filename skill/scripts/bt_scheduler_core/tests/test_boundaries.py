"""The module's isolation contract: standard library + itself only, no knowledge of the rest of the methodology,
and (SC-AC01/02) no AI of any kind inside the package."""
from __future__ import annotations

import ast
import re
import sys
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1]
EXEMPT = {Path(__file__).resolve().name, "test_isolation.py", "test_no_ai.py"}  # they name the forbidden things to check
STDLIB = set(sys.stdlib_module_names)
ALLOWED_LOCAL = {"bt_scheduler_core", "support"}

DYNAMIC_NAMES = {"eval", "exec", "__import__", "import_module", "getenv", "environ", "environb", "putenv", "system",
                 "popen", "ctypes", "load_module", "find_spec"}


def imports(path: Path) -> list[tuple[str, int, int]]:
    found = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            found += [(alias.name.split(".")[0], 0, node.lineno) for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            found.append(((node.module or "").split(".")[0], node.level, node.lineno))
    return found


def code_violations(source: str) -> list[str]:
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
            found.append(f"line {node.lineno}: compile() builtin")
        if isinstance(node, ast.Attribute) and node.attr in ("parents", "sleep"):
            found.append(f"line {node.lineno}: .{node.attr} (tree climbing / busy waiting)")
    return found


class Boundaries(unittest.TestCase):
    def sources(self) -> list[Path]:
        return sorted(p for p in MODULE.rglob("*.py") if "__pycache__" not in p.parts)

    def package_sources(self) -> list[Path]:
        return [p for p in self.sources() if "tests" not in p.relative_to(MODULE).parts]

    def test_sources_exist(self):
        names = {p.name for p in self.package_sources()}
        self.assertTrue({"plan.py", "states.py", "scheduler.py", "contracts.py", "repository.py", "sqlite_repository.py",
                         "reservation.py", "dispatch.py", "events.py", "recovery.py", "cli.py"} <= names)

    def test_only_standard_library_and_the_package_itself_are_imported(self):
        for path in self.sources():
            for name, level, line in imports(path):
                if level:
                    continue
                self.assertTrue(name in STDLIB or name in ALLOWED_LOCAL, f"{path.relative_to(MODULE)}:{line} imports {name!r}")

    def test_package_code_never_imports_its_own_tests(self):
        for path in self.package_sources():
            for name, _l, line in imports(path):
                self.assertNotEqual(name, "support", f"{path.name}:{line}")

    def test_relative_imports_do_not_climb_out_of_the_package(self):
        for path in self.sources():
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.ImportFrom) and node.level:
                    self.assertEqual(node.level, 1, f"{path.name}:{node.lineno}")

    def test_no_knowledge_of_the_rest_of_the_methodology(self):
        forbidden = re.compile(r"bitacora|RUN\.json|HANDOFF|bt_(?!scheduler_core)\w+|~/|/home/|\.claude", re.IGNORECASE)
        for path in self.sources():
            if path.name in EXEMPT:
                continue
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                hit = forbidden.search(line)
                self.assertIsNone(hit, f"{path.relative_to(MODULE)}:{number} mentions {hit and hit.group(0)!r}")

    def test_no_ai_vocabulary_in_package_code(self):
        """SC-AC01: no SDK, prompt, provider or model name anywhere in the package's code."""
        forbidden = re.compile(r"anthropic|openai|gemini|claude|codex|gpt|langchain|\bllm\b|sonnet|opus|haiku|prompt|"
                               r"tokens?_used|embedding", re.IGNORECASE)
        for path in self.package_sources():
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                hit = forbidden.search(line)
                self.assertIsNone(hit, f"{path.relative_to(MODULE)}:{number} mentions {hit and hit.group(0)!r}")

    def test_no_environment_dynamic_import_tree_climbing_or_sleep_in_package_code(self):
        for path in self.package_sources():
            self.assertEqual(code_violations(path.read_text(encoding="utf-8")), [], path.name)

    def test_no_network_or_process_modules_in_package_code(self):
        banned = {"socket", "urllib", "http", "subprocess", "multiprocessing", "ctypes", "importlib", "pickle", "ssl",
                  "asyncio", "concurrent"}
        for path in self.package_sources():
            self.assertEqual({n for n, _l, _x in imports(path)} & banned, set(), path.name)

    def test_only_the_sqlite_repository_touches_files_or_sqlite(self):
        for path in self.package_sources():
            text = path.read_text(encoding="utf-8")
            touches = [w for w in ("write_text", "write_bytes", "os.replace", "unlink", "mkdir", "chmod", "sqlite3")
                       if w in text] + (["open("] if re.search(r"(?<![\w.])open\(", text) else [])
            if path.name == "sqlite_repository.py":
                continue
            self.assertEqual(touches, [], path.name)

    def test_the_plan_is_opened_for_reading_only(self):
        self.assertIn("read_bytes", (MODULE / "plan.py").read_text(encoding="utf-8"))

    def test_the_detector_catches_each_known_evasion(self):
        samples = {"environ via os": "import os\nX = os.environ", "getenv aliased": "from os import getenv\nX = getenv('A')",
                   "eval": "X = eval('1')", "exec": "exec('pass')", "dunder import": "m = __import__('x')",
                   "import_module": "import importlib\nm = importlib.import_module('x')",
                   "parents climb": "from pathlib import Path\nX = Path(__file__).parents[3]",
                   "os.system": "import os\nos.system('ls')", "sleep": "import time\ntime.sleep(1)",
                   "compile builtin": "c = compile('1', 'x', 'eval')"}
        for label, source in samples.items():
            with self.subTest(label=label):
                self.assertTrue(code_violations(source), label)
        self.assertEqual(code_violations("import re\nR = re.compile('a')"), [])

    def test_the_import_check_catches_third_party_and_foreign_modules(self):
        with tempfile.TemporaryDirectory() as tmp:
            for source in ("import requests", "from bt_core import X", "import bt_runstate as r", "from numpy import a"):
                f = Path(tmp) / "m.py"
                f.write_text(source + "\n", encoding="utf-8")
                names = {n for n, level, _ in imports(f) if not level}
                self.assertFalse(names <= (STDLIB | ALLOWED_LOCAL), source)

    def test_every_source_file_stays_reviewable(self):
        for path in self.sources():
            self.assertLessEqual(len(path.read_text(encoding="utf-8").splitlines()), 500, path.name)


if __name__ == "__main__":
    unittest.main()
