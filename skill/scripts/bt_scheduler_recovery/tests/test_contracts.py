import math
import unittest
from dataclasses import FrozenInstanceError, replace

from bt_scheduler_recovery import (
    HistorySummary,
    Policy,
    RecoveryCase,
    RecoveryDecision,
    RecoveryError,
    propose,
)
from helpers import case


class ContractsTests(unittest.TestCase):
    def test_round_trip(self):
        source = case()
        self.assertEqual(source, RecoveryCase.from_dict(source.to_dict()))
        self.assertEqual(case(handoff_sha="c" * 40).handoff_sha, "c" * 40)
        refs = tuple(f"ledger:{index:064x}" for index in range(32))
        self.assertEqual(len(case(evidence_refs=refs).evidence_refs), 32)
        decision = propose(source)
        self.assertEqual(decision, RecoveryDecision.from_dict(decision.to_dict()))
        with self.assertRaises(FrozenInstanceError):
            source.now = 3

    def test_direct_constructors_reject_hostile_values(self):
        values = {"run_id": ["../run", "", "token=secret", "a" * 129, 1],
                  "plan_sha256": ["x" * 64, "A" * 64, "a" * 63], "revision": [True, 0, 1.2],
                  "token": [False, 0, -1], "technical_cause": ["ECONNRESET", "retry", None],
                  "core_cause": ["timeout", ""], "confidence": ["sure", 1],
                  "execution_state": ["uncertain", "running"], "current": [1, "true"],
                  "manual_cancel": [None, 0], "handoff_sha": ["/tmp/path", "a" * 65],
                  "verification_ref": ["/private/log", "verdict:secrets"],
                  "evidence_refs": [["ledger:" + "a" * 64], ("file:/tmp/log",), ("ledger:" + "a" * 64,) * 2],
                  "attempts_used": [True, -1, 0], "max_attempts": [0, 1e9],
                  "now": [math.nan, math.inf, True, -1, 10**1000], "reset_epoch": [math.nan, -1],
                  "failure_at": [math.inf], "max_wait_seconds": [0, 86401], "recovery_round": [-1],
                  "max_waits": [True, 1_000_001]}
        for field, invalid in values.items():
            for value in invalid:
                with self.subTest(field=field, value=repr(value)), self.assertRaises(RecoveryError):
                    case(**{field: value})

    def test_hostile_wire_rejects_unknown_schema_and_fields(self):
        for raw in (None, [], 3, {}, {**case().to_dict(), "schema_version": "v2"},
                    {**case().to_dict(), "detail": "password=secret"},
                    {**case().to_dict(), "evidence_refs": "ledger:secret"},
                    {key: value for key, value in case().to_dict().items() if key != "run_id"}):
            with self.subTest(raw=raw), self.assertRaises(RecoveryError):
                RecoveryCase.from_dict(raw)

    def test_wire_structures_are_bounded_before_copying_or_conversion(self):
        source = case().to_dict()
        oversized_key = dict(source)
        oversized_key["x" * 10_000] = oversized_key.pop("run_id")
        cases = (
            ({**source, "evidence_refs": ["ledger:" + "a" * 64] * 33}, "INVALID_INPUT"),
            (oversized_key, "INVALID_INPUT"),
            ({**source, **{f"unknown-{index}": None for index in range(100)}}, "INVALID_INPUT"),
            ({**source, "technical_cause": "unknown" * 100_000}, "INVALID_INPUT"),
        )
        for raw, expected_code in cases:
            with self.subTest(raw_size=len(repr(raw))), self.assertRaises(RecoveryError) as caught:
                RecoveryCase.from_dict(raw)
            self.assertEqual(caught.exception.code, expected_code)
        with self.assertRaises(RecoveryError) as caught:
            case(run_id="r" * 100_000)
        self.assertEqual(caught.exception.code, "INVALID_INPUT")

    def test_policy_and_history_validation(self):
        for change in ({"max_same_cause": 0}, {"base_backoff_seconds": math.inf},
                       {"max_backoff_seconds": 0}, {"version": "secret\n"},
                       {"max_decisions": True}, {"reset_margin_seconds": -1}):
            with self.subTest(change=change), self.assertRaises(RecoveryError):
                Policy(**change)
        for kwargs in ({"same_cause_attempts": -1}, {"decisions": math.nan}, {"decisions": True}):
            with self.assertRaises(RecoveryError):
                HistorySummary(**kwargs)

    def test_malicious_decision_rejected(self):
        value = propose(case())
        for change in ({"wait_seconds": math.nan}, {"action": "execute"}, {"reason_code": "secret\n"},
                       {"routing_hint": "codex"}, {"retry_budget_remaining": 0},
                       {"cooldown_until": math.inf}, {"human_required": 1}):
            with self.subTest(change=change), self.assertRaises(RecoveryError):
                replace(value, **change)


if __name__ == "__main__":
    unittest.main()
