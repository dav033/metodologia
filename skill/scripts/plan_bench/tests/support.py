from __future__ import annotations

import hashlib
import io
import json
import tarfile
from pathlib import Path
from typing import Any

from plan_bench.contract import (
    BENCHMARK_ID,
    CELL_SCHEMA_VERSION,
    RUBRIC_SHA256,
    RUBRIC_VERSION,
    SCHEMA_VERSION,
    case_input_sha256,
    expected_cells,
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value: object) -> bytes:
    raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return raw


def make_store(root: Path, *, included_cases: int = 5, write_cells: bool = False,
               write_reviews: bool = False) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    cases = []
    for index in range(1, 6):
        case_id = f"C{index}"
        if index > included_cases:
            cases.append({"case_id": case_id, "status": "excluded", "exclusion_reason": "snapshot unavailable in test fixture"})
            continue
        input_path = f"inputs/{case_id}/SPEC.md"
        input_raw = f"# Synthetic test-only input {case_id}\n".encode()
        (root / input_path).parent.mkdir(parents=True, exist_ok=True)
        (root / input_path).write_bytes(input_raw)
        snapshot_path = f"workspaces/{case_id}/source.tar"
        snapshot_buffer = io.BytesIO()
        with tarfile.open(fileobj=snapshot_buffer, mode="w") as archive:
            member = tarfile.TarInfo("README.md")
            snapshot_raw = f"synthetic repository snapshot {case_id}\n".encode()
            member.size = len(snapshot_raw)
            archive.addfile(member, io.BytesIO(snapshot_raw))
        snapshot_raw = snapshot_buffer.getvalue()
        (root / snapshot_path).parent.mkdir(parents=True, exist_ok=True)
        (root / snapshot_path).write_bytes(snapshot_raw)
        oracle_path = f"oracles/{case_id}.json"
        oracle_raw = b'{"oracle_ids":["RISK-1","RISK-2"]}\n'
        (root / oracle_path).parent.mkdir(parents=True, exist_ok=True)
        (root / oracle_path).write_bytes(oracle_raw)
        case = {
            "case_id": case_id,
            "status": "included",
            "input_files": [{"path": input_path, "sha256": _sha(input_raw)},
                            {"path": snapshot_path, "sha256": _sha(snapshot_raw)}],
            "input_sha256": "0" * 64,
            "oracle_file": oracle_path,
            "oracle_sha256": _sha(oracle_raw),
            "oracle_ids": ["RISK-1", "RISK-2"],
            "repository_sha256": _sha(snapshot_raw),
            "repository_role": "synthetic",
            "exclusion_reason": None,
        }
        case["input_sha256"] = case_input_sha256(case)
        cases.append(case)

    arms = [
        {"arm_id": "A", "version": "current_v2", "source_sha256": _sha(b"current-source"),
         "agent_config_sha256": _sha(b"current-config"), "profile_id": "claude-work", "runtime_id": "claude-code",
         "runtime_version": "2.1.301", "model_id": "claude-opus-5-5", "effort": "high",
         "tools": ["Read", "Grep", "Glob"], "permission_mode": "plan", "session_persistence": False,
         "timeout_seconds": 1800},
        {"arm_id": "B", "version": "improved_v2", "source_sha256": _sha(b"improved-source"),
         "agent_config_sha256": _sha(b"improved-config"), "profile_id": "claude-work", "runtime_id": "claude-code",
         "runtime_version": "2.1.301", "model_id": "claude-opus-5-5", "effort": "high",
         "tools": ["Read", "Grep", "Glob"], "permission_mode": "plan", "session_persistence": False,
         "timeout_seconds": 1800},
    ]
    retrospectives = []
    for output_id in ("V1_RAW", "V1_EDITED", "V2_RERUN_20261016"):
        path = f"retrospective/{output_id}.md"
        raw = f"# Test-only retrospective placeholder {output_id}\n".encode()
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_bytes(raw)
        retrospectives.append({"output_id": output_id, "label": f"test-only {output_id}", "path": path,
                               "sha256": _sha(raw)})

    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "benchmark_id": BENCHMARK_ID,
        "frozen_at_utc": "2026-10-16T12:00:00Z",
        "seed": 1729,
        "shuffle_algorithm": "sha256-seeded-sort-v1",
        "rubric_version": RUBRIC_VERSION,
        "rubric_sha256": RUBRIC_SHA256,
        "prompt_template_sha256": _sha(b"test-only prompt template"),
        "cases": cases,
        "arms": arms,
        "repetitions": 3,
        "run_order": [],
        "retrospectives": retrospectives,
        "reviewers": [
            {"reviewer_id": "reviewer-1", "profile_id": "test-profile-1", "model_id": "test-model-1"},
            {"reviewer_id": "reviewer-2", "profile_id": "test-profile-2", "model_id": "test-model-2"},
        ],
        "limits": {"matched_run_cap": 30, "reference_run_cap": 1, "review_record_cap": 66,
                   "reviews_per_output": 2, "timeout_seconds": 1800},
    }
    manifest["run_order"] = expected_cells(manifest)
    manifest_raw = write_json(root / "manifest.json", manifest)
    (root / "manifest.sha256").write_text(_sha(manifest_raw) + "\n", encoding="ascii")
    if write_cells:
        _write_cells(root, manifest, write_reviews=write_reviews)
    return manifest


def _metric_records(cell_path: Path, cell: dict[str, Any]) -> dict[str, Any]:
    arm = cell["arm_id"]
    b = arm == "B"
    count = 1 if b else 3
    coverage = 0.9 if b else 0.6
    command = f"python3 -m bt_planner check {cell['cell_id']} --json"
    values = {
        "O1": ({"errors": count, "warnings": count}, float(count * 2), "count"),
        "O2": ({"covered": 2 if b else 1, "requirements": 2,
                "per_requirement": {"R1": True, "R2": b}}, coverage, "ratio"),
        "O3": (count, float(count), "count"),
        "O4": (count, float(count), "count"),
        "O5": (4 if b else 2, float(4 if b else 2), "count"),
        "O6": (count, float(count), "count"),
        "O7": ({"planned": 1, "cited_as_existing": 0}, None, "count"),
        "O8": ({"tasks": 4, "critical_path_minutes": 20, "widest_level": 2,
                "unordered_shared_pairs": [], "interfaces": 1}, None, "mixed"),
        "O9": ({"wall_seconds": 100.0, "exit_status": 0, "tokens": None, "cost_usd": None}, None, "mixed"),
    }
    result = {}
    for metric_id, (value, comparison, unit) in values.items():
        source_path = f"sources/{metric_id}.json"
        raw = json.dumps({"fixture": "synthetic-test-only", "metric": metric_id, "cell_id": cell["cell_id"]},
                         sort_keys=True).encode() + b"\n"
        (cell_path / source_path).parent.mkdir(parents=True, exist_ok=True)
        (cell_path / source_path).write_bytes(raw)
        result[metric_id] = {"status": "measured", "value": value, "comparison_value": comparison,
                             "unit": unit, "source_command": command, "source_path": source_path,
                             "source_sha256": _sha(raw)}
    return result


def _evidence() -> list[dict[str, str]]:
    return [{"location": "PLAN.md M1/T1", "quote": "Implement the scoped behavior and verify the contract."}]


def _review(blind_id: str, reviewer_id: str, oracle_ids: list[str], score: int, detected: bool) -> dict[str, Any]:
    scores: dict[str, Any] = {key: {"score": score, "evidence": _evidence()}
                              for key in ("J1", "J2", "J3", "J4", "J6", "J7")}
    scores["J5"] = {"oracles": [{"oracle_id": item, "detected": detected, "evidence": _evidence()}
                                  for item in oracle_ids], "new_risks": []}
    scores["J8"] = {"findings": []}
    return {"schema_version": "1.0.0", "blind_output_id": blind_id, "reviewer_id": reviewer_id,
            "rubric": {"version": RUBRIC_VERSION, "sha256": RUBRIC_SHA256}, "scores": scores}


def _write_cells(root: Path, manifest: dict[str, Any], *, write_reviews: bool) -> None:
    map_entries = []
    cells_by_id = {}
    for cell in manifest["run_order"]:
        cell_id = f"{cell['case_id']}-{cell['arm_id']}-{cell['replicate']}"
        cell_path = root / "runs" / cell["case_id"] / cell["arm_id"] / str(cell["replicate"])
        cell_path.mkdir(parents=True, exist_ok=True)
        case = next(item for item in manifest["cases"] if item["case_id"] == cell["case_id"])
        arm = next(item for item in manifest["arms"] if item["arm_id"] == cell["arm_id"])
        plan_md = f"# Test-only plan {cell_id}\n".encode()
        plan_json = json.dumps({"schema_version": "1.2.0", "plan_id": cell_id}, sort_keys=True).encode() + b"\n"
        (cell_path / "PLAN.md").write_bytes(plan_md)
        (cell_path / "PLAN.json").write_bytes(plan_json)
        meta = {
            "schema_version": CELL_SCHEMA_VERSION, "cell_id": cell_id, **cell, "status": "complete",
            "profile_id": arm["profile_id"], "runtime_id": arm["runtime_id"],
            "runtime_version": arm["runtime_version"],
            "model_id": arm["model_id"], "effort": arm["effort"], "tools": arm["tools"],
            "permission_mode": arm["permission_mode"], "timeout_seconds": arm["timeout_seconds"],
            "input_sha256": case["input_sha256"], "repository_sha256": case["repository_sha256"],
            "prompt_template_sha256": manifest["prompt_template_sha256"],
            "agent_config_sha256": arm["agent_config_sha256"],
            "started_at_utc": "2026-10-16T12:00:00Z", "finished_at_utc": "2026-10-16T12:01:40Z",
            "elapsed_seconds": 100.0, "exit_status": 0, "timed_out": False, "attempt_count": 1,
            "reported_tokens": None, "reported_cost_usd": None,
            "plan_md_sha256": _sha(plan_md), "plan_json_sha256": _sha(plan_json), "incomplete_reason": None,
        }
        write_json(cell_path / "meta.json", meta)
        write_json(cell_path / "observed.json", {"schema_version": "1.0.0", "cell_id": cell_id,
                                                 "metrics": _metric_records(cell_path,
                                                                            {**cell, "cell_id": cell_id})})
        cells_by_id[cell_id] = case["oracle_ids"]
        map_entries.append({"output_id": cell_id, "blind_output_id": f"blind-{len(map_entries) + 1:03d}",
                            "case_id": cell["case_id"]})
    for retrospective in manifest["retrospectives"]:
        map_entries.append({"output_id": retrospective["output_id"],
                            "blind_output_id": f"blind-{len(map_entries) + 1:03d}", "case_id": "C1"})
    if write_reviews:
        write_json(root / "review-map.private.json", {"schema_version": "1.0.0", "outputs": map_entries})
        for entry in map_entries:
            oracle_ids = cells_by_id.get(entry["output_id"], ["RISK-1", "RISK-2"])
            cell_id = entry["output_id"] if entry["output_id"] in cells_by_id else None
            arm = cell_id.split("-")[1] if cell_id else "retrospective"
            score = (3 if arm == "B" else 1) if arm != "retrospective" else 2
            detected = arm == "B"
            for reviewer in manifest["reviewers"]:
                review = _review(entry["blind_output_id"], reviewer["reviewer_id"], oracle_ids, score, detected)
                write_json(root / "reviews" / entry["blind_output_id"] / f"{reviewer['reviewer_id']}.json", review)
