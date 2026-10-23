"""Missing phone evidence cannot hide an already confirmed blocking product finding."""
import unittest

from bt_scheduler_quality.tests import test_adapter as support


class ManualAuditFindingsTests(unittest.TestCase):
    _system = support.M6M1AdapterTests._system
    _start_attempts = support.M6M1AdapterTests._start_attempts

    def start(self, findings):
        build = support._task("T1", "python3 build.py")
        build.update(kind="implement")
        build["verification"][0]["category"] = "functional"
        audit = support._task("T2", "test -s audit.md")
        audit.update(kind="audit", after=["T1"], expected_paths=["docs/audit.md", "docs/audit.findings.json"])
        audit["verification"][0]["category"] = "functional"
        audit["acceptance_criteria"].append("physical phone observations")
        audit["verification"].append({"type": "manual", "value": "Observe camera and keyboard on a physical phone",
            "purpose": "physical phone observations", "expected": "observations recorded", "category": "product"})
        system = self._system([build, audit], schema_version="1.2.0", max_attempts=2,
            read_ledger=lambda *_: support.M6M1AdapterTests._ledger(*findings), read_changes=lambda _: ())
        root, core, _, executor, store, port = system
        observations = []
        port.publish_audit_observation = lambda _task, _attempt, data: observations.append(data)
        self._start_attempts(core, executor, root, ("T1",))
        core.step()
        self.assertTrue(support._wait_for(lambda: core.snapshot().tasks["T1"]["state"] == "completed"))
        self._start_attempts(core, executor, root, ("T2",))
        core.step()
        return core, store, observations

    def test_a_confirmed_high_finding_reworks_its_producer_before_waiting_for_phone_evidence(self):
        core, _, observations = self.start([{"id": "F1", "severity": "high", "status": "open",
                              "summary": "photo send control is disabled", "tasks": ["T1"]}])
        self.assertTrue(support._wait_for(lambda: core.snapshot().tasks["T1"]["state"] != "completed"))
        self.assertIn("rework_requested", [entry.kind for entry in core.audit_log()])
        self.assertTrue(any(item["gate_status"] == "evaluated" and not item["not_run_checks"] for item in observations))

    def test_a_clean_audit_still_waits_for_the_missing_phone_observations(self):
        core, store, _ = self.start([])
        self.assertTrue(support._wait_for(lambda: bool(store.list_reviews())))
        self.assertEqual(core.snapshot().tasks["T1"]["state"], "completed")
        self.assertNotEqual(core.snapshot().tasks["T2"]["state"], "completed")
