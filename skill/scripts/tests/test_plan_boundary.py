"""Architecture boundary checks for the planner integration."""
from __future__ import annotations

import ast
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))
REPO = SCRIPTS.parent.parent

import bt_plan_adapter as adapter  # noqa: E402


class Boundary(unittest.TestCase):
    """The dependency points one way: methodology -> adapter -> bt_planner."""

    ALLOWED_USERS = {
        "bt_plan_adapter.py",
        "bt_remote_edit.py",     # remote edit-brief is a planner client: it applies plan revisions through bt_planner
        "test_remote_events.py", "test_remote_recovery.py",   # their fixtures build planner revisions
        "test_plan_adapter_evidence.py",
        "test_plan_boundary.py",
        "test_plan_integration.py",
        "test_package_install.py",
        "test_planblock.py",      # pins the contract between the generated status block and the planner's narrative digest
        "test_plan_bench.py",    # the benchmark harness is a planner client by design (see plan_bench below)
    }

    def top_imports(self, path: Path) -> set[str]:
        names = set()
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                names |= {alias.name.split(".")[0] for alias in node.names}
            elif isinstance(node, ast.ImportFrom) and not node.level:
                names.add((node.module or "").split(".")[0])
        return names

    def test_only_the_adapter_imports_the_module(self):
        offenders = []
        for path in sorted(REPO.rglob("*.py")):
            rel = path.relative_to(REPO)
            if (".git" in rel.parts or "bt_planner" in rel.parts or "node_modules" in rel.parts
                    or ".state" in rel.parts or ".venv" in rel.parts or path.name in self.ALLOWED_USERS
                    or "artifacts" in rel.parts or "plan_bench" in rel.parts or "build" in rel.parts):
                continue  # `.state` holds throwaway review snapshots (full copies of the tree, venv included);
                #           `artifacts` are experiment outputs of the bitácora (e.g. a model duel), not methodology code
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (SyntaxError, UnicodeError):
                continue
            for node in ast.walk(tree):
                names = set()
                if isinstance(node, ast.Import):
                    names = {a.name.split(".")[0] for a in node.names}
                elif isinstance(node, ast.ImportFrom) and not node.level:
                    names = {(node.module or "").split(".")[0]}
                elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                    names = {node.value.split(".")[0]}
                if "bt_planner" in names:
                    offenders.append(f"{rel}:{getattr(node, 'lineno', '?')}")
        self.assertEqual(offenders, [], "only bt_plan_adapter may reach the planner module")
        self.assertIn("bt_planner", self.top_imports(SCRIPTS / "bt_plan_adapter.py"))

    def test_the_module_imports_nothing_of_the_methodology(self):
        stdlib = set(sys.stdlib_module_names)
        for path in (SCRIPTS / "bt_planner").glob("*.py"):
            outside = {n for n in self.top_imports(path) if n and n not in stdlib and n != "bt_planner"}
            self.assertEqual(outside, set(), path.name)

    def test_the_old_scattered_modules_are_gone(self):
        for name in ("bt_plan_contract", "bt_plan_revisions", "bt_plan_sync"):
            self.assertFalse((SCRIPTS / f"{name}.py").exists(), name)

    def test_module_suite_passes_in_an_isolated_interpreter(self):
        done = subprocess.run(
            [sys.executable, "-I", "-m", "unittest", "discover", "-s", str(SCRIPTS / "bt_planner" / "tests")],
            capture_output=True, text=True, timeout=300, cwd=tempfile.gettempdir(),
            env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"},
        )
        self.assertEqual(done.returncode, 0, (done.stderr or done.stdout)[-1500:])
        self.assertRegex(done.stderr, r"Ran \d+ tests")

    def test_module_runs_as_a_command_from_a_lone_copy_with_no_methodology_reachable(self):
        import shutil
        with tempfile.TemporaryDirectory(prefix="planner-cmd-") as tmp:
            shutil.copytree(SCRIPTS / "bt_planner", Path(tmp) / "bt_planner",
                            ignore=shutil.ignore_patterns("__pycache__", "tests"))
            done = subprocess.run([
                sys.executable, "-I", "-c",
                "import sys; sys.path.insert(0, sys.argv[1]); from bt_planner.cli import main; "
                "import importlib.util as u; "
                "assert all(u.find_spec(m) is None for m in ('bt_core', 'bt_runstate', 'bitacora')); "
                "sys.exit(main(['example']))",
                tmp,
            ], capture_output=True, text=True, timeout=60, cwd=tempfile.gettempdir())
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn('"plan_id"', done.stdout)
