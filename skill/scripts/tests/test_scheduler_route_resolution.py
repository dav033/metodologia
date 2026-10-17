"""Integration coverage for resolving persisted M2 routes through M3's route and policy gates."""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bt_scheduler_executor as m3
import scheduler_executor_support as s
from scheduler_executor_support import adapter, core


def req(ref="direct:claude/sonnet#xhigh", **kw):
    base = {"idempotency_key": "k1", "plan_id": "REQ-042", "revision": 1, "task_id": "T1",
            "plan_sha256": "a" * 64, "attempt_id": "att-0001", "token": 1,
            "executor": ref, "repository": "app", "project": "proj"}
    base.update(kw)
    return m3.StartRequest(**base)


class M2Routes(s.World):
    """References produced by the real M2 decision ledger resolve through its public lookup, and only the selected route."""

    def setUp(self):
        super().setUp()
        try:
            import bt_scheduler_decision as m2
            from bt_scheduler_decision.tests.support import request
            from bt_scheduler_decision.tests.test_recorder import _record
            from scheduler_chain_support import real_candidate as candidate
        except Exception as error:  # noqa: BLE001
            self.skipTest(f"M2 module not importable here: {type(error).__name__}")
        import dataclasses

        def for_this_plan(**kw):                         # the decisions are for the plan and task the tests run (REQ-042/T1)
            asked = request(**kw)
            return dataclasses.replace(asked, plan_id="REQ-042", revision=1,
                                       plan_sha256=getattr(self, "sha", asked.plan_sha256),
                                       task=dataclasses.replace(asked.task, task_id="T1"))

        self.m2, self.candidate, self.request, self.make_record = m2, candidate, for_this_plan, _record
        self.ledger_path = self.tmp / "decisions.db"
        self.ledger = m2.DecisionLedger(self.ledger_path)

    def refs(self):
        now = time.time()
        selected = self.candidate(provider="claude", model="sonnet", profile="claude-personal", effort="low", rank=0,
                                  observed_at=now - 1, valid_until=now + 3600)
        other = self.candidate(provider="codex", model="gpt-6-luna", profile="codex-1", effort="low", rank=1,
                               observed_at=now - 1, valid_until=now + 3600)
        asked = self.request(candidates=(selected, other), requested_at=now)
        saved = self.ledger.persist(asked, self.make_record(asked))
        return (self.m2.executor_reference(saved.decision_id, selected.route_id),
                self.m2.executor_reference(saved.decision_id, other.route_id))

    def test_the_selected_route_of_a_real_decision_resolves_to_a_launchable_route(self):
        selected_ref, _ = self.refs()
        resolver = adapter.RouteResolver("proj", m2_lookup=adapter.m2_ledger_lookup(self.ledger_path))
        route = resolver.resolve(req(selected_ref))
        self.assertEqual((route.provider, route.model, route.profile, route.effort, route.reference),
                         ("claude", "sonnet", "claude-personal", "low", selected_ref))
        self.assertGreater(route.quota_valid_until, time.time())

    def test_a_decision_made_for_another_task_is_refused(self):
        selected_ref, _ = self.refs()                    # the fixture's decision belongs to REQ-042 / T1
        resolver = adapter.RouteResolver("proj", m2_lookup=adapter.m2_ledger_lookup(self.ledger_path))
        with self.assertRaises(m3.ExecutorError) as caught:
            resolver.resolve(req(selected_ref, plan_id="REQ-777", task_id="T9"))
        self.assertEqual(caught.exception.code, "ROUTE_INVALID")

    def test_a_decision_that_a_later_one_replaced_is_refused(self):
        first_ref, _ = self.refs()
        replacement = self.candidate(provider="codex", model="gpt-6-luna", profile="codex-1", effort="low", rank=0)
        asked = self.request(candidates=(replacement,), requested_at=500.0)
        self.ledger.persist(asked, self.make_record(asked, created_at=500.0))
        binding = self.m2.resolve_executor_binding(self.ledger_path, first_ref)
        resolver = adapter.RouteResolver("proj", m2_lookup=adapter.m2_ledger_lookup(self.ledger_path))
        with self.assertRaises(m3.ExecutorError) as caught:
            resolver.resolve(req(first_ref, plan_id=binding.plan_id, revision=binding.revision, task_id=binding.task_id))
        self.assertEqual(caught.exception.code, "ROUTE_INVALID")
        self.assertIn("replaced", caught.exception.detail)

    def test_the_live_decision_for_its_own_task_launches(self):
        selected_ref, _ = self.refs()
        binding = self.m2.resolve_executor_binding(self.ledger_path, selected_ref)
        resolver = adapter.RouteResolver("proj", m2_lookup=adapter.m2_ledger_lookup(self.ledger_path))
        route = resolver.resolve(req(selected_ref, plan_id=binding.plan_id, revision=binding.revision,
                                     task_id=binding.task_id))
        self.assertEqual(route.reference, selected_ref)

    def test_an_alternative_that_m2_did_not_select_is_never_run(self):
        _, alternative_ref = self.refs()
        resolver = adapter.RouteResolver("proj", m2_lookup=adapter.m2_ledger_lookup(self.ledger_path))
        with self.assertRaises(m3.ExecutorError) as caught:
            resolver.resolve(req(alternative_ref))
        self.assertEqual(caught.exception.code, "ROUTE_UNRESOLVABLE")

    def test_an_unreadable_ledger_is_a_transient_refusal_not_a_sticky_unknown(self):
        selected_ref, _ = self.refs()
        resolver = adapter.RouteResolver("proj", m2_lookup=adapter.m2_ledger_lookup(self.tmp / "missing" / "nope.db"))
        with self.assertRaises(m3.ExecutorError) as caught:
            resolver.resolve(req(selected_ref))
        self.assertEqual(caught.exception.code, "PORT_ERROR")

    def test_the_policy_still_applies_to_what_m2_selected(self):
        now = time.time()
        bad = self.candidate(provider="claude", model="sonnet", profile="claude-work", effort="low", rank=0,
                             observed_at=now - 1, valid_until=now + 3600)
        asked = self.request(candidates=(bad,), requested_at=now)
        saved = self.ledger.persist(asked, self.make_record(asked))
        ref = self.m2.executor_reference(saved.decision_id, bad.route_id)
        resolver = adapter.RouteResolver("proj", m2_lookup=adapter.m2_ledger_lookup(self.ledger_path))
        with self.assertRaises(m3.ExecutorError) as caught:       # a work-only account for a personal project
            resolver.resolve(req(ref))
        self.assertEqual(caught.exception.code, "POLICY_DENIED")

    def test_wire_accepts_the_ledger_path_and_the_whole_chain_runs_a_selected_route(self):
        self.approve([s.task("T1", "ok")])
        selected_ref, _ = self.refs()
        wiring = self.wire(selected_ref, m2_ledger=self.ledger_path)
        self.assertTrue(self.run_until(wiring, lambda snap: snap.status == "completed"), wiring.scheduler.snapshot())
        record = self.records()[0]
        self.assertEqual(record["provider"], "claude")
        self.assertEqual(record["argv"][record["argv"].index("--model") + 1], "sonnet")
        self.assertEqual(record["env"]["CLAUDE_CONFIG_DIR"], str(self.tmp / "claude-a"))


class AuditFixes(s.World):
    """Regressions for the independent audits of the M2->M3 and planner->M1->M3 seams."""

    def test_the_route_prefixed_form_m1s_assignment_port_emits_resolves_like_the_bare_one(self):
        found = {"m2:v1:" + "a" * 64 + ":" + "b" * 64: {"provider": "claude", "model": "haiku",
                                                           "profile": "claude-personal",
                                                           "plan_sha256": "a" * 64,
                                                           "quota_valid_until": time.time() + 3600}}
        seen = []

        def lookup(ref, request):
            seen.append(ref)
            return found.get(ref.removeprefix("route:"))
        resolver = adapter.RouteResolver("proj", m2_lookup=lookup)
        route = resolver.resolve(req("route:" + next(iter(found))))
        self.assertEqual((route.model, route.single_use), ("haiku", True))

    def test_direct_references_are_refused_while_m2_selects_routes_unless_the_operator_allows_them(self):
        lookup = lambda ref, request: None
        with self.assertRaises(m3.ExecutorError) as caught:
            adapter.RouteResolver("proj", m2_lookup=lookup).resolve(req("direct:claude/haiku"))
        self.assertEqual(caught.exception.code, "ROUTE_UNRESOLVABLE")
        self.assertEqual(adapter.RouteResolver("proj", m2_lookup=lookup, allow_direct=True)
                         .resolve(req("direct:claude/haiku")).model, "haiku")
        self.assertEqual(adapter.RouteResolver("proj").resolve(req("direct:claude/haiku")).model, "haiku")

    def test_a_route_selected_for_another_plan_task_revision_or_expired_is_refused(self):
        base = {"provider": "claude", "model": "haiku", "profile": "claude-personal", "plan_id": "REQ-042",
                "revision": 1, "task_id": "T1", "plan_sha256": "a" * 64}
        for extra in ({"plan_id": "REQ-OTHER"}, {"task_id": "T99"}, {"revision": 9},
                      {"quota_valid_until": 1.0}):
            with self.subTest(extra=extra), self.assertRaises(m3.ExecutorError) as caught:
                adapter.RouteResolver("proj", m2_lookup=lambda ref, request, e=extra: {**base, **e}).resolve(req("route:x"))
            self.assertEqual(caught.exception.code, "ROUTE_INVALID")
        ok = adapter.RouteResolver("proj", m2_lookup=lambda ref, request: {
            **base, "quota_valid_until": time.time() + 3600
        }).resolve(req("route:x"))
        self.assertEqual(ok.model, "haiku")

    def test_missing_or_mismatched_approved_plan_hash_is_refused(self):
        base = {"provider": "claude", "model": "haiku", "profile": "claude-personal", "plan_id": "REQ-042",
                "revision": 1, "task_id": "T1", "quota_valid_until": time.time() + 3600}
        for found in ({**base}, {**base, "plan_sha256": "b" * 64}):
            with self.subTest(found_hash=found.get("plan_sha256")), self.assertRaises(m3.ExecutorError) as caught:
                adapter.RouteResolver("proj", m2_lookup=lambda ref, request, row=found: row).resolve(req("route:x"))
            self.assertEqual(caught.exception.code, "ROUTE_INVALID")
            self.assertIn("plan_sha256", caught.exception.detail)

    def test_the_account_m2_evaluated_must_still_be_the_account_the_profile_selects(self):
        route = m3.Route("claude", "haiku", "claude-personal", "", "route:x", account_ref="acct:" + "0" * 64)
        try:
            import bt_scheduler_decision  # noqa: F401
        except ImportError:
            self.skipTest("M2 not importable")
        with self.assertRaises(m3.ExecutorError) as caught:
            adapter.validate_route(route, "proj")
        self.assertIn("account behind this profile changed", caught.exception.detail)
        good = m3.Route("claude", "haiku", "claude-personal", "", "route:x",
                        account_ref=adapter.m2_account_ref("claude", "claude-personal"))
        adapter.validate_route(good, "proj")

    def test_launch_revalidates_the_route_it_waited_for(self):
        ws = m3.Workspace(path=str(self.tmp / "wt"), branch="m3/x", base_sha="0" * 40, repo=str(self.repos["app"]))
        Path(ws.path).mkdir()
        driver = adapter.MethodologyDriver("proj")
        route = m3.Route("claude", "haiku", "claude-personal", "")
        driver.prepare(route, "p", ws, 60)
        s.bt_profiles.add("claude-personal", "codex")                 # the profile now belongs to another provider
        with self.assertRaises(m3.ExecutorError) as caught:
            driver.prepare(route, "p", ws, 60)
        self.assertEqual(caught.exception.code, "ROUTE_INVALID")

    def test_a_profiles_own_token_variables_and_launcher_survive_the_credential_filter(self):
        wrapper = self.bin / "claude-wrapper"
        wrapper.write_text("#!/bin/sh\nexec claude \"$@\"\n")
        wrapper.chmod(0o755)
        s.bt_profiles.add("claude-token", "claude", {"CLAUDE_CONFIG_DIR": str(self.tmp / "tok")})
        spec = s.bt_profiles.load()["claude-token"]
        import json
        path = s.bt_profiles.STATE / "profiles.json"
        data = json.loads(path.read_text())
        data["claude-token"]["bin"] = "claude-wrapper"
        path.write_text(json.dumps(data))
        os.environ["ANTHROPIC_API_KEY"] = "inherited"
        self.addCleanup(os.environ.pop, "ANTHROPIC_API_KEY", None)
        ws = m3.Workspace(path=str(self.tmp / "wt2"), branch="m3/x", base_sha="0" * 40, repo=str(self.repos["app"]))
        Path(ws.path).mkdir()
        launch = adapter.MethodologyDriver("proj").prepare(m3.Route("claude", "haiku", "claude-token", ""), "p", ws, 60)
        self.assertEqual(Path(launch.argv[0]).name, "claude-wrapper")
        self.assertIn("ANTHROPIC_API_KEY", launch.env_remove)
        self.assertEqual(dict(launch.env_set)["CLAUDE_CONFIG_DIR"], str(self.tmp / "tok"))
        del spec

    def test_a_transient_executor_failure_is_raised_not_answered_with_a_rejection(self):
        class Flaky:
            def start(self, request):
                return m3.Receipt("rejected", "PORT_ERROR", "ledger of M2 unavailable")
        self.approve([s.task("T1", "x")])
        port = adapter.CoreExecutionPort(Flaky(), s.sched.approved_plan(self.rdir), project="proj")
        order = core.StartOrder("k", "REQ-042", 1, "T1", "att-0001", 1, "direct:claude/haiku")
        with self.assertRaises(RuntimeError):
            port.start(order)                                            # M1 records a port error and tries again
        class Final:
            def start(self, request):
                return m3.Receipt("rejected", "ROUTE_INVALID", "no")
        self.assertEqual(adapter.CoreExecutionPort(Final(), s.sched.approved_plan(self.rdir), project="proj")
                         .start(order).status, "rejected")

    def test_an_order_for_another_plan_revision_is_refused_by_the_port(self):
        self.approve([s.task("T1", "x")])
        port = adapter.CoreExecutionPort(object(), s.sched.approved_plan(self.rdir), project="proj")
        order = core.StartOrder("k", "REQ-042", 2, "T1", "att-0001", 1, "direct:claude/haiku")
        self.assertIn("another plan revision", port.start(order).detail)

    def test_a_new_core_run_of_the_same_requirement_gets_its_own_executor_root(self):
        self.approve([s.task("T1", "x")])
        first = self.wire("direct:claude/haiku")
        self.assertTrue(self.run_until(first, lambda snap: snap.status == "completed"))
        first.close()
        for name in ("SCHEDULER.db", "SCHEDULER.db-wal", "SCHEDULER.db-shm"):      # a NEW run of the same plan revision
            (self.rdir / name).unlink(missing_ok=True)
        second = self.wire("direct:claude/haiku", verifier=s.Verifier())
        self.assertNotEqual(first.executor.root, second.executor.root)
        self.assertTrue(self.run_until(second, lambda snap: snap.status == "completed"))
        self.assertEqual(len(self.records()), 2, "the second run reused the first run's finished attempt instead of running")

    def test_the_run_identity_changes_with_the_plan_revision(self):
        self.approve([s.task("T1", "x")])
        one = self.wire("direct:claude/haiku")
        a = adapter.run_identity(one.scheduler)
        one.close()
        for name in ("SCHEDULER.db", "SCHEDULER.db-wal", "SCHEDULER.db-shm"):
            (self.rdir / name).unlink(missing_ok=True)
        self.approve([s.task("T1", "x"), s.task("T2", "y")], revision=2)
        two = self.wire("direct:claude/haiku")
        self.assertNotEqual(a, adapter.run_identity(two.scheduler))
        self.assertIn("r2-", adapter.run_identity(two.scheduler))

    def test_a_workspace_is_a_valid_bt_worktree_candidate_not_only_a_scope_check(self):
        import bt_worktree
        ws = m3.GitWorkspaces(self.tmp / "root2", self.repos).allocate(req(attempt_id="att-0010"))
        (Path(ws.path) / "made.txt").write_text("x")
        allocation = adapter.worktree_allocation({"request": {"task_id": "T1"}, "workspace": ws.to_dict()})
        sha = bt_worktree.candidate(allocation)
        self.assertEqual(s.git(self.repos["app"], "show", f"{sha}:made.txt"), "x")


class QuotaFreshness(s.World):
    """A quota deadline must survive M2 persistence and be rechecked when M3 launches."""

    def make_selected_reference(self):
        import dataclasses

        import bt_scheduler_decision as m2
        from bt_scheduler_decision.tests.support import request as make_request
        from bt_scheduler_decision.tests.test_recorder import _record
        from scheduler_chain_support import real_candidate

        now = time.time()
        selected = real_candidate(provider="claude", model="sonnet", profile="claude-personal", effort="low",
                                  observed_at=now - 1, valid_until=now + 3600)
        asked = make_request(candidates=(selected,), requested_at=now)
        asked = dataclasses.replace(asked, plan_id="REQ-042", revision=1,
                                    task=dataclasses.replace(asked.task, task_id="T1"))
        self.ledger_path = self.tmp / "quota-decisions.db"
        ledger = m2.DecisionLedger(self.ledger_path)
        saved = ledger.persist(asked, _record(asked))
        return m2, saved, m2.executor_reference(saved.decision_id, selected.route_id)

    def test_selected_quota_deadline_survives_m2_ledger_and_resolves_into_m3_route(self):
        _, saved, reference = self.make_selected_reference()
        expected = saved.selected.quota_valid_until
        lookup = adapter.m2_ledger_lookup(self.ledger_path)
        found = lookup(reference, req(reference))
        self.assertEqual(found["quota_valid_until"], expected)
        route = adapter.RouteResolver("proj", m2_lookup=lookup).resolve(req(reference))
        self.assertEqual(route.quota_valid_until, expected)

    def test_missing_non_finite_and_expired_quota_deadlines_are_rejected(self):
        base = {"provider": "claude", "model": "haiku", "profile": "claude-personal", "plan_id": "REQ-042",
                "revision": 1, "task_id": "T1", "plan_sha256": "a" * 64}
        for expiry in (None, True, float("inf"), 1.0):
            found = {**base, "quota_valid_until": expiry}
            with self.subTest(expiry=expiry), self.assertRaises(m3.ExecutorError) as caught:
                adapter.RouteResolver("proj", m2_lookup=lambda ref, request, row=found: row).resolve(req("route:x"))
            self.assertEqual(caught.exception.code, "ROUTE_INVALID")

    def test_legacy_m2_record_without_quota_deadline_remains_readable_but_cannot_launch(self):
        m2, saved, reference = self.make_selected_reference()
        connection = sqlite3.connect(self.ledger_path)
        try:
            raw = json.loads(connection.execute("SELECT record_json FROM decision_records WHERE decision_id=?",
                                                 (saved.decision_id,)).fetchone()[0])
            raw["schema_version"] = "1.0.0"
            for field in ("quota_observed_at", "quota_used_percent", "quota_valid_until"):
                raw["selected"].pop(field)
            connection.execute("UPDATE decision_records SET record_json=? WHERE decision_id=?",
                               (json.dumps(raw, sort_keys=True, separators=(",", ":")), saved.decision_id))
            connection.commit()
        finally:
            connection.close()
        binding = m2.resolve_executor_binding(self.ledger_path, reference)
        self.assertIsNone(binding.route.quota_valid_until)
        with self.assertRaises(m3.ExecutorError) as caught:
            adapter.RouteResolver("proj", m2_lookup=adapter.m2_ledger_lookup(self.ledger_path)).resolve(req(reference))
        self.assertEqual(caught.exception.code, "ROUTE_INVALID")

    def test_quota_expiring_while_queued_is_rechecked_before_provider_launch(self):
        from unittest.mock import patch

        route = m3.Route("claude", "haiku", "claude-personal", "", "route:x",
                         account_ref=adapter.m2_account_ref("claude", "claude-personal"), single_use=True,
                         quota_valid_until=1.0)
        with patch("bt_scheduler_executor_adapter.time.time", return_value=0.0):
            adapter.validate_route(route, "proj")
        workspace = m3.Workspace(path=str(self.tmp / "expired-wt"), branch="m3/x", base_sha="0" * 40,
                                 repo=str(self.repos["app"]))
        Path(workspace.path).mkdir()
        with self.assertRaises(m3.ExecutorError) as caught:
            adapter.MethodologyDriver("proj").prepare(route, "p", workspace, 60)
        self.assertEqual(caught.exception.code, "ROUTE_INVALID")
        self.assertIn("expired quota evidence", caught.exception.detail)
