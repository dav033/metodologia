"""Canonical M6 result and evidence-manifest construction."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from .contracts import QualityError, VerifyRequest
from .criteria import CheckResult, CriterionResult
from .identity import checks_hash, criteria_hash
from .policy import QualityPolicy

SCHEMA_VERSION = "m6.verify-result/1"
MANIFEST_VERSION = "m6.evidence-manifest/1"


def canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def finished_at() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def build_evidence(
    order: VerifyRequest,
    policy: QualityPolicy,
    *,
    base_sha: str | None,
    snapshot_sha: str | None,
    checks: tuple[CheckResult, ...],
    criteria: tuple[CriterionResult, ...],
    status: str,
    issues: tuple[Mapping[str, str], ...],
    extra_manifest: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], bytes, bytes, str]:
    criteria_digest = criteria_hash(order.acceptance_criteria)
    check_digest = checks_hash(order)
    check_rows = []
    artifact_bodies: dict[str, bytes] = {}
    for item in checks:
        for reference, content in (
            (item.stdout_ref, item.outcome.stdout),
            (item.stderr_ref, item.outcome.stderr),
        ):
            digest = reference.rsplit("/", 1)[-1]
            artifact_bodies[digest] = content
        check_rows.append(
            {
                "id": item.spec.id,
                "command": item.spec.command,
                "argv": list(item.spec.argv),
                "status": item.outcome.status,
                "exit_code": item.outcome.exit_code,
                "duration_ms": item.outcome.duration_ms,
                "issue_code": item.outcome.issue_code,
                "stdout_ref": item.stdout_ref,
                "stderr_ref": item.stderr_ref,
            }
        )
    base_result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "identity": {
            "plan_id": order.plan_id,
            "revision": order.revision,
            "task_id": order.task_id,
            "attempt_id": order.attempt_id,
            "token": order.token,
        },
        "input": {
            "snapshot_sha": snapshot_sha,
            "base_sha": base_sha,
            "criteria_hash": criteria_digest,
            "order_sha256": order.input_hash,
            "checks_sha256": check_digest,
        },
        "verifier": {
            "kind": "deterministic",
            "identity": policy.verifier_identity,
            "independent": True,
            "policy_version": policy.version,
        },
        "criteria": [item.to_dict() for item in criteria],
        "checks": check_rows,
        "status": status,
        "finished_at": finished_at(),
    }
    if issues:
        base_result["issues"] = [dict(item) for item in issues]
    manifest: dict[str, Any] = {
        "schema_version": MANIFEST_VERSION,
        "request": order.to_dict(),
        "input": dict(base_result["input"]),
        "verifier": dict(base_result["verifier"]),
        "criteria": base_result["criteria"],
        "checks": [
            {
                **row,
                "purpose": item.spec.purpose,
                "kind": item.spec.kind,
                "expected": item.spec.expected,
                "issue_code": item.outcome.issue_code,
                "output_truncated": item.outcome.output_truncated,
            }
            for row, item in zip(check_rows, checks, strict=True)
        ],
        "issues": base_result.get("issues", []),
        "finished_at": base_result["finished_at"],
    }
    if extra_manifest:
        manifest["context"] = dict(extra_manifest)
    manifest_bytes = canonical_json(manifest)
    manifest_digest = sha256_bytes(manifest_bytes)
    result = {**base_result, "evidence_manifest": f"m6://result/{manifest_digest}"}
    result_bytes = canonical_json(result)
    return result, result_bytes, manifest_bytes, manifest_digest


def validate_result_contract(value: object) -> None:
    if not isinstance(value, dict):
        raise QualityError("RESULT_INVALID", "result must be an object")
    required = {
        "schema_version",
        "identity",
        "input",
        "verifier",
        "criteria",
        "checks",
        "status",
        "evidence_manifest",
        "finished_at",
    }
    if set(value) - (required | {"issues"}) or not required <= set(value):
        raise QualityError("RESULT_INVALID", "result has missing or unknown fields")
    _validate_result_identity(value["identity"])
    _validate_result_input(value["input"])
    _validate_result_verifier(value["verifier"])
    _validate_criterion_records(value["criteria"])
    _validate_check_records(value["checks"])
    _validate_result_completion(value)
    if "issues" in value:
        _validate_issue_records(value["issues"])


def _validate_result_identity(identity: object) -> None:
    identity_keys = {"plan_id", "revision", "task_id", "attempt_id", "token"}
    if (
        not isinstance(identity, dict)
        or set(identity) != identity_keys
        or any(
            not isinstance(identity[name], str) or not identity[name]
            for name in ("plan_id", "task_id", "attempt_id")
        )
        or any(
            not isinstance(identity[name], int)
            or isinstance(identity[name], bool)
            or identity[name] <= 0
            for name in ("revision", "token")
        )
    ):
        raise QualityError("RESULT_INVALID", "result identity is invalid")


def _validate_result_input(input_data: object) -> None:
    input_keys = {
        "snapshot_sha",
        "base_sha",
        "criteria_hash",
        "order_sha256",
        "checks_sha256",
    }
    if not isinstance(input_data, dict) or set(input_data) != input_keys:
        raise QualityError("RESULT_INVALID", "result input hashes are invalid")
    for name in ("snapshot_sha", "base_sha"):
        digest = input_data[name]
        if digest is not None and (
            not isinstance(digest, str)
            or len(digest) not in (40, 64)
            or any(char not in "0123456789abcdef" for char in digest)
        ):
            raise QualityError("RESULT_INVALID", "result commit ID is invalid")
    for name in ("criteria_hash", "order_sha256", "checks_sha256"):
        if not _is_sha256(input_data[name]):
            raise QualityError("RESULT_INVALID", "result input hash is invalid")


def _validate_result_verifier(verifier: object) -> None:
    if (
        not isinstance(verifier, dict)
        or set(verifier) != {"kind", "identity", "independent", "policy_version"}
        or not isinstance(verifier["kind"], str)
        or verifier["kind"] not in {"deterministic", "human"}
        or not isinstance(verifier["identity"], str)
        or not verifier["identity"]
        or not isinstance(verifier["independent"], bool)
        or not isinstance(verifier["policy_version"], str)
        or not verifier["policy_version"]
    ):
        raise QualityError("RESULT_INVALID", "result verifier metadata is invalid")


def _validate_criterion_records(criteria: object) -> None:
    if not isinstance(criteria, list) or not criteria:
        raise QualityError("RESULT_INVALID", "result criteria must be a non-empty list")
    for item in criteria:
        _validate_criterion_record(item)


def _validate_criterion_record(item: object) -> None:
    if not isinstance(item, dict) or set(item) != {"criterion", "status", "evidence"}:
        raise QualityError("RESULT_INVALID", "result criterion record is invalid")
    if not isinstance(item["criterion"], str) or not item["criterion"]:
        raise QualityError("RESULT_INVALID", "result criterion record is invalid")
    if not isinstance(item["status"], str) or item["status"] not in {
        "pass",
        "fail",
        "unknown",
    }:
        raise QualityError("RESULT_INVALID", "result criterion record is invalid")
    if not isinstance(item["evidence"], list) or any(
        not isinstance(ref, str) or len(ref) > 256 for ref in item["evidence"]
    ):
        raise QualityError("RESULT_INVALID", "result criterion record is invalid")


def _validate_check_records(checks: object) -> None:
    if not isinstance(checks, list) or not checks:
        raise QualityError("RESULT_INVALID", "result checks must be a non-empty list")
    for item in checks:
        _validate_check_record(item)


def _validate_check_record(item: object) -> None:
    check_keys = {
        "id",
        "command",
        "argv",
        "status",
        "exit_code",
        "duration_ms",
        "issue_code",
        "stdout_ref",
        "stderr_ref",
    }
    if not isinstance(item, dict) or set(item) != check_keys:
        raise QualityError("RESULT_INVALID", "result check record is invalid")
    if any(
        not isinstance(item[name], str) or not item[name] for name in ("id", "command")
    ):
        raise QualityError("RESULT_INVALID", "result check record is invalid")
    if not isinstance(item["argv"], list) or any(
        not isinstance(arg, str) for arg in item["argv"]
    ):
        raise QualityError("RESULT_INVALID", "result check record is invalid")
    if not isinstance(item["status"], str) or item["status"] not in {
        "pass",
        "fail",
        "unknown",
    }:
        raise QualityError("RESULT_INVALID", "result check record is invalid")
    if item["issue_code"] is not None and not _valid_issue_code(item["issue_code"]):
        raise QualityError("RESULT_INVALID", "result check record is invalid")
    exit_code = item["exit_code"]
    if exit_code is not None and (
        not isinstance(exit_code, int) or isinstance(exit_code, bool)
    ):
        raise QualityError("RESULT_INVALID", "result check record is invalid")
    duration = item["duration_ms"]
    if not isinstance(duration, int) or isinstance(duration, bool) or duration < 0:
        raise QualityError("RESULT_INVALID", "result check record is invalid")
    if not _artifact_ref(item["stdout_ref"]) or not _artifact_ref(item["stderr_ref"]):
        raise QualityError("RESULT_INVALID", "result check record is invalid")


def _valid_issue_code(value: object) -> bool:
    return (
        isinstance(value, str)
        and 1 <= len(value) <= 64
        and value.isascii()
        and value.replace("_", "").isalnum()
        and value[0].isupper()
    )


def _validate_result_completion(value: Mapping[str, object]) -> None:
    if (
        value["schema_version"] != SCHEMA_VERSION
        or not isinstance(value["status"], str)
        or value["status"] not in {"PASS", "FAIL", "NEEDS_REVIEW", "STALE"}
    ):
        raise QualityError(
            "RESULT_INVALID", "result schema version or status is unsupported"
        )
    if not _result_ref(value["evidence_manifest"]):
        raise QualityError(
            "RESULT_INVALID", "result evidence manifest reference is invalid"
        )
    try:
        parsed_time = datetime.fromisoformat(value["finished_at"])
    except (AttributeError, TypeError, ValueError):
        parsed_time = None
    if (
        parsed_time is None
        or parsed_time.utcoffset() is None
        or parsed_time.utcoffset().total_seconds() != 0
    ):
        raise QualityError("RESULT_INVALID", "result timestamp must be UTC")


def _validate_issue_records(issues: object) -> None:
    if not isinstance(issues, list):
        raise QualityError("RESULT_INVALID", "result issues must be a list")
    for issue in issues:
        if not isinstance(issue, dict) or set(issue) != {"code", "detail"}:
            raise QualityError("RESULT_INVALID", "result issue is invalid")
        code, detail = issue["code"], issue["detail"]
        if (
            not _valid_issue_code(code)
            or not isinstance(detail, str)
            or len(detail) > 512
        ):
            raise QualityError("RESULT_INVALID", "result issue is invalid")


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(char in "0123456789abcdef" for char in value)
    )


def _artifact_ref(value: object) -> bool:
    return (
        isinstance(value, str)
        and value.startswith("m6://artifact/")
        and _is_sha256(value.removeprefix("m6://artifact/"))
    )


def _result_ref(value: object) -> bool:
    return (
        isinstance(value, str)
        and value.startswith("m6://result/")
        and _is_sha256(value.removeprefix("m6://result/"))
    )
