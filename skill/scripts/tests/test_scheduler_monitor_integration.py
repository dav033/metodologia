"""M4's single methodology import boundary, public API, CLI, and installed package wiring."""
from __future__ import annotations

import ast
import sys
import tomllib
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
REPO = SCRIPTS.parent.parent
sys.path.insert(0, str(SCRIPTS))

import bt_scheduler_monitor_adapter as monitor_adapter


class SchedulerMonitorBoundaryTests(unittest.TestCase):
    def _imports(self, path: Path) -> set[str]:
        found: set[str] = set()
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                found.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and not node.level:
                found.add((node.module or "").split(".")[0])
        return found

    def _module_imports(self, path: Path) -> set[str]:
        found: set[str] = set()
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                found.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and not node.level:
                found.add(node.module or "")
        return found

    def test_only_methodology_monitor_adapter_imports_the_m4_package(self):
        offenders = []
        for path in sorted(SCRIPTS.rglob("*.py")):
            if "tests" in path.parts or "bt_scheduler_monitor" in path.relative_to(SCRIPTS).parts:
                continue
            if "bt_scheduler_monitor" in self._imports(path) and path.name != "bt_scheduler_monitor_adapter.py":
                offenders.append(str(path.relative_to(REPO)))
        self.assertEqual(offenders, [])
        self.assertIn("bt_scheduler_monitor", self._imports(SCRIPTS / "bt_scheduler_monitor_adapter.py"))
        self.assertIn("bt_scheduler_monitor_adapter", self._imports(SCRIPTS / "bt_scheduler_m4_stream_bridge.py"))
        self.assertIn("bt_scheduler_monitor_adapter", self._imports(SCRIPTS / "bt_scheduler_monitor_recovery.py"))

    def test_m1_m2_m3_and_operator_apis_are_exposed_by_the_adapter(self):
        for name in ("REQUIRED_M1_CONTRACT", "IncidentDeliveryReport", "deliver_incident_outbox",
                     "read_metric_snapshots", "operator_query", "ExecutionOutputFrame", "ProcessIdentity",
                     "BoundedFrameQueue", "create_stream_adapter"):
            self.assertTrue(hasattr(monitor_adapter, name), name)
        self.assertIn("bt_scheduler_monitor_adapter", self._imports(SCRIPTS / "bt_scheduler_stream_adapter.py"))
        self.assertIn("bt_scheduler_monitor_adapter", self._imports(SCRIPTS / "bt_scheduler_decision_adapter.py"))

    def test_scheduler_state_writers_remain_in_their_owner_modules(self):
        owners = {
            "bt_scheduler_" + "core.sqlite_repository": "class SqliteRepository",
            "bt_scheduler_" + "decision.recorder": "class DecisionLedger",
            "bt_scheduler_" + "executor.ledger": "class Ledger",
        }
        for module, owner_class in owners.items():
            path = SCRIPTS / Path(*module.split("."))
            source = path.with_suffix(".py").read_text(encoding="utf-8")
            with self.subTest(module=module):
                self.assertIn(owner_class, source)

        m4_paths = [path for path in (SCRIPTS / "bt_scheduler_monitor").rglob("*.py")
                    if "tests" not in path.relative_to(SCRIPTS / "bt_scheduler_monitor").parts]
        m4_paths.extend(SCRIPTS / name for name in (
            "bt_scheduler_monitor_adapter.py", "bt_scheduler_stream_adapter.py", "bt_cli_scheduler_monitor.py",
        ))
        forbidden = set(owners)
        for path in m4_paths:
            imports = self._module_imports(path)
            with self.subTest(path=path.relative_to(SCRIPTS)):
                self.assertFalse(any(name in forbidden or any(name.startswith(owner + ".") for owner in forbidden)
                                     for name in imports),
                                 f"M4 must use owner APIs, not import state writer modules: {path.name}")

    def test_root_pyproject_installs_the_package_adapters_and_methodology_cli(self):
        config = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
        setuptools = config["tool"]["setuptools"]
        self.assertIn("bt_scheduler_monitor", setuptools["packages"])
        self.assertIn("README.md", setuptools["package-data"]["bt_scheduler_monitor"])
        modules = setuptools["py-modules"]
        self.assertIn("bt_scheduler_monitor_adapter", modules)
        self.assertIn("bt_scheduler_stream_adapter", modules)
        self.assertIn("bt_cli_scheduler_monitor", modules)
        self.assertEqual(config["project"]["scripts"]["bt-scheduler-monitor"],
                         "bt_cli_scheduler_monitor:main")


if __name__ == "__main__":
    unittest.main()
