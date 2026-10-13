"""Agent routing, model selection and telemetry summaries."""
from __future__ import annotations

import datetime as dt
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
import bt_core  # noqa: E402
import bt_events  # noqa: E402
import bt_lock  # noqa: E402
import bt_profiles  # noqa: E402


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="agents-test-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / "bitacora"
        self.state = self.root / ".state"
        self.state.mkdir(parents=True)
        self.workdir = self.base / "work-account"
        self.codexdir = self.base / "codex-account"
        self.workdir.mkdir()
        self.codexdir.mkdir()
        for target, attribute, value in ((bt_agents, "STATE", self.state),
                                         (bt_events, "STATE", self.state),
                                         (bt_profiles, "STATE", self.state),
                                         (bt_profiles, "ROOT", self.root),
                                         (bt_core, "STATE", self.state)):
            p = patch.object(target, attribute, value)
            p.start()
            self.addCleanup(p.stop)
        (self.root / "work-project").mkdir()
        (self.root / "work-project" / "project.json").write_text('{"work": true}')
        (self.root / "personal-project").mkdir()
        (self.root / "personal-project" / "project.json").write_text('{"work": false}')
        bt_profiles.add("claude-work", "claude", {"CLAUDE_CONFIG_DIR": str(self.workdir)}, work_only=True)
        bt_profiles.add("codex-named", "codex", {"CODEX_HOME": str(self.codexdir)})

    def cli(self, binary):
        return patch.object(bt_agents.shutil, "which", side_effect=lambda name: None if name == binary + "-missing" else "/bin/" + name)


class ModelSelectionTests(AgentTests):
    def test_infer_kind_explicit_valid_value_wins_and_normalizes(self):
        self.assertEqual(bt_agents.infer_kind("audit implementation", "  DOCS "), "docs")

    def test_infer_kind_uses_title_words_then_defaults_to_implementation(self):
        self.assertEqual(bt_agents.infer_kind("Update README and docs"), "docs")
        self.assertEqual(bt_agents.infer_kind("Review implementation"), "audit")
        self.assertEqual(bt_agents.infer_kind("Implement a new parser"), "implement")

    def test_invalid_explicit_kind_falls_back_to_title(self):
        self.assertEqual(bt_agents.infer_kind("run tests", "unknown"), "test")

    def test_start_tier_architecture_and_audit(self):
        self.assertEqual(bt_agents.start_tier(" ARCHITECTURE ", "docs"), 2)
        self.assertEqual(bt_agents.start_tier("standard", "audit"), 1)
        self.assertEqual(bt_agents.start_tier(None, "implement"), 0)

    def test_model_rank_and_provider_detection(self):
        self.assertEqual([bt_agents.rank_of(m) for m in ("haiku", "sonnet", "opus", "GPT-6.1-SOL")],
                         [0, 1, 2, 1])
        self.assertEqual(bt_agents.rank_of("custom-opus"), 2)
        self.assertEqual(bt_agents.rank_of("unknown"), 0)
        self.assertEqual(bt_agents.provider_of_model("Claude Opus"), "claude")
        self.assertEqual(bt_agents.provider_of_model("o4-mini"), "codex")
        self.assertIsNone(bt_agents.provider_of_model("mystery-model"))

    def test_model_for_claude_tiers_and_configured_model_strength(self):
        self.assertEqual(bt_agents.model_for("claude", 0), ("haiku", None))
        self.assertEqual(bt_agents.model_for("claude", 1), ("sonnet", "xhigh"))
        self.assertEqual(bt_agents.model_for("claude", 2), ("opus", "xhigh"))
        self.assertEqual(bt_agents.model_for("claude", 1, "opus"), ("opus", "xhigh"))
        self.assertEqual(bt_agents.model_for("claude", 2, "sonnet"), ("opus", "xhigh"))

    def test_model_for_codex_tiers_always_set_effort_and_docs_use_low(self):
        self.assertEqual(bt_agents.model_for("codex", 0), ("gpt-6-luna", "medium"))
        self.assertEqual(bt_agents.model_for("codex", 1), ("gpt-6.1-sol", "high"))
        self.assertEqual(bt_agents.model_for("codex", 2), ("gpt-6.1-sol", "xhigh"))
        self.assertEqual(bt_agents.model_for("codex", 0, kind="docs"), ("gpt-6-luna", "low"))
        self.assertEqual(bt_agents.model_for("codex", 1, "gpt-6-luna"), ("gpt-6.1-sol", "high"))

    def test_configured_model_is_only_kept_for_its_provider(self):
        self.assertEqual(bt_agents.model_for("claude", 0, "gpt-6.1-sol"), ("haiku", None))
        self.assertEqual(bt_agents.model_for("codex", 0, "opus"), ("gpt-6-luna", "medium"))

    def test_legacy_claude_ladder_and_stronger_configured_model(self):
        state = {"agent": "claude"}
        self.assertEqual(bt_agents.legacy_model_for(state, 0), ("haiku", None))
        self.assertEqual(bt_agents.legacy_model_for(state, 1), ("sonnet", "xhigh"))
        self.assertEqual(bt_agents.legacy_model_for(state, 2), ("opus", "xhigh"))
        self.assertEqual(bt_agents.legacy_model_for({"agent": "claude", "model": "opus"}, 1),
                         ("opus", "xhigh"))
        self.assertEqual(bt_agents.legacy_model_for({"agent": "claude", "model": "sonnet"}, 2),
                         ("opus", "xhigh"))

    def test_legacy_codex_keeps_only_codex_models_and_raises_effort_from_tier_one(self):
        self.assertEqual(bt_agents.legacy_model_for({"agent": "codex", "model": "gpt-6-luna"}, 0),
                         ("gpt-6-luna", None))
        self.assertEqual(bt_agents.legacy_model_for({"agent": "codex", "model": "gpt-6.1-sol"}, 1),
                         ("gpt-6.1-sol", "xhigh"))
        self.assertEqual(bt_agents.legacy_model_for({"agent": "codex", "model": "opus"}, 2),
                         (None, "xhigh"))


class QuotaTests(AgentTests):
    def test_profiles_for_one_account_share_quota_key(self):
        bt_profiles.add("claude-alias", "claude", {"CLAUDE_CONFIG_DIR": str(self.workdir)})
        self.assertEqual(bt_agents.account_key("claude-work"), bt_agents.account_key("claude-alias"))
        self.assertEqual(bt_agents.account_key(None, "codex"), "codex:default")
        self.assertEqual(bt_agents.account_key(None), "claude:default")

    def test_explicit_epoch_is_kept_and_cleared_by_account(self):
        now = 1_800_000_000.0
        with patch.object(bt_agents.time, "time", return_value=now):
            self.assertEqual(bt_agents.quota_mark("claude-work", "claude", now + 1234), now + 1234)
            self.assertEqual(bt_agents.cooling_until("claude-work"), now + 1234)
            self.assertTrue(bt_agents.quota_clear("claude-work"))
            self.assertIsNone(bt_agents.cooling_until("claude-work"))
            self.assertFalse(bt_agents.quota_clear("claude-work"))

    def test_unknown_epoch_cooldown_doubles_and_caps_at_four_hours(self):
        now = 1_800_000_000.0
        expected_minutes = [30, 60, 120, 240, 240]
        with patch.object(bt_agents.time, "time", return_value=now):
            for expected in expected_minutes:
                until = bt_agents.quota_mark("codex-named", "codex", 0, default_min=30)
                self.assertEqual(until, now + expected * 60)

    def test_past_epoch_is_treated_as_unknown_and_reason_is_normalized(self):
        now = 1_800_000_000.0
        with patch.object(bt_agents.time, "time", return_value=now):
            until = bt_agents.quota_mark("codex-named", "codex", now - 1, "  over\n quota  ", default_min=7)
        stored = json.loads((self.state / "quota.json").read_text())[bt_agents.account_key("codex-named")]
        self.assertEqual(until, now + 7 * 60)
        self.assertEqual(stored["reason"], "over quota")

    def test_cooling_until_expires_at_epoch(self):
        now = 1_800_000_000.0
        with patch.object(bt_agents.time, "time", return_value=now):
            bt_agents.quota_mark(None, "claude", now + 1)
            self.assertEqual(bt_agents.cooling_until(None, "claude"), now + 1)
        with patch.object(bt_agents.time, "time", return_value=now + 1):
            self.assertIsNone(bt_agents.cooling_until(None, "claude"))


class PoolAndRouteTests(AgentTests):
    def _all_clis(self):
        return patch.object(bt_agents.shutil, "which", return_value="/bin/fake-cli")

    def test_pool_applies_work_gate_and_preserves_work_profile_for_work_projects(self):
        with self._all_clis():
            self.assertNotIn("claude-work", bt_agents.pool_for("personal-project", ["claude-work"]))
            self.assertEqual(bt_agents.pool_for("work-project", ["claude-work"]), ["claude-work"])

    def test_pool_drops_generic_duplicate_when_named_profile_covers_account(self):
        bt_profiles.add("claude-alias", "claude", {})
        with self._all_clis():
            self.assertEqual(bt_agents.pool_for("personal-project", ["claude", "claude-alias"]), ["claude"])
            self.assertEqual(bt_agents.pool_for("personal-project", ["claude-alias", "claude"]), ["claude-alias"])

    def test_pool_rejects_unknown_requested_profile(self):
        with self._all_clis(), self.assertRaises(bt_profiles.ProfileError):
            bt_agents.pool_for("personal-project", ["absent"])

    def test_pool_skips_missing_cli_and_missing_account_directory(self):
        bt_profiles.add("claude-missing-cli", "claude", {}, binary="claude-missing")
        bt_profiles.add("claude-missing-dir", "claude", {"CLAUDE_CONFIG_DIR": str(self.base / "absent")})
        with patch.object(bt_agents.shutil, "which", side_effect=lambda b: None if b == "claude-missing" else "/bin/" + b):
            self.assertEqual(bt_agents.pool_for("personal-project", ["claude-missing-cli", "claude-missing-dir"]), [])

    def test_pool_keeps_requested_order(self):
        with self._all_clis():
            self.assertEqual(bt_agents.pool_for("personal-project", ["codex-named", "claude"]),
                             ["codex-named", "claude"])

    def test_fixed_route_uses_legacy_model_and_pool_route_selects_candidate(self):
        fixed = bt_agents.route("personal-project", {"agent": "claude", "profile": "claude"}, 1, "audit")
        self.assertEqual((fixed["profile"], fixed["model"], fixed["effort"], fixed["why"]),
                         ("claude", "sonnet", "xhigh", "fixed (no pool)"))
        with self._all_clis():
            pooled = bt_agents.route("personal-project", {"pool": ["codex-named", "claude"]}, 0)
        self.assertEqual(pooled["profile"], "codex-named")

    def test_route_raises_no_route_when_every_account_cools(self):
        with self._all_clis(), patch.object(bt_agents.time, "time", return_value=1_800_000_000.0):
            bt_agents.quota_mark("claude", "claude", 1_800_000_100.0)
            bt_agents.quota_mark("codex-named", "codex", 1_800_000_200.0)
            with self.assertRaises(bt_agents.NoRoute) as ctx:
                bt_agents.route("personal-project", {"pool": ["claude", "codex-named"]}, 1)
            self.assertEqual(ctx.exception.until, 1_800_000_100.0)


class CandidateRankingTests(AgentTests):
    def setUp(self):
        super().setUp()
        self.now = 1_800_000_000.0
        self.time_patch = patch.object(bt_agents.time, "time", return_value=self.now)
        self.time_patch.start()
        self.addCleanup(self.time_patch.stop)
        self.rows = []
        self.events_patch = patch.object(bt_events, "read_all", side_effect=lambda: self.rows)
        self.events_patch.start()
        self.addCleanup(self.events_patch.stop)
        self.cli_patch = patch.object(bt_agents.shutil, "which", return_value="/bin/fake-cli")
        self.cli_patch.start()
        self.addCleanup(self.cli_patch.stop)

    def event(self, profile, agent, model, result="done", seconds=10, kind="implement", age=60):
        stamp = dt.datetime.fromtimestamp(self.now - age, tz=dt.timezone.utc).isoformat()
        return {"profile": profile, "agent": agent, "model": model, "kind": kind, "result": result,
                "seconds": seconds, "ts": stamp}

    def populate_rates(self, profile, agent, model, done, failed, kind="implement"):
        self.rows.extend(self.event(profile, agent, model, "done" if i < done else "failed", kind=kind)
                         for i in range(done + failed))

    def test_cooling_accounts_are_excluded_and_earliest_reset_is_returned(self):
        bt_agents.quota_mark("claude", "claude", self.now + 200)
        bt_agents.quota_mark("codex-named", "codex", self.now + 100)
        routes, soonest = bt_agents.candidates("personal-project", ["claude", "codex-named"], 0)
        self.assertEqual(routes, [])
        self.assertEqual(soonest, self.now + 100)

    def test_avoid_provider_moves_it_last_but_does_not_remove_only_candidate(self):
        routes, _ = bt_agents.candidates("personal-project", ["claude", "codex-named"], 0,
                                         avoid_providers={"claude"})
        self.assertEqual([r["agent"] for r in routes], ["codex", "claude"])
        only, _ = bt_agents.candidates("personal-project", ["claude"], 0, avoid_providers={"claude"})
        self.assertEqual([r["agent"] for r in only], ["claude"])

    def test_measured_success_rate_wins_after_minimum_samples(self):
        self.populate_rates("claude", "claude", "haiku", 5, 0)
        self.populate_rates("codex-named", "codex", "gpt-6-luna", 3, 2)
        routes, _ = bt_agents.candidates("personal-project", ["codex-named", "claude"], 0)
        self.assertEqual([r["agent"] for r in routes], ["claude", "codex"])

    def test_success_rate_is_ignored_below_minimum_samples(self):
        self.populate_rates("claude", "claude", "haiku", 4, 0)
        self.populate_rates("codex-named", "codex", "gpt-6-luna", 0, 4)
        routes, _ = bt_agents.candidates("personal-project", ["codex-named", "claude"], 0)
        self.assertEqual([r["agent"] for r in routes], ["codex", "claude"])

    def test_a_small_rate_difference_is_noise_and_leaves_the_tie_to_load_and_pool_order(self):
        # Deliberate: rates are compared in 20-point bands. 82% vs 90% over a few dozen attempts is not evidence, and
        # keeping the tie lets quota balancing (load, pool order) decide instead of piling work on one account.
        self.populate_rates("claude", "claude", "haiku", 41, 9)
        self.populate_rates("codex-named", "codex", "gpt-6-luna", 45, 5)
        routes, _ = bt_agents.candidates("personal-project", ["claude", "codex-named"], 0)
        self.assertEqual([r["agent"] for r in routes], ["claude", "codex"])

    def test_heavier_recent_load_loses_and_pool_order_breaks_remaining_ties(self):
        self.rows.extend(self.event("claude", "claude", "haiku", seconds=7200) for _ in range(1))
        routes, _ = bt_agents.candidates("personal-project", ["claude", "codex-named"], 0)
        self.assertEqual([r["agent"] for r in routes], ["codex", "claude"])
        self.rows.clear()
        routes, _ = bt_agents.candidates("personal-project", ["codex-named", "claude"], 0)
        self.assertEqual([r["agent"] for r in routes], ["codex", "claude"])


class CatalogTests(AgentTests):
    def test_catalog_lists_models_work_gate_cooling_and_pool(self):
        now = 1_800_000_000.0
        with patch.object(bt_agents.time, "time", return_value=now), patch.object(
                bt_agents.time, "localtime", return_value=time.gmtime(now + 3600)), \
                patch.object(bt_agents.shutil, "which", side_effect=lambda b: None if b == "codex" else "/bin/" + b):
            bt_agents.quota_mark("claude-work", "claude", now + 3600)
            cat = bt_agents.catalog("personal-project")
        self.assertEqual({m["id"] for m in cat["models"]}, set(bt_agents.MODELS))
        work = next(a for a in cat["accounts"] if a["profile"] == "claude-work")
        self.assertTrue(work["work_only"])
        self.assertFalse(work["allowed_here"])
        self.assertIsNotNone(work["cooling_until"])
        self.assertEqual(cat["pool"], ["claude"])
        self.assertEqual(len(cat["ladder"]["codex"]), 3)

    def test_brief_shows_models_account_flags_and_only_one_duplicate_account(self):
        bt_profiles.add("claude-alias", "claude", {})
        with patch.object(bt_agents.shutil, "which", return_value="/bin/fake-cli"), patch.object(
                bt_agents.time, "time", return_value=1_800_000_000.0):
            bt_agents.quota_mark("claude-work", "claude", 1_800_000_300.0)
            text = bt_agents.brief("personal-project")
        self.assertIn("`haiku`", text)
        self.assertIn("`gpt-6.1-sol`", text)
        self.assertIn("work projects only", text)
        self.assertIn("NOT allowed for this project", text)
        self.assertIn("usage limit until", text)
        self.assertEqual(text.count("(claude"), 2)  # work account plus one representation of the default account
        self.assertNotIn("`claude` (claude", text)


class EventSummaryTests(AgentTests):
    def test_summary_groups_by_default_and_uses_implicit_implement_kind(self):
        rows = [
            {"agent": "claude", "profile": "a", "model": "haiku", "effort": None, "result": "done",
             "seconds": 10, "usage": {"total_tokens": 100}},
            {"agent": "claude", "profile": "a", "model": "haiku", "effort": None, "result": "usage_limit",
             "seconds": 20, "usage": {"total_tokens": 200}},
            {"agent": "codex", "profile": "b", "model": "gpt-6-luna", "effort": "low", "result": "failed",
             "seconds": 30, "usage": {}},
        ]
        groups = bt_events.summary(rows)
        self.assertEqual(len(groups), 2)
        claude = next(g for g in groups if g["agent"] == "claude")
        self.assertEqual((claude["attempts"], claude["done"], claude["other"], claude["success_rate"]),
                         (2, 1, 1, 1.0))
        self.assertEqual(claude["tokens_per_done"], 300)
        self.assertEqual(claude["coverage"], 1.0)

    def test_summary_custom_grouping_cost_and_tokens_require_complete_measurement(self):
        rows = [
            {"agent": "claude", "kind": "docs", "result": "done", "seconds": 10,
             "usage": {"input_tokens": 10, "output_tokens": 20, "cache_read_tokens": 3,
                       "cache_write_tokens": 2, "cost_usd_reported": 0.1234}},
            {"agent": "claude", "kind": "docs", "result": "verified", "seconds": 20,
             "usage": {"total_tokens": 40, "cost_usd_reported": 0.2}},
            {"agent": "claude", "kind": "docs", "result": "failed", "seconds": 30,
             "usage": {"total_tokens": None, "cost_usd_reported": 0.1}},
        ]
        row = bt_events.summary(rows, by=("kind",))[0]
        self.assertEqual(row["kind"], "docs")
        self.assertEqual(row["attempts"], 3)
        self.assertEqual(row["success_rate"], 0.67)
        self.assertIsNone(row["tokens_per_done"])
        self.assertEqual(row["cost_usd_reported"], 0.4234)
        self.assertEqual(bt_events.summary(rows, by=("not-a-key",))[0]["attempts"], 3)

    def test_tokens_per_done_is_reported_when_every_attempt_has_tokens(self):
        rows = [{"result": "done", "usage": {"input_tokens": 10, "output_tokens": 20}},
                {"result": "verified", "usage": {"total_tokens": 60}}]
        row = bt_events.summary(rows, by=("project",))[0]
        self.assertEqual(row["tokens_per_done"], 45)

    def test_advice_waits_for_threshold_then_compares_enough_judged_attempts(self):
        rows = []
        rows.extend({"agent": "claude", "model": "haiku", "effort": None, "kind": "test",
                     "result": "done" if i < 3 else "failed", "seconds": 10} for i in range(4))
        self.assertEqual(bt_events.advice(rows), ["not enough data yet: a group needs 5 judged attempts before it is compared"])
        rows.append({"agent": "claude", "model": "haiku", "effort": None, "kind": "test",
                     "result": "done", "seconds": 10})
        rows.extend({"agent": "codex", "model": "gpt-6-luna", "effort": "low", "kind": "test",
                     "result": "failed", "seconds": 20} for _ in range(5))
        advice = bt_events.advice(rows)
        self.assertIn("test: best measured is claude/haiku (80% of 5, 10s avg)", advice)
        self.assertTrue(any("codex/gpt-6-luna" in line and "consider starting it one tier up" in line
                            for line in advice))


if __name__ == "__main__":
    unittest.main()
