"""Verify the methodology boundary around the standalone knowledge package."""
from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
REPO = SCRIPTS.parent.parent
PACKAGE = SCRIPTS / "bt_knowledge"


def imports(path: Path) -> set[str]:
    found = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            found.add(node.module.split(".")[0])
    return found


class Boundary(unittest.TestCase):
    def test_only_the_adapter_imports_the_knowledge_package(self):
        consumers = [path.name for path in sorted(SCRIPTS.glob("*.py")) if "bt_knowledge" in imports(path)]
        self.assertEqual(consumers, ["bt_knowledge_adapter.py"])

    def test_the_knowledge_package_imports_no_methodology_modules(self):
        allowed = set(sys.stdlib_module_names) | {"bt_knowledge"}
        for path in sorted(PACKAGE.rglob("*.py")):
            with self.subTest(source=path.relative_to(PACKAGE)):
                self.assertLessEqual(imports(path), allowed)

    def test_knowledge_suite_passes_in_an_isolated_subprocess(self):
        code = (
            "import sys, unittest\n"
            f"sys.path.insert(0, {str(SCRIPTS)!r})\n"
            f"suite = unittest.defaultTestLoader.discover({str(PACKAGE / 'tests')!r})\n"
            "result = unittest.TextTestRunner(verbosity=2).run(suite)\n"
            "raise SystemExit(not result.wasSuccessful())\n"
        )
        result = subprocess.run([sys.executable, "-I", "-c", code], cwd=REPO, text=True, capture_output=True,
                                timeout=180)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class KnowledgeCli(unittest.TestCase):
    def test_ingest_and_json_query_round_trip_under_temporary_bitacora_root(self):
        with tempfile.TemporaryDirectory(prefix="knowledge-cli-") as temp:
            root = Path(temp) / "bitacora"
            delta_path = Path(temp) / "delta.json"
            delta_path.write_text(json.dumps({
                "schema": "knowledge-delta/1",
                "project": "sample",
                "repository": "app",
                "observed_commit": "a" * 40,
                "contributor": "integration-test",
                "observations": [{
                    "subject": "module:checkout",
                    "relation": "CONSUMES",
                    "object": "contract:auth",
                    "status": "observed",
                    "evidence": ["src/checkout.py:12"],
                }],
            }), encoding="utf-8")
            env = dict(os.environ, BITACORA_ROOT=str(root))
            command = [sys.executable, str(SCRIPTS / "bitacora.py"), "--project", "sample", "knowledge"]
            ingested = subprocess.run([*command, "ingest", str(delta_path), "--json"], cwd=REPO, env=env,
                                      text=True, capture_output=True, timeout=30)
            self.assertEqual(ingested.returncode, 0, ingested.stdout + ingested.stderr)
            self.assertEqual(json.loads(ingested.stdout)["relations_added"], 1)

            queried = subprocess.run([*command, "query", "--json"], cwd=REPO, env=env, text=True,
                                     capture_output=True, timeout=30)
            self.assertEqual(queried.returncode, 0, queried.stdout + queried.stderr)
            rows = json.loads(queried.stdout)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["subject"], "module:checkout")
            self.assertEqual(rows[0]["object"], "contract:auth")


if __name__ == "__main__":
    unittest.main()
