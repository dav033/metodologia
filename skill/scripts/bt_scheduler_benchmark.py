"""Hash-checked frozen synthetic corpus and privacy-bounded Laya prompt construction."""
from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

from bt_scheduler_decision import sha256_json

DATASET_VERSION = "scheduler-m2-synthetic-choice-v1"
FAMILIES = ("quota_capacity", "risk_effort", "history", "resource_dependency", "ambiguous_tradeoff")


class FixtureError(ValueError):
    pass


def load_fixtures(corpus_path: str | Path, manifest_path: str | Path) -> tuple[dict[str, Any], dict[str, Any]]:
    corpus_file, manifest_file = Path(corpus_path), Path(manifest_path)
    raw = corpus_file.read_bytes()
    try:
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        corpus = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FixtureError("fixture corpus or manifest is missing or invalid") from exc
    digest = hashlib.sha256(raw).hexdigest()
    if not isinstance(corpus, dict) or not isinstance(manifest, dict) or \
            corpus.get("dataset_version") != DATASET_VERSION or manifest.get("dataset_version") != DATASET_VERSION or \
            manifest.get("dataset_sha256") != digest or manifest.get("frozen_before_first_laya_call") is not True:
        raise FixtureError("fixture hash, version or pre-inference freeze marker does not match")
    if corpus.get("label_protocol") != manifest.get("label_protocol"):
        raise FixtureError("fixture label protocol does not match the frozen manifest")
    cases = corpus.get("cases")
    if not isinstance(cases, list) or len(cases) != 200 or manifest.get("cases") != len(cases):
        raise FixtureError("frozen corpus must contain exactly 200 cases")
    ids = [case.get("case_id") for case in cases if isinstance(case, dict)]
    if len(ids) != len(cases) or len(ids) != len(set(ids)):
        raise FixtureError("fixture case IDs are missing or duplicated")
    splits = {
        "calibration": [case for case in cases if case.get("split") == "calibration"],
        "held_out": [case for case in cases if case.get("split") == "held_out"],
    }
    for split, expected_ids in (("calibration", manifest.get("calibration_case_ids")),
                                ("held_out", manifest.get("held_out_case_ids"))):
        actual_ids = [case["case_id"] for case in splits[split]]
        if len(actual_ids) != 100 or actual_ids != expected_ids:
            raise FixtureError(f"{split} case IDs do not match the manifest")
        counts = Counter(case.get("family") for case in splits[split])
        if counts != Counter({family: 20 for family in FAMILIES}):
            raise FixtureError(f"{split} family strata do not match the frozen protocol")
    calibration = set(manifest["calibration_case_ids"])
    held_out = set(manifest["held_out_case_ids"])
    if calibration & held_out:
        raise FixtureError("calibration and held-out case IDs overlap")
    digests = [case.get("task_sha256") for case in cases]
    if len(digests) != len(set(digests)) or manifest.get("duplicate_canonical_task_digests_across_splits") != 0:
        raise FixtureError("canonical task digests overlap or duplicate")
    for case in cases:
        if case.get("family") not in FAMILIES:
            raise FixtureError("fixture family is unsupported")
        options = case.get("options")
        eligible = case.get("eligible_route_ids")
        if not isinstance(options, list) or not 2 <= len(options) <= 8 or not isinstance(eligible, list):
            raise FixtureError("fixture candidate set is invalid")
        option_ids = {item.get("route_id") for item in options if isinstance(item, dict) and item.get("eligible") is True}
        if option_ids != set(eligible) or len(option_ids) != len(options):
            raise FixtureError("fixture has a candidate outside its eligible set")
        if case.get("oracle_route_id") not in option_ids or case.get("deterministic_route_id") not in option_ids:
            raise FixtureError("fixture labels are outside the eligible set")
        utilities = case.get("oracle_utilities")
        if not isinstance(utilities, dict) or set(utilities) != option_ids or any(
                not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value)
                for value in utilities.values()):
            raise FixtureError("fixture oracle utilities are invalid")
        if case.get("language") not in {"en", "es"}:
            raise FixtureError("fixture language is unsupported")
        if not isinstance(case.get("priority_weights"), dict) or not isinstance(case.get("classifications"), dict):
            raise FixtureError("fixture task facts or oracle weights are invalid")
        weights = case["priority_weights"]
        utilities = {}
        option_features = {}
        for item in options:
            features = item.get("features")
            if not isinstance(features, dict) or set(features) != set(weights):
                raise FixtureError("fixture feature dimensions differ from their oracle weights")
            try:
                utility = sum(weights[key] * features[key] for key in weights)
            except (TypeError, KeyError) as exc:
                raise FixtureError("fixture utility values are invalid") from exc
            if not math.isfinite(utility):
                raise FixtureError("fixture utility is not finite")
            utilities[item["route_id"]] = round(utility, 8)
            option_features[item["route_id"]] = features
        expected_oracle = min(utilities, key=lambda route: (-utilities[route], route))
        expected_baseline = min(options, key=lambda item: (item["baseline_rank"], item["route_id"]))["route_id"]
        if expected_oracle != case["oracle_route_id"] or utilities != case["oracle_utilities"] or \
                expected_baseline != case["deterministic_route_id"]:
            raise FixtureError("fixture oracle or baseline label does not match the frozen rubric")
        expected_task_digest = sha256_json({"brief": case["task"], "classifications": case["classifications"],
                                            "priority_weights": weights, "options": option_features})
        if expected_task_digest != case["task_sha256"]:
            raise FixtureError("fixture canonical task digest does not match task facts and candidates")
    return corpus, manifest


def laya_payload(case: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    """Build exactly the unlabeled state sent to Laya; no answer labels/utilities enter this function."""
    options = sorted(case["options"], key=lambda item: item["route_id"])
    label_to_route = {}
    criteria = {}
    summaries = []
    for index, item in enumerate(options, start=1):
        label = f"option-{index}"
        label_to_route[label] = item["route_id"]
        features = item["features"]
        detail = (
            f"provider={item['provider']}; model={item['model']}; effort={item['effort'] or 'provider-default'}; "
            f"profile={item['profile']}; quality_fit={features['quality_fit']:.3f}; "
            f"quota_headroom={features['quota_headroom']:.3f}; latency_fit={features['latency_fit']:.3f}; "
            f"verified_record={features['verified_record']:.3f}; risk_fit={features['risk_fit']:.3f}; "
            f"resource_fit={features['resource_fit']:.3f}; effort_fit={features['effort_fit']:.3f}"
        )
        criteria[label] = detail
        summaries.append({"label": label, "details": detail})
    state = {
        "task": case["task"],
        "classifications": case["classifications"],
        "eligible_candidates": summaries,
    }
    question = {
        "type": "choice",
        "instructions": "Choose the eligible route that best follows the task priorities and candidate measurements. "
                        "Consider the stated weights; return one listed option only.",
        "criteria": criteria,
    }
    return {"state": state, "questions": {"decision": question}, "lang": case["language"]}, label_to_route


def parse_choice(result: object, labels: dict[str, str]) -> tuple[str | None, float | None]:
    if not isinstance(result, dict):
        return None, None
    answers = result.get("answers")
    answer = answers.get("decision") if isinstance(answers, dict) else None
    if not isinstance(answer, dict) or answer.get("type") != "choice":
        return None, None
    route = labels.get(answer.get("choice"))
    confidence = answer.get("answer_confidence")
    if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not math.isfinite(confidence):
        confidence = None
    return route, float(confidence) if confidence is not None else None
