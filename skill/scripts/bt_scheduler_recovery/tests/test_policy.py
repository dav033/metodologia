import unittest
from dataclasses import replace

from bt_scheduler_recovery import HistorySummary, Policy, propose
from helpers import case


class PolicyTests(unittest.TestCase):
    def test_safety_precedes_budget_and_cause(self):
        for changes, reason in (({"manual_cancel": True}, "manual_cancel"),
                                ({"execution_state": "cancelled"}, "manual_cancel"),
                                ({"current": False}, "identity_unverified"),
                                ({"identity_verified": False}, "identity_unverified"),
                                ({"execution_state": "live"}, "execution_unsettled"),
                                ({"execution_state": "unknown"}, "execution_unsettled"),
                                ({"core_cause": "lost"}, "execution_unsettled")):
            with self.subTest(changes=changes):
                result = propose(case(max_attempts=1, **changes))
                self.assertEqual((result.action, result.reason_code), ("block", reason))

    def test_guards_block_without_authoritative_evidence(self):
        for changes, reason in (({"now": 99}, "evidence_from_future"),
                                ({"now": 100_000}, "evidence_stale"),
                                ({"evidence_refs": ()}, "evidence_insufficient"),
                                ({"confidence": "inferred"}, "evidence_insufficient"),
                                ({"max_attempts": 1}, "attempts_exhausted"),
                                ({"handoff_sha": None}, "handoff_missing")):
            with self.subTest(changes=changes):
                result = propose(case(**changes))
                self.assertEqual((result.action, result.reason_code), ("block", reason))

    def test_permanent_matrix(self):
        for cause in ("artifact_error", "start_failed", "killed", "lost", "clean", "integration_conflict",
                      "predecessor_missing", "unknown"):
            with self.subTest(cause=cause):
                result = propose(case(technical_cause=cause))
                self.assertEqual(result.action, "block")
                self.assertTrue(result.human_required)

    def test_transient_matrix_requires_confirmation_and_handoff(self):
        for cause in ("connection_lost", "timeout", "agent_error", "incomplete_output"):
            with self.subTest(cause=cause):
                source = case(technical_cause=cause)
                self.assertEqual(propose(source).action, "retry")
                self.assertEqual(propose(replace(source, transient_confirmed=False)).action, "block")
                self.assertEqual(propose(replace(source, handoff_sha=None)).action, "block")
                self.assertEqual(propose(replace(source, execution_state="finished")).action, "block")
                self.assertEqual(propose(replace(source, confidence="reported")).action, "retry")

    def test_cooldown_is_absolute_and_exponential(self):
        policy = Policy(base_backoff_seconds=10, max_backoff_seconds=15)
        source = case(now=100)
        self.assertEqual(propose(source, policy).cooldown_until, 110)
        later = propose(replace(source, now=105, recovery_round=1), policy)
        self.assertEqual((later.wait_seconds, later.cooldown_until, later.waits_remaining), (5, 110, 1))
        self.assertEqual(propose(replace(source, now=110), policy).action, "retry")
        self.assertEqual(propose(source, policy, HistorySummary(1)).cooldown_until, 115)
        self.assertEqual(propose(source, policy, HistorySummary(2)).reason_code, "same_cause_limit")

    def test_waits_and_elapsed_are_bounded_for_one_hundred_rounds(self):
        source = case(now=100)
        policy = Policy(base_backoff_seconds=10)
        for index in range(100):
            result = propose(replace(source, recovery_round=index), policy)
            self.assertEqual(result.action, "wait" if index < 3 else "block")
            self.assertGreaterEqual(result.waits_remaining, 0)
        self.assertEqual(propose(source, Policy(max_elapsed_seconds=1, base_backoff_seconds=10)).reason_code,
                         "elapsed_limit")
        self.assertEqual(propose(source, Policy(base_backoff_seconds=10), HistorySummary(decisions=10000)).reason_code,
                         "decision_limit")

    def test_quota_known_short_unknown_long_elapsed_reset(self):
        source = case(technical_cause="quota_exhausted", reset_epoch=110, now=100)
        result = propose(source)
        self.assertEqual((result.action, result.wait_seconds, result.routing_hint), ("wait", 11, "reevaluate"))
        self.assertEqual(propose(replace(source, reset_epoch=None)).reason_code, "quota_reset_unknown")
        self.assertEqual(propose(replace(source, reset_epoch=90000)).reason_code, "wait_window_exceeded")
        self.assertEqual(propose(replace(source, now=111, recovery_round=1)).action, "retry")
        self.assertEqual(propose(replace(source, max_waits=0)).reason_code, "wait_limit")

    def test_timeout_has_only_one_retry(self):
        source = case(technical_cause="timeout")
        self.assertEqual(propose(source).action, "retry")
        self.assertEqual(propose(source, history=HistorySummary(1)).reason_code, "timeout_repeated")

    def test_m6_blockers_precede_attempt_and_code_retry_exhaustion(self):
        for reason in ("BLOCKED_EXTERNAL", "BLOCKED_ENV"):
            with self.subTest(reason=reason):
                result = propose(case(reason_code=reason, attempts_used=3, max_attempts=3),
                                 history=HistorySummary(same_cause_attempts=100))
                expected = ("m6_blocked_external_owner_must_restore_dependency" if reason == "BLOCKED_EXTERNAL"
                            else "m6_blocked_env_operator_must_repair_environment")
                self.assertEqual((result.action, result.reason_code), ("block", expected))
                self.assertEqual(result.retry_budget_remaining, 0)

    def test_reason_policy_taxonomy_never_routes_m6_pass_to_acceptance(self):
        expected = {
            "TIMEOUT": ("retry", None),
            "FLAKY_SUSPECTED": ("block", "flaky_requires_m6_rerun_policy"),
            "NOT_RUN": ("block", "m6_not_run"),
            "FAIL_CODE": ("retry", None),
            "PASS": ("block", "m6_pass_not_recovery"),
        }
        for reason, (action, decision_reason) in expected.items():
            with self.subTest(reason=reason):
                result = propose(case(reason_code=reason))
                self.assertEqual(result.action, action)
                if decision_reason is not None:
                    self.assertEqual(result.reason_code, decision_reason)

    def test_unclassified_legacy_decision_is_identical(self):
        source = case()
        self.assertEqual(source.to_dict()["schema_version"], "m5.recovery-case/2")
        self.assertEqual(source.reason_code, "UNCLASSIFIED")
        self.assertEqual(propose(source), propose(case(reason_code="UNCLASSIFIED")))

    def test_verification_rejection_never_accepts(self):
        source = case(core_cause="verification_rejected", technical_cause="verification_rejected",
                      execution_state="finished", verification_ref="verdict:" + "d" * 64)
        self.assertEqual((propose(source).action, propose(source).reason_code), ("retry", "verification_rejected"))
        self.assertEqual(propose(replace(source, verification_ref=None)).reason_code, "verification_evidence_missing")
        self.assertEqual(propose(replace(source, core_cause="execution_failed")).action, "block")
        self.assertEqual(propose(replace(source, technical_cause="clean")).action, "retry")
        self.assertEqual(propose(replace(source, execution_state="failed")).action, "block")

    def test_m6_code_failure_uses_bounded_verification_rework(self):
        source = case(core_cause="verification_rejected", technical_cause="verification_rejected",
                      execution_state="finished", verification_ref="verdict:" + "d" * 64,
                      reason_code="FAIL_CODE")
        self.assertEqual(propose(source).action, "retry")
        self.assertEqual(propose(source, history=HistorySummary(same_cause_attempts=2)).reason_code,
                         "same_cause_limit")

    def test_largest_valid_timestamp_produces_bounded_decision(self):
        result = propose(case(now=1e12, failure_at=1e12))
        self.assertEqual((result.action, result.wait_seconds), ("wait", 1))

    def test_determinism_and_identity_policy_hashing(self):
        source = case()
        self.assertEqual(propose(source), propose(source))
        self.assertEqual(source, case())
        first = propose(source).decision_id
        for changed in (replace(source, run_id="run-2"), replace(source, token=2), replace(source, revision=2),
                        replace(source, recovery_round=1), replace(source, plan_sha256="d" * 64)):
            self.assertNotEqual(first, propose(changed).decision_id)
        self.assertNotEqual(first, propose(source, Policy(base_backoff_seconds=2)).decision_id)


if __name__ == "__main__":
    unittest.main()
