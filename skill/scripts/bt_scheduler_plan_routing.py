"""Bounded, non-reserving joint M2 route mapping for an approved Scheduler plan."""
from __future__ import annotations

import math
import re
import time
from collections.abc import Mapping, Sequence
from dataclasses import replace

import bt_scheduler_decision_adapter as decision_sources
from bt_scheduler_decision import (
    DecisionInputError,
    DecisionLedger,
    DecisionLedgerError,
    DecisionRequest,
    QuotaWindowPreference,
    RoutePolicyEvidence,
    plan_ready_batch,
)
from bt_scheduler_decision.batch import MAX_BATCH_TASKS, BatchPlan
from bt_scheduler_decision.batch_quota_evidence import (
    BATCH_EVIDENCE_VERSION,
    BatchQuotaEvidence,
)
from bt_scheduler_laya import CHECKPOINTS

_PLAN_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_QUOTA_REFRESH_PROVIDERS = {"claude", "codex", "antigravity"}


def persist_dispatch_batch(ledger: DecisionLedger, requests: Sequence[DecisionRequest], *,
                           preserve_baseline_by_task: Mapping[str, bool],
                           quota_evidence_by_task: Mapping[str, Mapping[str, BatchQuotaEvidence]]) -> BatchPlan:
    """Keep polling without dispatch proposals from consuming the bounded durable ledger."""
    preview = plan_ready_batch(
        requests, preserve_baseline_by_task=preserve_baseline_by_task,
        quota_evidence_by_task=quota_evidence_by_task,
    )
    if not preview.assignments:
        return preview
    return ledger.batch_decisions.persist(
        requests, preserve_baseline_by_task=preserve_baseline_by_task,
        quota_evidence_by_task=quota_evidence_by_task,
    )


def quota_aware_requested_at(initial_time: float, refresh_status: object) -> float:
    """Bind M2 facts after refresh, never before an observation returned by that refresh."""
    timestamps = [initial_time, time.time()]
    if isinstance(refresh_status, dict):
        for status in refresh_status.values():
            observed_at = status.get("observed_at") if isinstance(status, dict) else None
            if isinstance(observed_at, (int, float)) and not isinstance(observed_at, bool) and \
                    math.isfinite(observed_at):
                timestamps.append(float(observed_at))
    return max(timestamps)


def _no_routes(core_module, tasks, reason: str):
    return tuple(core_module.PlannedRoute(
        view.id if isinstance(getattr(view, "id", None), str) and view.id else f"invalid_task_{index}",
        reason=reason,
    ) for index, view in enumerate(tasks))


def _route_evidence(candidates, now: float) -> dict[str, RoutePolicyEvidence]:
    evidence = {}
    for candidate in candidates:
        windows = ()
        pressure = candidate.quota_used_percent
        if (candidate.quota_status == "available" and isinstance(pressure, (int, float)) and
                not isinstance(pressure, bool) and math.isfinite(pressure) and 0 <= pressure <= 100 and
                isinstance(candidate.quota_valid_until, (int, float)) and candidate.quota_valid_until > now):
            windows = (QuotaWindowPreference("current_quota", float(pressure), None),)
        history = candidate.history
        duration = history.median_duration_seconds if history.duration_samples > 0 else None
        evidence[candidate.route_id] = RoutePolicyEvidence(quota_windows=windows, duration_seconds=duration)
    return evidence


def _apply_preflight(candidates, refresh_status):
    normalized = []
    for candidate in candidates:
        if candidate.provider not in _QUOTA_REFRESH_PROVIDERS:
            normalized.append(candidate)
            continue
        state = refresh_status.get(candidate.profile) if isinstance(refresh_status, dict) else None
        if not isinstance(state, dict) or state.get("status") != "available":
            candidate = replace(candidate, quota_status="unknown")
        normalized.append(candidate)
    return tuple(normalized)


def _quota_evidence(task_id, candidates, refresh_status):
    rows = {}
    reason_states = {
        "quota_fresh": "fresh", "quota_observation_stale": "stale", "quota_observation_missing": "missing",
        "quota_data_malformed": "malformed", "quota_refresh_failed": "refresh_failed",
        "quota_unavailable": "missing",
    }
    for candidate in candidates:
        if candidate.provider not in _QUOTA_REFRESH_PROVIDERS:
            state = {"available": "fresh", "stale": "stale", "exhausted": "exhausted"}.get(
                candidate.quota_status, "missing",
            )
            reason = f"quota_{state}"
        else:
            preflight = refresh_status.get(candidate.profile) if isinstance(refresh_status, dict) else None
            if not isinstance(preflight, dict) and isinstance(refresh_status, dict):
                preflight = refresh_status.get("*")
            preflight = preflight if isinstance(preflight, dict) else {}
            reason = preflight.get("reason") if isinstance(preflight.get("reason"), str) else "quota_observation_missing"
            state = preflight.get("state") if preflight.get("state") in {
                "fresh", "stale", "missing", "malformed", "refresh_failed", "exhausted",
            } else reason_states.get(reason, "missing")
            if reason == "preflight_account_limit_exceeded":
                state = "refresh_failed"
            if state == "fresh" and candidate.quota_status != "available":
                state = "stale" if candidate.quota_status == "stale" else \
                    "exhausted" if candidate.quota_status == "exhausted" else "missing"
                reason = "quota_observation_stale" if state == "stale" else \
                    "quota_exhausted" if state == "exhausted" else "quota_observation_missing"
        rows[candidate.route_id] = BatchQuotaEvidence(
            BATCH_EVIDENCE_VERSION, task_id, candidate.route_id, candidate.profile, candidate.account_ref, state,
            candidate.quota_observed_at, candidate.quota_valid_until, candidate.quota_used_percent, reason,
        )
    return rows


def _batch_metadata(core_module, batch_id: str, candidate, assignment, quota_evidence) -> dict[str, str]:
    metadata = {
        "schema_version": core_module.ROUTING_CONTRACT_VERSION,
        "batch_id": batch_id,
        "route_id": candidate.route_id,
        "provider": candidate.provider,
        "model": candidate.model,
        "profile": candidate.profile,
        "effort": candidate.effort or "",
        "account_ref": candidate.account_ref,
        "assignment_reason": assignment.reason_code,
        "policy_rank": str(assignment.route_policy_rank),
    }
    if quota_evidence is not None:
        metadata.update({
            "quota_state": quota_evidence.state,
            "quota_reason": quota_evidence.reason_code,
            "quota_observed_at": "" if quota_evidence.observed_at is None else str(quota_evidence.observed_at),
            "quota_valid_until": "" if quota_evidence.valid_until is None else str(quota_evidence.valid_until),
            "quota_used_percent": "" if quota_evidence.used_percent is None else str(quota_evidence.used_percent),
        })
    return metadata


def plan_full_dag(core_module, port, request, refresh_quota: object):
    """Allocate the whole bounded DAG through one M2 batch and persist the selected references."""
    tasks = request.tasks if isinstance(request.tasks, Sequence) and not isinstance(request.tasks, (str, bytes)) else ()
    if not tasks:
        return ()
    if request.contract_version != core_module.ROUTING_CONTRACT_VERSION or \
            not isinstance(request.plan_sha256, str) or not _PLAN_SHA256.fullmatch(request.plan_sha256):
        return _no_routes(core_module, tasks, "m2_batch_invalid")
    if len(tasks) > MAX_BATCH_TASKS:
        return _no_routes(core_module, tasks, "m2_batch_task_limit_exceeded")

    try:
        refresh_status = refresh_quota(port.project)
    except Exception:  # noqa: BLE001 - quota refresh failure makes every affected route ineligible.
        refresh_status = {"*": {"status": "unavailable", "reason": "quota_refresh_failed"}}
    requested_at = quota_aware_requested_at(request.now, refresh_status)

    checkpoint_revision = CHECKPOINTS[port.checkpoint][1]
    seen = set()
    try:
        decision_requests = []
        candidates_by_task = {}
        evidence_by_task = {}
        preserve_baseline = {}
        for view in tasks:
            if not isinstance(view, core_module.TaskView) or not isinstance(view.id, str) or not view.id or view.id in seen:
                return _no_routes(core_module, tasks, "m2_batch_invalid")
            seen.add(view.id)
            task, kind, classifications = decision_sources.task_facts(
                view.id, view.meta, view.dependencies, view.acceptance_criteria, view.verification,
                view.shared_resources, view.expected_paths,
            )
            candidates = _apply_preflight(
                decision_sources._candidate_rows(port.project, kind, classifications, requested_at), refresh_status,
            )
            decision_request = DecisionRequest(
                request.plan_id, request.revision, request.plan_sha256, len(tasks), requested_at, task,
                candidates, decision_sources.POLICY_VERSION, checkpoint_revision,
            )
            decision_requests.append(decision_request)
            candidates_by_task[view.id] = {
                (candidate.route_id, candidate.account_ref): candidate for candidate in candidates
            }
            evidence_by_task[view.id] = _route_evidence(candidates, requested_at)
            preserve_baseline[view.id] = kind == "audit"

        batch = port.ledger.batch_decisions.persist(
            tuple(decision_requests), route_evidence_by_task=evidence_by_task,
            preserve_baseline_by_task=preserve_baseline,
            quota_evidence_by_task={view.id: _quota_evidence(
                view.id, decision_requests[index].candidates, refresh_status,
            ) for index, view in enumerate(tasks)},
        )
    except DecisionInputError as exc:
        reason = "m2_batch_candidate_limit_exceeded" if any(
            "candidate_limit" in issue or "route_matrix_limit" in issue for issue in exc.issues
        ) else "m2_batch_invalid"
        return _no_routes(core_module, tasks, reason)
    except DecisionLedgerError as exc:
        reason = "m2_batch_unavailable" if exc.code in {"ledger_unavailable", "read_only"} else "m2_batch_invalid"
        return _no_routes(core_module, tasks, reason)
    except (TypeError, ValueError, OSError):
        return _no_routes(core_module, tasks, "m2_batch_invalid")

    assignments = {item.task_id: item for item in batch.assignments}
    unassigned = {item.task_id: item.reason_code for item in batch.unassigned}
    quota_evidence_by_route = {(row.task_id, row.route_id): row for row in batch.quota_evidence}
    output = []
    for view in tasks:
        assignment = assignments.get(view.id)
        if assignment is None:
            output.append(core_module.PlannedRoute(view.id, reason=unassigned.get(view.id, "m2_batch_invalid")))
            continue
        candidate = candidates_by_task.get(view.id, {}).get((assignment.route_id, assignment.account_ref))
        if candidate is None:
            output.append(core_module.PlannedRoute(view.id, reason="m2_batch_invalid"))
            continue
        output.append(core_module.PlannedRoute(
            view.id, _batch_metadata(core_module, batch.batch_id, candidate, assignment,
                                     quota_evidence_by_route.get((view.id, assignment.route_id))),
        ))
    return tuple(output)
