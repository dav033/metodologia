"""Validated, redacted quota evidence attached to a bounded batch decision."""
from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass

from .contracts import DecisionInputError, ValidatedRequest

MAX_BATCH_CANDIDATES = 4096
MAX_BATCH_TASKS = 128
BATCH_EVIDENCE_VERSION = "1.3.0"
BATCH_PLAN_SCHEMA_VERSION = "1.3.0"
_QUOTA_REASONS = {
    "quota_fresh", "quota_observation_stale", "quota_observation_missing", "quota_data_malformed",
    "quota_refresh_failed", "quota_exhausted", "preflight_account_limit_exceeded",
}


@dataclass(frozen=True)
class BatchQuotaEvidence:
    """Allowlisted quota facts for one considered route, without credentials or task prose."""

    schema_version: str
    task_id: str
    route_id: str
    profile: str
    account_ref: str
    state: str
    observed_at: float | None
    valid_until: float | None
    used_percent: float | None
    reason_code: str


def validate_quota_evidence(raw: object, requests_by_task: Mapping[str, ValidatedRequest]
                            ) -> dict[str, Mapping[str, BatchQuotaEvidence]]:
    evidence = raw if raw is not None else {}
    if not isinstance(evidence, Mapping) or len(evidence) > MAX_BATCH_TASKS:
        raise DecisionInputError(("batch.quota_evidence",))
    normalized: dict[str, Mapping[str, BatchQuotaEvidence]] = {}
    valid_states = {"fresh", "stale", "missing", "malformed", "refresh_failed", "exhausted"}
    for task_id, route_evidence in evidence.items():
        if task_id not in requests_by_task or not isinstance(route_evidence, Mapping) or \
                len(route_evidence) > MAX_BATCH_CANDIDATES:
            raise DecisionInputError(("batch.quota_evidence",))
        task_candidates = {candidate.route_id: candidate for candidate in requests_by_task[task_id].request.candidates}
        rows = {}
        for route_id, value in route_evidence.items():
            if (not isinstance(value, BatchQuotaEvidence) or value.schema_version != BATCH_EVIDENCE_VERSION or
                    route_id != value.route_id or
                    route_id not in task_candidates or value.task_id != task_id or
                    value.profile != task_candidates[route_id].profile or
                    value.account_ref != task_candidates[route_id].account_ref or value.state not in valid_states or
                    value.reason_code not in _QUOTA_REASONS):
                raise DecisionInputError(("batch.quota_evidence",))
            for number in (value.observed_at, value.valid_until, value.used_percent):
                if number is not None and (not isinstance(number, (int, float)) or isinstance(number, bool) or
                                           not math.isfinite(number)):
                    raise DecisionInputError(("batch.quota_evidence",))
            requested_at = requests_by_task[task_id].request.requested_at
            if value.state == "fresh" and (value.observed_at is None or value.observed_at > requested_at or
                                            value.valid_until is None or value.valid_until <= requested_at or
                                            value.valid_until <= value.observed_at or value.used_percent is None or
                                            value.used_percent >= 100) or \
                    value.state == "exhausted" and value.used_percent != 100 or \
                    value.used_percent is not None and not 0 <= value.used_percent <= 100:
                raise DecisionInputError(("batch.quota_evidence",))
            rows[route_id] = value
        normalized[task_id] = rows
    return normalized
