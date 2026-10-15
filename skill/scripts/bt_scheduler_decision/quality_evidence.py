"""Revalidate frozen Laya quality evidence before it can authorize production inference."""
from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .bench_local import paired_accuracy_bootstrap, select_calibration_cutoff
from .gates import decision_facts_are_ambiguous, laya_choice_passes_runtime_gate

FAMILIES = ("ambiguous_tradeoff", "history", "quota_capacity", "resource_dependency", "risk_effort")
MIN_CASES_PER_SPLIT = 100
MIN_CASES_PER_FAMILY = 20
MIN_CALIBRATION_RETAINED = 50
BOOTSTRAP_RESAMPLES = 10_000
BOOTSTRAP_SEED = 20261014
CHECKPOINTS = ("english", "multilingual", "typed-decisions")
MAX_EVIDENCE_ARTIFACT_BYTES = 16 * 1024 * 1024


class QualityEvidenceError(ValueError):
    """Calibration or held-out evidence is missing, inconsistent, or did not pass."""


@dataclass(frozen=True)
class QualityEvidence:
    checkpoint: str
    checkpoint_revision: str
    calibration_version: str
    confidence_cutoff: float
    artifacts_sha256: str


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise QualityEvidenceError("quality artifact contains a duplicate JSON key")
        result[key] = value
    return result


def _reject_nonfinite(_value: str) -> None:
    raise QualityEvidenceError("quality artifact contains a non-finite number")


def _load(path: Path) -> tuple[dict[str, Any], bytes]:
    _require(path.stat().st_size <= MAX_EVIDENCE_ARTIFACT_BYTES,
             "quality artifact exceeds the 16 MiB size limit")
    raw = path.read_bytes()
    _require(len(raw) <= MAX_EVIDENCE_ARTIFACT_BYTES, "quality artifact exceeds the 16 MiB size limit")
    value = json.loads(raw, object_pairs_hook=_unique_pairs, parse_constant=_reject_nonfinite)
    if not isinstance(value, dict):
        raise QualityEvidenceError("quality artifact must be a JSON object")
    return value, raw


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise QualityEvidenceError(reason)


def _is_finite_number(value: object) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except (OverflowError, TypeError, ValueError):
        return False


def _same_number(actual: object, expected: float | None) -> bool:
    return actual is None and expected is None or \
        _is_finite_number(actual) and _is_finite_number(expected) and actual == expected


def _validate_manifest_and_corpus(manifest: dict[str, Any], manifest_raw: bytes,
                                  corpus: dict[str, Any], corpus_raw: bytes) \
        -> tuple[dict[str, dict[str, Any]], dict[str, list[str]]]:
    contract_path = Path(__file__).with_name("api-contract.json")
    api_contract, _ = _load(contract_path)
    gate_contract = api_contract.get("laya_quality_gate")
    frozen_dataset = gate_contract.get("frozen_dataset") if isinstance(gate_contract, dict) else None
    dataset_sha = manifest.get("dataset_sha256")
    dataset_version = manifest.get("dataset_version")
    _require(isinstance(frozen_dataset, dict) and
             hashlib.sha256(manifest_raw).hexdigest() == frozen_dataset.get("manifest_sha256") and
             dataset_sha == frozen_dataset.get("dataset_sha256") and
             dataset_version == frozen_dataset.get("dataset_version") and
             manifest.get("frozen_before_first_laya_call") is True and
             isinstance(dataset_sha, str) and hashlib.sha256(corpus_raw).hexdigest() == dataset_sha and
             isinstance(dataset_version, str) and corpus.get("dataset_version") == dataset_version and
             corpus.get("label_protocol") == manifest.get("label_protocol"),
             "frozen dataset corpus does not match its manifest")

    cases = corpus.get("cases")
    _require(isinstance(cases, list) and len(cases) == 2 * MIN_CASES_PER_SPLIT and
             manifest.get("cases") == len(cases), "frozen dataset must contain both 100-case splits")
    expected_ids: dict[str, list[str]] = {}
    case_by_id: dict[str, dict[str, Any]] = {}
    min_counts = manifest.get("family_minimum_counts_per_split")
    _require(isinstance(min_counts, dict), "frozen manifest family minima are missing")
    for split, manifest_key in (("calibration", "calibration_case_ids"), ("held_out", "held_out_case_ids")):
        ids = manifest.get(manifest_key)
        _require(isinstance(ids, list) and len(ids) >= MIN_CASES_PER_SPLIT and
                 all(isinstance(item, str) and item for item in ids) and len(ids) == len(set(ids)),
                 f"manifest {split} IDs do not meet the minimum sample count")
        split_cases = [row for row in cases if isinstance(row, dict) and row.get("split") == split]
        actual_ids = [row.get("case_id") for row in split_cases]
        _require(actual_ids == ids and len(split_cases) >= MIN_CASES_PER_SPLIT,
                 f"frozen corpus {split} IDs differ from its manifest")
        counts = Counter(row.get("family") for row in split_cases)
        manifest_counts = min_counts.get(split)
        _require(isinstance(manifest_counts, dict) and all(
            isinstance(manifest_counts.get(family), int) and not isinstance(manifest_counts.get(family), bool) and
            manifest_counts[family] >= MIN_CASES_PER_FAMILY for family in FAMILIES) and
            all(counts[family] >= MIN_CASES_PER_FAMILY for family in FAMILIES) and
            sum(counts.values()) == len(split_cases) and set(counts) == set(FAMILIES),
            f"frozen corpus {split} strata do not meet the 20-case family minimum")
        expected_ids[split] = ids
        for row in split_cases:
            case_id = row.get("case_id")
            eligible = row.get("eligible_route_ids")
            _require(isinstance(case_id, str) and isinstance(eligible, list) and eligible and
                     all(isinstance(route, str) and route for route in eligible) and
                     len(eligible) == len(set(eligible)) and row.get("oracle_route_id") in eligible and
                     row.get("deterministic_route_id") in eligible and
                     isinstance(row.get("classifications"), dict),
                     "frozen corpus contains invalid labels or candidate sets")
            case_by_id[case_id] = row
    _require(set(expected_ids["calibration"]).isdisjoint(expected_ids["held_out"]),
             "calibration and held-out manifest IDs overlap")
    _require(len(case_by_id) == len(cases), "frozen corpus contains duplicate or unsupported case IDs")
    return case_by_id, expected_ids


def _validate_result_rows(rows: object, expected_ids: list[str], split: str,
                          case_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    _require(isinstance(rows, list) and len(rows) == len(expected_ids) and
             len(rows) >= MIN_CASES_PER_SPLIT, f"{split} results do not contain the full frozen sample")
    checked: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        _require(isinstance(row, dict) and row.get("case_id") == expected_ids[index],
                 f"{split} result IDs differ from the frozen manifest")
        case = case_by_id[expected_ids[index]]
        route = row.get("predicted_route_id")
        _require(row.get("family") == case.get("family") and row.get("eligible_choice") is True and
                 isinstance(route, str) and route in case["eligible_route_ids"] and
                 row.get("matches_oracle") is (route == case["oracle_route_id"]) and
                 row.get("baseline_matches_oracle") is (case["deterministic_route_id"] == case["oracle_route_id"]),
                 f"{split} result labels or candidate eligibility differ from the frozen corpus")
        usage = row.get("usage")
        _require(isinstance(usage, dict) and usage.get("truncated") is False and row.get("error") is None,
                 f"{split} results contain failed or truncated choices")
        confidence = row.get("answer_confidence")
        _require(confidence is None or (_is_finite_number(confidence) and 0 <= confidence <= 1),
                 f"{split} result confidence is invalid")
        checked.append(row)
    counts = Counter(row.get("family") for row in checked)
    _require(all(counts[family] >= MIN_CASES_PER_FAMILY for family in FAMILIES),
             f"{split} results do not contain 20 measured cases per family")
    return checked


def _validate_calibration(calibration: dict[str, Any], raw_results: dict[str, Any],
                          manifest: dict[str, Any], expected_ids: dict[str, list[str]],
                          case_by_id: dict[str, dict[str, Any]], raw_results_bytes: bytes) -> tuple[str, str, str, float]:
    checkpoint = calibration.get("checkpoint")
    revision = calibration.get("checkpoint_revision")
    calibration_version = calibration.get("calibration_version")
    cutoff = calibration.get("confidence_cutoff")
    dataset_sha = manifest.get("dataset_sha256")
    _require(calibration.get("schema_version") == 1 and calibration.get("held_out_touched") is False and
             calibration.get("gate_enabled") is True and calibration.get("gate_reason") == "calibration_gate_passed" and
             calibration.get("diagnostic_only_when_disabled") is False and
             isinstance(checkpoint, str) and checkpoint in CHECKPOINTS and
             isinstance(revision, str) and revision and isinstance(calibration_version, str) and calibration_version and
             _is_finite_number(cutoff) and 0 <= cutoff <= 1 and
             calibration.get("dataset_sha256") == dataset_sha and
             calibration.get("dataset_version") == manifest.get("dataset_version") and
             calibration.get("label_protocol") == manifest.get("label_protocol") and
             calibration.get("labeler_independence") == manifest.get("labeler_independence") and
             calibration.get("device") == "cuda" and
             calibration.get("calibration_result_sha256") == hashlib.sha256(raw_results_bytes).hexdigest(),
             "calibration did not pass the frozen 100-case confidence gate")
    _require(raw_results.get("schema_version") == 1 and raw_results.get("split") == "calibration" and
             raw_results.get("held_out_touched") is False and raw_results.get("frozen_before_first_laya_call") is True and
             raw_results.get("dataset_sha256") == dataset_sha and
             raw_results.get("dataset_version") == manifest.get("dataset_version"),
             "calibration measurement does not match the frozen calibration dataset")
    raw_runs, decision_rows = raw_results.get("results"), calibration.get("checkpoint_results")
    _require(isinstance(raw_runs, list) and isinstance(decision_rows, list) and
             len(raw_runs) == len(CHECKPOINTS) and len(decision_rows) == len(CHECKPOINTS),
             "calibration must include every official checkpoint")
    _require(all(isinstance(row, dict) and isinstance(row.get("checkpoint"), str) for row in raw_runs) and
             all(isinstance(row, dict) and isinstance(row.get("checkpoint"), str) for row in decision_rows),
             "calibration checkpoint results are malformed")
    _require({row.get("checkpoint") for row in raw_runs} == set(CHECKPOINTS) and
             {row.get("checkpoint") for row in decision_rows} == set(CHECKPOINTS),
             "calibration checkpoint set is incomplete or duplicated")

    validated_gates: dict[str, tuple[float, int, float]] = {}
    for name in CHECKPOINTS:
        run_rows = [row for row in raw_runs if isinstance(row, dict) and row.get("checkpoint") == name]
        decision_matches = [row for row in decision_rows if isinstance(row, dict) and row.get("checkpoint") == name]
        _require(len(run_rows) == 1 and len(decision_matches) == 1, "calibration has duplicate checkpoint results")
        run, decision_row = run_rows[0], decision_matches[0]
        _require(run.get("requested_device") == "cuda" and
                 decision_row.get("revision") == run.get("checkpoint_revision") and
                 decision_row.get("sha256") == run.get("checkpoint_sha256"),
                 "calibration checkpoint provenance is inconsistent")
        rows = _validate_result_rows(run.get("cases"), expected_ids["calibration"], "calibration", case_by_id)
        measured_gate = select_calibration_cutoff(rows, minimum_retained=MIN_CALIBRATION_RETAINED)
        gate = decision_row.get("confidence_gate")
        _require(isinstance(gate, dict) and gate.get("minimum_retained") == MIN_CALIBRATION_RETAINED and
                 gate.get("cutoff") == measured_gate.cutoff and gate.get("retained") == measured_gate.retained and
                 gate.get("correct") == measured_gate.correct and
                 _same_number(gate.get("accuracy"), measured_gate.accuracy) and
                 _same_number(gate.get("wilson_lower_bound"), measured_gate.wilson_lower_bound) and
                 _same_number(gate.get("deterministic_accuracy"), measured_gate.deterministic_accuracy) and
                 gate.get("valid_choices") == len(rows) and gate.get("hard_filter_violations") == 0 and
                 gate.get("truncated_choices") == 0 and gate.get("passed") is (measured_gate.cutoff is not None),
                 "calibration checkpoint gate does not match recalculated measurements")
        if measured_gate.cutoff is not None:
            validated_gates[name] = (measured_gate.wilson_lower_bound or 0.0, measured_gate.retained,
                                     sum(row.get("matches_oracle") is True for row in rows) / len(rows))
    _require(checkpoint in validated_gates, "selected checkpoint did not pass recalculated calibration")
    selected_rows = [row for row in decision_rows if isinstance(row, dict) and row.get("checkpoint") == checkpoint]
    selected_gate = selected_rows[0].get("confidence_gate") if len(selected_rows) == 1 else None
    _require(isinstance(selected_gate, dict), "selected calibration confidence gate is malformed")
    _require(selected_rows[0].get("revision") == revision and selected_gate.get("cutoff") == cutoff,
             "selected calibration checkpoint evidence is inconsistent")
    best_checkpoint = max(validated_gates, key=lambda name: (validated_gates[name][0], validated_gates[name][1],
                                                             validated_gates[name][2], name))
    _require(best_checkpoint == checkpoint, "calibration did not select the strongest passing checkpoint")
    return checkpoint, revision, calibration_version, float(cutoff)


def _validate_held_out(held_out: dict[str, Any], calibration: dict[str, Any],
                       calibration_raw: bytes, checkpoint: str, revision: str, cutoff: float,
                       manifest: dict[str, Any], expected_ids: dict[str, list[str]],
                       case_by_id: dict[str, dict[str, Any]]) -> None:
    summary, rows = held_out.get("summary"), held_out.get("cases")
    _require(held_out.get("schema_version") == 1 and
             held_out.get("benchmark") == "scheduler-m2-local-held-out-selection-v1" and
             held_out.get("split") == "held_out" and held_out.get("dataset_sha256") == manifest.get("dataset_sha256") and
             held_out.get("dataset_version") == manifest.get("dataset_version") and
             held_out.get("frozen_calibration_decision_sha256") == hashlib.sha256(calibration_raw).hexdigest() and
             held_out.get("checkpoint") == checkpoint and held_out.get("checkpoint_revision") == revision and
             held_out.get("checkpoint_sha256") == calibration.get("checkpoint_sha256") and
             held_out.get("requested_device") == "cuda" and held_out.get("laya_gate_authorized") is True and
             isinstance(summary, dict), "held-out evidence does not match calibration or the frozen dataset")
    checked = _validate_result_rows(rows, expected_ids["held_out"], "held-out", case_by_id)
    paired_rows: list[dict[str, bool]] = []
    for row in checked:
        case = case_by_id[row["case_id"]]
        ambiguous = decision_facts_are_ambiguous(case["classifications"], evidence_complete=True,
                                                  dependency_count=0, has_shared_resources=False)
        _require(row.get("task_ambiguous") is ambiguous,
                 "held-out ambiguity labels differ from production decision policy")
        accepted = laya_choice_passes_runtime_gate(
            quality_authorized=True, task_ambiguous=ambiguous, candidate_eligible=True,
            answer_confidence=row.get("answer_confidence"), cutoff=cutoff)
        expected_hybrid_route = row["predicted_route_id"] if accepted else case["deterministic_route_id"]
        _require(row.get("hybrid_used_laya") is accepted and row.get("hybrid_route_id") == expected_hybrid_route,
                 "held-out hybrid rows differ from the production confidence and ambiguity gate")
        paired_rows.append({"hybrid_correct": expected_hybrid_route == case["oracle_route_id"],
                            "baseline_correct": case["deterministic_route_id"] == case["oracle_route_id"]})
    _require(held_out.get("resamples") == BOOTSTRAP_RESAMPLES and held_out.get("seed") == BOOTSTRAP_SEED,
             "held-out bootstrap protocol differs from the frozen benchmark")
    measured_interval = paired_accuracy_bootstrap(paired_rows, resamples=BOOTSTRAP_RESAMPLES,
                                                  seed=BOOTSTRAP_SEED)
    hybrid_accuracy = sum(row["hybrid_correct"] for row in paired_rows) / len(paired_rows)
    valid_choices = len(checked)
    expected_summary = (
        summary.get("cases") == MIN_CASES_PER_SPLIT and summary.get("valid_choices") == valid_choices and
        summary.get("invalid_or_failed") == 0 and summary.get("hard_filter_violations") == 0 and
        summary.get("ambiguity_filter_applied") is True and summary.get("ambiguity_gate_violations") == 0 and
        summary.get("truncated_choices") == 0 and summary.get("confidence_gate_enabled") is True and
        summary.get("confidence_cutoff") == cutoff and summary.get("held_out_labeler_is_human") is False and
        summary.get("production_hybrid_accuracy") == hybrid_accuracy and
        summary.get("production_hybrid_paired_delta_95ci") == list(measured_interval) and
        summary.get("valid_choices") == MIN_CASES_PER_SPLIT
    )
    _require(expected_summary and _is_finite_number(measured_interval[0]) and measured_interval[0] > 0,
             "recalculated held-out hybrid does not clear the 100-case paired bootstrap gate")


def _load_quality_evidence(calibration_path: str | Path, calibration_results_path: str | Path,
                           held_out_path: str | Path, corpus_path: str | Path,
                           manifest_path: str | Path) -> QualityEvidence:
    """Return evidence only when every frozen input and both quality gates recalculate successfully."""
    calibration, calibration_raw = _load(Path(calibration_path))
    calibration_results, calibration_results_raw = _load(Path(calibration_results_path))
    held_out, held_out_raw = _load(Path(held_out_path))
    manifest, manifest_raw = _load(Path(manifest_path))
    corpus, corpus_raw = _load(Path(corpus_path))
    case_by_id, expected_ids = _validate_manifest_and_corpus(manifest, manifest_raw, corpus, corpus_raw)
    checkpoint, revision, calibration_version, cutoff = _validate_calibration(
        calibration, calibration_results, manifest, expected_ids, case_by_id, calibration_results_raw)
    _validate_held_out(held_out, calibration, calibration_raw, checkpoint, revision, cutoff,
                       manifest, expected_ids, case_by_id)
    artifact_digest = hashlib.sha256(b"\0".join((calibration_raw, calibration_results_raw, held_out_raw,
                                                   corpus_raw, manifest_raw))).hexdigest()
    api_contract, _ = _load(Path(__file__).with_name("api-contract.json"))
    gate_contract = api_contract.get("laya_quality_gate")
    approved_digests = gate_contract.get("approved_evidence_sha256") if isinstance(gate_contract, dict) else None
    _require(isinstance(approved_digests, list) and
             all(isinstance(item, str) and len(item) == 64 and
                 all(character in "0123456789abcdef" for character in item) for item in approved_digests) and
             artifact_digest in approved_digests,
             "quality evidence digest is not explicitly approved by the M2 contract")
    return QualityEvidence(checkpoint, revision, calibration_version, cutoff, artifact_digest)


def load_quality_evidence(calibration_path: str | Path, calibration_results_path: str | Path,
                          held_out_path: str | Path, corpus_path: str | Path,
                          manifest_path: str | Path) -> QualityEvidence:
    """Normalize malformed external artifact shapes into a stable fail-closed validation error."""
    try:
        return _load_quality_evidence(calibration_path, calibration_results_path, held_out_path,
                                      corpus_path, manifest_path)
    except QualityEvidenceError:
        raise
    except (TypeError, KeyError, IndexError, OverflowError, RecursionError) as exc:
        raise QualityEvidenceError("quality artifacts have an invalid schema") from exc
