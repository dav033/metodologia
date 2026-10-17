"""Descriptive benchmark reporting with a per-metric directional guard."""
from __future__ import annotations

import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from .contract import REVIEW_SCORE_IDS, BenchmarkError
from .verify import verify_store

_LOWER = {"O1", "O3", "O4", "O6"}
_HIGHER = {"O2", "O5"}
_JUDGED = ("J1", "J2", "J3", "J4", "J5", "J6", "J7", "J8")


def _numeric(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _cell_values(cells: list[dict[str, Any]], metric_id: str) -> dict[str, dict[str, list[float]]]:
    result: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for cell in cells:
        observed = cell.get("observed")
        if cell["meta"]["status"] != "complete" or not isinstance(observed, dict):
            continue
        record = observed["metrics"][metric_id]
        value = _numeric(record.get("comparison_value")) if record.get("status") == "measured" else None
        if value is not None:
            result[cell["meta"]["case_id"]][cell["meta"]["arm_id"]].append(value)
    return result


def _complete_case_values(values: dict[str, dict[str, list[float]]]) -> dict[str, dict[str, tuple[float, ...]]]:
    return {case_id: {arm_id: tuple(scores) for arm_id, scores in arms.items()}
            for case_id, arms in values.items()
            if all(len(arms.get(arm, [])) == 3 for arm in ("A", "B"))}


def _direction(values: dict[str, dict[str, list[float]]], direction: str,
               reviewer_values: dict[str, dict[str, dict[str, list[float]]]] | None = None) -> dict[str, Any]:
    complete = _complete_case_values(values)
    if len(complete) < 4:
        return {"status": "no_supported_difference", "complete_cases": len(complete),
                "reason": "fewer_than_four_complete_cases"}
    better_count = 0
    worst_case_holds = True
    case_results: dict[str, dict[str, float | bool]] = {}
    for case_id, arms in sorted(complete.items()):
        a, b = arms["A"], arms["B"]
        median_a, median_b = statistics.median(a), statistics.median(b)
        better = median_b > median_a if direction == "higher" else median_b < median_a
        no_worse = min(b) >= min(a) if direction == "higher" else max(b) <= max(a)
        better_count += int(better)
        worst_case_holds &= no_worse
        case_results[case_id] = {"A_median": median_a, "B_median": median_b,
                                 "B_median_better": better, "B_not_worse_than_A_worst": no_worse}
    if better_count < 4 or not worst_case_holds:
        return {"status": "no_supported_difference", "complete_cases": len(complete),
                "cases": case_results, "reason": "directional_threshold_not_met"}
    if reviewer_values is not None:
        reviewer_directions = {}
        for reviewer_id, samples in reviewer_values.items():
            reviewer_complete = _complete_case_values(samples)
            reviewer_better = 0
            for case_id in complete:
                arms = reviewer_complete.get(case_id)
                if arms is None:
                    return {"status": "no_supported_difference", "complete_cases": len(complete),
                            "reason": "reviewer_evidence_incomplete"}
                median_a, median_b = statistics.median(arms["A"]), statistics.median(arms["B"])
                reviewer_better += int(median_b > median_a if direction == "higher" else median_b < median_a)
            reviewer_directions[reviewer_id] = reviewer_better
            if reviewer_better < 4:
                return {"status": "no_supported_difference", "complete_cases": len(complete),
                        "cases": case_results, "reviewer_better_cases": reviewer_directions,
                        "reason": "reviewers_do_not_agree_on_direction"}
        return {"status": "directional_difference", "direction": "B_better", "complete_cases": len(complete),
                "cases": case_results, "reviewer_better_cases": reviewer_directions,
                "interpretation": "descriptive_only_n_equals_3"}
    return {"status": "directional_difference", "direction": "B_better", "complete_cases": len(complete),
            "cases": case_results, "interpretation": "descriptive_only_n_equals_3"}


def _observed(cells: list[dict[str, Any]]) -> dict[str, Any]:
    records: dict[str, list[dict[str, Any]]] = {f"O{i}": [] for i in range(1, 10)}
    stability: dict[str, dict[str, Any]] = {}
    directions = {}
    coverage_samples: dict[str, list[dict[str, bool]]] = defaultdict(list)
    for metric_id, metric_records in records.items():
        values_by_case_arm: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
        for cell in cells:
            if cell["meta"]["status"] != "complete" or cell.get("observed") is None:
                continue
            record = cell["observed"]["metrics"][metric_id]
            metric_records.append({"cell_id": cell["cell_id"], **record})
            if metric_id == "O2" and record.get("status") == "measured":
                coverage_key = f"{cell['meta']['case_id']}/{cell['meta']['arm_id']}"
                coverage_samples[coverage_key].append(record["value"]["per_requirement"])
            value = _numeric(record.get("comparison_value")) if record.get("status") == "measured" else None
            if value is not None:
                key = f"{cell['meta']['case_id']}/{cell['meta']['arm_id']}"
                values_by_case_arm[key]["samples"].append(value)
        if metric_id in {"O1", "O2", "O3", "O4", "O5", "O6", "O7", "O8"}:
            stability[metric_id] = {
                key: {"samples": len(group["samples"]),
                      "range": [min(group["samples"]), max(group["samples"])]}
                for key, group in sorted(values_by_case_arm.items())
            }
        if metric_id in _LOWER | _HIGHER:
            directions[metric_id] = _direction(values_by_case(values_by_case_arm, metric_id),
                                               "lower" if metric_id in _LOWER else "higher")
    coverage_agreement = {}
    for key, samples in sorted(coverage_samples.items()):
        if len(samples) != 3 or any(set(sample) != set(samples[0]) for sample in samples[1:]):
            coverage_agreement[key] = {"status": "unknown", "reason": "coverage_samples_incomplete_or_mismatched"}
            continue
        stable = sum(len({sample[requirement_id] for sample in samples}) == 1 for requirement_id in samples[0])
        total = len(samples[0])
        coverage_agreement[key] = {"status": "measured", "agreeing_requirements": stable,
                                   "requirements": total, "agreement_rate": stable / total}
    stability_details = {key: value for key, value in stability.items()}
    stability["O10"] = {"status": "measured", "source_command": "bt_plan_bench.py score <store>",
                        "unit": "per_metric ranges and per-requirement coverage agreement",
                        "details": stability_details, "per_requirement_coverage_agreement": coverage_agreement}
    return {"metrics": records, "stability": stability, "directional_findings": directions}


def values_by_case(groups: dict[str, dict[str, list[float]]], metric_id: str) -> dict[str, dict[str, list[float]]]:
    result: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for pair_id, details in groups.items():
        case_id, arm_id = pair_id.rsplit("/", 1)
        result[case_id][arm_id].extend(details["samples"])
    return result


def _judged(reviews: list[dict[str, Any]], cells: list[dict[str, Any]], manifest: dict[str, Any]) -> dict[str, Any]:
    if not reviews:
        return {"status": "not_collected", "by_output": []}
    output_to_cell = {cell["cell_id"]: cell for cell in cells}
    reviewer_data: dict[str, dict[str, dict[str, list[float]]]] = {
        reviewer["reviewer_id"]: defaultdict(lambda: defaultdict(list)) for reviewer in manifest["reviewers"]}
    output_scores: dict[str, dict[str, dict[str, float]]] = defaultdict(lambda: defaultdict(dict))
    j5_reviewer: dict[str, dict[str, dict[str, list[float]]]] = {
        reviewer["reviewer_id"]: defaultdict(lambda: defaultdict(list)) for reviewer in manifest["reviewers"]}
    j5_output_scores: dict[str, dict[str, dict[str, float]]] = defaultdict(lambda: defaultdict(dict))
    by_output = []
    j5_items: dict[str, list[dict[str, Any]]] = defaultdict(list)
    j8_items: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for output in reviews:
        cell = output_to_cell.get(output["output_id"])
        run_info = {"case_id": cell["meta"]["case_id"], "arm_id": cell["meta"]["arm_id"]} if cell else {
            "case_id": None, "arm_id": "retrospective"}
        reviewers = []
        for review in output["reviews"]:
            scores = review["scores"]
            reviewer_id = review["reviewer_id"]
            for criterion in REVIEW_SCORE_IDS:
                if cell is not None:
                    key = f"{run_info['case_id']}/{run_info['arm_id']}"
                    reviewer_data[reviewer_id][criterion][key].append(float(scores[criterion]["score"]))
                    output_scores[criterion][cell["cell_id"]][reviewer_id] = float(scores[criterion]["score"])
            j5 = scores["J5"]
            j5_items[reviewer_id].append({"blind_output_id": output["blind_output_id"], "oracle_findings": j5})
            if cell is not None:
                oracle_records = j5.get("oracles", [])
                detected_rate = sum(item["detected"] for item in oracle_records) / len(oracle_records)
                key = f"{run_info['case_id']}/{run_info['arm_id']}"
                j5_reviewer[reviewer_id]["J5_detection_rate"][key].append(detected_rate)
                j5_output_scores[cell["cell_id"]][reviewer_id] = detected_rate
            j8_items[reviewer_id].append({"blind_output_id": output["blind_output_id"], "findings": scores["J8"]["findings"]})
            reviewers.append({"reviewer_id": reviewer_id, "scores": scores})
        by_output.append({"output_id": output["output_id"], "blind_output_id": output["blind_output_id"],
                          **run_info, "reviews": reviewers})
    directions = {}
    for criterion in REVIEW_SCORE_IDS:
        by_reviewer = {}
        for reviewer_id, data in reviewer_data.items():
            per_case: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
            for key, scores in data[criterion].items():
                case_id, arm_id = key.rsplit("/", 1)
                per_case[case_id][arm_id].extend(scores)
            by_reviewer[reviewer_id] = per_case
        per_cell = defaultdict(lambda: defaultdict(list))
        for cell_id, scores in output_scores[criterion].items():
            if len(scores) == 2:
                cell = output_to_cell[cell_id]
                key = f"{cell['meta']['case_id']}/{cell['meta']['arm_id']}"
                per_cell[cell["meta"]["case_id"]][cell["meta"]["arm_id"]].append(statistics.median(scores.values()))
        directions[criterion] = _direction(per_cell, "higher", by_reviewer)
    j5_reviewers_by_case: dict[str, dict[str, dict[str, list[float]]]] = {}
    for reviewer_id, data in j5_reviewer.items():
        per_case: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
        for key, scores in data["J5_detection_rate"].items():
            case_id, arm_id = key.rsplit("/", 1)
            per_case[case_id][arm_id].extend(scores)
        j5_reviewers_by_case[reviewer_id] = per_case
    j5_per_cell: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for cell_id, scores in j5_output_scores.items():
        if len(scores) == 2:
            cell = output_to_cell[cell_id]
            j5_per_cell[cell["meta"]["case_id"]][cell["meta"]["arm_id"]].append(
                statistics.median(scores.values()))
    directions["J5_detection_rate"] = _direction(j5_per_cell, "higher", j5_reviewers_by_case)
    return {"status": "collected", "by_output": by_output, "J5_by_reviewer": dict(j5_items),
            "J8_by_reviewer": dict(j8_items), "directional_findings": directions}


def score_store(root: str | Path) -> dict[str, Any]:
    """Build observed metrics only from complete cell records; missing cells remain missing."""
    store = verify_store(root)
    if not store["cells"]:
        raise BenchmarkError("CELLS_NOT_SCORED", "no run cells are recorded")
    if any(cell["meta"]["status"] == "complete" and cell.get("observed") is None for cell in store["cells"]):
        raise BenchmarkError("OBSERVED_MISSING", "complete cells need observed.json before scoring")
    return {"schema_version": "1.0.0", "benchmark_id": store["manifest"]["benchmark_id"],
            "manifest_sha256": store["manifest_sha256"], "status": _store_status(store["cells"], store["manifest"]),
            "observed": _observed(store["cells"]), "missing_cells": _missing(store["cells"], store["manifest"])}


def build_report(root: str | Path) -> dict[str, Any]:
    """Assemble observed and judged evidence without an overall score or superiority claim."""
    store = verify_store(root, reviews=True)
    if any(cell["meta"]["status"] == "complete" and cell.get("observed") is None for cell in store["cells"]):
        raise BenchmarkError("OBSERVED_MISSING", "complete cells need observed.json before reporting")
    scored = score_store(root)
    return {"schema_version": "1.0.0", "benchmark_id": store["manifest"]["benchmark_id"],
            "manifest_sha256": store["manifest_sha256"], "status": scored["status"],
            "observed": scored["observed"], "judged": _judged(store["reviews"], store["cells"], store["manifest"]),
            "missing_cells": scored["missing_cells"],
            "execution_and_rework": {"status": "not_measured",
                                     "reason": "benchmark plans are not executed; only retrospective corrections are separately labelled"},
            "comparison_policy": {"overall_aggregate": "prohibited", "cross_metric_score": "prohibited",
                                  "retrospectives_are_causal": False, "replicates_are_descriptive": True,
                                  "directional_rule": ">=4 complete cases; B median direction in >=4; no case B worse than A worst; both reviewers agree for judged metrics"}}


def _missing(cells: list[dict[str, Any]], manifest: dict[str, Any]) -> list[str]:
    recorded = {cell["cell_id"] for cell in cells}
    expected = {f"{item['case_id']}-{item['arm_id']}-{item['replicate']}" for item in manifest["run_order"]}
    return sorted(expected - recorded)


def _store_status(cells: list[dict[str, Any]], manifest: dict[str, Any]) -> str:
    all_cases_included = all(case["status"] == "included" for case in manifest["cases"])
    all_cells_complete = cells and all(cell["meta"]["status"] == "complete" for cell in cells)
    return "complete" if all_cases_included and all_cells_complete else "incomplete"
