"""Regression tests for the five harness defects (FIX): token normalization, task-level learning, quality-protected
balancing, coverage-aware efficiency and a real exploration budget. Deterministic, no provider calls, AC-nn = the
acceptance case of the FIX brief."""
from __future__ import annotations

import datetime as dt
import json
import sys
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_agents import AgentTests  # noqa: E402  (configures the disposable root)

import bt_agents  # noqa: E402
import bt_efficiency  # noqa: E402
import bt_events  # noqa: E402
import bt_explore  # noqa: E402
import bt_outcomes  # noqa: E402
import bt_routing_policy as policy  # noqa: E402
import bt_scheduler_decision_adapter as adapter  # noqa: E402
import bt_usage  # noqa: E402

NOW = 1_800_000_000.0
STAMP = dt.datetime.fromtimestamp(NOW - 60, tz=dt.timezone.utc).isoformat()

CODEX_RAW = json.dumps({"type": "turn.completed", "usage": {"input_tokens": 1000, "cached_input_tokens": 800,
                                                            "output_tokens": 200}})
CLAUDE_RAW = json.dumps({"type": "result", "total_cost_usd": 0.5, "usage": {
    "input_tokens": 10, "output_tokens": 20, "cache_read_input_tokens": 100, "cache_creation_input_tokens": 50}})
CLAUDE_CUT = "\n".join(json.dumps({"type": "assistant", "message": {"id": f"m{i}", "usage": {
    "input_tokens": 5, "output_tokens": 5, "cache_read_input_tokens": 10, "cache_creation_input_tokens": 0}}})
                       for i in range(2))
AGY_RAW = json.dumps({"event": "result", "result": {"status": "SUCCESS", "usage": {
    "input_tokens": 300, "output_tokens": 50, "total_tokens": 350}}})


def session(result="done", tasks=None, results=None, model="sonnet", agent="claude", profile="p1", tokens=True,
            seconds=100, kind="implement", **extra):
    ids = tasks or ["T1"]
    usage = {"source": "claude-stream-json", "quality": "reported", "input_tokens": 10, "output_tokens": 20,
             "cache_read_tokens": 0, "cache_write_tokens": 0} if tokens else {}
    row = {"agent": agent, "profile": profile, "model": model, "effort": "medium", "kind": kind, "tier": 1,
           "result": result, "seconds": seconds, "usage": usage, "origin": "real", "project": "pr", "req": "REQ-1", "run_id": "run-1",
           "event_id": f"e{id(ids)}{len(extra)}{result}{model}", "tasks": ids, "task": "+".join(ids), "ts": STAMP}
    if results is not None:
        row["task_results"] = results
    return {**row, **extra}


class UsageSemantics(unittest.TestCase):
    def test_codex_cached_tokens_are_a_subset_of_input_and_not_added_twice(self):  # AC-01
        usage = bt_events.extract_usage("codex", CODEX_RAW)
        norm = bt_usage.normalize(usage, "codex")
        self.assertEqual((norm["total"], norm["quality"], norm["comparable"]), (1200, "complete", True))
        row = {"agent": "codex", "usage": usage}
        self.assertEqual(bt_events._tokens(usage, "codex"), 1200)
        self.assertEqual(bt_efficiency._tokens(row), 1200)
        self.assertEqual(adapter._token_count(row), 1200)

    def test_claude_counts_cache_reads_and_writes_in_addition_to_input(self):  # AC-02
        usage = bt_events.extract_usage("claude", CLAUDE_RAW)
        self.assertEqual(usage["cache_write_tokens"], 50)
        self.assertEqual(bt_usage.normalize(usage, "claude")["total"], 180)
        self.assertEqual({bt_events._tokens(usage, "claude"), bt_efficiency._tokens({"agent": "claude", "usage": usage}),
                          adapter._token_count({"agent": "claude", "usage": usage})}, {180})

    def test_a_cut_stream_is_partial_and_never_a_final_total(self):  # AC-03
        usage = bt_events.extract_usage("claude", CLAUDE_CUT)
        norm = bt_usage.normalize(usage, "claude")
        self.assertEqual((norm["quality"], norm["total"], norm["comparable"]), ("partial", 40, False))
        self.assertIsNone(bt_events._tokens(usage, "claude"))
        self.assertIsNone(adapter._token_count({"agent": "claude", "usage": usage}))
        group = bt_events.summary([{"agent": "claude", "result": "done", "usage": usage}], by=("agent",))[0]
        self.assertEqual((group["measured"], group["tokens_measured"], group["tokens_unreliable"]), (0, 0, 1))
        self.assertIsNone(group["tokens_per_done"])

    def test_missing_counters_are_not_invented_and_zero_is_not_absence(self):  # AC-04
        self.assertIsNone(bt_usage.measured_total({}, "claude"))
        self.assertEqual(bt_usage.normalize(None, "codex")["quality"], "unknown")
        only_input = {"input_tokens": 10, "output_tokens": 5}  # Claude without cache counters: lower bound, not final
        self.assertEqual(bt_usage.normalize(only_input, "claude")["quality"], "partial")
        zero = {"input_tokens": 0, "output_tokens": 0, "cache_read_tokens": 0, "cache_write_tokens": 0}
        self.assertEqual(bt_usage.measured_total(zero, "claude"), 0)  # a measured zero, unlike an absent measurement

    def test_total_only_and_antigravity_totals_stay_provider_specific(self):
        text = bt_events.extract_usage("codex", "tokens used\n12,345\n")
        norm = bt_usage.normalize(text, "codex")
        self.assertEqual((norm["quality"], norm["total"], norm["comparable"]), ("total_only", 12345, False))
        self.assertEqual(bt_usage.measured_total(text, "codex"), 12345)
        self.assertIsNone(bt_usage.comparable_total(text, "codex"))
        agy = bt_events.extract_usage("antigravity", AGY_RAW)
        self.assertEqual(bt_usage.normalize(agy, "antigravity")["total"], 350)
        self.assertFalse(bt_usage.normalize(agy, "antigravity")["comparable"])

    def test_contradictory_and_malformed_records_are_not_comparable_and_never_negative(self):
        cache_over_input = {"input_tokens": 10, "output_tokens": 5, "cache_read_tokens": 99}
        self.assertEqual(bt_usage.normalize(cache_over_input, "codex")["quality"], "contradictory")
        wrong_total = {"input_tokens": 10, "output_tokens": 5, "total_tokens": 999}
        self.assertEqual(bt_usage.normalize(wrong_total, "codex")["quality"], "contradictory")
        self.assertIsNone(bt_usage.comparable_total(wrong_total, "codex"))
        for bad in ({"input_tokens": -5, "output_tokens": 5}, {"input_tokens": True, "output_tokens": "5"}, "text", 7):
            n = bt_usage.normalize(bad, "codex")
            self.assertTrue(n["total"] is None or n["total"] >= 0)
            self.assertNotEqual(n["quality"], "complete")

    def test_legacy_rows_without_agent_or_quality_are_still_read(self):  # AC-16 (usage side)
        self.assertEqual(bt_usage.measured_total({"total_tokens": 60}), 60)
        self.assertEqual(bt_usage.measured_total({"input_tokens": 10, "output_tokens": 20}), 30)


class TaskOutcomes(AgentTests):
    def test_two_verified_and_one_failed_task_are_three_outcomes_not_a_failed_session(self):  # AC-05
        rows = [session("partial", ["T1", "T2", "T3"], {"T1": "done", "T2": "done", "T3": "verify_failed"})]
        counts = bt_outcomes.counts(rows)[("claude", "sonnet", "medium", "implement")]
        self.assertEqual((counts["verified"], counts["failed"], counts["judged"]), (2, 1, 3))
        with patch.object(bt_events, "read_all", return_value=rows):
            rates, _ = bt_agents._stats()
        self.assertEqual(rates.samples[("claude", "sonnet", "medium", "implement")], 3)

    def test_three_verified_tasks_cost_one_session(self):  # AC-06
        rows = [session("done", ["T1", "T2", "T3"], {"T1": "done", "T2": "done", "T3": "done"})]
        group = bt_efficiency.summarize(rows)[0]
        self.assertEqual((group["verified"], group["sessions"], group["shared_sessions"], group["tokens_measured"]),
                         (3, 1, 1, 30))
        self.assertEqual(group["measured_tokens_per_verified"], 10)  # a conserving average of ONE session's cost

    def test_skipped_and_unjudged_results_neither_reward_nor_penalise(self):  # AC-07
        rows = [session("partial", ["T1", "T2", "T3"], {"T1": "done", "T2": "skipped", "T3": "claimed"}),
                session("partial", tasks=["T4"], event_id="legacy")]  # legacy aggregate partial
        counts = bt_outcomes.counts(rows)[("claude", "sonnet", "medium", "implement")]
        self.assertEqual((counts["verified"], counts["failed"], counts["skipped"], counts["unjudged"]), (1, 0, 1, 2))
        self.assertEqual(counts["judged"], 1)

    def test_a_replayed_or_recovered_row_does_not_duplicate_outcomes(self):  # AC-08
        attempt = session("done", ["T1"], {"T1": "done"}, event_id="a", attempt=1)
        replay = {**attempt, "event_id": "b", "recovered": True}                    # same task, same attempt
        elsewhere = {**attempt, "event_id": "c", "model": "opus", "attempt": 2}      # verified again by another route
        self.assertEqual(len(bt_outcomes.outcomes([attempt, replay, elsewhere])), 1)
        counts = bt_outcomes.counts([attempt, replay, elsewhere], ("model",))
        self.assertEqual(sum(g["verified"] for g in counts.values()), 1)

    def test_a_retry_is_an_attempt_not_a_second_completed_task(self):  # AC-19
        first = session("failed", ["T1"], {"T1": "failed"}, event_id="a", attempt=1, seconds=50)
        second = session("done", ["T1"], {"T1": "done"}, event_id="b", attempt=2, seconds=70)
        group = bt_efficiency.summarize([first, second])[0]
        self.assertEqual((group["attempts"], group["verified"], group["failed"], group["retries"], group["sessions"]),
                         (2, 1, 1, 1, 2))
        self.assertEqual(group["retry_rate"], 0.5)
        self.assertEqual(group["seconds"], 120)                                     # each session's cost exactly once

    def test_detail_for_records_a_stable_outcome_per_task(self):
        tasks = [{"id": "T1", "kind": "implement", "attempts": 0}, {"id": "T2", "kind": "docs", "attempts": 1}]
        detail = bt_events.detail_for(tasks, "partial", {"T1": "done", "T2": "failed"})
        self.assertEqual(detail["task_outcomes"], [{"id": "T1", "kind": "implement", "result": "done", "attempt": 1},
                                                   {"id": "T2", "kind": "docs", "result": "failed", "attempt": 1}])

    def test_synthetic_origin_and_provider_loss_do_not_contaminate_quality(self):  # AC-17 (separation)
        audit = session("done", ["A"], {"A": "done"}, kind="audit", event_id="x")
        smoke = session("failed", ["T9"], {"T9": "failed"}, origin="synthetic", event_id="y")
        quota = session("failed", ["T8"], {"T8": "failed"}, loss="usage_limit", event_id="z")
        counts = bt_outcomes.counts([audit, smoke, quota])
        self.assertEqual(counts[("claude", "sonnet", "medium", "audit")]["verified"], 1)
        implement = counts[("claude", "sonnet", "medium", "implement")]
        self.assertEqual((implement["failed"], implement["provider_loss"], implement["judged"]), (0, 1, 0))

    def test_decision_engine_history_reads_the_same_verdicts(self):  # AC-17 (consumer)
        rows = [session("partial", ["T1", "T2", "T3"], {"T1": "done", "T2": "done", "T3": "verify_failed"})]
        history = adapter._history_snapshot(rows)[("claude", "sonnet", "p1", "medium", "implement")]
        self.assertEqual((history.verified_successes, history.verified_failures), (2, 1))
        self.assertEqual(history.token_samples, 1)                                   # tokens of one session, once

    def test_review_findings_stop_is_unjudged_and_attemptless_rows_are_distinct_sessions(self):
        with patch.object(bt_events, "extract_usage", return_value={}):
            path = bt_events.record_attempt(
                "pr", {"req": "REQ-9", "agent": "claude"}, "T1", 1, {"agent": "claude", "model": "sonnet"}, "stopped",
                {"task_outcomes": [{"id": "T1", "kind": "implement", "result": "failed", "attempt": 1}]})
        row = json.loads(path.read_text().splitlines()[-1])
        self.assertEqual(bt_outcomes.counts([row])[("claude", "sonnet", None, "implement")]["judged"], 0)
        final_fail = session("failed", ["FINAL"], None, event_id="f1")
        final_ok = session("done", ["FINAL"], None, event_id="f2")
        counts = bt_outcomes.counts([final_fail, final_ok])[("claude", "sonnet", "medium", "implement")]
        self.assertEqual((counts["failed"], counts["verified"]), (1, 1))

    def test_summary_keeps_the_session_success_rate_and_adds_the_task_view(self):
        rows = [session("partial", ["T1", "T2", "T3"], {"T1": "done", "T2": "done", "T3": "verify_failed"})]
        group = bt_events.summary(rows, by=("agent",))[0]
        self.assertEqual((group["task_success_rate"], group["success_rate"]), (0.67, 0.0))


class RouterBase(AgentTests):
    def setUp(self):
        super().setUp()
        self.rows = []
        for patcher in (patch.object(bt_agents.time, "time", return_value=NOW),
                        patch.object(bt_events, "read_all", side_effect=lambda: self.rows),
                        patch.object(bt_explore, "STATE", self.state),
                        patch.object(bt_agents.shutil, "which", return_value="/bin/fake-cli")):
            patcher.start()
            self.addCleanup(patcher.stop)

    def attempts(self, profile, agent, model, done, failed, kind="implement", effort=None):
        for i in range(done + failed):
            self.rows.append({"profile": profile, "agent": agent, "model": model, "kind": kind, "effort": effort,
                              "result": "done" if i < done else "failed", "seconds": 10, "ts": STAMP})

    def usage(self, profile, five, seven):
        provider = "claude" if profile == "claude" else "codex"
        return {bt_agents.account_key(profile, provider): {
            "status": "ok", "observed_at": NOW - 60, "profile": profile, "provider": provider,
            "windows": {"five_hour": {"used_percent": five, "resets_at": NOW + 3600, "window_minutes": 300},
                        "seven_day": {"used_percent": seven, "resets_at": NOW + 3 * 86400, "window_minutes": 10080}}}}

    def order(self, usage, kind="implement", tier=0, **kw):
        with patch("bt_subscriptions.load", return_value=usage):
            routes, _ = bt_agents.candidates("personal-project", ["claude", "codex-named"], tier, kind, **kw)
        return routes


class QualityProtection(RouterBase):
    def setUp(self):
        super().setUp()
        self.attempts("claude", "claude", "haiku", 38, 2)             # A: 95 % verified over 40 outcomes
        self.attempts("codex-named", "codex", "gpt-6-luna", 20, 20, effort="medium")   # B: 50 % over 40
        # A is the busier subscription (70 %), B has room (20 %): the fixture of the brief
        self.usage_rows = {**self.usage("claude", 70, 70), **self.usage("codex-named", 20, 20)}

    def test_critical_work_does_not_follow_quota_to_a_clearly_inferior_route(self):  # AC-09
        routes = self.order(self.usage_rows, risk="high")
        self.assertEqual(routes[0]["agent"], "claude")
        self.assertIn("critical work: verified quality before quota", routes[0]["why"])
        self.assertIn("lower bound", routes[0]["why"])
        self.assertEqual(len(routes), 2)                                            # the inferior route stays as fallback

    def test_routine_work_may_follow_quota_between_comparable_routes(self):
        self.rows.clear()
        self.attempts("claude", "claude", "haiku", 36, 4)             # 90 %
        self.attempts("codex-named", "codex", "gpt-6-luna", 32, 8, effort="medium")    # 80 %: within the quality gap
        self.assertEqual(self.order(self.usage_rows)[0]["agent"], "codex")

    def test_routine_work_still_avoids_a_clearly_inferior_route_and_the_policy_is_configurable(self):
        self.assertEqual(self.order(self.usage_rows)[0]["agent"], "claude")
        with patch.object(policy, "config", side_effect=lambda k, d: "off" if k.endswith("protection") else d):
            self.assertEqual(self.order(self.usage_rows, risk="high")[0]["agent"], "codex")   # quota-first when off
        with patch.object(policy, "config", side_effect=lambda k, d: 0.6 if k.endswith("quality_gap") else d):
            self.assertEqual(self.order(self.usage_rows)[0]["agent"], "codex")                # a wider gap tolerates it

    def test_a_small_sample_is_not_relegated_by_its_own_uncertainty(self):
        self.rows.clear()
        self.attempts("claude", "claude", "haiku", 50, 0)             # proven: lower bound ~0.96
        self.attempts("codex-named", "codex", "gpt-6-luna", 8, 2, effort="medium")     # 80 % observed, lower bound ~0.60
        self.assertEqual(self.order(self.usage_rows)[0]["agent"], "codex")   # 16-point gap < 0.25: quota decides

    def test_missing_history_never_blocks_a_task(self):  # AC-10
        self.rows.clear()
        for risk in (None, "high"):
            routes = self.order(self.usage_rows, risk=risk)
            self.assertEqual(len(routes), 2)
            self.assertTrue(all(r["tier"] == 0 for r in routes))

    def test_a_small_lucky_sample_does_not_outrank_a_proven_route_on_critical_work(self):
        self.rows.clear()
        self.attempts("claude", "claude", "haiku", 190, 10)           # 95 % over 200
        self.attempts("codex-named", "codex", "gpt-6-luna", 5, 0, effort="medium")     # 100 % over 5: lower bound 0.72
        self.assertEqual(self.order(self.usage_rows, risk="high")[0]["agent"], "claude")

    def test_tier_floor_and_account_restrictions_survive(self):
        routes = self.order(self.usage_rows, tier=2, risk="high")
        self.assertTrue(all(bt_agents.rank_of(r["model"]) >= 2 or r["agent"] == "codex" for r in routes))
        self.assertEqual({r["tier"] for r in routes}, {2})


class LearningRouter(RouterBase):
    """The learning router (exploration, effort evidence) is what these classes test. A kind with an owner role is routed
    by the role policy instead (bt_role_policy), so the role lookup is switched off to reach the learning path."""

    def setUp(self):
        super().setUp()
        import bt_role_policy
        patcher = patch.object(bt_role_policy, "role_for_kind", return_value=None)
        patcher.start()
        self.addCleanup(patcher.stop)


class ExplorationBudget(LearningRouter):
    def pool_state(self):
        return {"pool": ["claude", "codex-named"], "req": "REQ-1", "agent": "claude"}

    def route(self, **kw):
        with patch("bt_subscriptions.load", return_value={}):
            return bt_agents.route("personal-project", self.pool_state(), kw.pop("tier", 1), **kw)

    def seed_proven_sonnet(self):
        self.attempts("claude", "claude", "sonnet", 20, 0, effort="medium")

    def test_ordinary_runs_do_not_spend_the_exploration_budget(self):  # AC-13
        self.seed_proven_sonnet()
        for _ in range(5):  # five ordinary, unjudged attempts of the expensive route (claimed, never verified)
            self.rows.append({"profile": "codex-named", "agent": "codex", "model": "gpt-6.1-sol", "kind": "implement",
                              "result": "claimed", "seconds": 5, "ts": STAMP})
        self.assertEqual(bt_explore.used(NOW), ({}, 0))
        chosen = self.route()
        self.assertEqual(chosen["decision"]["kind"], "explore")
        self.assertEqual(chosen["model"], "gpt-6.1-sol")

    def test_five_admitted_explorations_exhaust_the_weekly_budget(self):  # AC-14
        self.seed_proven_sonnet()
        kinds = [self.route()["decision"]["kind"] for _ in range(6)]
        self.assertEqual(kinds, ["explore"] * 5 + ["exploit"])
        record = [json.loads(line) for line in (self.state / "explore.jsonl").read_text().splitlines()][0]
        self.assertEqual((record["agent"], record["model"], record["kind"], record["tier"]),
                         ("codex", "gpt-6.1-sol", "implement", 1))
        self.assertIn("cold start", record["reason"])
        self.assertEqual(record["budget_before"]["route_used"], 0)
        self.assertEqual(bt_explore.used(NOW)[0], {("codex", "gpt-6.1-sol"): 5})   # the budget survives a restart

    def test_budget_is_configurable_and_a_global_cap_applies(self):
        self.seed_proven_sonnet()
        with patch.object(bt_agents, "_config", side_effect=lambda k, d: 2 if k.endswith("budget_week") else d):
            self.assertEqual([self.route()["decision"]["kind"] for _ in range(3)], ["explore", "explore", "exploit"])

    def test_two_workers_cannot_overspend_the_same_balance(self):  # AC-15
        route = {"agent": "codex", "model": "gpt-6.1-sol", "kind": "implement", "tier": 1}
        admitted, barrier = [], threading.Barrier(8)

        def worker():
            barrier.wait()
            admitted.append(bt_explore.reserve(route, "pr", "REQ-1", "test", 5, None, NOW) is not None)

        threads = [threading.Thread(target=worker) for _ in range(8)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        self.assertEqual(sum(admitted), 5)
        self.assertEqual(bt_explore.used(NOW)[1], 5)

    def test_critical_work_never_explores_and_a_lone_candidate_is_not_an_exploration(self):
        self.seed_proven_sonnet()
        self.assertEqual(self.route(risk="high")["decision"]["kind"], "exploit")
        self.assertEqual(bt_explore.used(NOW)[1], 0)
        with patch("bt_subscriptions.load", return_value={}):
            lone = bt_agents.route("personal-project", {"pool": ["codex-named"], "req": "R"}, 1)
        self.assertEqual(lone["decision"]["kind"], "exploit")                         # forced, not selected by the policy
        self.assertEqual(bt_explore.used(NOW)[1], 0)

    def test_fallback_escalation_and_explicit_are_classified_separately(self):
        self.seed_proven_sonnet()
        with patch.object(bt_agents, "cooling_until", side_effect=lambda p, a=None: NOW + 600 if p == "codex-named"
                          else None):
            self.assertEqual(self.route()["decision"]["kind"], "fallback")
        self.assertEqual(self.route(avoid_providers={"codex"})["decision"]["kind"], "escalation")
        pinned = bt_agents.route("personal-project", {"agent": "claude"}, 1)
        self.assertEqual(pinned["decision"]["kind"], "explicit")
        self.assertEqual(bt_explore.used(NOW)[1], 0)

    def test_cold_start_still_works_without_any_history_and_legacy_rows_count_for_nothing(self):  # AC-16
        self.rows.append({"agent": "codex", "model": "gpt-6.1-sol", "result": "done", "kind": "implement"})  # no decision
        chosen = self.route(tier=0)
        self.assertIn(chosen["agent"], ("claude", "codex"))
        self.assertEqual(bt_explore.used(NOW)[1], 0 if chosen["decision"]["kind"] != "explore" else 1)

    def test_attempt_row_carries_the_decision_and_settles_the_ledger(self):
        record = bt_explore.reserve({"agent": "codex", "model": "gpt-6.1-sol", "kind": "implement", "tier": 1}, "pr",
                                    "REQ-1", "why", 5, None, NOW)
        decision = bt_explore.decision_for("explore", "why", record)
        with patch.object(bt_events, "extract_usage", return_value={}):
            path = bt_events.record_attempt("pr", {"req": "REQ-1", "agent": "codex"}, "T1", 1,
                                            {"agent": "codex", "model": "gpt-6.1-sol", "decision": decision}, "done")
        row = json.loads(path.read_text().splitlines()[-1])
        self.assertEqual(row["decision"]["decision_id"], record["decision_id"])
        settled = [json.loads(line) for line in (self.state / "explore.jsonl").read_text().splitlines()][-1]
        self.assertEqual((settled["type"], settled["result"], settled["verified"]), ("settle", "done", True))


class EfficiencyCoverage(AgentTests):
    def test_two_accounts_of_one_provider_never_mix(self):  # AC-11
        rows = [session("done", profile="acct-a"), session("done", profile="acct-b", event_id="o")]
        with patch.object(bt_agents, "account_key", side_effect=lambda p, a: f"{a}:{p}"):
            groups = bt_efficiency.summarize(rows)
        self.assertEqual(sorted(g["account"] for g in groups), ["claude:acct-a", "claude:acct-b"])
        self.assertTrue(all(g["sessions"] == 1 for g in groups))

    def test_incomplete_telemetry_is_flagged_and_never_published_as_a_kpi(self):  # AC-12
        group = bt_efficiency.summarize([session("done", tokens=False)])[0]
        self.assertIsNone(group["measured_tokens_per_verified"])
        self.assertEqual(group["measured_tokens_status"], "insufficient_coverage")
        self.assertEqual(group["token_coverage"], 0.0)
        self.assertIn("not tokens", group["units"]["estimated_units"])

    def test_four_attempts_two_measured_keep_partial_aggregates_labelled(self):
        rows = [session("done", tokens=True, event_id="1"), session("done", tokens=True, event_id="2", tasks=["T2"]),
                session("done", tokens=False, event_id="3", tasks=["T3"]),
                session("done", tokens=False, event_id="4", tasks=["T4"])]
        group = bt_efficiency.summarize(rows)[0]
        self.assertEqual((group["sessions"], group["verified"], group["sessions_with_tokens"]), (4, 4, 2))
        self.assertEqual(group["tokens_measured"], 60)                               # the partial aggregate is kept...
        self.assertIsNone(group["measured_tokens_per_verified"])                    # ...but never divided as complete
        self.assertEqual(group["token_coverage"], 0.5)
        self.assertEqual(group["token_quality"]["unknown"], 2)

    def test_partial_or_total_only_sessions_are_not_summed_as_measured_tokens(self):
        partial = session("done", usage={"source": "claude-stream-json-partial", "quality": "partial",
                                         "input_tokens": 5, "output_tokens": 5, "cache_read_tokens": 0,
                                         "cache_write_tokens": 0, "total_tokens": 10}, event_id="p")
        group = bt_efficiency.summarize([partial])[0]
        self.assertEqual((group["tokens_measured"], group["sessions_partial_tokens"]), (0, 1))

    def test_shared_sessions_are_not_attributed_to_each_task(self):
        group = bt_efficiency.summarize([session("done", ["T1", "T2"], {"T1": "done", "T2": "done"})])[0]
        self.assertEqual((group["sessions"], group["attempts"], group["shared_sessions"]), (1, 2, 1))
        self.assertEqual(group["seconds"], 100)                                      # not 200


class EffortSeparation(LearningRouter):
    def setUp(self):
        super().setUp()
        self.attempts("codex-named", "codex", "gpt-6.1-sol", 5, 15, effort="medium")   # fixture of the brief
        self.attempts("codex-named", "codex", "gpt-6.1-sol", 18, 2, effort="high")

    def routes(self, **kw):
        with patch("bt_subscriptions.load", return_value={}):
            routes, _ = bt_agents.candidates("personal-project", ["codex-named"], 1, "implement", **kw)
        return routes

    def test_each_effort_is_its_own_measured_configuration(self):
        with patch.object(bt_events, "read_all", return_value=self.rows):
            rates, _ = bt_agents._stats()
        medium, high = ("codex", "gpt-6.1-sol", "medium", "implement"), ("codex", "gpt-6.1-sol", "high", "implement")
        self.assertEqual((rates[medium], rates[high]), (0.25, 0.9))
        self.assertEqual((rates.samples[medium], rates.samples[high]), (20, 20))   # High's successes never reach Medium
        self.assertNotEqual(rates.lower[medium], rates.lower[high])

    def test_the_route_reports_the_evidence_of_the_effort_that_will_run(self):
        medium = self.routes()[0]
        high = self.routes(effort="high")[0]
        self.assertEqual((medium["effort"], medium["evidence"]["kind"], medium["evidence"]["rate"]), ("medium", "direct", 0.25))
        self.assertEqual((high["effort"], high["evidence"]["kind"], high["evidence"]["rate"]), ("high", "direct", 0.9))
        self.assertEqual(medium["tier"], high["tier"])                              # the tier floor is untouched
        self.assertIn("direct verified task success 25%", medium["why"])

    def test_an_unmeasured_effort_gets_labelled_indirect_evidence_never_a_measured_rate(self):
        xhigh = self.routes(effort="xhigh")[0]
        evidence = xhigh["evidence"]
        self.assertEqual((evidence["kind"], evidence["rate"], evidence["samples"]), ("aggregate", None, 40))
        self.assertEqual(evidence["from_efforts"], ["high", "medium"])
        self.assertAlmostEqual(evidence["aggregate_rate"], 23 / 40)
        self.assertIn("INDIRECT evidence only", xhigh["why"])
        self.assertLess(evidence["lower"], policy.wilson_lower(23, 40))             # ranked below what it would be if direct

    def test_without_any_history_the_router_still_answers(self):
        self.rows.clear()
        route = self.routes(effort="high")[0]
        self.assertEqual((route["evidence"]["kind"], route["effort"]), ("none", "high"))

    def test_the_executed_explicit_effort_is_chosen_before_comparing_and_recorded_once(self):
        import bt_runsession
        unit = [{"id": "T1", "effort": "high"}, {"id": "T2"}]
        self.assertEqual(bt_runsession._asked_effort(unit), "high")
        with patch("bt_subscriptions.load", return_value={}):
            chosen = bt_agents.route("personal-project", {"pool": ["codex-named"], "req": "R"}, 1, effort="high")
        self.assertEqual((chosen["effort"], chosen["decision"]["evidence"]["kind"]), ("high", "direct"))
        self.assertIs(bt_runsession._explicit_effort(chosen, unit), chosen)         # nothing left to apply twice
        self.assertEqual(bt_agents.apply_explicit_effort("codex", "gpt-6.1-sol", "high", "medium"), "high")  # never lowers
        self.assertEqual(bt_agents.apply_explicit_effort("claude", "haiku", None, "high"), None)

    def test_the_decision_engine_history_keeps_efforts_apart(self):
        history = adapter._history_snapshot(self.rows_with_profile())
        medium = history[("codex", "gpt-6.1-sol", "codex-named", "medium", "implement")]
        high = history[("codex", "gpt-6.1-sol", "codex-named", "high", "implement")]
        self.assertEqual((medium.verified_successes, medium.verified_failures), (5, 15))
        self.assertEqual((high.verified_successes, high.verified_failures), (18, 2))

    def rows_with_profile(self):
        return [{**r, "origin": "real"} for r in self.rows]


class RunIdentity(AgentTests):
    def test_event_ids_of_a_new_run_never_collide_and_legacy_ids_are_unchanged(self):
        import hashlib
        self.assertEqual(bt_events.event_id_for("p", "REQ-1", 3), hashlib.sha1(b"p|REQ-1|3").hexdigest()[:16])
        self.assertNotEqual(bt_events.event_id_for("p", "REQ-1", 3, "run-a"), bt_events.event_id_for("p", "REQ-1", 3, "run-b"))

    def test_a_second_run_of_the_same_req_is_recorded_and_a_replay_of_one_run_is_not(self):
        info = {"agent": "claude", "model": "sonnet"}
        with patch.object(bt_events, "extract_usage", return_value={}):
            first = bt_events.record_attempt("p", {"req": "REQ-1", "context_run_id": "run-a"}, "T1", 1, info, "done")
            replay = bt_events.record_attempt("p", {"req": "REQ-1", "context_run_id": "run-a"}, "T1", 1, info, "done")
            second = bt_events.record_attempt("p", {"req": "REQ-1", "context_run_id": "run-b"}, "T1", 1, info, "done")
        self.assertIsNotNone(first)
        self.assertIsNone(replay)                                                   # same run, same session: idempotent
        self.assertIsNotNone(second)                                                # new run: its session 1 is not dropped
        rows = bt_events.read_all()
        self.assertEqual({r["run_id"] for r in rows}, {"run-a", "run-b"})

    def test_outcomes_of_two_runs_of_one_req_do_not_collide(self):
        run_a = session("done", ["T1"], {"T1": "done"}, event_id="a", attempt=1, run_id="run-a")
        run_b = session("failed", ["T1"], {"T1": "failed"}, event_id="b", attempt=1, run_id="run-b")
        run_b2 = session("done", ["T1"], {"T1": "done"}, event_id="c", attempt=2, run_id="run-b")
        counts = bt_outcomes.counts([run_a, run_b, run_b2])[("claude", "sonnet", "medium", "implement")]
        self.assertEqual((counts["verified"], counts["failed"]), (2, 1))

    def test_a_replay_inside_one_run_and_a_second_verification_count_once(self):
        a = session("done", ["T1"], {"T1": "done"}, event_id="a", attempt=1, run_id="run-a")
        replay = {**a, "event_id": "r", "recovered": True}
        again = {**a, "event_id": "s", "model": "opus", "attempt": 2}
        self.assertEqual(len(bt_outcomes.outcomes([a, replay, again])), 1)

    def test_retry_blocked_restarts_attempt_numbers_without_overwriting_history(self):
        before = session("failed", ["T1"], {"T1": "failed"}, event_id="a", attempt=1, run_id="run-a", attempt_epoch=None)
        after = session("done", ["T1"], {"T1": "done"}, event_id="b", attempt=1, run_id="run-a", attempt_epoch=1)
        counts = bt_outcomes.counts([before, after])[("claude", "sonnet", "medium", "implement")]
        self.assertEqual((counts["verified"], counts["failed"]), (1, 1))

    def test_legacy_rows_without_a_run_id_are_never_merged(self):
        legacy = [session("done", ["T1"], {"T1": "done"}, event_id=e, attempt=1, run_id=None) for e in ("x", "y")]
        self.assertEqual(len(bt_outcomes.outcomes(legacy)), 2)

    def test_run_state_keeps_its_run_id_across_reads_and_a_new_run_gets_another(self):
        import bt_runstate as rs
        first = rs.init_state("p", self.base / "r1", "claude", "haiku", True, dict(rs.DEFAULT_LIMITS), None, False)
        second = rs.init_state("p", self.base / "r1", "claude", "haiku", True, dict(rs.DEFAULT_LIMITS), None, False)
        self.assertNotEqual(first["context_run_id"], second["context_run_id"])
        self.assertEqual(first["context_run_id"], {**first}["context_run_id"])

    def test_rework_never_crosses_runs(self):
        import bt_quality
        old_run = session("failed", ["T1"], {"T1": "failed"}, event_id="a", run_id="run-a", session=1)
        new_run = session("done", ["T1"], {"T1": "done"}, event_id="b", run_id="run-b", session=2)
        self.assertEqual(bt_quality.rework_events([old_run, new_run]), [])
        same_run = {**new_run, "run_id": "run-a"}
        self.assertEqual([e for e, _ in bt_quality.rework_events([old_run, same_run])], ["a"])


WORKER = """
import os, sys, time
sys.path.insert(0, sys.argv[1])
import bt_explore
go = sys.argv[2]
while not os.path.exists(go):
    time.sleep(0.002)
record = bt_explore.reserve({"agent": "codex", "model": "gpt-6.1-sol", "kind": "implement", "tier": 1}, "p", "R", "t",
                            5, None)
print("1" if record else "0")
"""


class ExploreProcesses(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.TemporaryDirectory(prefix="explore-proc-")
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.bitacora = base / "bitacora"                       # the children's BITACORA_ROOT
        self.root = self.bitacora / ".state"                    # == bt_core.STATE in the children
        self.root.mkdir(parents=True)
        self.scripts = str(Path(__file__).resolve().parent.parent)
        patcher = patch.object(bt_explore, "STATE", self.root)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.ledger = self.root / "explore.jsonl"

    def spawn(self, code: str, *args):
        import os
        import subprocess
        env = {**os.environ, "BITACORA_ROOT": str(self.bitacora)}
        return subprocess.Popen([sys.executable, "-I", "-c", code, self.scripts, *args], env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def run_workers(self, count=8):
        go = self.root / "go"
        procs = [self.spawn(WORKER, str(go)) for _ in range(count)]
        go.write_text("go")  # every process spins on this file: they reserve at the same moment
        outputs = [p.communicate(timeout=60)[0].strip() for p in procs]
        self.assertTrue(all(p.returncode == 0 for p in procs))
        return outputs

    def test_eight_processes_against_a_budget_of_five_admit_exactly_five(self):  # 1, 2
        outputs = self.run_workers(8)
        self.assertEqual(outputs.count("1"), 5)
        rows = [json.loads(line) for line in self.ledger.read_text().splitlines()]
        self.assertEqual(len([r for r in rows if r["type"] == "reserve"]), 5)
        self.assertEqual(len({r["decision_id"] for r in rows}), 5)                   # no duplicated reservation
        # restart (3): a fresh process still sees five and admits nothing more
        self.assertEqual(self.run_workers(2).count("1"), 0)
        self.assertEqual(bt_explore.used()[1], 5)

    def test_a_process_killed_after_reserving_keeps_its_reservation_and_is_reported_as_orphan(self):  # 4
        code = ("import sys, os; sys.path.insert(0, sys.argv[1]); import bt_explore;"
                "bt_explore.reserve({'agent':'codex','model':'gpt-6.1-sol','kind':'implement','tier':1},'p','R','t',5,None);"
                "os._exit(137)")
        proc = self.spawn(code)
        proc.communicate(timeout=60)
        self.assertEqual(bt_explore.used()[1], 1)
        later = __import__("time").time() + bt_explore.ORPHAN_AFTER_SEC + 60
        self.assertEqual(len(bt_explore.status(later)["orphans"]), 1)
        self.assertEqual(bt_explore.used(later)[1], 1)                               # still spent: the cap never reopens early

    def test_a_lock_holder_that_dies_does_not_deadlock_the_next_reservation(self):
        code = ("import sys, os; sys.path.insert(0, sys.argv[1]); import bt_explore;"
                "cm = bt_explore._exclusive(); cm.__enter__(); os._exit(1)")
        self.spawn(code).communicate(timeout=60)
        start = __import__("time").time()
        record = bt_explore.reserve({"agent": "codex", "model": "m", "tier": 1}, "p", "R", "t", 5, None)
        self.assertIsNotNone(record)
        self.assertLess(__import__("time").time() - start, 5)

    def test_a_busy_lock_fails_closed_without_hanging(self):  # 8
        code = ("import sys, time; sys.path.insert(0, sys.argv[1]); import bt_explore;"
                "cm = bt_explore._exclusive(); cm.__enter__(); print('held', flush=True); time.sleep(3)")
        holder = self.spawn(code)
        self.assertEqual(holder.stdout.readline().strip(), "held")
        with patch.object(bt_explore, "LOCK_WAIT_SEC", 0.3):
            self.assertIsNone(bt_explore.reserve({"agent": "codex", "model": "m", "tier": 1}, "p", "R", "t", 5, None))
        holder.communicate(timeout=60)
        self.assertEqual(bt_explore.used()[1], 0)                                    # nothing admitted while blocked

    def test_a_write_failure_refuses_the_reservation_and_ordinary_routing_continues(self):  # 8
        with patch.object(bt_explore, "_path", return_value=self.root / "missing-dir" / "x" / "explore.jsonl"), \
                patch("pathlib.Path.mkdir", side_effect=OSError("read-only")):
            self.assertIsNone(bt_explore.reserve({"agent": "codex", "model": "m", "tier": 1}, "p", "R", "t", 5, None))

    def test_a_torn_ledger_line_is_quarantined_counted_and_never_glued_to_the_next_write(self):  # 5
        good = {"type": "reserve", "decision_id": "g1", "at": __import__("time").time(), "agent": "codex", "model": "m"}
        self.ledger.write_text(json.dumps(good) + '\n{"type": "reserve", "decision_id": "x", "ag')
        self.assertEqual(bt_explore.used()[1], 2)                                    # a read never understates the spend
        self.assertIsNone(bt_explore.reserve({"agent": "codex", "model": "m", "tier": 1}, "p", "R", "t", -1, 2))
        self.assertTrue((self.root / "explore.corrupt.jsonl").exists())              # quarantined, not discarded
        rows = [json.loads(line) for line in self.ledger.read_text().splitlines()]    # every line parses now
        self.assertEqual([r.get("orphan") for r in rows], [None, "corrupt_line"])
        self.assertIsNotNone(bt_explore.reserve({"agent": "codex", "model": "m", "tier": 1}, "p", "R", "t", -1, None))
        self.assertEqual(bt_explore.used()[1], 3)

    def test_settling_twice_is_safe_and_the_window_expires(self):  # 6, 7
        t0 = 1_800_000_000.0
        record = bt_explore.reserve({"agent": "codex", "model": "m", "tier": 1}, "p", "R", "t", 1, None, t0)
        self.assertIsNone(bt_explore.reserve({"agent": "codex", "model": "m", "tier": 1}, "p", "R", "t", 1, None, t0 + 60))
        bt_explore.settle(record["decision_id"], "done", True)
        bt_explore.settle(record["decision_id"], "failed", False)
        settles = [json.loads(line) for line in self.ledger.read_text().splitlines() if '"settle"' in line]
        self.assertEqual([(s["result"], s["verified"]) for s in settles], [("done", True)])
        self.assertEqual(bt_explore.used(t0 + 8 * 86400)[1], 0)                      # seven-day window
        self.assertIsNotNone(bt_explore.reserve({"agent": "codex", "model": "m", "tier": 1}, "p", "R", "t", 1, None,
                                                t0 + 8 * 86400))

    def test_a_reserve_key_makes_a_restart_reuse_its_reservation(self):
        route = {"agent": "codex", "model": "m", "tier": 1}
        first = bt_explore.reserve(route, "p", "R", "t", 5, None, key="run|4|T1")
        again = bt_explore.reserve(route, "p", "R", "t", 5, None, key="run|4|T1")
        other = bt_explore.reserve(route, "p", "R", "t", 5, None, key="run|5|T2")
        self.assertEqual(first["decision_id"], again["decision_id"])
        self.assertNotEqual(first["decision_id"], other["decision_id"])
        self.assertEqual(bt_explore.used()[1], 2)

    def test_ordinary_runs_and_fallbacks_never_touch_the_ledger(self):
        self.assertEqual(bt_explore.used(), ({}, 0))
        self.assertFalse(self.ledger.exists())


class ReviewFindingsV3(ExploreProcesses):
    def test_invalid_utf8_in_the_ledger_is_quarantined_not_fatal(self):
        self.ledger.write_bytes(b'{"type": "reserve", "decision_id": "x", "agent": "codex", "model": "caf\xc3')
        self.assertEqual(bt_explore.used()[1], 1)                                   # reading never raises
        self.assertIsNotNone(bt_explore.reserve({"agent": "codex", "model": "m", "tier": 1}, "p", "R", "t", 5, None))
        self.assertEqual(bt_explore.used()[1], 2)                                   # the torn line stays counted
        self.assertTrue((self.root / "explore.corrupt.jsonl").exists())

    def test_a_reserve_key_is_reused_only_for_the_same_route(self):
        first = bt_explore.reserve({"agent": "codex", "model": "m1", "tier": 1}, "p", "R", "t", 5, None, key="k")
        other = bt_explore.reserve({"agent": "claude", "model": "m2", "tier": 1}, "p", "R", "t", 5, None, key="k")
        self.assertNotEqual(first["decision_id"], other["decision_id"])
        self.assertEqual(bt_explore.used()[1], 2)

    def test_a_torn_reserve_still_counts_against_the_route_it_names(self):
        self.ledger.write_text('{"type": "reserve", "decision_id": "x", "at": %s, "agent": "codex", "model": "m", "ta'
                               % __import__("time").time())
        self.assertIsNone(bt_explore.reserve({"agent": "codex", "model": "m", "tier": 1}, "p", "R", "t", 1, None))
        self.assertEqual(bt_explore.used()[0].get(("codex", "m")), 1)


class ReviewFindingsV3Router(RouterBase):
    def test_delegations_choose_the_route_with_the_evidence_of_the_effort_they_ask_for(self):
        import bt_delegate
        seen = {}

        def fake(project, state, tier, kind, avoid=None, **kw):
            seen.update(kw)
            return {"profile": "p", "agent": "codex", "model": "gpt-6.1-sol", "effort": "high"}
        with patch.object(bt_agents, "route", side_effect=fake), patch.object(bt_agents, "pool_for", return_value=["p"]):
            bt_delegate.auto_route("proj", "implement", 1, None, "high")
        self.assertEqual((seen["effort"], seen["allow_explore"]), ("high", False))

    def test_the_task_success_rate_keeps_its_published_meaning(self):
        rows = [session("partial", ["T1", "T2", "T3", "T4"],
                        {"T1": "done", "T2": "done", "T3": "verify_failed", "T4": "claimed"})]
        group = bt_events.summary(rows, by=("agent",))[0]
        self.assertEqual((group["task_success_rate"], group["verified_task_success_rate"]), (0.67, 0.67))
        self.assertEqual(group["task_success_rate_incl_unjudged"], 0.5)

    def test_attribution_adopts_builder_rows_written_before_run_id_existed(self):
        import bt_quality
        legacy_builder = session("done", ["T1"], {"T1": "done"}, event_id="b1", run_id=None, session=1, kind="implement")
        tasks = [{"id": "T1", "status": "done", "kind": "implement"}]
        builders, _ = bt_quality.attribution([legacy_builder], "pr", "REQ-1", tasks, "run-new")
        self.assertEqual(builders, ["b1"])

    def test_a_few_direct_failures_are_not_hidden_by_a_strong_neighbour_effort(self):
        self.attempts("codex-named", "codex", "gpt-6.1-sol", 20, 0, effort="medium")
        self.attempts("codex-named", "codex", "gpt-6.1-sol", 0, 4, effort="high")   # below min_samples: not direct
        with patch.object(bt_events, "read_all", return_value=self.rows):
            rates, _ = bt_agents._stats()
        evidence, rate, _ = bt_agents.evidence_for(rates, "codex", "gpt-6.1-sol", "high", "implement")
        self.assertEqual((evidence["kind"], rate, evidence["poor"], evidence["samples"]), ("aggregate", None, True, 24))


class BenchmarkReplay(unittest.TestCase):
    @staticmethod
    def run_replay() -> dict:
        import importlib.util
        import io
        from contextlib import redirect_stdout
        path = Path(__file__).resolve().parents[3] / "evals" / "harness_replay.py"
        spec = importlib.util.spec_from_file_location("harness_replay_under_test", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        out = io.StringIO()
        with redirect_stdout(out):
            module.main()
        return json.loads(out.getvalue())

    def test_replay_is_deterministic_homogeneous_and_never_claims_a_real_saving(self):  # AC-20
        first, second = self.run_replay(), self.run_replay()
        self.assertEqual(first, second)
        self.assertEqual(first["kind"], "simulation")
        self.assertIsNone(first["measured"])
        self.assertTrue(first["same_verified_work"])
        self.assertTrue(first["quality_guard"]["after_not_worse"])
        for side in ("before", "after"):
            self.assertIn("relative_cost_units", first[side])
            self.assertNotIn("relative_cost_estimate", first[side])                  # no legacy weights mixed in
            self.assertGreater(first[side]["failed_attempts"], 0)                    # failures and retries are in
        self.assertFalse(any("saving" in key or "percent" in key for key in first))


if __name__ == "__main__":
    unittest.main()
