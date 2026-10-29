"""What a durable M6 check inherits (REQ-030): under `verifier.inherit_env` the operator's environment reaches the
checks, but never the engine's own variables (its database URL) nor the names that point at the host session's devices
and sockets. `VK_DRIVER_FILES` naming the host's GPU driver kept Chromium's software WebGL from starting in the sandbox
(pictures REQ-021 T3.11). Real bubblewrap sandbox through the M6 runner.

    PYTHONPATH=skill/scripts:skill/scripts/tests uv run python -m unittest test_durable_m6_env
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from bt_durable.adapters.m6 import sandbox_policy
from bt_scheduler_quality.policy import CheckSpec, QualityPolicy
from bt_scheduler_quality.runner import SandboxRunner
from bt_scheduler_quality.runner_sandbox_process import sandbox_available

DB_URL = "postgresql://engine:not-a-real-password@127.0.0.1:5435/bt_durable"
INHERITED = (("VK_DRIVER_FILES", "/usr/share/vulkan/icd.d/intel_icd.json"), ("BT_DURABLE_DATABASE_URL", DB_URL),
             ("DBOS_SYSTEM_DATABASE_URL", DB_URL), ("INVOCATION_ID", "0123456789abcdef"), ("WAYLAND_DISPLAY", "wayland-1"),
             ("PICTURES_FLAG", "kept"))


@unittest.skipUnless(sandbox_available(QualityPolicy()), "bubblewrap is not available")
class CheckEnvironment(unittest.TestCase):
    def setUp(self):
        self.policy = QualityPolicy(environment=(("EXPLICIT_SETTING", "from-the-env-file"),),
                                    ambient_environment=INHERITED, secret_values=(DB_URL,), toolchain=False)
        self.snapshot = Path(tempfile.mkdtemp(prefix="bt-m6-env-", dir=os.environ.get("BT_LAB_DIR") or None))
        (self.snapshot / "README.md").write_text("snapshot\n")

    def environment_seen(self, policy: QualityPolicy) -> dict[str, str]:
        check = CheckSpec(id="ENV", kind="command", command="env", argv=("env",), cwd=".", purpose="environment")
        out = SandboxRunner(policy).run(check, self.snapshot)
        self.assertEqual(out.status, "pass", out)
        lines = (out.stdout or b"").decode("utf-8", "replace").splitlines()
        return dict(line.split("=", 1) for line in lines if "=" in line)

    def test_engine_and_host_session_names_never_reach_a_check(self):
        seen = self.environment_seen(sandbox_policy(self.policy))
        self.assertEqual((seen.get("PICTURES_FLAG"), seen.get("EXPLICIT_SETTING")), ("kept", "from-the-env-file"))
        for name in ("VK_DRIVER_FILES", "BT_DURABLE_DATABASE_URL", "DBOS_SYSTEM_DATABASE_URL", "INVOCATION_ID",
                     "WAYLAND_DISPLAY"):
            self.assertNotIn(name, seen)

    def test_without_the_filter_the_runner_passes_them_through(self):
        seen = self.environment_seen(self.policy)                      # negative control: the runner itself
        self.assertEqual(seen.get("VK_DRIVER_FILES"), "/usr/share/vulkan/icd.d/intel_icd.json")
        self.assertIn("BT_DURABLE_DATABASE_URL", seen)

    def test_a_policy_without_inherited_names_is_returned_unchanged(self):
        plain = QualityPolicy(environment=(("EXPLICIT_SETTING", "x"),))
        self.assertIs(sandbox_policy(plain), plain)


if __name__ == "__main__":
    unittest.main()
