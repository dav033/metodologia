"""The hooks, the bitácora CLI and the legacy runtime run under the system interpreter, which has no third-party
packages (REQ-030 M0). Only bt_contracts, bt_supervisor and bt_durable may import them, and nothing on the legacy
path may import those packages at module level."""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
THIRD_PARTY = ("pydantic", "pydantic_core", "dbos", "psutil", "sqlalchemy", "psycopg", "structlog", "hypothesis")
NEW_PACKAGES = ("bt_contracts", "bt_supervisor", "bt_durable")
LEGACY_ENTRYPOINTS = ("bitacora", "bt_hooks", "bt_scheduler_run", "bt_scheduler_watch", "bt_scheduler_ops",
                      "bt_server", "bt_remote_api", "bt_remote_snapshot", "bt_remote_commands", "bt_remote_events",
                      "bt_remote_recovery", "bt_route_pins", "bt_page_flow_review", "file_guard")
# The gateway and the Telegram bot run under the VPS system interpreter (remote/deploy/deploy.sh): stdlib only.
GATEWAY = SCRIPTS.parents[1] / "remote" / "gateway"
GATEWAY_MODULES = ("main", "app", "server", "stream", "notifications", "telegram_bot", "bot_main", "read_routes",
                   "panel_proxy")

PROBE = """
import importlib.abc, sys
BLOCKED = {blocked!r}
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path=None, target=None):
        if name.split(".")[0] in BLOCKED:
            raise ImportError(f"third-party or new-runtime import on the stdlib path: {{name}}")
        return None
sys.meta_path.insert(0, Block())
sys.path.insert(0, {scripts!r})
import importlib
for module in {modules!r}:
    importlib.import_module(module)
print("ok")
"""


class StdlibBoundary(unittest.TestCase):
    def test_legacy_entrypoints_import_without_third_party_packages(self):
        code = PROBE.format(blocked=set(THIRD_PARTY + NEW_PACKAGES), scripts=str(SCRIPTS), modules=LEGACY_ENTRYPOINTS)
        done = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True, timeout=120)
        self.assertEqual(done.returncode, 0, done.stderr[-3000:])
        self.assertIn("ok", done.stdout)

    def test_gateway_and_telegram_bot_import_without_third_party_packages(self):
        code = PROBE.format(blocked=set(THIRD_PARTY + NEW_PACKAGES), scripts=str(GATEWAY), modules=GATEWAY_MODULES)
        done = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True, timeout=120)
        self.assertEqual(done.returncode, 0, done.stderr[-3000:])
        self.assertIn("ok", done.stdout)


if __name__ == "__main__":
    unittest.main()
