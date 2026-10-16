"""Reproduce the frozen synthetic M2 deterministic-route baseline without inference or network access."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]
REQ_DIR = Path(__file__).resolve().parent
BASELINE_REQ = REQ_DIR.parent / "REQ-013-scheduler-m2-decision-engine-with-local"
CORPUS_PATH = BASELINE_REQ / "fixtures-v1.json"
MANIFEST_PATH = BASELINE_REQ / "fixture-manifest-v1.json"
REPORT_PATH = REQ_DIR / "baseline-report.json"
sys.path.insert(0, str(REPO_ROOT / "skill" / "scripts"))

from bt_scheduler_benchmark import load_fixtures  # noqa: E402


def build_report() -> dict[str, Any]:
    corpus, manifest = load_fixtures(CORPUS_PATH, MANIFEST_PATH)
    raw_corpus = CORPUS_PATH.read_bytes()
    raw_manifest = MANIFEST_PATH.read_bytes()
    cases = corpus["cases"]
    selected: list[dict[str, Any]] = []
    by_family: dict[str, dict[str, int]] = defaultdict(
        lambda: {"cases": 0, "baseline_matches_oracle": 0, "excluded_routes": 0}
    )
    for case in cases:
        options = sorted(case["options"], key=lambda row: (row["baseline_rank"], row["route_id"]))
        route_id = options[0]["route_id"]
        if route_id != case["deterministic_route_id"]:
            raise ValueError("deterministic fixture label does not match the current reference ranking")
        eligible_ids = sorted(row["route_id"] for row in options)
        selected.append(
            {
                "case_id": case["case_id"],
                "selected_route_id": route_id,
                "eligible_route_ids": eligible_ids,
                "quota_headroom": {
                    row["route_id"]: row["features"]["quota_headroom"] for row in options
                },
                "excluded_candidates": case["excluded_candidates"],
            }
        )
        family = by_family[case["family"]]
        family["cases"] += 1
        family["baseline_matches_oracle"] += int(route_id == case["oracle_route_id"])
        family["excluded_routes"] += len(case["excluded_candidates"])

    selected_bytes = json.dumps(
        selected, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    matches = sum(row["baseline_matches_oracle"] for row in by_family.values())
    return {
        "schema_version": 1,
        "source_requirement": "REQ-013",
        "method": "Validate frozen fixtures with bt_scheduler_benchmark.load_fixtures; select the minimum (baseline_rank, route_id); no inference or network access.",
        "fixture": {
            "dataset_version": corpus["dataset_version"],
            "sha256": hashlib.sha256(raw_corpus).hexdigest(),
            "manifest_sha256": hashlib.sha256(raw_manifest).hexdigest(),
            "label_manifest_sha256": manifest["dataset_sha256"],
            "cases": len(cases),
            "splits": dict(sorted(Counter(row["split"] for row in cases).items())),
            "families": dict(sorted(Counter(row["family"] for row in cases).items())),
        },
        "summary": {
            "baseline_matches_oracle": matches,
            "baseline_accuracy_fixture_only": matches / len(cases),
            "hard_filter_violations": sum(
                item["selected_route_id"] not in item["eligible_route_ids"] for item in selected
            ),
            "excluded_routes": sum(len(item["excluded_candidates"]) for item in selected),
            "selected_output_sha256": hashlib.sha256(selected_bytes).hexdigest(),
        },
        "by_family": dict(sorted(by_family.items())),
        "limitations": [
            "Synthetic rubric labels are not real task acceptance outcomes.",
            "The fixture accuracy is not a calibrated probability or a quota-efficiency measurement.",
            "The benchmark does not model provider-side usage changes or concurrent sessions.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true")
    action.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    report = build_report()
    rendered = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.write:
        REPORT_PATH.write_text(rendered, encoding="utf-8")
        print(f"wrote {REPORT_PATH}")
        return 0
    expected = REPORT_PATH.read_text(encoding="utf-8")
    if expected != rendered:
        print("baseline-report.json does not match the frozen fixture output", file=sys.stderr)
        return 1
    print("baseline fixture, deterministic output digest, and report match")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
