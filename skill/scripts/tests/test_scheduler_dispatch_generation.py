"""Retry route identity across real M2 persistence and M3 single-use ledger gates.

All provider/quota inputs below are explicit test fixtures. No provider launches,
Git repositories, hooks, or real quota observations are involved.
"""
from __future__ import annotations

import dataclasses
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bt_scheduler_adapter as adapter
from bt_scheduler_decision import DecisionInputError, idempotency_key, validate_request
from bt_scheduler_decision.tests.support import PLAN_HASH, candidate, request
from bt_scheduler_executor.errors import ExecutorError
from bt_scheduler_executor.ledger import Ledger
from bt_scheduler_executor.model import QUEUED, StartRequest


class DispatchGenerationTests(unittest.TestCase):
    def test_new_authorized_attempt_gets_new_reference_and_keeps_m3_single_use(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            port = adapter.DecisionAssignmentPort("proj", root / "m2.db", laya_root=root)
            self.addCleanup(port.close)
            task = adapter.core.TaskView("T1", "M1", "app", (), (), 0,
                                          {"title": "Implement feature", "risk": "low", "complexity": "low",
                                           "scope": "small_change"})
            order = adapter.core.AssignmentRequest("REQ-013", 1, (task,), 1, 100.0, PLAN_HASH)
            with (patch.object(adapter, "refresh_quota_preflight", return_value={
                    "work": {"status": "available", "reason": "quota_fresh"}}),
                  patch.object(adapter.decision_sources, "_candidate_rows", return_value=(candidate(),)),
                  patch("bt_scheduler_plan_routing.time.time", return_value=100.0)):
                first = port.propose(order)[0]
                self.assertEqual(port.propose(order)[0], first)
                retry_order = dataclasses.replace(order, ready=(dataclasses.replace(task, attempts=1),))
                retry = port.propose(retry_order)[0]
                self.assertEqual(port.propose(retry_order)[0], retry)
                third_order = dataclasses.replace(order, ready=(dataclasses.replace(task, attempts=2),))
                third = port.propose(third_order)[0]
            m3 = Ledger(root / "m3.db", clock=lambda: 100.0)
            for index, assignment in enumerate((first, retry, third), start=1):
                start = StartRequest(f"key-{index}", order.plan_id, 1, "T1", f"att-{index}", index,
                                     assignment.executor, "app", plan_sha256=PLAN_HASH)
                binding = adapter.resolve_m2_route(root / "m2.db", assignment.executor)
                self.assertIsNotNone(binding)
                route = {**binding, "single_use": True, "reference": assignment.executor}
                row, created = m3.insert(start, dirname=f"attempt-{index}", state=QUEUED, route=route)
                self.assertTrue(created)
                self.assertEqual(row["state"], QUEUED)
            self.assertEqual(len({first.executor, retry.executor, third.executor}), 3)
            replay = dataclasses.replace(start, idempotency_key="illegal-replay", attempt_id="att-4")
            with self.assertRaisesRegex(ExecutorError, "ROUTE_INVALID"):
                m3.insert(replay, dirname="attempt-4", state=QUEUED, route=route)

    def test_zero_generation_preserves_pre_extension_decision_key(self):
        # Frozen from the prior key algorithm and this deterministic request fixture.
        self.assertEqual(idempotency_key(request()),
                         "c723c448fe13cdbb6059b8f74c1495049ac978fb2224812d869d215b383a3ddc")

    def test_generation_is_validated_and_survives_normalization(self):
        base = request()
        for invalid in (-1, True, 1.5, "1"):
            with self.subTest(invalid=invalid), self.assertRaises(DecisionInputError):
                validate_request(dataclasses.replace(base, dispatch_generation=invalid))
        for generation in (0, 1, 2):
            value = dataclasses.replace(base, dispatch_generation=generation)
            self.assertEqual(validate_request(value).request.dispatch_generation, generation)
            self.assertEqual(idempotency_key(value), idempotency_key(dataclasses.replace(value, requested_at=101.0)))
        self.assertNotEqual(idempotency_key(base), idempotency_key(dataclasses.replace(base, dispatch_generation=1)))


if __name__ == "__main__":
    unittest.main()
