"""Pure quota assessment and bounded READY-batch planning by effective account."""
from __future__ import annotations

import math
import re
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .contracts import (
    API_VERSION,
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
from .quota import (
    MAX_OBSERVATIONS,
    MAX_REQUIRED_WINDOWS,
    QUOTA_PROVIDERS,
    QuotaAssessment,
    QuotaObservation,
    assess_account_windows,
)
from .validation import validate_request

MAX_BATCH_ROUTES = 256
MAX_BATCH_TASKS = 128
MAX_BATCH_CANDIDATES = 4096
MAX_ACCOUNT_CONCURRENCY = 1_000_000
BATCH_POLICY_VERSION = "m2-bounded-batch-v1"
_ACCOUNT_REF = re.compile(r"^acct:[0-9a-f]{64}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")


@dataclass(frozen=True)
class RouteQuotaRequirement:
    """Quota windows required by one candidate route; aliases share account_ref, not budget rows."""

    route_id: str
    provider: str
    account_ref: str
    required_windows: tuple[tuple[str | None, str], ...]
    schema_version: str = API_VERSION


@dataclass(frozen=True)
class BatchRouteQuotaAssessment:
    route_id: str
    account_ref: str
    assessment: QuotaAssessment
    schema_version: str = API_VERSION

    @property
    def eligible(self) -> bool:
        return self.assessment.state == "available"


@dataclass(frozen=True)
class BatchQuotaAssessment:
    schema_version: str
    unique_account_count: int
    routes: tuple[BatchRouteQuotaAssessment, ...]

    @property
    def eligible_route_ids(self) -> tuple[str, ...]:
        return tuple(row.route_id for row in self.routes if row.eligible)

    @property
    def excluded_route_ids(self) -> tuple[str, ...]:
        return tuple(row.route_id for row in self.routes if not row.eligible)


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
                   policy: RoutePolicyConfig) -> _PreparedBatch:
    requests_by_task, common_facts, all_account_refs = _validated_requests(requests)
    evidence = _validated_evidence(route_evidence_by_task, requests_by_task)
    concurrency = _validated_concurrency(account_concurrency, all_account_refs)
    normalized_policy = _validated_policy(policy)
    return _PreparedBatch(requests_by_task, evidence, concurrency, normalized_policy,
                          common_facts, int(common_facts[3]))


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
            validated, prepared.evidence_by_task.get(task_id, {}), risk=risk, policy=prepared.policy,
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
        })
    except (TypeError, ValueError) as exc:
        raise DecisionInputError(("batch.fingerprint",)) from exc
    batch_id = sha256_json({"batch_policy_version": BATCH_POLICY_VERSION, "input_sha256": input_sha256})
    return batch_id, input_sha256


def plan_ready_batch(requests: Sequence[DecisionRequest], *,
                     account_concurrency: Sequence[AccountConcurrency] = (),
                     route_evidence_by_task: Mapping[str, Mapping[str, RoutePolicyEvidence]] | None = None,
                     policy: RoutePolicyConfig = DEFAULT_ROUTE_POLICY) -> BatchPlan:
    """Select a deterministic, capacity-aware assignment set without creating durable reservations."""
    if (not isinstance(requests, Sequence) or isinstance(requests, (str, bytes)) or
            not 1 <= len(requests) <= MAX_BATCH_TASKS or
            not isinstance(account_concurrency, Sequence) or
            isinstance(account_concurrency, (str, bytes)) or len(account_concurrency) > MAX_BATCH_CANDIDATES or
            not isinstance(policy, RoutePolicyConfig)):
        raise DecisionInputError(("batch.input",))

    prepared = _prepare_batch(requests, account_concurrency, route_evidence_by_task, policy)
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
        API_VERSION, BATCH_POLICY_VERSION, prepared.policy.version, batch_id, input_sha256, prepared.free_slots,
        len(prepared.requests_by_task), assignments, unassigned, route_exclusions,
    )


def assess_batch_quota(requirements: Sequence[RouteQuotaRequirement], observations: Sequence[QuotaObservation], *,
                       now: object) -> BatchQuotaAssessment:
    """Assess routes against current account windows without summing aliases or reserving capacity."""
    clock = _number(now)
    if (clock is None or clock < 0 or not isinstance(requirements, Sequence) or
            isinstance(requirements, (str, bytes)) or not 1 <= len(requirements) <= MAX_BATCH_ROUTES or
            not isinstance(observations, Sequence) or isinstance(observations, (str, bytes)) or
            len(observations) > MAX_OBSERVATIONS):
        raise DecisionInputError(("batch_quota",))
    normalized = tuple(_validate_requirement(row) for row in requirements)
    route_ids = tuple(row.route_id for row in normalized)
    if len(set(route_ids)) != len(route_ids):
        raise DecisionInputError(("batch_quota.duplicate_route",))

    grouped: dict[tuple[str, str, tuple[tuple[str | None, str], ...]], list[str]] = {}
    for row in normalized:
        key = (row.provider, row.account_ref, tuple(sorted(row.required_windows, key=lambda item: (item[0] or "", item[1]))))
        grouped.setdefault(key, []).append(row.route_id)

    results: dict[str, BatchRouteQuotaAssessment] = {}
    for (provider, account_ref, windows), grouped_routes in grouped.items():
        required_by_model: dict[str | None, list[str]] = {}
        for model, window_id in windows:
            required_by_model.setdefault(model, []).append(window_id)
        assessment = assess_account_windows(
            observations, account_ref=account_ref, provider=provider,
            required_windows={model: tuple(names) for model, names in required_by_model.items()}, now=clock,
        )
        for route_id in grouped_routes:
            results[route_id] = BatchRouteQuotaAssessment(route_id, account_ref, assessment)
    ordered_results = tuple(results[route_id] for route_id in sorted(results))
    unique_accounts = len({(row.provider, row.account_ref) for row in normalized})
    return BatchQuotaAssessment(API_VERSION, unique_accounts, ordered_results)


def _validate_requirement(value: object) -> RouteQuotaRequirement:
    if not isinstance(value, RouteQuotaRequirement):
        raise DecisionInputError(("batch_quota.requirement",))
    if (value.schema_version != API_VERSION or not isinstance(value.route_id, str) or
            _SHA256.fullmatch(value.route_id) is None or
            not isinstance(value.provider, str) or value.provider not in QUOTA_PROVIDERS or
            not isinstance(value.account_ref, str) or _ACCOUNT_REF.fullmatch(value.account_ref) is None or
            not isinstance(value.required_windows, Sequence) or isinstance(value.required_windows, (str, bytes)) or
            not 1 <= len(value.required_windows) <= MAX_REQUIRED_WINDOWS):
        raise DecisionInputError(("batch_quota.requirement",))
    normalized: list[tuple[str | None, str]] = []
    for key in value.required_windows:
        if (not isinstance(key, tuple) or len(key) != 2 or
                key[0] is not None and
                (not isinstance(key[0], str) or _TOKEN.fullmatch(key[0]) is None) or
                not isinstance(key[1], str) or _TOKEN.fullmatch(key[1]) is None):
            raise DecisionInputError(("batch_quota.windows",))
        normalized.append((key[0], key[1]))
    if len(set(normalized)) != len(normalized):
        raise DecisionInputError(("batch_quota.duplicate_window",))
    return RouteQuotaRequirement(value.route_id, value.provider, value.account_ref, tuple(normalized))


def _number(value: object) -> float | None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    try:
        result = float(value)
    except OverflowError:
        return None
    return result if math.isfinite(result) else None
