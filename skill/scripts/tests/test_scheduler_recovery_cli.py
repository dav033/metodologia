"""The public operational CLI inspects private M5 state without writing scheduler/legacy state."""
from __future__ import annotations

import ast
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from bt_scheduler_recovery import DecisionStore, RecoveryCase

SCRIPTS = Path(__file__).resolve().parents[1]


class RecoveryOperationalCLI(unittest.TestCase):
    def invoke(self, cwd, *args):
        script = (f"import sys,runpy;sys.path.insert(0,{str(SCRIPTS)!r});"
                  f"sys.argv=['bitacora']+{list(args)!r};runpy.run_module('bitacora',run_name='__main__')")
        return subprocess.run([sys.executable, "-I", "-B", "-c", script], cwd=cwd,
                              text=True, capture_output=True, timeout=15, check=False)

    def test_json_human_and_restart_inspection_do_not_change_store(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "private" / "history.db"
            case = RecoveryCase("run", "plan", 1, "a" * 64, "task", "attempt", 1, "execution_failed")
            with DecisionStore(path) as store:
                decision = store.decide(case)
            before = path.read_bytes()
            for _restart in range(2):
                for command in ("inspect", "metrics"):
                    for structured in (False, True):
                        arguments = ("--json",) if structured else ()
                        done = self.invoke(temporary, "recovery", command, "--store", str(path), *arguments)
                        self.assertEqual(done.returncode, 0, done.stderr)
                        if structured:
                            result = json.loads(done.stdout)
                            self.assertEqual(result["decisions"] if command == "metrics" else result["decision_id"],
                                             1 if command == "metrics" else decision.decision_id)
                        else:
                            self.assertIn("decisions:" if command == "metrics" else "reason_code:", done.stdout)
            self.assertEqual(path.read_bytes(), before)
            missing = Path(temporary) / "absent" / "history.db"
            done = self.invoke(temporary, "recovery", "inspect", "--store", str(missing), "--json")
            self.assertEqual(done.returncode, 2)
            self.assertEqual(json.loads(done.stdout)["error"], "STORE_MISSING")
            self.assertFalse(missing.parent.exists())

    def test_only_the_recovery_adapter_imports_the_m5_package_in_production(self):
        offenders = []
        for path in SCRIPTS.glob("*.py"):
            if path.name == "bt_scheduler_recovery_adapter.py":
                continue
            for node in ast.walk(ast.parse(path.read_text())):
                names = [alias.name for alias in node.names] if isinstance(node, ast.Import) else \
                    [node.module or ""] if isinstance(node, ast.ImportFrom) else []
                if any(name == "bt_scheduler_recovery" or name.startswith("bt_scheduler_recovery.") for name in names):
                    offenders.append((path.name, node.lineno))
        self.assertEqual(offenders, [])
