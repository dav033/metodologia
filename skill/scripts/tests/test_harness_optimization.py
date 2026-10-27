"""Harness quota optimisation: ladder, start tiers, cold start, quota balance, fallback, grouping, review policy,
timeouts, stagnation and verified-efficiency metrics (one test per rule; deterministic, no provider calls)."""
from __future__ import annotations

import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from test_agents import AgentTests  # noqa: E402  (configures the disposable root)

import bt_agents  # noqa: E402
import bt_efficiency  # noqa: E402
import bt_events  # noqa: E402
import bt_orchestration_context as context  # noqa: E402
import bt_requirements_gate as gate  # noqa: E402
import bt_review_policy  # noqa: E402
import bt_routing_policy as policy  # noqa: E402
import bt_runprompt  # noqa: E402
import bt_runsession  # noqa: E402
import bt_runsettle  # noqa: E402
import bt_runstate as rs  # noqa: E402
import bt_runtier  # noqa: E402

NOW = 1_800_000_000.0


def task(tid, tier=0, kind="implement", after=(), risk=None, status="todo", milestone="M1", **extra):
    return {"id": tid, "title": tid, "repo": "r", "after": list(after), "verify": "true", "kind": kind, "tier": tier,
            "risk": risk, "status": status, "milestone": milestone, "attempts": 0, "error_hashes": [], **extra}


def run_state(*tasks, limits=None):
    return {"tasks": list(tasks), "limits": limits if limits is not None else dict(rs.DEFAULT_LIMITS)}


class LadderAndStartTier(unittest.TestCase):
    def test_no_rung_reaches_xhigh_and_effort_climbs_with_the_tier(self):  # 1
        for ladder in (bt_agents.LADDER, bt_agents.AUDIT_LADDER):
            self.assertNotIn("xhigh", [e for rungs in ladder.values() for _, e in rungs])
        self.assertEqual([bt_agents.model_for("claude", t) for t in (0, 1, 2)],
                         [("haiku", None), ("sonnet", "medium"), ("opus", "high")])
        self.assertEqual([bt_agents.model_for("codex", t) for t in (0, 1, 2)],
                         [("gpt-6-luna", "medium"), ("gpt-6.1-sol", "medium"), ("gpt-6.1-sol", "high")])

    def test_simple_tasks_start_light_and_kind_ceilings_bound_complex_ones(self):
        for kind in ("docs", "test", "research", "implement"):
            self.assertEqual(policy.start_tier(None, kind, "S", "low")[0], 0, kind)
        self.assertEqual(policy.start_tier("architecture", "docs")[0], 0)
        self.assertEqual(policy.start_tier(None, "research", "L")[0], 1)
        self.assertEqual(policy.start_tier(None, "test", None, "high")[0], 1)
        tier, reason = policy.start_tier(None, "implement", "L", "high")
        self.assertEqual(tier, 2)
        self.assertIn("complexity L", reason)                                    # the reason is recorded with it
        self.assertEqual(policy.start_tier(None, "audit")[0], 1)

    def test_explicit_effort_is_the_only_way_to_xhigh_and_is_recorded(self):
        chosen = {"agent": "claude", "model": "opus", "effort": "high", "why": "x"}
        raised = bt_runsession._explicit_effort(chosen, [task("T1", effort="xhigh")])
        self.assertEqual(raised["effort"], "xhigh")
        self.assertIn("explicit task effort xhigh", raised["why"])
        self.assertEqual(bt_runsession._explicit_effort(chosen, [task("T1", effort="low")]), chosen)  # never lowers
        agy = {"agent": "antigravity", "model": "gemini-3.8-flash-low", "effort": None}
        self.assertEqual(bt_runsession._explicit_effort(agy, [task("T1", effort="xhigh")]), agy)

    def test_fixed_mode_uses_role_defaults_without_failure_tier_escalation(self):  # 3
        state = {"agent": "claude"}
        self.assertEqual(bt_agents.legacy_model_for(state, 1), ("sonnet", "medium"))
        self.assertEqual(bt_agents.route("p", {"agent": "codex"}, 1)["effort"], "high")
        self.assertEqual(bt_agents.route("p", {"agent": "codex"}, 2)["effort"], "high")


class RouterTests(AgentTests):
    def setUp(self):
        super().setUp()
        self.rows = []
        for patcher in (patch.object(bt_agents.time, "time", return_value=NOW),
                        patch.object(bt_events, "read_all", side_effect=lambda: self.rows),
                        patch.object(bt_agents.shutil, "which", return_value="/bin/fake-cli")):
            patcher.start()
            self.addCleanup(patcher.stop)

    def attempts(self, profile, agent, model, done, failed, kind="implement", effort=None):
        import datetime as dt
        stamp = dt.datetime.fromtimestamp(NOW - 60, tz=dt.timezone.utc).isoformat()
        for i in range(done + failed):
            self.rows.append({"profile": profile, "agent": agent, "model": model, "kind": kind, "effort": effort,
                              "result": "done" if i < done else "failed", "seconds": 10, "ts": stamp})

    def usage(self, profile, five, seven, observed=NOW - 60, seven_reset=NOW + 3 * 86400):
        return {bt_agents.account_key(profile, "claude" if profile == "claude" else "codex"): {
            "status": "ok", "observed_at": observed, "profile": profile,
            "provider": "claude" if profile == "claude" else "codex",
            "windows": {"five_hour": {"used_percent": five, "resets_at": NOW + 3600, "window_minutes": 300},
                        "seven_day": {"used_percent": seven, "resets_at": seven_reset, "window_minutes": 10080}}}}

    def order(self, usage, kind="implement", tier=0, **kw):
        with patch("bt_subscriptions.load", return_value=usage):
            routes, _ = bt_agents.candidates("personal-project", ["claude", "codex-named"], tier, kind, **kw)
        return [r["agent"] for r in routes]

    def test_pool_mode_prefers_the_account_with_more_headroom(self):  # 4
        usage = {**self.usage("claude", 10, 90), **self.usage("codex-named", 10, 20)}
        self.assertEqual(self.order(usage)[0], "codex")
        usage = {**self.usage("claude", 10, 20), **self.usage("codex-named", 10, 90)}
        self.assertEqual(self.order(usage)[0], "claude")

    def test_small_differences_do_not_concentrate_work_on_one_account(self):
        usage = {**self.usage("claude", 41, 41), **self.usage("codex-named", 48, 48)}   # same 10-point bucket
        self.attempts("claude", "claude", "haiku", 20, 0)                               # claude is the proven route
        self.attempts("codex-named", "codex", "gpt-6-luna", 5, 0)                       # 5/5: judged, not yet proven
        self.assertEqual(self.order(usage)[0], "claude")                                # quality decides inside a bucket

    def test_stale_telemetry_is_neither_empty_nor_full(self):  # 5
        stale = self.usage("codex-named", 0, 0, observed=NOW - 4 * 3600)               # 0 % used but 4 h old
        known_low = self.usage("claude", 20, 20)
        self.assertEqual(self.order({**known_low, **stale})[0], "claude")               # known 20 % beats unknown
        known_high = self.usage("claude", 90, 90)
        self.assertEqual(self.order({**known_high, **stale})[0], "codex")               # unknown beats known 90 %

    def test_weekly_pace_deprioritises_an_account_burning_its_week_too_fast(self):
        usage = {**self.usage("claude", 5, 60, seven_reset=NOW + 6 * 86400),            # 60 % used, 1/7 of week gone
                 **self.usage("codex-named", 5, 50, seven_reset=NOW + 2 * 86400)}      # 50 % used, 5/7 gone
        self.assertEqual(self.order(usage)[0], "codex")
        self.assertIsNone(policy.weekly_pace_surplus({"status": "ok", "windows": {}}, NOW))

    def test_auth_blocked_account_cannot_beat_healthy_weekly_pace_penalty(self):
        for status in ("invalid_credentials", "auth_unavailable", "manual_challenge", "http_401", "http_403"):
            with self.subTest(status=status):
                usage = {**self.usage("claude", 5, 40, seven_reset=NOW + 6 * 86400),
                         **self.usage("codex-named", 0, 0)}
                usage[bt_agents.account_key("codex-named", "codex")]["status"] = status
                self.assertEqual(self.order(usage)[0], "claude")

    def test_cold_start_explores_cheap_routes_but_never_high_risk_or_audit_work(self):  # 6
        self.attempts("claude", "claude", "haiku", 5, 0)
        self.assertEqual(self.order({})[0], "codex")                                   # unseen cheap route explores
        self.assertEqual(self.order({}, risk="high")[0], "claude")                     # not on high-risk work
        self.assertEqual(self.order({}, "audit", 1)[0], "claude")                      # audit order is untouched

    def test_expensive_cold_start_needs_budget_and_five_attempts_are_not_proof(self):
        self.assertTrue(policy.may_explore(8, "implement", None, 0, 4))
        self.assertFalse(policy.may_explore(8, "implement", None, 0, 5))               # weekly budget (5) used up
        self.assertFalse(policy.may_explore(8, "implement", "high", 0, 0))
        self.assertFalse(policy.may_explore(1, "audit", None, 0, 0))
        with patch.object(policy, "config", side_effect=lambda k, d: 9 if k.endswith("budget_week") else d):
            self.assertTrue(policy.may_explore(8, "implement", None, 0, 8))            # the owner may raise it
        self.assertLess(policy.wilson_lower(5, 5), 0.8)                                # 5/5 is not a proven route
        self.assertGreater(policy.wilson_lower(50, 50), 0.95)

    def test_unproven_route_never_beats_a_proven_one_without_exploration(self):
        self.attempts("claude", "claude", "haiku", 4, 1)                                # 4/5: lower bound ~0.51
        self.assertEqual(self.order({}, risk="high")[0], "claude")
        self.assertEqual(self.order({}, "audit", 1, ) [0], "claude")

    def test_tier_two_is_never_served_by_a_lighter_model(self):  # 2
        routes, _ = bt_agents.candidates("personal-project", ["claude", "codex-named"], 2, "implement")
        self.assertEqual({(r["model"], r["effort"]) for r in routes}, {("opus", "high"), ("gpt-6.1-sol", "high")})

    def test_cooldown_excludes_the_failed_combination_until_its_reset(self):  # 15
        bt_agents.quota_mark("claude", "claude", NOW + 900)
        self.assertEqual(self.order({}, tier=1), ["codex"])
        routes, soonest = bt_agents.candidates("personal-project", ["claude"], 1, "implement")
        self.assertEqual((routes, soonest), ([], NOW + 900))

    def test_batch_workers_do_not_share_one_account(self):  # 17
        first = bt_agents.route("personal-project", {"pool": ["claude", "codex-named"]}, 0)
        busy = {bt_agents.account_key(first["profile"], first["agent"])}
        second = bt_agents.route("personal-project", {"pool": ["claude", "codex-named"]}, 0, "implement", None, busy)
        self.assertNotEqual(first["agent"], second["agent"])

    def test_effort_weight_is_configurable_and_marked_as_an_estimate(self):
        self.assertGreater(policy.effort_weight("high"), policy.effort_weight("medium"))
        with patch.object(policy, "config", return_value={"high": 4.0}):
            self.assertEqual(policy.effort_weight("high"), 4.0)
            self.assertEqual(policy.effort_weight("low"), 1.0)
        self.attempts("claude", "claude", "sonnet", 1, 0, effort="high")
        _, load = bt_agents._stats()
        self.assertEqual(load[bt_agents.account_key("claude", "claude")], 10 * 3 * 1.5)


class GroupingTests(unittest.TestCase):
    def test_a_hard_task_does_not_lift_its_light_neighbours(self):  # 7, 8
        state = run_state(task("T1", tier=2), task("T2"), task("T3"))
        light = rs.unit_of(state, state["tasks"][1])
        self.assertEqual([t["id"] for t in light], ["T2", "T3"])
        self.assertEqual(rs.unit_tier(light), 0)
        self.assertEqual([t["id"] for t in rs.unit_of(state, state["tasks"][0])], ["T1"])

    def test_default_group_sizes_per_tier(self):
        light = run_state(*[task(f"T{i}") for i in range(1, 6)])
        self.assertEqual(len(rs.unit_of(light, light["tasks"][0])), 3)
        for tier in (1, 2):
            heavy = run_state(*[task(f"T{i}", tier=tier) for i in range(1, 4)])
            self.assertEqual(len(rs.unit_of(heavy, heavy["tasks"][0])), 1, tier)

    def test_group_sizes_are_configurable(self):
        state = run_state(*[task(f"T{i}") for i in range(1, 6)], limits={"group_max": {"0": 2}})
        self.assertEqual(len(rs.unit_of(state, state["tasks"][0])), 2)
        self.assertEqual(bt_runtier.group_max({"group_max": {"1": 4}}, 1), 1)

    def test_dependencies_are_respected_inside_and_across_groups(self):  # 9
        chain = run_state(task("T1"), task("T2", after=["T1"]), task("T3", after=["T2"]), task("T4", after=["T3"]))
        self.assertEqual([t["id"] for t in rs.unit_of(chain, chain["tasks"][0])], ["T1", "T2", "T3"])  # cap 3, in order
        blocked = run_state(task("T1", tier=2), task("T2", after=["T1"]), task("T3"))
        self.assertEqual([t["id"] for t in rs.unit_of(blocked, blocked["tasks"][2])], ["T3"])          # T2 waits for T1

    def test_kinds_and_risk_classes_do_not_mix_and_audits_run_alone(self):
        state = run_state(task("T1"), task("T2", kind="docs"), task("T3", risk="high"), task("T4"))
        self.assertEqual([t["id"] for t in rs.unit_of(state, state["tasks"][0])], ["T1", "T4"])
        audit = task("M1-audit", tier=1, kind="audit", synthetic=True)
        self.assertEqual(rs.unit_of(run_state(audit, task("T1")), audit), [audit])


class TimeoutAndStagnation(unittest.TestCase):
    def test_tier_timeouts_and_explicit_overrides(self):  # 13
        limits = dict(rs.DEFAULT_LIMITS)
        self.assertEqual([bt_runtier.session_timeout_min(limits, t) for t in (0, 1, 2)], [25, 25, 25])
        self.assertEqual(bt_runtier.session_timeout_min({"session_timeout_min": 90}, 0), 90)       # stored explicit value
        self.assertEqual(bt_runtier.session_timeout_min({**limits, "session_timeout_min": 30,
                                                         "session_timeout_by_tier": None}, 2), 30)
        self.assertEqual(bt_runtier.session_timeout_min({**limits, "session_timeout_min": 30}, 2), 25)

    def test_headless_claude_has_a_strict_turn_limit(self):
        argv, _ = bt_runprompt.agent_argv({"agent": "claude"}, Path("."), "P", "haiku", None)
        self.assertEqual(argv[argv.index("--max-turns") + 1], "45")

    def test_consecutive_attempts_that_change_nothing_block_the_task(self):
        t = task("T1", attempts=0)
        same = {"tree_sig": "abc"}
        self.assertIsNone(bt_runsettle._fail_attempt(t, "alpha broke", 4, same))
        self.assertIsNone(bt_runsettle._fail_attempt(t, "beta crashed", 4, same))  # first idle repeat: escalate, go on
        reason = bt_runsettle._fail_attempt(t, "gamma exploded", 4, same)
        self.assertIn("no progress", reason)
        self.assertEqual(t["idle_attempts"], 2)

    def test_progress_resets_the_idle_counter(self):
        t = task("T1")
        for sig, err in (("a", "one"), ("a", "two"), ("b", "three"), ("b", "four")):
            self.assertIsNone(bt_runsettle._fail_attempt(t, f"{err} failure", 9, {"tree_sig": sig}))
        self.assertEqual(t["idle_attempts"], 1)

    def test_attempts_without_a_signature_never_count_as_idle(self):
        t = task("T1")
        for err in ("one", "two", "three"):
            self.assertIsNone(bt_runsettle._fail_attempt(t, f"{err} failure", 9, None))
        self.assertEqual(t.get("idle_attempts", 0), 0)


class ReviewPolicyTests(unittest.TestCase):
    audited = staticmethod(lambda: {"tasks": [task("T1"), task("M1-audit", tier=1, kind="audit", synthetic=True)]})

    def test_with_a_milestone_audit_commits_skip_the_per_commit_antagonist(self):  # 11
        rule = bt_review_policy.commit_review_rule(self.audited(), [task("T1")])
        self.assertIn("Do NOT run the antagonist per commit", rule)
        self.assertIn("verify, tests and linters", rule)                        # mandatory checks stay
        self.assertIn("EVERY commit", bt_review_policy.commit_review_rule({"tasks": [task("T1")]}, [task("T1")]))

    def test_high_risk_work_uses_the_escalated_milestone_audit(self):
        rule = bt_review_policy.commit_review_rule(self.audited(), [task("T1", risk="high")])
        self.assertIn("Do NOT run the antagonist per commit", rule)
        self.assertNotIn("EVERY commit", rule)

    def test_a_high_risk_security_surface_keeps_one_security_pass_under_audit_coverage(self):
        login = task("T1", risk="high", kind="implement", title="Server sessions and the permission guard")
        rule = bt_review_policy.commit_review_rule(self.audited(), [login])
        self.assertIn("SECURITY-SENSITIVE", rule)
        self.assertIn("ONE security-only antagonist pass", rule)
        self.assertIn("Do NOT run the general antagonist per commit", rule)
        self.assertNotIn("EVERY commit", rule)
        for other in (task("T1", risk="medium", kind="implement", title="Server sessions"),        # not high risk
                      task("T1", risk="high", kind="audit", title="Sessions audit"),               # reviews, does not open
                      task("T1", risk="high", kind="implement", title="Plans page")):              # no security surface
            self.assertNotIn("SECURITY-SENSITIVE", bt_review_policy.commit_review_rule(self.audited(), [other]))

    def test_the_security_pass_reads_the_full_task_text_from_the_frozen_plan(self):
        frozen = {"schema_version": "1.3.0", "plan_id": "P", "revision": 1,
                  "tasks": [{"id": "T1", "kind": "implement", "risk": "high", "subplan_id": "SP-1",
                             "title": "Local mode", "objective": "Loopback detection must not trust forwarded headers"},
                            {"id": "A1", "kind": "audit", "subplan_id": "SP-1"}],
                  "subplans": [{"id": "SP-1", "audit_task": "A1"}]}
        state = {"plan_id": "P", "revision": 1, "frozen_plan": frozen, "tasks": [task("A1", kind="audit", status="todo")]}
        self.assertIn("SECURITY-SENSITIVE", bt_review_policy.commit_review_rule(state, [{"id": "T1"}]))
        state["tasks"][0]["status"] = "done"                                                      # no audit left: full gate
        self.assertIn("EVERY commit", bt_review_policy.commit_review_rule(state, [{"id": "T1"}]))

    def test_only_the_units_own_milestone_audit_lifts_the_gate(self):
        state = self.audited()
        self.assertTrue(bt_review_policy.milestone_audit_active(state, [task("T1")]))
        self.assertFalse(bt_review_policy.milestone_audit_active(state, [task("T9", milestone=None)]))  # never audited
        self.assertFalse(bt_review_policy.milestone_audit_active(state, [task("T2", milestone="M2")]))
        state["tasks"][1]["status"] = "blocked"
        self.assertFalse(bt_review_policy.milestone_audit_active(state, [task("T1")]))

    def test_a_finished_audit_no_longer_covers_new_commits(self):
        state = {"tasks": [task("M1-audit", kind="audit", synthetic=True, status="done")]}
        self.assertFalse(bt_review_policy.milestone_audit_active(state))

    def test_only_the_frozen_subplans_own_pending_audit_covers_its_tasks(self):
        plan_tasks = [
            {"id": "T1", "kind": "implement", "subplan_id": "SP-1"},
            {"id": "T2", "kind": "implement", "subplan_id": "SP-2"},
            {"id": "A1", "kind": "audit", "subplan_id": "SP-1"},
            {"id": "A2", "kind": "audit", "subplan_id": "SP-2"},
        ]
        frozen = {"schema_version": "1.3.0", "plan_id": "PLAN-X", "revision": 4,
                  "tasks": plan_tasks,
                  "subplans": [{"id": "SP-1", "audit_task": "A1"}, {"id": "SP-2", "audit_task": "A2"}]}
        state = {"plan_id": "PLAN-X", "revision": 4, "frozen_plan": frozen,
                 "tasks": [task("A1", kind="audit", status="todo"), task("A2", kind="audit", status="todo")]}
        self.assertTrue(bt_review_policy.subplan_audit_active(state, [{"id": "T1"}]))
        self.assertIn("Do NOT run the antagonist per commit",
                      bt_review_policy.commit_review_rule(state, [{"id": "T1"}]))
        state["tasks"][0]["status"] = "blocked"
        self.assertFalse(bt_review_policy.subplan_audit_active(state, [{"id": "T1"}]))
        self.assertIn("EVERY commit", bt_review_policy.commit_review_rule(state, [{"id": "T1"}]))
        self.assertTrue(bt_review_policy.subplan_audit_active(state, [{"id": "T2"}]))
        self.assertIn("Do NOT run the antagonist per commit",
                      bt_review_policy.commit_review_rule(state, [{"id": "T2"}]))

    def test_subplan_audit_requires_a_matching_frozen_plan_identity(self):
        state = {"plan_id": "PLAN-X", "revision": 4,
                 "frozen_plan": {"schema_version": "1.3.0", "plan_id": "PLAN-X", "revision": 3,
                                 "tasks": [{"id": "T1", "subplan_id": "SP-1"},
                                           {"id": "A1", "kind": "audit", "subplan_id": "SP-1"}],
                                 "subplans": [{"id": "SP-1", "audit_task": "A1"}]},
                 "tasks": [task("A1", kind="audit", status="todo")]}
        self.assertFalse(bt_review_policy.subplan_audit_active(state, [{"id": "T1"}]))
        self.assertIn("EVERY commit", bt_review_policy.commit_review_rule(state, [{"id": "T1"}]))

    def test_legacy_prompt_rules_follow_the_policy(self):  # 12
        state, unit = self.audited(), [task("T1")]
        audited = "\n".join(bt_runprompt._rules("p", "REQ-001", "T1", "feat", state=state, unit=unit))
        legacy = "\n".join(bt_runprompt._rules("p", "REQ-001", "T1", "feat"))
        self.assertNotIn("before EVERY commit", audited)
        self.assertIn("Do NOT run the antagonist per commit", audited)
        self.assertIn("before EVERY commit", legacy)

    def test_orchestrator_package_carries_the_same_policy(self):  # 12
        with tempfile.TemporaryDirectory() as temp:
            rdir = Path(temp)
            (rdir / "SPEC.md").write_text("Approved scope\n")
            (rdir / "PLAN.md").write_text("---\nstatus: approved\nexecution_contract: requirements-v1\n---\nPlan\n")
            review = {key: key + " approved" for key in gate.FIELDS}
            review.update(evidence=["SPEC.md", "PLAN.md"], unresolved=[])
            gate.record(rdir, review)
            member = task("T1", status="todo")
            base = {"req": "REQ-001", "project": "t", "context_run_id": "run-1", "log": []}
            plain = json.loads(bt_runprompt.session_prompt("t", rdir, {**base, "tasks": [member]}, member, 1, "f", [member]))
            audited = json.loads(bt_runprompt.session_prompt(
                "t", rdir, {**base, **self.audited()}, member, 1, "f", [member]))
        self.assertIn("EVERY commit", plain["instructions"])
        self.assertIn("Do NOT run the antagonist per commit", audited["instructions"])
        self.assertIn("Preserve concurrent edits", audited["instructions"])         # the rest of the contract intact


class VerifiedEfficiency(unittest.TestCase):
    @staticmethod
    def row(result, model="sonnet", tokens=None, seconds=100, **extra):
        # A Claude result event always carries both cache counters; without them the measurement is partial (bt_usage).
        usage = {"input_tokens": tokens, "output_tokens": 0, "cache_read_tokens": 0, "cache_write_tokens": 0} \
            if tokens is not None else {}
        return {"agent": "claude", "model": model, "effort": "medium", "kind": "implement", "tier": 1,
                "result": result, "seconds": seconds, "usage": usage, "origin": "real", **extra}

    def test_only_supervisor_verified_results_count_as_success(self):  # 18
        rows = [self.row("done"), self.row("verify_failed"), self.row("verify_failed"), self.row("claimed"),
                self.row("done", origin="synthetic")]
        group = bt_efficiency.summarize(rows)[0]
        self.assertEqual((group["verified"], group["unverified_claims"], group["other"]), (1, 2, 1))
        self.assertAlmostEqual(group["verified_success_rate"], 1 / 3)
        self.assertAlmostEqual(group["claim_precision"], 1 / 3)
        self.assertEqual(group["attempts"], 4)                                    # synthetic rows excluded

    def test_measured_and_estimated_consumption_are_never_merged(self):  # 19
        measured = bt_efficiency.summarize([self.row("done", tokens=1000), self.row("done", tokens=3000)])[0]
        self.assertEqual(measured["measured_tokens_per_verified"], 2000)
        self.assertEqual(measured["consumption_provenance"], {"measured_attempts": 2, "estimated_attempts": 2, "of": 2})
        mixed = bt_efficiency.summarize([self.row("done", tokens=1000), self.row("done")])[0]
        self.assertIsNone(mixed["measured_tokens_per_verified"])                  # not every attempt reported tokens
        self.assertEqual(mixed["estimated_units_per_verified"], 100 * 3 * policy.effort_weight("medium"))

    def test_confidence_reflects_the_sample_size(self):
        self.assertEqual(bt_efficiency.confidence(3, 3), "insufficient")
        self.assertEqual(bt_efficiency.confidence(10, 10), "medium")
        self.assertEqual(bt_efficiency.confidence(30, 30), "high")
        self.assertEqual(bt_efficiency.confidence(5, 10), "medium")

    def test_router_rates_ignore_unverified_claims(self):  # 18
        import datetime as dt
        stamp = dt.datetime.now().astimezone().isoformat()
        rows = [{"agent": "codex", "model": "gpt-6-luna", "profile": "p", "kind": "implement", "ts": stamp, "seconds": 1,
                 "result": result} for result in ["done"] * 5 + ["claimed"] * 20]
        with patch.object(bt_events, "read_all", return_value=rows), patch.object(bt_agents, "account_key",
                                                                                  return_value="a"):
            rates, _ = bt_agents._stats()
        self.assertEqual(rates[("codex", "gpt-6-luna", None, "implement")], 1.0)
        self.assertEqual(rates.samples[("codex", "gpt-6-luna", None, "implement")], 5)


if __name__ == "__main__":
    unittest.main()
