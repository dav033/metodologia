"""Pure quota assessment and bounded READY-batch planning by effective account."""
from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .batch_quota import (
    BatchQuotaAssessment,
    BatchRouteQuotaAssessment,
    RouteQuotaRequirement,
    assess_batch_quota,
)
from .batch_quota_evidence import (
    BATCH_PLAN_SCHEMA_VERSION,
    BatchQuotaEvidence,
    validate_quota_evidence,
)
from .batch_validation import validate_baseline_overrides
from .contracts import (
    Candidate,
    DecisionInputError,
    DecisionRequest,
    ValidatedRequest,
)
from .identity import sha256_json
from .policy import (
    DEFAULT_ROUTE_POLICY,
    RoutePolicyConfig,
    RoutePolicyEvidence,
    rank_with_route_policy,
)
from .validation import validate_request

MAX_BATCH_TASKS = 128
MAX_BATCH_CANDIDATES = 4096
MAX_ACCOUNT_CONCURRENCY = 1_000_000
BATCH_POLICY_VERSION = "m2-bounded-batch-v2"
_ACCOUNT_REF = re.compile(r"^acct:[0-9a-f]{64}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
__all__ = [
    "AccountConcurrency", "BatchAssignment", "BatchPlan", "BatchQuotaAssessment", "BatchRouteExclusion",
    "BatchRouteQuotaAssessment", "BatchUnassignment", "RouteQuotaRequirement", "assess_batch_quota",
    "plan_ready_batch",
]


@dataclass(frozen=True)
class AccountConcurrency:
    """Known account-wide concurrency facts supplied by the caller for one planning snapshot."""

    account_ref: str
    active_assignments: int
    max_concurrent: int


@dataclass(frozen=True)
class BatchAssignment:
    task_id: str
    route_id: str
    account_ref: str
    route_policy_rank: int
    reason_code: str


@dataclass(frozen=True)
class BatchUnassignment:
    task_id: str
    reason_code: str


@dataclass(frozen=True)
class BatchRouteExclusion:
    task_id: str
    route_id: str
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class BatchPlan:
    schema_version: str
    batch_policy_version: str
    route_policy_version: str
    batch_id: str
    input_sha256: str
    free_slots: int
    considered_task_count: int
    assignments: tuple[BatchAssignment, ...]
    unassigned: tuple[BatchUnassignment, ...]
    route_exclusions: tuple[BatchRouteExclusion, ...]
    quota_evidence: tuple[BatchQuotaEvidence, ...] = ()


@dataclass(frozen=True)
class _RouteOption:
    candidate: Candidate
    policy_rank: int


@dataclass(frozen=True)
class _PreparedBatch:
    requests_by_task: Mapping[str, ValidatedRequest]
    evidence_by_task: Mapping[str, Mapping[str, RoutePolicyEvidence]]
    concurrency_by_account: Mapping[str, AccountConcurrency]
    policy: RoutePolicyConfig
    common_facts: tuple[object, ...]
    free_slots: int
    preserve_baseline_by_task: Mapping[str, bool]
    quota_evidence_by_task: Mapping[str, Mapping[str, BatchQuotaEvidence]]


def _validated_policy(policy: RoutePolicyConfig) -> RoutePolicyConfig:
    if not isinstance(policy, RoutePolicyConfig):
        raise DecisionInputError(("batch.policy",))
    try:
        return RoutePolicyConfig(
            tuple(sorted(policy.quality_floors_by_risk)),
            policy.minimum_verified_samples, policy.upcoming_reset_window_seconds,
            policy.schema_version, policy.version,
        )
    except (TypeError, ValueError) as exc:
        raise DecisionInputError(("batch.policy",)) from exc


def _validated_requests(requests: Sequence[DecisionRequest]) -> tuple[dict[str, ValidatedRequest],
                                                                      tuple[object, ...], set[str]]:
    validated_by_task: dict[str, ValidatedRequest] = {}
    common_facts: tuple[object, ...] | None = None
    candidate_count = 0
    all_account_refs: set[str] = set()
    for raw_request in requests:
        validated = validate_request(raw_request)
        request = validated.request
        task_id = request.task.task_id
        if task_id in validated_by_task:
            raise DecisionInputError(("batch.duplicate_task",))
        facts = (request.plan_id, request.revision, request.plan_sha256, request.free_slots,
                 request.requested_at, request.policy_version, request.checkpoint_revision)
        if common_facts is not None and facts != common_facts:
            raise DecisionInputError(("batch.inconsistent_snapshot",))
        common_facts = facts
        validated_by_task[task_id] = validated
        candidate_count += len(request.candidates)
        all_account_refs.update(candidate.account_ref for candidate in request.candidates)
        if candidate_count > MAX_BATCH_CANDIDATES:
            raise DecisionInputError(("batch.candidate_limit",))
    if common_facts is None:
        raise DecisionInputError(("batch.input",))
    return validated_by_task, common_facts, all_account_refs


def _validated_evidence(raw_evidence: Mapping[str, Mapping[str, RoutePolicyEvidence]] | None,
                        requests_by_task: Mapping[str, ValidatedRequest]
                        ) -> dict[str, Mapping[str, RoutePolicyEvidence]]:
    evidence_by_task = raw_evidence if raw_evidence is not None else {}
    if not isinstance(evidence_by_task, Mapping) or len(evidence_by_task) > MAX_BATCH_TASKS or \
            any(not isinstance(task_id, str) or task_id not in requests_by_task
                for task_id in evidence_by_task):
        raise DecisionInputError(("batch.evidence_identity",))
    normalized: dict[str, Mapping[str, RoutePolicyEvidence]] = {}
    for task_id, evidence in evidence_by_task.items():
        if not isinstance(evidence, Mapping):
            raise DecisionInputError(("batch.evidence",))
        normalized[task_id] = dict(evidence)
    return normalized


def _validated_concurrency(account_concurrency: Sequence[AccountConcurrency], all_account_refs: set[str]
                           ) -> dict[str, AccountConcurrency]:
    concurrency_by_account: dict[str, AccountConcurrency] = {}
    for raw_capacity in account_concurrency:
        if not isinstance(raw_capacity, AccountConcurrency):
            raise DecisionInputError(("batch.account_concurrency",))
        row = raw_capacity
        if (not isinstance(row.account_ref, str) or _ACCOUNT_REF.fullmatch(row.account_ref) is None or
                not isinstance(row.active_assignments, int) or isinstance(row.active_assignments, bool) or
                not 0 <= row.active_assignments <= MAX_ACCOUNT_CONCURRENCY or
                not isinstance(row.max_concurrent, int) or isinstance(row.max_concurrent, bool) or
                not 1 <= row.max_concurrent <= MAX_ACCOUNT_CONCURRENCY):
            raise DecisionInputError(("batch.account_concurrency",))
        if row.account_ref in concurrency_by_account:
            raise DecisionInputError(("batch.duplicate_account_concurrency",))
        if row.account_ref not in all_account_refs:
            raise DecisionInputError(("batch.unused_account_concurrency",))
        concurrency_by_account[row.account_ref] = AccountConcurrency(
            row.account_ref, row.active_assignments, row.max_concurrent,
        )
    return concurrency_by_account


def _prepare_batch(requests: Sequence[DecisionRequest], account_concurrency: Sequence[AccountConcurrency],
                   route_evidence_by_task: Mapping[str, Mapping[str, RoutePolicyEvidence]] | None,
                   policy: RoutePolicyConfig,
                   preserve_baseline_by_task: Mapping[str, bool] | None,
                   quota_evidence_by_task: Mapping[str, Mapping[str, BatchQuotaEvidence]] | None) -> _PreparedBatch:
    requests_by_task, common_facts, all_account_refs = _validated_requests(requests)
    evidence = _validated_evidence(route_evidence_by_task, requests_by_task)
    baseline = validate_baseline_overrides(
        preserve_baseline_by_task, set(requests_by_task), MAX_BATCH_TASKS,
    )
    quota_evidence = validate_quota_evidence(quota_evidence_by_task, requests_by_task)
    concurrency = _validated_concurrency(account_concurrency, all_account_refs)
    normalized_policy = _validated_policy(policy)
    return _PreparedBatch(requests_by_task, evidence, concurrency, normalized_policy,
                          common_facts, int(common_facts[3]), baseline, quota_evidence)


def _rank_batch_routes(prepared: _PreparedBatch) -> tuple[dict[str, tuple[_RouteOption, ...]],
                                                           dict[str, str],
                                                           tuple[BatchRouteExclusion, ...]]:
    options_by_task: dict[str, tuple[_RouteOption, ...]] = {}
    excluded_reason_by_task: dict[str, str] = {}
    route_exclusions: list[BatchRouteExclusion] = []
    matrix_size = 0
    for task_id in sorted(prepared.requests_by_task):
        validated = prepared.requests_by_task[task_id]
        risk = validated.request.task.classifications.get("risk")
        ranking = rank_with_route_policy(
            validated, prepared.evidence_by_task.get(task_id, {}), risk=risk,
            preserve_baseline=prepared.preserve_baseline_by_task.get(task_id, False), policy=prepared.policy,
        )
        route_exclusions.extend(
            BatchRouteExclusion(task_id, item.route_id, item.reason_codes)
            for item in ranking.hard_exclusions
        )
        route_exclusions.extend(
            BatchRouteExclusion(task_id, item.route_id, (item.reason_code,))
            for item in ranking.quality_exclusions
        )
        account_options: dict[str, _RouteOption] = {}
        for position, candidate in enumerate(ranking.eligible, start=1):
            account_options.setdefault(candidate.account_ref, _RouteOption(candidate, position))
        matrix_size += len(account_options)
        if matrix_size > MAX_BATCH_CANDIDATES:
            raise DecisionInputError(("batch.route_matrix_limit",))
        ordered = tuple(sorted(account_options.values(), key=lambda option: (option.policy_rank,
                                                                              option.candidate.route_id)))
        options_by_task[task_id] = ordered
        if not ordered:
            excluded_reason_by_task[task_id] = (
                "quality_floor_no_supported_route"
                if ranking.fallback_reason == "quality_floor_no_supported_route"
                else "no_eligible_route"
            )
    return options_by_task, excluded_reason_by_task, tuple(sorted(route_exclusions,
                                                                  key=lambda item: (item.task_id, item.route_id)))


def _account_capacities(options_by_task: Mapping[str, tuple[_RouteOption, ...]],
                        concurrency_by_account: Mapping[str, AccountConcurrency],
                        free_slots: int) -> dict[str, int]:
    capacity_by_account: dict[str, int] = {}
    for task_options in options_by_task.values():
        for option in task_options:
            account_ref = option.candidate.account_ref
            configured = concurrency_by_account.get(account_ref)
            capacity_by_account[account_ref] = min(
                free_slots,
                max(0, configured.max_concurrent - configured.active_assignments)
                if configured is not None else free_slots,
            )
    return capacity_by_account


def _match_batch_routes(options_by_task: Mapping[str, tuple[_RouteOption, ...]],
                        capacity_by_account: Mapping[str, int], free_slots: int) -> dict[str, str]:
    task_order = sorted(options_by_task, key=lambda task_id: (len(options_by_task[task_id]), task_id))
    account_order = {
        task_id: tuple(option.candidate.account_ref for option in options_by_task[task_id])
        for task_id in options_by_task
    }
    assigned_account_by_task: dict[str, str] = {}
    occupants_by_account: dict[str, set[str]] = defaultdict(set)

    def assign(task_id: str, account_ref: str) -> None:
        previous = assigned_account_by_task.get(task_id)
        if previous is not None:
            occupants_by_account[previous].remove(task_id)
        assigned_account_by_task[task_id] = account_ref
        occupants_by_account[account_ref].add(task_id)

    def augment(task_id: str, seen_accounts: set[str]) -> bool:
        for account_ref in account_order[task_id]:
            if account_ref in seen_accounts:
                continue
            seen_accounts.add(account_ref)
            occupants = occupants_by_account[account_ref]
            if len(occupants) < capacity_by_account[account_ref]:
                assign(task_id, account_ref)
                return True
            movable = sorted(occupants, key=lambda occupant: (-len(account_order[occupant]), occupant))
            for occupant in movable:
                if augment(occupant, seen_accounts):
                    assign(task_id, account_ref)
                    return True
        return False

    for task_id in task_order:
        if len(assigned_account_by_task) >= free_slots:
            break
        augment(task_id, set())
    return assigned_account_by_task


def _assignment_rows(options_by_task: Mapping[str, tuple[_RouteOption, ...]],
                     excluded_reason_by_task: Mapping[str, str], assigned_account_by_task: Mapping[str, str],
                     task_ids: Sequence[str], free_slots: int
                     ) -> tuple[tuple[BatchAssignment, ...], tuple[BatchUnassignment, ...]]:
    assignment_option_by_task_account = {
        (task_id, option.candidate.account_ref): option
        for task_id, task_options in options_by_task.items()
        for option in task_options
    }
    assignments = tuple(
        BatchAssignment(
            task_id,
            (option := assignment_option_by_task_account[(task_id, account_ref)]).candidate.route_id,
            account_ref,
            option.policy_rank,
            "route_policy_preferred" if option.policy_rank == 1 else "account_capacity_alternative",
        )
        for task_id, account_ref in sorted(assigned_account_by_task.items())
    )
    unassigned_rows: list[BatchUnassignment] = []
    for task_id in sorted(task_ids):
        if task_id in assigned_account_by_task:
            continue
        if not options_by_task[task_id]:
            reason = excluded_reason_by_task[task_id]
        elif len(assigned_account_by_task) >= free_slots:
            reason = "free_slots_exhausted"
        else:
            reason = "account_concurrency_exhausted"
        unassigned_rows.append(BatchUnassignment(task_id, reason))
    return assignments, tuple(unassigned_rows)


def _batch_fingerprint(prepared: _PreparedBatch) -> tuple[str, str]:
    normalized_capacities = tuple(sorted(prepared.concurrency_by_account.values(), key=lambda row: row.account_ref))
    fingerprint_rows = []
    for task_id in sorted(prepared.requests_by_task):
        try:
            fingerprint_rows.append({
                "task_id": task_id,
                "request_sha256": sha256_json(prepared.requests_by_task[task_id].request),
                "route_evidence": prepared.evidence_by_task.get(task_id, {}),
                "preserve_baseline": prepared.preserve_baseline_by_task.get(task_id, False),
                "quota_evidence": prepared.quota_evidence_by_task.get(task_id, {}),
            })
        except (TypeError, ValueError) as exc:
            raise DecisionInputError(("batch.fingerprint",)) from exc
    try:
        input_sha256 = sha256_json({
            "batch_policy_version": BATCH_POLICY_VERSION,
            "route_policy": prepared.policy,
            "common_facts": prepared.common_facts,
            "tasks": fingerprint_rows,
            "account_concurrency": normalized_capacities,
            "preserve_baseline_by_task": prepared.preserve_baseline_by_task,
        })
    except (TypeError, ValueError) as exc:
        raise DecisionInputError(("batch.fingerprint",)) from exc
    batch_id = sha256_json({"batch_policy_version": BATCH_POLICY_VERSION, "input_sha256": input_sha256})
    return batch_id, input_sha256


def plan_ready_batch(requests: Sequence[DecisionRequest], *,
                     account_concurrency: Sequence[AccountConcurrency] = (),
                     route_evidence_by_task: Mapping[str, Mapping[str, RoutePolicyEvidence]] | None = None,
                     preserve_baseline_by_task: Mapping[str, bool] | None = None,
                     quota_evidence_by_task: Mapping[str, Mapping[str, BatchQuotaEvidence]] | None = None,
                     policy: RoutePolicyConfig = DEFAULT_ROUTE_POLICY) -> BatchPlan:
    """Select a deterministic, capacity-aware assignment set without creating durable reservations."""
    if (not isinstance(requests, Sequence) or isinstance(requests, (str, bytes)) or
            not 1 <= len(requests) <= MAX_BATCH_TASKS or
            not isinstance(account_concurrency, Sequence) or
            isinstance(account_concurrency, (str, bytes)) or len(account_concurrency) > MAX_BATCH_CANDIDATES or
            not isinstance(policy, RoutePolicyConfig)):
        raise DecisionInputError(("batch.input",))

    prepared = _prepare_batch(requests, account_concurrency, route_evidence_by_task, policy,
                              preserve_baseline_by_task, quota_evidence_by_task)
    return _plan_prepared_batch(prepared)


def _plan_prepared_batch(prepared: _PreparedBatch) -> BatchPlan:
    """Plan from one already-normalized snapshot so callers can safely compare multiple policies."""
    options_by_task, excluded_reason_by_task, route_exclusions = _rank_batch_routes(prepared)
    capacities = _account_capacities(options_by_task, prepared.concurrency_by_account, prepared.free_slots)
    assigned = _match_batch_routes(options_by_task, capacities, prepared.free_slots)
    assignments, unassigned = _assignment_rows(
        options_by_task, excluded_reason_by_task, assigned, tuple(prepared.requests_by_task), prepared.free_slots,
    )
    batch_id, input_sha256 = _batch_fingerprint(prepared)
    return BatchPlan(
        BATCH_PLAN_SCHEMA_VERSION, BATCH_POLICY_VERSION, prepared.policy.version, batch_id, input_sha256, prepared.free_slots,
        len(prepared.requests_by_task), assignments, unassigned, route_exclusions,
        tuple(sorted((row for task_rows in prepared.quota_evidence_by_task.values() for row in task_rows.values()),
                     key=lambda row: (row.task_id, row.route_id))),
    )
