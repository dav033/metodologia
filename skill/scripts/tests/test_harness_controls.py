"""Integrated quota refresh and bounded marathon execution, with disposable provider fixtures."""
import json
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from test_agents import AgentTests
import bt_agents
import bt_profiles
import bt_routing_policy as policy
import bt_runtier
import bt_runstate
import bt_runsettle
import bt_runprompt
import bt_subscriptions as usage
from bt_subscription_sources import UsageError


class FreshRouting(AgentTests):
    def setUp(self):
        super().setUp()
        self.now = 1_800_000_000.0
        p = patch.object(usage.time, "time", return_value=self.now)
        p.start()
        self.addCleanup(p.stop)

    def windows(self, short=20):
        return {"five_hour": {"used_percent": short, "resets_at": self.now + 3600, "window_minutes": 300},
                "seven_day": {"used_percent": 20, "resets_at": self.now + 86400, "window_minutes": 10080}}

    def test_route_refreshes_before_selecting_and_throttles_for_900_seconds(self):
        with patch.object(usage, "read_claude", return_value=self.windows(90)) as claude, patch.object(
                usage, "read_codex", return_value=self.windows(20)) as codex:
            for _ in range(2):
                route = bt_agents.route("personal-project", {"pool": ["claude", "codex-named"]}, 0,
                                        allow_explore=False)
                self.assertEqual(route["profile"], "codex-named")
            self.assertEqual((claude.call_count, codex.call_count), (1, 1))
            with patch.object(usage.time, "time", return_value=self.now + 900):
                usage.ensure_fresh(["claude", "codex-named"])
            self.assertEqual((claude.call_count, codex.call_count), (2, 2))

    def test_refresh_keeps_challenge_and_retry_after_locks(self):
        for row in ({"status": "manual_challenge"}, {"retry_at": self.now + 4000}):
            (self.state / "subscription-usage.json").write_text(json.dumps({
                "schema_version": 1, "accounts": {bt_agents.account_key("claude"): row}}))
            with patch.object(usage, "read_claude") as read:
                usage.ensure_fresh(["claude"])
            read.assert_not_called()

    def test_concurrent_routes_keep_last_pressure_or_auth_block_during_refresh(self):
        for status in ("ok", "invalid_credentials"):
            with self.subTest(status=status):
                a = {"status": status, "observed_at": self.now - 1000,
                     "attempted_at": self.now - 1000, "windows": self.windows(90)}
                b = {"status": "ok", "observed_at": self.now, "attempted_at": self.now,
                     "windows": self.windows(60)}
                (self.state / "subscription-usage.json").write_text(json.dumps({"schema_version": 1,
                    "accounts": {bt_agents.account_key("claude"): a,
                                 bt_agents.account_key("codex-named"): b}}))
                entered, release = threading.Event(), threading.Event()

                def delayed_read(_profile):
                    entered.set()
                    if not release.wait(3):
                        raise RuntimeError("fixture synchronization timeout")
                    return self.windows(20)

                state = {"pool": ["claude", "codex-named"]}
                with patch.object(usage, "read_claude", side_effect=delayed_read), ThreadPoolExecutor(1) as workers:
                    first = workers.submit(bt_agents.route, "personal-project", state, 0, allow_explore=False)
                    try:
                        self.assertTrue(entered.wait(2))
                        second = bt_agents.route("personal-project", state, 0, allow_explore=False)
                        self.assertEqual(second["profile"], "codex-named")
                    finally:
                        release.set()
                    self.assertEqual(first.result(timeout=2)["profile"], "claude")

    def test_failed_refresh_preserves_auth_block_and_exhaustion(self):
        with patch.object(usage, "read_claude", side_effect=UsageError("manual_challenge")):
            usage.ensure_fresh(["claude"])
        self.assertTrue(policy.subscription_blocked(usage.load()[bt_agents.account_key("claude")]))

    def test_refresh_does_not_sample_work_only_accounts_for_personal_work(self):
        with patch.object(usage, "read_claude") as read:
            usage.ensure_fresh(["claude-work"], project="personal-project")
        read.assert_not_called()

    def test_model_pressure_85_is_a_fallback_even_when_quality_leads(self):
        a = {"status": "ok", "observed_at": self.now, "windows": self.windows(20)}
        a["windows"]["seven_day_opus"] = {
            "used_percent": 85, "resets_at": self.now + 86400, "window_minutes": 10080}
        b = {"status": "ok", "observed_at": self.now, "windows": self.windows(30)}
        (self.state / "subscription-usage.json").write_text(json.dumps({"schema_version": 1, "accounts": {
            bt_agents.account_key("claude"): a, bt_agents.account_key("codex-named"): b}}))
        routes, _ = bt_agents.candidates("personal-project", ["claude", "codex-named"], 2)
        self.assertEqual(routes[0]["profile"], "codex-named")
        self.assertEqual(len(routes), 2)  # 85% remains a fallback; 100% is the hard exclusion.


class MarathonBounds(unittest.TestCase):
    def test_kind_ceiling_applies_to_floor_model_and_retry(self):
        for kind, ceiling in (("docs", 0), ("test", 1), ("research", 1)):
            with self.subTest(kind=kind):
                self.assertLessEqual(bt_agents.start_tier("architecture", kind, "L", "high"), ceiling)
                expected = ("haiku", None) if kind == "docs" else ("sonnet", "medium")
                self.assertEqual(bt_agents.model_for("claude", 2, "opus", kind), expected)
                t = {"kind": kind, "tier": ceiling, "attempts": 0, "error_hashes": []}
                self.assertIsNone(bt_runsettle._fail_attempt(t, "broken", 4))
                self.assertLessEqual(t["tier"], ceiling)

    def test_group_configuration_cannot_raise_hard_caps(self):
        for tier, limit in ((0, 3), (1, 1), (2, 1)):
            self.assertEqual(bt_runtier.group_max({"group_max": {str(tier): 99}}, tier), limit)

    def test_defaults_and_claude_turn_limit(self):
        for tier in (0, 1, 2):
            self.assertLessEqual(bt_runtier.session_timeout_min(bt_runstate.DEFAULT_LIMITS, tier), 25)
        argv, _ = bt_runprompt.agent_argv({"agent": "claude"}, Path("."), "P", "haiku", None)
        self.assertEqual(argv[argv.index("--max-turns") + 1], "45")

    def test_a_delegation_gets_the_configured_turns_not_the_marathon_45(self):
        import bt_delegate                    # pictures REQ-021 SP-12: Opus Designers stopped at 45 turns
        self.assertEqual(bt_delegate._max_turns(), 120)
        with patch("bt_config.get", return_value=200):
            self.assertEqual(bt_delegate._max_turns(), 200)
        with patch("bt_config.get", return_value=0):
            self.assertEqual(bt_delegate._max_turns(), 120)
        argv, _ = bt_runprompt.agent_argv({"agent": "claude"}, Path("."), "P", "opus", "high",
                                          max_turns=bt_delegate._max_turns())
        self.assertEqual(argv[argv.index("--max-turns") + 1], "120")
        self.assertIn("max_turns=_max_turns()", Path(bt_delegate.__file__).read_text())   # what the delegation passes


if __name__ == "__main__":
    unittest.main()
