"""Subscription data validation, sampling and real-quota routing with disposable fixtures."""
from __future__ import annotations

import datetime as dt
import email.utils
import json
import sys
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bt_agents
import bt_profiles
import bt_subscription_schedule as schedule
import bt_subscription_sources as sources
import bt_subscriptions as usage
from test_agents import AgentTests


class SubscriptionUsageTests(AgentTests):
    def setUp(self):
        super().setUp()
        self.now = 1_800_000_000.0
        for target in (usage,):
            p = patch.object(target, "STATE", self.state)
            p.start()
            self.addCleanup(p.stop)
        p = patch.object(usage.time, "time", return_value=self.now)
        p.start()
        self.addCleanup(p.stop)

    def row(self, short=20, weekly=30, age=0, reset=None, status="ok"):
        return {"status": status, "observed_at": self.now-age, "attempted_at": self.now-age, "windows": {
            "five_hour": sources.window(short, reset or self.now+3600, 300),
            "seven_day": sources.window(weekly, self.now+86400, 10080)}}

    def save(self, accounts):
        (self.state / "subscription-usage.json").write_text(json.dumps({"schema_version": 1, "accounts": accounts}))

    def test_lower_headroom_loses_even_with_lower_local_load(self):
        bt_profiles.add("codex-other", "codex", {"CODEX_HOME": str(self.base / "other")})
        self.save({bt_agents.account_key("codex-named"): self.row(short=80, weekly=10),
                   bt_agents.account_key("codex-other"): self.row(short=10, weekly=20)})
        routes, _ = bt_agents.candidates("personal-project", ["codex-named", "codex-other"], 0)
        self.assertEqual(routes[0]["profile"], "codex-other")
        self.assertIn("20% used", routes[0]["why"])

    def test_weekly_pressure_counts_even_when_short_window_is_empty(self):
        self.assertEqual(usage.capacity(self.row(short=0, weekly=95), "gpt-6.1-sol"), (95, None))

    def test_exhausted_weekly_window_removes_route_until_its_reset(self):
        self.save({bt_agents.account_key("codex-named"): self.row(short=0, weekly=100)})
        routes, reset = bt_agents.candidates("personal-project", ["codex-named"], 0)
        self.assertEqual(routes, [])
        self.assertEqual(reset, self.now+86400)

    def test_stale_or_failed_data_is_unknown_but_known_exhaustion_survives(self):
        for row in (self.row(age=7201), self.row(status="http_401")):
            self.assertEqual(usage.capacity(row, "sonnet"), (None, None))
        exhausted = self.row(weekly=100, age=10000, status="network_unavailable")
        self.assertEqual(usage.capacity(exhausted, "sonnet"), (None, self.now+86400))

    def test_reset_does_not_fabricate_a_zero_usage_window(self):
        row = self.row(short=100, reset=self.now-1)
        self.assertEqual(usage.capacity(row, "sonnet"), (None, None))

    def test_claude_null_reset_remains_active_but_a_missing_reset_is_unknown(self):
        row = self.row()
        row["provider"] = "claude"
        row["windows"]["five_hour"]["resets_at"] = None
        self.assertEqual(usage.capacity(row, "sonnet", self.now), (30, None))
        del row["windows"]["five_hour"]["resets_at"]
        self.assertEqual(usage.capacity(row, "sonnet", self.now), (None, None))

    def test_unrepresentable_cached_numbers_are_unknown_instead_of_raising(self):
        with self.assertRaises(sources.UsageError):
            sources.number(10 ** 1000)
        row = self.row()
        row["observed_at"] = 10 ** 1000
        self.assertEqual(usage.capacity(row, "gpt-6.1-sol", self.now), (None, None))

    def test_model_specific_claude_quota_is_respected(self):
        row = self.row()
        row["windows"]["seven_day_opus"] = sources.window(100, self.now+8000, 10080)
        self.assertEqual(usage.capacity(row, "opus"), (100, self.now+8000))
        self.assertEqual(usage.capacity(row, "sonnet"), (30, None))

    def test_malformed_or_future_samples_are_not_ranked_as_unused(self):
        for value in (None, [], {"status": "ok"}, self.row(age=-10)):
            self.assertEqual(usage.capacity(value, "sonnet"), (None, None))
        row = self.row()
        row["windows"]["five_hour"]["used_percent"] = True
        self.assertEqual(usage.capacity(row, "sonnet"), (None, None))

    def test_audit_provider_preference_is_not_overridden_by_codex_headroom(self):
        self.save({bt_agents.account_key("claude"): self.row(short=95),
                   bt_agents.account_key("codex-named"): self.row(short=0, weekly=0)})
        routes, _ = bt_agents.candidates("personal-project", ["codex-named", "claude"], 1, "audit")
        self.assertEqual((routes[0]["agent"], routes[0]["effort"]), ("claude", "medium"))

    def test_exhausted_claude_audit_falls_back_to_codex(self):
        self.save({bt_agents.account_key("claude"): self.row(short=100)})
        route = bt_agents.route("personal-project", {"pool": ["claude", "codex-named"]}, 1, "audit")
        self.assertEqual((route["agent"], route["effort"]), ("codex", "medium"))

    def test_collector_deduplicates_accounts_and_obeys_hourly_interval(self):
        profiles = {"claude": {"provider": "claude", "env": {}},
                    "claude-alias": {"provider": "claude", "env": {}}}
        with patch.object(bt_profiles, "load", return_value=profiles), patch.object(
                usage, "read_claude", return_value=self.row()["windows"]) as read:
            usage.poll()
            usage.poll()
        self.assertEqual(read.call_count, 1)
        events = list((self.state/"events").glob("subscription-usage-*.jsonl"))
        self.assertEqual(len(events), 1)
        self.assertEqual(len(events[0].read_text().splitlines()), 1)

    def test_collector_error_preserves_known_exhaustion_and_leaks_no_exception_text(self):
        key = bt_agents.account_key("claude")
        self.save({key: self.row(weekly=100, age=4000)})
        profiles = {"claude": {"provider": "claude", "env": {}}}
        with patch.object(bt_profiles, "load", return_value=profiles), patch.object(
                usage, "read_claude", side_effect=sources.UsageError("http_401")):
            rows = usage.poll()
        self.assertEqual(rows[0]["status"], "http_401")
        self.assertEqual(rows[0]["exhausted_until"], self.now+86400)

    def test_challenge_stops_automatic_site_requests_and_retry_after_is_respected(self):
        key = bt_agents.account_key("claude")
        profiles = {"claude": {"provider": "claude", "env": {}}}
        for old in ({"status": "manual_challenge"}, {"retry_at": self.now+4000}):
            self.save({key: old})
            with patch.object(bt_profiles, "load", return_value=profiles), patch.object(usage, "read_claude") as read:
                usage.poll()
            read.assert_not_called()

    def test_concurrent_collectors_reserve_one_request_per_account(self):
        profiles = {"claude": {"provider": "claude", "env": {}}}
        entered, release = threading.Event(), threading.Event()
        def read_once(_profile):
            entered.set()
            if not release.wait(3): raise RuntimeError("fixture synchronization timeout")
            return self.row()["windows"]
        with patch.object(bt_profiles, "load", return_value=profiles), patch.object(
                usage, "read_claude", side_effect=read_once) as read, ThreadPoolExecutor(max_workers=2) as workers:
            first = workers.submit(usage.poll)
            self.assertTrue(entered.wait(2))
            second = workers.submit(usage.poll)
            second.result(timeout=2)
            release.set()
            first.result(timeout=2)
        self.assertEqual(read.call_count, 1)

    def test_timer_jitter_does_not_skip_the_next_hourly_sample(self):
        key = bt_agents.account_key("claude")
        self.save({key: self.row(age=3500)})
        profiles = {"claude": {"provider": "claude", "env": {}}}
        with patch.object(bt_profiles, "load", return_value=profiles), patch.object(
                usage, "read_claude", return_value=self.row()["windows"]) as read:
            usage.poll()
        read.assert_called_once_with("claude")

    def test_retry_after_accepts_seconds_and_http_dates(self):
        future = dt.datetime.fromtimestamp(self.now+86400, dt.timezone.utc)
        self.assertEqual(sources.retry_after(email.utils.format_datetime(future, usegmt=True)), self.now+86400)
        self.assertEqual(sources.retry_after("7200"), self.now+7200)
        self.assertEqual(sources.retry_after("invalid"), self.now+3600)

    def test_codex_windows_are_identified_by_duration_not_position(self):
        payload = {"rateLimits": {"limitId": "codex", "primary": {"usedPercent": 13, "windowDurationMins": 10080,
                                              "resetsAt": self.now+8000},
                                  "secondary": {"usedPercent": 42, "windowDurationMins": 300,
                                                "resetsAt": self.now+1000}}}
        parsed = sources.parse_codex(payload)
        self.assertEqual(parsed["five_hour"]["used_percent"], 42)
        self.assertEqual(parsed["seven_day"]["used_percent"], 13)

    def test_codex_uses_the_named_bucket_and_blocks_explicit_usage_denials(self):
        windows = {"primary": {"usedPercent": 10, "windowDurationMins": 300, "resetsAt": self.now + 1000},
                   "secondary": {"usedPercent": 20, "windowDurationMins": 10080, "resetsAt": self.now + 8000}}
        payload = {"rateLimits": {"limitId": "other", **windows},
                   "rateLimitsByLimitId": {"codex": {"primary": windows["primary"],
                                                       "secondary": windows["secondary"]},
                                              "codex_model": {"normalModelSlug": "gpt-6.1-sol",
                                                               "primary": {"usedPercent": 100,
                                                                           "windowDurationMins": 10080,
                                                                           "resetsAt": self.now + 8000}}}}
        parsed = sources.parse_codex(payload)
        self.assertEqual(parsed["five_hour"]["used_percent"], 10)
        row = {"status": "ok", "observed_at": self.now, "windows": parsed}
        self.assertEqual(usage.capacity(row, "gpt-6.1-sol", self.now), (100, self.now + 8000))
        self.assertEqual(usage.capacity(row, "gpt-6-luna", self.now), (20, None))
        for denied in ({"ordinaryUsageAllowed": False}, {"ordinaryUsageAllowed": None},
                       {"bucket": {"spendControlReached": True}},
                       {"bucket": {"rateLimitReachedType": "workspace_member_credits_depleted"}},
                       {"bucket": {"spendControlReached": None}}):
            bucket = {"limitId": "codex", **windows, **denied.get("bucket", {})}
            payload = {"rateLimits": bucket, **{k: v for k, v in denied.items() if k != "bucket"}}
            with self.subTest(denied=denied), self.assertRaises(sources.UsageError):
                sources.parse_codex(payload)
        with self.assertRaises(sources.UsageError):
            sources.parse_codex({"rateLimits": {"limitId": "other", **windows}})
        null_reset = {"limitId": "codex",
                      "primary": {"usedPercent": 0, "windowDurationMins": 300, "resetsAt": None},
                      "secondary": windows["secondary"]}
        with self.assertRaises(sources.UsageError):
            sources.parse_codex({"rateLimits": null_reset})

    def test_claude_response_requires_timezone_and_valid_percentage(self):
        reset = dt.datetime.fromtimestamp(self.now+500,dt.timezone.utc).isoformat()
        self.assertEqual(sources.parse_claude({"five_hour": {"utilization": 55, "resets_at": reset}})
                         ["five_hour"]["used_percent"], 55)
        for value in ({"five_hour": {"utilization": 55, "resets_at": "2026-10-13"}},
                      {"five_hour": {"utilization": 55}},
                      {"five_hour": {"utilization": 101, "resets_at": reset}}, [], {}):
            with self.assertRaises(sources.UsageError): sources.parse_claude(value)

    def test_scheduler_uses_only_metadata_cli_and_hourly_user_timer(self):
        service, timer = schedule.render()
        self.assertIn("usage poll", service)
        self.assertNotIn("delegate", service)
        self.assertNotIn(" exec ", service)
        self.assertIn("OnCalendar=hourly", timer)
        self.assertIn("Persistent=true", timer)
        with self.assertRaises(ValueError): schedule.unit_quote("unsafe\nvalue")

    def test_timer_install_refuses_to_overwrite_unmanaged_files(self):
        directory = self.base / "config/systemd/user"
        directory.mkdir(parents=True)
        path = directory / (schedule.NAME + ".service")
        path.write_text("owner service")
        with patch.dict(schedule.os.environ, {"XDG_CONFIG_HOME": str(self.base / "config")}), patch.object(
                schedule.sys, "platform", "linux"), patch.object(schedule.shutil, "which", return_value="systemctl"), \
                patch.object(schedule.subprocess, "run") as run, self.assertRaises(RuntimeError):
            schedule.install()
        self.assertEqual(path.read_text(), "owner service")
        run.assert_not_called()


class CodexMetadataProtocolTests(unittest.IsolatedAsyncioTestCase):
    async def test_only_initialize_and_rate_limit_messages_are_sent_without_model_turns(self):
        payload = {"rateLimits": {"limitId": "codex", "primary": {"usedPercent": 42, "windowDurationMins": 300,
                                              "resetsAt": 1_900_000_000}}}
        process = Mock(returncode=None)
        process.stdin.drain = AsyncMock()
        process.stdout.readline = AsyncMock(side_effect=[b'{"id":1,"result":{}}\n',
            (json.dumps({"id": 2, "result": payload})+'\n').encode()])
        process.wait = AsyncMock(return_value=0)
        with patch.object(sources.asyncio, "create_subprocess_exec", AsyncMock(return_value=process)), \
                patch.object(sources.bt_profiles, "get", return_value={"bin": "codex"}), \
                patch.object(sources.bt_profiles, "session_env", return_value={}):
            parsed = await sources._read_codex("codex", 1)
        messages = [json.loads(call.args[0]) for call in process.stdin.write.call_args_list]
        self.assertEqual([m["method"] for m in messages], ["initialize", "initialized", "account/rateLimits/read"])
        self.assertEqual(parsed["five_hour"]["used_percent"], 42)
        process.terminate.assert_called_once()


if __name__ == "__main__":
    unittest.main()
