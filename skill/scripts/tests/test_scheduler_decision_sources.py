from __future__ import annotations

import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bt_agents
import bt_agy
import bt_events
import bt_plan_adapter as plan_adapter
import bt_profiles
import bt_scheduler_adapter as m1_adapter
import bt_scheduler_core as core
import bt_scheduler_decision_adapter as m2_adapter
import bt_scheduler_plan_routing as plan_routing
import bt_subscription_sources as quota_sources
import bt_subscriptions
from bt_scheduler_decision import rank_candidates
from bt_scheduler_decision.tests.support import (
    PLAN_HASH,
    candidate,
    synthetic_quality_artifacts,
)
from bt_scheduler_decision.tests.support import request as m2_request


class MethodologyDecisionSourceTests(unittest.TestCase):
    def test_route_options_follow_the_supported_provider_ladder_and_task_floor(self):
        self.assertEqual(m2_adapter._route_options("claude", 0, "implement"),
                         (("haiku", None), ("sonnet", "xhigh"), ("opus", "xhigh")))
        self.assertEqual(m2_adapter._route_options("codex", 1, "implement"),
                         (("gpt-6.1-sol", "high"), ("gpt-6.1-sol", "xhigh")))
        self.assertEqual(m2_adapter._route_options("codex", 0, "docs"),
                         (("gpt-6-luna", "low"), ("gpt-6.1-sol", "high"),
                          ("gpt-6.1-sol", "xhigh")))
        self.assertEqual(m2_adapter._route_options("claude", 1, "audit"),
                         (("sonnet", "medium"), ("opus", "high")))
        self.assertEqual(m2_adapter._route_options("antigravity", 0, "implement"),
                         (("gemini-3.8-flash-low", None), ("gemini-3.8-flash-medium", None)))
        self.assertEqual(m2_adapter._route_options("unsupported", 0, "implement"), ())

    def test_tier_floor_uses_task_kind_and_classification_rules_without_medium_risk_promotion(self):
        medium_risk = {"complexity": "low", "scope": "small_change", "coupling": "low",
                       "risk": "medium", "estimated_minutes": 30}
        self.assertEqual(m2_adapter._tier_floor(medium_risk, "implement"), (0, ("kind:implement",)))
        self.assertEqual(m2_adapter._tier_for({**medium_risk, "complexity": "high", "risk": "low"},
                                               "implement"), 1)
        self.assertEqual(m2_adapter._tier_for({**medium_risk, "coupling": "medium", "risk": "low"},
                                               "implement"), 1)
        self.assertEqual(m2_adapter._tier_for({**medium_risk, "scope": "large_change", "risk": "low"},
                                               "implement"), 1)
        self.assertEqual(m2_adapter._tier_for({**medium_risk, "estimated_minutes": 120, "risk": "low"},
                                               "implement"), 1)
        self.assertEqual(m2_adapter._tier_for({**medium_risk, "estimated_minutes": 240, "risk": "low"},
                                               "implement"), 2)
        self.assertEqual(m2_adapter._tier_for({**medium_risk, "risk": "high"}, "implement"), 2)
        self.assertEqual(m2_adapter._tier_for({**medium_risk, "scope": "full_system", "risk": "low"},
                                               "implement"), 2)
        self.assertEqual(m2_adapter._tier_for({**medium_risk, "complexity": "extreme", "risk": "low"},
                                               "implement"), 2)
        self.assertEqual(m2_adapter._tier_for(medium_risk, "audit"), 1)

    def test_tier_floor_explanation_names_classifications_and_rules_that_raise_it(self):
        tier, rules = m2_adapter._tier_floor({"complexity": "high", "scope": "large_change",
                                               "coupling": "high", "risk": "medium",
                                               "estimated_minutes": 120}, "implement")
        self.assertEqual(tier, 1)
        self.assertEqual(rules, ("kind:implement", "complexity:high", "scope:large_change",
                                 "coupling:high", "duration:at_least_120_minutes"))

    def test_candidate_snapshot_uses_real_router_order_and_fails_closed_on_unknown_quota(self):
        now = 100.0
        profiles = {
            "claude-a": {"provider": "claude", "bin": "claude", "env": {}, "work_only": False},
            "claude-b": {"provider": "claude", "bin": "claude", "env": {"CLAUDE_CONFIG_DIR": "/fixture/b"},
                         "work_only": False},
            "codex-a": {"provider": "codex", "bin": "codex", "env": {}, "work_only": False},
            "agy-a": {"provider": "antigravity", "bin": "agy", "env": {}, "work_only": False},
        }
        keys = {profile: f"{profile}:account" for profile in profiles}
        usage = {
            keys["claude-a"]: {"status": "ok", "observed_at": 95.0},
            keys["claude-b"]: {"status": "network_unavailable", "observed_at": 95.0},
            keys["codex-a"]: {"status": "network_unavailable", "observed_at": 95.0},
        }
        telemetry = [
            {"agent": "claude", "model": "haiku", "profile": "claude-a", "effort": "", "kind": "implement",
             "origin": "real", "outcome": "verified", "result": "done", "seconds": 10,
             "usage": {"total_tokens": 100}},
            {"agent": "claude", "model": "haiku", "profile": "claude-a", "effort": "", "kind": "implement",
             "origin": "real", "outcome": "claimed_unverified", "result": "done", "seconds": 20,
             "usage": {"total_tokens": 200}},
            {"agent": "claude", "model": "haiku", "profile": "claude-a", "effort": "", "kind": "implement",
             "origin": "synthetic", "outcome": "verified", "result": "done", "seconds": 1,
             "usage": {"total_tokens": 1}},
        ]

        def quota(row, model, instant):
            if row is usage[keys["claude-b"]]:
                return None, now + 300
            if row.get("status") != "ok":
                return None, None
            if row is usage[keys["claude-a"]] and model == "opus":
                return None, now + 300
            return (35.0, None) if row is usage[keys["claude-a"]] else (None, None)

        routes = [
            {"profile": "claude-a", "agent": "claude", "model": "haiku", "effort": None},
            {"profile": "claude-b", "agent": "claude", "model": "haiku", "effort": None},
            {"profile": "codex-a", "agent": "codex", "model": "gpt-6-luna", "effort": "medium"},
            {"profile": "agy-a", "agent": "antigravity", "model": "gemini-3.8-flash-low", "effort": None},
        ]
        with patch.object(bt_agents, "pool_for", return_value=list(profiles)), \
                patch.object(bt_agents, "account_key", side_effect=lambda profile, _provider=None: keys[profile]), \
                patch.object(bt_agents, "candidates", return_value=(routes, None)), \
                patch.object(bt_agents, "cooling_until", return_value=None), \
                patch.object(bt_profiles, "load", return_value=profiles), \
                patch.object(bt_subscriptions, "load", return_value=usage), \
                patch.object(bt_subscriptions, "capacity", side_effect=quota), \
                patch.object(bt_agy, "load_cache", return_value={"status": "ok", "observed_at": 95.0}), \
                patch.object(bt_agy, "capacity", return_value=(40.0, None)), \
                patch.object(bt_events, "read_all", return_value=telemetry), \
                patch.object(m2_adapter.shutil, "which", return_value="/usr/bin/provider"):
            rows = m2_adapter._candidate_rows("fixture", "implement", {"risk": "low", "scope": "small_change"}, now)

        by_route = {(row.profile, row.model, row.effort): row for row in rows}
        self.assertEqual(len(rows), 11)
        self.assertEqual(set(by_route), {
            ("claude-a", "haiku", None), ("claude-a", "sonnet", "xhigh"),
            ("claude-a", "opus", "xhigh"), ("claude-b", "haiku", None),
            ("claude-b", "sonnet", "xhigh"), ("claude-b", "opus", "xhigh"),
            ("codex-a", "gpt-6-luna", "medium"), ("codex-a", "gpt-6.1-sol", "high"),
            ("codex-a", "gpt-6.1-sol", "xhigh"), ("agy-a", "gemini-3.8-flash-low", None),
            ("agy-a", "gemini-3.8-flash-medium", None),
        })
        self.assertEqual(by_route[("claude-a", "haiku", None)].baseline_rank, 0)
        self.assertEqual(by_route[("claude-b", "haiku", None)].baseline_rank, 1)
        self.assertEqual(by_route[("codex-a", "gpt-6-luna", "medium")].baseline_rank, 2)
        self.assertEqual(by_route[("agy-a", "gemini-3.8-flash-low", None)].baseline_rank, 3)
        self.assertIsNone(by_route[("claude-a", "sonnet", "xhigh")].baseline_rank)
        self.assertEqual(by_route[("claude-a", "haiku", None)].account_ref,
                         by_route[("claude-a", "opus", "xhigh")].account_ref)
        self.assertEqual(by_route[("claude-a", "haiku", None)].quota_status, "available")
        self.assertEqual(by_route[("claude-a", "opus", "xhigh")].quota_status, "exhausted")
        self.assertEqual(by_route[("claude-a", "haiku", None)].history.verified_successes, 1)
        self.assertEqual(by_route[("claude-a", "haiku", None)].history.claimed_unverified, 1)
        self.assertEqual(by_route[("claude-a", "haiku", None)].history.duration_samples, 2)
        self.assertEqual(by_route[("claude-a", "haiku", None)].history.median_duration_seconds, 15)
        self.assertEqual(by_route[("claude-a", "haiku", None)].history.median_total_tokens, 150)
        self.assertEqual(by_route[("codex-a", "gpt-6-luna", "medium")].quota_status, "unknown")
        self.assertEqual(by_route[("codex-a", "gpt-6-luna", "medium")].auth_status, "unknown")
        self.assertEqual(by_route[("claude-b", "haiku", None)].quota_status, "exhausted")
        self.assertEqual(by_route[("agy-a", "gemini-3.8-flash-low", None)].quota_status, "available")
        ranked = rank_candidates(m2_request(candidates=rows, requested_at=now))
        self.assertEqual({row.profile for row in ranked.eligible}, {"claude-a", "agy-a"})
        self.assertTrue(any("capacity_exhausted" in item.reason_codes for item in ranked.exclusions))
        self.assertNotEqual(by_route[("claude-a", "haiku", None)].account_ref, keys["claude-a"])

    def test_unknown_and_stale_quota_are_not_eligible(self):
        now = 100.0
        with patch.object(bt_subscriptions, "capacity", return_value=(None, None)):
            unknown = m2_adapter._usage_facts("codex", "codex:one", "gpt-6-luna",
                                              {"codex:one": {"status": "not_sampled"}}, now)
        self.assertEqual(unknown[0], "unknown")
        self.assertEqual(unknown[1], "unknown")
        self.assertIsNone(unknown[4])
        with patch.object(bt_subscriptions, "capacity", return_value=(None, None)):
            stale = m2_adapter._usage_facts("claude", "claude:one", "sonnet",
                                            {"claude:one": {"status": "ok", "observed_at": -8000}}, now)
        self.assertEqual(stale[0], "stale")
        self.assertEqual(stale[1], "unknown")
        with patch.object(bt_subscriptions, "capacity", return_value=(None, None)):
            invalid = m2_adapter._usage_facts("codex", "codex:one", "gpt-6-luna",
                                              {"codex:one": {"status": "invalid_credentials", "observed_at": now}}, now)
        self.assertEqual(invalid[0], "unknown")
        self.assertEqual(invalid[1], "invalid")

    def test_claude_null_reset_is_known_in_m2_but_codex_null_reset_stays_unknown(self):
        now = 1_800_000_000.0
        reset = dt.datetime.fromtimestamp(now + 8000, dt.timezone.utc).isoformat()
        claude_profile, codex_profile = "claude-null", "codex-null"
        keys = {claude_profile: "claude:one", codex_profile: "codex:one"}
        profiles = {
            claude_profile: {"provider": "claude", "bin": "claude", "env": {}, "work_only": False},
            codex_profile: {"provider": "codex", "bin": "codex", "env": {}, "work_only": False},
        }
        claude_windows = quota_sources.parse_claude({
            "five_hour": {"utilization": 0, "resets_at": None},
            "seven_day": {"utilization": 96, "resets_at": reset},
        })
        self.assertIsNone(claude_windows["five_hour"]["resets_at"])
        usage = {
            keys[claude_profile]: {"provider": "claude", "status": "ok", "observed_at": now - 30,
                                   "windows": claude_windows},
            keys[codex_profile]: {"provider": "codex", "status": "ok", "observed_at": now - 30,
                                  "windows": {
                                      "five_hour": {"used_percent": 0, "resets_at": None, "window_minutes": 300},
                                      "seven_day": {"used_percent": 20, "resets_at": now + 8000,
                                                    "window_minutes": 10080},
                                  }},
        }
        routes = [{"profile": profile} for profile in profiles]
        with patch.object(bt_agents, "pool_for", return_value=list(profiles)), \
                patch.object(bt_agents, "account_key", side_effect=lambda profile, _provider=None: keys[profile]), \
                patch.object(bt_agents, "candidates", return_value=(routes, None)), \
                patch.object(bt_agents, "cooling_until", return_value=None), \
                patch.object(bt_profiles, "load", return_value=profiles), \
                patch.object(bt_subscriptions, "load", return_value=usage), \
                patch.object(bt_events, "read_all", return_value=[]), \
                patch.object(m2_adapter.shutil, "which", return_value="/usr/bin/provider"):
            rows = m2_adapter._candidate_rows("fixture", "implement",
                                              {"risk": "low", "scope": "small_change"}, now)

        by_profile = {row.profile: row for row in rows}
        self.assertEqual(by_profile[claude_profile].quota_status, "available")
        self.assertEqual(by_profile[claude_profile].quota_used_percent, 96)
        self.assertEqual(by_profile[codex_profile].quota_status, "unknown")
        result = rank_candidates(m2_request(candidates=rows, requested_at=now))
        self.assertEqual({row.profile for row in result.eligible}, {claude_profile})

        exhausted_windows = quota_sources.parse_claude({
            "five_hour": {"utilization": 100, "resets_at": None},
            "seven_day": {"utilization": 30, "resets_at": reset},
        })
        exhausted_row = {"provider": "claude", "status": "ok", "observed_at": now - 30,
                         "windows": exhausted_windows}
        exhausted = m2_adapter._usage_facts("claude", "claude:exhausted", "haiku",
                                           {"claude:exhausted": exhausted_row}, now)
        self.assertEqual(exhausted[0], "exhausted")
        self.assertEqual(exhausted[-1], "capacity_exhausted")

    def test_unrepresentable_cached_observation_is_unknown_without_crashing_m2(self):
        account = "codex:one"
        row = {"status": "ok", "observed_at": 10 ** 1000}
        with patch.object(bt_subscriptions, "capacity", return_value=(None, None)):
            facts = m2_adapter._usage_facts("codex", account, "gpt-6-luna", {account: row}, now=100.0)
        self.assertEqual(facts[0], "unknown")
        self.assertEqual(facts[1], "unknown")
        self.assertIsNone(facts[2])
        self.assertIsNone(facts[3])

    def test_codex_model_specific_bucket_unknown_blocks_only_its_model(self):
        now = 1_800_000_000.0
        payload = {"rateLimitsByLimitId": {
            "codex": {"primary": {"usedPercent": 10, "windowDurationMins": 300, "resetsAt": now + 1000},
                      "secondary": {"usedPercent": 20, "windowDurationMins": 10080, "resetsAt": now + 8000}},
            "model-scope": {"normalModelSlug": "gpt-6.1-sol",
                            "primary": {"usedPercent": 10, "windowDurationMins": 60, "resetsAt": now + 1000}},
        }}
        parsed = quota_sources.parse_codex(payload)
        sample = {"status": "ok", "observed_at": now, "windows": parsed}
        self.assertEqual(bt_subscriptions.capacity(sample, "gpt-6.1-sol", now), (None, None))
        self.assertEqual(bt_subscriptions.capacity(sample, "gpt-6-luna", now), (20, None))

        payload["rateLimitsByLimitId"]["model-scope"] = {
            "normalModelSlug": "gpt-6.1-sol", "spendControlReached": True,
            "primary": {"usedPercent": 10, "windowDurationMins": 300, "resetsAt": now + 1000},
        }
        parsed = quota_sources.parse_codex(payload)
        sample["windows"] = parsed
        self.assertEqual(bt_subscriptions.capacity(sample, "gpt-6.1-sol", now), (None, None))
        self.assertEqual(bt_subscriptions.capacity(sample, "gpt-6-luna", now), (20, None))


class M1DecisionPortTests(unittest.TestCase):
    def setUp(self):
        profiles = ("p1", "p2", "work", "work-codex")
        quota = {profile: {"status": "available", "reason": "quota_fresh"} for profile in profiles}
        preflight = patch.object(m1_adapter, "refresh_quota_preflight", return_value=quota)
        preflight.start()
        self.addCleanup(preflight.stop)
        requested_at = patch.object(plan_routing, "quota_aware_requested_at",
                                    side_effect=lambda initial_time, _refresh_status: initial_time)
        requested_at.start()
        self.addCleanup(requested_at.stop)

    def test_assignment_persists_decision_and_returns_only_resolvable_selected_reference(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            claude = candidate(provider="claude", model="sonnet", profile="p1", rank=0)
            codex = candidate(provider="codex", model="sol", profile="p2", rank=1)
            view = core.TaskView(
                "T1", "M1", "metodologia", ("scheduler-core",), ("skill/scripts/bt_scheduler_*/**",), 0,
                {"title": "Add a verified route adapter", "objective": "Keep M1 as the reservation authority.",
                 "complexity": "medium", "scope": "large_change", "estimated_minutes": 60, "risk": "medium",
                 "coupling": "high", "confidence": "high", "classification_evidence": {
                     name: {"justification": f"Verified {name} from the approved plan.",
                            "evidence": [f"spec:REQ-013#{name}"]}
                     for name in ("complexity", "scope", "duration", "risk", "coupling", "confidence")}},
                dependencies=("T0",), acceptance_criteria=("M1 validates and reserves the route.",),
                verification=({"type": "command", "value": "python -m unittest"},),
            )
            request = core.AssignmentRequest("REQ-013", 1, (view,), 1, 100.0, PLAN_HASH)
            port = m1_adapter.DecisionAssignmentPort("metodologia", root / "m2.sqlite3", laya_root=root)
            try:
                with patch.object(m1_adapter.decision_sources, "_candidate_rows", return_value=(claude, codex)):
                    first = port.propose(request)
                    replay = port.propose(request)
                self.assertEqual(len(first), 1)
                self.assertEqual(first, replay)
                self.assertTrue(first[0].executor.startswith("route:m2:v1:"))
                selected = m1_adapter.resolve_m2_route(root / "m2.sqlite3", first[0].executor)
                self.assertIsNotNone(selected)
                self.assertIn((selected["provider"], selected["model"], selected["profile"], selected["effort"]),
                              {(claude.provider, claude.model, claude.profile, claude.effort or ""),
                               (codex.provider, codex.model, codex.profile, codex.effort or "")})
            finally:
                port.close()

            restarted = m1_adapter.DecisionAssignmentPort("metodologia", root / "m2.sqlite3", laya_root=root)
            try:
                with patch.object(m1_adapter.decision_sources, "_candidate_rows", return_value=(claude, codex)):
                    after_restart = restarted.propose(request)
                self.assertEqual(after_restart, first)
            finally:
                restarted.close()

    def test_port_obeys_ready_limit_and_free_slots(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            port = m1_adapter.DecisionAssignmentPort("metodologia", root / "m2.sqlite3", laya_root=root)
            try:
                with patch.object(m1_adapter.decision_sources, "_candidate_rows", return_value=(candidate(),)) as build:
                    self.assertEqual(port.propose(core.AssignmentRequest("REQ-013", 1, (), 0, 100.0, PLAN_HASH)), ())
                    self.assertEqual(build.call_count, 0)
            finally:
                port.close()

    def test_m1_disables_laya_when_quality_artifacts_are_malformed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifacts = synthetic_quality_artifacts(root, "revision-a")
            calibration = artifacts[0]
            report = json.loads(calibration.read_text(encoding="utf-8"))
            report["checkpoint_results"][0]["confidence_gate"] = None
            calibration.write_text(json.dumps(report), encoding="utf-8")
            port = m1_adapter.DecisionAssignmentPort(
                "metodologia", root / "m2.sqlite3", laya_root=root, quality_artifacts=artifacts)
            try:
                self.assertFalse(port.quality_gate.enabled)
                self.assertIsNone(port.chooser)
            finally:
                port.close()

    def test_port_only_decides_ready_tasks_within_the_m1_free_slot_limit(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            port = m1_adapter.DecisionAssignmentPort("metodologia", root / "m2.sqlite3", laya_root=root)
            first_view = core.TaskView("T1", "M1", "repo", (), (), 0, {"title": "First task"})
            second_view = core.TaskView("T2", "M1", "repo", (), (), 0, {"title": "Second task"})
            request_value = core.AssignmentRequest("REQ-013", 1, (first_view, second_view), 1, 100.0, PLAN_HASH)
            try:
                with patch.object(m1_adapter.decision_sources, "_candidate_rows",
                                  side_effect=((), (candidate(),))) as build:
                    assignments = port.propose(request_value)
                self.assertEqual([item.task_id for item in assignments], ["T2"])
                self.assertEqual(build.call_count, 2)
            finally:
                port.close()

    def test_m1_reserves_the_m2_recommendation_through_its_assignment_contract(self):
        evidence = {name: {"justification": f"Inspected the quota-aware route task evidence for {name}.",
                           "evidence": [f"command:python -m unittest -> inspected {name} evidence"]}
                    for name in ("complexity", "scope", "duration", "risk", "coupling", "confidence")}
        plan = {
            "schema_version": "1.1.0", "plan_id": "REQ-013", "revision": 1, "spec_ref": "SPEC.md",
            "milestones": [{"id": "M1", "title": "Decision Engine",
                            "acceptance_criteria": ["The route is recommended and reserved by M1."]}],
            "tasks": [{
                "id": "T1", "milestone_id": "M1", "title": "Recommend a quota-aware route",
                "objective": "M2 recommends a route and M1 reserves it.", "repository": "metodologia", "after": [],
                "shared_resources": ["scheduler-decision"], "expected_paths": ["skill/scripts/bt_scheduler_*/**"],
                "acceptance_criteria": ["M1 authorizes every route."], "estimate_rationale": "The adapter path is known.",
                "verification": [{"type": "command", "value": "python -m unittest",
                                   "purpose": "verify the route contract"}],
                "complexity": "medium", "scope": "small_change", "estimated_minutes": 30,
                "risk": "medium", "coupling": "high", "confidence": "high",
                "classification_evidence": evidence,
            }],
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            requirement = root / "REQ-013-m2-e2e"
            requirement.mkdir()
            (requirement / "SPEC.md").write_text("# Decision Engine test specification\n", encoding="utf-8")
            (requirement / "PLAN.md").write_text(
                "---\nstatus: approved\n---\n# Plan\n\n### M1 — Decision Engine\n"
                "- [ ] T1 — Recommend a quota-aware route · repo: metodologia · "
                "verify: `python -m unittest` · files: skill/scripts/bt_scheduler_*/** · "
                "resources: scheduler-decision\n", encoding="utf-8")
            plan_path = requirement / "PLAN.json"
            plan_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
            plan_messages = []
            self.assertEqual(plan_adapter.run_cli("check", requirement, as_json=True, emit=plan_messages.append), 0,
                             plan_messages)
            self.assertEqual(plan_adapter.run_cli("freeze", requirement, emit=plan_messages.append), 0,
                             plan_messages)
            approved_plan = m1_adapter.approved_plan(requirement)
            self.assertEqual((approved_plan.plan_id, approved_plan.revision), ("REQ-013", 1))

            port = m1_adapter.DecisionAssignmentPort("metodologia", root / "m2.sqlite3", laya_root=root)
            try:
                with patch.object(m1_adapter.decision_sources, "_candidate_rows",
                                  return_value=(candidate(rank=0), candidate(provider="codex", model="sol",
                                                                            profile="work-codex", rank=1))):
                    scheduler = core.SchedulerCore(
                        approved_plan, core.InMemoryRepository(),
                        ports=core.Ports(assignment=port, execution=core.FakeExecutor(),
                                         verification=core.FakeVerifier()),
                        config=core.Config(max_parallel_tasks=1), clock=lambda: 100.0,
                    )
                    scheduler.start()
                    scheduler.step()
                task = scheduler.snapshot().tasks["T1"]
                self.assertEqual(task["state"], "active")
                self.assertTrue(task["executor"].startswith("route:m2:v1:"))
                self.assertEqual(scheduler.read(lambda ctx: len(ctx.state.attempts)), 1)
                selected_route = m1_adapter.resolve_m2_route(root / "m2.sqlite3", task["executor"])
                self.assertIsNotNone(selected_route)
                self.assertIn((selected_route["provider"], selected_route["model"], selected_route["profile"]),
                              {("claude", "sonnet", "work"), ("codex", "sol", "work-codex")})
            finally:
                port.close()


if __name__ == "__main__":
    unittest.main()
