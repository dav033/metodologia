"""Small valid requests shared by M2 contract and policy tests."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from bt_scheduler_decision import (
    Candidate,
    DecisionRequest,
    RouteHistory,
    TaskFacts,
    account_reference,
    candidate_route_id,
)
from bt_scheduler_decision.bench_local import (
    paired_accuracy_bootstrap,
    select_calibration_cutoff,
)
from bt_scheduler_decision.gates import (
    decision_facts_are_ambiguous,
    laya_choice_passes_runtime_gate,
)

PLAN_HASH = "a" * 64


def synthetic_quality_artifacts(directory: str | Path, checkpoint_revision: str) -> tuple[Path, Path, Path, Path, Path]:
    """Build deliberately synthetic evidence that production must never authorize."""
    root = Path(directory)
    repo_root = Path(__file__).resolve().parents[4]
    evidence_root = repo_root / "bitacora/metodologia/requirements/REQ-013-scheduler-m2-decision-engine-with-local"
    corpus_raw = (evidence_root / "fixtures-v1.json").read_bytes()
    manifest_raw = (evidence_root / "fixture-manifest-v1.json").read_bytes()
    (root / "corpus.json").write_bytes(corpus_raw)
    (root / "manifest.json").write_bytes(manifest_raw)
    corpus = json.loads(corpus_raw)
    manifest = json.loads(manifest_raw)
    cases_by_id = {row["case_id"]: row for row in corpus["cases"]}
    by_split = {"calibration": [cases_by_id[item] for item in manifest["calibration_case_ids"]],
                "held_out": [cases_by_id[item] for item in manifest["held_out_case_ids"]]}

    def measured_rows(split: str) -> list[dict]:
        return [{"case_id": case["case_id"], "family": case["family"],
                 "predicted_route_id": case["oracle_route_id"], "answer_confidence": 0.8, "eligible_choice": True,
                 "matches_oracle": True,
                 "baseline_matches_oracle": case["deterministic_route_id"] == case["oracle_route_id"],
                 "usage": {"truncated": False}, "error": None}
                for case in by_split[split]]

    calibration_rows = measured_rows("calibration")
    selected_stats = select_calibration_cutoff(calibration_rows)
    calibration_runs = []
    decision_rows = []
    for name in ("english", "multilingual", "typed-decisions"):
        revision = checkpoint_revision if name == "typed-decisions" else f"{name}-revision"
        checksum = hashlib.sha256(name.encode()).hexdigest()
        calibration_runs.append({"checkpoint": name, "checkpoint_revision": revision,
                                 "checkpoint_sha256": checksum, "requested_device": "cuda",
                                 "cases": calibration_rows})
        decision_rows.append({"checkpoint": name, "revision": revision, "sha256": checksum,
                              "confidence_gate": {"minimum_retained": 50, "cutoff": selected_stats.cutoff,
                                                  "retained": selected_stats.retained,
                                                  "correct": selected_stats.correct, "accuracy": selected_stats.accuracy,
                                                  "wilson_lower_bound": selected_stats.wilson_lower_bound,
                                                  "deterministic_accuracy": selected_stats.deterministic_accuracy,
                                                  "valid_choices": 100, "hard_filter_violations": 0,
                                                  "truncated_choices": 0, "passed": True}})
    calibration_results = {"schema_version": 1, "split": "calibration", "held_out_touched": False,
                          "frozen_before_first_laya_call": True, "dataset_sha256": manifest["dataset_sha256"],
                          "dataset_version": manifest["dataset_version"], "results": calibration_runs}
    calibration_results_raw = (json.dumps(calibration_results, sort_keys=True) + "\n").encode()
    (root / "calibration-results.json").write_bytes(calibration_results_raw)
    calibration = {
        "schema_version": 1, "held_out_touched": False, "gate_enabled": True,
        "gate_reason": "calibration_gate_passed", "diagnostic_only_when_disabled": False,
        "checkpoint": "typed-decisions", "checkpoint_repository": "official/test",
        "checkpoint_revision": checkpoint_revision, "checkpoint_sha256": hashlib.sha256(b"typed-decisions").hexdigest(),
        "calibration_version": "test-calibration-v1", "confidence_cutoff": selected_stats.cutoff,
        "dataset_version": manifest["dataset_version"], "dataset_sha256": manifest["dataset_sha256"],
        "calibration_result_sha256": hashlib.sha256(calibration_results_raw).hexdigest(),
        "device": "cuda", "label_protocol": manifest["label_protocol"],
        "labeler_independence": manifest["labeler_independence"], "checkpoint_results": decision_rows,
    }
    calibration_path = root / "calibration-decision.json"
    calibration_raw = (json.dumps(calibration, sort_keys=True) + "\n").encode()
    calibration_path.write_bytes(calibration_raw)
    held_out_rows = measured_rows("held_out")
    heldout_paired = []
    for case, row in zip(by_split["held_out"], held_out_rows, strict=True):
        ambiguous = decision_facts_are_ambiguous(case["classifications"], evidence_complete=True,
                                                  dependency_count=0, has_shared_resources=False)
        accepted = laya_choice_passes_runtime_gate(quality_authorized=True, task_ambiguous=ambiguous,
                                                    candidate_eligible=True, answer_confidence=0.8,
                                                    cutoff=selected_stats.cutoff)
        hybrid_route = row["predicted_route_id"] if accepted else case["deterministic_route_id"]
        hybrid_correct = hybrid_route == case["oracle_route_id"]
        row.update({"task_ambiguous": ambiguous, "hybrid_used_laya": accepted,
                    "hybrid_route_id": hybrid_route})
        heldout_paired.append({"hybrid_correct": hybrid_correct,
                               "baseline_correct": case["deterministic_route_id"] == case["oracle_route_id"]})
    interval = paired_accuracy_bootstrap(heldout_paired)
    hybrid_accuracy = sum(row["hybrid_correct"] for row in heldout_paired) / len(heldout_paired)
    held_out = {
        "benchmark": "scheduler-m2-local-held-out-selection-v1", "split": "held_out",
        "schema_version": 1, "dataset_sha256": manifest["dataset_sha256"],
        "dataset_version": manifest["dataset_version"],
        "frozen_calibration_decision_sha256": hashlib.sha256(calibration_raw).hexdigest(),
        "checkpoint": "typed-decisions", "checkpoint_revision": checkpoint_revision,
        "checkpoint_sha256": calibration["checkpoint_sha256"], "requested_device": "cuda",
        "resamples": 10_000, "seed": 20261014,
        "laya_gate_authorized": True,
        "summary": {"cases": 100, "valid_choices": 100, "invalid_or_failed": 0,
                    "hard_filter_violations": 0, "confidence_gate_enabled": True,
                    "confidence_cutoff": selected_stats.cutoff, "ambiguity_filter_applied": True,
                    "ambiguity_gate_violations": 0, "held_out_labeler_is_human": False,
                    "truncated_choices": 0, "production_hybrid_accuracy": hybrid_accuracy,
                    "production_hybrid_paired_delta_95ci": list(interval)},
        "cases": held_out_rows,
    }
    held_out_path = root / "held-out.json"
    held_out_path.write_text(json.dumps(held_out, sort_keys=True) + "\n", encoding="utf-8")
    return calibration_path, root / "calibration-results.json", held_out_path, root / "corpus.json", root / "manifest.json"


def task_facts(*, task_id: str = "T1", brief: str = "Update the validated scheduler route safely.",
               classifications: dict | None = None, evidence: dict | None = None,
               acceptance_criteria: tuple[str, ...] = ("The route is persisted and reviewable.",)) -> TaskFacts:
    dimensions = {"complexity": "medium", "scope": "small_change", "estimated_minutes": 30,
                  "risk": "low", "coupling": "low", "confidence": "high"}
    dimensions.update(classifications or {})
    evidence_values = evidence if evidence is not None else {
        name: {"justification": f"Inspected concrete {name} factors before this task.",
               "evidence": [f"spec:REQ-013#{name}"]}
        for name in ("complexity", "scope", "duration", "risk", "coupling", "confidence")
    }
    return TaskFacts(task_id=task_id, brief=brief, classifications=dimensions, classification_evidence=evidence_values,
                     dependencies=("T0",), acceptance_criteria=acceptance_criteria,
                     verification=({"type": "command", "value": "python -m unittest"},),
                     shared_resources=("scheduler-contract",), expected_paths=("skill/scripts/bt_scheduler_*/**",))


def candidate(*, provider: str = "claude", model: str = "sonnet", profile: str = "work", effort: str | None = "high",
              rank: int | None = 0, quota_status: str = "available", observed_at: float = 99.0,
              valid_until: float = 120.0, used_percent: float = 20.0, source_status: str = "available",
              history: RouteHistory | None = None) -> Candidate:
    route_id = candidate_route_id(provider, model, profile, effort)
    return Candidate(route_id, provider, model, profile, account_reference(f"{provider}:shared-account"), effort,
                     source_status, (), True, "valid", "available", quota_status, observed_at, valid_until,
                     used_percent, rank, history or RouteHistory())


def request(*, task: TaskFacts | None = None, candidates: tuple[Candidate, ...] | None = None,
            requested_at: float = 100.0) -> DecisionRequest:
    return DecisionRequest("REQ-013", 1, PLAN_HASH, 2, requested_at, task or task_facts(),
                           (candidate(),) if candidates is None else candidates, "m2-policy-1", None)
