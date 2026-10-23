"""Checks the frozen M2 API and evaluation contract stays internally coherent."""
from __future__ import annotations

import inspect
import json
import unittest
from pathlib import Path

import bt_scheduler_decision as public_api
from bt_scheduler_decision import (
    API_VERSION,
    DecisionLedger,
    DecisionRequest,
    LearningSnapshot,
    LearningSnapshotStore,
    resolve_executor_reference,
)

CONTRACT = Path(__file__).resolve().parents[1] / "bt_scheduler_decision" / "api-contract.json"


class DecisionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    def test_request_has_approved_plan_and_explicit_quota_state(self):
        request = self.contract["decision_request"]
        self.assertEqual(self.contract["contract_version"], "1.2.0")
        self.assertEqual(API_VERSION, self.contract["contract_version"])
        self.assertEqual(self.contract["compatible_record_versions"], ["1.0.0", "1.1.0", "1.2.0"])
        self.assertIn("checkpoint_revision", request["nullable"])
        self.assertIs(inspect.signature(DecisionRequest).parameters["checkpoint_revision"].default,
                      inspect.Parameter.empty)
        self.assertIn("plan_sha256", request["required"])
        self.assertEqual(request["max_task_nested_json_nodes"], 8192)
        self.assertEqual(request["max_task_nested_json_bytes"], 262144)
        self.assertEqual(request["max_task_json_key_characters"], 128)
        self.assertRegex("0" * 64, request["plan_sha256_pattern"])
        self.assertIn("quota_status", request["candidate_required"])
        self.assertIn("account_ref", request["candidate_required"])
        self.assertEqual(set(request["quota_states"]), {"available", "unknown", "stale", "exhausted"})
        self.assertIn("quota_valid_until is finite and > requested_at", request["available_quota_invariants"])
        self.assertIn("task_id", request["task_required"])
        self.assertIn("task_id", request["validated_task_input_digest_fields"])
        self.assertIn("history_required", request)
        self.assertIn("median_total_tokens", request["history_required"])
        self.assertIn("estimated", request["history_source_quality"])
        self.assertEqual(request["max_history_observations_per_field"], 1000000000)
        self.assertEqual(request["max_median_total_tokens"], 1000000000000)
        self.assertEqual(request["max_baseline_rank"], 255)
        self.assertEqual(request["classification_evidence_shape"]["never_store"],
                         ["justification", "raw_reference_values"])

    def test_selection_policy_is_fail_closed_and_keeps_the_router_reference(self):
        policy = self.contract["selection_policy"]
        self.assertIn("quota_status is available with a fresh finite observation", policy["hard_filters"])
        self.assertIn("capacity_unknown", policy["capacity_semantics"])
        self.assertEqual(policy["provider_inventory_source"], "existing bt_agents.candidates; no second provider catalog")
        history = policy["history_scoring"]
        self.assertEqual(history["prior"], "Beta(2,2)")
        self.assertEqual(history["minimum_verified_samples"], 5)
        self.assertTrue(history["does_not_override_baseline_rank"])
        self.assertFalse(history["is_future_success_probability"])

    def test_decision_ledger_has_fixed_bounds_and_read_only_reference_contract(self):
        ledger = self.contract["decision_ledger"]
        self.assertIn("original DecisionRequest", ledger["write_input"])
        self.assertIn("ValidatedRequest rejected", ledger["write_input"])
        self.assertEqual(ledger["maximum_records"], 100000)
        self.assertEqual(ledger["maximum_record_bytes"], 131072)
        self.assertIn("schema version 3", ledger["storage"])
        self.assertIn("through schema 2 learning_snapshots to schema 3 batch_decisions",
                      ledger["schema_1_migration"])
        self.assertIn("read-only schema-1 opens remain valid", ledger["schema_1_migration"])
        self.assertIn("read-only schema-2 opens remain valid", ledger["schema_2_migration"])
        self.assertIn("BEGIN IMMEDIATE", ledger["transaction"])
        self.assertEqual(ledger["file_mode_octal"], "0600")
        self.assertIn("read-only", ledger["executor_resolution"])
        self.assertTrue(callable(DecisionLedger))
        self.assertTrue(callable(LearningSnapshot))
        self.assertTrue(callable(LearningSnapshotStore))
        self.assertTrue(callable(resolve_executor_reference))
        record = self.contract["decision_record"]
        self.assertIn("baseline_route", record["factor_code_values"])
        self.assertIn("laya_choice_accepted", record["factor_code_values"])
        self.assertIn("laya_timeout", record["fallback_reason_values"])

    def test_batch_decision_ledger_has_a_versioned_public_surface_and_fixed_bounds(self):
        batch = self.contract["batch_decision"]
        self.assertEqual(batch["schema_version"], API_VERSION)
        self.assertEqual(batch["store"], "DecisionLedger.batch_decisions")
        self.assertEqual(batch["store_type"], "BatchDecisionStore")
        self.assertEqual(batch["methods"], ["persist", "get"])
        self.assertTrue(isinstance(inspect.getattr_static(DecisionLedger, "batch_decisions"), property))
        surface = batch["public_surface"]
        self.assertEqual(surface["planner"], "plan_ready_batch")
        self.assertEqual(surface["store_type"], batch["store_type"])
        for name in (*surface["input_types"], *surface["result_types"], surface["planner"], surface["store_type"]):
            self.assertTrue(callable(getattr(public_api, name)), name)
            self.assertIn(name, public_api.__all__)
        self.assertEqual(batch["maximum_tasks"], 128)
        self.assertEqual(batch["maximum_candidates_and_account_edges"], 4096)
        self.assertEqual(batch["maximum_batch_decisions"], 10000)
        self.assertEqual(batch["maximum_plan_bytes"], 2097152)
        self.assertIn("assignments", batch["stored_fields"])
        self.assertEqual(batch["assignment_reasons"], ["route_policy_preferred", "account_capacity_alternative"])
        self.assertIn("route_exclusions", batch["stored_fields"])
        self.assertTrue(batch["immutability"].startswith("append-only"))

    def test_shadow_comparison_is_opt_in_replayable_and_side_effect_free(self):
        shadow = self.contract["shadow_comparison"]
        self.assertEqual(shadow["schema_version"], API_VERSION)
        self.assertEqual(shadow["policy_version"], public_api.SHADOW_POLICY_VERSION)
        self.assertEqual(shadow["disabled_result"], None)
        self.assertFalse(shadow["durable_persistence"])
        self.assertEqual(shadow["side_effects"], {
            "dispatch_performed": False,
            "reservations_created": False,
            "task_state_changed": False,
            "ledger_written": False,
            "provider_called": False,
        })
        for name in shadow["result_types"] + [shadow["api"]]:
            self.assertTrue(callable(getattr(public_api, name)), name)
            self.assertIn(name, public_api.__all__)
        self.assertEqual(shadow["stable_difference_codes"], [
            "same_assignment", "route_changed", "assignment_added", "assignment_removed",
            "assignment_reason_changed", "same_unassignment", "unassignment_reason_changed",
        ])

    def test_learning_snapshots_are_versioned_bounded_and_content_addressed(self):
        snapshot = self.contract["learning_snapshot"]
        self.assertEqual(snapshot["schema_version"], "1.2.0")
        self.assertEqual(snapshot["maximum_snapshots"], 10000)
        self.assertEqual(snapshot["maximum_snapshot_bytes"], 32768)
        self.assertIn("created_at", snapshot["stored_fields"])
        self.assertEqual(snapshot["time_units"]["learning_cutoff"], "finite UTC epoch seconds")
        self.assertIn("source_fingerprint", snapshot)
        self.assertIn("append-only", snapshot["immutability"])
        self.assertIn("raw events", snapshot["redaction"])

    def test_idempotency_excludes_wall_clock_but_binds_all_decision_sources(self):
        idem = self.contract["idempotency"]
        self.assertEqual(idem["algorithm"], "sha256")
        for field in ("plan_sha256", "validated_task_input_digest", "candidate_quota_telemetry_snapshot",
                      "policy_version", "checkpoint_revision"):
            self.assertIn(field, idem["canonical_fields"])
        self.assertIn("task_id", self.contract["decision_request"]["validated_task_input_digest_fields"])
        self.assertFalse(idem["request_time_included"])

    def test_executor_reference_is_content_addressed_and_selection_scoped(self):
        reference = self.contract["executor_reference"]
        self.assertTrue(reference["resolve_only_selected_route"])
        self.assertEqual(reference["format"], "m2:v1:<decision_sha256>:<route_sha256>")
        self.assertEqual(self.contract["route_identity"]["canonical_fields"],
                         ["provider", "model", "profile", "effort"])
        self.assertIn("account_ref", self.contract["decision_record"]["route_fields"])
        self.assertIn("quota_observed_at", self.contract["decision_record"]["route_fields"])
        self.assertIn("quota_used_percent", self.contract["decision_record"]["route_fields"])
        self.assertIn("quota_valid_until", self.contract["decision_record"]["route_fields"])
        self.assertIn("quota_snapshot_sha256", self.contract["decision_record"]["required"])
        self.assertIn("alternatives", self.contract["decision_record"]["required"])
        self.assertEqual(self.contract["m1_batch"]["max_proposals"], "AssignmentRequest.free_slots")
        self.assertTrue(self.contract["m1_batch"]["m1_remains_final_authority"])

    def test_quota_observation_contract_is_versioned_bounded_and_cache_only(self):
        quota = self.contract["quota_observation"]
        self.assertEqual(quota["schema_version"], "1.2.0")
        self.assertIn("account_ref", quota["required"])
        self.assertIn("window_id", quota["required"])
        self.assertIn("resets_at", quota["required"])
        self.assertEqual(quota["max_validity_seconds"], 86400)
        self.assertFalse(quota["performs_network_access"])
        self.assertEqual(quota["null_reset_provider"], "claude")
        self.assertEqual(quota["source_by_provider"]["antigravity"], "antigravity_cache")

    def test_demand_contract_separates_units_and_requires_clean_attribution(self):
        demand = self.contract["quota_demand"]
        self.assertEqual(demand["schema_version"], self.contract["contract_version"])
        self.assertIn("sample_count", demand["estimate_fields"])
        self.assertIn("attribution", demand["sample_fields"])
        self.assertEqual(demand["units"], ["provider_tokens", "quota_percentage_points"])
        self.assertIn("one active task and explicit evidence that external usage is absent",
                      demand["attribution_requirements"])
        self.assertIn("unknown with attribution_unknown", demand["contamination_result"])
        self.assertTrue(demand["never_convert_between_units"])
        self.assertEqual(demand["max_estimate_ttl_seconds"], 86400)

    def test_batch_quota_contract_deduplicates_shared_accounts_and_requires_every_window(self):
        batch = self.contract["batch_quota"]
        self.assertEqual(batch["schema_version"], API_VERSION)
        self.assertEqual(batch["effective_account_key"], ["provider", "account_ref"])
        self.assertFalse(batch["durable_reservations"])
        self.assertTrue(batch["m1_remains_final_authority"])
        self.assertIn("every declared base and model-specific window", batch["route_eligibility"])
        self.assertIn("assessment", batch["route_result_fields"])
        self.assertIn("exhausted_windows", batch["assessment_fields"])

    def test_confidence_and_privacy_do_not_claim_more_than_the_evidence(self):
        confidence = self.contract["confidence"]
        self.assertIn("never real-world task-success probability", confidence["semantics"])
        self.assertEqual(confidence["source_semantics"]["laya_answer_confidence"],
                         "laya_calibrated_choice_score")
        self.assertFalse(confidence["persist_arbitrary_model_explanation"])
        privacy = self.contract["privacy"]
        for key in ("persist_task_brief", "persist_evidence_justifications", "persist_acceptance_or_verification_text",
                    "persist_credentials_or_profile_environment", "persist_raw_model_output"):
            self.assertFalse(privacy[key], key)
        self.assertTrue(privacy["persist_task_brief_sha256"])

    def test_quality_gate_is_fixed_and_has_all_five_required_families(self):
        gate = self.contract["laya_quality_gate"]
        self.assertGreaterEqual(gate["calibration_minimum_cases"], 100)
        self.assertGreaterEqual(gate["held_out_minimum_cases"], 100)
        self.assertEqual(set(gate["family_minimums"]), set(gate["held_out_families"]))
        self.assertTrue(all(count >= 20 for count in gate["family_minimums"].values()))
        self.assertEqual(gate["paired_bootstrap_resamples"], 10000)
        self.assertEqual(gate["maximum_hard_filter_violations"], 0)
        self.assertEqual(gate["required_paired_accuracy_improvement_lower_bound"], "positive")
        self.assertTrue(gate["fixture_protocol"]["labels_must_be_frozen_before_laya"])
        self.assertTrue(gate["fixture_protocol"]["split_case_ids_must_be_disjoint"])
        self.assertEqual(gate["bootstrap_seed"], 20261014)
        self.assertEqual(gate["bootstrap_method"].split(";", 1)[0],
                         "two-sided 95% paired percentile interval")
        manifest = gate["fixture_protocol"]
        self.assertTrue({"dataset_sha256", "frozen_before_first_laya_call", "label_protocol",
                         "labeler_independence", "calibration_case_ids", "held_out_case_ids"}
                        <= set(manifest["manifest_required_fields"]))
        self.assertEqual(manifest["duplicate_canonical_task_digests_across_splits"], 0)


if __name__ == "__main__":
    unittest.main()
