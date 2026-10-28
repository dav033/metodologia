"""Control plane of the durable runtime (REQ-030 M5): frontier, classification and recovery policy are pure,
bounded and evidence-based. Hypothesis explores task-state assignments and failure sequences."""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hypothesis import given, settings
from hypothesis import strategies as st

from bt_contracts.execution import AgentReport, ProcessRecord, VerifyOutcome
from bt_contracts.failure import Budget, FailureClass, RecoveryAction, Spent
from bt_durable.control import classify, frontier, policy
from bt_scheduler_core.plan import load_plan

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
        done = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=60)
        self.assertEqual(done.returncode, 0, done.stderr)


if __name__ == "__main__":
    unittest.main()
