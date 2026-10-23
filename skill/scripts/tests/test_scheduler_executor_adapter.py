"""The adapter: route validation against the catalogue and profile policy, launch (argv/environment/gates) through the
existing drivers, brief from the frozen plan, and translation to the scheduler core's classes."""
from __future__ import annotations

import os
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bt_scheduler_executor as m3
import scheduler_executor_support as s
from scheduler_executor_support import adapter, core


def req(ref="direct:claude/sonnet#xhigh", **kw):
    base = {"idempotency_key": "k1", "plan_id": "REQ-042", "revision": 1, "task_id": "T1",
            "attempt_id": "att-0001", "token": 1, "executor": ref, "repository": "app", "project": "proj"}
    base.update(kw)
    return m3.StartRequest(**base)


class Resolver(s.World):
    def setUp(self):
        super().setUp()
        self.resolver = adapter.RouteResolver("proj")

    def resolve(self, ref, **kw):
        return self.resolver.resolve(req(ref, **kw))

    def refused(self, ref, code):
        with self.assertRaises(m3.ExecutorError) as caught:
            self.resolve(ref)
        self.assertEqual(caught.exception.code, code, caught.exception.detail)
        return caught.exception

    def test_each_provider_resolves_to_its_own_catalogue_model(self):
        self.assertEqual(self.resolve("direct:claude/sonnet#xhigh"), m3.Route("claude", "sonnet", "", "xhigh", "direct:claude/sonnet#xhigh"))
        self.assertEqual(self.resolve("direct:codex/gpt-6.1-sol#high").provider, "codex")
        self.assertEqual(self.resolve("direct:antigravity/gemini-3.8-flash-low").provider, "antigravity")

    def test_gemini_is_antigravity(self):
        route = self.resolve("direct:gemini/gemini-3.8-flash-low")
        self.assertEqual((route.provider, route.model), ("antigravity", "gemini-3.8-flash-low"))
        self.assertEqual(self.resolve("direct:agy/gemini-3.8-flash-medium").provider, "antigravity")

    def test_a_named_profile_of_the_right_provider_is_kept(self):
        self.assertEqual(self.resolve("direct:claude/opus@claude-personal#high").profile, "claude-personal")
        self.assertEqual(self.resolve("direct:codex/gpt-6-luna@codex-1#medium").profile, "codex-1")

    def test_anything_that_is_not_a_reference_is_unresolvable_never_defaulted(self):
        for ref in ("local", "", "claude", "direct:", "direct:claude", "direct:claude/", "route:abc", "plain text",
                    "direct:claude/sonnet@", "direct:CLAUDE/sonnet"):
            with self.subTest(ref=ref):
                ex = None
                try:
                    self.resolve(ref) if ref else self.resolver.resolve(req("x"))
                except m3.ExecutorError as error:
                    ex = error
                self.assertIsNotNone(ex)
                self.assertEqual(ex.code, "ROUTE_UNRESOLVABLE")

    def test_the_cores_fifo_label_local_never_runs(self):
        self.refused("local", "ROUTE_UNRESOLVABLE")

    def test_a_model_that_does_not_belong_to_the_provider_is_invalid(self):
        self.refused("direct:claude/gpt-6.1-sol", "ROUTE_INVALID")
        self.refused("direct:codex/sonnet", "ROUTE_INVALID")
        self.refused("direct:antigravity/opus", "ROUTE_INVALID")
        self.refused("direct:claude/totally-made-up", "ROUTE_INVALID")

    def test_an_unlaunchable_provider_is_invalid(self):
        self.refused("direct:mistral/large", "ROUTE_INVALID")

    def test_effort_rules(self):
        self.refused("direct:claude/sonnet#ludicrous", "ROUTE_INVALID")
        self.refused("direct:antigravity/gemini-3.8-flash-low#high", "ROUTE_INVALID")   # effort is part of the id
        self.resolve("direct:claude/haiku")                                              # effort optional

    def test_an_unknown_profile_or_one_of_another_provider_is_invalid(self):
        self.refused("direct:claude/sonnet@nobody", "ROUTE_INVALID")
        self.refused("direct:claude/sonnet@codex-1", "ROUTE_INVALID")

    def test_a_work_only_profile_is_refused_for_a_project_not_marked_work(self):
        self.refused("direct:claude/sonnet@claude-work", "POLICY_DENIED")
        work = adapter.RouteResolver("workproj")
        self.assertEqual(work.resolve(req("direct:claude/sonnet@claude-work")).profile, "claude-work")

    def test_the_ambient_account_needs_its_executable(self):
        os.environ["PATH"] = str(self.tmp / "nowhere")
        self.refused("direct:claude/sonnet", "POLICY_DENIED")

    def test_route_references_go_to_the_m2_lookup_when_there_is_one(self):
        plan_sha256 = "a" * 64
        found = {"route:r1": {"provider": "codex", "model": "gpt-6-luna", "profile": "codex-1",
                              "effort": "medium", "plan_id": "REQ-042", "revision": 1, "task_id": "T1",
                              "plan_sha256": plan_sha256, "quota_valid_until": time.time() + 3600}}
        resolver = adapter.RouteResolver("proj", m2_lookup=lambda ref, request: found.get(ref))
        route = resolver.resolve(req("route:r1", plan_sha256=plan_sha256))
        self.assertEqual((route.provider, route.model, route.profile, route.reference), ("codex", "gpt-6-luna", "codex-1", "route:r1"))
        self.assertGreater(route.quota_valid_until, time.time())
        with self.assertRaises(m3.ExecutorError) as caught:
            resolver.resolve(req("route:unknown"))
        self.assertEqual(caught.exception.code, "ROUTE_UNRESOLVABLE")

    def test_an_m2_answer_is_validated_as_hard_as_a_direct_reference(self):
        plan_sha256 = "b" * 64
        bad = {"route:r2": {"provider": "claude", "model": "gpt-6.1-sol",
                            "plan_id": "REQ-042", "revision": 1, "task_id": "T1",
                            "plan_sha256": plan_sha256, "quota_valid_until": time.time() + 3600}}
        with self.assertRaises(m3.ExecutorError) as caught:
            adapter.RouteResolver("proj", m2_lookup=lambda ref, request: bad.get(ref)).resolve(
                req("route:r2", plan_sha256=plan_sha256))
        self.assertEqual(caught.exception.code, "ROUTE_INVALID")

    def test_no_model_name_is_hardcoded_in_the_adapter(self):
        text = (Path(adapter.__file__)).read_text()
        for model in ("sonnet", "opus", "haiku", "gpt-6", "gemini-3"):
            self.assertNotIn(model, text.replace("claude-personal", ""), model)


class Gates(s.World):
    def test_the_work_only_gate_refuses_before_any_worktree_exists(self):
        work_repo = s.make_repo(self.root / "workproj" / "repo")
        resolver = adapter.RouteResolver("workproj", repos=lambda role: work_repo if role == "app" else None)
        route = resolver.resolve(req("direct:claude/sonnet@claude-work#low", project="workproj"))       # repo inside a work project
        self.assertEqual(route.profile, "claude-work")
        outside = adapter.RouteResolver("workproj", repos=lambda role: self.repos["app"])               # repo outside any project
        with self.assertRaises(m3.ExecutorError) as caught:
            outside.resolve(req("direct:claude/sonnet@claude-work#low", project="workproj"))
        self.assertEqual(caught.exception.code, "POLICY_DENIED")

    def test_effort_is_checked_per_provider(self):
        resolver = adapter.RouteResolver("proj")
        resolver.resolve(req("direct:claude/opus#max"))
        with self.assertRaises(m3.ExecutorError) as caught:
            resolver.resolve(req("direct:codex/gpt-6.1-sol#max"))
        self.assertEqual(caught.exception.code, "ROUTE_INVALID")
        resolver.resolve(req("direct:codex/gpt-6.1-sol#xhigh"))

    def test_the_child_environment_drops_parent_session_state_and_foreign_credentials(self):
        os.environ.update({"CLAUDECODE": "1", "CLAUDE_CODE_ENTRYPOINT": "cli", "CODEX_THREAD_ID": "t", "ANTHROPIC_API_KEY": "sk-x",
                           "OPENAI_API_KEY": "sk-y"})
        for name in ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "CODEX_THREAD_ID", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
            self.addCleanup(os.environ.pop, name, None)
        ws = m3.Workspace(path=str(self.tmp / "wt"), branch="m3/x", base_sha="0" * 40, repo=str(self.repos["app"]))
        Path(ws.path).mkdir()
        driver = adapter.MethodologyDriver("proj")
        with_profile = driver.prepare(m3.Route("claude", "haiku", "claude-personal", ""), "p", ws, 60)
        for name in ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "CODEX_THREAD_ID", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
            self.assertIn(name, with_profile.env_remove, name)
        ambient = driver.prepare(m3.Route("claude", "haiku", "", ""), "p", ws, 60)
        self.assertIn("CLAUDECODE", ambient.env_remove)
        self.assertNotIn("ANTHROPIC_API_KEY", ambient.env_remove)                 # the inherited account is the ambient route's own


class Driver(s.World):
    def prepare(self, route, workdir=None, project="proj", repo=None):
        ws = m3.Workspace(path=str(workdir or self.tmp / "wt"), branch="m3/x", base_sha="0" * 40,
                          repo=str(repo or self.repos["app"]))
        Path(ws.path).mkdir(parents=True, exist_ok=True)
        return adapter.MethodologyDriver(project).prepare(route, "PROMPT SCENARIO:ok", ws, 120)

    def test_claude_gets_its_model_effort_and_profile_account(self):
        launch = self.prepare(m3.Route("claude", "sonnet", "claude-personal", "xhigh"))
        argv = list(launch.argv)
        self.assertEqual(argv[1], "-p")
        self.assertEqual(argv[argv.index("--model") + 1], "sonnet")
        self.assertEqual(argv[argv.index("--effort") + 1], "xhigh")
        self.assertIn("--output-format", argv)
        env = dict(launch.env_set)
        self.assertEqual(env["CLAUDE_CONFIG_DIR"], str(self.tmp / "claude-a"))

    def test_a_profile_replaces_the_inherited_account_of_every_provider(self):
        launch = self.prepare(m3.Route("claude", "sonnet", "claude-personal", "low"))
        self.assertIn("CODEX_HOME", launch.env_remove)               # the inherited Codex account does not leak down
        self.assertEqual(dict(launch.env_set)["CLAUDE_CONFIG_DIR"], str(self.tmp / "claude-a"))

    def test_codex_gets_the_worktree_the_model_and_the_effort_and_reads_the_prompt_from_stdin(self):
        wt = self.tmp / "wt-codex"
        launch = self.prepare(m3.Route("codex", "gpt-6.1-sol", "codex-1", "high"), workdir=wt)
        argv = list(launch.argv)
        self.assertEqual(argv[1], "exec")
        self.assertEqual(argv[argv.index("-C") + 1], str(wt))
        self.assertEqual(argv[argv.index("-m") + 1], "gpt-6.1-sol")
        self.assertIn('model_reasoning_effort="high"', argv)
        self.assertEqual(launch.stdin, "PROMPT SCENARIO:ok")
        self.assertEqual(dict(launch.env_set)["CODEX_HOME"], str(self.tmp / "codex-1"))
        self.assertIn("CLAUDE_CONFIG_DIR", launch.env_remove)

    def test_gemini_runs_through_agy_with_the_effort_inside_the_model_id(self):
        launch = self.prepare(m3.Route("antigravity", "gemini-3.8-flash-medium", "", ""))
        argv = list(launch.argv)
        self.assertEqual(Path(argv[0]).name, "agy")
        self.assertEqual(argv[argv.index("--model") + 1], "gemini-3.8-flash-medium")
        self.assertNotIn("--effort", argv)
        self.assertTrue(any(a.startswith("--print=PROMPT") for a in argv))
        self.assertIn("--print-timeout", argv)

    def test_the_ambient_account_is_used_unchanged_when_no_profile_is_named(self):
        launch = self.prepare(m3.Route("claude", "haiku", "", ""))
        self.assertEqual(launch.env_set, ())
        self.assertNotIn("CLAUDE_CONFIG_DIR", launch.env_remove)

    def test_work_only_profiles_are_gated_by_the_projects_repository_not_the_worktree(self):
        work_repo = s.make_repo(self.root / "workproj" / "repo")
        ws = self.tmp / "elsewhere" / "wt"                         # a worktree far from any registered project
        launch = self.prepare(m3.Route("claude", "sonnet", "claude-work", "low"), workdir=ws, project="workproj", repo=work_repo)
        self.assertTrue(launch.argv)
        with self.assertRaises(m3.ExecutorError) as caught:
            self.prepare(m3.Route("claude", "sonnet", "claude-work", "low"), project="proj")
        self.assertEqual(caught.exception.code, "POLICY_DENIED")
        with self.assertRaises(m3.ExecutorError) as caught:         # work project, but the repository is outside any project
            self.prepare(m3.Route("claude", "sonnet", "claude-work", "low"), project="workproj")
        self.assertEqual(caught.exception.code, "POLICY_DENIED")

    def test_the_provider_binary_is_found_by_path_at_launch_time(self):
        launch = self.prepare(m3.Route("claude", "haiku", "", ""))
        self.assertEqual(Path(launch.argv[0]).parent, self.bin)

    def test_classification_uses_the_real_normalisers(self):
        driver = adapter.MethodologyDriver("proj")
        claude = m3.Route("claude", "sonnet")
        ok = '{"type":"result","subtype":"success","is_error":false,"result":"done","total_cost_usd":0.5,"usage":{"input_tokens":1}}'
        cls = driver.classify(claude, ok, 0)
        self.assertEqual((cls.status, cls.terminal_event, cls.cost_usd), ("completed", True, 0.5))
        limit = '{"type":"result","is_error":true,"result":"Claude AI usage limit reached|1900000000"}'
        cls = driver.classify(claude, limit, 1)
        self.assertEqual((cls.status, cls.reset_epoch), ("limit", 1900000000))
        self.assertEqual(driver.classify(claude, "no result event", 0).status, "partial")
        codex = m3.Route("codex", "gpt-6-luna")
        self.assertEqual(driver.classify(codex, "hi\ntokens used\n1,234", 0).status, "completed")
        self.assertEqual(driver.classify(codex, "hi\ntokens used\n1,234", 0).usage, {"total_tokens": 1234})
        agy = m3.Route("antigravity", "gemini-3.8-flash-low")
        done = '{"event":"result","result":{"status":"SUCCESS","response":"ok"}}'
        self.assertEqual(driver.classify(agy, done, 0).status, "completed")
        self.assertEqual(driver.classify(claude, "", None, timed_out=True).status, "timeout")


class Brief(s.World):
    def test_the_brief_is_the_frozen_plans_task(self):
        self.approve([s.task("T1", "Build it", scenario="ok")])
        plan = s.sched.approved_plan(self.rdir)
        brief = adapter.PlanBriefs(plan).brief(req(task_id="T1"))
        self.assertEqual(brief.title, "Build it SCENARIO:ok")
        self.assertEqual(brief.objective, "do T1")
        self.assertEqual(brief.acceptance_criteria, ("T1 works",))
        self.assertEqual(brief.verification, ("smoke: true",))
        self.assertEqual(brief.expected_paths, ("T1/**",))

    def test_a_task_that_is_not_in_the_plan_is_refused(self):
        self.approve([s.task("T1", "x")])
        with self.assertRaises(m3.ExecutorError) as caught:
            adapter.PlanBriefs(s.sched.approved_plan(self.rdir)).brief(req(task_id="T99"))
        self.assertEqual(caught.exception.code, "ORDER_INVALID")


class Translation(s.World):
    def setUp(self):
        super().setUp()
        self.approve([s.task("T1", "x"), s.task("T2", "y", repo="docs")])
        self.plan = s.sched.approved_plan(self.rdir)

    class FakeExecutor:
        def __init__(self):
            self.started, self.cancelled, self.answer = [], [], m3.Receipt("accepted")
            self.status = m3.AttemptStatus("queued")

        def start(self, request):
            self.started.append(request)
            return self.answer

        def cancel(self, attempt_id, token, key, reason=""):
            self.cancelled.append((attempt_id, token, key, reason))
            return self.answer

        def query(self, attempt_id):
            return self.status

    def port(self, **kw):
        self.fake = self.FakeExecutor()
        return adapter.CoreExecutionPort(self.fake, self.plan, project="proj", **kw)

    def test_a_query_before_the_executor_is_composed_is_not_ready_rather_than_an_attribute_error(self):
        port = adapter.CoreExecutionPort(None, self.plan, project="proj")
        with self.assertRaises(core.PortNotReady):
            port.query("att-0001")

    def order(self, **kw):
        base = {"idempotency_key": "REQ-042:r1:att-0001:start", "plan_id": "REQ-042", "revision": 1,
                "task_id": "T1", "attempt_id": "att-0001", "token": 7, "executor": "direct:claude/sonnet",
                "acceptance_criteria": ("a",), "verification": ({"type": "command", "value": "true"},)}
        base.update(kw)
        return core.StartOrder(**base)

    def test_a_start_order_becomes_a_request_with_the_tasks_repository_and_the_answer_is_the_cores_ack(self):
        ack = self.port().start(self.order(task_id="T2"))
        self.assertIsInstance(ack, core.Ack)
        self.assertEqual(ack.status, "accepted")
        request = self.fake.started[0]
        self.assertEqual((request.repository, request.project, request.token, request.executor),
                         ("docs", "proj", 7, "direct:claude/sonnet"))

    def test_accepted_attempts_are_reported_to_the_runtime_stream_tracker(self):
        tracked = []
        port = self.port()
        port.on_accepted_attempt = tracked.append

        self.assertEqual(port.start(self.order()).status, "accepted")

        self.assertEqual(tracked, ["att-0001"])

    def test_rejections_keep_their_code_in_the_acks_detail(self):
        port = self.port()
        self.fake.answer = m3.Receipt("rejected", "ROUTE_INVALID", "bad model")
        ack = port.start(self.order())
        self.assertEqual((ack.status, ack.detail), ("rejected", "ROUTE_INVALID: bad model"))

    def test_an_unknown_task_or_a_task_without_a_repository_is_rejected_by_the_adapter(self):
        self.assertEqual(self.port().start(self.order(task_id="T9")).status, "rejected")
        self.approve([{**s.task("T1", "x"), "repository": ""}], revision=2)
        plan = s.sched.approved_plan(self.rdir)
        port = adapter.CoreExecutionPort(self.FakeExecutor(), plan, project="proj")
        self.assertIn("REPOSITORY_UNKNOWN", port.start(self.order(revision=2)).detail)
        port = adapter.CoreExecutionPort(self.FakeExecutor(), plan, project="proj", default_repository="app")
        self.assertEqual(port.start(self.order(revision=2)).status, "accepted")

    def test_cancel_is_fenced_by_the_cores_token(self):
        port = self.port()
        ack = port.cancel(core.CancelOrder("k", "att-0001", 7, "stop"))
        self.assertEqual(ack.status, "accepted")
        self.assertEqual(self.fake.cancelled, [("att-0001", 7, "k", "stop")])

    def test_query_maps_the_modules_states_to_the_cores_vocabulary(self):
        port = self.port()
        expected = {"queued": "running", "preparing": "running", "running": "running", "settling": "running",
                    "finished": "finished", "failed": "failed", "cancelled": "cancelled", "not_found": "not_found"}
        for state, wanted in expected.items():
            self.fake.status = m3.AttemptStatus(state)
            status = port.query("att-0001")
            self.assertIsInstance(status, core.ExecutionStatus)
            self.assertEqual(status.state, wanted)
            self.assertIn(status.state, core.contracts.EXEC_STATES)

    def test_events_enter_the_core_as_its_own_events_with_a_reason_for_failures(self):
        seen = []

        class Scheduler:
            def ingest(self, event):
                seen.append(event)
                return core.IngestResult("applied")
        sink = adapter.CoreEventSink(Scheduler())
        sink.deliver(m3.TechnicalEvent("a:failed", "execution_failed", "REQ-042", 1, "T1", "att-0001", 7, "t",
                                       {"cause": "quota_exhausted", "detail": "limit", "reset_epoch": 1}))
        sink.deliver(m3.TechnicalEvent("a:hb:1", "heartbeat", "REQ-042", 1, "T1", "att-0001", 7, "t", {"seq": 1}))
        self.assertTrue(all(isinstance(e, core.Event) for e in seen))
        self.assertEqual(seen[0].payload["reason"], "quota_exhausted: limit")
        self.assertEqual((seen[0].source, seen[0].token, seen[0].kind), ("executor", 7, "execution_failed"))

    def test_an_unbound_sink_leaves_events_in_the_outbox_and_an_invalid_one_is_dropped_not_stuck(self):
        with self.assertRaises(RuntimeError):
            adapter.CoreEventSink().deliver(m3.TechnicalEvent("a", "heartbeat", "P", 1, "T", "a", 1, "t"))

        class Rejecting:
            def ingest(self, event):
                return core.IngestResult("invalid", "unknown_attempt")
        sink = adapter.CoreEventSink(Rejecting())
        sink.deliver(m3.TechnicalEvent("a", "execution_started", "P", 1, "T", "a", 1, "t"))
        self.assertEqual(sink.dropped, ["a: unknown_attempt"])

    def test_the_pinned_route_assignment_respects_free_slots_and_is_labelled_as_the_operators(self):
        views = tuple(core.TaskView(f"T{i}", "M1", "app", (), (), 0) for i in range(4))
        request = core.AssignmentRequest("REQ-042", 1, views, 2, 0.0)
        out = adapter.PinnedRoute("direct:claude/haiku").propose(request)
        self.assertEqual([(a.task_id, a.executor) for a in out], [("T0", "direct:claude/haiku"), ("T1", "direct:claude/haiku")])
        self.assertIn("operator", out[0].note)

    def test_a_workspace_is_exposed_in_the_shape_bt_worktree_consumes(self):
        import bt_worktree
        ws = m3.GitWorkspaces(self.tmp / "root", self.repos).allocate(req(attempt_id="att-0009"))
        allocation = adapter.worktree_allocation({"request": {"task_id": "T1"}, "workspace": ws.to_dict()})
        (Path(ws.path) / "inside.txt").write_text("x")
        self.assertEqual(bt_worktree.check_scope(allocation, ["inside.txt"])["status"], "parallel")
        with self.assertRaises(bt_worktree.WorktreeError):
            (Path(ws.path) / "outside.txt").write_text("x")
            bt_worktree.check_scope(allocation, ["inside.txt"])


class Layout(s.World):
    def test_the_executor_root_sits_next_to_the_schedulers_database(self):
        layout = self.tmp / "bitacora" / "proj" / "requirements" / "REQ-042-x"
        layout.mkdir(parents=True)
        self.assertEqual(adapter.executor_root(layout), self.tmp / "bitacora" / ".state" / "executor" / "proj-REQ-042")
        self.assertEqual(adapter.executor_root(self.rdir), self.rdir / "EXECUTOR")


class AcceptedAttemptAfterWithdrawnRework(unittest.TestCase):
    def test_a_completed_task_reports_its_accepted_attempt_not_the_failed_redo_after_it(self):
        """REQ-020 T14a: rework + withdraw left att-0101 (a start the integrator rejected) after the accepted att-0097; T15 then asked for
        the snapshot of att-0101 (PREDECESSOR_HANDOFF_MISSING)."""
        from types import SimpleNamespace

        from bt_scheduler_executor_adapter import _accepted_attempts

        attempts = {"a1": SimpleNamespace(state="accepted"), "a2": SimpleNamespace(state="failed"), "b1": SimpleNamespace(state="accepted"),
                    "c1": SimpleNamespace(state="running")}
        tasks = {"A": SimpleNamespace(state="completed", attempts=["a1", "a2"]), "B": SimpleNamespace(state="completed", attempts=["b1"]),
                 "C": SimpleNamespace(state="active", attempts=["c1"])}
        scheduler = SimpleNamespace(read=lambda fn: fn(SimpleNamespace(state=SimpleNamespace(tasks=tasks, attempts=attempts))))
        self.assertEqual(_accepted_attempts(scheduler), {"A": "a1", "B": "b1"})


if __name__ == "__main__":
    unittest.main()
