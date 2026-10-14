"""Routing characterization through the CLI (REQ-007 T8, gate G6, characterization half only).

Pins today's routing gates with fake provider binaries and throwaway state: account sharing, work-only gates,
cooldowns, audit order and fixed-provider budgets. The bounded cold-start scheduling change of T8 is NOT here: it is
a behavior change blocked by D-014 until the owner ratifies the ADR.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skill" / "scripts" / "bitacora.py"


class RoutingCase(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory(prefix="routing-parity-")
        self.addCleanup(temp.cleanup)
        self.tmp = Path(temp.name)
        for name in ("bin", "home", "work"):
            (self.tmp / name).mkdir()
        for binary in ("claude", "codex"):
            fake = self.tmp / "bin" / binary
            fake.write_text("#!/bin/sh\nexit 0\n")
            fake.chmod(0o755)
        self.env = {"PATH": f"{self.tmp / 'bin'}:/usr/bin:/bin", "HOME": str(self.tmp / "home"),
                    "BITACORA_ROOT": str(self.tmp / "bit"), "PYTHONDONTWRITEBYTECODE": "1"}
        self.cli("init")
        (self.tmp / "bit" / ".state").mkdir(exist_ok=True)

    def cli(self, *args: str, project: str | None = "demo", check: bool = True):
        command = [sys.executable, str(SCRIPT)] + (["--project", project] if project else []) + list(args)
        done = subprocess.run(command, capture_output=True, text=True, env=self.env, cwd=self.tmp / "work", timeout=60)
        if check:
            self.assertEqual(done.returncode, 0, f"{args}: {done.stderr}")
        return done

    def route(self, kind: str = "implement", tier: str = "0") -> dict:
        return json.loads(self.cli("agents", "route", "--kind", kind, "--tier", tier).stdout)

    def cool(self, key: str, seconds: int = 3600) -> None:
        path = self.tmp / "bit" / ".state" / "quota.json"
        data = json.loads(path.read_text()) if path.exists() else {}
        now = time.time()
        data[key] = {"until": now + seconds, "at": now, "streak": 1, "model": "x", "reason": "fixture"}
        path.write_text(json.dumps(data))


class RoutingParityTests(RoutingCase):
    def test_audit_without_other_signals_goes_to_claude_sonnet_medium(self) -> None:
        route = self.route("audit", "1")
        self.assertEqual((route["agent"], route["model"], route["effort"]), ("claude", "sonnet", "medium"))

    def test_audit_falls_back_to_codex_sol_medium_when_claude_is_cooling(self) -> None:
        self.cool("claude:default")
        route = self.route("audit", "1")
        self.assertEqual((route["agent"], route["model"], route["effort"]), ("codex", "gpt-6.1-sol", "medium"))

    def test_audit_budget_never_inherits_builder_xhigh(self) -> None:
        for tier in ("0", "1"):
            route = self.route("audit", tier)
            self.assertNotIn(route["effort"], ("xhigh", "max"))

    def test_escalated_audit_uses_high_not_xhigh(self) -> None:
        route = self.route("audit", "2")
        self.assertEqual((route["agent"], route["model"], route["effort"]), ("claude", "opus", "high"))

    def test_every_account_cooling_is_reported_not_silently_routed(self) -> None:
        self.cool("claude:default")
        self.cool("codex:default")
        done = self.cli("agents", "route", "--kind", "implement", "--tier", "0", check=False)
        self.assertNotEqual(done.returncode, 0)
        self.assertNotIn('"profile"', done.stdout)

    def test_work_only_profile_is_never_chosen_for_a_personal_project(self) -> None:
        self.cli("profiles", "add", "claude-work-fixture", "--provider", "claude", "--work-only",
                 "--env", f"CLAUDE_CONFIG_DIR={self.tmp / 'work-config'}", project=None)
        # make the personal accounts unavailable: the work-only one must still not be used
        self.cool("claude:default")
        self.cool("codex:default")
        done = self.cli("agents", "route", "--kind", "implement", "--tier", "0", check=False)
        self.assertNotEqual(done.returncode, 0, "a work-only account served a non-work project")

    def test_two_profile_ids_for_one_account_share_a_cooldown(self) -> None:
        config = self.tmp / "same-account"
        for name in ("alias-one", "alias-two"):
            self.cli("profiles", "add", name, "--provider", "claude", "--env", f"CLAUDE_CONFIG_DIR={config}",
                     project=None)
        listing = self.cli("agents", "list").stdout
        self.assertIn("alias-one", listing)
        probe = ("import sys; sys.path.insert(0, %r); import bt_agents;"
                 "print(bt_agents.account_key('alias-one') == bt_agents.account_key('alias-two'),"
                 "bt_agents.account_key('alias-one') == bt_agents.account_key('claude'))" % str(SCRIPT.parent))
        done = subprocess.run([sys.executable, "-I", "-c", probe], capture_output=True, text=True, env=self.env)
        self.assertEqual(done.stdout.split(), ["True", "False"], done.stderr)

    def test_unknown_usage_is_labelled_unknown_never_zero(self) -> None:
        self.assertIn("unknown", self.route("audit", "1")["why"])


if __name__ == "__main__":
    unittest.main()
