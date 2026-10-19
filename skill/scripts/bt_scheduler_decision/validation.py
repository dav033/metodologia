"""Runtime validation and redacted normalization for the public M2 request contract."""
from __future__ import annotations

import json
import math
import re
import unicodedata
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any

from .contracts import (
    AUTH_STATES,
    CANDIDATE_STATES,
    COMPLEXITY_VALUES,
    EVIDENCE_DIMENSIONS,
    EVIDENCE_KINDS,
    HISTORY_QUALITIES,
    LEVEL_VALUES,
    QUOTA_STATES,
    RUNTIME_STATES,
    SCOPE_VALUES,
    SOURCE_REASON_CODES,
    Candidate,
    DecisionInputError,
    DecisionRequest,
    RouteHistory,
    TaskFacts,
    ValidatedRequest,
)
from .identity import candidate_route_id, canonical_json, sha256_json

MAX_CANDIDATES = 256
MAX_SEQUENCE_ITEMS = 128
MAX_TASK_JSON_NODES = 8192
MAX_JSON_BYTES = 262_144
MAX_TEXT = 4096
MAX_JSON_KEY = 128
MAX_TASK_BRIEF = 2048
MAX_HISTORY_COUNT = 1_000_000_000
MAX_MEDIAN_TOTAL_TOKENS = 1_000_000_000_000
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_CODE = re.compile(r"[a-z][a-z0-9_]{0,63}\Z")
_REFERENCE = re.compile(r"(file|command|precedent|spec|task|assumption):(.+)\Z")

_CLASSIFICATION_VALUES = {
    "complexity": set(COMPLEXITY_VALUES), "scope": set(SCOPE_VALUES), "risk": set(LEVEL_VALUES),
    "coupling": set(LEVEL_VALUES), "confidence": set(LEVEL_VALUES),
}


def _charge_json_bytes(value: Any, path: str, budget: list[int]) -> None:
    try:
        serialized = json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        size = len(serialized.encode("utf-8", errors="strict"))
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise DecisionInputError([f"{path}:not_json_compatible"]) from exc
    budget[1] -= size
    if budget[1] < 0:
        raise DecisionInputError([f"{path}:too_large"])


def _freeze_json_node(value: Any, path: str, depth: int, budget: list[int]) -> Any:
    budget[0] -= 1
    if budget[0] < 0:
        raise DecisionInputError([f"{path}:too_many_nodes"])
    if depth > 8:
        raise DecisionInputError([f"{path}:too_deep"])
    if value is None or isinstance(value, (bool, int)):
        _charge_json_bytes(value, path, budget)
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise DecisionInputError([f"{path}:non_finite"])
        _charge_json_bytes(value, path, budget)
        return value
    if isinstance(value, str):
        if len(value) > MAX_TEXT:
            raise DecisionInputError([f"{path}:text_too_long"])
        normalized = unicodedata.normalize("NFC", value)
        if len(normalized) > MAX_TEXT:
            raise DecisionInputError([f"{path}:text_too_long"])
        try:
            normalized.encode("utf-8", errors="strict")
        except UnicodeEncodeError as exc:
            raise DecisionInputError([f"{path}:invalid_unicode"]) from exc
        _charge_json_bytes(normalized, path, budget)
        return normalized
    if isinstance(value, Mapping):
        if len(value) > 64 or any(not isinstance(key, str) for key in value):
            raise DecisionInputError([f"{path}:invalid_object"])
        budget[1] -= 2
        if budget[1] < 0:
            raise DecisionInputError([f"{path}:too_large"])
        normalized: dict[str, Any] = {}
        for index, (key, item) in enumerate(value.items()):
            if len(key) > MAX_JSON_KEY:
                raise DecisionInputError([f"{path}:invalid_object_key"])
            try:
                normalized_key = unicodedata.normalize("NFC", key)
                normalized_key.encode("utf-8", errors="strict")
            except UnicodeEncodeError as exc:
                raise DecisionInputError([f"{path}:invalid_object_key"]) from exc
            if len(normalized_key) > MAX_JSON_KEY:
                raise DecisionInputError([f"{path}:invalid_object_key"])
            if normalized_key in normalized:
                raise DecisionInputError([f"{path}:duplicate_object_key"])
            if index:
                budget[1] -= 1
            try:
                key_size = len(json.dumps(normalized_key, ensure_ascii=False).encode("utf-8")) + 1
            except (TypeError, ValueError, UnicodeEncodeError) as exc:
                raise DecisionInputError([f"{path}:invalid_object_key"]) from exc
            budget[1] -= key_size
            if budget[1] < 0:
                raise DecisionInputError([f"{path}:too_large"])
            normalized[normalized_key] = _freeze_json_node(item, f"{path}.fields[{index}]", depth + 1, budget)
        return MappingProxyType(normalized)
    if isinstance(value, (tuple, list)):
        if len(value) > MAX_SEQUENCE_ITEMS:
            raise DecisionInputError([f"{path}:too_many_items"])
        budget[1] -= 2 + max(0, len(value) - 1)
        if budget[1] < 0:
            raise DecisionInputError([f"{path}:too_large"])
        return tuple(_freeze_json_node(item, f"{path}[]", depth + 1, budget) for item in value)
    raise DecisionInputError([f"{path}:not_json_compatible"])


def _freeze_json(value: Any, path: str, budget: list[int] | None = None) -> Any:
    return _freeze_json_node(value, path, 0, [MAX_TASK_JSON_NODES, MAX_JSON_BYTES] if budget is None else budget)


def _freeze_optional_json(value: object, path: str, budget: list[int]) -> object | None:
    try:
        return _freeze_json(value, path, budget)
    except DecisionInputError as exc:
        if any(issue.endswith((":too_large", ":too_many_nodes")) for issue in exc.issues):
            raise DecisionInputError(["request:too_large"]) from exc
        return None


def _text(value: object, path: str, *, maximum: int = MAX_TEXT, empty: bool = False) -> str:
    if not isinstance(value, str):
        raise DecisionInputError([f"{path}:not_text"])
    if len(value) > maximum:
        raise DecisionInputError([f"{path}:invalid_text"])
    normalized = value.strip()
    if (not normalized and not empty) or len(normalized) > maximum or any(ord(char) < 32 and char not in "\t\n\r"
                                                                        for char in normalized):
        raise DecisionInputError([f"{path}:invalid_text"])
    normalized = unicodedata.normalize("NFC", normalized)
    if len(normalized) > maximum:
        raise DecisionInputError([f"{path}:invalid_text"])
    try:
        normalized.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise DecisionInputError([f"{path}:invalid_unicode"]) from exc
    return normalized


def _finite(value: object, path: str, *, optional: bool = False) -> float | None:
    if value is None and optional:
        return None
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise DecisionInputError([f"{path}:not_finite_number"])
    try:
        numeric = float(value)
    except (OverflowError, ValueError) as exc:
        raise DecisionInputError([f"{path}:not_finite_number"]) from exc
    if not math.isfinite(numeric):
        raise DecisionInputError([f"{path}:not_finite_number"])
    return numeric


def _count(value: object, path: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= MAX_HISTORY_COUNT:
        raise DecisionInputError([f"{path}:invalid_count"])
    return value


def _string_tuple(values: object, path: str, *, maximum: int = MAX_SEQUENCE_ITEMS) -> tuple[str, ...]:
    if not isinstance(values, (tuple, list)) or len(values) > maximum:
        raise DecisionInputError([f"{path}:invalid_sequence"])
    result = tuple(_text(value, f"{path}[]", maximum=MAX_TEXT) for value in values)
    if len(result) != len(set(result)):
        raise DecisionInputError([f"{path}:duplicate_value"])
    return result


def _classifications(value: object) -> tuple[Mapping[str, object], tuple[str, ...]]:
    if not isinstance(value, Mapping):
        return MappingProxyType({name: None for name in (*_CLASSIFICATION_VALUES, "estimated_minutes")}), \
            ("classification_object_malformed",)
    problems: list[str] = []
    normalized: dict[str, object] = {}
    expected = {*_CLASSIFICATION_VALUES, "estimated_minutes"}
    for name in expected:
        raw = value.get(name)
        if name == "estimated_minutes":
            if raw is None or isinstance(raw, int) and not isinstance(raw, bool) and 0 <= raw <= 100_000:
                normalized[name] = raw
            else:
                normalized[name] = None
                problems.append(f"classification_{name}_invalid")
        elif raw is None or isinstance(raw, str) and raw in _CLASSIFICATION_VALUES[name]:
            normalized[name] = raw
        else:
            normalized[name] = None
            problems.append(f"classification_{name}_invalid")
    if set(value) - expected:
        problems.append("classification_unknown_dimension")
    return MappingProxyType(normalized), tuple(sorted(set(problems)))


def _evidence(value: object) -> tuple[Mapping[str, object], tuple[str, ...], str]:
    if not isinstance(value, Mapping):
        return MappingProxyType({}), ("classification_evidence_malformed",), sha256_json({"invalid": "not_object"})
    sanitized: dict[str, object] = {}
    fingerprint: dict[str, object] = {}
    problems: list[str] = []
    for name in EVIDENCE_DIMENSIONS:
        entry = value.get(name)
        if not isinstance(entry, Mapping):
            problems.append(f"evidence_{name}_missing_or_malformed")
            fingerprint[name] = {"valid": False}
            continue
        justification = entry.get("justification")
        refs = entry.get("evidence")
        if not isinstance(justification, str) or not justification.strip() or len(justification) > 1000:
            problems.append(f"evidence_{name}_justification_invalid")
            fingerprint[name] = {"valid": False, "justification_type": type(justification).__name__}
            continue
        try:
            justification.encode("utf-8", errors="strict")
        except UnicodeEncodeError:
            problems.append(f"evidence_{name}_justification_invalid")
            fingerprint[name] = {"valid": False, "justification_type": "invalid_unicode"}
            continue
        if not isinstance(refs, (list, tuple)) or not refs or len(refs) > 32:
            problems.append(f"evidence_{name}_references_invalid")
            fingerprint[name] = {"valid": False, "justification_sha256": sha256_json(justification),
                                 "reference_shape": type(refs).__name__}
            continue
        kinds = []
        refs_valid = True
        for ref in refs:
            if not isinstance(ref, str) or len(ref) > 1024:
                refs_valid = False
                break
            try:
                ref.encode("utf-8", errors="strict")
            except UnicodeEncodeError:
                refs_valid = False
                break
            match = _REFERENCE.fullmatch(ref.strip())
            if not match or match.group(1) not in EVIDENCE_KINDS:
                refs_valid = False
                break
            kinds.append(match.group(1))
        if not refs_valid:
            problems.append(f"evidence_{name}_references_invalid")
            fingerprint[name] = {"valid": False, "justification_sha256": sha256_json(justification),
                                 "references_valid": False}
            continue
        sanitized[name] = MappingProxyType({
            "valid": True,
            "reference_kinds": tuple(sorted(set(kinds))),
            "reference_count": len(refs),
        })
        fingerprint[name] = {"valid": True, "justification_sha256": sha256_json(justification),
                             "references_sha256": sha256_json(tuple(refs))}
    if set(value) - set(EVIDENCE_DIMENSIONS):
        problems.append("evidence_unknown_dimension")
    return MappingProxyType(sanitized), tuple(sorted(set(problems))), sha256_json(fingerprint)


def _validate_history(history: object, path: str) -> RouteHistory:
    if not isinstance(history, RouteHistory):
        raise DecisionInputError([f"{path}:invalid_history"])
    if history.source_quality not in HISTORY_QUALITIES:
        raise DecisionInputError([f"{path}.source_quality:unknown"])
    successes = _count(history.verified_successes, f"{path}.verified_successes")
    failures = _count(history.verified_failures, f"{path}.verified_failures")
    claimed = _count(history.claimed_unverified, f"{path}.claimed_unverified")
    other = _count(history.other_failures, f"{path}.other_failures")
    duration_samples = _count(history.duration_samples, f"{path}.duration_samples")
    token_samples = _count(history.token_samples, f"{path}.token_samples")
    duration = _finite(history.median_duration_seconds, f"{path}.median_duration_seconds", optional=True)
    tokens = history.median_total_tokens
    if tokens is not None and (not isinstance(tokens, int) or isinstance(tokens, bool) or
                               not 0 <= tokens <= MAX_MEDIAN_TOTAL_TOKENS):
        raise DecisionInputError([f"{path}.median_total_tokens:invalid"])
    if (duration_samples == 0) != (duration is None) or (token_samples == 0) != (tokens is None):
        raise DecisionInputError([f"{path}:sample_coverage_mismatch"])
    if duration is not None and duration < 0:
        raise DecisionInputError([f"{path}.median_duration_seconds:negative"])
    if history.source_quality == "unknown" and any((successes, failures, claimed, other, duration_samples, token_samples)):
        raise DecisionInputError([f"{path}:unknown_has_observations"])
    return RouteHistory(history.source_quality, successes, failures, claimed, other, duration_samples, duration,
                        token_samples, tokens)


def _validate_candidate(candidate: object, index: int, requested_at: float) -> Candidate:
    path = f"candidates[{index}]"
    if not isinstance(candidate, Candidate):
        raise DecisionInputError([f"{path}:wrong_type"])
    provider = _text(candidate.provider, f"{path}.provider", maximum=64)
    model = _text(candidate.model, f"{path}.model", maximum=128)
    profile = _text(candidate.profile, f"{path}.profile", maximum=64)
    account_ref = _text(candidate.account_ref, f"{path}.account_ref", maximum=69)
    if not account_ref.startswith("acct:") or not _SHA256.fullmatch(account_ref[5:]):
        raise DecisionInputError([f"{path}.account_ref:invalid"])
    effort = None if candidate.effort is None else _text(candidate.effort, f"{path}.effort", maximum=32)
    route_id = candidate_route_id(provider, model, profile, effort)
    if candidate.route_id != route_id:
        raise DecisionInputError([f"{path}.route_id:mismatch"])
    source_status = candidate.source_status if candidate.source_status in CANDIDATE_STATES else "unknown"
    if not isinstance(candidate.profile_authorized, bool):
        raise DecisionInputError([f"{path}.profile_authorized:not_boolean"])
    auth_status = candidate.auth_status if candidate.auth_status in AUTH_STATES else "unknown"
    runtime_status = candidate.runtime_status if candidate.runtime_status in RUNTIME_STATES else "unknown"
    quota_status = candidate.quota_status if candidate.quota_status in QUOTA_STATES else "unknown"
    observed = _finite(candidate.quota_observed_at, f"{path}.quota_observed_at", optional=True)
    valid_until = _finite(candidate.quota_valid_until, f"{path}.quota_valid_until", optional=True)
    used = _finite(candidate.quota_used_percent, f"{path}.quota_used_percent", optional=True)
    if quota_status == "available":
        if used is not None and used >= 100 and observed is not None and observed <= requested_at and \
                valid_until is not None and valid_until > requested_at:
            quota_status = "exhausted"
        elif observed is None or observed > requested_at or valid_until is None or valid_until <= requested_at or \
                used is None or not 0 <= used < 100:
            quota_status = "stale" if valid_until is not None and valid_until <= requested_at else "unknown"
    baseline = candidate.baseline_rank
    if baseline is not None and (not isinstance(baseline, int) or isinstance(baseline, bool) or
                                 not 0 <= baseline < MAX_CANDIDATES):
        raise DecisionInputError([f"{path}.baseline_rank:invalid"])
    reason_codes = tuple(sorted(_string_tuple(candidate.source_reason_codes, f"{path}.source_reason_codes", maximum=32)))
    if any(not _CODE.fullmatch(code) or code not in SOURCE_REASON_CODES for code in reason_codes):
        raise DecisionInputError([f"{path}.source_reason_codes:invalid_code"])
    history = _validate_history(candidate.history, f"{path}.history")
    return Candidate(route_id, provider, model, profile, account_ref, effort, source_status, reason_codes,
                     candidate.profile_authorized, auth_status, runtime_status, quota_status, observed, valid_until,
                     used, baseline, history)


def validate_request(request: object) -> ValidatedRequest:
    """Reject malformed identity/route data, but downgrade invalid optional classifications to explicit unknowns."""
    if not isinstance(request, DecisionRequest):
        raise DecisionInputError(["request:wrong_type"])
    plan_id = _text(request.plan_id, "plan_id", maximum=128)
    if not isinstance(request.revision, int) or isinstance(request.revision, bool) or request.revision < 1:
        raise DecisionInputError(["revision:invalid"])
    if not isinstance(request.plan_sha256, str) or not _SHA256.fullmatch(request.plan_sha256):
        raise DecisionInputError(["plan_sha256:invalid"])
    if not isinstance(request.free_slots, int) or isinstance(request.free_slots, bool) or request.free_slots < 1:
        raise DecisionInputError(["free_slots:invalid"])
    if (not isinstance(request.dispatch_generation, int) or isinstance(request.dispatch_generation, bool)
            or request.dispatch_generation < 0):
        raise DecisionInputError(["dispatch_generation:invalid"])
    requested_at = _finite(request.requested_at, "requested_at")
    task = request.task
    if not isinstance(task, TaskFacts):
        raise DecisionInputError(["task:wrong_type"])
    task_id = _text(task.task_id, "task.task_id", maximum=128)
    brief = _text(task.brief, "task.brief", maximum=MAX_TASK_BRIEF, empty=True)
    task_json_budget = [MAX_TASK_JSON_NODES, MAX_JSON_BYTES]
    raw_classifications = _freeze_optional_json(task.classifications, "task.classifications", task_json_budget)
    raw_evidence = _freeze_optional_json(task.classification_evidence, "task.classification_evidence", task_json_budget)
    classifications, class_warnings = _classifications(raw_classifications)
    evidence, evidence_warnings, evidence_digest = _evidence(raw_evidence)
    dependencies = _string_tuple(task.dependencies, "task.dependencies")
    criteria = _string_tuple(task.acceptance_criteria, "task.acceptance_criteria")
    resources = _string_tuple(task.shared_resources, "task.shared_resources")
    paths = _string_tuple(task.expected_paths, "task.expected_paths")
    if not isinstance(task.verification, (tuple, list)) or len(task.verification) > 32:
        raise DecisionInputError(["task.verification:invalid_sequence"])
    verification = tuple(_freeze_json(value, "task.verification", task_json_budget) for value in task.verification)
    if any(not isinstance(value, Mapping) for value in verification):
        raise DecisionInputError(["task.verification:entry_not_object"])
    normalized_task = TaskFacts(task_id, brief, classifications, evidence, dependencies, criteria, verification,
                                resources, paths)
    if not isinstance(request.candidates, (tuple, list)) or len(request.candidates) > MAX_CANDIDATES:
        raise DecisionInputError(["candidates:invalid_count"])
    candidates = tuple(sorted((_validate_candidate(candidate, index, requested_at)
                               for index, candidate in enumerate(request.candidates)), key=lambda item: item.route_id))
    if len({item.route_id for item in candidates}) != len(candidates):
        raise DecisionInputError(["candidates:duplicate_route_id"])
    policy_version = _text(request.policy_version, "policy_version", maximum=128)
    checkpoint = None if request.checkpoint_revision is None else \
        _text(request.checkpoint_revision, "checkpoint_revision", maximum=256)
    normalized = DecisionRequest(plan_id, request.revision, request.plan_sha256, request.free_slots, requested_at,
                                 normalized_task, candidates, policy_version, checkpoint, request.dispatch_generation)
    task_digest_payload = {
        "task_id": task_id,
        "brief_sha256": sha256_json(brief),
        "classifications": dict(classifications),
        "classification_warnings": tuple(sorted(set(class_warnings + evidence_warnings))),
        "classification_evidence_sha256": evidence_digest,
        "dependencies": dependencies,
        "acceptance_criteria_sha256": sha256_json(criteria),
        "verification_sha256": sha256_json(verification),
        "shared_resources": resources,
        "expected_paths": paths,
    }
    try:
        task_input_sha256 = sha256_json(task_digest_payload)
    except ValueError as exc:
        raise DecisionInputError(["task:canonicalization_failed"]) from exc
    candidate_payload = [candidate for candidate in candidates]
    try:
        candidate_snapshot_sha256 = sha256_json(candidate_payload)
        normalized_size = len(canonical_json(normalized).encode("utf-8"))
    except (TypeError, ValueError) as exc:
        raise DecisionInputError(["request:canonicalization_failed"]) from exc
    if normalized_size > MAX_JSON_BYTES:
        raise DecisionInputError(["request:too_large"])
    quota_payload = [{"route_id": candidate.route_id, "quota_status": candidate.quota_status,
                      "quota_observed_at": candidate.quota_observed_at,
                      "quota_valid_until": candidate.quota_valid_until,
                      "quota_used_percent": candidate.quota_used_percent}
                     for candidate in candidates]
    quota_snapshot_sha256 = sha256_json(quota_payload)
    return ValidatedRequest(normalized, task_input_sha256, candidate_snapshot_sha256, quota_snapshot_sha256,
                            tuple(sorted(set(class_warnings + evidence_warnings))))
