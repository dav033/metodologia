"""Opt-in, side-effect-free comparison of the deterministic baseline and batch policy."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .batch import (
    MAX_BATCH_CANDIDATES,
    MAX_BATCH_TASKS,
    AccountConcurrency,
    BatchPlan,
    BatchRouteExclusion,
    BatchUnassignment,
    _plan_prepared_batch,
    _prepare_batch,
    _PreparedBatch,
)
from .contracts import API_VERSION, Candidate, DecisionInputError, DecisionRequest
from .identity import sha256_json
from .policy import (
    DEFAULT_ROUTE_POLICY,
    RoutePolicyConfig,
    RoutePolicyEvidence,
    rank_candidates,
)

SHADOW_POLICY_VERSION = "m2-shadow-comparison-v1"
_SHADOW_BASELINE_ASSIGNMENT_REASONS = {"baseline_preferred_route", "baseline_capacity_alternative"}
_SHADOW_CHANGE_CODES = {
    "same_assignment", "route_changed", "assignment_added", "assignment_removed",
    "assignment_reason_changed", "same_unassignment", "unassignment_reason_changed",
}


@dataclass(frozen=True)
class ShadowAssignment:
    task_id: str
    route_id: str
    account_ref: str
    route_rank: int
    reason_code: str


@dataclass(frozen=True)
class ShadowTaskComparison:
    task_id: str
    baseline_route_id: str | None
    proposed_route_id: str | None
    baseline_reason_code: str
    proposed_reason_code: str
    difference_code: str


@dataclass(frozen=True)
class ShadowComparison:
    schema_version: str
    shadow_policy_version: str
    snapshot_sha256: str
    comparison_sha256: str
    baseline_assignments: tuple[ShadowAssignment, ...]
    baseline_unassigned: tuple[BatchUnassignment, ...]
    baseline_route_exclusions: tuple[BatchRouteExclusion, ...]
    proposed_plan: BatchPlan
    task_comparisons: tuple[ShadowTaskComparison, ...]
    dispatch_performed: bool = False
    reservations_created: bool = False
    task_state_changed: bool = False
    ledger_written: bool = False
    provider_called: bool = False

    def __post_init__(self) -> None:
        if (self.schema_version != API_VERSION or self.shadow_policy_version != SHADOW_POLICY_VERSION or
                any(value is not False for value in (self.dispatch_performed, self.reservations_created,
                                                     self.task_state_changed, self.ledger_written,
                                                     self.provider_called))):
            raise DecisionInputError(("shadow.side_effects",))


def compare_shadow_batch(requests: Sequence[DecisionRequest], *, enabled: bool,
                         account_concurrency: Sequence[AccountConcurrency] = (),
                         route_evidence_by_task: Mapping[str, Mapping[str, RoutePolicyEvidence]] | None = None,
                         policy: RoutePolicyConfig = DEFAULT_ROUTE_POLICY) -> ShadowComparison | None:
    """Return a replayable comparison only when explicitly enabled; never dispatch or persist it."""
    if not isinstance(enabled, bool):
        raise DecisionInputError(("shadow.enabled",))
    if not enabled:
        return None
    if (not isinstance(requests, Sequence) or isinstance(requests, (str, bytes)) or
            not 1 <= len(requests) <= MAX_BATCH_TASKS or
            not isinstance(account_concurrency, Sequence) or
            isinstance(account_concurrency, (str, bytes)) or len(account_concurrency) > MAX_BATCH_CANDIDATES):
        raise DecisionInputError(("shadow.input",))

    request_rows = tuple(requests)
    concurrency_rows = tuple(account_concurrency)
    prepared = _prepare_batch(
        request_rows, account_concurrency=concurrency_rows,
        route_evidence_by_task=route_evidence_by_task, policy=policy,
        preserve_baseline_by_task=None, quota_evidence_by_task=None,
    )
    proposed_plan = _plan_prepared_batch(prepared)
    baseline_assignments, baseline_unassigned, baseline_exclusions = _plan_baseline(prepared)
    task_comparisons = _compare_task_outcomes(
        tuple(prepared.requests_by_task), baseline_assignments, baseline_unassigned, proposed_plan,
    )
    snapshot_sha256 = _shadow_snapshot_fingerprint(prepared, tuple(prepared.requests_by_task))
    comparison_sha256 = sha256_json({
        "schema_version": API_VERSION,
        "shadow_policy_version": SHADOW_POLICY_VERSION,
        "snapshot_sha256": snapshot_sha256,
        "baseline_assignments": baseline_assignments,
        "baseline_unassigned": baseline_unassigned,
        "baseline_route_exclusions": baseline_exclusions,
        "proposed_plan": proposed_plan,
        "task_comparisons": task_comparisons,
        "side_effects": {
            "dispatch_performed": False,
            "reservations_created": False,
            "task_state_changed": False,
            "ledger_written": False,
            "provider_called": False,
        },
    })
    return ShadowComparison(
        API_VERSION, SHADOW_POLICY_VERSION, snapshot_sha256, comparison_sha256,
        baseline_assignments, baseline_unassigned, baseline_exclusions, proposed_plan, task_comparisons,
    )


def _plan_baseline(prepared: _PreparedBatch
                   ) -> tuple[tuple[ShadowAssignment, ...], tuple[BatchUnassignment, ...],
                              tuple[BatchRouteExclusion, ...]]:
    assignments: list[ShadowAssignment] = []
    unassigned: list[BatchUnassignment] = []
    exclusions: list[BatchRouteExclusion] = []
    account_capacity: dict[str, int] = {}
    options_by_task: dict[str, tuple[tuple[Candidate, int], ...]] = {}

    for task_id, validated in prepared.requests_by_task.items():
        ranking = rank_candidates(validated)
        exclusions.extend(
            BatchRouteExclusion(task_id, item.route_id, tuple(sorted(item.reason_codes)))
            for item in ranking.exclusions
        )
        account_options: dict[str, Candidate] = {}
        for candidate in ranking.eligible:
            account_options.setdefault(candidate.account_ref, candidate)
        options = tuple((candidate, rank) for rank, candidate in enumerate(account_options.values(), start=1))
        options_by_task[task_id] = options
        for candidate, _ in options:
            if candidate.account_ref in account_capacity:
                continue
            configured = prepared.concurrency_by_account.get(candidate.account_ref)
            account_capacity[candidate.account_ref] = (
                min(prepared.free_slots, max(0, configured.max_concurrent - configured.active_assignments))
                if configured is not None else prepared.free_slots
            )

    assigned_count = 0
    for task_id in prepared.requests_by_task:
        options = options_by_task[task_id]
        if not options:
            unassigned.append(BatchUnassignment(task_id, "no_eligible_route"))
            continue
        if assigned_count >= prepared.free_slots:
            unassigned.append(BatchUnassignment(task_id, "free_slots_exhausted"))
            continue
        for candidate, rank in options:
            if account_capacity[candidate.account_ref] < 1:
                continue
            account_capacity[candidate.account_ref] -= 1
            assignments.append(ShadowAssignment(
                task_id,
                candidate.route_id,
                candidate.account_ref,
                rank,
                "baseline_preferred_route" if rank == 1 else "baseline_capacity_alternative",
            ))
            assigned_count += 1
            break
        else:
            unassigned.append(BatchUnassignment(task_id, "account_concurrency_exhausted"))

    return (
        tuple(sorted(assignments, key=lambda row: row.task_id)),
        tuple(sorted(unassigned, key=lambda row: row.task_id)),
        tuple(sorted(exclusions, key=lambda row: (row.task_id, row.route_id))),
    )


def _compare_task_outcomes(task_ids: Sequence[str], baseline_assignments: Sequence[ShadowAssignment],
                           baseline_unassigned: Sequence[BatchUnassignment],
                           proposed_plan: BatchPlan) -> tuple[ShadowTaskComparison, ...]:
    baseline_by_task = {row.task_id: row for row in baseline_assignments}
    baseline_unassigned_by_task = {row.task_id: row for row in baseline_unassigned}
    proposed_by_task = {row.task_id: row for row in proposed_plan.assignments}
    proposed_unassigned_by_task = {row.task_id: row for row in proposed_plan.unassigned}
    comparisons = []
    for task_id in sorted(task_ids):
        baseline = baseline_by_task.get(task_id)
        proposed = proposed_by_task.get(task_id)
        baseline_reason = (baseline.reason_code if baseline is not None else
                           baseline_unassigned_by_task[task_id].reason_code)
        proposed_reason = (proposed.reason_code if proposed is not None else
                           proposed_unassigned_by_task[task_id].reason_code)
        if baseline is None and proposed is None:
            difference = "same_unassignment" if baseline_reason == proposed_reason else "unassignment_reason_changed"
        elif baseline is None:
            difference = "assignment_added"
        elif proposed is None:
            difference = "assignment_removed"
        elif baseline.route_id != proposed.route_id:
            difference = "route_changed"
        elif baseline_reason != proposed_reason:
            difference = "assignment_reason_changed"
        else:
            difference = "same_assignment"
        comparisons.append(ShadowTaskComparison(
            task_id,
            baseline.route_id if baseline is not None else None,
            proposed.route_id if proposed is not None else None,
            baseline_reason,
            proposed_reason,
            difference,
        ))
    return tuple(comparisons)


def _shadow_snapshot_fingerprint(prepared: _PreparedBatch, task_order: Sequence[str]) -> str:
    tasks = tuple({
        "task_id": task_id,
        "request_sha256": sha256_json(prepared.requests_by_task[task_id].request),
    } for task_id in task_order)
    capacities = tuple(sorted(prepared.concurrency_by_account.values(), key=lambda row: row.account_ref))
    return sha256_json({
        "schema_version": API_VERSION,
        "shadow_policy_version": SHADOW_POLICY_VERSION,
        "common_facts": prepared.common_facts,
        "ready_task_order": tuple(task_order),
        "tasks": tasks,
        "route_evidence_by_task": prepared.evidence_by_task,
        "route_policy": prepared.policy,
        "account_concurrency": capacities,
    })
