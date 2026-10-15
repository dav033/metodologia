#!/usr/bin/env python3
"""Measure pinned local Laya checkpoints on the frozen calibration split only."""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from bt_scheduler_benchmark import (
    FixtureError,
    laya_payload,
    load_fixtures,
    parse_choice,
)
from bt_scheduler_decision.bench_local import (
    route_regret,
    summarize_regrets,
    summarize_runtime,
    summarize_selection,
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
DEFAULT_OUTPUT = REQ / "laya-results.json"
DEFAULT_ROOT = Path.home() / ".local/share/bt-scheduler-laya"


def run(root: Path, checkpoints: tuple[str, ...], devices: tuple[str, ...], deadline: float,
        max_cases: int = 100) -> dict:
    corpus, manifest = load_fixtures(CORPUS, MANIFEST)
    calibration = sorted((case for case in corpus["cases"] if case["split"] == "calibration"),
                         key=lambda item: item["case_id"])
    results = []
    if not isinstance(max_cases, int) or isinstance(max_cases, bool) or not 1 <= max_cases <= len(calibration):
        raise ValueError("case limit must be between 1 and the full calibration split")
    sampled_cases = calibration[:max_cases]
    for checkpoint in checkpoints:
        for device in devices:
            rows = []
            client = LocalLayaClient(LocalLayaConfig(root, checkpoint, deadline_seconds=deadline, device=device))
            try:
                for index, case in enumerate(sampled_cases, start=1):
                    payload, labels = laya_payload(case)
                    started = time.perf_counter()
                    try:
                        result = client.predict(payload["state"], payload["questions"], payload["lang"])
                        route_id, confidence = parse_choice(result, labels)
                        metrics = dict(client.last_metrics)
                        error = None
                    except Exception as exc:  # noqa: BLE001 - record worker failures per case and finish the sample.
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
                        "laya_regret": route_regret(case["oracle_utilities"], route_id),
                        "deterministic_regret": route_regret(case["oracle_utilities"], case["deterministic_route_id"]),
                        "requested_device": device,
                        "wall_ms": round(wall_ms, 3), "error": error,
                    }
                    for key in ("load_ms", "inference_ms", "device", "rss_peak_bytes", "usage",
                                "device_fallback", "memory_limit_bytes", "cgroup_memory_limit_bytes",
                                "cgroup_swap_limit_bytes",
                                "cuda_load_peak_allocated_bytes", "cuda_load_peak_reserved_bytes",
                                "cuda_inference_peak_allocated_bytes", "cuda_inference_peak_reserved_bytes"):
                        if key in metrics:
                            row[key] = metrics[key]
                    rows.append(row)
                    if index % 10 == 0 or index == len(sampled_cases):
                        print(f"{checkpoint}/{device}: {index}/{len(sampled_cases)} sampled calibration cases",
                              file=sys.stderr, flush=True)
            finally:
                client.close()
            summary = summarize_selection(rows) if max_cases == len(calibration) else summarize_runtime(rows)
            if max_cases == len(calibration):
                summary["regret"] = summarize_regrets(rows, {"laya": "laya_regret",
                                                              "deterministic": "deterministic_regret"})
            results.append({"checkpoint": checkpoint, "checkpoint_revision": CHECKPOINTS[checkpoint][1],
                            "checkpoint_sha256": CHECKPOINTS[checkpoint][2], "requested_device": device,
                            "sampled_cases": len(rows), "complete_calibration": max_cases == len(calibration),
                            "summary": summary, "cases": rows})
    return {
        "schema_version": 1,
        "benchmark": "scheduler-m2-local-checkpoint-calibration-v1",
        "split": "calibration",
        "started_at_utc": datetime.now(UTC).isoformat(),
        "dataset_version": manifest["dataset_version"],
        "dataset_sha256": manifest["dataset_sha256"],
        "frozen_before_first_laya_call": manifest["frozen_before_first_laya_call"],
        "laya_setup_root": str(root),
        "deadline_seconds": deadline,
        "results": results,
        "held_out_touched": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoints", default="all", help="comma-separated checkpoint names or all")
    parser.add_argument("--devices", default="cuda,cpu", help="comma-separated requested devices")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--deadline-seconds", type=float, default=240.0)
    parser.add_argument("--max-cases", type=int, default=100,
                        help="diagnostic cap; values below 100 collect runtime only, never quality evidence")
    parser.add_argument("--json", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    checkpoints = tuple(CHECKPOINTS) if args.checkpoints == "all" else tuple(
        part.strip() for part in args.checkpoints.split(",") if part.strip())
    devices = tuple(part.strip() for part in args.devices.split(",") if part.strip())
    if not checkpoints or any(name not in CHECKPOINTS for name in checkpoints) or \
            len(set(checkpoints)) != len(checkpoints) or not devices or \
            any(device not in {"cuda", "cpu"} for device in devices) or len(set(devices)) != len(devices):
        parser.error("choose distinct known checkpoints and devices")
    if args.json.exists():
        parser.error(f"refusing to overwrite benchmark output: {args.json}")
    try:
        payload = run(args.root.expanduser(), checkpoints, devices, args.deadline_seconds, args.max_cases)
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                             encoding="utf-8")
    except (FixtureError, OSError, ValueError) as exc:
        print(f"local benchmark failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"output": str(args.json), "dataset_sha256": payload["dataset_sha256"],
                      "combinations": len(payload["results"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
