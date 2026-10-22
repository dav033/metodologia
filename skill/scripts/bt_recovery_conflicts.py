"""Validate and publish complete, source-specific integration conflict observations.

This module is deliberately independent of M5. Callers provide immutable official
records and a trusted sink; it never treats a caller's assertion as source evidence.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

SCHEMA = "conflict-observation/1"
_SHA = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")


class ConflictEvidenceError(ValueError):
    """The conflict cannot be safely reconstructed from the supplied official records."""


def _canonical_digest(value: object) -> str:
    try:
        payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    except (TypeError, ValueError) as error:
        raise ConflictEvidenceError("source record is not canonical JSON") from error
    return hashlib.sha256(payload).hexdigest()


def _commit(value: object, label: str) -> str:
    if not isinstance(value, str) or _SHA.fullmatch(value) is None:
        raise ConflictEvidenceError(f"invalid {label} identity")
    return value


def _paths(values: object) -> list[str]:
    if not isinstance(values, (tuple, list)) or not values:
        raise ConflictEvidenceError("full conflict paths are missing")
    result = []
    for path in values:
        if (not isinstance(path, str) or not path or len(path) > 4096 or path.startswith("/") or
                "\\" in path or "\x00" in path or any(part in ("", ".", "..") for part in path.split("/"))):
            raise ConflictEvidenceError("unsafe conflict path")
        if path not in result:
            result.append(path)
    return sorted(result)


def collect_conflict_evidence(source_records: Mapping[str, Any], *, source_type: str,
                              conflict: Mapping[str, Any], repository_root: Path | str | None = None) -> dict[str, Any]:
    """Return a plain ``conflict-observation/1`` mapping after cross-checking records.

    Start conflicts require M1 attempts/accepted maps, frozen old/current task
    scopes and DAG, and M3 order/base/snapshot/trees. M6 cannot exist until an
    attempt reaches verification, so it is required only for ``integration_gate``.
    ``source_records`` must be read from the official owners and include a digest
    beside every record. A stored but unrepeatable historical observation is not
    upgraded here.
    """
    if source_type not in {"start", "integration_gate"}:
        raise ConflictEvidenceError("unknown conflict source")
    required = {"m1_attempts", "m1_accepted", "frozen_plan", "current_plan", "m3_manifest", "m3_order"}
    if source_type == "integration_gate":
        required.add("m6_verdict")
    if not isinstance(source_records, Mapping) or not required.issubset(source_records):
        raise ConflictEvidenceError("required official conflict source is missing")
    records: dict[str, Mapping[str, Any]] = {}
    digests: dict[str, str] = {}
    for name in sorted(required):
        record = source_records[name]
        if not isinstance(record, Mapping) or not isinstance(record.get("record"), Mapping):
            raise ConflictEvidenceError(f"invalid official source record: {name}")
        actual = _canonical_digest(record["record"])
        if record.get("sha256") != actual:
            raise ConflictEvidenceError(f"official source digest mismatch: {name}")
        records[name] = record["record"]
        digests[name] = actual

    run_id = records["m3_order"].get("run_id")
    plan_id = records["m3_order"].get("plan_id")
    revision = records["m3_order"].get("revision")
    task_id = records["m3_order"].get("task_id")
    attempt_id = records["m3_order"].get("attempt_id")
    plan_sha = records["m3_order"].get("plan_sha256")
    token = records["m3_order"].get("token")
    consumer_id = records["m3_order"].get("consumer_id")
    repository_id = records["m3_order"].get("repository_id")
    identity = (run_id, plan_id, revision, task_id, attempt_id, plan_sha)
    if (not all(isinstance(v, str) and v for v in (run_id, plan_id, task_id, attempt_id)) or
            type(revision) is not int or revision < 1 or not isinstance(plan_sha, str) or
            re.fullmatch(r"[0-9a-f]{64}", plan_sha) is None):
        raise ConflictEvidenceError("M3 order identity is incomplete")
    for name in ("m1_attempts", "m1_accepted", "frozen_plan", "current_plan", "m3_manifest"):
        record = records[name]
        if any(record.get(key) != value for key, value in zip(
                ("run_id", "plan_id", "revision", "task_id", "attempt_id", "plan_sha256"), identity)):
            raise ConflictEvidenceError(f"source identity mismatch: {name}")
    if source_type == "integration_gate":
        m6 = records["m6_verdict"]
        if any(m6.get(key) != value for key, value in zip(
                ("run_id", "plan_id", "revision", "task_id", "attempt_id", "plan_sha256"), identity)):
            raise ConflictEvidenceError("source identity mismatch: m6_verdict")

    side_records = conflict.get("sides")
    if not isinstance(side_records, (tuple, list)) or len(side_records) < 2:
        raise ConflictEvidenceError("conflict sides are incomplete")
    sides = []
    for ordinal, side in enumerate(side_records):
        if not isinstance(side, Mapping):
            raise ConflictEvidenceError("invalid conflict side")
        base = _commit(side.get("base_sha"), "side base")
        snapshot = _commit(side.get("snapshot_sha"), "side snapshot")
        tree = _commit(side.get("tree_sha"), "side tree")
        sides.append({"ordinal": ordinal, "role": side.get("role"), "task_id": side.get("task_id"),
                      "attempt_id": side.get("attempt_id"), "base_digest": hashlib.sha256(base.encode()).hexdigest(),
                      "snapshot_digest": hashlib.sha256(snapshot.encode()).hexdigest(),
                      "tree_digest": hashlib.sha256(tree.encode()).hexdigest()})
    paths = _paths(conflict.get("paths"))
    if repository_root is not None:
        root = Path(repository_root).resolve(strict=True)
        for relative in paths:
            cursor = root
            for part in relative.split("/"):
                cursor = cursor / part
                if cursor.is_symlink():
                    raise ConflictEvidenceError("symlink conflict path")
    accepted_map = records["m1_accepted"].get("accepted")
    if not isinstance(accepted_map, Mapping):
        raise ConflictEvidenceError("M1 accepted-attempt map is missing")
    for side in side_records:
        if side.get("role") == "accepted" and accepted_map.get(side.get("task_id")) != side.get("attempt_id"):
            raise ConflictEvidenceError("accepted conflict side is stale")
    manifest_paths = records["m3_manifest"].get("paths")
    if not isinstance(manifest_paths, (tuple, list)) or set(paths) - set(manifest_paths):
        raise ConflictEvidenceError("M3 manifest does not cover the complete conflict paths")
    merge_base = _commit(conflict.get("merge_base"), "merge base")
    refusal = conflict.get("ordinary_rework_refusal")
    refusal_detail = conflict.get("ordinary_rework_refusal_detail")
    if refusal not in {"overlap_requires_structural_recovery", "ordinary_rework_refused"}:
        raise ConflictEvidenceError("ordinary rework refusal is missing")
    if not isinstance(refusal_detail, str) or not refusal_detail.strip() or len(refusal_detail) > 4096:
        raise ConflictEvidenceError("ordinary rework refusal detail is missing")

    observation = {"schema_version": SCHEMA, "source_type": source_type, "run_id": run_id,
        "plan_id": plan_id, "revision": revision, "plan_sha256": plan_sha, "task_id": task_id,
        "attempt_id": attempt_id, "token": token, "consumer_id": consumer_id,
        "repository_id": repository_id, "paths": paths, "sides": sides,
        "original_merge_base": hashlib.sha256(merge_base.encode()).hexdigest(),
        "carry_ancestry": list(conflict.get("carry_ancestry", ())),
        "evidence_digests": sorted(set(digests.values())), "ordinary_rework_refusal": refusal,
        "ordinary_rework_refusal_detail": refusal_detail}
    if not all(isinstance(value, str) and value for value in (token, consumer_id, repository_id)):
        raise ConflictEvidenceError("M3 consumer identity is incomplete")
    try:
        from bt_scheduler_recovery_adapter import validate_conflict_observation
        validate_conflict_observation(observation)
    except (TypeError, ValueError) as error:
        raise ConflictEvidenceError("conflict observation contract validation failed") from error
    return observation
