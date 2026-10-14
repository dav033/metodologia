"""`bitacora_platform.<name>` aliases the flat `bt_<name>` modules without a second module instance (D-014).

Checked in subprocesses with a throwaway BITACORA_ROOT: importing bt_core in this process would freeze ROOT before
the legacy isolation test can set it.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "skill" / "scripts"

PROBE = r"""
import json, sys
sys.path.insert(0, %r)
import bitacora_platform.core as alias_core, bt_core
import bitacora_platform.agents as alias_agents, bt_agents
from bitacora_platform import config as alias_config
import bt_config
result = {
    "same_core": alias_core is bt_core, "same_agents": alias_agents is bt_agents, "same_config": alias_config is bt_config,
    "spec_name": bt_core.__spec__.name, "module_name": bt_core.__name__,
    "root_shared": alias_core.ROOT is bt_core.ROOT,
}
bt_core.MARKER = "patched-through-flat-name"
result["patch_visible"] = alias_core.MARKER
try:
    import bitacora_platform.not_a_module
except ModuleNotFoundError:
    result["unknown"] = "ModuleNotFoundError"
print(json.dumps(result))
"""


class NamespaceAliasTests(unittest.TestCase):
    def test_alias_is_the_same_module_object_and_keeps_its_own_spec(self) -> None:
        with tempfile.TemporaryDirectory(prefix="alias-") as temp:
            env = {"PATH": os.environ.get("PATH", ""), "HOME": temp, "BITACORA_ROOT": str(Path(temp) / "b"),
                   "PYTHONDONTWRITEBYTECODE": "1"}
            done = subprocess.run([sys.executable, "-I", "-c", PROBE % str(SCRIPTS)], capture_output=True,
                                  text=True, env=env, cwd=temp, timeout=60)
        self.assertEqual(done.returncode, 0, done.stderr)
        result = json.loads(done.stdout)
        self.assertTrue(result["same_core"] and result["same_agents"] and result["same_config"])
        self.assertEqual((result["spec_name"], result["module_name"]), ("bt_core", "bt_core"))
        self.assertTrue(result["root_shared"])
        self.assertEqual(result["patch_visible"], "patched-through-flat-name")
        self.assertEqual(result["unknown"], "ModuleNotFoundError")


if __name__ == "__main__":
    unittest.main()
