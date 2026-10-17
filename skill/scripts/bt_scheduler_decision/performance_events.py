"""Pure normalization of M1 attempt and independent verdict facts for M2 learning."""
from __future__ import annotations

import datetime as dt
import re
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace

from .contracts import API_VERSION, LEGACY_API_VERSIONS
from .identity import canonical_json, parse_executor_reference, sha256_json

PERFORMANCE_EVENT_VERSION = API_VERSION
MAX_PERFORMANCE_EVENTS = 100_000

OUTCOMES = ("pass", "fail", "claimed_unverified", "cancelled", "infrastructure_failure", "unknown")
ATTEMPT_STATES = (
    "reserved", "dispatched", "running", "verifying", "accepted", "failed", "rejected", "cancelled",
    "uncertain", "claimed", "claimed_unverified", "unknown",
)
APPLICATION_STATUSES = ("applied", "duplicate", "stale", "invalid", "noop")
NORMALIZED_APPLICATION_STATUSES = ("applied", "stale", "invalid", "noop", "missing")
PERFORMANCE_REASON_CODES = (
    "attempt_cancelled", "attempt_failed_infrastructure", "attempt_not_terminal", "attempt_verdict_state_mismatch",
    "claimed_unverified", "conflicting_duplicate", "decision_contract_unsupported", "decision_identity_mismatch",
    "decision_missing", "multiple_applied_verdicts", "pass_evidence_missing", "route_reference_invalid",
    "selected_route_missing", "selected_route_mismatch", "synthetic_evidence", "verdict_identity_mismatch",
    "verdict_missing", "verdict_not_applied", "verdict_timestamp_invalid", "verdict_timestamp_missing",
    "verifier_missing", "verifier_not_independent",
)
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_EXECUTOR_PREFIX = "route:"
_ATTEMPT_FIELDS = {"plan_id", "revision", "task_id", "attempt_id", "executor_ref", "state", "synthetic"}
_DECISION_FIELDS = {"schema_version", "decision_id", "plan_id", "revision", "task_id", "selected_route_id"}
_VERDICT_FIELDS = {
    "verdict_id", "plan_id", "revision", "task_id", "attempt_id", "accepted", "verifier", "evidence_present",
    "application_status", "synthetic", "applied_at",
}
_EVENT_FIELDS = {
    "schema_version", "event_id", "plan_id", "revision", "task_id", "attempt_id", "attempt_state", "decision_id",
    "route_id", "verdict_id", "application_status", "synthetic", "outcome", "applied_at",
    "eligible_for_history", "reason_codes",
}


class PerformanceEventError(ValueError):
    """Stable input error; issues name fields only and never include external values."""

    code = "performance_event_invalid"

    def __init__(self, issues: Sequence[str]):
        self.issues = tuple(sorted(set(issues)))
        super().__init__(f"{self.code}: {', '.join(self.issues[:8])}")


def _mapping(value: object, allowed: set[str], required: set[str], path: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise PerformanceEventError((f"{path}:object_required",))
    if len(value) > 64 or any(not isinstance(key, str) for key in value):
        raise PerformanceEventError((f"{path}:shape_invalid",))
    keys = set(value)
    issues = [f"{path}:unexpected_field" for key in keys - allowed]
    issues.extend(f"{path}.{key}:missing" for key in required - keys)
    if issues:
        raise PerformanceEventError(issues)
    return value


def _text(value: object, path: str, *, maximum: int = 256, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise PerformanceEventError((f"{path}:text_required",))
    normalized = unicodedata.normalize("NFC", value.strip())
    try:
        normalized.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise PerformanceEventError((f"{path}:invalid_unicode",)) from exc
    if len(normalized) > maximum or (not normalized and not allow_empty):
        raise PerformanceEventError((f"{path}:length_invalid",))
    return normalized


def _revision(value: object, path: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 2**31 - 1:
        raise PerformanceEventError((f"{path}:integer_invalid",))
    return value


def _sha256(value: object, path: str, *, nullable: bool = False) -> str | None:
    if nullable and value is None:
        return None
    text = _text(value, path, maximum=64)
    if not _SHA256.fullmatch(text):
        raise PerformanceEventError((f"{path}:sha256_invalid",))
    return text


def _utc_timestamp(value: str) -> str | None:
    if not value:
        return None
    try:
        parsed = dt.datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(dt.UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _event_id(plan_id: str, revision: int, task_id: str, attempt_id: str, attempt_state: str,
              verdict_id: str | None) -> str:
    identity = {"attempt_id": attempt_id, "verdict_id": verdict_id} if verdict_id is not None else \
        {"attempt_id": attempt_id, "attempt_state": attempt_state, "verdict_id": None}
    return sha256_json({"performance_event": PERFORMANCE_EVENT_VERSION, "plan_id": plan_id,
                        "revision": revision, "task_id": task_id, **identity})


@dataclass(frozen=True)
class PerformanceEvent:
    """Redacted, replayable join of an M1 attempt, its M2 decision and an applied independent verdict."""

    schema_version: str
    event_id: str
    plan_id: str
    revision: int
    task_id: str
    attempt_id: str
    attempt_state: str
    decision_id: str | None
    route_id: str | None
    verdict_id: str | None
    application_status: str
    synthetic: bool
    outcome: str
    applied_at: str | None
    eligible_for_history: bool
    reason_codes: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "event_id": self.event_id,
            "plan_id": self.plan_id,
            "revision": self.revision,
            "task_id": self.task_id,
            "attempt_id": self.attempt_id,
            "attempt_state": self.attempt_state,
            "decision_id": self.decision_id,
            "route_id": self.route_id,
            "verdict_id": self.verdict_id,
            "application_status": self.application_status,
            "synthetic": self.synthetic,
            "outcome": self.outcome,
            "applied_at": self.applied_at,
            "eligible_for_history": self.eligible_for_history,
            "reason_codes": list(self.reason_codes),
        }

    @classmethod
    def from_dict(cls, data: object) -> PerformanceEvent:
        row = _mapping(data, _EVENT_FIELDS, _EVENT_FIELDS, "event")
        schema_version = _text(row["schema_version"], "event.schema_version", maximum=16)
        event_id = _sha256(row["event_id"], "event.event_id")
        plan_id = _text(row["plan_id"], "event.plan_id")
        revision = _revision(row["revision"], "event.revision")
        task_id = _text(row["task_id"], "event.task_id")
        attempt_id = _text(row["attempt_id"], "event.attempt_id")
        attempt_state = _text(row["attempt_state"], "event.attempt_state", maximum=32)
        decision_id = _sha256(row["decision_id"], "event.decision_id", nullable=True)
        route_id = _sha256(row["route_id"], "event.route_id", nullable=True)
        verdict_id = row["verdict_id"]
        if verdict_id is not None:
            verdict_id = _text(verdict_id, "event.verdict_id")
        application_status = _text(row["application_status"], "event.application_status", maximum=16)
        synthetic = row["synthetic"]
        outcome = _text(row["outcome"], "event.outcome", maximum=32)
        applied_at = row["applied_at"]
        if applied_at is not None:
            applied_at = _text(applied_at, "event.applied_at", maximum=64)
            if _utc_timestamp(applied_at) != applied_at:
                raise PerformanceEventError(("event.applied_at:timestamp_invalid",))
        eligible = row["eligible_for_history"]
        reasons = row["reason_codes"]
        if not isinstance(synthetic, bool) or not isinstance(eligible, bool) or not isinstance(reasons, list) or \
                len(reasons) > len(PERFORMANCE_REASON_CODES):
            raise PerformanceEventError(("event:shape_invalid",))
        if outcome not in OUTCOMES or attempt_state not in ATTEMPT_STATES or \
                application_status not in NORMALIZED_APPLICATION_STATUSES:
            raise PerformanceEventError(("event:enum_invalid",))
        if any(not isinstance(code, str) or code not in PERFORMANCE_REASON_CODES for code in reasons):
            raise PerformanceEventError(("event.reason_codes:enum_invalid",))
        normalized_reasons = tuple(sorted(set(reasons)))
        if tuple(reasons) != normalized_reasons:
            raise PerformanceEventError(("event.reason_codes:order_invalid",))
        if event_id is None or schema_version != PERFORMANCE_EVENT_VERSION or \
                event_id != _event_id(plan_id, revision, task_id, attempt_id, attempt_state, verdict_id):
            raise PerformanceEventError(("event:identity_mismatch",))
        expected_eligible = (
            outcome in ("pass", "fail") and not normalized_reasons and not synthetic and
            application_status == "applied" and decision_id is not None and route_id is not None and
            verdict_id is not None and applied_at is not None and
            ((outcome == "pass" and attempt_state == "accepted") or
             (outcome == "fail" and attempt_state == "rejected"))
        )
        if eligible != expected_eligible:
            raise PerformanceEventError(("event.eligible_for_history:mismatch",))
        return cls(schema_version, event_id, plan_id, revision, task_id, attempt_id, attempt_state, decision_id,
                   route_id, verdict_id, application_status, synthetic, outcome, applied_at, eligible,
                   normalized_reasons)


def normalize_performance_event(
    attempt: Mapping[str, object],
    decision: Mapping[str, object] | None,
    verdict: Mapping[str, object] | None,
) -> PerformanceEvent:
    """Normalize minimal M1/M2 projections; it performs no reads, writes, provider calls or authority changes."""
    attempt_row = _mapping(attempt, _ATTEMPT_FIELDS, _ATTEMPT_FIELDS, "attempt")
    plan_id = _text(attempt_row["plan_id"], "attempt.plan_id")
    revision = _revision(attempt_row["revision"], "attempt.revision")
    task_id = _text(attempt_row["task_id"], "attempt.task_id")
    attempt_id = _text(attempt_row["attempt_id"], "attempt.attempt_id")
    executor_ref = _text(attempt_row["executor_ref"], "attempt.executor_ref")
    attempt_state = _text(attempt_row["state"], "attempt.state", maximum=32).lower()
    attempt_synthetic = attempt_row["synthetic"]
    if not isinstance(attempt_synthetic, bool):
        raise PerformanceEventError(("attempt.synthetic:boolean_required",))
    if attempt_state not in ATTEMPT_STATES:
        attempt_state = "unknown"

    reasons: set[str] = set()
    if attempt_synthetic:
        reasons.add("synthetic_evidence")
    raw_executor_ref = executor_ref.removeprefix(_EXECUTOR_PREFIX)
    parsed_ref = parse_executor_reference(raw_executor_ref)
    ref_decision_id, route_id = parsed_ref if parsed_ref is not None else (None, None)
    if parsed_ref is None:
        reasons.add("route_reference_invalid")

    decision_id: str | None = ref_decision_id
    if decision is None:
        reasons.add("decision_missing")
    else:
        decision_row = _mapping(decision, _DECISION_FIELDS, _DECISION_FIELDS, "decision")
        decision_version = _text(decision_row["schema_version"], "decision.schema_version", maximum=16)
        ledger_decision_id = _sha256(decision_row["decision_id"], "decision.decision_id")
        decision_plan_id = _text(decision_row["plan_id"], "decision.plan_id")
        decision_revision = _revision(decision_row["revision"], "decision.revision")
        decision_task_id = _text(decision_row["task_id"], "decision.task_id")
        selected_route_id = _sha256(decision_row["selected_route_id"], "decision.selected_route_id", nullable=True)
        if decision_version not in {API_VERSION, *LEGACY_API_VERSIONS}:
            reasons.add("decision_contract_unsupported")
        if (ledger_decision_id, decision_plan_id, decision_revision, decision_task_id) != \
                (ref_decision_id, plan_id, revision, task_id):
            reasons.add("decision_identity_mismatch")
        if selected_route_id is None:
            reasons.add("selected_route_missing")
        elif selected_route_id != route_id:
            reasons.add("selected_route_mismatch")
        if ref_decision_id is None:
            decision_id = ledger_decision_id

    application_status = "missing"
    verdict_id: str | None = None
    applied_at: str | None = None
    synthetic = attempt_synthetic
    outcome = "unknown"

    if attempt_state == "cancelled":
        outcome = "cancelled"
        reasons.add("attempt_cancelled")
    elif attempt_state == "failed":
        outcome = "infrastructure_failure"
        reasons.add("attempt_failed_infrastructure")
    elif attempt_state in ("claimed", "claimed_unverified"):
        outcome = "claimed_unverified"
        reasons.add("claimed_unverified")
    elif attempt_state not in ("accepted", "rejected"):
        reasons.add("attempt_not_terminal")

    if verdict is None:
        if attempt_state in ("accepted", "rejected"):
            reasons.add("verdict_missing")
    else:
        verdict_row = _mapping(verdict, _VERDICT_FIELDS, _VERDICT_FIELDS, "verdict")
        verdict_id = _text(verdict_row["verdict_id"], "verdict.verdict_id")
        verdict_plan_id = _text(verdict_row["plan_id"], "verdict.plan_id")
        verdict_revision = _revision(verdict_row["revision"], "verdict.revision")
        verdict_task_id = _text(verdict_row["task_id"], "verdict.task_id")
        verdict_attempt_id = _text(verdict_row["attempt_id"], "verdict.attempt_id")
        accepted = verdict_row["accepted"]
        verifier = _text(verdict_row["verifier"], "verdict.verifier", allow_empty=True)
        evidence_present = verdict_row["evidence_present"]
        raw_status = _text(verdict_row["application_status"], "verdict.application_status", maximum=16)
        verdict_synthetic = verdict_row["synthetic"]
        raw_timestamp = _text(verdict_row["applied_at"], "verdict.applied_at", maximum=64, allow_empty=True)
        if not isinstance(accepted, bool) or not isinstance(evidence_present, bool) or not isinstance(verdict_synthetic, bool):
            raise PerformanceEventError(("verdict:boolean_field_invalid",))
        if raw_status not in APPLICATION_STATUSES:
            application_status = "invalid"
        elif raw_status in ("applied", "duplicate"):
            application_status = "applied"
        else:
            application_status = raw_status
        if application_status != "applied":
            reasons.add("verdict_not_applied")
        synthetic = attempt_synthetic or verdict_synthetic
        if synthetic:
            reasons.add("synthetic_evidence")
        if (verdict_plan_id, verdict_revision, verdict_task_id, verdict_attempt_id) != \
                (plan_id, revision, task_id, attempt_id):
            reasons.add("verdict_identity_mismatch")
        if not verifier:
            reasons.add("verifier_missing")
        elif verifier == executor_ref:
            reasons.add("verifier_not_independent")
        if attempt_state in ("accepted", "rejected"):
            expected_state = "accepted" if accepted else "rejected"
            if attempt_state != expected_state:
                reasons.add("attempt_verdict_state_mismatch")
            elif not any(reason in reasons for reason in ("verdict_identity_mismatch", "verdict_not_applied")):
                outcome = "pass" if accepted else "fail"
        else:
            reasons.add("attempt_verdict_state_mismatch")
        if accepted and not evidence_present:
            reasons.add("pass_evidence_missing")
        applied_at = _utc_timestamp(raw_timestamp)
        if not raw_timestamp:
            reasons.add("verdict_timestamp_missing")
        elif applied_at is None:
            reasons.add("verdict_timestamp_invalid")

    if attempt_state in ("accepted", "rejected") and reasons:
        outcome = "unknown"
    if outcome in ("pass", "fail") and reasons:
        outcome = "unknown"
    ordered_reasons = tuple(sorted(reasons))
    event_id = _event_id(plan_id, revision, task_id, attempt_id, attempt_state, verdict_id)
    eligible = (
        outcome in ("pass", "fail") and not ordered_reasons and not synthetic and
        application_status == "applied" and decision_id is not None and route_id is not None and
        verdict_id is not None and applied_at is not None and
        ((outcome == "pass" and attempt_state == "accepted") or
         (outcome == "fail" and attempt_state == "rejected"))
    )
    return PerformanceEvent(
        PERFORMANCE_EVENT_VERSION, event_id, plan_id, revision, task_id, attempt_id, attempt_state, decision_id,
        route_id, verdict_id, application_status, synthetic, outcome, applied_at, eligible, ordered_reasons,
    )


def reduce_performance_events(events: Sequence[PerformanceEvent]) -> tuple[PerformanceEvent, ...]:
    """Deduplicate replayed verdicts and demote conflicting identities instead of choosing a winner."""
    if isinstance(events, (str, bytes)) or not isinstance(events, Sequence) or len(events) > MAX_PERFORMANCE_EVENTS:
        raise PerformanceEventError(("events:collection_invalid",))
    grouped: dict[str, list[PerformanceEvent]] = {}
    for item in events:
        if not isinstance(item, PerformanceEvent):
            raise PerformanceEventError(("events:item_invalid",))
        checked = PerformanceEvent.from_dict(item.to_dict())
        grouped.setdefault(checked.event_id, []).append(checked)

    deduplicated: list[PerformanceEvent] = []
    for event_id in sorted(grouped):
        rows = grouped[event_id]
        applied_rows = [row for row in rows if row.application_status == "applied"]
        relevant_rows = applied_rows or rows
        serialized = {canonical_json(row.to_dict()) for row in relevant_rows}
        if len(serialized) == 1:
            deduplicated.append(relevant_rows[0])
            continue
        base = min(relevant_rows, key=lambda row: canonical_json(row.to_dict()))
        reasons = tuple(sorted({*base.reason_codes, "conflicting_duplicate"}))
        deduplicated.append(replace(base, outcome="unknown", eligible_for_history=False, reason_codes=reasons))

    applied_by_attempt: dict[tuple[str, int, str, str], list[int]] = {}
    for index, event in enumerate(deduplicated):
        if event.eligible_for_history and event.verdict_id is not None:
            identity = (event.plan_id, event.revision, event.task_id, event.attempt_id)
            applied_by_attempt.setdefault(identity, []).append(index)
    for indices in applied_by_attempt.values():
        if len({deduplicated[index].verdict_id for index in indices}) <= 1:
            continue
        for index in indices:
            event = deduplicated[index]
            reasons = tuple(sorted({*event.reason_codes, "multiple_applied_verdicts"}))
            deduplicated[index] = replace(event, outcome="unknown", eligible_for_history=False,
                                          reason_codes=reasons)
    return tuple(sorted(deduplicated, key=lambda event: event.event_id))
