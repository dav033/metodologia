from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import bt_agents
import bt_plan_adapter as adapter
import bt_scheduler_adapter as scheduler_adapter
import bt_scheduler_decision_adapter as m2
import bt_scheduler_quality.contracts as m6_contracts
from bt_scheduler_core.errors import SchedulerError
from bt_scheduler_core.plan import load_plan
from bt_scheduler_quality import QualityError, VerifyRequest
from bt_scheduler_quality.policy import QualityPolicy, compile_verification
from test_plan_integration import Isolated, planner

m1_plan = scheduler_adapter.m1_plan


class PlanContractCompatibility(Isolated):
    def _write(self, plan: dict) -> bytes:
        encoded = planner.dumps(plan).encode("utf-8")
        (self.rdir / "PLAN.json").write_bytes(encoded)
        return encoded

    def _legacy_plan(self) -> tuple[dict, bytes]:
        plan = self.good_plan()
        plan["schema_version"] = "1.1.0"
        plan.pop("requirements", None)
        for task in plan["tasks"]:
            task.pop("covers", None)
            task.pop("kind", None)
            for verification in task.get("verification", []):
                verification.pop("category", None)
        return plan, self._write(plan)

    def test_schema_1_2_requires_and_forwards_validated_kind_and_category(self):
        plan = self.good_plan()
        plan["tasks"][0]["kind"] = "docs"
        raw = self._write(plan)

        loaded = load_plan(raw, approved_sha256=hashlib.sha256(raw).hexdigest())

        self.assertEqual(loaded.task("T1").meta["kind"], "docs")
        verification = loaded.task("T1").verification[0]
        self.assertIn(verification["category"], {"static", "functional", "integration", "regression", "product"})

        for field, value in (("kind", "unknown"), ("kind", None)):
            invalid = json.loads(raw)
            invalid["tasks"][0][field] = value
            encoded = json.dumps(invalid).encode("utf-8")
            with self.subTest(field=field, value=value), self.assertRaises(SchedulerError):
                load_plan(encoded, approved_sha256=hashlib.sha256(encoded).hexdigest())

        invalid = json.loads(raw)
        invalid["tasks"][0]["verification"][0]["category"] = "unknown"
        encoded = json.dumps(invalid).encode("utf-8")
        with self.assertRaises(SchedulerError):
            load_plan(encoded, approved_sha256=hashlib.sha256(encoded).hexdigest())

        for field in ("kind", "category"):
            invalid = json.loads(raw)
            if field == "kind":
                invalid["tasks"][0].pop("kind")
            else:
                invalid["tasks"][0]["verification"][0].pop("category")
            encoded = json.dumps(invalid).encode("utf-8")
            with self.subTest(missing=field), self.assertRaises(SchedulerError):
                load_plan(encoded, approved_sha256=hashlib.sha256(encoded).hexdigest())

    def test_legacy_kind_stays_title_inferred_and_legacy_category_is_absent(self):
        plan, _raw = self._legacy_plan()
        plan["tasks"][0]["kind"] = "audit"  # additive field from an unversioned producer is ignored by M1
        plan["tasks"][0]["title"] = "Write documentation"
        raw = self._write(plan)
        loaded = load_plan(raw, approved_sha256=hashlib.sha256(raw).hexdigest())

        meta = loaded.task("T1").meta
        self.assertNotIn("kind", meta)
        _facts, kind, _classifications = m2.task_facts(
            "T1", meta, (), ("criteria",), (), (), ()
        )
        self.assertEqual(kind, bt_agents.infer_kind("Write documentation"))
        self.assertEqual(kind, "docs")
        self.assertNotIn("category", loaded.task("T1").verification[0])

    def test_m2_prefers_valid_explicit_kind_over_title_inference(self):
        _facts, kind, _classifications = m2.task_facts(
            "T1", {"title": "Write documentation", "kind": "audit"}, (), ("criteria",), (), (), ()
        )

        self.assertEqual(kind, "audit")

    def test_legacy_fixture_routing_golden_is_unchanged(self):
        fixture = Path(bt_agents.__file__).parent / "bt_scheduler_core" / "tests" / "fixtures" / "plan.example.json"
        plan = json.loads(fixture.read_text(encoding="utf-8"))
        self.assertEqual(plan["schema_version"], "1.0.0")
        task = next(item for item in plan["tasks"] if item["id"] == "T1")
        _facts, kind, route_facts = m2.task_facts(
            task["id"], task, task["after"], task["acceptance_criteria"], task["verification"],
            task["shared_resources"], task["expected_paths"]
        )
        self.assertEqual(kind, "implement")
        self.assertEqual(route_facts["risk"], "high")
        self.assertNotIn("review_axis", route_facts)
        self.assertEqual(m2._route_role(kind, route_facts), "implementer")
        self.assertEqual(m2._route_options("claude", 0, kind), (("sonnet", "medium"),))

    def test_consumer_capabilities_report_legacy_support_and_unknown_future_versions(self):
        for version in ("1.0.0", "1.1.0"):
            with self.subTest(schema_version=version):
                self.assertTrue(scheduler_adapter.downstream_compatibility(version)["supported"])
        self.assertFalse(scheduler_adapter.downstream_compatibility("1.2.1")["supported"])

    def test_malformed_consumer_capability_marker_fails_closed(self):
        with patch.object(m6_contracts, "PLAN_SCHEMA_CAPABILITIES", frozenset({"1.2.0", "invalid"})):
            report = scheduler_adapter.downstream_compatibility("1.2.0")

        self.assertFalse(report["supported"])
        self.assertEqual(report["consumers"]["M6"], {
            "status": "unknown", "supported_schema_versions": []
        })

    def test_m6_hashes_category_and_keeps_the_legacy_hash_unchanged(self):
        fixture = Path(m6_contracts.__file__).parent / "tests" / "fixtures" / "verify-order-pass.json"
        legacy = json.loads(fixture.read_text(encoding="utf-8"))
        legacy_request = VerifyRequest.from_mapping(legacy)

        self.assertEqual(legacy_request.input_hash, "0a1fbb8a208701a0029f073187bc16229111db8ce252281ff46557e6e9eaef3f")
        self.assertNotIn("category", legacy_request.to_dict()["verification"][0])

        categorized = json.loads(json.dumps(legacy))
        categorized["verification"][0]["category"] = "integration"
        request = VerifyRequest.from_mapping(categorized)

        self.assertEqual(request.verification[0].category, "integration")
        self.assertEqual(request.to_dict()["verification"][0]["category"], "integration")
        self.assertNotEqual(request.input_hash, legacy_request.input_hash)
        with tempfile.TemporaryDirectory() as snapshot:
            policy = QualityPolicy()
            self.assertEqual(compile_verification(legacy_request, Path(snapshot), policy),
                             compile_verification(request, Path(snapshot), policy))

        categorized["verification"][0]["category"] = "unknown"
        with self.assertRaises(QualityError):
            VerifyRequest.from_mapping(categorized)

    def test_unknown_consumer_capability_blocks_approval_handoff_launch_and_resume(self):
        self.good_plan()
        self.set_status("review")

        with patch.object(m6_contracts, "PLAN_SCHEMA_CAPABILITIES", None):
            compatibility = scheduler_adapter.plan_compatibility_report(self.rdir)
            with self.assertRaisesRegex(SystemExit, "PLAN_CONSUMER_INCOMPATIBLE"):
                import bt_rounds
                bt_rounds.plan_decide(self.rdir, True, "", "compat-test")
            self.assertEqual(planner.plan_status(self.rdir), "review")
            self.assertEqual(planner.list_revisions(self.rdir), [])
            self.assertEqual(adapter.run_cli("freeze", self.rdir, emit=lambda _message: None,
                                             compatibility_report=compatibility), 2)
            self.assertEqual(planner.list_revisions(self.rdir), [])

            self.assertTrue(any("PLAN_CONSUMER_INCOMPATIBLE" in problem
                                for problem in adapter.handoff_problems(
                                    self.rdir, compatibility_report=compatibility
                                )))
            self.set_status("approved")
            with self.assertRaisesRegex(SystemExit, "PLAN_CONSUMER_INCOMPATIBLE"):
                adapter.freeze_approved(self.rdir, compatibility_report=compatibility)
            self.assertEqual(planner.list_revisions(self.rdir), [])
            self.assertIn("PLAN_CONSUMER_INCOMPATIBLE", adapter.launch_problem(
                self.rdir, freeze=True, forced=True, compatibility_report=compatibility
            ) or "")
            self.assertEqual(planner.list_revisions(self.rdir), [])
            self.assertIn("PLAN_CONSUMER_INCOMPATIBLE", adapter.resume_problem(
                self.rdir, {}, compatibility_report=compatibility
            ) or "")

            messages: list[str] = []
            self.assertEqual(adapter.run_cli("compat", self.rdir, emit=messages.append,
                                             compatibility_report=compatibility), 0)
            report = json.loads("\n".join(messages))
            compatibility = report["downstream_compatibility"]
            self.assertFalse(compatibility["supported"])
            self.assertEqual(compatibility["planner"]["status"], "supported")
            self.assertEqual(set(compatibility["consumers"]), {"M1", "M2", "M6"})
            self.assertEqual(compatibility["consumers"]["M6"]["status"], "unknown")

        for module in (m1_plan, m2, m6_contracts):
            with self.subTest(consumer=module.__name__), patch.object(module, "PLAN_SCHEMA_CAPABILITIES", None):
                self.assertFalse(scheduler_adapter.downstream_compatibility()["supported"])

    def test_rollback_restores_frozen_1_1_bytes_without_rewriting_hash(self):
        _legacy, legacy_bytes = self._legacy_plan()
        self.set_status("approved")
        entry = planner.approve_freeze(self.rdir, adapter.plan_id(self.rdir), adapter.APPROVED_STATES)
        frozen = planner.list_revisions(self.rdir)
        self.assertEqual(frozen[0]["sha256"], entry["sha256"])

        self.good_plan()
        with patch.object(m6_contracts, "PLAN_SCHEMA_CAPABILITIES", frozenset()):
            compatibility = scheduler_adapter.plan_compatibility_report(self.rdir)
            self.assertIn("PLAN_CONSUMER_INCOMPATIBLE", adapter.launch_problem(
                self.rdir, freeze=False, compatibility_report=compatibility
            ) or "")

        (self.rdir / "PLAN.json").write_bytes(legacy_bytes)
        with patch.object(m6_contracts, "PLAN_SCHEMA_CAPABILITIES", frozenset()):
            self.assertIsNone(adapter.launch_problem(
                self.rdir, freeze=False, compatibility_report=scheduler_adapter.plan_compatibility_report(self.rdir)
            ))

        self.assertEqual((self.rdir / "PLAN.json").read_bytes(), legacy_bytes)
        self.assertEqual(planner.list_revisions(self.rdir)[0]["sha256"], entry["sha256"])

    def test_scheduler_rechecks_capability_against_the_frozen_revision(self):
        self.good_plan()
        self.set_status("approved")
        entry = planner.approve_freeze(self.rdir, adapter.plan_id(self.rdir), adapter.APPROVED_STATES)
        self.assertEqual(entry["revision"], 1)

        # The mutable working plan is legacy, but Scheduler must gate the frozen 1.2.0 revision it will load.
        self._legacy_plan()
        with patch.object(m6_contracts, "PLAN_SCHEMA_CAPABILITIES", None), \
                self.assertRaises(SchedulerError) as context:
            scheduler_adapter.approved_plan(self.rdir)

        self.assertEqual(context.exception.code, "PLAN_CONSUMER_INCOMPATIBLE")
        self.assertIn("schema 1.2.0", str(context.exception))


if __name__ == "__main__":
    unittest.main()
