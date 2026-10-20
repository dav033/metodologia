"""M1 + M3 together: a whole plan through the real scheduler core and the real executor, with the methodology's own
provider drivers running against fake provider binaries. The independent verifier is a stub: only it completes tasks."""
from __future__ import annotations

import ast
import hashlib
import json
import os
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scheduler_executor_support as s
from scheduler_executor_support import adapter, core


class TaskRoutes:
    """Per-task route references: a test stand-in for M2 (the adapter's PinnedRoute pins one reference for all)."""

    def __init__(self, routes, default="direct:claude/haiku"):
        self.routes, self.default = routes, default

    def propose(self, request):
        return [core.Assignment(t.id, self.routes.get(t.id, self.default), "test route") for t in request.ready[:request.free_slots]]


class Capture:
    """A RecoveryPort that records what M3/M1 told it about each failure and always says: block."""

    def __init__(self):
        self.contexts = []

    def propose(self, context):
        self.contexts.append(context)
        return core.RecoveryProposal("block", "test recovery")


def task_state(wiring, tid):
    return wiring.scheduler.snapshot().tasks[tid]["state"]


class Plan(s.World):
    def wire_routes(self, routes, **kw):
        w = self.wire("unused", **kw)
        w.scheduler.ports.assignment = TaskRoutes(routes)
        return w

    def test_a_parallel_plan_over_three_providers_completes_only_through_the_independent_verifier(self):
        self.approve([s.task("T1", "claude work"), s.task("T2", "codex work"), s.task("T3", "gemini work"),
                      s.task("T4", "join", after=["T1", "T2", "T3"]), s.task("T5", "docs", repo="docs"),
                      s.task("T6", "docs more", after=["T5"], repo="docs")])
        w = self.wire_routes({"T1": "direct:claude/sonnet@claude-personal#low", "T2": "direct:codex/gpt-6-luna@codex-1#medium",
                              "T3": "direct:gemini/gemini-3.8-flash-low", "T4": "direct:claude/haiku",
                              "T5": "direct:codex/gpt-6-luna#low", "T6": "direct:claude/haiku"}, parallel=3)
        self.assertTrue(self.run_until(w, lambda snap: snap.status == "completed"), w.scheduler.snapshot())
        snap = w.scheduler.snapshot()
        self.assertEqual({t: v["state"] for t, v in snap.tasks.items()}, {f"T{i}": "completed" for i in range(1, 7)})
        for v in snap.tasks.values():
            self.assertEqual(v["evidence"], "stub verification passed")
        providers = sorted(r["provider"] for r in self.records())
        self.assertEqual(providers, ["agy", "claude", "claude", "claude", "codex", "codex"])
        by_cwd = {r["cwd"] for r in self.records()}
        self.assertEqual(len(by_cwd), 6, "two attempts shared a directory")
        self.assertTrue(all("worktrees" in cwd for cwd in by_cwd))
        self.assertEqual(sorted(o.task_id for o in self.verifier.orders), [f"T{i}" for i in range(1, 7)])

    def test_each_agent_got_exactly_the_model_effort_profile_and_worktree_it_was_assigned(self):
        self.approve([s.task("T1", "a"), s.task("T2", "b"), s.task("T3", "c")])
        w = self.wire_routes({"T1": "direct:claude/sonnet@claude-personal#low", "T2": "direct:codex/gpt-6.1-sol@codex-1#high",
                              "T3": "direct:gemini/gemini-3.8-flash-medium"})
        self.assertTrue(self.run_until(w, lambda snap: snap.status == "completed"))
        by = {r["provider"]: r for r in self.records()}
        claude, codex, agy = by["claude"], by["codex"], by["agy"]
        self.assertEqual(claude["argv"][claude["argv"].index("--model") + 1], "sonnet")
        self.assertEqual(claude["argv"][claude["argv"].index("--effort") + 1], "low")
        self.assertEqual(claude["env"]["CLAUDE_CONFIG_DIR"], str(self.tmp / "claude-a"))
        self.assertIsNone(claude["env"]["CODEX_HOME"])                      # another provider's account is not inherited
        self.assertEqual(codex["argv"][codex["argv"].index("-m") + 1], "gpt-6.1-sol")
        self.assertIn('model_reasoning_effort="high"', codex["argv"])
        self.assertEqual(codex["env"]["CODEX_HOME"], str(self.tmp / "codex-1"))
        self.assertGreater(codex["stdin_bytes"], 100)                       # the prompt came through stdin
        self.assertEqual(agy["argv"][agy["argv"].index("--model") + 1], "gemini-3.8-flash-medium")
        for r in by.values():                                               # variables no account owns are inherited as they were
            self.assertEqual(r["env"]["OTHER_SECRET"], "leak-me")

    def test_the_agents_work_is_preserved_in_its_own_branch_and_never_in_the_main_checkout(self):
        self.approve([s.task("T1", "commit one", scenario="commit"), s.task("T2", "dirty one", scenario="dirty")])
        w = self.wire_routes({"T1": "direct:claude/haiku", "T2": "direct:codex/gpt-6-luna#low"})
        self.assertTrue(self.run_until(w, lambda snap: snap.status == "completed"))
        self.assertEqual(s.git(self.repos["app"], "status", "--porcelain"), "")
        self.assertEqual((self.repos["app"] / "README.md").read_text(), "original\n")
        rows = {r["request"]["task_id"]: r for r in (w.executor.ledger.get(a) for a in w.executor.ledger.all_ids())}
        self.assertEqual(rows["T1"]["handoff"]["commit_count"], 1)
        self.assertFalse(rows["T1"]["handoff"]["dirty"])
        self.assertTrue(rows["T2"]["handoff"]["dirty"])
        self.assertFalse(rows["T2"]["handoff"]["has_commits"])
        self.assertEqual(s.git(self.repos["app"], "show", rows["T2"]["handoff"]["snapshot_sha"] + ":README.md"), "changed by agent")

    def test_an_agent_that_says_it_finished_is_not_a_completed_task_until_the_verifier_says_so(self):
        self.approve([s.task("T1", "work")])
        silent = s.Verifier()
        silent.request = lambda order: core.Ack("accepted")               # a verifier that never answers
        w = self.wire_routes({"T1": "direct:claude/haiku"}, verifier=silent)
        self.assertTrue(self.run_until(w, lambda snap: snap.tasks["T1"]["state"] == "active"
                                       and w.executor.ledger.count(("finished",)) == 1))
        w.scheduler.step()
        self.assertNotEqual(task_state(w, "T1"), "completed")
        self.assertEqual(w.scheduler.snapshot().status, "running")

    def test_a_rejecting_verifier_blocks_the_task_with_its_evidence(self):
        self.approve([s.task("T1", "work"), s.task("T2", "other")])
        w = self.wire_routes({}, verifier=s.Verifier(accept=False))
        self.assertTrue(self.run_until(w, lambda snap: snap.status == "blocked"))
        self.assertEqual({t: v["state"] for t, v in w.scheduler.snapshot().tasks.items()}, {"T1": "blocked", "T2": "blocked"})

    def test_quota_exhaustion_blocks_only_that_branch_and_keeps_the_half_done_work(self):
        self.approve([s.task("T1", "hits the limit", scenario="quota"), s.task("T2", "depends", after=["T1"]),
                      s.task("T3", "independent")])
        recovery = Capture()
        w = self.wire_routes({"T1": "direct:claude/sonnet#low"}, recovery=recovery)
        self.assertTrue(self.run_until(w, lambda snap: snap.status == "blocked"))
        snap = w.scheduler.snapshot()
        self.assertEqual(snap.tasks["T3"]["state"], "completed")
        self.assertEqual(snap.tasks["T1"]["state"], "blocked")
        self.assertTrue(snap.tasks["T2"]["unreachable"])
        attempt = next(a for a in w.executor.ledger.all_ids() if w.executor.ledger.get(a)["request"]["task_id"] == "T1")
        row = w.executor.ledger.get(attempt)
        self.assertEqual((row["outcome"]["cause"], row["outcome"]["reset_epoch"]), ("quota_exhausted", 1900000000))
        self.assertTrue(row["handoff"]["dirty"])
        self.assertTrue((Path(row["handoff"]["worktree"]) / "claude-half.txt").exists())
        self.assertEqual(len(recovery.contexts), 1)
        self.assertEqual(recovery.contexts[0].cause, "execution_failed")
        self.assertIn("quota_exhausted", recovery.contexts[0].detail)       # what M5 will read: the cause class, as a fact

    def test_connection_loss_and_plain_errors_are_told_apart_in_the_cores_failure_reason(self):
        self.approve([s.task("T1", "net", scenario="net"), s.task("T2", "crash", scenario="crash")])
        recovery = Capture()
        w = self.wire_routes({"T1": "direct:codex/gpt-6-luna#low", "T2": "direct:gemini/gemini-3.8-flash-low"},
                             recovery=recovery)
        self.assertTrue(self.run_until(w, lambda snap: snap.status == "blocked"))
        details = {c.task_id: c.detail for c in recovery.contexts}
        self.assertIn("connection_lost", details["T1"])
        self.assertIn("agent_error", details["T2"])

    def test_an_unresolvable_assignment_fails_the_attempt_without_starting_anything(self):
        self.approve([s.task("T1", "x")])
        w = self.wire("unused")
        w.scheduler.ports.assignment = core.FifoAssignment()                 # the core's own FIFO assigns the label "local"
        self.assertTrue(self.run_until(w, lambda snap: snap.status == "blocked"))
        self.assertEqual(self.records(), [])
        self.assertEqual(w.executor.ledger.get("att-0001")["state"], "rejected")
        self.assertEqual(w.executor.ledger.get("att-0001")["rejection"]["code"], "ROUTE_UNRESOLVABLE")

    def test_a_model_that_does_not_fit_its_provider_never_starts_a_process(self):
        self.approve([s.task("T1", "x")])
        w = self.wire("direct:claude/gpt-6.1-sol")
        self.assertTrue(self.run_until(w, lambda snap: snap.status == "blocked"))
        self.assertEqual(self.records(), [])

    def test_a_work_only_profile_cannot_run_a_personal_project(self):
        self.approve([s.task("T1", "x")])
        w = self.wire("direct:claude/sonnet@claude-work#low", project="proj")
        self.assertTrue(self.run_until(w, lambda snap: snap.status == "blocked"))
        self.assertEqual(self.records(), [])
        self.assertEqual(w.executor.ledger.get("att-0001")["rejection"]["code"], "POLICY_DENIED")


class Operations(s.World):
    def test_cancelling_the_run_stops_the_running_agents_and_preserves_their_work(self):
        self.approve([s.task("T1", "long", scenario="sleep"), s.task("T2", "long too", scenario="sleep", repo="docs")])
        w = self.wire("direct:claude/haiku")
        self.assertTrue(self.run_until(w, lambda snap: all(v["state"] == "active" for v in snap.tasks.values())
                                       and len(self.records()) == 2))
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline and not all((Path(w.executor.ledger.get(a)["workspace"]["path"]) / "claude-started.txt").exists()
                                                      for a in w.executor.ledger.all_ids()):
            time.sleep(0.05)
        w.scheduler.cancel("operator")
        self.assertTrue(self.run_until(w, lambda snap: snap.status == "cancelled", 60), w.scheduler.snapshot())
        for attempt in w.executor.ledger.all_ids():
            row = w.executor.ledger.get(attempt)
            self.assertEqual(row["state"], "cancelled")
            self.assertTrue(row["handoff"]["dirty"])
            self.assertTrue((Path(row["handoff"]["worktree"]) / "claude-started.txt").exists())
        self.assertTrue(w.executor.wait_idle(30))
        self.assertEqual(w.executor.ledger.count(("running", "preparing", "queued", "settling")), 0)

    def test_an_executor_restart_in_the_middle_of_a_run_loses_nothing_and_starts_nothing_twice(self):
        self.approve([s.task("T1", "slow", scenario="ok"), s.task("T2", "after", after=["T1"])])
        os.environ["FAKE_DELAY"] = "1.5"
        self.addCleanup(os.environ.pop, "FAKE_DELAY", None)
        w = self.wire("direct:claude/haiku")
        self.assertTrue(self.run_until(w, lambda snap: snap.tasks["T1"]["state"] == "active"
                                       and w.executor.ledger.count(("running",)) == 1))
        w.close()                                                            # supervision dies; the agent lives on
        verifier = s.Verifier()
        w2 = self.wire("direct:claude/haiku", verifier=verifier)
        self.assertTrue(self.run_until(w2, lambda snap: snap.status == "completed", 90), w2.scheduler.snapshot())
        self.assertEqual(sorted(r["scenario"] for r in self.records()), ["ok", "ok"])        # two tasks, two runs, no duplicate
        self.assertEqual(len({r["cwd"] for r in self.records()}), 2)

    def test_the_core_and_the_executor_agree_on_every_attempt_at_the_end(self):
        self.approve([s.task("T1", "a"), s.task("T2", "b", scenario="crash"), s.task("T3", "c", after=["T1"])])
        w = self.wire("direct:claude/haiku", max_attempts=2)
        self.assertTrue(self.run_until(w, lambda snap: snap.status == "blocked", 90))
        trail = w.scheduler.audit_log()
        attempts = {e.attempt_id for e in trail if e.attempt_id}
        for attempt in attempts:
            row = w.executor.ledger.get(attempt)
            self.assertIsNotNone(row, f"the core knows {attempt} but the executor does not")
            self.assertIn(row["state"], ("finished", "failed", "rejected", "cancelled"))
        self.assertEqual(sorted(w.executor.ledger.all_ids()), sorted(attempts))

    def test_a_legacy_requirement_is_not_taken_over_and_its_run_json_is_untouched(self):
        self.approve([s.task("T1", "x")])
        legacy = self.rdir / "RUN.json"
        legacy.write_text(json.dumps({"req": "REQ-042", "status": "running", "tasks": []}))
        before = hashlib.sha256(legacy.read_bytes()).hexdigest()
        with self.assertRaises(core.SchedulerError) as caught:
            self.wire("direct:claude/haiku")
        self.assertEqual(caught.exception.code, "NOT_ALLOWED")
        self.assertEqual(hashlib.sha256(legacy.read_bytes()).hexdigest(), before)
        self.assertEqual(self.records(), [])

    def test_a_task_in_a_repository_that_is_not_registered_is_rejected_before_any_worktree(self):
        self.approve([s.task("T1", "x", repo="ghost")])
        w = self.wire("direct:claude/haiku")
        self.assertTrue(self.run_until(w, lambda snap: snap.status == "blocked"))
        self.assertEqual(w.executor.ledger.get("att-0001")["rejection"]["code"], "REPOSITORY_UNKNOWN")
        self.assertEqual(self.records(), [])

    def test_no_secret_value_appears_in_the_executors_state_or_in_the_cores_audit(self):
        self.approve([s.task("T1", "x")])
        w = self.wire("direct:claude/sonnet@claude-personal#low")
        self.assertTrue(self.run_until(w, lambda snap: snap.status == "completed"))
        blob = json.dumps(w.scheduler.audit_log(), default=str)
        for path in (self.tmp / "REQ-042-demo").rglob("*"):
            if path.is_file() and path.suffix in (".json", ".db", ".log", ".txt", ".jsonl") and "worktrees" not in path.parts:
                blob += path.read_bytes().decode("utf-8", "replace")
        self.assertNotIn("leak-me", blob)


REPO = Path(__file__).resolve().parents[3]
MODULE = "bt_scheduler_executor"


class Boundary(unittest.TestCase):
    ALLOWED = frozenset({"bt_scheduler_executor_adapter.py", "test_scheduler_executor_integration.py",
                         "test_scheduler_executor_adapter.py", "scheduler_executor_support.py", "test_package_install.py",
                         "test_scheduler_executor_real.py", "test_scheduler_executor_readme.py"})

    @staticmethod
    def names_in(path: Path) -> set[str]:
        found = set()
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                found |= {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom) and not node.level:
                found.add((node.module or "").split(".")[0])
        return found

    def test_only_the_adapter_imports_the_executor_module(self):
        offenders = []
        for path in sorted(REPO.rglob("*.py")):
            rel = path.relative_to(REPO)
            if ".git" in rel.parts or MODULE in rel.parts or rel.parts[0] == "bitacora" or "node_modules" in rel.parts:
                continue
            # This boundary is about runtime dependencies; tests may import the executor directly.
            if "tests" in rel.parts or path.name.startswith("test_"):
                continue
            if path.name not in self.ALLOWED and MODULE in self.names_in(path):
                offenders.append(str(rel))
        self.assertEqual(offenders, [], "only bt_scheduler_executor_adapter may reach the executor module")

    def test_the_module_imports_nothing_of_the_methodology(self):
        stdlib = set(sys.stdlib_module_names)
        for path in sorted((REPO / "skill" / "scripts" / MODULE).glob("*.py")):
            bad = {n for n in self.names_in(path) if n not in stdlib and n != MODULE}
            self.assertEqual(bad, set(), path.name)

    def test_the_adapter_is_the_only_file_that_names_both_the_core_adapter_and_the_executor(self):
        text = Path(adapter.__file__).read_text()
        self.assertIn("import bt_scheduler_adapter as sched", text)
        self.assertNotIn("import bt_scheduler_core", text)

    def test_the_module_suite_passes_as_an_isolated_subprocess(self):
        import subprocess
        done = subprocess.run([sys.executable, "-I", "-m", "unittest", "discover", "-s",
                               str(REPO / "skill" / "scripts" / MODULE / "tests"), "-p", "test_[bcs]*.py"],
                              capture_output=True, text=True, cwd="/", timeout=600, check=False)
        self.assertEqual(done.returncode, 0, (done.stderr or done.stdout)[-1500:])

    def test_historical_runs_of_this_repository_are_byte_identical_after_a_whole_executor_session(self):
        def settled(path):
            """A run that is still going rewrites its own projection every heartbeat: only finished runs are history."""
            try:
                return json.loads(path.read_text(encoding="utf-8")).get("status") in ("done", "completed", "cancelled")
            except (OSError, ValueError, AttributeError):
                return True
        runs = sorted((REPO / "bitacora" / "metodologia").rglob("RUN.json")) + \
            [p for p in sorted((REPO / "bitacora" / "metodologia").rglob("RUN.projection.json")) if settled(p)]
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in runs}
        world = Operations("test_no_secret_value_appears_in_the_executors_state_or_in_the_cores_audit")
        result = unittest.TestResult()
        world.run(result)
        self.assertTrue(result.wasSuccessful(), result.errors + result.failures)
        self.assertEqual({p: hashlib.sha256(p.read_bytes()).hexdigest() for p in runs}, before)


if __name__ == "__main__":
    unittest.main()
