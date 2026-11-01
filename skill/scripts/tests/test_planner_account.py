"""The Planner runs on a Claude account with quota and leaves one that ran out, conversation included (REQ-021, 2026-10-29)."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bt_agent_terminal as terminal
import bt_agent_wall as wall
import bt_agents
import bt_planner_notices as notices
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
            tomorrow = time.strftime("%b %d", time.localtime(time.time() + 86400))
            limited = f"❯ notice\n  ⎿  You've hit your weekly limit · resets {tomorrow}, 6pm\n     /usage-credits to request more"
            with patch("bt_core.ROOT", Path(tmp)), patch.object(terminal, "exists", return_value=True), patch.object(terminal, "agent_state", return_value="running"), \
                    patch.object(terminal, "screen", return_value=limited), patch.object(terminal, "kill") as kill, \
                    patch.object(terminal, "send") as send, \
                    patch.object(terminal, "start_planner", return_value=(True, "Planner abierto")) as start:
                self.assertTrue(terminal.notify_planner("pictures", "REQ-021", "SP-8 confirmado"))
            kill.assert_called_once()
            send.assert_not_called()
            self.assertEqual(start.call_args.kwargs["avoid"], "/acc/work")
            self.assertIn("SP-8 confirmado", start.call_args.kwargs["message"])

    def test_a_planner_with_quota_is_simply_told(self):
        with patch.object(terminal, "exists", return_value=True), patch.object(terminal, "agent_state", return_value="running"), patch.object(terminal, "screen", return_value="❯ listo"), \
                patch.object(terminal, "send", return_value="Enviado.") as send, patch.object(terminal, "kill") as kill:
            self.assertTrue(terminal.notify_planner("pictures", "REQ-021", "SP-8 confirmado"))
        kill.assert_not_called()
        self.assertIn("SP-8 confirmado", send.call_args.args[1])

    def test_a_planner_waiting_on_the_owners_consent_is_not_typed_into_and_the_owner_is_told_where(self):
        prompt = ("  WARNING: Claude Code running in Bypass Permissions mode\n  ❯ No, exit\n    Yes, I accept\n"
                  "  Enter to confirm · Esc to cancel")
        with patch.object(terminal, "exists", return_value=True), patch.object(terminal, "agent_state", return_value="running"), patch.object(terminal, "screen", return_value=prompt), \
                patch.object(terminal, "send") as send, patch.object(terminal, "kill") as kill, \
                patch("bt_runutil.notify") as notify:
            self.assertFalse(terminal.notify_planner("pictures", "REQ-021", "SP-8 confirmado"))
        send.assert_not_called()
        kill.assert_not_called()
        self.assertIn("attach -t bit-pictures-REQ-021-planner", notify.call_args.args[1])
        self.assertIn("Yes, I accept", notify.call_args.args[1])

    def test_the_route_says_when_no_account_but_the_spent_one_is_left(self):
        with patch.object(terminal, "unattended", return_value=True), \
                patch.object(bt_agents, "candidates", return_value=([ROUTES[1]], 1793400000.0)):
            self.assertEqual(terminal.planner_route("pictures", avoid="/acc/luis")["until"], "1793400000.0")
            self.assertNotIn("exhausted", terminal.planner_route("pictures", avoid="/acc/work"))
        with patch.object(bt_agents, "candidates", return_value=([], None)):
            self.assertEqual(terminal.planner_route("pictures")["exhausted"], "1")

    def test_a_wall_that_answers_a_notice_moves_the_planner_with_the_notices_it_had_not_read(self):
        """2026-10-30 16:25: the request typed into a Planner whose Codex account had run out was lost."""
        with tempfile.TemporaryDirectory() as tmp:
            rdir = Path(tmp) / "pictures" / "requirements" / "REQ-021-x"
            (rdir / ".planning").mkdir(parents=True)
            (rdir / terminal.RECORD).write_text(json.dumps({"provider": "codex", "codex_home": "/acc/codex-luis"}))
            wall.hold(rdir, "[older] SP-7 confirmado", time.time() + 600, "quota")
            limited = terminal.Said.of("El agente no lo leyó: su cuenta se quedó sin cuota.", "limited")
            with patch("bt_core.ROOT", Path(tmp)), patch.object(terminal, "exists", return_value=True), patch.object(terminal, "agent_state", return_value="running"), \
                    patch.object(terminal, "screen", return_value="› listo"), patch.object(terminal, "kill") as kill, \
                    patch.object(terminal, "send", return_value=limited), patch.object(terminal, "unattended", return_value=True), \
                    patch.object(terminal, "start_planner", return_value=(True, "Planner abierto")) as start:
                state, message = notices.tell("pictures", "REQ-021", "[notice] add the 039 migration")
            self.assertEqual(state, "moved", message)
            kill.assert_called_once()
            self.assertEqual(start.call_args.kwargs["avoid"], "/acc/codex-luis")
            self.assertEqual(start.call_args.kwargs["route"]["home"], "/acc/luis")
            self.assertEqual(start.call_args.kwargs["message"], "[older] SP-7 confirmado\n\n[notice] add the 039 migration")
            self.assertEqual(wall.held(rdir), [])

    def test_a_wall_whose_reset_has_passed_is_stale_and_the_notice_is_typed(self):
        past = datetime.fromtimestamp(time.time() - 3600).strftime("%-I:%M %p")
        shown = f"› x\n■ You've hit your usage limit. Upgrade to Pro or try again at {past}.\n› "
        with patch.object(terminal, "exists", return_value=True), patch.object(terminal, "agent_state", return_value="running"), patch.object(terminal, "screen", return_value=shown), \
                patch.object(terminal, "send", return_value="Enviado.") as send, patch.object(terminal, "kill") as kill:
            self.assertTrue(terminal.notify_planner("pictures", "REQ-021", "SP-8 confirmado"))
        kill.assert_not_called()
        send.assert_called_once()

    def test_a_planner_waiting_on_the_owner_is_told_once_and_the_notice_held(self):
        prompt = "  WARNING: Claude Code running in Bypass Permissions mode\n  ❯ No, exit\n    Yes, I accept"
        with tempfile.TemporaryDirectory() as tmp:
            rdir = Path(tmp) / "pictures" / "requirements" / "REQ-021-x"
            (rdir / ".planning").mkdir(parents=True)
            with patch("bt_core.ROOT", Path(tmp)), patch.object(terminal, "exists", return_value=True), patch.object(terminal, "agent_state", return_value="running"), \
                    patch.object(terminal, "screen", return_value=prompt), patch.object(terminal, "send") as send, \
                    patch("bt_runutil.notify") as notify:
                self.assertEqual(notices.tell("pictures", "REQ-021", "a")[0], "held")
                self.assertEqual(notices.tell("pictures", "REQ-021", "a", retry=True)[0], "held")
            send.assert_not_called()
            self.assertEqual(notify.call_count, 1)
            self.assertEqual([n["text"] for n in wall.held(rdir)], ["a"])


class Walls(unittest.TestCase):
    NOW = datetime(2026, 10, 30, 16, 25).timestamp()
    CODEX = ("■ You've hit your usage limit. Upgrade to Pro (https://chatgpt.com/explore/pro), visit "
             "https://chatgpt.com/codex/settings/usage to purchase more credits or try again at 4:32 PM.")

    def test_the_exact_codex_and_claude_walls_and_when_each_comes_back(self):
        at = lambda shown, now=self.NOW, **kw: datetime.fromtimestamp(wall.reset_at(shown, now, **kw))
        self.assertEqual(at(self.CODEX), datetime(2026, 10, 30, 16, 32))
        self.assertEqual(at("You've hit your weekly limit · resets Oct 31, 6pm\n /usage-credits to request more"),
                         datetime(2026, 10, 31, 18, 0))
        self.assertEqual(at("5-hour limit reached ∙ resets 3am", fresh=True), datetime(2026, 10, 31, 3, 0))
        self.assertEqual(at("You've hit your usage limit. try again in 2 hours 5 minutes"), datetime(2026, 10, 30, 18, 30))
        self.assertEqual(at("You've hit your usage limit or try again at Nov 3rd, 2026 4:32 PM."),
                         datetime(2026, 11, 3, 16, 32))
        self.assertEqual(wall.reset_at("Claude usage limit reached|1761868800", self.NOW), 1761868800.0)
        for text in ("You're out of extra usage · resets 3pm", "Weekly limit reached ∙ resets Nov 2",
                     "Claude usage limit reached. Your limit will reset at 5pm"):
            self.assertTrue(wall.LIMITED.search(text), text)
        self.assertFalse(wall.LIMITED.search("Approaching rate limits"))

    def test_a_wall_is_stale_once_its_reset_passed_but_never_when_it_just_answered(self):
        later = datetime(2026, 10, 30, 17, 0).timestamp()
        self.assertEqual(wall.limited(self.CODEX, self.NOW)[0], True)
        self.assertEqual(wall.limited(self.CODEX, later)[0], False)
        hit, until = wall.limited(self.CODEX, later, fresh=True)
        self.assertEqual((hit, datetime.fromtimestamp(until)), (True, datetime(2026, 10, 31, 16, 32)))

    def test_the_modals(self):
        modal = ("  Approaching rate limits\n  Switch to gpt-6-luna for lower credit usage?\n\n› 1. Switch to gpt-6-luna\n"
                 "  2. Keep current model\n  3. Keep current model (never show again)\n\n  enter select · esc back")
        self.assertEqual(wall.modal(modal), ("model-switch", "2"))
        self.assertEqual(wall.modal("› 1. Yes\n  2. No\n  enter select · esc back")[0], "blocking")
        self.assertEqual(wall.modal("› Ask Codex to do anything\n  ⏎ send"), ("", ""))


class RoleRouteModel(unittest.TestCase):
    """Every role session runs the model and effort its role policy names (D-267): `role_route` returned Claude Opus high
    for every role, so the Solucionador ran Opus although D-253 says Sonnet high (pictures REQ-021, 2026-10-31)."""

    def setUp(self):
        for target, name, value in ((bt_profiles, "load", PROFILES), (bt_agents, "pool_for", [])):
            patcher = patch.object(target, name, return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch.dict(os.environ, {"BITACORA_PLANNER_CLAUDE_CONFIG_DIR": "", "BITACORA_SOLVER_CLAUDE_CONFIG_DIR": ""})
        patcher.start()
        self.addCleanup(patcher.stop)

    @staticmethod
    def ranked(role):
        """The router's ranking for `role`: the policy's choices, one route per profile and provider."""
        import bt_role_policy
        homes = {"claude": ("claude-luis", "claude-work"), "codex": ("codex-luis",)}
        return [{"agent": provider, "profile": pid, "model": model, "effort": effort}
                for provider, model, effort in bt_role_policy.options(role) for pid in homes[provider]]

    def route(self, role, *, unattended=True, override="", ranking=None):
        ranking = self.ranked(role) if ranking is None else ranking
        with patch.object(bt_agents, "candidates", return_value=(ranking, None)) as candidates, \
                patch.object(terminal, "unattended", return_value=unattended):
            route = terminal.role_route("pictures", role, override=override)
        if ranking is not None and candidates.call_count:
            self.assertEqual(candidates.call_args.kwargs.get("role"), role)
        return route

    def test_the_solver_runs_claude_sonnet_high(self):
        route = self.route("solver")
        self.assertEqual((route["provider"], route["home"], route["model"], route["effort"]),
                         ("claude", "/acc/luis", "sonnet", "high"))

    def test_the_solver_falls_back_to_codex_terra_medium(self):
        route = self.route("solver", unattended=False)
        self.assertEqual((route["provider"], route["home"], route["model"], route["effort"]),
                         ("codex", "/acc/codex-luis", "gpt-6.1-terra", "medium"))

    def test_the_planner_and_the_designer_keep_opus_high(self):
        for role in ("planner", "designer"):
            route = self.route(role)
            self.assertEqual((route["provider"], route["model"], route["effort"]), ("claude", "opus", "high"), role)

    def test_a_ranked_claude_route_without_a_model_takes_the_policy_rung(self):
        route = self.route("solver", ranking=[{"agent": "claude", "profile": "claude-luis"}])
        self.assertEqual((route["model"], route["effort"]), ("sonnet", "high"))

    def test_a_pinned_account_runs_the_policy_model(self):
        with patch.dict(os.environ, {"BITACORA_SOLVER_CLAUDE_CONFIG_DIR": "/acc/pinned",
                                     "BITACORA_PLANNER_CLAUDE_CONFIG_DIR": "/acc/pinned"}):
            solver = self.route("solver", override="BITACORA_SOLVER_CLAUDE_CONFIG_DIR")
            planner = terminal.planner_route("pictures")
        self.assertEqual((solver["home"], solver["model"], solver["effort"]), ("/acc/pinned", "sonnet", "high"))
        self.assertEqual((planner["home"], planner["model"], planner["effort"]), ("/acc/pinned", "opus", "high"))

    def test_the_last_resort_account_runs_the_policy_model(self):
        solver = self.route("solver", unattended=False, ranking=[{"agent": "claude", "profile": "claude-luis"}])
        self.assertEqual((solver["provider"], solver["model"], solver["effort"]), ("claude", "sonnet", "high"))
        with patch.object(bt_agents, "candidates", side_effect=RuntimeError("no ranking")):
            planner = terminal.planner_route("pictures")
        self.assertEqual((planner["model"], planner["effort"]), ("opus", "high"))

    def test_a_role_without_a_claude_rung_keeps_opus_high(self):
        self.assertEqual(terminal.claude_choice("nobody"), ("opus", "high"))

    def test_the_router_ranking_itself_carries_the_solver_model(self):
        """No mocked ranking: the role router's own routes for the Solucionador name Sonnet high and Terra medium."""
        import bt_role_routing
        import bt_subscriptions
        with patch.object(bt_subscriptions, "load", return_value={}), \
                patch.object(bt_role_routing, "recent_sessions", return_value={}), \
                patch.object(bt_agents, "cooling_until", return_value=None):
            routes, _ = bt_agents.candidates("pictures", ["claude-luis", "codex-luis"], 1, "plan", allow_explore=False,
                                             role="solver")
        self.assertEqual({(r["agent"], r["model"], r["effort"]) for r in routes},
                         {("claude", "sonnet", "high"), ("codex", "gpt-6.1-terra", "medium")})

    def test_a_claude_planner_starts_with_the_routed_model(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {"HOME": tmp}):
            root, rdir = Path(tmp) / "root", Path(tmp) / "root" / "pictures" / "requirements" / "REQ-021-x"
            (rdir / ".planning").mkdir(parents=True)
            for route, flags in (({"provider": "claude", "home": "/acc/luis", "model": "sonnet", "effort": "medium"},
                                  "--model sonnet --effort medium"),
                                 ({"provider": "claude", "home": "/acc/luis"}, "--model opus --effort high")):
                with patch.object(terminal, "exists", return_value=False), patch.object(terminal, "start") as start:
                    ok, message = terminal.start_planner(root, "pictures", rdir, fresh=True, route=route)
                self.assertTrue(ok, message)
                self.assertIn(flags, start.call_args.args[2])


if __name__ == "__main__":
    unittest.main()
