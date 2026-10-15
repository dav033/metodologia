"""R1: standard library + itself only; no knowledge of the rest of the methodology; no AI vocabulary in the code."""
from __future__ import annotations

import ast
import re
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1]
STDLIB = set(sys.stdlib_module_names)
ALLOWED_LOCAL = {"bt_scheduler_executor"}
TEST_LOCAL = {"support", "bt_scheduler_executor", "faults"}
SOURCES = sorted(p for p in MODULE.glob("*.py"))
TESTS = sorted(p for p in (MODULE / "tests").glob("*.py"))
# written in pieces so that this very file does not look like a user of the sibling modules to their boundary tests
FORBIDDEN_WORDS = tuple("bt_" + name for name in ("core", "runstate", "profiles", "agents", "driver", "worktree",
                                                 "scheduler_" + "core", "plan" + "ner", "scheduler_" + "decision")) \
    + ("bita" + "cora", "RUN" + ".json")
POLICY_NAMES = {"getenv", "environb", "eval", "exec", "__import__", "import_module", "ctypes"}


def imports(path: Path):
    found = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            found += [(a.name.split(".")[0], 0, node.lineno) for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            found.append(((node.module or "").split(".")[0], node.level, node.lineno))
    return found


class Boundaries(unittest.TestCase):
    def test_only_the_standard_library_and_the_package_itself_are_imported(self):
        for path in SOURCES:
            for name, level, line in imports(path):
                if level:
                    self.assertLessEqual(level, 1, f"{path.name}:{line} climbs out of the package")
                    continue
                self.assertTrue(name in STDLIB or name in ALLOWED_LOCAL, f"{path.name}:{line} imports {name}")

    def test_tests_import_only_the_standard_library_the_package_and_their_helpers(self):
        for path in TESTS:
            for name, level, line in imports(path):
                self.assertTrue(name in STDLIB or name in TEST_LOCAL or level, f"{path.name}:{line} imports {name}")

    def test_no_other_module_of_the_methodology_is_named_in_the_code(self):
        for path in SOURCES:
            code = path.read_text(encoding="utf-8")
            for word in FORBIDDEN_WORDS:
                self.assertNotIn(word, code, f"{path.name} names {word}")

    def test_no_environment_policy_and_no_dynamic_execution(self):
        for path in SOURCES:
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                name = node.id if isinstance(node, ast.Name) else node.attr if isinstance(node, ast.Attribute) else None
                if name in POLICY_NAMES:
                    self.fail(f"{path.name}:{node.lineno} uses {name}")

    def test_the_only_place_that_reads_the_ambient_environment_is_the_child_environment_builder(self):
        hits = [p.name for p in SOURCES if "os.environ" in p.read_text(encoding="utf-8")]
        self.assertEqual(sorted(hits), ["gitutil.py", "spawn.py"])

    def test_no_provider_or_model_is_named_in_the_code(self):
        pattern = re.compile(r"\b(claude|codex|gemini|antigravity|opus|sonnet|haiku|gpt)\b", re.I)
        for path in SOURCES:
            for number, text in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if text.lstrip().startswith(("#", '"""')):
                    continue
                code = text.split("#")[0]
                self.assertIsNone(pattern.search(code), f"{path.name}:{number} names a provider: {text.strip()[:80]}")

    def test_the_package_never_writes_outside_the_places_it_is_given(self):
        # the only absolute-path literals allowed are the proc/boot-id reads of the identity helpers
        for path in SOURCES:
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.startswith("/"):
                    self.assertTrue(node.value in ("/", "/stat", "/cmdline") or node.value.startswith(("/proc", "/dev/null")), f"{path.name}:{node.lineno} {node.value}")

    def test_every_source_file_is_small_enough_to_review(self):
        for path in SOURCES:
            self.assertLess(len(path.read_text(encoding="utf-8").splitlines()), 500, path.name)


if __name__ == "__main__":
    unittest.main()
