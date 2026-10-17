"""Versioned, provider-independent benchmark record contracts."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

BENCHMARK_ID = "req024-planner-quality-v1"
SCHEMA_VERSION = "1.1.0"
CELL_SCHEMA_VERSION = "1.1.0"
RUBRIC_VERSION = "1.0.0"
RUBRIC_SHA256 = "519cf844f79c1aa8b395ef6b08157db803e38abfa2dc29ad6ee6f020bd357885"
CASE_IDS = ("C1", "C2", "C3", "C4", "C5")
RETROSPECTIVE_IDS = ("V1_RAW", "V1_EDITED", "V2_RERUN_20261016")
METRIC_IDS = tuple(f"O{number}" for number in range(1, 10))
REVIEW_SCORE_IDS = ("J1", "J2", "J3", "J4", "J6", "J7")
HEX64 = re.compile(r"^[a-f0-9]{64}$")
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


class BenchmarkError(ValueError):
    """A malformed or inconsistent benchmark record with a stable error code."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def _object(value: object, name: str) -> dict[str, Any]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise BenchmarkError("RECORD_INVALID", f"{name} must be a JSON object with string keys")
    return value


def _keys(value: dict[str, Any], required: set[str], name: str) -> None:
    if set(value) != required:
        missing = sorted(required - set(value))
        extra = sorted(set(value) - required)
        raise BenchmarkError("RECORD_FIELDS_INVALID", f"{name} fields differ (missing={missing}, extra={extra})")


def _hash(value: object, name: str) -> None:
    if not isinstance(value, str) or HEX64.fullmatch(value) is None:
        raise BenchmarkError("RECORD_INVALID", f"{name} must be a lowercase SHA-256 digest")


def _utc(value: object, name: str) -> None:
    if not isinstance(value, str):
        raise BenchmarkError("RECORD_INVALID", f"{name} must be an ISO-8601 UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise BenchmarkError("RECORD_INVALID", f"{name} must be an ISO-8601 UTC timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise BenchmarkError("RECORD_INVALID", f"{name} must include a UTC offset")


def strict_json_loads(raw: bytes, name: str) -> object:
    """Parse bounded JSON while rejecting duplicate keys and non-finite numbers."""
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise BenchmarkError("JSON_DUPLICATE_KEY", f"{name} contains duplicate key {key!r}")
            result[key] = value
        return result

    def constant(value: str) -> object:
        raise BenchmarkError("JSON_NONFINITE", f"{name} contains non-finite number {value}")

    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=constant)
    except BenchmarkError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BenchmarkError("JSON_INVALID", f"{name} is not valid UTF-8 JSON") from exc


def load_rubric() -> dict[str, Any]:
    path = Path(__file__).with_name("data") / "rubric-v1.json"
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise BenchmarkError("RUBRIC_MISSING", "the packaged rubric is unavailable") from exc
    if hashlib.sha256(raw).hexdigest() != RUBRIC_SHA256:
        raise BenchmarkError("RUBRIC_HASH_MISMATCH", "the pinned rubric bytes changed")
    value = _object(strict_json_loads(raw, "rubric-v1.json"), "rubric")
    if value.get("rubric_id") != BENCHMARK_ID or value.get("version") != RUBRIC_VERSION:
        raise BenchmarkError("RUBRIC_VERSION_INVALID", "the packaged rubric identity or version is invalid")
    return value


def _validate_case(case: object, expected_id: str) -> dict[str, Any]:
    item = _object(case, f"case {expected_id}")
    if item.get("case_id") != expected_id or item.get("status") not in {"included", "excluded"}:
        raise BenchmarkError("MANIFEST_INVALID", f"case {expected_id} has an invalid id or status")
    if item["status"] == "included":
        _keys(item, {"case_id", "status", "input_files", "input_sha256", "oracle_file", "oracle_sha256",
                     "oracle_ids", "repository_sha256", "repository_role", "exclusion_reason"},
              f"case {expected_id}")
        inputs = item.get("input_files")
        if not isinstance(inputs, list) or not inputs:
            raise BenchmarkError("MANIFEST_INVALID", f"case {expected_id} needs pinned input files")
        for index, entry in enumerate(inputs):
            record = _object(entry, f"case {expected_id}.input_files[{index}]")
            _relative_file(record.get("path"), f"case {expected_id}.input_files[{index}].path")
            _hash(record.get("sha256"), f"case {expected_id}.input_files[{index}].sha256")
        if len({entry["path"] for entry in inputs}) != len(inputs):
            raise BenchmarkError("MANIFEST_INVALID", f"case {expected_id} repeats an input path")
        _hash(item.get("input_sha256"), f"case {expected_id}.input_sha256")
        _relative_file(item.get("oracle_file"), f"case {expected_id}.oracle_file")
        _hash(item.get("oracle_sha256"), f"case {expected_id}.oracle_sha256")
        _hash(item.get("repository_sha256"), f"case {expected_id}.repository_sha256")
        snapshot_path = f"workspaces/{expected_id}/source.tar"
        snapshots = [entry for entry in inputs if entry["path"] == snapshot_path]
        if len(snapshots) != 1 or snapshots[0]["sha256"] != item["repository_sha256"]:
            raise BenchmarkError(
                "MANIFEST_INVALID",
                f"case {expected_id} must pin {snapshot_path} with repository_sha256",
            )
        oracle_ids = item.get("oracle_ids")
        if not isinstance(oracle_ids, list) or not oracle_ids or any(
                not isinstance(oracle_id, str) or SAFE_ID.fullmatch(oracle_id) is None for oracle_id in oracle_ids) or \
                len(set(oracle_ids)) != len(oracle_ids):
            raise BenchmarkError("MANIFEST_INVALID", f"case {expected_id} needs unique, safe oracle ids")
        if item.get("exclusion_reason") is not None:
            raise BenchmarkError("MANIFEST_INVALID", f"included case {expected_id} cannot have an exclusion reason")
    elif not isinstance(item.get("exclusion_reason"), str) or not item["exclusion_reason"].strip():
        _keys(item, {"case_id", "status", "exclusion_reason"}, f"case {expected_id}")
        raise BenchmarkError("MANIFEST_INVALID", f"excluded case {expected_id} needs a reason")
    else:
        _keys(item, {"case_id", "status", "exclusion_reason"}, f"case {expected_id}")
    return item


def _relative_file(value: object, name: str) -> None:
    if not isinstance(value, str) or not value or "\\" in value:
        raise BenchmarkError("RECORD_INVALID", f"{name} must be a relative POSIX file path")
    path = Path(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise BenchmarkError("RECORD_INVALID", f"{name} must stay inside the benchmark store")


def case_input_sha256(case: dict[str, Any]) -> str:
    encoded = json.dumps(case["input_files"], ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _validate_arm(arm: object, expected_id: str) -> dict[str, Any]:
    item = _object(arm, f"arm {expected_id}")
    _keys(item, {"arm_id", "version", "source_sha256", "agent_config_sha256", "profile_id", "runtime_id",
                 "runtime_version", "model_id", "effort", "tools", "permission_mode", "session_persistence",
                 "timeout_seconds"}, f"arm {expected_id}")
    versions = {"A": "current_v2", "B": "improved_v2"}
    if item.get("arm_id") != expected_id or item.get("version") != versions[expected_id]:
        raise BenchmarkError("MANIFEST_INVALID", f"arm {expected_id} is not the declared controlled arm")
    for field in ("source_sha256", "agent_config_sha256"):
        _hash(item.get(field), f"arm {expected_id}.{field}")
    for field in ("profile_id", "runtime_id", "runtime_version"):
        value = item.get(field)
        if not isinstance(value, str) or SAFE_ID.fullmatch(value) is None:
            raise BenchmarkError("MANIFEST_INVALID", f"arm {expected_id}.{field} must be a safe identifier")
    expected = {
        "model_id": "claude-opus-5-5",
        "effort": "high",
        "tools": ["Read", "Grep", "Glob"],
        "permission_mode": "plan",
        "session_persistence": False,
        "timeout_seconds": 1800,
    }
    if any(item.get(key) != value for key, value in expected.items()):
        raise BenchmarkError("MANIFEST_CONTROL_MISMATCH", f"arm {expected_id} violates the pinned run controls")
    return item


def expected_cells(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    cases = [case["case_id"] for case in manifest["cases"] if case["status"] == "included"]
    cells = [(case, arm, replicate) for case in cases for arm in ("A", "B")
             for replicate in range(1, manifest["repetitions"] + 1)]
    seed = str(manifest["seed"])
    cells.sort(key=lambda row: hashlib.sha256(f"{seed}\0{row[0]}\0{row[1]}\0{row[2]}".encode()).digest())
    return [{"case_id": case, "arm_id": arm, "replicate": replicate} for case, arm, replicate in cells]


def validate_manifest(value: object) -> dict[str, Any]:
    manifest = _object(value, "manifest")
    _keys(manifest, {"schema_version", "benchmark_id", "frozen_at_utc", "seed", "shuffle_algorithm",
                     "rubric_version", "rubric_sha256", "prompt_template_sha256", "cases", "arms",
                     "repetitions", "run_order", "retrospectives", "reviewers", "limits"}, "manifest")
    if manifest.get("schema_version") != SCHEMA_VERSION or manifest.get("benchmark_id") != BENCHMARK_ID:
        raise BenchmarkError("MANIFEST_INVALID", "unsupported manifest version or benchmark id")
    _utc(manifest.get("frozen_at_utc"), "manifest.frozen_at_utc")
    if isinstance(manifest.get("seed"), bool) or not isinstance(manifest.get("seed"), int) or manifest["seed"] < 0:
        raise BenchmarkError("MANIFEST_INVALID", "manifest.seed must be a nonnegative integer")
    if manifest.get("shuffle_algorithm") != "sha256-seeded-sort-v1":
        raise BenchmarkError("MANIFEST_INVALID", "unsupported seeded run-order algorithm")
    if manifest.get("rubric_version") != RUBRIC_VERSION or manifest.get("rubric_sha256") != RUBRIC_SHA256:
        raise BenchmarkError("RUBRIC_HASH_MISMATCH", "manifest does not pin the packaged rubric")
    _hash(manifest.get("prompt_template_sha256"), "manifest.prompt_template_sha256")
    cases = manifest.get("cases")
    arms = manifest.get("arms")
    if not isinstance(cases, list) or len(cases) != len(CASE_IDS):
        raise BenchmarkError("MANIFEST_INVALID", "manifest must contain exactly C1 through C5")
    if not isinstance(arms, list) or len(arms) != 2:
        raise BenchmarkError("MANIFEST_INVALID", "manifest must contain exactly the current and improved V2 arms")
    for expected_id, case in zip(CASE_IDS, cases):
        _validate_case(case, expected_id)
    for expected_id, arm in zip(("A", "B"), arms):
        _validate_arm(arm, expected_id)
    shared_controls = ("profile_id", "runtime_id", "runtime_version", "model_id", "effort", "tools",
                       "permission_mode")
    if any(arms[0][key] != arms[1][key] for key in shared_controls):
        raise BenchmarkError(
            "MANIFEST_CONTROL_MISMATCH",
            "controlled arms must use the same account profile, runtime version, model and tool controls",
        )
    if manifest.get("repetitions") != 3:
        raise BenchmarkError("MANIFEST_INVALID", "the frozen design requires three repetitions per arm and case")
    run_order = manifest.get("run_order")
    expected_order = expected_cells(manifest)
    if not isinstance(run_order, list) or any(
            not isinstance(item, dict) or set(item) != {"case_id", "arm_id", "replicate"} or
            not isinstance(item.get("case_id"), str) or not isinstance(item.get("arm_id"), str) or
            isinstance(item.get("replicate"), bool) or not isinstance(item.get("replicate"), int)
            for item in run_order) or run_order != expected_order:
        raise BenchmarkError("MANIFEST_INVALID", "run_order is not the unique seeded shuffle of the included cells")
    retrospectives = manifest.get("retrospectives")
    if not isinstance(retrospectives, list) or len(retrospectives) != len(RETROSPECTIVE_IDS) or \
            any(not isinstance(item, dict) for item in retrospectives) or \
            [item.get("output_id") for item in retrospectives] != list(RETROSPECTIVE_IDS):
        raise BenchmarkError("MANIFEST_INVALID", "manifest must pin the three declared retrospective outputs")
    for item in retrospectives:
        _keys(item, {"output_id", "label", "path", "sha256"}, "retrospective")
        if not isinstance(item.get("output_id"), str) or SAFE_ID.fullmatch(item["output_id"]) is None:
            raise BenchmarkError("MANIFEST_INVALID", "retrospective output ids must be safe identifiers")
        if not isinstance(item.get("label"), str) or not item["label"].strip():
            raise BenchmarkError("MANIFEST_INVALID", "retrospective outputs need explicit labels")
        _relative_file(item.get("path"), f"retrospective {item.get('output_id')}.path")
        _hash(item.get("sha256"), f"retrospective {item.get('output_id')}.sha256")
    reviewers = manifest.get("reviewers")
    if not isinstance(reviewers, list) or len(reviewers) != 2:
        raise BenchmarkError("MANIFEST_INVALID", "manifest must pin two reviewers before scoring")
    reviewer_ids = []
    reviewer_profiles = []
    reviewer_models = []
    for reviewer in reviewers:
        record = _object(reviewer, "reviewer")
        _keys(record, {"reviewer_id", "profile_id", "model_id"}, "reviewer")
        for field in ("reviewer_id", "profile_id", "model_id"):
            if not isinstance(record.get(field), str) or not record[field].strip():
                raise BenchmarkError("MANIFEST_INVALID", f"reviewer.{field} must be pinned before scoring")
            if record[field] != record[field].strip():
                raise BenchmarkError("MANIFEST_INVALID", f"reviewer.{field} must not have surrounding whitespace")
        if SAFE_ID.fullmatch(record["reviewer_id"]) is None:
            raise BenchmarkError("MANIFEST_INVALID", "reviewer_id must be a bounded safe identifier")
        reviewer_ids.append(record["reviewer_id"])
        reviewer_profiles.append(record["profile_id"])
        reviewer_models.append(record["model_id"])
    if len(set(reviewer_ids)) != 2:
        raise BenchmarkError("MANIFEST_INVALID", "the two reviewers must have distinct identities")
    if len(set(reviewer_profiles)) != 2:
        raise BenchmarkError("MANIFEST_INVALID", "the two reviewers must use distinct profiles")
    if len(set(reviewer_models)) != 2:
        raise BenchmarkError("MANIFEST_INVALID", "the two reviewers must use distinct models")
    limits = manifest.get("limits")
    expected_limits = {"matched_run_cap": 30, "reference_run_cap": 1, "review_record_cap": 66,
                       "reviews_per_output": 2, "timeout_seconds": 1800}
    if limits != expected_limits:
        raise BenchmarkError("MANIFEST_CONTROL_MISMATCH", "manifest resource limits differ from the approved plan")
    if len(expected_order) > limits["matched_run_cap"]:
        raise BenchmarkError("MANIFEST_CONTROL_MISMATCH", "included cases exceed the approved matched-run cap")
    load_rubric()
    return manifest
