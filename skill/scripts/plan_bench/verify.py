"""Verify a frozen benchmark store in the required manifest → cells → reviews order."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .contract import (
    CELL_SCHEMA_VERSION,
    METRIC_IDS,
    REVIEW_SCORE_IDS,
    SAFE_ID,
    BenchmarkError,
    _utc,
    case_input_sha256,
    expected_cells,
    strict_json_loads,
    validate_manifest,
)
from .storage import contained_file, digest, read_bytes, read_json, verify_digest
from .workspace import validate_workspace_archive

_CELL_DIR = re.compile(r"^runs/([A-Z][0-9])/([AB])/([1-3])$")
_ALLOWED_CELL_FILES = {"meta.json", "PLAN.md", "PLAN.json", "observed.json", "check.json", "quality.json"}
_ALLOWED_SOURCE_FILES = {"check.json", "quality.json", "report.json", *(f"O{number}.json" for number in range(1, 10))}


def _manifest(root: Path) -> tuple[dict[str, Any], str]:
    try:
        root.resolve(strict=True)
    except OSError as exc:
        raise BenchmarkError("STORE_MISSING", "benchmark store does not exist") from exc
    raw = read_bytes(root, "manifest.json")
    try:
        sidecar = read_bytes(root, "manifest.sha256", maximum=256).decode("ascii").strip()
    except UnicodeDecodeError as exc:
        raise BenchmarkError("MANIFEST_HASH_INVALID", "manifest.sha256 must be ASCII hex") from exc
    actual = digest(raw)
    if sidecar != actual:
        raise BenchmarkError("MANIFEST_HASH_MISMATCH", "manifest.sha256 does not match manifest.json")
    manifest = validate_manifest(strict_json_loads(raw, "manifest.json"))
    return manifest, actual


def _metric_record(root: Path, cell_dir: str, value: object, metric_id: str, cell_id: str) -> None:
    if not isinstance(value, dict):
        raise BenchmarkError("CELL_INVALID", f"{cell_id} metric {metric_id} must be an object")
    if value.get("status") not in {"measured", "unknown", "not_measured"}:
        raise BenchmarkError("CELL_INVALID", f"{cell_id} metric {metric_id} has an invalid status")
    for field in ("unit", "source_command"):
        if not isinstance(value.get(field), str) or not value[field].strip():
            raise BenchmarkError("METRIC_SOURCE_MISSING", f"{cell_id} metric {metric_id} needs {field}")
    if value["status"] == "measured":
        if set(value) != {"status", "value", "comparison_value", "unit", "source_command", "source_path",
                          "source_sha256"} or \
                "value" not in value or not isinstance(value.get("source_sha256"), str):
            raise BenchmarkError("CELL_INVALID", f"{cell_id} measured metric {metric_id} needs value and source hash")
        if re.fullmatch(r"[a-f0-9]{64}", value["source_sha256"]) is None:
            raise BenchmarkError("CELL_INVALID", f"{cell_id} metric {metric_id} source hash is invalid")
        source_path = value.get("source_path")
        if not isinstance(source_path, str) or "\\" in source_path or \
                Path(source_path).parts[0:1] != ("sources",) or Path(source_path).name not in _ALLOWED_SOURCE_FILES or \
                len(Path(source_path).parts) != 2 or Path(source_path).as_posix() != source_path:
            raise BenchmarkError("CELL_INVALID", f"{cell_id} metric {metric_id} needs a local source artifact")
        try:
            verify_digest(root, f"{cell_dir}/{source_path}", value["source_sha256"])
        except BenchmarkError as exc:
            code = "METRIC_SOURCE_HASH_MISMATCH" if exc.code == "CONTENT_HASH_MISMATCH" else "METRIC_SOURCE_MISSING"
            raise BenchmarkError(code, f"{cell_id} metric {metric_id}: {exc.message}") from exc
        if value.get("comparison_value") is not None and (isinstance(value["comparison_value"], bool) or
                not isinstance(value["comparison_value"], (int, float))):
            raise BenchmarkError("CELL_INVALID", f"{cell_id} metric {metric_id} comparison_value must be numeric")
    else:
        if set(value) != {"status", "unit", "source_command", "reason"} or \
                not isinstance(value.get("reason"), str) or not value["reason"].strip():
            raise BenchmarkError("CELL_INVALID", f"{cell_id} unknown metric {metric_id} needs a reason")


def _verify_observed(root: Path, relative: str, cell_id: str) -> dict[str, Any]:
    observed = read_json(root, relative)
    if not isinstance(observed, dict) or set(observed) != {"schema_version", "cell_id", "metrics"} or \
            observed.get("schema_version") != "1.0.0" or \
            observed.get("cell_id") != cell_id or not isinstance(observed.get("metrics"), dict):
        raise BenchmarkError("CELL_INVALID", f"{cell_id} observed.json has an invalid shape")
    metrics = observed["metrics"]
    if set(metrics) != set(METRIC_IDS):
        raise BenchmarkError("CELL_INVALID", f"{cell_id} must record exactly O1 through O9")
    cell_dir = Path(relative).parent.as_posix()
    for metric_id in METRIC_IDS:
        _metric_record(root, cell_dir, metrics[metric_id], metric_id, cell_id)
    coverage = metrics["O2"]
    if coverage.get("status") == "measured":
        value = coverage.get("value")
        if not isinstance(value, dict) or not isinstance(value.get("per_requirement"), dict) or \
                not value["per_requirement"] or any(not isinstance(key, str) or not key or not isinstance(item, bool)
                                                     for key, item in value["per_requirement"].items()):
            raise BenchmarkError("CELL_INVALID", f"{cell_id} O2 must include per-requirement coverage booleans")
        if not 0 <= coverage["comparison_value"] <= 1:
            raise BenchmarkError("CELL_INVALID", f"{cell_id} O2 comparison_value must be a coverage ratio")
    return observed


def _cell_records(root: Path, manifest: dict[str, Any]) -> list[dict[str, Any]]:
    expected = expected_cells(manifest)
    expected_dirs = {f"runs/{item['case_id']}/{item['arm_id']}/{item['replicate']}": item for item in expected}
    runs = root / "runs"
    if runs.is_symlink():
        raise BenchmarkError("STORE_SYMLINK", "runs must be a real directory")
    if not runs.exists():
        return []
    if not runs.is_dir():
        raise BenchmarkError("STORE_SYMLINK", "runs must be a real directory")
    present_dirs: set[str] = set()
    present_cell_dirs: set[str] = set()
    allowed_directories = {"runs"}
    for relative_dir in expected_dirs:
        parts = relative_dir.split("/")
        allowed_directories.update("/".join(parts[:index]) for index in range(2, len(parts) + 1))
        allowed_directories.add(f"{relative_dir}/sources")
    for path in runs.rglob("*"):
        if path.is_symlink():
            raise BenchmarkError("STORE_SYMLINK", f"cell path {path.relative_to(root).as_posix()!r} cannot be a symlink")
        relative_path = path.relative_to(root).as_posix()
        if path.is_dir():
            if relative_path not in allowed_directories:
                raise BenchmarkError("CELL_UNEXPECTED", f"unexpected cell directory {relative_path!r}")
            if _CELL_DIR.fullmatch(relative_path):
                present_cell_dirs.add(relative_path)
            continue
        if not path.is_file():
            raise BenchmarkError("CELL_INVALID", f"cell path {relative_path!r} is not a regular file")
        parts = relative_path.split("/")
        if len(parts) < 5:
            raise BenchmarkError("CELL_UNEXPECTED", f"unexpected file outside a cell {relative_path!r}")
        cell_dir = "/".join(parts[:4])
        if cell_dir not in expected_dirs:
            raise BenchmarkError("CELL_UNEXPECTED", f"unexpected cell {cell_dir!r}")
        present_cell_dirs.add(cell_dir)
        if len(parts) == 5 and parts[4] in _ALLOWED_CELL_FILES:
            if parts[4] == "meta.json":
                present_dirs.add(cell_dir)
            continue
        if len(parts) == 6 and parts[4] == "sources" and parts[5] in _ALLOWED_SOURCE_FILES:
            continue
        raise BenchmarkError("CELL_UNEXPECTED", f"unapproved cell artifact {relative_path!r}")
    if not present_cell_dirs:
        return []
    if not present_dirs:
        raise BenchmarkError("CELL_MISSING", "cell directories must contain metadata, including incomplete cells")
    missing = sorted(set(expected_dirs) - present_dirs)
    if missing:
        raise BenchmarkError("CELL_MISSING", f"scheduled cells must be recorded, including incomplete cells: {missing}")
    result = []
    for relative_dir in sorted(expected_dirs):
        expected_cell = expected_dirs[relative_dir]
        meta = read_json(root, f"{relative_dir}/meta.json")
        cell_id = f"{expected_cell['case_id']}-{expected_cell['arm_id']}-{expected_cell['replicate']}"
        if not isinstance(meta, dict) or meta.get("schema_version") != CELL_SCHEMA_VERSION or meta.get("cell_id") != cell_id:
            raise BenchmarkError("CELL_INVALID", f"{cell_id} metadata has an invalid identity or version")
        required_meta = {"schema_version", "cell_id", "case_id", "arm_id", "replicate", "status", "profile_id",
                         "runtime_id", "runtime_version", "model_id", "effort", "tools", "permission_mode",
                         "timeout_seconds", "input_sha256",
                         "repository_sha256", "prompt_template_sha256", "agent_config_sha256", "started_at_utc",
                         "finished_at_utc", "elapsed_seconds", "exit_status", "timed_out", "attempt_count",
                         "reported_tokens", "reported_cost_usd", "plan_md_sha256", "plan_json_sha256",
                         "incomplete_reason"}
        if set(meta) != required_meta:
            raise BenchmarkError("CELL_INVALID", f"{cell_id} metadata contains missing or unapproved fields")
        if any(meta.get(key) != expected_cell[key] for key in ("case_id", "arm_id", "replicate")):
            raise BenchmarkError("CELL_INVALID", f"{cell_id} metadata does not match the frozen schedule")
        if meta.get("status") not in {"complete", "incomplete"}:
            raise BenchmarkError("CELL_INVALID", f"{cell_id} has an invalid status")
        case = next(item for item in manifest["cases"] if item["case_id"] == expected_cell["case_id"])
        arm = next(item for item in manifest["arms"] if item["arm_id"] == expected_cell["arm_id"])
        expected_meta = {
            "profile_id": arm["profile_id"], "runtime_id": arm["runtime_id"],
            "runtime_version": arm["runtime_version"],
            "model_id": arm["model_id"], "effort": arm["effort"], "tools": arm["tools"],
            "permission_mode": arm["permission_mode"], "timeout_seconds": arm["timeout_seconds"],
        }
        for key in ("profile_id", "runtime_id", "runtime_version", "model_id", "effort", "tools",
                    "permission_mode", "timeout_seconds"):
            if meta.get(key) != expected_meta[key]:
                raise BenchmarkError("CELL_CONTROL_MISMATCH", f"{cell_id} does not match frozen controls")
        if meta.get("input_sha256") != case_input_sha256(case) or \
                meta.get("repository_sha256") != case.get("repository_sha256"):
            raise BenchmarkError("CELL_CONTROL_MISMATCH", f"{cell_id} input hash differs from the manifest")
        if meta.get("prompt_template_sha256") != manifest["prompt_template_sha256"] or \
                meta.get("agent_config_sha256") != arm["agent_config_sha256"]:
            raise BenchmarkError("CELL_CONTROL_MISMATCH", f"{cell_id} prompt or Planner config hash differs from the manifest")
        _utc(meta.get("started_at_utc"), f"{cell_id}.started_at_utc")
        _utc(meta.get("finished_at_utc"), f"{cell_id}.finished_at_utc")
        if not isinstance(meta.get("timed_out"), bool) or isinstance(meta.get("attempt_count"), bool) or \
                meta.get("attempt_count") != 1:
            raise BenchmarkError("CELL_INVALID", f"{cell_id} must record a boolean timeout and exactly one attempt")
        tokens = meta.get("reported_tokens")
        if tokens is not None and (isinstance(tokens, bool) or not isinstance(tokens, int) or tokens < 0):
            raise BenchmarkError("CELL_INVALID", f"{cell_id} reported_tokens must be a nonnegative integer or null")
        cost = meta.get("reported_cost_usd")
        if cost is not None and (not isinstance(cost, str) or re.fullmatch(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?", cost) is None):
            raise BenchmarkError("CELL_INVALID", f"{cell_id} reported_cost_usd must be a decimal string or null")
        if meta.get("exit_status") is not None and (isinstance(meta["exit_status"], bool) or
                not isinstance(meta["exit_status"], int)):
            raise BenchmarkError("CELL_INVALID", f"{cell_id} exit_status must be an integer or null")
        if not isinstance(meta.get("elapsed_seconds"), (int, float)) or isinstance(meta.get("elapsed_seconds"), bool) or \
                meta["elapsed_seconds"] < 0 or meta["elapsed_seconds"] > arm["timeout_seconds"]:
            raise BenchmarkError("CELL_INVALID", f"{cell_id} elapsed_seconds must be nonnegative")
        if meta["status"] == "incomplete":
            if not isinstance(meta.get("incomplete_reason"), str) or not meta["incomplete_reason"].strip() or \
                    meta.get("plan_md_sha256") is not None or meta.get("plan_json_sha256") is not None:
                raise BenchmarkError("CELL_INVALID", f"{cell_id} incomplete status needs a reason")
            if any((root / relative_dir / filename).exists() for filename in ("PLAN.md", "PLAN.json")):
                raise BenchmarkError("CELL_INVALID", f"{cell_id} incomplete cell cannot publish a plan output")
        else:
            if meta.get("exit_status") != 0 or meta.get("timed_out") or meta.get("incomplete_reason") is not None:
                raise BenchmarkError("CELL_INVALID", f"{cell_id} complete status requires exit_status 0")
            for name, field in (("PLAN.md", "plan_md_sha256"), ("PLAN.json", "plan_json_sha256")):
                _verify_output(root, relative_dir, name, meta.get(field), cell_id)
        observed_relative = f"{relative_dir}/observed.json"
        try:
            observed = _verify_observed(root, observed_relative, cell_id)
        except BenchmarkError as exc:
            if exc.code != "STORE_FILE_MISSING" or meta["status"] != "incomplete":
                raise
            observed = None
        result.append({"cell_id": cell_id, "relative_dir": relative_dir, "meta": meta, "observed": observed})
    return result


def _verify_output(root: Path, directory: str, name: str, expected: object, cell_id: str) -> None:
    if not isinstance(expected, str) or len(expected) != 64:
        raise BenchmarkError("CELL_INVALID", f"{cell_id} has no {name} output hash")
    try:
        verify_digest(root, f"{directory}/{name}", expected)
    except BenchmarkError as exc:
        raise BenchmarkError("CELL_OUTPUT_HASH_MISMATCH", f"{cell_id}: {exc.message}") from exc


def _verify_reviews(root: Path, manifest: dict[str, Any], cells: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mapping = read_json(root, "review-map.private.json")
    if not isinstance(mapping, dict) or set(mapping) != {"schema_version", "outputs"} or \
            mapping.get("schema_version") != "1.0.0" or \
            not isinstance(mapping.get("outputs"), list):
        raise BenchmarkError("REVIEW_INVALID", "review-map.private.json has an invalid shape")
    completed = {cell["cell_id"] for cell in cells if cell["meta"]["status"] == "complete"}
    completed.update(item["output_id"] for item in manifest["retrospectives"])
    entries = mapping["outputs"]
    if any(not isinstance(item, dict) or set(item) != {"output_id", "blind_output_id", "case_id"} or
           any(not isinstance(item.get(field), str) or SAFE_ID.fullmatch(item[field]) is None
               for field in ("output_id", "blind_output_id", "case_id")) for item in entries):
        raise BenchmarkError("REVIEW_INVALID", "review map entries must contain safe output, blind and case ids")
    ids = [item.get("blind_output_id") for item in entries]
    targets = [item.get("output_id") for item in entries]
    if len(entries) != len(completed) or set(targets) != completed or len(set(ids)) != len(ids) or \
            any(not isinstance(value, str) or SAFE_ID.fullmatch(value) is None for value in ids):
        raise BenchmarkError("REVIEW_INVALID", "blind review map must cover each completed output exactly once")
    reviewer_ids = {item["reviewer_id"] for item in manifest["reviewers"]}
    loaded = []
    for entry in entries:
        blind_id = entry["blind_output_id"]
        case_id = entry.get("case_id")
        if case_id not in {case["case_id"] for case in manifest["cases"]}:
            raise BenchmarkError("REVIEW_INVALID", f"review map case id for {blind_id} is invalid")
        cell = next((item for item in cells if item["cell_id"] == entry["output_id"]), None)
        if cell is not None and cell["meta"]["case_id"] != case_id:
            raise BenchmarkError("REVIEW_INVALID", f"review map case id for {blind_id} differs from the cell")
        case = next(item for item in manifest["cases"] if item["case_id"] == case_id)
        oracle_ids = case.get("oracle_ids", [])
        reviews = []
        for reviewer_id in sorted(reviewer_ids):
            relative = f"reviews/{blind_id}/{reviewer_id}.json"
            review = read_json(root, relative)
            _validate_review(review, blind_id, reviewer_id, manifest, oracle_ids)
            reviews.append(review)
        directory = root / "reviews" / blind_id
        if directory.is_symlink():
            raise BenchmarkError("STORE_SYMLINK", f"review directory {blind_id!r} cannot be a symlink")
        if directory.is_dir() and {path.name for path in directory.iterdir()} != {f"{item}.json" for item in reviewer_ids}:
            raise BenchmarkError("REVIEW_INVALID", f"{blind_id} has unexpected or duplicate review records")
        loaded.append({"output_id": entry["output_id"], "blind_output_id": blind_id, "reviews": reviews})
    return loaded


def _validate_review(value: object, blind_id: str, reviewer_id: str, manifest: dict[str, Any],
                     oracle_ids: list[str]) -> None:
    if not isinstance(value, dict) or value.get("schema_version") != "1.0.0" or \
            value.get("blind_output_id") != blind_id or value.get("reviewer_id") != reviewer_id:
        raise BenchmarkError("REVIEW_INVALID", f"review for {blind_id}/{reviewer_id} has invalid identity")
    if set(value) != {"schema_version", "blind_output_id", "reviewer_id", "rubric", "scores"}:
        raise BenchmarkError("REVIEW_INVALID", f"review for {blind_id}/{reviewer_id} contains unapproved fields")
    forbidden = {"arm_id", "arm", "model_id", "provider", "overall_score", "aggregate_score"}
    if forbidden & set(value):
        raise BenchmarkError("REVIEW_INVALID", f"review for {blind_id}/{reviewer_id} leaks arm data or an aggregate")
    rubric = value.get("rubric")
    if not isinstance(rubric, dict) or rubric.get("version") != manifest["rubric_version"] or \
            rubric.get("sha256") != manifest["rubric_sha256"]:
        raise BenchmarkError("REVIEW_INVALID", f"review for {blind_id}/{reviewer_id} uses another rubric")
    scores = value.get("scores")
    if not isinstance(scores, dict) or set(scores) != set(REVIEW_SCORE_IDS) | {"J5", "J8"}:
        raise BenchmarkError("REVIEW_INVALID", f"review for {blind_id}/{reviewer_id} needs J1–J8 entries")
    for score_id in REVIEW_SCORE_IDS:
        record = scores[score_id]
        if not isinstance(record, dict) or set(record) != {"score", "evidence"} or \
                isinstance(record.get("score"), bool) or not isinstance(record.get("score"), int) or \
                record.get("score") not in {0, 1, 2, 3} or not _has_quote(record.get("evidence")):
            raise BenchmarkError("REVIEW_INVALID", f"{blind_id}/{reviewer_id} {score_id} needs a 0–3 score and quote")
    for score_id in ("J5", "J8"):
        if not isinstance(scores[score_id], dict):
            raise BenchmarkError("REVIEW_INVALID", f"{blind_id}/{reviewer_id} {score_id} must be itemized")
    if set(scores["J5"]) != {"oracles", "new_risks"} or set(scores["J8"]) != {"findings"}:
        raise BenchmarkError("REVIEW_INVALID", f"{blind_id}/{reviewer_id} J5/J8 contain unapproved fields")
    j5 = scores["J5"].get("oracles")
    if not isinstance(j5, list) or [item.get("oracle_id") for item in j5 if isinstance(item, dict)] != oracle_ids or \
            any(not isinstance(item, dict) or set(item) != {"oracle_id", "detected", "evidence"} or
                not isinstance(item.get("detected"), bool) or
                not _has_quote(item.get("evidence")) for item in j5):
        raise BenchmarkError("REVIEW_INVALID", f"{blind_id}/{reviewer_id} J5 oracle findings need yes/no and quotes")
    risks = scores["J5"].get("new_risks")
    if not isinstance(risks, list) or any(not isinstance(item, dict) or set(item) != {"classification", "evidence", "rationale"} or
            item.get("classification") not in
            {"valid", "invalid"} or not _has_quote(item.get("evidence")) or
            not isinstance(item.get("rationale"), str) or not item["rationale"].strip() for item in risks):
        raise BenchmarkError("REVIEW_INVALID", f"{blind_id}/{reviewer_id} J5 new risks need evidence and rationale")
    findings = scores["J8"].get("findings")
    if not isinstance(findings, list) or any(not isinstance(item, dict) or set(item) != {
            "classification", "deterministic_gate_caught", "evidence"} or item.get("classification") not in
            {"demonstrated_defect", "plausible_risk", "false"} or
            not isinstance(item.get("deterministic_gate_caught"), bool) or not _has_quote(item.get("evidence"))
            for item in findings):
        raise BenchmarkError("REVIEW_INVALID", f"{blind_id}/{reviewer_id} J8 findings need a class, gate flag and quote")


def _has_quote(value: object) -> bool:
    return isinstance(value, list) and bool(value) and all(
        isinstance(item, dict) and set(item) == {"location", "quote"} and
        isinstance(item.get("location"), str) and item["location"].strip() and
        isinstance(item.get("quote"), str) and item["quote"].strip() for item in value
    )


def verify_store(root: str | Path, *, reviews: bool = False) -> dict[str, Any]:
    """Check the hash-pinned manifest first, then cell evidence, then optional blind reviews."""
    store_root = Path(root)
    manifest, manifest_sha256 = _manifest(store_root)
    for case in manifest["cases"]:
        if case["status"] != "included":
            continue
        for item in case["input_files"]:
            verify_digest(store_root, item["path"], item["sha256"])
            if item["path"] == f"workspaces/{case['case_id']}/source.tar":
                validate_workspace_archive(contained_file(store_root, item["path"]), case["case_id"])
        verify_digest(store_root, case["oracle_file"], case["oracle_sha256"])
    for item in manifest["retrospectives"]:
        verify_digest(store_root, item["path"], item["sha256"])
    cells = _cell_records(store_root, manifest)
    loaded_reviews = _verify_reviews(store_root, manifest, cells) if reviews else []
    return {"manifest": manifest, "manifest_sha256": manifest_sha256, "cells": cells, "reviews": loaded_reviews}
