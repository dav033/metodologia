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


if __name__ == "__main__":
    unittest.main()
