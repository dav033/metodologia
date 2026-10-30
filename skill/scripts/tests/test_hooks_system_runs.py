"""A session the system started for one task never gets the bitácora's chores from the hooks (D-168: pictures REQ-021
T93's durable attempt read the bitácora's secret alert at its Stop hook and committed a gitleaks exemption into the
methodology's repository)."""
from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bt_hooks
import bt_secrets
from bt_core import ROOT


class SystemRuns(unittest.TestCase):
    def setUp(self):
        bt_secrets.set_alert(ROOT, "Finding: REDACTED")
        self.addCleanup(bt_secrets.clear_alert, ROOT)

    def stop(self, **env) -> str:
        out = io.StringIO()
        clean = {k: v for k, v in os.environ.items() if k not in bt_hooks.SYSTEM_RUN}
        with patch.dict(os.environ, {**clean, **env}, clear=True), \
                patch("sys.stdin", io.StringIO(json.dumps({"session_id": "s1", "cwd": str(ROOT)}))), \
                patch.object(bt_hooks, "resolve_project", return_value=None), contextlib.redirect_stdout(out):
            bt_hooks.hook_stop("codex")
        return out.getvalue()

    def test_the_secret_alert_reaches_the_owners_sessions_only(self):
        self.assertIn("possible secret", self.stop())
        self.assertEqual(self.stop(BITACORA_ATTEMPT="pictures-REQ-021-r24-T93-a3-04b33f7d"), "")
        self.assertEqual(self.stop(BITACORA_TASK="T93"), "")
        self.assertEqual(self.stop(BITACORA_DELEGATION="D-1"), "")
        self.assertEqual(self.stop(BITACORA_AGENT_ROLE="planner"), "")        # D-237: the Planner committed on main

    def test_a_role_session_cannot_resolve_the_alert_with_a_commit(self):
        import subprocess
        env = {**os.environ, "BITACORA_AGENT_ROLE": "planner", "BITACORA_ROOT": str(ROOT)}
        done = subprocess.run([sys.executable, str(Path(bt_hooks.__file__).with_name("bitacora.py")), "commit",
                               "fix: remove secret"], env=env, capture_output=True, text=True, check=False)
        self.assertIn("REFUSED", done.stdout)

    def test_a_role_session_started_by_the_system_carries_its_role(self):
        import bt_agent_terminal
        seen = []
        with patch.object(bt_agent_terminal, "exists", return_value=False), \
                patch.object(bt_agent_terminal, "_run", side_effect=lambda *a, **k: seen.append(a) or
                             __import__("subprocess").CompletedProcess(a, 0, "", "")):
            bt_agent_terminal.start("bit-pictures-REQ-021-planner", Path("/tmp"), "true")
        self.assertIn("BITACORA_AGENT_ROLE=planner", seen[0])


if __name__ == "__main__":
    unittest.main()
