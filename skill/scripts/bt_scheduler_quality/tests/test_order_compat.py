"""Admission of legacy remediation orders through the real M1/M6 adapter."""

import unittest
from dataclasses import replace

import test_adapter as fixtures


class LegacyRepairAdmissionTests(unittest.TestCase):
    _system = fixtures.M6M1AdapterTests._system
    _start_attempts = fixtures.M6M1AdapterTests._start_attempts

    def test_legacy_repair_command_expected_pass_is_verified_without_changing_the_plan(self):
        task = fixtures._task("T1", "python3 verify.py")
        task["verification"][0]["expected"] = "pass"
        root, core, _, executor, _store, adapter = self._system([task])
        attempts = self._start_attempts(core, executor, root, ("T1",))
        response = adapter.request(fixtures._order_from_plan(core, "T1", attempts["T1"]))
        self.assertEqual(response.status, "accepted")
        self.assertTrue(fixtures._wait_for(lambda: core.snapshot().tasks["T1"]["state"] == "completed"))
        self.assertEqual(adapter.engine.runner.runner.calls, ["python3 verify.py"])
        self.assertEqual(core.plan.task("T1").verification[0]["expected"], "pass")

    def test_legacy_command_compatibility_does_not_accept_other_expected_values(self):
        task = fixtures._task("T1", "python3 verify.py")
        task["verification"][0]["expected"] = "ignore failure"
        root, core, _, executor, store, adapter = self._system([task])
        attempts = self._start_attempts(core, executor, root, ("T1",))
        response = adapter.request(fixtures._order_from_plan(core, "T1", attempts["T1"]))
        self.assertEqual((response.status, response.detail), ("rejected", "ORDER_INVALID"))
        self.assertTrue(response.permanent)                         # the core ends the attempt instead of re-sending a refused order
        self.assertEqual(store.pending_requests(), ())
        self.assertEqual(adapter.engine.runner.runner.calls, [])

    def test_legacy_compatibility_still_rejects_a_changed_command(self):
        task = fixtures._task("T1", "python3 verify.py")
        task["verification"][0]["expected"] = "pass"
        root, core, _, executor, store, adapter = self._system([task])
        attempts = self._start_attempts(core, executor, root, ("T1",))
        approved = fixtures._order_from_plan(core, "T1", attempts["T1"])
        changed = {**approved.verification[0], "value": "python3 other.py"}
        response = adapter.request(replace(approved, verification=(changed,)))
        self.assertEqual((response.status, response.detail), ("rejected", "ORDER_DIFFERS_FROM_APPROVED_PLAN"))
        self.assertEqual(store.pending_requests(), ())

    def test_legacy_command_failure_is_not_accepted(self):
        task = fixtures._task("T1", "python3 verify.py")
        task["verification"][0]["expected"] = "pass"
        runner = fixtures.ScriptedRunner(failing_commands=("python3 verify.py",))
        root, core, _, executor, store, adapter = self._system([task], runner=runner)
        attempts = self._start_attempts(core, executor, root, ("T1",))
        response = adapter.request(fixtures._order_from_plan(core, "T1", attempts["T1"]))
        self.assertEqual(response.status, "accepted")
        self.assertTrue(fixtures._wait_for(lambda: core.snapshot().tasks["T1"]["state"] == "recovering"))
        result = store.get_result(fixtures._request_key(core, attempts["T1"]))
        self.assertEqual(result["status"], "FAIL")
