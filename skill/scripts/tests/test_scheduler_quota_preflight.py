"""Scheduler quota refresh stays inside its project's authorized account pool."""
from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bt_agy
import bt_profiles
import bt_scheduler_adapter as adapter
import bt_subscriptions


class QuotaPreflightTests(unittest.TestCase):
    def test_refreshes_only_authorized_pool_and_reports_unavailable_sources(self):
        profiles = {"claude-work": {"provider": "claude"},
                    "gemini-work": {"provider": "antigravity"},
                    "codex-other": {"provider": "codex"}}
        rows = [{"profile": "claude-work", "status": "http_401", "bottleneck_used_percent": None}]
        with patch("bt_agents.pool_for", return_value=["claude-work", "gemini-work"]), \
                patch.object(bt_profiles, "load", return_value=profiles), \
                patch.object(bt_subscriptions, "poll", return_value=rows) as poll, \
                patch.object(bt_agy, "refresh", return_value={"status": "error"}) as refresh, \
                patch.object(bt_agy, "capacity", return_value=(None, None)):
            result = adapter.refresh_quota_preflight("demo")
        poll.assert_called_once_with(["claude-work"])
        refresh.assert_called_once_with()
        self.assertEqual(result["claude-work"]["state"], "refresh_failed")
        self.assertEqual(result["claude-work"]["reason"], "quota_refresh_failed")
        self.assertEqual(result["gemini-work"]["state"], "refresh_failed")

    def test_does_not_refresh_antigravity_outside_authorized_pool(self):
        with patch("bt_agents.pool_for", return_value=["codex-work"]), \
                patch.object(bt_profiles, "load", return_value={"codex-work": {"provider": "codex"}}), \
                patch.object(bt_subscriptions, "poll", return_value=[]) as poll, \
                patch.object(bt_agy, "refresh") as refresh:
            adapter.refresh_quota_preflight("demo")
        poll.assert_called_once_with(["codex-work"])
        refresh.assert_not_called()

    def test_reports_subscription_poll_failure_explicitly(self):
        with patch("bt_agents.pool_for", return_value=["claude-work"]), \
                patch.object(bt_profiles, "load", return_value={"claude-work": {"provider": "claude"}}), \
                patch.object(bt_subscriptions, "poll", side_effect=RuntimeError("private detail")):
            result = adapter.refresh_quota_preflight("demo")
        self.assertEqual(result["claude-work"]["state"], "refresh_failed")
        self.assertEqual(result["claude-work"]["reason"], "quota_refresh_failed")
        self.assertNotIn("private detail", repr(result))

    def test_missing_and_stale_observations_keep_distinct_states_and_safe_fields(self):
        profiles = {"claude-work": {"provider": "claude"}}
        with patch("bt_agents.pool_for", return_value=["claude-work"]), \
                patch.object(bt_profiles, "load", return_value=profiles), \
                patch.object(bt_subscriptions, "poll", return_value=[]):
            missing = adapter.refresh_quota_preflight("demo")["claude-work"]
        self.assertEqual((missing["state"], missing["reason"]), ("missing", "quota_observation_missing"))
        stale_observation = 1.0
        with patch("bt_agents.pool_for", return_value=["claude-work"]), \
                patch.object(bt_profiles, "load", return_value=profiles), \
                patch.object(bt_subscriptions, "poll", return_value=[{
                    "profile": "claude-work", "status": "http_401", "observed_at": stale_observation,
                    "bottleneck_used_percent": 18.0,
                }]):
            stale = adapter.refresh_quota_preflight("demo")["claude-work"]
        self.assertEqual((stale["state"], stale["reason"]), ("stale", "quota_refresh_failed"))
        self.assertEqual(stale["observed_at"], stale_observation)
        self.assertLessEqual(stale["valid_until"], time.time())

    def test_malformed_quota_pressure_never_reports_a_route_as_available(self):
        profiles = {"claude-work": {"provider": "claude"}}
        with patch("bt_agents.pool_for", return_value=["claude-work"]), \
                patch.object(bt_profiles, "load", return_value=profiles), \
                patch.object(bt_subscriptions, "poll", return_value=[{
                    "profile": "claude-work", "status": "ok", "bottleneck_used_percent": True,
                }]):
            result = adapter.refresh_quota_preflight("demo")
        self.assertEqual(result["claude-work"]["state"], "malformed")
        self.assertEqual(result["claude-work"]["reason"], "quota_data_malformed")

    def test_refuses_an_oversized_account_pool_without_polling(self):
        pool = [f"account-{index}" for index in range(adapter._QUOTA_PREFLIGHT_MAX_ACCOUNTS + 1)]
        profiles = {pid: {"provider": "claude"} for pid in pool}
        with patch("bt_agents.pool_for", return_value=pool), \
                patch.object(bt_profiles, "load", return_value=profiles), \
                patch("bt_agents._pool_account_identity", side_effect=lambda pid, _spec: ("claude", (pid,))), \
                patch.object(bt_subscriptions, "poll") as poll:
            result = adapter.refresh_quota_preflight("demo")
        self.assertEqual(result, {"*": {"status": "unavailable", "reason": "preflight_account_limit_exceeded"}})
        poll.assert_not_called()

    def test_limit_counts_effective_accounts_after_alias_deduplication(self):
        pool = [f"alias-{index}" for index in range(40)]
        profiles = {pid: {"provider": "claude"} for pid in pool}
        identity_for = lambda pid, _spec: ("claude", ("one" if int(pid.split("-")[1]) < 20 else "two",))
        with patch("bt_agents.pool_for", return_value=pool), \
                patch.object(bt_profiles, "load", return_value=profiles), \
                patch("bt_agents._pool_account_identity", side_effect=identity_for), \
                patch.object(bt_subscriptions, "poll", return_value=[]) as poll:
            result = adapter.refresh_quota_preflight("demo")
        self.assertEqual(poll.call_args.args[0], ["alias-0", "alias-20"])
        self.assertEqual(len(result), 40)
        self.assertNotEqual(result.get("*", {}).get("reason"), "preflight_account_limit_exceeded")


if __name__ == "__main__":
    unittest.main()
