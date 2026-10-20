"""Compare frozen offline routing baselines without provider calls or synthetic learning labels."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from bt_scheduler_benchmark import FixtureError, load_fixtures
from bt_scheduler_decision import (
    Candidate,
    DecisionRequest,
    RouteHistory,
    TaskFacts,
    account_reference,
    candidate_route_id,
    plan_ready_batch,
    rank_candidates,
    sha256_json,
)
from bt_scheduler_decision.policy import rank_with_route_policy

REPO_ROOT = Path(__file__).resolve().parents[2]
REQ_DIR = REPO_ROOT / "bitacora" / "metodologia" / "requirements" / \
    "REQ-020-scheduler-m2-learning-and-quota-optimiza"
BASELINE_REQ_DIR = REQ_DIR.parent / "REQ-013-scheduler-m2-decision-engine-with-local"
CORPUS_PATH = BASELINE_REQ_DIR / "fixtures-v1.json"
MANIFEST_PATH = BASELINE_REQ_DIR / "fixture-manifest-v1.json"
EXPECTED_CORPUS_SHA256 = "b5cbcc43d70b7fbd2a191400cad411ba5e8992d1b49b30d10d406575c2228b2d"
EXPECTED_MANIFEST_SHA256 = "f1644af9e0a53ff392e7520cef08af55934fede6f80510e2349d47ed3f6ee5be"
BENCHMARK_VERSION = "req020-offline-routing-comparison-v1"
EVALUATION_SPLIT = "held_out"
FIXTURE_NOW = 100.0
FIXTURE_QUOTA_VALID_UNTIL = 200.0
_CLASSIFICATION_EVIDENCE_DIMENSIONS = ("complexity", "scope", "duration", "risk", "coupling", "confidence")


class BenchmarkError(ValueError):
    """Stable, offline benchmark input or invariant failure."""


class _EligibleRoundRobin:
    def __init__(self, all_route_ids: set[str]):
        self.route_order = tuple(sorted(all_route_ids))
        self.position = 0

    def select(self, eligible_route_ids: set[str]) -> str:
        for offset in range(len(self.route_order)):
            index = (self.position + offset) % len(self.route_order)
            route_id = self.route_order[index]
            if route_id in eligible_route_ids:
                self.position = (index + 1) % len(self.route_order)
                return route_id
        raise BenchmarkError("eligible round-robin received no eligible routes")


def _load_frozen_cases() -> tuple[list[dict[str, Any]], dict[str, str]]:
    corpus_bytes = CORPUS_PATH.read_bytes()
    manifest_bytes = MANIFEST_PATH.read_bytes()
    corpus_sha256 = hashlib.sha256(corpus_bytes).hexdigest()
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    if corpus_sha256 != EXPECTED_CORPUS_SHA256 or manifest_sha256 != EXPECTED_MANIFEST_SHA256:
        raise BenchmarkError("frozen source fixture digest changed; review and version a new snapshot")
    corpus, manifest = load_fixtures(CORPUS_PATH, MANIFEST_PATH)
    cases = [case for case in corpus["cases"] if case["split"] == EVALUATION_SPLIT]
    if len(cases) != 100 or len({case["case_id"] for case in cases}) != len(cases):
        raise BenchmarkError("held-out benchmark split must contain 100 unique cases")
    return cases, {
        "dataset_version": corpus["dataset_version"],
        "corpus_sha256": corpus_sha256,
        "manifest_sha256": manifest_sha256,
        "label_manifest_sha256": manifest["dataset_sha256"],
        "baseline_protocol": corpus["baseline_protocol"],
    }


def _request_for_case(case: dict[str, Any], source_sha256: str) -> DecisionRequest:
    evidence = {
        name: {
            "justification": "Synthetic benchmark metadata is used only to construct the frozen request.",
            "evidence": [f"assumption:req013-synthetic-{name}"],
        }
        for name in _CLASSIFICATION_EVIDENCE_DIMENSIONS
    }
    task = TaskFacts(
        task_id=case["case_id"],
        brief=case["task"],
        classifications=dict(case["classifications"]),
        classification_evidence=evidence,
        acceptance_criteria=("Select one eligible route for the synthetic fixture.",),
        verification=({"type": "command", "value": "offline-fixture-only"},),
        shared_resources=("synthetic-offline-benchmark",),
    )
    candidates = []
    for option in case["options"]:
        route_id = candidate_route_id(option["provider"], option["model"], option["profile"], option["effort"])
        if route_id != option["route_id"]:
            raise BenchmarkError("fixture route identity does not match the M2 route contract")
        quota_percent = option["observed_context"]["quota_used_percent"]
        if not isinstance(quota_percent, (int, float)) or isinstance(quota_percent, bool) or \
                not math.isfinite(quota_percent) or not 0 <= quota_percent < 100:
            raise BenchmarkError("synthetic fixture quota input is outside the bounded available range")
        provider_account = account_reference(f"fixture:{option['provider']}:{option['profile']}")
        candidates.append(Candidate(
            route_id=route_id,
            provider=option["provider"],
            model=option["model"],
            profile=option["profile"],
            account_ref=provider_account,
            effort=option["effort"],
            source_status="available",
            source_reason_codes=(),
            profile_authorized=True,
            auth_status="valid",
            runtime_status="available",
            quota_status="available",
            quota_observed_at=FIXTURE_NOW,
            quota_valid_until=FIXTURE_QUOTA_VALID_UNTIL,
            quota_used_percent=float(quota_percent),
            baseline_rank=option["baseline_rank"],
            history=RouteHistory(),
        ))
    if len(candidates) != len(case["eligible_route_ids"]):
        raise BenchmarkError("frozen candidate count differs from its eligible route set")
    return DecisionRequest(
        plan_id="REQ-020-offline-frozen-benchmark",
        revision=1,
        plan_sha256=source_sha256,
        free_slots=1,
        requested_at=FIXTURE_NOW,
        task=task,
        candidates=tuple(candidates),
        policy_version="m2-route-policy-v1",
        checkpoint_revision=None,
    )


def _snapshot_sha256(cases: list[dict[str, Any]], source: dict[str, str]) -> str:
    return sha256_json({
        "benchmark_version": BENCHMARK_VERSION,
        "dataset_version": source["dataset_version"],
        "corpus_sha256": source["corpus_sha256"],
        "manifest_sha256": source["manifest_sha256"],
        "evaluation_split": EVALUATION_SPLIT,
        "cases": tuple({
            "case_id": case["case_id"],
            "task_sha256": case["task_sha256"],
            "eligible_route_ids": tuple(sorted(case["eligible_route_ids"])),
            "options": tuple({
                "route_id": option["route_id"],
                "provider": option["provider"],
                "model": option["model"],
                "profile": option["profile"],
                "effort": option["effort"],
                "baseline_rank": option["baseline_rank"],
                "features": option["features"],
                "synthetic_context": option["observed_context"],
            } for option in case["options"]),
        } for case in cases),
        "resource_snapshot": {"free_slots_per_case": 1, "cross_case_account_concurrency": "not_modelled"},
    })


def _percentile(values: list[float], quantile: float) -> float | None:
    return sorted(values)[max(0, math.ceil(quantile * len(values)) - 1)] if values else None


def _mean(values: list[float]) -> float | None:
    return statistics.fmean(values) if values else None


def _method_metrics(cases: list[dict[str, Any]], selections: list[dict[str, str]], elapsed_ns: list[int],
                    fallback_reasons: Counter[str] | None = None) -> dict[str, Any]:
    selected_by_case = {row["case_id"]: row["route_id"] for row in selections}
    if len(selections) != len(cases) or len(selected_by_case) != len(cases):
        raise BenchmarkError("a routing method did not emit exactly one selection per frozen case")

    quality_regrets: list[float] = []
    quality_matches = 0
    utility_values: list[float] = []
    quota_headroom_values: list[float] = []
    synthetic_load_values: list[float] = []
    by_family: dict[str, dict[str, Any]] = defaultdict(lambda: {"cases": 0, "oracle_matches": 0, "regret": []})
    for case in cases:
        route_id = selected_by_case[case["case_id"]]
        utilities = case["oracle_utilities"]
        if route_id not in case["eligible_route_ids"] or route_id not in utilities:
            raise BenchmarkError("a routing method selected a route outside the frozen eligible set")
        utility_values.append(float(utilities[route_id]))
        regret = max(utilities.values()) - utilities[route_id]
        quality_regrets.append(float(regret))
        matched = route_id == case["oracle_route_id"]
        quality_matches += int(matched)
        family = by_family[case["family"]]
        family["cases"] += 1
        family["oracle_matches"] += int(matched)
        family["regret"].append(float(regret))
        option = next(item for item in case["options"] if item["route_id"] == route_id)
        quota_headroom_values.append(float(option["features"]["quota_headroom"]))
        synthetic_load_values.append(float(option["observed_context"]["load_minutes"]))

    family_metrics = {
        name: {
            "cases": values["cases"],
            "synthetic_oracle_accuracy": values["oracle_matches"] / values["cases"],
            "mean_synthetic_oracle_regret": _mean(values["regret"]),
        }
        for name, values in sorted(by_family.items())
    }
    timings_ms = [elapsed / 1_000_000 for elapsed in elapsed_ns]
    output_hash = sha256_json(selections)
    result = {
        "cases": len(cases),
        "selected_cases": len(selections),
        "selection_coverage": len(selections) / len(cases),
        "selected_output_sha256": output_hash,
        "quality": {
            "label_kind": "synthetic_oracle_utility_not_verified_acceptance",
            "synthetic_oracle_accuracy": quality_matches / len(cases),
            "synthetic_oracle_quality_coverage": 1.0,
            "mean_selected_synthetic_utility": _mean(utility_values),
            "mean_synthetic_oracle_regret": _mean(quality_regrets),
            "verified_acceptance_coverage": 0.0,
            "verified_acceptance_rate": None,
            "by_family": family_metrics,
        },
        "quota": {
            "selected_route_synthetic_headroom_coverage": len(quota_headroom_values) / len(cases),
            "mean_selected_synthetic_quota_headroom": _mean(quota_headroom_values),
            "observed_account_window_coverage": 0.0,
            "verified_tasks_per_observed_account_window": None,
            "quota_exhaustions": None,
        },
        "attribution": {
            "attributed_usage_coverage": 0.0,
            "measured_task_quota_deltas": None,
        },
        "duration": {
            "selected_route_synthetic_load_coverage": len(synthetic_load_values) / len(cases),
            "mean_selected_synthetic_load_minutes": _mean(synthetic_load_values),
            "observed_time_to_verified_coverage": 0.0,
            "time_to_verified_minutes": None,
        },
        "human_intervention": {"observed_coverage": 0.0, "intervention_count": None, "rate": None},
        "optimizer_cost": {
            "measurement": "local selection wall-clock; not provider or task runtime",
            "selection_evaluations": len(elapsed_ns),
            "median_ms": statistics.median(timings_ms) if timings_ms else None,
            "p95_ms": _percentile(timings_ms, 0.95),
        },
    }
    if fallback_reasons is not None:
        result["contextual_fallbacks"] = dict(sorted(fallback_reasons.items()))
    return result


def build_report() -> dict[str, Any]:
    cases, source = _load_frozen_cases()
    source_sha256 = sha256_json({
        "corpus_sha256": source["corpus_sha256"],
        "manifest_sha256": source["manifest_sha256"],
    })
    snapshot_sha256 = _snapshot_sha256(cases, source)
    all_route_ids = {route_id for case in cases for route_id in case["eligible_route_ids"]}
    round_robin = _EligibleRoundRobin(all_route_ids)
    selections: dict[str, list[dict[str, str]]] = {
        "fifo_first_eligible": [],
        "eligible_round_robin": [],
        "legacy_router_frozen_output": [],
        "m2_deterministic": [],
        "m2_contextual_missing_history_fallback": [],
    }
    timings: dict[str, list[int]] = {name: [] for name in selections}
    contextual_fallbacks: Counter[str] = Counter()

    for case in cases:
        eligible = set(case["eligible_route_ids"])
        options = case["options"]
        request = _request_for_case(case, source_sha256)
        if {item.route_id for item in request.candidates} != eligible:
            raise BenchmarkError("M2 request does not contain the exact frozen eligible candidate set")

        started = time.perf_counter_ns()
        fifo_route = next(option["route_id"] for option in options if option["route_id"] in eligible)
        timings["fifo_first_eligible"].append(time.perf_counter_ns() - started)

        started = time.perf_counter_ns()
        round_robin_route = round_robin.select(eligible)
        timings["eligible_round_robin"].append(time.perf_counter_ns() - started)

        legacy_route = case["deterministic_route_id"]
        if legacy_route not in eligible:
            raise BenchmarkError("frozen legacy router output is not in the eligible route set")

        started = time.perf_counter_ns()
        deterministic = rank_candidates(request)
        if len(deterministic.eligible) != len(eligible) or deterministic.selected is None:
            raise BenchmarkError("deterministic M2 changed the frozen eligible route set")
        deterministic_route = deterministic.selected.route_id
        timings["m2_deterministic"].append(time.perf_counter_ns() - started)

        started = time.perf_counter_ns()
        # Production (`bt_scheduler_plan_routing.plan_full_dag`) keeps the router's order for every task that is not
        # documentation, because that order is already quota- and role-aware; the offline cases model that default.
        policy_ranking = rank_with_route_policy(request, {}, risk=case["classifications"].get("risk"),
                                                preserve_baseline=True)
        contextual_plan = plan_ready_batch((request,), route_evidence_by_task={case["case_id"]: {}},
                                           preserve_baseline_by_task={case["case_id"]: True})
        if len(contextual_plan.assignments) != 1 or not policy_ranking.eligible:
            raise BenchmarkError("contextual M2 failed to produce one eligible offline recommendation")
        contextual_route = contextual_plan.assignments[0].route_id
        # The fallback is named after the input condition (no verified quality history), not after the policy switch
        # that preserves the baseline; the invariant checked below (contextual == deterministic) is what matters.
        contextual_fallbacks["quality_evidence_unavailable"] += 1
        if contextual_route != policy_ranking.selected.route_id:
            raise BenchmarkError("contextual batch and route-policy selections disagree")
        timings["m2_contextual_missing_history_fallback"].append(time.perf_counter_ns() - started)

        if deterministic_route != legacy_route:
            raise BenchmarkError("deterministic M2 no longer reproduces the frozen legacy route")
        if contextual_route != deterministic_route:
            raise BenchmarkError("contextual M2 did not preserve deterministic fallback without verified history")
        for method, route_id in (
            ("fifo_first_eligible", fifo_route),
            ("eligible_round_robin", round_robin_route),
            ("legacy_router_frozen_output", legacy_route),
            ("m2_deterministic", deterministic_route),
            ("m2_contextual_missing_history_fallback", contextual_route),
        ):
            selections[method].append({"case_id": case["case_id"], "route_id": route_id})

    method_definitions = {
        "fifo_first_eligible": "First route in the frozen options order; all listed routes are eligible.",
        "eligible_round_robin": "Stable SHA-256 route order with one shared cursor; skip routes absent from each eligible set.",
        "legacy_router_frozen_output": "Frozen deterministic_route_id from the fixture protocol recorded from bt_agents.candidates; no live router or provider call.",
        "m2_deterministic": "Current M2 rank_candidates() on the same validated request and eligible candidates.",
        "m2_contextual_missing_history_fallback": "Current M2 batch and route policy with no correlated verified outcomes, baseline preserved as in production; missing history must preserve deterministic fallback.",
    }
    methods = []
    legacy_by_case = {row["case_id"]: row["route_id"] for row in selections["legacy_router_frozen_output"]}
    for method, rows in selections.items():
        metrics = _method_metrics(
            cases,
            rows,
            timings[method],
            contextual_fallbacks if method == "m2_contextual_missing_history_fallback" else None,
        )
        metrics["agreement_with_legacy_frozen_output"] = sum(
            row["route_id"] == legacy_by_case[row["case_id"]] for row in rows
        ) / len(cases)
        methods.append({
            "method_id": method,
            "definition": method_definitions[method],
            "input_snapshot_sha256": snapshot_sha256,
            "eligible_candidate_count": sum(len(case["eligible_route_ids"]) for case in cases),
            "selections": rows,
            "metrics": metrics,
        })

    return {
        "schema_version": 1,
        "benchmark_version": BENCHMARK_VERSION,
        "mode": "offline",
        "evaluation_split": EVALUATION_SPLIT,
        "synthetic_diagnostic_only": True,
        "same_frozen_input_for_all_methods": True,
        "inputs": {
            **source,
            "snapshot_sha256": snapshot_sha256,
            "case_count": len(cases),
            "eligible_candidate_count": sum(len(case["eligible_route_ids"]) for case in cases),
            "resource_model": {
                "free_slots_per_case": 1,
                "cross_case_account_concurrency": "not_modelled_by_source_fixture",
                "all_methods_share_resource_snapshot": True,
            },
            "verified_quality_history_cases": 0,
            "real_quota_window_observations": 0,
            "attributable_usage_delta_observations": 0,
            "verified_acceptance_outcomes": 0,
            "human_intervention_observations": 0,
        },
        "methods": methods,
        "limitations": [
            "The frozen held-out labels and route features are synthetic; oracle accuracy and regret are not real acceptance outcomes or calibrated success probabilities.",
            "No non-synthetic correlated PASS/FAIL history is present, so contextual M2 correctly exercises the deterministic fallback and does not learn from synthetic labels.",
            "Quota headroom and load minutes are synthetic route features; the fixture has no fresh account-window observations, attributed quota deltas, or real concurrency snapshot.",
            "Provider usage, verified task duration, human interventions, and quota exhaustion rates are unobserved and reported as uncovered rather than zero.",
            "The legacy method reuses the frozen fixture's recorded bt_agents.candidates output; it does not invoke a live router, provider, or credential source.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("offline",), required=True)
    parser.add_argument("--json", type=Path, required=True, dest="json_path")
    args = parser.parse_args(argv)
    try:
        report = build_report()
        rendered = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        args.json_path.parent.mkdir(parents=True, exist_ok=True)
        args.json_path.write_text(rendered, encoding="utf-8")
    except (BenchmarkError, FixtureError, OSError, ValueError) as exc:
        print(f"offline benchmark failed: {exc}", file=sys.stderr)
        return 1
    print(f"wrote {args.json_path} ({report['inputs']['case_count']} frozen held-out cases)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
