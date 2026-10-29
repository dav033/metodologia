"""The Planner runs on a Claude account with quota and leaves one that ran out, conversation included (REQ-021, 2026-10-29)."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bt_agent_terminal as terminal
import bt_agents
import bt_profiles

PROFILES = {"claude-work": {"provider": "claude", "env": {"CLAUDE_CONFIG_DIR": "/acc/work"}},
            "claude-luis": {"provider": "claude", "env": {"CLAUDE_CONFIG_DIR": "/acc/luis"}},
            "codex-luis": {"provider": "codex", "env": {"CODEX_HOME": "/acc/codex-luis"}}}
ROUTES = [{"agent": "codex", "profile": "codex-luis", "model": "gpt-6.1-sol", "effort": "high"},
          {"agent": "claude", "profile": "claude-luis"}, {"agent": "claude", "profile": "claude-work"}]


class PlannerAccount(unittest.TestCase):
    def setUp(self):
        for target, name, value in ((bt_profiles, "load", PROFILES), (bt_agents, "candidates", (ROUTES, None)),
                                    (bt_agents, "pool_for", [])):
            patcher = patch.object(target, name, return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch.dict(os.environ, {"BITACORA_PLANNER_CLAUDE_CONFIG_DIR": ""})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_the_first_unattended_claude_account_the_router_ranks_and_never_the_one_to_avoid(self):
        with patch.object(terminal, "unattended", return_value=True):
            self.assertEqual(terminal.planner_route("pictures")["home"], "/acc/luis")
            self.assertEqual(terminal.planner_route("pictures", avoid="/acc/luis")["home"], "/acc/work")
        with patch.dict(os.environ, {"BITACORA_PLANNER_CLAUDE_CONFIG_DIR": "/acc/owner"}):
            self.assertEqual(terminal.planner_route("pictures")["home"], "/acc/owner")

    def test_an_account_that_would_ask_the_owner_first_is_skipped_for_codex(self):
        with patch.object(terminal, "unattended", side_effect=lambda path: path == "/acc/work"):
            self.assertEqual(terminal.planner_route("pictures")["home"], "/acc/work")
        with patch.object(terminal, "unattended", return_value=False):
            route = terminal.planner_route("pictures")
        self.assertEqual((route["provider"], route["home"], route["model"]), ("codex", "/acc/codex-luis", "gpt-6.1-sol"))

    def test_unattended_reads_the_owners_setting_of_the_account(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(terminal.unattended(tmp))
            (Path(tmp) / "settings.json").write_text(json.dumps({"skipDangerousModePermissionPrompt": True}))
            self.assertTrue(terminal.unattended(tmp))

    def test_a_codex_planner_starts_from_the_plan_and_keeps_the_claude_conversation_on_record(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {"HOME": tmp}):
            root, rdir = Path(tmp) / "root", Path(tmp) / "root" / "pictures" / "requirements" / "REQ-021-x"
            (rdir / ".planning").mkdir(parents=True)
            (rdir / terminal.RECORD).write_text(json.dumps({"session_id": "sid-1", "config_dir": "/acc/luis"}))
            route = {"provider": "codex", "home": "/acc/codex-luis", "model": "gpt-6.1-sol", "effort": "high"}
            with patch.object(terminal, "planner_route", return_value=route), \
                    patch.object(terminal, "exists", return_value=False), patch.object(terminal, "start") as start:
                ok, message = terminal.start_planner(root, "pictures", rdir, message="[notice] escribe las Pruebas")
            self.assertTrue(ok, message)
            command, env = start.call_args.args[2], start.call_args.args[3]
            self.assertIn("codex --dangerously-bypass-approvals-and-sandbox -m gpt-6.1-sol", command)
            self.assertEqual(env, {"CODEX_HOME": "/acc/codex-luis"})
            prompt = next((Path(tmp) / ".local/share/bitacora-sessions/pictures").glob("*.prompt.md")).read_text()
            self.assertIn("escribe las Pruebas", prompt)
            record = json.loads((rdir / terminal.RECORD).read_text())
            self.assertEqual((record["provider"], record["codex_home"], record["session_id"]), ("codex", "/acc/codex-luis", "sid-1"))

    def test_the_conversation_moves_to_the_account_with_quota(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, rdir = Path(tmp) / "root", Path(tmp) / "root" / "pictures" / "requirements" / "REQ-021-x"
            (rdir / ".planning").mkdir(parents=True)
            old_account, new_account = Path(tmp) / "work", Path(tmp) / "luis"
            old = terminal.transcript(str(old_account), str(root), "sid-1")
            old.parent.mkdir(parents=True)
            old.write_text('{"type": "user"}\n')
            (rdir / terminal.RECORD).write_text(json.dumps({"session_id": "sid-1", "config_dir": str(old_account), "cwd": str(root)}))
            with patch.object(terminal, "planner_route", return_value={"provider": "claude", "home": str(new_account)}), \
                    patch.object(terminal, "exists", return_value=False), patch.object(terminal, "start") as start:
                ok, message = terminal.start_planner(root, "pictures", rdir, message="[notice] SP-8 confirmado")
            self.assertTrue(ok, message)
            self.assertTrue(terminal.transcript(str(new_account), str(root), "sid-1").is_file())
            command, env = start.call_args.args[2], start.call_args.args[3]
            self.assertIn("--resume sid-1", command)
            self.assertIn("SP-8 confirmado", command)
            self.assertEqual(env, {"CLAUDE_CONFIG_DIR": str(new_account)})
            self.assertEqual(json.loads((rdir / terminal.RECORD).read_text())["config_dir"], str(new_account))

    def test_a_notice_that_finds_the_planner_out_of_quota_restarts_it_elsewhere_with_the_notice(self):
        with tempfile.TemporaryDirectory() as tmp:
            rdir = Path(tmp) / "pictures" / "requirements" / "REQ-021-x"
            (rdir / ".planning").mkdir(parents=True)
            (rdir / terminal.RECORD).write_text(json.dumps({"session_id": "sid-1", "config_dir": "/acc/work"}))
            limited = "❯ notice\n  ⎿  You've hit your weekly limit · resets Oct 31, 6pm\n     /usage-credits to request more"
            with patch("bt_core.ROOT", Path(tmp)), patch.object(terminal, "exists", return_value=True), \
                    patch.object(terminal, "screen", return_value=limited), patch.object(terminal, "kill") as kill, \
                    patch.object(terminal, "send") as send, \
                    patch.object(terminal, "start_planner", return_value=(True, "Planner abierto")) as start:
                self.assertTrue(terminal.notify_planner("pictures", "REQ-021", "SP-8 confirmado"))
            kill.assert_called_once()
            send.assert_not_called()
            self.assertEqual(start.call_args.kwargs["avoid"], "/acc/work")
            self.assertIn("SP-8 confirmado", start.call_args.kwargs["message"])

    def test_a_planner_with_quota_is_simply_told(self):
        with patch.object(terminal, "exists", return_value=True), patch.object(terminal, "screen", return_value="❯ listo"), \
                patch.object(terminal, "send", return_value="Enviado.") as send, patch.object(terminal, "kill") as kill:
            self.assertTrue(terminal.notify_planner("pictures", "REQ-021", "SP-8 confirmado"))
        kill.assert_not_called()
        self.assertIn("SP-8 confirmado", send.call_args.args[1])

    def test_a_planner_waiting_on_the_owners_consent_is_not_typed_into_and_the_owner_is_told_where(self):
        prompt = ("  WARNING: Claude Code running in Bypass Permissions mode\n  ❯ No, exit\n    Yes, I accept\n"
                  "  Enter to confirm · Esc to cancel")
        with patch.object(terminal, "exists", return_value=True), patch.object(terminal, "screen", return_value=prompt), \
                patch.object(terminal, "send") as send, patch.object(terminal, "kill") as kill, \
                patch("bt_runutil.notify") as notify:
            self.assertFalse(terminal.notify_planner("pictures", "REQ-021", "SP-8 confirmado"))
        send.assert_not_called()
        kill.assert_not_called()
        self.assertIn("attach -t bit-pictures-REQ-021-planner", notify.call_args.args[1])
        self.assertIn("Yes, I accept", notify.call_args.args[1])


if __name__ == "__main__":
    unittest.main()
