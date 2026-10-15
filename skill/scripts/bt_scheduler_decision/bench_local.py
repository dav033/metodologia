"""Reproducible, dependency-free M2 benchmark statistics and confidence-gate calculations."""
from __future__ import annotations

import math
import random
import statistics
from collections.abc import Mapping, Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class CalibrationGateResult:
    cutoff: float | None
    retained: int
    correct: int
    accuracy: float | None
    wilson_lower_bound: float | None
    deterministic_accuracy: float


def wilson_lower_bound(successes: int, total: int, *, z: float = 1.6448536269514722) -> float | None:
    """One-sided Wilson lower confidence bound for a binomial proportion."""
    if not isinstance(successes, int) or isinstance(successes, bool) or not isinstance(total, int) or \
            isinstance(total, bool) or total <= 0 or not 0 <= successes <= total or \
            not isinstance(z, (int, float)) or isinstance(z, bool) or not math.isfinite(z) or z <= 0:
        return None
    p = successes / total
    z2 = z * z
    center = p + z2 / (2 * total)
    radius = z * math.sqrt((p * (1 - p) + z2 / (4 * total)) / total)
    return max(0.0, (center - radius) / (1 + z2 / total))


def select_calibration_cutoff(rows: Sequence[Mapping[str, object]], *, minimum_retained: int = 50,
                              z: float = 1.6448536269514722) -> CalibrationGateResult:
    """Choose the lowest observed confidence threshold whose retained accuracy clears baseline by Wilson LB."""
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)) or not rows:
        return CalibrationGateResult(None, 0, 0, None, None, 0.0)
    baseline_values = [row.get("baseline_matches_oracle") for row in rows]
    if any(not isinstance(value, bool) for value in baseline_values):
        raise ValueError("benchmark rows need boolean deterministic labels")
    baseline_accuracy = sum(baseline_values) / len(baseline_values)
    confidence_values = []
    for row in rows:
        value = row.get("answer_confidence")
        if value is not None and (not isinstance(value, (int, float)) or isinstance(value, bool) or
                                  not math.isfinite(value) or not 0 <= value <= 1):
            raise ValueError("answer confidence must be finite in [0, 1]")
        correct = row.get("matches_oracle")
        if correct is not None and not isinstance(correct, bool):
            raise ValueError("oracle correctness must be boolean or null")
        if value is not None:
            confidence_values.append(float(value))
    for cutoff in sorted(set(confidence_values)):
        retained = [row for row in rows if isinstance(row.get("answer_confidence"), (int, float)) and
                    not isinstance(row.get("answer_confidence"), bool) and
                    row["answer_confidence"] >= cutoff and isinstance(row.get("matches_oracle"), bool)]
        if len(retained) < minimum_retained:
            continue
        correct = sum(row["matches_oracle"] is True for row in retained)
        lower = wilson_lower_bound(correct, len(retained), z=z)
        if lower is not None and lower >= baseline_accuracy:
            return CalibrationGateResult(cutoff, len(retained), correct, correct / len(retained), lower,
                                         baseline_accuracy)
    return CalibrationGateResult(None, 0, 0, None, None, baseline_accuracy)


def paired_accuracy_bootstrap(rows: Sequence[Mapping[str, object]], *, resamples: int = 10_000,
                              seed: int = 20261014) -> tuple[float | None, float | None]:
    """Two-sided 95% paired percentile interval; sample n rows with replacement using a fixed seed."""
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)) or not rows or \
            not isinstance(resamples, int) or isinstance(resamples, bool) or not 1 <= resamples <= 1_000_000 or \
            not isinstance(seed, int) or isinstance(seed, bool):
        return None, None
    differences = []
    for row in rows:
        hybrid, baseline = row.get("hybrid_correct"), row.get("baseline_correct")
        if not isinstance(hybrid, bool) or not isinstance(baseline, bool):
            raise TypeError("paired bootstrap rows need boolean hybrid and baseline outcomes")
        differences.append(int(hybrid) - int(baseline))
    rng = random.Random(seed)
    n = len(differences)
    estimates = sorted(sum(differences[rng.randrange(n)] for _ in range(n)) / n for _ in range(resamples))
    lower = estimates[max(0, math.ceil(.025 * resamples) - 1)]
    upper = estimates[max(0, math.ceil(.975 * resamples) - 1)]
    return lower, upper


def route_regret(utilities: Mapping[str, object], route_id: object) -> float | None:
    """Return oracle utility minus selected-route utility for a frozen candidate set."""
    if not isinstance(utilities, Mapping) or not utilities or not isinstance(route_id, str) or route_id not in utilities:
        return None
    values = tuple(utilities.values())
    if any(not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value)
           for value in values):
        raise ValueError("regret utilities must be finite numbers")
    return round(float(max(values) - utilities[route_id]), 8)


def summarize_regrets(rows: Sequence[Mapping[str, object]], route_fields: Mapping[str, str]) -> dict[str, object]:
    """Summarize measured per-case utility regret and report selection coverage."""
    summary: dict[str, object] = {}
    total = len(rows)
    for label, field in route_fields.items():
        values = [float(row[field]) for row in rows if isinstance(row.get(field), (int, float)) and
                  not isinstance(row.get(field), bool)]
        summary[label] = {
            "measured_cases": len(values),
            "coverage": len(values) / total if total else None,
            "mean": statistics.fmean(values) if values else None,
            "median": statistics.median(values) if values else None,
        }
    return summary


def summarize_runtime(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    """Summarize device and resource measurements without implying selection quality."""
    def measured(key: str) -> list[float]:
        return [float(row[key]) for row in rows if isinstance(row.get(key), (int, float)) and
                not isinstance(row.get(key), bool)]

    def percentile(values: list[float], quantile: float) -> float | None:
        return sorted(values)[max(0, math.ceil(quantile * len(values)) - 1)] if values else None

    return {
        "sampled_cases": len(rows),
        "quality_evaluation": "not_evaluated",
        "observed_devices": sorted({row["device"] for row in rows if isinstance(row.get("device"), str)}),
        "load_ms_median": statistics.median(measured("load_ms")) if measured("load_ms") else None,
        "inference_ms_median": statistics.median(measured("inference_ms")) if measured("inference_ms") else None,
        "wall_ms_p95": percentile(measured("wall_ms"), .95),
        "peak_rss_bytes": max((row.get("rss_peak_bytes", 0) for row in rows), default=0),
        "peak_cuda_reserved_bytes": max((row.get("cuda_inference_peak_reserved_bytes", 0)
                                          for row in rows), default=0),
        "cgroup_memory_limit_bytes": max((row.get("cgroup_memory_limit_bytes", 0) for row in rows), default=0),
        "cgroup_swap_limit_bytes": max((row.get("cgroup_swap_limit_bytes", 0) for row in rows), default=0),
        "errors": sum(row.get("error") is not None for row in rows),
    }


def summarize_selection(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    """Aggregate only bounded selection outcomes and measured runtime/resource values."""
    count = len(rows)
    if not count:
        return {"cases": 0, "oracle_accuracy": None, "deterministic_accuracy": None,
                "agreement_with_baseline": None}
    valid = [row for row in rows if row.get("predicted_route_id") is not None]
    wall = [float(row["wall_ms"]) for row in rows if isinstance(row.get("wall_ms"), (int, float)) and
            not isinstance(row.get("wall_ms"), bool)]
    infer = [float(row["inference_ms"]) for row in rows if isinstance(row.get("inference_ms"), (int, float)) and
             not isinstance(row.get("inference_ms"), bool)]
    p95 = lambda values: sorted(values)[max(0, math.ceil(.95 * len(values)) - 1)] if values else None
    return {
        "cases": count,
        "valid_choices": len(valid),
        "invalid_or_failed": count - len(valid),
        "oracle_accuracy": sum(row.get("matches_oracle") is True for row in rows) / count,
        "deterministic_accuracy": sum(row.get("baseline_matches_oracle") is True for row in rows) / count,
        "agreement_with_baseline": sum(row.get("matches_baseline") is True for row in rows) / count,
        "wall_latency_ms": {"median": statistics.median(wall) if wall else None, "p95": p95(wall),
                            "cold_first": wall[0] if wall else None},
        "worker_inference_latency_ms": {"median": statistics.median(infer) if infer else None,
                                         "p95": p95(infer)},
        "peak_rss_bytes": max((row.get("rss_peak_bytes", 0) for row in rows), default=0),
        "peak_cuda_allocated_bytes": max((row.get("cuda_inference_peak_allocated_bytes", 0)
                                           for row in rows), default=0),
        "peak_cuda_reserved_bytes": max((row.get("cuda_inference_peak_reserved_bytes", 0)
                                         for row in rows), default=0),
        "peak_cuda_load_allocated_bytes": max((row.get("cuda_load_peak_allocated_bytes", 0)
                                                for row in rows), default=0),
        "peak_cuda_load_reserved_bytes": max((row.get("cuda_load_peak_reserved_bytes", 0)
                                               for row in rows), default=0),
    }
