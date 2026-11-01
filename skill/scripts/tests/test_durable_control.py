"""Control plane of the durable runtime (REQ-030 M5): frontier, classification and recovery policy are pure,
bounded and evidence-based. Hypothesis explores task-state assignments and failure sequences."""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bt_contracts.execution import AgentReport, ProcessRecord, VerifyOutcome
from bt_contracts.failure import Budget, FailureClass, RecoveryAction, Spent
from bt_durable.control import classify, frontier, policy
from bt_durable.legacy import load_plan
from hypothesis import given, settings
from hypothesis import strategies as st

SCRIPTS = Path(__file__).resolve().parents[1]


def plan_of(tasks):
    text = json.dumps({"schema_version": "1.0.0", "plan_id": "REQ-900", "revision": 1, "tasks": tasks})
    import hashlib
    return load_plan(text, approved_sha256=hashlib.sha256(text.encode()).hexdigest())


def t(tid, after=(), repo="app", paths=None, resources=()):
    return {"id": tid, "milestone_id": "M1", "title": tid, "objective": tid, "repository": repo, "after": list(after),
            "expected_paths": paths if paths is not None else [f"{tid}/**"], "shared_resources": list(resources),
            "acceptance_criteria": [f"{tid} works"],
            "verification": [{"type": "command", "value": "true", "purpose": f"{tid} works"}]}


DIAMOND = plan_of([t("A"), t("B", ["A"]), t("C", ["A"]), t("D", ["B", "C"]), t("E", resources=["db"]),
                   t("F", resources=["db"])])


class Frontier(unittest.TestCase):
    def test_dependencies_and_exclusive_resources(self):
        front = frontier.compute(DIAMOND, {}, max_parallel=4)
        self.assertEqual(front.ready, ("A", "E"))            # F shares the exclusive resource with E
        front = frontier.compute(DIAMOND, {"A": "completed", "E": "running"}, max_parallel=4)
        self.assertEqual(front.ready, ("B", "C"))
        self.assertIn("F", front.held_by_resources)

    def test_a_blocked_task_blocks_only_its_dependents(self):
        front = frontier.compute(DIAMOND, {"A": "completed", "B": "blocked", "E": "completed"}, max_parallel=4)
        self.assertEqual(front.ready, ("C", "F"))
        self.assertEqual(front.unreachable, ("D",))

    def test_inherited_counts_as_done(self):
        states = {x: "inherited" for x in "ABCDEF"}
        self.assertTrue(frontier.compute(DIAMOND, states, max_parallel=1).finished)

    @settings(max_examples=300, deadline=None)
    @given(st.dictionaries(st.sampled_from("ABCDEF"), st.sampled_from(["completed", "inherited", "blocked",
                                                                         "cancelled", "running"])),
           st.integers(min_value=1, max_value=4))
    def test_ready_tasks_respect_every_invariant(self, states, parallel):
        front = frontier.compute(DIAMOND, states, max_parallel=parallel)
        running = sum(1 for s in states.values() if s == "running")
        self.assertLessEqual(len(front.ready) + running, max(parallel, running))
        by_id = {x.id: x for x in DIAMOND.tasks}
        for tid in front.ready:
            self.assertNotIn(tid, states)                                     # never restarts a known task
            self.assertTrue(all(states.get(d) in frontier.DONE for d in by_id[tid].after))
        self.assertFalse({"E", "F"} <= set(front.ready) | {k for k, v in states.items() if v == "running"}
                         and "E" in front.ready and "F" in front.ready)


# pictures REQ-021 r32 (D-262): T2.11 designs the contract; T2.3/T2.4/T2.5 → T2.6 → T2.55 → T2.56 → T2.57 (ui)
R32 = plan_of([t("T2.11"), t("T2.3", ["T2.11"]), t("T2.4", ["T2.11"]), t("T2.5", ["T2.11"]),
               t("T2.6", ["T2.3", "T2.4", "T2.5"]), t("T2.55", ["T2.6"]), t("T2.56", ["T2.55"]),
               t("T2.57", ["T2.56"])])
R32_INHERITED = {"T2.6": "inherited", "T2.55": "inherited", "T2.56": "inherited"}


class TransitiveFrontier(unittest.TestCase):
    def test_an_inherited_dependency_whose_ancestors_run_again_is_not_satisfied(self):
        # the r32 states: T2.11 re-running, T2.3/T2.4/T2.5 sent back (not started), the T2.6 chain inherited
        states = {**R32_INHERITED, "T2.11": "running"}
        old = frontier.compute(R32, states, max_parallel=4)
        self.assertIn("T2.57", old.ready)                    # the defect: only the direct dependency T2.56 was read
        front = frontier.compute(R32, states, max_parallel=4, transitive=True)
        self.assertNotIn("T2.57", front.ready)
        self.assertIn("T2.57", front.waiting)
        self.assertEqual(frontier.unready_ancestors(R32, states, "T2.57"), ("T2.11", "T2.3", "T2.4", "T2.5"))
        done = {**states, "T2.11": "completed"}               # T2.11 settled: its dependents run, T2.57 still waits
        front = frontier.compute(R32, done, max_parallel=4, transitive=True)
        self.assertEqual(front.ready, ("T2.3", "T2.4", "T2.5"))
        self.assertIn("T2.57", front.waiting)
        every = {**done, "T2.3": "completed", "T2.4": "inherited", "T2.5": "completed"}
        self.assertEqual(frontier.compute(R32, every, max_parallel=4, transitive=True).ready, ("T2.57",))

    def test_a_stopped_ancestor_behind_inherited_tasks_makes_the_task_unreachable(self):
        states = {**R32_INHERITED, "T2.11": "completed", "T2.3": "blocked", "T2.4": "completed", "T2.5": "completed"}
        self.assertNotIn("T2.57", frontier.compute(R32, states, max_parallel=4).unreachable)   # before: it was ready
        front = frontier.compute(R32, states, max_parallel=4, transitive=True)
        self.assertEqual(front.unreachable, ("T2.57",))
        self.assertTrue(frontier.settled(R32, states, transitive=True))

    @settings(max_examples=300, deadline=None)
    @given(st.dictionaries(st.sampled_from([x.id for x in R32.tasks]),
                           st.sampled_from(["completed", "inherited", "blocked", "cancelled", "running"])))
    def test_a_ready_task_has_every_ancestor_done(self, states):
        front = frontier.compute(R32, states, max_parallel=8, transitive=True)
        for tid in front.ready:
            self.assertTrue(all(states.get(a) in frontier.DONE for a in R32.ancestors(tid)), (tid, states))
        for tid in front.unreachable:
            self.assertTrue(any(states.get(a) in frontier.STOPPED for a in R32.ancestors(tid)), (tid, states))


def verdict(status, reason="FAIL_CODE", digest="", failing=("npm test",)):
    return VerifyOutcome(status=status, reason_code=reason, digest=digest, failing_checks=failing)


def proc(**kw):
    base = {"backend": "systemd", "state": "exited", "exit_code": 0, "log_path": "/tmp/x.log"}
    return ProcessRecord(**{**base, **kw})


class Classification(unittest.TestCase):
    def test_infrastructure_and_code_failures_get_different_classes(self):
        oom = classify.classify(classify.AttemptFacts(process=proc(), agent=AgentReport(status="completed"),
                                verify=verdict("FAIL", digest="FATAL ERROR: Ineffective mark-compacts near heap limit "
                                                              "Allocation failed - JavaScript heap out of memory")))
        code = classify.classify(classify.AttemptFacts(process=proc(), agent=AgentReport(status="completed"),
                                 verify=verdict("FAIL", digest="AssertionError: expected 3 got 4")))
        self.assertEqual(oom.failure_class, FailureClass.ENVIRONMENT)
        self.assertEqual(oom.code, "VERIFIER_OOM")
        self.assertEqual(code.failure_class, FailureClass.IMPLEMENTATION)
        self.assertIn("expected 3 got 4", code.agent_note)

    def test_quota_permission_and_agent_oom(self):
        quota = classify.classify(classify.AttemptFacts(process=proc(exit_code=1),
                                                        agent=AgentReport(status="limit", reset_epoch=123)))
        auth = classify.classify(classify.AttemptFacts(start_error="POLICY_DENIED: profile not allowed here"))
        agent_oom = classify.classify(classify.AttemptFacts(process=proc(oom_killed=True, result="oom-kill")))
        self.assertEqual(quota.failure_class, FailureClass.QUOTA)
        self.assertEqual(auth.failure_class, FailureClass.PERMISSION)
        self.assertEqual(agent_oom.code, "AGENT_OOM")

    def test_missing_source_file_is_not_a_dependency_problem(self):
        missing = "Error [ERR_MODULE_NOT_FOUND]: Cannot find module '/workspace/scripts/test/x.ts' imported from /workspace/"
        package = "Error: Cannot find module 'left-pad'"
        a = classify.classify(classify.AttemptFacts(process=proc(), verify=verdict("FAIL", digest=missing)))
        b = classify.classify(classify.AttemptFacts(process=proc(), verify=verdict("FAIL", digest=package)))
        self.assertEqual(a.failure_class, FailureClass.IMPLEMENTATION)
        self.assertEqual(b.code, "DEPENDENCY_MISSING")

    def test_declared_env_var_missing_is_environment(self):
        out = "Error: Set PICTURES_REQ021_DATABASE_URL, or set DATABASE_URL together with CI=true and APP_ENV=test."
        found = classify.classify(classify.AttemptFacts(process=proc(), verify=verdict("FAIL", digest=out),
                                                        declared_requires=("PICTURES_REQ021_DATABASE_URL",)))
        self.assertEqual((found.failure_class, found.code), (FailureClass.ENVIRONMENT, "ENV_MISSING"))

    def test_verifier_review_codes(self):
        cases = {"SANDBOX_UNAVAILABLE": FailureClass.TRANSIENT, "CHECK_MANUAL": FailureClass.PRODUCT_DECISION,
                 "POLICY_ENTRY_MISSING_AUTHORIZATION": FailureClass.PERMISSION, "CHECK_TIMEOUT": FailureClass.VERIFICATION}
        for reason, expected in cases.items():
            got = classify.classify(classify.AttemptFacts(process=proc(), verify=verdict("NEEDS_REVIEW", reason)))
            self.assertEqual(got.failure_class, expected, reason)

    def test_signature_ignores_volatile_details(self):
        a = classify.signature(FailureClass.IMPLEMENTATION, "X", "Timeout 30000ms exceeded at 0xdeadbeef /tmp/a1/b:12:4")
        b = classify.signature(FailureClass.IMPLEMENTATION, "X", "Timeout 20000ms exceeded at 0xfeedface /tmp/zz/q:9:1")
        self.assertEqual(a, b)

    def test_pass_is_not_a_failure(self):
        self.assertIsNone(classify.classify(classify.AttemptFacts(process=proc(), verify=verdict("PASS", failing=()))))


def report(cls, code="X", sig="sig00000"):
    from bt_contracts.failure import FailureReport
    return FailureReport(failure_class=cls, code=code, summary="s", signature=sig)


class NoChangeAndContract(unittest.TestCase):
    """D-262: an attempt that changed nothing, and a UI contract the base does not hold, are facts for the owner."""

    def snapshot(self, changed=()):
        from bt_contracts.execution import Snapshot
        return Snapshot(snapshot_sha="a" * 40, base_sha="a" * 40 if not changed else "b" * 40, changed_paths=changed)

    def test_an_unchanged_attempt_is_classified_from_the_agent_s_own_reason(self):
        said = "Stopped at the design gate: design/contracts/cuentas-admin@v2.md is missing. No changes made."
        agent = AgentReport(status="completed", text=said)
        self.assertTrue(classify.unchanged(self.snapshot(), agent))
        self.assertFalse(classify.unchanged(self.snapshot(("src/a.ts",)), agent))
        self.assertFalse(classify.unchanged(self.snapshot(), AgentReport(status="failed", text=said)))
        checked = classify.classify(classify.AttemptFacts(agent=agent, verify=verdict("FAIL", digest="Missing script"),
                                                          failing_output="Missing script"))
        self.assertEqual(checked.code, "CHECK_FAILED")
        found = classify.no_change(checked, agent, verdict("FAIL"))
        self.assertEqual((found.failure_class, found.code), (FailureClass.ENVIRONMENT, classify.NO_CHANGE))
        self.assertIn("design gate", found.summary)
        self.assertIn("changed nothing", found.agent_note)
        again = classify.no_change(checked, AgentReport(status="completed", text="other words, same stop"),
                                   verdict("FAIL"))
        self.assertEqual(found.signature, again.signature)             # a repeat is recognisable whatever it says
        decision = policy.decide(found, Spent(attempts=1, signatures={found.signature: 1}), Budget(), now=0,
                                 other_route=True)
        self.assertEqual(decision.action, RecoveryAction.ESCALATE)
        self.assertIn("design gate", decision.reason)

    def test_the_contract_gate_names_its_state(self):
        for state, code in (("missing", "DESIGN_CONTRACT_MISSING"), ("unapproved", "DESIGN_CONTRACT_UNAPPROVED"),
                            ("hash-mismatch", "DESIGN_CONTRACT_HASH_MISMATCH")):
            found = classify.design_contract({"state": state, "path": "design/contracts/shop@v1.md",
                                              "design_task": "T1"})
            self.assertEqual((found.failure_class, found.code), (FailureClass.ENVIRONMENT, code))
            self.assertIn(code, found.summary)
            self.assertEqual(policy.decide(found, Spent(), Budget(), now=0, other_route=True).action,
                             RecoveryAction.ESCALATE)


class HeapLimit(unittest.TestCase):
    """D-262 (pictures REQ-021 r32 T3.91 a1): a Node heap-limit abort is not a sandbox memory kill."""
    HEAP = ("<--- Last few GCs --->\nFATAL ERROR: Ineffective mark-compacts near heap limit Allocation failed - "
            "JavaScript heap out of memory\n")
    OWN = "npx --no-install tsx scripts/test/test-ui-arrastre-mesas-parametricas.ts --suite rectangular-mouse"

    def oom(self, out):
        v = verdict("FAIL", digest=out, failing=(self.OWN, "npx --no-install tsc --noEmit"))
        return v, classify.classify(classify.AttemptFacts(verify=v, failing_output=out))

    def test_the_task_s_own_harness_gets_an_implementation_failure_with_a_concrete_note(self):
        v, first = self.oom(self.HEAP)
        self.assertEqual(first.code, "VERIFIER_OOM")                       # what the classifier alone still says
        paths = ("scripts/test/test-ui-arrastre-mesas-parametricas.ts", "src/**")
        own = classify.own_check(v.failing_checks, known_paths=paths)
        self.assertEqual(own, self.OWN)
        self.assertEqual(classify.own_check(v.failing_checks, own=(self.OWN,)), self.OWN)   # created_by in the plan
        self.assertEqual(classify.own_check(v.failing_checks, known_paths=("src/**",)), "")
        found = classify.heap_limit(first, v, own=own, relaxed=False)
        self.assertEqual((found.failure_class, found.code), (FailureClass.IMPLEMENTATION, classify.HEAP_LIMIT))
        self.assertIn("NODE_OPTIONS", found.agent_note)
        self.assertIn("--max-old-space-size=4096", found.agent_note)
        self.assertEqual(policy.decide(found, Spent(attempts=1, signatures={found.signature: 1}), Budget(), now=0,
                                       other_route=False).action, RecoveryAction.RETRY)

    def test_another_check_is_re_verified_once_then_goes_to_the_owner_as_a_plan_problem(self):
        v, first = self.oom(self.HEAP)
        self.assertIsNone(classify.heap_limit(first, v, own="", relaxed=False))   # the relaxed heap may still help
        found = classify.heap_limit(first, v, own="", relaxed=True)
        self.assertEqual((found.failure_class, found.code), (FailureClass.CONTRACT, classify.HEAP_LIMIT_PLAN))
        self.assertEqual(policy.decide(found, Spent(attempts=1), Budget(), now=0, other_route=False).action,
                         RecoveryAction.ESCALATE)

    def test_a_genuine_sandbox_memory_kill_keeps_the_environment_repair(self):
        for out in (self.HEAP + "Killed\n", "process exited with signal 9 (oom-kill)\nKilled\n"):
            v, first = self.oom(out)
            self.assertEqual(first.code, "VERIFIER_OOM")
            self.assertEqual(classify.heap_abort(out), "")
            self.assertIsNone(classify.heap_limit(first, v, own=self.OWN, relaxed=True))


class Policy(unittest.TestCase):
    B = Budget()

    def test_never_bypasses_permission_or_product_decisions(self):
        for cls in (FailureClass.PERMISSION, FailureClass.PRODUCT_DECISION):
            self.assertEqual(policy.decide(report(cls), Spent(), self.B, now=0, other_route=True).action,
                             RecoveryAction.ESCALATE)

    def test_environment_repair_is_bounded_and_needs_no_attempt(self):
        first = policy.decide(report(FailureClass.ENVIRONMENT, "VERIFIER_OOM"), Spent(attempts=1), self.B, now=0,
                              other_route=False)
        again = policy.decide(report(FailureClass.ENVIRONMENT, "VERIFIER_OOM"),
                              Spent(attempts=1, environment_repairs=1), self.B, now=0, other_route=False)
        self.assertEqual(first.action, RecoveryAction.REPAIR_ENVIRONMENT)
        self.assertEqual(again.action, RecoveryAction.ESCALATE)

    def test_quota_switches_route_then_waits_for_the_reset_then_escalates(self):
        f = report(FailureClass.QUOTA)
        self.assertEqual(policy.decide(f, Spent(), self.B, now=0, other_route=True).action,
                         RecoveryAction.RETRY_OTHER_ROUTE)
        wait = policy.decide(f, Spent(route_changes=2), self.B, now=100, other_route=True, reset_epoch=500)
        self.assertEqual((wait.action, wait.not_before), (RecoveryAction.WAIT, 500))
        unknown = policy.decide(f, Spent(route_changes=2), self.B, now=100, other_route=False)
        self.assertEqual(unknown.not_before, 100 + policy.QUOTA_COOLDOWN)
        self.assertEqual(policy.decide(f, Spent(waits=self.B.max_waits), self.B, now=0, other_route=False).action,
                         RecoveryAction.ESCALATE)

    def test_same_failure_twice_becomes_one_remediation_then_the_owner(self):
        f = report(FailureClass.IMPLEMENTATION, sig="same0000")
        self.assertEqual(policy.decide(f, Spent(attempts=1, signatures={"same0000": 1}), self.B, now=0,
                                       other_route=False).action, RecoveryAction.RETRY)
        self.assertEqual(policy.decide(f, Spent(attempts=2, signatures={"same0000": 2}), self.B, now=0,
                                       other_route=False).action, RecoveryAction.REMEDIATE)
        self.assertEqual(policy.decide(f, Spent(attempts=3, signatures={"same0000": 3}), self.B, now=0,
                                       other_route=False, remediated=True).action, RecoveryAction.ESCALATE)

    @staticmethod
    def failed(sig, failing=("npm test",), passing=()):
        """A failed attempt as `spent` reads it (process, failure, verify)."""
        from types import SimpleNamespace
        return SimpleNamespace(process=proc(exit_code=1), agent=None, failure=report(FailureClass.IMPLEMENTATION,
                               "CHECK_FAILED", sig), verify=VerifyOutcome(status="FAIL", failing_checks=failing,
                                                                          passing_checks=passing))

    def test_an_answered_decision_opens_a_fresh_attempt_window(self):
        """pictures REQ-021 r32 T3.91 (D-269): a1..a9 spent the budget; after the operator's answer a10 failed once on a
        NEW assertion (the drag worked now) and escalated at once, «the task used its attempts». Counted from the
        answer, a10 is the window's first attempt and is retried; the window's own budget still escalates."""
        history = [self.failed(f"old{n:05d}") for n in range(9)] + [self.failed("new00000")]
        whole = policy.spent(history)
        self.assertEqual((whole.attempts, whole.total_attempts), (10, None))
        f = report(FailureClass.IMPLEMENTATION, "CHECK_FAILED", "new00000")
        self.assertEqual(policy.decide(f, whole, self.B, now=0, other_route=False).limit_hit, "max_attempts")
        window = policy.spent(history, since=9)
        self.assertEqual((window.attempts, window.total_attempts, window.signatures), (1, 10, {"new00000": 1}))
        self.assertEqual(policy.decide(f, window, self.B, now=0, other_route=False).action, RecoveryAction.RETRY)
        spent_window = policy.spent(history + [self.failed(f"w{n:07d}") for n in range(3)], since=9)
        late = policy.decide(f, spent_window, self.B, now=0, other_route=False)
        self.assertEqual((late.action, late.limit_hit), (RecoveryAction.ESCALATE, "max_attempts"))
        self.assertIn("since the last answered decision", late.reason)

    def test_the_whole_task_has_a_ceiling_across_answers(self):
        budget = Budget(max_attempts=4, max_attempts_total=12)
        history = [self.failed(f"s{n:07d}") for n in range(12)]
        f = report(FailureClass.IMPLEMENTATION, "CHECK_FAILED", "s0000011")
        used = policy.spent(history, since=11)                       # the window's first attempt, the task's 12th
        decision = policy.decide(f, used, budget, now=0, other_route=False)
        self.assertEqual((decision.action, decision.limit_hit), (RecoveryAction.ESCALATE, "max_attempts_total"))
        self.assertEqual(policy.decide(f, policy.spent(history[:11], since=10), budget, now=0,
                                       other_route=False).action, RecoveryAction.RETRY)

    def test_the_default_ceiling_stays_out_of_the_settings_an_older_engine_reads(self):
        """The client sends the settings to the engine; an engine on the code before D-269 forbids unknown fields."""
        self.assertNotIn("max_attempts_total", Budget().model_dump(mode="json"))
        self.assertEqual(Budget.model_validate(Budget().model_dump(mode="json")).max_attempts_total, 20)
        self.assertEqual(Budget(max_attempts_total=9).model_dump(mode="json")["max_attempts_total"], 9)

    def test_the_window_counts_repeats_and_regressions_from_the_answer(self):
        same = [self.failed("same0000"), self.failed("same0000")]
        f = report(FailureClass.IMPLEMENTATION, "CHECK_FAILED", "same0000")
        self.assertEqual(policy.decide(f, policy.spent(same), self.B, now=0, other_route=False).action,
                         RecoveryAction.REMEDIATE)
        after = policy.spent([*same, self.failed("same0000")], since=2)
        self.assertEqual(after.signatures, {"same0000": 1})
        self.assertEqual(policy.decide(f, after, self.B, now=0, other_route=False, remediated=False).action,
                         RecoveryAction.RETRY)
        # a check that passed before the answer and fails after it is still a regression
        broke = [self.failed("a0000000", failing=("unit",), passing=("lint",)),
                 self.failed("b0000000", failing=("lint",)), self.failed("c0000000", failing=("lint",))]
        self.assertEqual(policy.spent(broke).consecutive_regressions, 2)
        self.assertEqual(policy.spent(broke, since=2).consecutive_regressions, 1)
        self.assertEqual(policy.spent(broke, since=3).consecutive_regressions, 0)

    @settings(max_examples=500, deadline=None)
    @given(st.lists(st.tuples(st.sampled_from(list(FailureClass)), st.sampled_from(["s1aaaaaa", "s2bbbbbb", "s3cccccc"])),
                    min_size=1, max_size=60))
    def test_no_failure_sequence_loops_forever(self, sequence):
        """Feeding any failure sequence back into the policy reaches escalate/stop within the budget's limits."""
        budget = Budget(max_attempts=4, max_waits=6, max_environment_repairs=1, max_route_changes=2)
        spent = Spent()
        remediated = False
        automatic = 0
        for cls, sig in sequence:
            spent = spent.model_copy(update={"signatures": {**spent.signatures, sig: spent.signatures.get(sig, 0) + 1}})
            decision = policy.decide(report(cls, "VERIFIER_OOM" if cls == FailureClass.ENVIRONMENT else "X", sig),
                                     spent, budget, now=0, other_route=True)
            if decision.action in (RecoveryAction.ESCALATE, RecoveryAction.STOP):
                return
            automatic += 1
            update = {}
            if decision.action in (RecoveryAction.RETRY, RecoveryAction.REMEDIATE,
                                   RecoveryAction.RECONCILE_INTEGRATION, RecoveryAction.RETRY_OTHER_ROUTE):
                update["attempts"] = spent.attempts + 1
            if decision.action == RecoveryAction.WAIT:
                update["waits"] = spent.waits + 1
            if decision.action == RecoveryAction.REPAIR_ENVIRONMENT:
                update["environment_repairs"] = spent.environment_repairs + 1
            if decision.action == RecoveryAction.RETRY_OTHER_ROUTE:
                update["route_changes"] = spent.route_changes + 1
            remediated = remediated or decision.action == RecoveryAction.REMEDIATE
            spent = spent.model_copy(update=update)
        # every automatic action consumed a bounded counter: the total is capped by the budget
        cap = (budget.max_attempts + budget.max_waits + budget.max_environment_repairs + budget.max_route_changes
               + 3 * budget.max_same_signature + 1)
        self.assertLessEqual(automatic, cap)


class Boundary(unittest.TestCase):
    def test_control_plane_imports_no_dbos(self):
        code = ("import sys, importlib.abc\n"
                "class B(importlib.abc.MetaPathFinder):\n"
                "    def find_spec(self, n, p=None, t=None):\n"
                "        if n.split('.')[0] in ('dbos','sqlalchemy'): raise ImportError(n)\n"
                f"sys.meta_path.insert(0, B()); sys.path.insert(0, {str(SCRIPTS)!r})\n"
                "import bt_durable.control.frontier, bt_durable.control.classify, bt_durable.control.policy\n"
                "print('ok')")
        done = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=60, check=False)
        self.assertEqual(done.returncode, 0, done.stderr)


if __name__ == "__main__":
    unittest.main()
