"""Validate machine-readable Planner check and quality-report output for benchmark ingestion."""
from __future__ import annotations

from typing import Any

from .contract import BenchmarkError, strict_json_loads

MAX_REPORT_BYTES = 8 * 1024 * 1024
CHECK_FIELDS = {"ok", "errors", "warnings"}
QUALITY_FIELDS = {
    "tasks", "milestones", "total_minutes", "critical_path", "widest_level", "distribution",
    "without_command_verification", "low_confidence", "with_evidence", "unordered_conflicts",
    "unordered_shared", "unconsumed_results", "redundant_edges", "coverage", "interfaces",
    "verification_categories", "criteria_without_command",
}
_DISTRIBUTIONS = {"complexity", "scope", "risk", "coupling", "confidence"}


def _parse(raw: bytes | str, name: str) -> object:
    if isinstance(raw, str):
        try:
            raw = raw.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise BenchmarkError("PLANNER_REPORT_INVALID", f"{name} is not valid UTF-8 text") from exc
    if not isinstance(raw, bytes):
        raise BenchmarkError("PLANNER_REPORT_INVALID", f"{name} must be UTF-8 JSON bytes or text")
    if len(raw) > MAX_REPORT_BYTES:
        raise BenchmarkError("PLANNER_REPORT_TOO_LARGE", f"{name} exceeds {MAX_REPORT_BYTES} bytes")
    return strict_json_loads(raw, name)


def parse_check_output(raw: bytes | str) -> dict[str, Any]:
    """Parse `bt_planner check --json` output without trusting the CLI's output types."""
    value = _parse(raw, "Planner check output")
    if not isinstance(value, dict) or set(value) != CHECK_FIELDS or not isinstance(value.get("ok"), bool) or \
            any(not isinstance(value.get(field), list) or any(not isinstance(item, str) for item in value[field])
                for field in ("errors", "warnings")):
        raise BenchmarkError("PLANNER_REPORT_INVALID", "Planner check output has an invalid schema")
    if value["ok"] != (not value["errors"]):
        raise BenchmarkError("PLANNER_REPORT_INVALID", "Planner check output has inconsistent ok and errors fields")
    return value


def parse_quality_report(raw: bytes | str) -> dict[str, Any]:
    """Parse the PLAN.json 1.2.0 `bt_planner report` JSON contract used by REQ-024 T16."""
    value = _parse(raw, "Planner quality report")
    if not isinstance(value, dict) or set(value) != QUALITY_FIELDS:
        raise BenchmarkError("PLANNER_REPORT_INVALID", "Planner quality report is not the complete 1.2.0 schema")
    for field in ("tasks", "milestones", "total_minutes", "widest_level"):
        _nonnegative_int(value.get(field), field)
    critical_path = value.get("critical_path")
    if not isinstance(critical_path, dict) or set(critical_path) != {"tasks", "minutes"} or \
            not isinstance(critical_path.get("tasks"), list) or \
            any(not isinstance(item, str) or not item for item in critical_path["tasks"]):
        raise BenchmarkError("PLANNER_REPORT_INVALID", "critical_path has an invalid schema")
    _nonnegative_int(critical_path.get("minutes"), "critical_path.minutes")
    distribution = value.get("distribution")
    if not isinstance(distribution, dict) or set(distribution) != _DISTRIBUTIONS:
        raise BenchmarkError("PLANNER_REPORT_INVALID", "distribution must include all five classification dimensions")
    for dimension, counts in distribution.items():
        if not isinstance(counts, dict) or any(not isinstance(key, str) for key in counts):
            raise BenchmarkError("PLANNER_REPORT_INVALID", f"distribution.{dimension} must map labels to counts")
        for label, count in counts.items():
            _nonnegative_int(count, f"distribution.{dimension}.{label}")
    for field in ("without_command_verification", "low_confidence", "with_evidence"):
        if not isinstance(value.get(field), list) or any(not isinstance(item, str) for item in value[field]):
            raise BenchmarkError("PLANNER_REPORT_INVALID", f"{field} must be a list of task ids")
    for field in ("unordered_conflicts", "unordered_shared", "unconsumed_results", "redundant_edges"):
        if not isinstance(value.get(field), list):
            raise BenchmarkError("PLANNER_REPORT_INVALID", f"{field} must be a list")
    _validate_coverage(value.get("coverage"))
    interfaces = value.get("interfaces")
    if not isinstance(interfaces, list) or any(not isinstance(item, dict) for item in interfaces):
        raise BenchmarkError("PLANNER_REPORT_INVALID", "interfaces must be a list of interface records")
    _validate_verification_categories(value.get("verification_categories"))
    _validate_unverified_criteria(value.get("criteria_without_command"))
    return value


def _nonnegative_int(value: object, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise BenchmarkError("PLANNER_REPORT_INVALID", f"{name} must be a nonnegative integer")


def _validate_coverage(value: object) -> None:
    if not isinstance(value, dict):
        raise BenchmarkError("PLANNER_REPORT_INVALID", "coverage must map requirement ids to task ids")
    for requirement_id, task_ids in value.items():
        if not isinstance(requirement_id, str) or not requirement_id or not isinstance(task_ids, list) or \
                any(not isinstance(task_id, str) or not task_id for task_id in task_ids):
            raise BenchmarkError("PLANNER_REPORT_INVALID", "coverage has an invalid requirement or task id")


def _validate_verification_categories(value: object) -> None:
    if not isinstance(value, dict):
        raise BenchmarkError("PLANNER_REPORT_INVALID", "verification_categories must be an object")
    fields = {"categories", "verifications", "planned_work", "manual_only"}
    for requirement_id, record in value.items():
        if not isinstance(requirement_id, str) or not requirement_id or not isinstance(record, dict) or \
                set(record) != fields or not isinstance(record.get("manual_only"), bool) or \
                not isinstance(record.get("categories"), list) or \
                any(not isinstance(item, str) for item in record["categories"]) or \
                any(not isinstance(record.get(field), list) or any(not isinstance(item, dict) for item in record[field])
                    for field in ("verifications", "planned_work")):
            raise BenchmarkError("PLANNER_REPORT_INVALID", "verification_categories has an invalid record")


def _validate_unverified_criteria(value: object) -> None:
    required = {"task_id", "criterion", "reason", "m6_criterion_status", "verification_indexes"}
    if not isinstance(value, list):
        raise BenchmarkError("PLANNER_REPORT_INVALID", "criteria_without_command must be a list")
    for record in value:
        if not isinstance(record, dict) or set(record) != required or \
                any(not isinstance(record.get(field), str) or not record[field]
                    for field in ("task_id", "criterion", "reason", "m6_criterion_status")) or \
                not isinstance(record.get("verification_indexes"), list) or \
                any(isinstance(index, bool) or not isinstance(index, int) or index < 0
                    for index in record["verification_indexes"]):
            raise BenchmarkError("PLANNER_REPORT_INVALID", "criteria_without_command has an invalid record")
