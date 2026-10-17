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
import bt_subscriptions
import bt_usage
from bt_scheduler_decision import (
    Candidate,
    RouteHistory,
    TaskFacts,
    account_reference,
    candidate_route_id,
)
from bt_scheduler_decision.engine import comparable_metric_snapshots

if TYPE_CHECKING:
    from bt_scheduler_monitor_adapter import MetricSample

POLICY_VERSION = "m2-methodology-v1"
PLAN_SCHEMA_CAPABILITIES = frozenset({"1.0.0", "1.1.0", "1.2.0"})
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
    return tier, tuple(rules)


def _tier_for(classifications: Mapping[str, object], kind: str) -> int:
    """Return the minimum model tier required by task kind and validated classifications."""
    return _tier_floor(classifications, kind)[0]


def _token_count(row: Mapping[str, Any]) -> int | None:
    """Final measured tokens of a session, by the one canonical semantics (bt_usage); partial records answer None."""
    return bt_usage.measured_total(row.get("usage"), row.get("agent"))


def _route_options(provider: str, tier: int, task_kind: str) -> tuple[tuple[str, str | None], ...]:
    """Enumerate configured model/effort rungs at or above the task floor."""
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
    evidence = meta.get("classification_evidence")
    kind = bt_agents.infer_kind(title, meta.get("kind"))
    task = TaskFacts(task_id, brief, classifications, evidence if isinstance(evidence, Mapping) else {},
                     tuple(dependencies), tuple(acceptance_criteria), tuple(verification),
                     tuple(shared_resources), tuple(expected_paths))
    return task, kind, classifications


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
                                    allow_explore=False)
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
        options = _route_options(provider, tier, task_kind)
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


__all__ = ["PLAN_SCHEMA_CAPABILITIES", "POLICY_VERSION", "_candidate_rows", "metric_samples_for_route", "task_facts"]
