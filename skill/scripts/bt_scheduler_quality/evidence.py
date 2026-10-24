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

SCHEMA_VERSION = "m6.verify-result/1.1"
MANIFEST_VERSION = "m6.evidence-manifest/1.1"
REASON_CODES = frozenset({"PASS", "FAIL_CODE", "BLOCKED_EXTERNAL", "BLOCKED_ENV", "TIMEOUT",
                          "FLAKY_SUSPECTED", "NOT_RUN", "POLICY_ENTRY_MISSING_AUTHORIZATION"})


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
    tree_digest: str | None = None,
    environment_fingerprint: str | None = None,
    check_tree_digests: Mapping[str, str | None] | None = None,
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
                "reason_code": reason_for_outcome(item.outcome.status, item.outcome.issue_code),
                "tree_digest": (check_tree_digests or {}).get(item.spec.id, tree_digest),
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
            "tree_digest": tree_digest,
            "contract_identities": dict(order.contract_identities),
            "environment_fingerprint": environment_fingerprint,
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
        "reason_code": overall_reason_code(check_rows, status, issues),
        "finished_at": finished_at(),
    }
    if order.composition_id is not None:
        base_result["input"].update(composition_id=order.composition_id, manifest_sha256=order.manifest_sha256)
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
                "reason_code": row["reason_code"],
                "tree_digest": row["tree_digest"],
                "output_truncated": item.outcome.output_truncated,
            }
            for row, item in zip(check_rows, checks, strict=True)
        ],
        "issues": base_result.get("issues", []),
        "finished_at": base_result["finished_at"],
    }
    if extra_manifest:
        manifest["context"] = dict(extra_manifest)
    manifest["reason_code"] = base_result["reason_code"]
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
    if set(value) - (required | {"issues", "reason_code"}) or not required <= set(value):
        raise QualityError("RESULT_INVALID", "result has missing or unknown fields")
    _validate_result_identity(value["identity"])
    _validate_result_input(value["input"])
    _validate_result_verifier(value["verifier"])
    _validate_criterion_records(value["criteria"])
    legacy = value.get("schema_version") == "m6.verify-result/1"
    _validate_check_records(value["checks"], legacy=legacy)
    _validate_result_completion(value)
    if "issues" in value:
        _validate_issue_records(value["issues"])
    if value.get("schema_version") == SCHEMA_VERSION and value.get("reason_code") not in REASON_CODES:
        raise QualityError("RESULT_INVALID", "result reason_code is invalid")
    if legacy and value.get("reason_code") not in {None, "UNCLASSIFIED"}:
        raise QualityError("RESULT_INVALID", "legacy result reason_code is invalid")


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
    optional = {"tree_digest", "contract_identities", "environment_fingerprint", "composition_id", "manifest_sha256"}
    if not isinstance(input_data, dict) or not input_keys <= set(input_data) or set(input_data) - input_keys - optional:
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
    tree = input_data.get("tree_digest")
    if tree is not None and (not isinstance(tree, str) or len(tree) not in (40, 64)
                             or any(char not in "0123456789abcdef" for char in tree)):
        raise QualityError("RESULT_INVALID", "result tree digest is invalid")
    contracts = input_data.get("contract_identities", {})
    if not isinstance(contracts, dict) or any(not isinstance(key, str) or not key or not _is_sha256(digest)
                                               for key, digest in contracts.items()):
        raise QualityError("RESULT_INVALID", "result contract identities are invalid")
    environment = input_data.get("environment_fingerprint")
    if environment is not None and (not isinstance(environment, str) or len(environment) not in (24, 64)
                                    or any(char not in "0123456789abcdef" for char in environment)):
        raise QualityError("RESULT_INVALID", "result environment fingerprint is invalid")
    composition, manifest = input_data.get("composition_id"), input_data.get("manifest_sha256")
    if (composition is None) != (manifest is None) or (composition is not None and
            (not isinstance(composition, str) or not composition or not _is_sha256(manifest))):
        raise QualityError("RESULT_INVALID", "result composition identity is invalid")


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


def _validate_check_records(checks: object, *, legacy: bool = False) -> None:
    if not isinstance(checks, list) or not checks:
        raise QualityError("RESULT_INVALID", "result checks must be a non-empty list")
    for item in checks:
        _validate_check_record(item, legacy=legacy)


def _validate_check_record(item: object, *, legacy: bool = False) -> None:
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
    if not isinstance(item, dict) or not check_keys <= set(item) or set(item) - check_keys - {"reason_code", "tree_digest"}:
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
    allowed_reason_codes = REASON_CODES | ({"UNCLASSIFIED"} if legacy else set())
    if item.get("reason_code") is not None and item["reason_code"] not in allowed_reason_codes:
        raise QualityError("RESULT_INVALID", "result check reason_code is invalid")
    tree = item.get("tree_digest")
    if tree is not None and (not isinstance(tree, str) or len(tree) not in (40, 64)
                             or any(char not in "0123456789abcdef" for char in tree)):
        raise QualityError("RESULT_INVALID", "result check tree digest is invalid")


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
        value["schema_version"] not in {"m6.verify-result/1", SCHEMA_VERSION}
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


def read_reason_code(record: Mapping[str, object]) -> str:
    """Read old persisted checks compatibly; a missing taxonomy was never classified."""
    value = record.get("reason_code")
    return value if value in REASON_CODES else "UNCLASSIFIED"


def read_result(value: Mapping[str, Any]) -> dict[str, Any]:
    """Expose compatible classifications to callers without rewriting the stored, content-addressed bytes."""
    result = dict(value)
    result["reason_code"] = read_reason_code(result)
    result["checks"] = [
        {**check, "reason_code": read_reason_code(check)} if isinstance(check, Mapping) else check
        for check in result.get("checks", ())
    ]
    return result


def reason_for_outcome(status: str, issue_code: str | None) -> str:
    if issue_code == "FLAKY_SUSPECTED":
        return "FLAKY_SUSPECTED"
    if status == "pass":
        return "PASS"
    if status == "fail":
        return "FAIL_CODE"
    if issue_code == "CHECK_TIMEOUT":
        return "TIMEOUT"
    if issue_code == "POLICY_ENTRY_MISSING_AUTHORIZATION":
        return issue_code
    if issue_code in {"CHECK_NOT_RUN", "CHECK_DEFERRED", "CHECK_MANUAL"}:
        return "NOT_RUN"
    if issue_code in {"CHECK_UNAVAILABLE", "CHECK_PRODUCTION_ACTION"}:
        return "BLOCKED_EXTERNAL"
    return "BLOCKED_ENV"


def overall_reason_code(
    checks: list[Mapping[str, object]],
    verdict_status: str,
    issues: tuple[Mapping[str, str], ...] = (),
) -> str:
    codes = [read_reason_code(check) for check in checks]
    if "FLAKY_SUSPECTED" in codes:
        return "FLAKY_SUSPECTED"
    if verdict_status == "PASS":
        return "PASS"
    for code in ("POLICY_ENTRY_MISSING_AUTHORIZATION", "FLAKY_SUSPECTED", "FAIL_CODE", "TIMEOUT",
                 "BLOCKED_EXTERNAL", "BLOCKED_ENV", "NOT_RUN"):
        if code in codes:
            return code
    if verdict_status == "FAIL":
        return "FAIL_CODE"
    if verdict_status == "NEEDS_REVIEW" and any(
        str(issue.get("code", "")).startswith("REVIEW_") for issue in issues
    ):
        return "BLOCKED_EXTERNAL"
    return "BLOCKED_ENV"
