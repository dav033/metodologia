"""Offline integration for the M2 batch assignment port and the M1->M3 route binding."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
import time
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bt_agents
import bt_scheduler_adapter as m1
import scheduler_executor_support as s
from bt_scheduler_core.plan import Plan, TaskSpec
from bt_scheduler_decision import DecisionInputError
from bt_scheduler_decision.tests.support import PLAN_HASH
from scheduler_chain_support import real_candidate

core = s.core
FROZEN_PLAN = (Path(__file__).resolve().parents[3] / "bitacora" / "metodologia" / "artifacts" /
               "REQ-017-planner-rerun-opus55-high-20261016" / "plan-revisions" / "PLAN.r1.json")
FROZEN_PLAN_SHA256 = "56b645ba9651161856cab0d5ed4024b4f0babb25106fd7a91f1660b68e1cf05c"


def frozen_req017_views():
    raw = FROZEN_PLAN.read_bytes()
    if hashlib.sha256(raw).hexdigest() != FROZEN_PLAN_SHA256:
        raise AssertionError("frozen REQ-017 r1 fixture hash changed")
    plan = json.loads(raw)
    if (plan.get("plan_id"), plan.get("revision"), len(plan.get("tasks", ()))) != ("REQ-017", 1, 7):
        raise AssertionError("frozen REQ-017 r1 fixture identity changed")
    return tuple(core.TaskView(
        task["id"], task["milestone_id"], task["repository"], tuple(task.get("shared_resources", ())),
        tuple(task.get("expected_paths", ())), 0,
        {key: task[key] for key in ("title", "objective", "complexity", "scope", "estimated_minutes", "risk",
                                    "coupling", "confidence", "classification_evidence") if key in task},
        dependencies=tuple(task.get("after", ())),
        acceptance_criteria=tuple(task.get("acceptance_criteria", ())),
        verification=tuple(task.get("verification", ())),
    ) for task in plan["tasks"])


def synthetic_routes(view, now):
    """Provide deterministic capable route rows while varying quota pressure across the frozen DAG."""
    from bt_scheduler_decision_adapter import _tier_for, task_facts

    _, kind, classifications = task_facts(view.id, view.meta, view.dependencies, view.acceptance_criteria,
                                           view.verification, view.shared_resources, view.expected_paths)
    tier = _tier_for(classifications, kind)
    preferred = ("claude-personal", "codex-luis", "agy-1")[int(view.id[1]) % 3]
    profiles = (("claude", "claude-personal"), ("codex", "codex-luis"), ("antigravity", "agy-1"),
                ("codex", "codex-1"))
    output = []
    for rank, (provider, profile) in enumerate(profiles):
        model, effort = bt_agents.model_for(provider, tier, kind=kind)
        pressure = 5.0 if profile == preferred else 25.0 + rank
        output.append(real_candidate(provider=provider, model=model, profile=profile, effort=effort, rank=rank,
                                     observed_at=now - 1, valid_until=now + 3600, used_percent=pressure))
    return tuple(output)


class DecisionAssignmentIntegration(s.World):
    def port(self):
        port = m1.DecisionAssignmentPort("proj", self.tmp / "decisions.db", laya_root=self.tmp)
        self.addCleanup(port.close)
        return port

    @staticmethod
    def view(task_id: str, title: str, resources: tuple[str, ...] = ()):
        return core.TaskView(task_id, "M1", "app", resources, (f"{task_id}/**",), 0,
                             {"title": title, "risk": "low", "complexity": "low", "scope": "small_change"})

    def candidate(self, provider: str, model: str, profile: str, rank: int, now: float, used_percent: float = 10.0):
        return real_candidate(provider=provider, model=model, profile=profile, effort="low", rank=rank,
                              observed_at=now - 1, valid_until=now + 3600, used_percent=used_percent)

    def stored_batches(self, path: Path):
        connection = sqlite3.connect(path)
        try:
            return [json.loads(row[0]) for row in connection.execute("SELECT plan_json FROM batch_decisions")]
        finally:
            connection.close()

    def test_batch_routes_resolve_through_m3_and_replay_idempotently(self):
        now = time.time()
        claude = self.candidate("claude", "sonnet", "claude-personal", 0, now, 5)
        codex = self.candidate("codex", "gpt-6-luna", "codex-1", 1, now, 75)
        request = core.AssignmentRequest(
            "REQ-042", 1, (self.view("T1", "Flexible task"), self.view("T2", "Codex-only task")),
            2, now, PLAN_HASH,
        )
        port = self.port()
        candidates = iter(((claude, codex), (codex,), (claude, codex), (codex,)))
        with (patch.object(m1, "refresh_quota_preflight", return_value={
                    "claude-personal": {"status": "available", "reason": "quota_fresh"},
                    "codex-1": {"status": "available", "reason": "quota_fresh"},
                }),
                patch.object(m1.decision_sources, "_candidate_rows", side_effect=lambda *args: next(candidates)),
                patch("bt_scheduler_plan_routing.time.time", return_value=now)):
            first = port.propose(request)
            replay = port.propose(request)

        self.assertEqual(first, replay)
        self.assertEqual([item.task_id for item in first], ["T1", "T2"])
        self.assertEqual([item.executor.startswith("route:m2:v1:") for item in first], [True, True])
        batches = self.stored_batches(self.tmp / "decisions.db")
        self.assertEqual(len(batches), 1)
        self.assertEqual(batches[0]["considered_task_count"], 2)
        self.assertEqual(len(batches[0]["assignments"]), 2)

        resolver = s.adapter.RouteResolver("proj", m2_lookup=s.adapter.m2_ledger_lookup(self.tmp / "decisions.db"))
        for assignment, expected in zip(first, (("claude", "sonnet", "claude-personal"),
                                                ("codex", "gpt-6-luna", "codex-1")), strict=True):
            route_request = s.adapter.m3.StartRequest(
                idempotency_key=f"route-{assignment.task_id}", plan_id=request.plan_id, revision=request.revision,
                task_id=assignment.task_id, attempt_id=f"attempt-{assignment.task_id}", token=1,
                executor=assignment.executor, repository="app", project="proj", plan_sha256=request.plan_sha256,
            )
            route = resolver.resolve(route_request)
            self.assertEqual((route.provider, route.model, route.profile), expected)

    def test_m1_still_enforces_shared_resource_exclusivity(self):
        now = time.time()
        claude = self.candidate("claude", "sonnet", "claude-personal", 0, now)
        codex = self.candidate("codex", "gpt-6-luna", "codex-1", 1, now)
        tasks = tuple(TaskSpec(
            task_id, "M1", (), "app", ("shared-db",), (f"{task_id}/**",), ("task is valid",), (),
            {"title": f"Task {task_id}", "risk": "low", "complexity": "low", "scope": "small_change"},
        ) for task_id in ("T1", "T2"))
        plan = Plan("REQ-042", 1, "1.0.0", PLAN_HASH, tasks)
        port = self.port()
        with (patch.object(m1, "refresh_quota_preflight", return_value={
                    "claude-personal": {"status": "available", "reason": "quota_fresh"},
                    "codex-1": {"status": "available", "reason": "quota_fresh"},
                }),
                patch.object(m1.decision_sources, "_candidate_rows", return_value=(claude, codex))):
            scheduler = core.SchedulerCore(
                plan, core.InMemoryRepository(),
                ports=core.Ports(assignment=port, execution=core.FakeExecutor(), verification=core.FakeVerifier()),
                config=core.Config(max_parallel_tasks=2), clock=lambda: now,
            )
            scheduler.start()
            scheduler.step()

        self.assertEqual({task: row["state"] for task, row in scheduler.snapshot().tasks.items()},
                         {"T1": "active", "T2": "ready"})
        self.assertEqual(len(self.stored_batches(self.tmp / "decisions.db")[0]["assignments"]), 2)

    def test_assignment_count_never_exceeds_m1_free_slots(self):
        now = time.time()
        claude = self.candidate("claude", "sonnet", "claude-personal", 0, now)
        request = core.AssignmentRequest(
            "REQ-042", 1, tuple(self.view(f"T{i}", f"Task {i}") for i in range(1, 4)), 1, now, PLAN_HASH,
        )
        with (patch.object(m1, "refresh_quota_preflight", return_value={
                    "claude-personal": {"status": "available", "reason": "quota_fresh"},
                }),
                patch.object(m1.decision_sources, "_candidate_rows", return_value=(claude,))):
            assignments = self.port().propose(request)
        self.assertLessEqual(len(assignments), request.free_slots)

    def test_ready_batch_preserves_audit_baseline(self):
        now = time.time()
        baseline = self.candidate("claude", "sonnet", "claude-personal", 0, now, 90)
        alternative = self.candidate("codex", "gpt-6-luna", "codex-1", 1, now, 5)
        request = core.AssignmentRequest(
            "REQ-042", 1, (self.view("T1", "Audit completed change"),), 1, now, PLAN_HASH,
        )
        port = self.port()
        with (patch.object(m1, "refresh_quota_preflight", return_value={
                    "claude-personal": {"status": "available", "reason": "quota_fresh"},
                    "codex-1": {"status": "available", "reason": "quota_fresh"},
                }) as refresh,
                patch.object(m1.decision_sources, "_candidate_rows", return_value=(baseline, alternative))):
            assignments = port.propose(request)

        self.assertEqual(len(assignments), 1)
        self.assertEqual(assignments[0].route_metadata["profile"], "claude-personal")
        refresh.assert_called_once_with("proj")

    def test_ready_batch_fails_closed_when_refresh_fails_despite_fresh_cached_candidate(self):
        now = time.time()
        claude = self.candidate("claude", "sonnet", "claude-personal", 0, now, 5)
        request = core.AssignmentRequest(
            "REQ-042", 1, (self.view("T1", "Fresh-looking task"),), 1, now, PLAN_HASH,
        )
        port = self.port()
        with (patch.object(m1, "refresh_quota_preflight", return_value={
                    "claude-personal": {"status": "unavailable", "reason": "quota_refresh_failed"},
                }),
                patch.object(m1.decision_sources, "_candidate_rows", return_value=(claude,))):
            assignments = port.propose(request)

        self.assertEqual(assignments, ())
        batches = self.stored_batches(self.tmp / "decisions.db")
        self.assertEqual(batches, [])

    def test_unavailable_ready_polls_preserve_ledger_capacity_for_quota_recovery(self):
        now = time.time()
        claude = self.candidate("claude", "sonnet", "claude-personal", 0, now, 5)
        port = self.port()
        quota = {"claude-personal": {"status": "unavailable", "reason": "quota_refresh_failed"}}
        with (patch("bt_scheduler_decision.batch_ledger.MAX_BATCH_RECORDS", 2),
                patch.object(m1, "refresh_quota_preflight", return_value=quota),
                patch.object(m1.decision_sources, "_candidate_rows", return_value=(claude,))):
            for tick in range(3):
                poll_time = now + tick
                request = core.AssignmentRequest(
                    "REQ-042", 1, (self.view("T1", "Recoverable task"),), 1, poll_time, PLAN_HASH,
                )
                with patch("bt_scheduler_plan_routing.time.time", return_value=poll_time):
                    self.assertEqual(port.propose(request), ())

            self.assertEqual(self.stored_batches(self.tmp / "decisions.db"), [])
            quota["claude-personal"] = {"status": "available", "reason": "quota_fresh"}
            request = core.AssignmentRequest(
                "REQ-042", 1, (self.view("T1", "Recoverable task"),), 1, now + 3, PLAN_HASH,
            )
            with patch("bt_scheduler_plan_routing.time.time", return_value=now + 3):
                assignments = port.propose(request)

        self.assertEqual(len(assignments), 1)
        self.assertEqual(assignments[0].task_id, "T1")
        batches = self.stored_batches(self.tmp / "decisions.db")
        self.assertEqual(len(batches), 1)
        self.assertEqual(len(batches[0]["assignments"]), 1)

    def test_ready_batch_over_limit_fails_explicitly_without_truncating_tasks(self):
        now = time.time()
        ready = tuple(self.view(f"T{i}", f"Task {i}") for i in range(129))
        request = core.AssignmentRequest("REQ-042", 1, ready, 1, now, PLAN_HASH)
        with (patch.object(m1, "refresh_quota_preflight") as refresh,
              patch.object(m1.decision_sources, "_candidate_rows") as candidates,
              self.assertRaisesRegex(DecisionInputError, "ready_batch:task_limit_exceeded")):
            self.port().propose(request)

        refresh.assert_not_called()
        candidates.assert_not_called()

    def test_full_plan_routing_recommends_every_task_without_batch_reservations(self):
        now = time.time()
        claude = self.candidate("claude", "sonnet", "claude-personal", 0, now, 5)
        blocked = core.TaskView("T2", "M2", "app", (), ("T2/**",), 0,
                                {"title": "Blocked child", "complexity": "medium", "scope": "small_change",
                                 "risk": "low"}, dependencies=("T1",))
        request = core.PlanRoutingRequest(
            "REQ-042", 1, PLAN_HASH,
            (self.view("T1", "Ready task"), blocked, self.view("T3", "Another task")), now,
        )
        port = self.port()
        with (patch.object(port.engine, "decide", side_effect=AssertionError("full-plan routing is batch-only")),
                patch.object(m1, "refresh_quota_preflight", return_value={
                    "claude-personal": {"status": "available", "reason": "quota_fresh"},
                }),
                patch.object(m1.decision_sources, "_candidate_rows", return_value=(claude,)) as candidates):
            routes = port.plan(request)

        self.assertEqual([item.task_id for item in routes], ["T1", "T2", "T3"])
        self.assertTrue(all(item.contract_version == core.ROUTING_CONTRACT_VERSION for item in routes))
        self.assertTrue(all(item.route_metadata["model"] == "sonnet" for item in routes))
        self.assertTrue(all(item.route_metadata["quota_state"] == "fresh" for item in routes))
        self.assertTrue(all(item.route_metadata["quota_reason"] == "quota_fresh" for item in routes))
        self.assertEqual(candidates.call_count, 3)
        batches = self.stored_batches(self.tmp / "decisions.db")
        self.assertEqual(len(batches), 1)
        self.assertEqual(batches[0]["considered_task_count"], 3)
        self.assertEqual(len(batches[0]["assignments"]), 3)
        self.assertEqual(len(batches[0]["quota_evidence"]), 3)
        self.assertTrue(all(item["state"] == "fresh" for item in batches[0]["quota_evidence"]))
        connection = sqlite3.connect(self.tmp / "decisions.db")
        try:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM decision_records").fetchone()[0], 0)
        finally:
            connection.close()

    def test_full_plan_audit_keeps_baseline_when_quota_favors_an_alternative(self):
        now = time.time()
        baseline = self.candidate("claude", "sonnet", "claude-personal", 0, now, 90)
        alternative = self.candidate("codex", "gpt-6-luna", "codex-1", 1, now, 5)
        request = core.PlanRoutingRequest(
            "REQ-042", 1, PLAN_HASH, (self.view("T1", "Audit completed change"),), now,
        )
        with (patch.object(m1, "refresh_quota_preflight", return_value={
                    "claude-personal": {"status": "available", "reason": "quota_fresh"},
                    "codex-1": {"status": "available", "reason": "quota_fresh"},
                }),
                patch.object(m1.decision_sources, "_candidate_rows", return_value=(baseline, alternative))):
            routes = self.port().plan(request)

        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0].route_metadata["profile"], "claude-personal")

    def test_full_plan_fails_closed_when_preflight_fails_despite_fresh_cached_candidate(self):
        now = time.time()
        claude = self.candidate("claude", "sonnet", "claude-personal", 0, now, 5)
        request = core.PlanRoutingRequest("REQ-042", 1, PLAN_HASH, (self.view("T1", "Fresh-looking task"),), now)
        with (patch.object(m1, "refresh_quota_preflight", return_value={
                    "claude-personal": {"status": "unavailable", "reason": "quota_refresh_failed"},
                }),
                patch.object(m1.decision_sources, "_candidate_rows", return_value=(claude,))):
            routes = self.port().plan(request)

        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0].route_metadata, {})
        self.assertEqual(routes[0].reason, "no_eligible_route")
        batch = self.stored_batches(self.tmp / "decisions.db")[0]
        self.assertEqual(batch["quota_evidence"][0]["state"], "refresh_failed")
        self.assertEqual(batch["quota_evidence"][0]["reason_code"], "quota_refresh_failed")

    def test_full_plan_accepts_fresh_preflight_observation_newer_than_m1_clock(self):
        now = time.time()
        observed_at = now + 3.0
        request = core.PlanRoutingRequest("REQ-042", 1, PLAN_HASH, (self.view("T1", "Fresh task"),), now)
        port = self.port()
        requested_at_values = []

        def candidates(_project, _kind, _classifications, requested_at):
            requested_at_values.append(requested_at)
            self.assertGreaterEqual(requested_at, observed_at)
            return (real_candidate(provider="claude", model="sonnet", profile="claude-personal", effort="low",
                                   rank=0, observed_at=observed_at, valid_until=observed_at + 3600,
                                   used_percent=5),)

        with (patch.object(m1, "refresh_quota_preflight", return_value={
                    "claude-personal": {"status": "available", "state": "fresh", "reason": "quota_fresh",
                                        "observed_at": observed_at, "valid_until": observed_at + 3600,
                                        "used_percent": 5},
                }),
                patch.object(m1.decision_sources, "_candidate_rows", side_effect=candidates)):
            routes = port.plan(request)

        self.assertEqual(len(routes), 1)
        self.assertTrue(routes[0].route_metadata)
        self.assertEqual(routes[0].route_metadata["quota_state"], "fresh")
        self.assertEqual(float(routes[0].route_metadata["quota_observed_at"]), observed_at)
        self.assertGreaterEqual(requested_at_values[0], observed_at)

    def test_ready_batch_accepts_fresh_preflight_observation_newer_than_m1_clock(self):
        now = time.time()
        observed_at = now + 3.0
        request = core.AssignmentRequest("REQ-042", 1, (self.view("T1", "Fresh task"),), 1, now, PLAN_HASH)
        port = self.port()
        requested_at_values = []

        def candidates(_project, _kind, _classifications, requested_at):
            requested_at_values.append(requested_at)
            self.assertGreaterEqual(requested_at, observed_at)
            return (real_candidate(provider="claude", model="sonnet", profile="claude-personal", effort="low",
                                   rank=0, observed_at=observed_at, valid_until=observed_at + 3600,
                                   used_percent=5),)

        with (patch.object(m1, "refresh_quota_preflight", return_value={
                    "claude-personal": {"status": "available", "state": "fresh", "reason": "quota_fresh",
                                        "observed_at": observed_at, "valid_until": observed_at + 3600,
                                        "used_percent": 5},
                }),
                patch.object(m1.decision_sources, "_candidate_rows", side_effect=candidates)):
            assignments = port.propose(request)

        self.assertEqual(len(assignments), 1)
        self.assertGreaterEqual(requested_at_values[0], observed_at)

    def test_oversized_full_plan_returns_one_stable_reason_per_input_task(self):
        now = time.time()
        tasks = tuple(self.view(f"T{i}", f"Task {i}") for i in range(129))
        request = core.PlanRoutingRequest("REQ-042", 1, PLAN_HASH, tasks, now)
        with patch.object(m1, "refresh_quota_preflight") as refresh:
            routes = self.port().plan(request)

        self.assertEqual(len(routes), len(tasks))
        self.assertTrue(all(item.reason == "m2_batch_task_limit_exceeded" for item in routes))
        refresh.assert_not_called()

    def test_frozen_req017_dag_routes_by_fresh_account_quota_without_reserving(self):
        now = time.time()
        views = frozen_req017_views()
        self.assertEqual({view.meta["complexity"] for view in views}, {"low", "medium"})
        request = core.PlanRoutingRequest("REQ-017", 1, FROZEN_PLAN_SHA256, views, now)
        quota = {
            "claude-personal": {"status": "available", "state": "fresh", "reason": "quota_fresh"},
            "codex-luis": {"status": "available", "state": "fresh", "reason": "quota_fresh"},
            "agy-1": {"status": "available", "state": "fresh", "reason": "quota_fresh"},
            "codex-1": {"status": "unavailable", "state": "stale", "reason": "quota_observation_stale"},
        }
        port = self.port()
        candidate_views = iter(views)
        with (patch.object(m1, "refresh_quota_preflight", return_value=quota),
              patch.object(m1.decision_sources, "_candidate_rows",
                           side_effect=lambda _project, _kind, _facts, _now: synthetic_routes(
                               next(candidate_views), now))):
            routes = port.plan(request)

        self.assertEqual([route.task_id for route in routes], [view.id for view in views])
        self.assertTrue(all(route.route_metadata for route in routes))
        self.assertEqual({route.route_metadata["provider"] for route in routes},
                         {"claude", "codex", "antigravity"})
        self.assertTrue(all(route.route_metadata["profile"] != "codex-1" for route in routes))
        self.assertTrue(all(route.route_metadata["account_ref"] and route.route_metadata["model"] and
                            route.route_metadata["assignment_reason"] for route in routes))
        from bt_scheduler_decision_adapter import _tier_for, task_facts
        views_by_id = {view.id: view for view in views}
        for route in routes:
            view = views_by_id[route.task_id]
            _, kind, classifications = task_facts(view.id, view.meta, view.dependencies, view.acceptance_criteria,
                                                   view.verification, view.shared_resources, view.expected_paths)
            tier = _tier_for(classifications, kind)
            expected_model, expected_effort = bt_agents.model_for(
                route.route_metadata["provider"], tier, kind=kind,
            )
            self.assertEqual((route.route_metadata["model"], route.route_metadata["effort"]),
                             (expected_model, expected_effort or ""))
            self.assertEqual(route.route_metadata["quota_state"], "fresh")
        batches = self.stored_batches(self.tmp / "decisions.db")
        self.assertEqual(len(batches), 1)
        self.assertEqual(batches[0]["considered_task_count"], 7)
        self.assertEqual(len(batches[0]["assignments"]), 7)
        stale_rows = [row for row in batches[0]["quota_evidence"] if row["profile"] == "codex-1"]
        self.assertEqual(len(stale_rows), 7)
        self.assertTrue(all((row["state"], row["reason_code"]) == ("stale", "quota_observation_stale")
                            for row in stale_rows))
        connection = sqlite3.connect(self.tmp / "decisions.db")
        try:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM decision_records").fetchone()[0], 0)
        finally:
            connection.close()

    def test_ready_revalidation_uses_changed_quota_and_m1_owns_the_only_reservation(self):
        now = time.time()
        view = frozen_req017_views()[0]
        task = TaskSpec(view.id, view.milestone_id, view.dependencies, view.repository, view.shared_resources,
                        view.expected_paths, view.acceptance_criteria, view.verification, view.meta)
        plan = Plan("REQ-017", 1, "1.1.0", FROZEN_PLAN_SHA256, (task,))
        first_quota = {
            "claude-personal": {"status": "available", "state": "fresh", "reason": "quota_fresh"},
            "codex-luis": {"status": "unavailable", "state": "stale", "reason": "quota_observation_stale"},
            "agy-1": {"status": "available", "state": "fresh", "reason": "quota_fresh"},
            "codex-1": {"status": "unavailable", "state": "stale", "reason": "quota_observation_stale"},
        }
        changed_quota = {
            "claude-personal": {"status": "unavailable", "state": "stale", "reason": "quota_observation_stale"},
            "codex-luis": {"status": "available", "state": "fresh", "reason": "quota_fresh"},
            "agy-1": {"status": "available", "state": "fresh", "reason": "quota_fresh"},
            "codex-1": {"status": "unavailable", "state": "stale", "reason": "quota_observation_stale"},
        }
        current_quota = [first_quota]
        refresh_calls = []
        port = self.port()
        with (patch.object(m1, "refresh_quota_preflight", side_effect=lambda _project: (
                    refresh_calls.append(current_quota[0]) or current_quota[0])),
              patch.object(m1.decision_sources, "_candidate_rows",
                           side_effect=lambda _project, _kind, _facts, _now: synthetic_routes(view, now)),
              patch("bt_scheduler_plan_routing.time.time", return_value=now)):
            initial = port.plan(core.PlanRoutingRequest("REQ-017", 1, FROZEN_PLAN_SHA256, (view,), now))
            scheduler = core.SchedulerCore(
                plan, core.InMemoryRepository(), ports=core.Ports(assignment=port),
                config=core.Config(max_parallel_tasks=1), clock=lambda: now,
            )
            scheduler.start()
            self.assertEqual(scheduler.snapshot().tasks[view.id]["state"], "ready")
            current_quota[0] = changed_quota
            report = scheduler.step()

        self.assertNotEqual(initial[0].route_metadata["profile"], "codex-luis")
        self.assertEqual(refresh_calls, [first_quota, changed_quota])
        self.assertEqual(len(report.claimed), 1)
        self.assertEqual(scheduler.snapshot().tasks[view.id]["state"], "active")
        attempts = scheduler.read(lambda ctx: tuple(ctx.state.attempts.values()))
        self.assertEqual(len(attempts), 1)
        selected = s.adapter.m2_ledger_lookup(self.tmp / "decisions.db")(attempts[0].executor)
        self.assertEqual((selected["profile"], selected["provider"], selected["model"], selected["effort"]),
                         ("codex-luis", "codex", "gpt-6.1-sol", "medium"))


if __name__ == "__main__":
    import unittest

    unittest.main()
