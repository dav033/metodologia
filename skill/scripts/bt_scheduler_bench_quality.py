#!/usr/bin/env python3
"""Freeze calibration before evaluating the hash-disjoint held-out split with local Laya."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from bt_scheduler_benchmark import (
    FixtureError,
    laya_payload,
    load_fixtures,
    parse_choice,
)
from bt_scheduler_decision.bench_local import (
    paired_accuracy_bootstrap,
    route_regret,
    select_calibration_cutoff,
    summarize_regrets,
    summarize_selection,
)
from bt_scheduler_decision.gates import (
    decision_facts_are_ambiguous,
    laya_choice_passes_runtime_gate,
)
from bt_scheduler_laya import (
    CHECKPOINTS,
    LocalLayaClient,
    LocalLayaConfig,
)

ROOT = SCRIPTS.parent.parent
REQ = ROOT / "bitacora/metodologia/requirements/REQ-013-scheduler-m2-decision-engine-with-local"
CORPUS = REQ / "fixtures-v1.json"
MANIFEST = REQ / "fixture-manifest-v1.json"
DEFAULT_CALIBRATION = REQ / "laya-results-cuda-v3.json"
DEFAULT_DECISION = REQ / "laya-calibration-decision-v2.json"
DEFAULT_OUTPUT = REQ / "benchmark-results-v2.json"
DEFAULT_ROOT = Path.home() / ".local/share/bt-scheduler-laya"
MIN_RETAINED = 50
BOOTSTRAP_RESAMPLES = 10_000
BOOTSTRAP_SEED = 20261014


class BenchmarkError(ValueError):
    pass


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _p95(values: list[float]) -> float | None:
    return sorted(values)[max(0, math.ceil(.95 * len(values)) - 1)] if values else None


def build_calibration_decision(results: dict[str, Any], *, source_sha256: str,
                               manifest: dict[str, Any], corpus: dict[str, Any] | None = None) -> dict[str, Any]:
    if results.get("dataset_sha256") != manifest.get("dataset_sha256") or \
            results.get("dataset_version") != manifest.get("dataset_version") or \
            results.get("split") != "calibration" or results.get("held_out_touched") is not False:
        raise BenchmarkError("calibration output does not match the frozen calibration split")
    runs = results.get("results")
    if not isinstance(runs, list) or len(runs) != len(CHECKPOINTS):
        raise BenchmarkError("calibration must measure every pinned checkpoint once")
    checked = []
    corpus_cases = {row["case_id"]: row for row in corpus.get("cases", [])} if isinstance(corpus, dict) else {}
    for run in runs:
        if not isinstance(run, dict):
            raise BenchmarkError("invalid checkpoint result")
        name = run.get("checkpoint")
        if name not in CHECKPOINTS or run.get("requested_device") != "cuda":
            raise BenchmarkError("calibration must use a pinned checkpoint on CUDA")
        repo, revision, digest = CHECKPOINTS[name]
        if (run.get("checkpoint_revision"), run.get("checkpoint_sha256")) != (revision, digest):
            raise BenchmarkError("checkpoint revision or digest differs from the pinned registry")
        rows = run.get("cases")
        if not isinstance(rows, list) or [row.get("case_id") for row in rows] != manifest["calibration_case_ids"]:
            raise BenchmarkError("calibration case IDs differ from the frozen calibration split")
        gate = select_calibration_cutoff(rows, minimum_retained=MIN_RETAINED)
        summary = summarize_selection(rows)
        if corpus_cases:
            for row in rows:
                case = corpus_cases.get(row.get("case_id"))
                if case is None:
                    raise BenchmarkError("calibration case is missing from the frozen corpus")
                row["laya_regret"] = route_regret(case["oracle_utilities"], row.get("predicted_route_id"))
                row["deterministic_regret"] = route_regret(case["oracle_utilities"],
                                                           case["deterministic_route_id"])
            summary["regret"] = summarize_regrets(rows, {"laya": "laya_regret",
                                                          "deterministic": "deterministic_regret"})
        hard_filter_violations = sum(row.get("predicted_route_id") is not None and
                                     row.get("eligible_choice") is not True for row in rows)
        truncated = sum(bool((row.get("usage") or {}).get("truncated")) for row in rows)
        valid_choices = sum(row.get("predicted_route_id") is not None and
                            row.get("eligible_choice") is True for row in rows)
        checked.append({
            "checkpoint": name,
            "repository": repo,
            "revision": revision,
            "sha256": digest,
            "requested_device": "cuda",
            "summary": summary,
            "confidence_gate": {
                "minimum_retained": MIN_RETAINED,
                "cutoff": gate.cutoff,
                "retained": gate.retained,
                "correct": gate.correct,
                "accuracy": gate.accuracy,
                "wilson_lower_bound": gate.wilson_lower_bound,
                "deterministic_accuracy": gate.deterministic_accuracy,
                "hard_filter_violations": hard_filter_violations,
                "truncated_choices": truncated,
                "valid_choices": valid_choices,
                "passed": gate.cutoff is not None and hard_filter_violations == 0 and truncated == 0 and
                          valid_choices == len(rows),
            },
        })
    gated = [item for item in checked if item["confidence_gate"]["passed"]]
    if gated:
        selected = max(gated, key=lambda item: (item["confidence_gate"]["wilson_lower_bound"],
                                                item["confidence_gate"]["retained"],
                                                item["summary"]["oracle_accuracy"],
                                                item["checkpoint"]))
    else:
        # Diagnostic winner is frozen without enabling production inference.
        selected = max(checked, key=lambda item: (item["summary"]["oracle_accuracy"],
                                                   -(item["summary"]["worker_inference_latency_ms"]["p95"] or math.inf),
                                                   item["checkpoint"]))
    enabled = bool(gated)
    return {
        "schema_version": 1,
        "calibration_version": f"scheduler-m2-calibration-v1:{source_sha256[:16]}",
        "dataset_version": manifest["dataset_version"],
        "dataset_sha256": manifest["dataset_sha256"],
        "calibration_result_sha256": source_sha256,
        "frozen_at_utc": datetime.now(UTC).isoformat(),
        "held_out_touched": False,
        "checkpoint": selected["checkpoint"],
        "checkpoint_repository": selected["repository"],
        "checkpoint_revision": selected["revision"],
        "checkpoint_sha256": selected["sha256"],
        "device": "cuda",
        "max_len": 1536,
        "head_max_len": 512,
        "gate_enabled": enabled,
        "confidence_cutoff": selected["confidence_gate"]["cutoff"] if enabled else None,
        "gate_reason": "calibration_gate_passed" if enabled else "no_checkpoint_cleared_calibrated_wilson_gate",
        "diagnostic_only_when_disabled": not enabled,
        "label_protocol": manifest["label_protocol"],
        "labeler_independence": manifest["labeler_independence"],
        "checkpoint_results": checked,
    }


def freeze_calibration(input_path: Path, output_path: Path) -> dict[str, Any]:
    corpus, manifest = load_fixtures(CORPUS, MANIFEST)
    results = json.loads(input_path.read_text(encoding="utf-8"))
    payload = build_calibration_decision(results, source_sha256=_sha256(input_path), manifest=manifest,
                                         corpus=corpus)
    if output_path.exists():
        raise BenchmarkError(f"refusing to overwrite frozen calibration decision: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    return payload


def evaluate_held_out(decision_path: Path, output_path: Path, root: Path, deadline: float) -> dict[str, Any]:
    corpus, manifest = load_fixtures(CORPUS, MANIFEST)
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    if decision.get("dataset_sha256") != manifest["dataset_sha256"] or \
            decision.get("held_out_touched") is not False or decision.get("device") != "cuda":
        raise BenchmarkError("frozen calibration decision is missing or incompatible")
    checkpoint = decision.get("checkpoint")
    if checkpoint not in CHECKPOINTS or \
            (decision.get("checkpoint_revision"), decision.get("checkpoint_sha256")) != \
            (CHECKPOINTS[checkpoint][1], CHECKPOINTS[checkpoint][2]):
        raise BenchmarkError("frozen checkpoint does not match the pinned registry")
    if output_path.exists():
        raise BenchmarkError(f"refusing to overwrite held-out benchmark: {output_path}")

    cases = sorted((row for row in corpus["cases"] if row["split"] == "held_out"),
                   key=lambda item: item["case_id"])
    output_rows = []
    client = LocalLayaClient(LocalLayaConfig(root, checkpoint, deadline_seconds=deadline, device="cuda"))
    try:
        for index, case in enumerate(cases, start=1):
            payload, labels = laya_payload(case)
            started = time.perf_counter()
            try:
                result = client.predict(payload["state"], payload["questions"], payload["lang"])
                route_id, confidence = parse_choice(result, labels)
                metrics = dict(client.last_metrics)
                error = None
            except Exception as exc:  # noqa: BLE001 - record worker failure per case and finish the sample.
                route_id, confidence, metrics = None, None, dict(client.last_metrics)
                error = getattr(exc, "reason", "worker_error")
            wall_ms = (time.perf_counter() - started) * 1000
            row = {
                "case_id": case["case_id"], "family": case["family"], "language": case["language"],
                "predicted_route_id": route_id, "answer_confidence": confidence,
                "oracle_route_id": case["oracle_route_id"],
                "deterministic_route_id": case["deterministic_route_id"],
                "matches_oracle": route_id == case["oracle_route_id"] if route_id else None,
                "baseline_matches_oracle": case["deterministic_route_id"] == case["oracle_route_id"],
                "matches_baseline": route_id == case["deterministic_route_id"] if route_id else None,
                "eligible_choice": route_id in case["eligible_route_ids"] if route_id else None,
                "task_ambiguous": decision_facts_are_ambiguous(case["classifications"], evidence_complete=True,
                                                                dependency_count=0, has_shared_resources=False),
                "wall_ms": round(wall_ms, 3), "error": error,
            }
            for key in ("load_ms", "inference_ms", "device", "requested_device", "device_fallback", "rss_peak_bytes",
                        "usage", "cuda_load_peak_allocated_bytes", "cuda_load_peak_reserved_bytes",
                        "cuda_inference_peak_allocated_bytes", "cuda_inference_peak_reserved_bytes"):
                if key in metrics:
                    row[key] = metrics[key]
            output_rows.append(row)
            if index % 10 == 0 or index == len(cases):
                print(f"held-out {checkpoint}/cuda: {index}/{len(cases)} cases", file=sys.stderr, flush=True)
    finally:
        client.close()

    summary = summarize_selection(output_rows)
    raw_rows = [{"hybrid_correct": row["matches_oracle"] is True,
                 "baseline_correct": row["baseline_matches_oracle"]} for row in output_rows]
    raw_delta = paired_accuracy_bootstrap(raw_rows, resamples=BOOTSTRAP_RESAMPLES, seed=BOOTSTRAP_SEED)
    confidence_gate = decision.get("gate_enabled") is True
    cutoff = decision.get("confidence_cutoff") if confidence_gate else None
    production_hybrid = []
    cases_by_id = {case["case_id"]: case for case in cases}
    for row in output_rows:
        accepted = laya_choice_passes_runtime_gate(
            quality_authorized=confidence_gate, task_ambiguous=row["task_ambiguous"],
            candidate_eligible=row["eligible_choice"] is True and row["predicted_route_id"] is not None,
            answer_confidence=row["answer_confidence"], cutoff=cutoff)
        case = cases_by_id[row["case_id"]]
        hybrid_route = row["predicted_route_id"] if accepted else row["deterministic_route_id"]
        row["hybrid_used_laya"] = bool(accepted)
        row["hybrid_route_id"] = hybrid_route
        row["laya_regret"] = route_regret(case["oracle_utilities"], row["predicted_route_id"])
        row["deterministic_regret"] = route_regret(case["oracle_utilities"], row["deterministic_route_id"])
        row["hybrid_regret"] = route_regret(case["oracle_utilities"], hybrid_route)
        production_hybrid.append({
            "hybrid_correct": row["matches_oracle"] is True if accepted else row["baseline_matches_oracle"],
            "baseline_correct": row["baseline_matches_oracle"],
        })
    hybrid_delta = paired_accuracy_bootstrap(production_hybrid, resamples=BOOTSTRAP_RESAMPLES,
                                             seed=BOOTSTRAP_SEED)
    hybrid_correct = sum(item["hybrid_correct"] for item in production_hybrid)
    hard_filter_violations = sum(row["predicted_route_id"] is not None and row["eligible_choice"] is not True
                                 for row in output_rows)
    ambiguity_gate_violations = sum(row["hybrid_used_laya"] and row["task_ambiguous"] is not True
                                    for row in output_rows)
    truncated = sum(bool((row.get("usage") or {}).get("truncated")) for row in output_rows)
    # Require complete eligible predictions, no truncation/filter violations, and a positive paired lower bound.
    held_out_passed = bool(
        confidence_gate and len(output_rows) >= MIN_RETAINED and summary["valid_choices"] == len(output_rows) and
        truncated == 0 and hard_filter_violations == 0 and ambiguity_gate_violations == 0 and
        hybrid_delta[0] is not None and hybrid_delta[0] > 0
    )
    summary.update({
        "production_hybrid_accuracy": hybrid_correct / len(output_rows) if output_rows else None,
        "production_hybrid_paired_delta_95ci": hybrid_delta,
        "raw_laya_paired_delta_95ci": raw_delta,
        "raw_laya_beats_deterministic": bool(raw_delta[0] is not None and raw_delta[0] > 0),
        "hard_filter_violations": hard_filter_violations,
        "ambiguity_filter_applied": True,
        "ambiguity_gate_violations": ambiguity_gate_violations,
        "truncated_choices": truncated,
        "regret": summarize_regrets(output_rows, {"laya": "laya_regret", "deterministic": "deterministic_regret",
                                                   "production_hybrid": "hybrid_regret"}),
        "confidence_gate_enabled": confidence_gate,
        "confidence_cutoff": cutoff,
        "held_out_labeler_is_human": False,
    })
    result = {
        "schema_version": 1,
        "benchmark": "scheduler-m2-local-held-out-selection-v1",
        "split": "held_out",
        "started_at_utc": datetime.now(UTC).isoformat(),
        "dataset_version": manifest["dataset_version"],
        "dataset_sha256": manifest["dataset_sha256"],
        "frozen_calibration_decision_sha256": _sha256(decision_path),
        "checkpoint": checkpoint,
        "checkpoint_revision": decision["checkpoint_revision"],
        "checkpoint_sha256": decision["checkpoint_sha256"],
        "requested_device": "cuda",
        "runtime_context": {"max_len": decision["max_len"], "head_max_len": decision["head_max_len"]},
        "resamples": BOOTSTRAP_RESAMPLES,
        "seed": BOOTSTRAP_SEED,
        "summary": summary,
        "laya_gate_authorized": held_out_passed,
        "cases": output_rows,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)
    calibrate = subparsers.add_parser("calibrate")
    calibrate.add_argument("--results", type=Path, default=DEFAULT_CALIBRATION)
    calibrate.add_argument("--output", type=Path, default=DEFAULT_DECISION)
    evaluate = subparsers.add_parser("evaluate")
    evaluate.add_argument("--calibration", type=Path, default=DEFAULT_DECISION)
    evaluate.add_argument("--json", type=Path, default=DEFAULT_OUTPUT)
    evaluate.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    evaluate.add_argument("--deadline-seconds", type=float, default=240.0)
    args = parser.parse_args()
    try:
        if args.action == "calibrate":
            decision = freeze_calibration(args.results, args.output)
            print(json.dumps({"output": str(args.output), "checkpoint": decision["checkpoint"],
                              "gate_enabled": decision["gate_enabled"],
                              "confidence_cutoff": decision["confidence_cutoff"]}, sort_keys=True))
        else:
            result = evaluate_held_out(args.calibration, args.json, args.root.expanduser(), args.deadline_seconds)
            print(json.dumps({"output": str(args.json), "checkpoint": result["checkpoint"],
                              "summary": result["summary"]}, sort_keys=True))
    except (BenchmarkError, FixtureError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"quality benchmark failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
