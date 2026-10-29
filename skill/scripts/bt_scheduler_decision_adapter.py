"""Translate Scheduler M1 requests and methodology facts into bounded M2 recommendations."""
from __future__ import annotations

import math
import shutil
import statistics
from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any

import bt_agents
import bt_agy
import bt_events
import bt_outcomes
import bt_profiles
import bt_routing_policy
import bt_role_policy
import bt_subscriptions
import bt_usage
from bt_scheduler_decision import (
    Candidate,
    DecisionRequest,
    QuotaWindowPreference,
    RouteHistory,
    RoutePolicyEvidence,
    TaskFacts,
    account_reference,
    candidate_route_id,
    plan_ready_batch,
    validate_request,
)
from bt_scheduler_decision.engine import comparable_metric_snapshots
from bt_scheduler_decision.policy import rank_with_route_policy

if TYPE_CHECKING:
    from bt_scheduler_monitor_adapter import MetricSample

POLICY_VERSION = "m2-methodology-v1"
PLAN_SCHEMA_CAPABILITIES = frozenset({"1.0.0", "1.1.0", "1.2.0", "1.3.0"})
_INVALID_AUTH = {"invalid_credentials", "http_401", "http_403", "unauthorized", "authentication_failed"}
_VERIFIED_FAILURES = {"verify_failed", "verification_rejected"}
_CLAIMED = {"claimed", "claimed_unverified"}
_FAILURES = {"agent_reported_failure", "usage_limit", "timeout", "verify_failed", "verification_rejected",
             "blocked_needs_human", "partial", "no_verdict"}


def _finite_epoch(value: object) -> float | None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    try:
        numeric = float(value)
    except (OverflowError, ValueError):
        return None
    return numeric if math.isfinite(numeric) else None


def _usage_facts(provider: str, account_key: str, model: str, usage: Mapping[str, Any], now: float
                 ) -> tuple[str, str, float | None, float | None, float | None, str | None]:
    """Return quota/auth facts from existing local quota readers; never refresh or contact a provider."""
    if provider == "antigravity":
        row = bt_agy.load_cache()
        pressure, exhausted_until = bt_agy.capacity(now)
        observed = _finite_epoch(row.get("observed_at"))
        status = row.get("status")
        max_age = bt_agy.MAX_AGE_SEC
    else:
        row = usage.get(account_key)
        row = row if isinstance(row, Mapping) else {}
        pressure, exhausted_until = bt_subscriptions.capacity(row, model, now)
        observed = _finite_epoch(row.get("observed_at"))
        status = row.get("status")
        max_age = bt_subscriptions.MAX_AGE_SECONDS

    valid_until = observed + max_age if observed is not None else None
    fresh = observed is not None and observed <= now and valid_until is not None and valid_until > now
    auth_status = "valid" if status == "ok" and fresh else \
        "invalid" if str(status).lower() in _INVALID_AUTH else "unknown"
    if (exhausted_until is not None and exhausted_until > now) or (pressure is not None and pressure >= 100):
        quota_status = "exhausted"
    elif pressure is not None and status == "ok" and fresh:
        quota_status = "available"
    elif valid_until is not None and valid_until <= now:
        quota_status = "stale"
    else:
        quota_status = "unknown"
    return quota_status, auth_status, observed, valid_until, pressure, \
        "capacity_exhausted" if quota_status == "exhausted" else None


def _tier_floor(classifications: Mapping[str, object], kind: str) -> tuple[int, tuple[str, ...]]:
    """Return the task floor and stable rules that explain which validated facts set it."""
    complexity = classifications.get("complexity")
    scope = classifications.get("scope")
    coupling = classifications.get("coupling")
    risk = classifications.get("risk")
    duration = classifications.get("estimated_minutes")
    architecture = complexity == "extreme" or scope == "full_system"
    router_complexity = "L" if complexity in {"high", "extreme"} else None
    tier = bt_agents.start_tier("architecture" if architecture else None, kind, router_complexity)
    rules = [f"kind:{kind}"]
    if complexity == "high":
        rules.append("complexity:high")
    if architecture:
        rules.append("architecture:extreme_or_full_system")
    if scope in {"large_change", "full_feature"}:
        tier = max(tier, 1)
        rules.append(f"scope:{scope}")
    if coupling in {"medium", "high"}:
        tier = max(tier, 1)
        rules.append(f"coupling:{coupling}")
    if isinstance(duration, int) and not isinstance(duration, bool):
        if duration >= 240:
            tier = max(tier, bt_agents.TOP)
            rules.append("duration:at_least_240_minutes")
        elif duration >= 120:
            tier = max(tier, 1)
            rules.append("duration:at_least_120_minutes")
    if risk == "high":
        tier = max(tier, bt_agents.TOP)
        rules.append("risk:high")
    capped = bt_routing_policy.cap_tier(tier, kind)
    if capped < tier:
        rules.append(f"kind_ceiling:{capped}")
    return capped, tuple(rules)


def _tier_for(classifications: Mapping[str, object], kind: str) -> int:
    """Return the minimum model tier required by task kind and validated classifications."""
    return _tier_floor(classifications, kind)[0]


def _token_count(row: Mapping[str, Any]) -> int | None:
    """Final measured tokens of a session, by the one canonical semantics (bt_usage); partial records answer None."""
    return bt_usage.measured_total(row.get("usage"), row.get("agent"))


def _route_options(provider: str, tier: int, task_kind: str, complexity: str | None = None) -> tuple[tuple[str, str | None], ...]:
    """Enumerate configured model/effort rungs at or above the task floor."""
    role = bt_role_policy.role_for_kind(task_kind)
    if role:
        return tuple((model, effort) for p, model, effort in bt_role_policy.options(role, complexity) if p == provider)
    if provider not in bt_agents.PROVIDERS:
        return ()
    options: list[tuple[str, str | None]] = []
    seen: set[tuple[str, str | None]] = set()
    for rung_tier in range(tier, bt_agents.TOP + 1):
        model, effort = bt_agents.model_for(provider, rung_tier, kind=task_kind)
        model_spec = bt_agents.MODELS.get(model) if isinstance(model, str) else None
        if not isinstance(model_spec, Mapping) or model_spec.get("provider") != provider or \
                (effort is not None and effort not in bt_agents.EFFORTS):
            continue
        option = (model, effort)
        if option not in seen:
            seen.add(option)
            options.append(option)
    return tuple(options)


def _route_role(task_kind: str, classifications: Mapping[str, object]) -> str | None:
    """Apply M1's optional task metadata without changing task kind or learning identity."""
    return bt_role_policy.role_for_task(task_kind, classifications.get("review_axis"))


def _history_snapshot(rows: Sequence[Mapping[str, Any]]) -> dict[tuple[str, str, str, str, str], RouteHistory]:
    """Route history per (provider, model, profile, effort, kind). Quality comes from TASK outcomes (bt_outcomes: the same
    verdicts the router learns from), so a session with two verified tasks and one failure is 2 + 1, not one failure;
    duration and tokens come from the session once. Provider losses (quota, credits, sign-in) are not a model failure."""
    grouped: dict[tuple[str, str, str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("origin") == "synthetic":
            continue
        key = (str(row.get("agent") or ""), str(row.get("model") or ""), str(row.get("profile") or ""),
               str(row.get("effort") or ""), str(row.get("kind") or "implement"))
        grouped[key].append(row)

    by_key: dict[tuple, list] = defaultdict(list)
    for o in bt_outcomes.outcomes([r for rs_ in grouped.values() for r in rs_]):  # dedupe across ALL rows first
        row = o["row"]
        by_key[(str(row.get("agent") or ""), str(row.get("model") or ""), str(row.get("profile") or ""),
                str(row.get("effort") or ""), str(row.get("kind") or "implement"))].append(o)
    result = {}
    for key, samples in grouped.items():
        found = by_key.get(key, [])
        successes = sum(o["verdict"] == "verified" for o in found)
        verified_failures = sum(o["verdict"] == "failed" for o in found)
        claimed = sum(o["result"] in _CLAIMED for o in found)
        failures = sum(o["verdict"] == "provider_loss" or o["result"] in _FAILURES - _VERIFIED_FAILURES for o in found)
        durations = [float(row["seconds"]) for row in samples
                     if isinstance(row.get("seconds"), (int, float)) and not isinstance(row.get("seconds"), bool)
                     and math.isfinite(row["seconds"]) and row["seconds"] >= 0]
        tokens = [value for row in samples if (value := _token_count(row)) is not None]
        verified = successes + verified_failures
        quality = "unknown" if not samples else "observed" if verified >= 5 else "sparse"
        result[key] = RouteHistory(
            quality, successes, verified_failures, claimed, failures, len(durations),
            float(statistics.median(durations)) if durations else None, len(tokens),
            int(statistics.median(tokens)) if tokens else None,
        )
    return result


def metric_samples_for_route(samples: Sequence[MetricSample], *, provider: str, profile: str | None,
                             model: str | None, name: str, unit: str,
                             comparability_key: str) -> tuple[MetricSample, ...]:
    """Select exact, comparable snapshots while preserving their provenance and quality metadata."""
    if not samples:
        return ()
    # M4 is optional for M1/M2 operation. Import its validated contract only when evidence is supplied.
    from bt_scheduler_monitor_adapter import MetricSample

    for sample in samples:
        if not isinstance(sample, MetricSample):
            raise TypeError("M4 metric input must contain validated MetricSample values")
    return comparable_metric_snapshots(tuple(samples), provider=provider, profile=profile, model=model,
                                       name=name, unit=unit, comparability_key=comparability_key)


def task_facts(task_id: str, meta_value: object, dependencies: Sequence[str], acceptance_criteria: Sequence[str],
               verification: Sequence[Mapping[str, Any]], shared_resources: Sequence[str],
               expected_paths: Sequence[str]) -> tuple[TaskFacts, str, Mapping[str, object]]:
    """Translate only the M1 task facts needed by M2; M1 contract types stay inside its adapter."""
    meta = meta_value if isinstance(meta_value, Mapping) else {}
    title = meta.get("title") if isinstance(meta.get("title"), str) else task_id
    objective = meta.get("objective") if isinstance(meta.get("objective"), str) else ""
    brief_parts = [title.strip(), objective.strip(), *(item.strip() for item in acceptance_criteria)]
    brief = "\n".join(part for part in brief_parts if part)[:2048]
    classifications = {key: meta.get(key) for key in
                       ("complexity", "scope", "estimated_minutes", "risk", "coupling", "confidence")}
    route_classifications = dict(classifications)
    if meta.get("review_axis") == "visual":
        route_classifications["review_axis"] = "visual"
    evidence = meta.get("classification_evidence")
    kind = "design" if meta.get("kind") == "design" else bt_agents.infer_kind(title, meta.get("kind"))
    task = TaskFacts(task_id, brief, classifications, evidence if isinstance(evidence, Mapping) else {},
                     tuple(dependencies), tuple(acceptance_criteria), tuple(verification),
                     tuple(shared_resources), tuple(expected_paths))
    return task, kind, route_classifications


def _candidate_rows(project: str, task_kind: str, classifications: Mapping[str, object], now: float
                    ) -> tuple[Candidate, ...]:
    pool = bt_agents.pool_for(project)
    if not pool:
        return ()
    profiles = bt_profiles.load()
    usage = bt_subscriptions.load()
    tier = _tier_for(classifications, task_kind)
    routes, _ = bt_agents.candidates(project, pool, tier, task_kind, risk=str(classifications.get("risk") or "") or None,
                                    complexity=str(classifications.get("complexity") or "") or None,
                                    allow_explore=False, role=_route_role(task_kind, classifications))
    router_rank = {
        (route.get("profile"), route.get("agent"), route.get("model"), route.get("effort")): index
        for index, route in enumerate(routes)
    }
    histories = _history_snapshot(bt_events.read_all())
    candidates = []
    for profile in pool:
        spec = profiles.get(profile)
        if not isinstance(spec, Mapping):
            continue
        provider = str(spec.get("provider") or "")
        options = _route_options(provider, tier, task_kind, str(classifications.get("complexity") or ""))
        if not options:
            continue
        key = bt_agents.account_key(profile, provider)
        cooldown = bt_agents.cooling_until(profile, provider)
        source_status = "temporarily_unavailable" if cooldown is not None and cooldown > now else "available"
        source_reasons = ("cooldown_active",) if source_status != "available" else ()
        binary = spec.get("bin") or provider
        runtime_status = "available" if shutil.which(str(binary)) else "unavailable"
        for model, effort in options:
            quota, auth, observed, valid_until, pressure, reason = _usage_facts(provider, key, model, usage, now)
            model_source_reasons = source_reasons if source_reasons else (("capacity_exhausted",) if reason else ())
            history_key = (provider, model, profile, effort or "", task_kind)
            history = histories.get(history_key, RouteHistory())
            route_id = candidate_route_id(provider, model, profile, effort)
            route_rank = router_rank.get((profile, provider, model, effort))
            candidates.append(Candidate(
                route_id, provider, model, profile, account_reference(key), effort,
                source_status, model_source_reasons, True, auth, runtime_status, quota,
                observed, valid_until, pressure, route_rank, history,
            ))
    return tuple(candidates)


# ------------------------------------------------------------------------------------------------- durable runtime
# The durable runtime (bt_durable) routes over the operator's allowed list (`execution.routes`) instead of the catalogue
# tiers: the list is the authorization and the baseline order, the live quota reading is the capacity. M2 decides over
# those candidates with the same hard filters, route policy and per-account matching the Scheduler's dispatch uses.
DURABLE_POLICY_VERSION = "m2-durable-v1"
# bt_quota_live caches a reading for 60 s; one older than this is not a statement about capacity now
LIVE_QUOTA_VALIDITY_SECONDS = 300.0
_RISK_LEVELS = ("low", "medium", "high")


def _durable_profile_facts(project: str, provider: str, profile: str) -> tuple[bool, str]:
    """(authorized, runtime status) of one allowed route. A named profile must exist for this provider, pass the work
    gate and not be excluded by the project; the provider's default account (no profile) is gated again by the driver
    at launch against the engine's ambient environment, as the static route list always was."""
    if not profile:
        binary = bt_profiles.DEFAULT_BIN.get(provider) or provider
        return True, "available" if shutil.which(binary) else "unavailable"
    try:
        spec = bt_profiles.get(profile)
        bt_profiles.authorize(profile, project)
    except SystemExit:
        return False, "unknown"
    authorized = spec.get("provider") == provider and profile not in bt_profiles.excluded_profiles(project)
    binary = str(spec.get("bin") or bt_profiles.DEFAULT_BIN.get(provider) or provider)
    return authorized, "available" if shutil.which(binary) else "unavailable"


def _durable_candidate(project: str, index: int, route: Mapping[str, Any], kind: str,
                       histories: Mapping[tuple[str, str, str, str, str], RouteHistory]) -> tuple[Candidate, float | None]:
    """One allowed route as an M2 candidate, plus the account's cooldown mark. The live reading is the capacity
    signal: `available` needs a fresh observation, `exhausted` is a hard source reason, anything else is unknown (M2
    never treats unknown as available). A cooldown mark from an earlier usage limit counts only while the live
    reading cannot say otherwise: a fresh reading with headroom is newer evidence than the mark."""
    provider, model = str(route["provider"]), str(route["model"])
    profile, effort = str(route.get("profile") or ""), str(route.get("effort") or "") or None
    m2_profile = profile or provider                  # the default account's profile id (bt_profiles.DEFAULTS)
    status = str(route.get("status") or "")
    auth = "valid" if status == "ok" else "invalid" if status.lower() in _INVALID_AUTH else "unknown"
    observed, used = _finite_epoch(route.get("observed_at")), _finite_epoch(route.get("used_percent"))
    reasons: set[str] = set()
    valid_until = None
    if route.get("capacity") == "available" and observed is not None:
        quota, valid_until = "available", observed + LIVE_QUOTA_VALIDITY_SECONDS
    elif route.get("capacity") == "exhausted":
        quota = "exhausted"
        reasons.add("capacity_exhausted")
    else:
        quota = "unknown"
    cooling = bt_agents.cooling_until(profile or None, provider)
    source_status = "available"
    if cooling is not None and quota != "available":
        source_status = "temporarily_unavailable"
        reasons.add("cooldown_active")
    authorized, runtime = _durable_profile_facts(project, provider, profile)
    history = histories.get((provider, model, profile, effort or "", kind), RouteHistory())
    return Candidate(candidate_route_id(provider, model, m2_profile, effort), provider, model, m2_profile,
                     account_reference(bt_agents.account_key(profile or None, provider)), effort, source_status,
                     tuple(sorted(reasons)), authorized, auth, runtime, quota, observed, valid_until, used, index,
                     history), cooling


def _durable_evidence(candidate: Candidate) -> RoutePolicyEvidence:
    """Route-policy evidence from the same facts: the live pressure of an available account and measured duration."""
    windows = ()
    if candidate.quota_status == "available" and candidate.quota_used_percent is not None and \
            0 <= candidate.quota_used_percent < 100:
        windows = (QuotaWindowPreference("live_quota", float(candidate.quota_used_percent), None),)
    history = candidate.history
    return RoutePolicyEvidence(quota_windows=windows, duration_seconds=history.median_duration_seconds
                               if history.duration_samples > 0 else None)


def durable_route_ranking(project: str, *, plan_id: str, revision: int, plan_sha256: str, task_id: str, meta: object,
                          dependencies: Sequence[str] = (), acceptance_criteria: Sequence[str] = (),
                          verification: Sequence[Mapping[str, Any]] = (), shared_resources: Sequence[str] = (),
                          expected_paths: Sequence[str] = (), routes: Sequence[Mapping[str, Any]], now: float,
                          with_history: bool = True) -> dict[str, Any]:
    """M2's recommendation for one READY task over the durable runtime's allowed routes.

    `routes` are plain facts in the operator's preference order: provider, model, profile ("" = the provider's default
    account), effort, and the live capacity reading (`capacity` available | exhausted | unknown, `used_percent`,
    `observed_at`, `status` = the reading's own status code). The answer is plain data keyed by position in `routes`:
    the selected position (None when M2 finds no eligible route), every eligible position in route-policy order, every
    rejected position with M2's stable reason codes, each account's cooldown mark, and the identities (batch id, input
    hash, policy versions) that make the decision replayable. Reads local caches only (profiles, cooldown marks, attempt
    history); it never refreshes quota, reserves anything or calls a provider."""
    task, kind, _ = task_facts(task_id, meta, dependencies, acceptance_criteria, verification, shared_resources,
                               expected_paths)
    histories: Mapping[tuple[str, str, str, str, str], RouteHistory] = {}
    if with_history:
        try:
            histories = _history_snapshot(bt_events.read_all())
        except Exception:  # noqa: BLE001 - history only orders equals; an unreadable history is unknown, not an error
            histories = {}
    observed = [value for route in routes if (value := _finite_epoch(route.get("observed_at"))) is not None]
    requested_at = max([float(now), *observed])       # facts are bound after the readings they rely on
    candidates: list[Candidate] = []
    index_of: dict[str, int] = {}
    described: list[dict[str, Any]] = []
    rejected: dict[int, list[str]] = {}
    for index, route in enumerate(routes):
        candidate, cooling = _durable_candidate(project, index, route, kind, histories)
        described.append({"route_id": candidate.route_id, "account_ref": candidate.account_ref,
                          "cooldown_until": cooling, "runtime": candidate.runtime_status,
                          "authorized": candidate.profile_authorized})
        if candidate.route_id in index_of:
            rejected[index] = ["duplicate_route"]
            continue
        index_of[candidate.route_id] = index
        candidates.append(candidate)
    preserve = kind != "docs"                         # as the Scheduler's dispatch: the baseline order leads
    answer: dict[str, Any] = {"policy_version": DURABLE_POLICY_VERSION, "requested_at": requested_at,
                              "task_kind": kind, "preserve_baseline": preserve, "routes": described,
                              "selected": None, "ranked": [], "rejected": [], "batch_id": None, "input_sha256": None,
                              "route_policy_version": None, "batch_policy_version": None,
                              "assignment_reason": None, "unassigned_reason": None}
    if not candidates:
        answer["rejected"] = [{"index": i, "reasons": r} for i, r in sorted(rejected.items())]
        return answer
    request = DecisionRequest(plan_id, revision, plan_sha256, 1, requested_at, task, tuple(candidates),
                              DURABLE_POLICY_VERSION, None)
    evidence = {candidate.route_id: _durable_evidence(candidate) for candidate in candidates}
    validated = validate_request(request)
    risk = validated.request.task.classifications.get("risk")
    ranking = rank_with_route_policy(validated, evidence, risk=risk if risk in _RISK_LEVELS else None,
                                     preserve_baseline=preserve)
    batch = plan_ready_batch((request,), route_evidence_by_task={task_id: evidence},
                             preserve_baseline_by_task={task_id: preserve})
    for exclusion in ranking.hard_exclusions:
        rejected[index_of[exclusion.route_id]] = list(exclusion.reason_codes)
    for exclusion in ranking.quality_exclusions:
        rejected[index_of[exclusion.route_id]] = [exclusion.reason_code]
    selected = batch.assignments[0] if batch.assignments else None
    answer.update({
        "selected": index_of[selected.route_id] if selected else None,
        "assignment_reason": selected.reason_code if selected else None,
        "unassigned_reason": batch.unassigned[0].reason_code if batch.unassigned else None,
        "ranked": [index_of[candidate.route_id] for candidate in ranking.eligible],
        "rejected": [{"index": i, "reasons": r} for i, r in sorted(rejected.items())],
        "batch_id": batch.batch_id, "input_sha256": batch.input_sha256,
        "route_policy_version": batch.route_policy_version, "batch_policy_version": batch.batch_policy_version,
    })
    return answer


__all__ = ["DURABLE_POLICY_VERSION", "PLAN_SCHEMA_CAPABILITIES", "POLICY_VERSION", "_candidate_rows",
           "durable_route_ranking", "metric_samples_for_route", "task_facts"]
