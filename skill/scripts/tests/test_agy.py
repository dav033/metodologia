"""Antigravity provider CLI, quota cache, telemetry and routing coverage."""
from __future__ import annotations

import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import bt_agents  # noqa: E402
import bt_agy  # noqa: E402
import bt_config  # noqa: E402
import bt_core  # noqa: E402
import bt_events  # noqa: E402
import bt_profiles  # noqa: E402
import bt_runprompt  # noqa: E402
import bt_runsettle  # noqa: E402
import bt_runtier  # noqa: E402


class AgTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="agy-test-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / "bitacora"
        self.state = self.root / ".state"
        self.state.mkdir(parents=True)
        self.home = self.base / "home"
        self.home.mkdir()
        token = self.home / ".gemini" / "antigravity-cli" / "antigravity-oauth-token"
        token.parent.mkdir(parents=True)
        token.write_text("test token marker", encoding="utf-8")

        for module, attribute, value in (
                (bt_agents, "STATE", self.state), (bt_events, "STATE", self.state),
                (bt_profiles, "STATE", self.state), (bt_profiles, "ROOT", self.root),
                (bt_profiles, "HOME", self.home), (bt_core, "ROOT", self.root),
                (bt_core, "STATE", self.state), (bt_config, "STATE", self.state)):
            p = patch.object(module, attribute, value)
            p.start()
            self.addCleanup(p.stop)
        self.home_patch = patch.object(Path, "home", return_value=self.home)
        self.home_patch.start()
        self.addCleanup(self.home_patch.stop)
        self.personal = self.root / "personal-project"
        self.personal.mkdir(parents=True)

    def add_profiles(self):
        bt_profiles.add("claude", "claude", {})
        bt_profiles.add("codex", "codex", {})
        bt_profiles.add("antigravity", "antigravity", {})

    def fake_clis(self):
        return patch.object(bt_agents.shutil, "which", return_value="/bin/fake-cli")


class UsageAndCommandTests(AgTestCase):
    def test_antigravity_profile_contract_and_auth_summary_use_isolated_token_marker(self):
        spec = {"provider": "antigravity", "bin": "agy"}
        self.assertIn("antigravity", bt_profiles.LAUNCHABLE)
        self.assertEqual(bt_profiles.DEFAULT_BIN["antigravity"], "agy")
        self.assertEqual(bt_profiles.ACCOUNT_VARS["antigravity"], ())
        self.assertIn("token present", bt_profiles._auth_summary(spec, {}))
        token = self.home / ".gemini" / "antigravity-cli" / "antigravity-oauth-token"
        token.unlink()
        self.assertIn("NOT signed in", bt_profiles._auth_summary(spec, {}))

    def test_parse_usage_real_report_and_ignore_unknown_or_garbage_rows(self):
        now = 1_800_000_000
        report = "\n".join((
            "Gemini Models\tWeekly Limit Remaining\t84%\t2026-10-20T16:21:10Z",
            "Gemini Models\tFive Hour Limit Remaining\t44%\t2026-10-13T16:21:10Z",
            "Claude and GPT models\tWeekly Limit Remaining\t72.5%\t2026-10-20T16:21:10Z",
            "Claude and GPT models\tFive Hour Limit Remaining\t91%\t2026-10-13T16:21:10Z",
            "Mystery Pool\tWeekly Limit Remaining\t1%\t2026-10-20T16:21:10Z",
            "not a quota row", "Gemini Models\tWeekly Limit Remaining\tbad\tgarbage",
        ))
        windows = bt_agy.parse_usage(report, now)
        self.assertEqual(set(windows), {"five_hour", "seven_day", "five_hour_claude_gpt", "seven_day_claude_gpt"})
        self.assertEqual(windows["five_hour"], {"used_percent": 56.0,
                         "resets_at": bt_agy.dt.datetime.fromisoformat("2026-10-13T16:21:10+00:00").timestamp(),
                         "window_minutes": 300})
        self.assertEqual(windows["seven_day"]["used_percent"], 16.0)
        self.assertEqual(windows["seven_day"]["window_minutes"], 10080)
        self.assertEqual(windows["five_hour_claude_gpt"]["used_percent"], 9.0)
        self.assertEqual(windows["seven_day_claude_gpt"]["used_percent"], 27.5)

    def test_argv_attaches_prompt_last_and_only_adds_timeout_when_given(self):
        with patch.object(bt_agy, "exe", return_value="/fake/agy"):
            args = bt_agy.argv(None, "inspect this prompt")
            self.assertEqual(args[0], "/fake/agy")
            self.assertEqual(args[1:3], ["--model", bt_agy.DEFAULT_MODEL])
            self.assertIn("--dangerously-skip-permissions", args)
            self.assertIn("stream-json", args)
            self.assertEqual(args[-1], "--print=inspect this prompt")
            self.assertNotIn("--print-timeout", args)
            timed = bt_agy.argv("gemini-3.8-flash-medium", "p", 123)
        self.assertEqual(timed[-3:], ["--print-timeout", "123s", "--print=p"])
        self.assertEqual(timed[2], "gemini-3.8-flash-medium")

    def test_read_usage_uses_patched_subprocess_and_rejects_signed_out_report(self):
        output = ("Gemini Models\tWeekly Limit Remaining\t84%\t2026-10-20T16:21:10Z\n"
                  "Gemini Models\tFive Hour Limit Remaining\t44%\t2026-10-13T16:21:10Z\n")
        completed = type("Completed", (), {"stdout": output, "stderr": "", "returncode": 0})()
        with patch.object(bt_agy, "exe", return_value="/fake/agy"), \
                patch.object(bt_agy.subprocess, "run", return_value=completed) as run:
            windows = bt_agy.read_usage()
        self.assertIn("five_hour", windows)
        self.assertEqual(run.call_args.args[0][-1], "--print=/usage")
        completed.stdout = "Please sign in to continue"
        with patch.object(bt_agy, "exe", return_value="/fake/agy"), \
                patch.object(bt_agy.subprocess, "run", return_value=completed), \
                self.assertRaisesRegex(RuntimeError, "no Gemini windows"):
            bt_agy.read_usage()


class CacheTests(AgTestCase):
    def write_cache(self, data):
        bt_agy._cache_path().write_text(json.dumps(data), encoding="utf-8")

    def cache(self, observed, five_used=30, week_used=60, five_reset=5000, week_reset=9000, status="ok"):
        self.write_cache({"observed_at": observed, "status": status, "windows": {
            "five_hour": {"used_percent": five_used, "resets_at": five_reset, "window_minutes": 300},
            "seven_day": {"used_percent": week_used, "resets_at": week_reset, "window_minutes": 10080}}})

    def test_capacity_uses_max_of_fresh_active_windows_and_ignores_elapsed_reset(self):
        self.cache(1000, five_used=40, week_used=72, five_reset=1200, week_reset=1900)
        self.assertEqual(bt_agy.capacity(now=1100), (72.0, None))

    def test_elapsed_reset_is_not_reported_as_exhausted_until(self):
        self.cache(1000, five_used=100, week_used=72, five_reset=900, week_reset=1900)
        self.assertEqual(bt_agy.capacity(now=1100), (None, None))

    def test_capacity_reports_exhausted_window_reset(self):
        self.cache(1000, five_used=100, week_used=20, five_reset=1200, week_reset=9000)
        self.assertEqual(bt_agy.capacity(now=1100), (100.0, 1200.0))

    def test_stale_cache_keeps_a_known_exhaustion_but_has_no_trusted_pressure(self):
        # Same rule as bt_subscriptions: headroom from stale data is unknown, but a known exhaustion lasts until its
        # reported reset, so a failed later read cannot put an exhausted account back in rotation.
        now = 1000 + bt_agy.MAX_AGE_SEC + 1
        self.cache(1000, five_used=100, five_reset=now + 10, week_reset=now + 100)
        pressure, exhausted = bt_agy.capacity(now=now)
        self.assertIsNone(pressure)
        self.assertEqual(exhausted, now + 10)
        stale_ok = now + 20  # the five-hour reset has passed: nothing is exhausted any more
        self.assertEqual(bt_agy.capacity(now=stale_ok), (None, None))

    def test_capacity_returns_unknown_for_corrupt_cache(self):
        bt_agy._cache_path().write_text("{broken", encoding="utf-8")
        self.assertEqual(bt_agy.capacity(now=1100), (None, None))

    def test_refresh_skips_young_cache(self):
        self.cache(1000)
        with patch.object(bt_agy, "read_usage", side_effect=AssertionError("must not refresh")):
            self.assertEqual(bt_agy.refresh(now=1100), json.loads(bt_agy._cache_path().read_text()))

    def test_refresh_preserves_old_windows_and_records_read_error(self):
        old = {"observed_at": 1000, "status": "ok", "windows": {"five_hour": {"used_percent": 12}}}
        self.write_cache(old)
        with patch.object(bt_agy, "read_usage", side_effect=RuntimeError("quota report unavailable")):
            refreshed = bt_agy.refresh(now=5000)
        self.assertEqual(refreshed["windows"], old["windows"])
        self.assertEqual(refreshed["status"], "error")
        self.assertEqual(refreshed["error"], "quota report unavailable")
        self.assertEqual(refreshed["attempted_at"], 5000)


class TranscriptTests(AgTestCase):
    def transcript(self, result):
        return json.dumps({"event": "result", "result": result})

    def test_result_event_parse_result_and_usage_of_success(self):
        usage = {"input_tokens": 123, "output_tokens": 45, "cache_read_tokens": 10,
                 "thinking_tokens": 7, "total_tokens": 178}
        raw = "{\"event\":\"start\"}\n" + self.transcript(
            {"status": "SUCCESS", "response": "finished", "usage": usage})
        self.assertEqual(bt_agy.result_event(raw)["usage"], usage)
        self.assertEqual(bt_agy.parse_result(raw), {"text": "finished", "cost": None,
                         "is_error": False, "limit": False})
        self.assertEqual(bt_agy.usage_of(raw), usage)

    def test_resource_exhausted_result_is_error_and_limit(self):
        raw = self.transcript({"status": "ERROR", "error": "RESOURCE_EXHAUSTED: quota reached"})
        self.assertEqual(bt_agy.parse_result(raw), {"text": "RESOURCE_EXHAUSTED: quota reached", "cost": None,
                         "is_error": True, "limit": True})

    def test_transcript_without_result_event_returns_none(self):
        raw = '{"event":"message","text":"still running"}\nplain tail'
        self.assertIsNone(bt_agy.result_event(raw))
        self.assertIsNone(bt_agy.parse_result(raw))
        self.assertIsNone(bt_agy.usage_of(raw))

    def test_runsettle_detects_agy_quota_reset_and_not_successful_quota_mention(self):
        now = 1_800_000_000
        exhausted = self.transcript({"status": "ERROR", "error": "RESOURCE_EXHAUSTED: quota. Resets in 2h30m"})
        with patch.object(bt_runsettle.time, "time", return_value=now):
            info = {"rc": 1, "text": exhausted, "parsed": bt_runsettle.parse_output(exhausted)}
            parsed = bt_runsettle.parse_output(exhausted)
            until = bt_runsettle.detect_limit(info)
        self.assertTrue(parsed["is_error"])
        self.assertGreaterEqual(until, now + 2.5 * 3600 - 1)
        self.assertLessEqual(until, now + 2.5 * 3600 + 1)

    def test_successful_run_mentioning_quota_is_not_a_limit(self):
        success = self.transcript({"status": "SUCCESS", "response": "The word quota appears in this explanation."})
        successful_info = {"rc": 0, "text": success, "parsed": bt_runsettle.parse_output(success)}
        self.assertIsNone(bt_runsettle.detect_limit(successful_info))

    def test_events_usage_maps_reported_tokens_and_nulls(self):
        usage = {"input_tokens": 123, "output_tokens": 45, "cache_read_tokens": 10,
                 "thinking_tokens": 7, "total_tokens": 178}
        raw = self.transcript({"status": "SUCCESS", "response": "ok", "usage": usage})
        self.assertEqual(bt_events.extract_usage("antigravity", raw), {
            "source": "agy-stream-json", "quality": "reported", "input_tokens": 123, "output_tokens": 45,
            "cache_read_tokens": 10, "cache_write_tokens": None, "reasoning_tokens": 7,
            "total_tokens": 178, "cost_usd_reported": None})
        self.assertEqual(bt_events.extract_usage("antigravity", ""), {
            "source": None, "quality": "unknown", "input_tokens": None, "output_tokens": None,
            "cache_read_tokens": None, "cache_write_tokens": None, "reasoning_tokens": None,
            "total_tokens": None, "cost_usd_reported": None})


class RoutingTests(AgTestCase):
    def setUp(self):
        super().setUp()
        self.now = 1_800_000_000.0
        self.time_patch = patch.object(bt_agents.time, "time", return_value=self.now)
        self.time_patch.start()
        self.addCleanup(self.time_patch.stop)
        self.profiles_patch = patch.object(bt_profiles, "load", return_value={
            "claude": {"provider": "claude", "bin": "claude", "env": {}, "work_only": False},
            "codex": {"provider": "codex", "bin": "codex", "env": {}, "work_only": False},
            "antigravity": {"provider": "antigravity", "bin": "agy", "env": {}, "work_only": False}})
        self.profiles_patch.start()
        self.addCleanup(self.profiles_patch.stop)

    def candidate_routes(self, pool, tier=1, kind="audit", **kwargs):
        import contextlib
        with contextlib.ExitStack() as stack:
            stack.enter_context(self.fake_clis())
            stack.enter_context(patch.object(bt_agents, "_stats", return_value=({}, {})))
            try:  # subscription-usage tracking is a separate feature: isolate from it only where it exists
                import bt_subscriptions
                stack.enter_context(patch.object(bt_subscriptions, "capacity", return_value=(None, None)))
                stack.enter_context(patch.object(bt_subscriptions, "load", return_value={}))
            except ImportError:
                pass
            return bt_agents.candidates("personal-project", pool, tier, kind, **kwargs)[0]

    def test_audit_prefers_antigravity_low_effort_none(self):
        routes = self.candidate_routes(["claude", "codex", "antigravity"])
        self.assertEqual((routes[0]["agent"], routes[0]["model"], routes[0]["effort"]),
                         ("antigravity", "gemini-3.8-flash-low", None))

    def test_non_audit_never_uses_antigravity_while_other_providers_are_available(self):
        for kind in ("implement", "test", "docs"):
            with self.subTest(kind=kind):
                routes = self.candidate_routes(["antigravity", "claude", "codex"], kind=kind)
                self.assertNotEqual(routes[0]["agent"], "antigravity")

    def test_antigravity_is_builder_reserve_when_claude_and_codex_cool(self):
        bt_agents.quota_mark("claude", "claude", self.now + 100)
        bt_agents.quota_mark("codex", "codex", self.now + 200)
        routes = self.candidate_routes(["claude", "codex", "antigravity"], kind="implement")
        self.assertEqual(routes[0]["agent"], "antigravity")

    def test_audit_avoids_builder_provider_when_another_provider_is_available(self):
        routes = self.candidate_routes(["claude", "codex", "antigravity"], avoid_providers={"antigravity"})
        self.assertNotEqual(routes[0]["agent"], "antigravity")

    def test_high_gemini_pressure_moves_audit_to_claude_or_codex(self):
        with patch.object(bt_agy, "capacity", return_value=(90.0, None)):
            routes = self.candidate_routes(["antigravity", "claude", "codex"])
        self.assertIn(routes[0]["agent"], {"claude", "codex"})

    def test_audit_provider_config_prefers_claude_and_none_disables_preference(self):
        bt_config.set_value("audit.provider", "claude")
        claude_routes = self.candidate_routes(["antigravity", "codex", "claude"])
        self.assertEqual(claude_routes[0]["agent"], "claude")
        bt_config.set_value("audit.provider", "none")
        no_preference = self.candidate_routes(["antigravity", "codex", "claude"])
        self.assertEqual(no_preference[0]["agent"], "antigravity")

    def test_pool_drops_antigravity_when_token_file_is_missing(self):
        token = self.home / ".gemini" / "antigravity-cli" / "antigravity-oauth-token"
        token.unlink()
        with patch.object(bt_profiles, "load", return_value={
                "antigravity": {"provider": "antigravity", "bin": "agy", "env": {}, "work_only": False}}), \
                self.fake_clis():
            self.assertEqual(bt_agents.pool_for("personal-project", ["antigravity"]), [])

    def test_model_provider_legacy_tier_and_runtime_arguments(self):
        self.assertEqual(bt_agents.provider_of_model("gemini-3.8-flash-low"), "antigravity")
        for tier in (0, 1, 2):
            model, _ = bt_agents.model_for("antigravity", tier)
            self.assertNotEqual(model, "gemini-3.8-flash-high")
            self.assertNotEqual(bt_agents.legacy_model_for({"agent": "antigravity"}, tier)[0],
                                "gemini-3.8-flash-high")
        args = bt_runtier.model_args("antigravity", "gemini-3.8-flash-low", "xhigh")
        self.assertEqual(args, ["--model", "gemini-3.8-flash-low"])

    def test_runprompt_builds_agy_argv_without_stdin(self):
        state = {"agent": "antigravity", "limits": {}}
        with patch.object(bt_agy, "exe", return_value="/fake/agy"):
            argv, stdin = bt_runprompt.agent_argv(state, self.base, "prompt")
        self.assertEqual(argv[0], "/fake/agy")
        self.assertEqual(argv[-1], "--print=prompt")
        self.assertIsNone(stdin)


class SessionIsolationTests(unittest.TestCase):
    def test_running_inside_an_agy_session_is_recognised_as_that_provider(self):
        import bt_profiles
        self.assertEqual(bt_profiles.ambient_provider({"ANTIGRAVITY_CONVERSATION_ID": "c1"}), "antigravity")
        self.assertEqual(bt_profiles.ambient_provider({"ANTIGRAVITY_AGENT": "1"}), "antigravity")
        self.assertIsNone(bt_profiles.ambient_provider({"PATH": "/bin"}))

    def test_child_sessions_never_inherit_the_parents_agy_session_state(self):
        import bt_profiles
        parent = {"ANTIGRAVITY_CONVERSATION_ID": "c1", "ANTIGRAVITY_CSRF_TOKEN": "secret", "ANTIGRAVITY_LS_ADDRESS": "x",
                  "PATH": "/bin"}
        for profile in (None, "claude"):
            env = bt_profiles.session_env(profile, "claude", parent)
            self.assertFalse([k for k in env if k.startswith("ANTIGRAVITY_")], profile)
            self.assertEqual(env["PATH"], "/bin")

    def test_a_delegation_error_lists_every_launchable_provider(self):
        import bt_delegate
        import tempfile
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(SystemExit) as ctx:
            bt_delegate.create("p", "t", None, "gemini", Path(tmp), [], None, 1, None, None, kind="docs")
        self.assertIn("antigravity", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
