"""Translate Scheduler M1 requests and methodology facts into bounded M2 recommendations."""
from __future__ import annotations

import math
import shutil
import statistics
from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

import bt_agents
import bt_agy
import bt_events
import bt_profiles
import bt_subscriptions
from bt_scheduler_decision import (
    Candidate,
    RouteHistory,
    TaskFacts,
    account_reference,
    candidate_route_id,
)

POLICY_VERSION = "m2-methodology-v1"
_INVALID_AUTH = {"invalid_credentials", "http_401", "http_403", "unauthorized", "authentication_failed"}
_VERIFIED_FAILURES = {"verify_failed", "verification_rejected"}
_CLAIMED = {"claimed", "claimed_unverified"}
_FAILURES = {"agent_reported_failure", "usage_limit", "timeout", "verify_failed", "verification_rejected",
             "blocked_needs_human", "partial", "no_verdict"}


def _finite_epoch(value: object) -> float | None:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
        return None
    return float(value)


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
    if exhausted_until is not None and exhausted_until > now:
        quota_status = "exhausted"
    elif pressure is not None and status == "ok" and fresh:
        quota_status = "available"
    elif valid_until is not None and valid_until <= now:
        quota_status = "stale"
    else:
        quota_status = "unknown"
    return quota_status, auth_status, observed, valid_until, pressure, \
        "capacity_exhausted" if quota_status == "exhausted" else None


def _tier_for(classifications: Mapping[str, object], kind: str) -> int:
    """Use the existing router ladder, with a conservative M2 floor for task risk and reach."""
    complexity = classifications.get("complexity")
    router_complexity = "L" if complexity in {"high", "extreme"} else None
    level = "architecture" if complexity == "extreme" or classifications.get("scope") == "full_system" else None
    tier = bt_agents.start_tier(level, kind, router_complexity)
    risk = classifications.get("risk")
    scope = classifications.get("scope")
    coupling = classifications.get("coupling")
    duration = classifications.get("estimated_minutes")
    if risk == "high" or level == "architecture" or \
            isinstance(duration, int) and not isinstance(duration, bool) and duration >= 240:
        return max(tier, bt_agents.TOP)
    if risk == "medium" or scope in {"large_change", "full_feature"} or coupling == "high" or \
            isinstance(duration, int) and not isinstance(duration, bool) and duration >= 120:
        return max(tier, 1)
    return tier


def _token_count(row: Mapping[str, Any]) -> int | None:
    usage = row.get("usage")
    if not isinstance(usage, Mapping):
        return None
    total = usage.get("total_tokens")
    if isinstance(total, int) and not isinstance(total, bool) and total >= 0:
        return total
    input_tokens, output_tokens = usage.get("input_tokens"), usage.get("output_tokens")
    if all(isinstance(value, int) and not isinstance(value, bool) and value >= 0
           for value in (input_tokens, output_tokens)):
        extras = sum(value for value in (usage.get("cache_read_tokens"), usage.get("cache_write_tokens"))
                     if isinstance(value, int) and not isinstance(value, bool) and value >= 0)
        return input_tokens + output_tokens + extras
    return None


def _history_snapshot(rows: Sequence[Mapping[str, Any]]) -> dict[tuple[str, str, str, str, str], RouteHistory]:
    grouped: dict[tuple[str, str, str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("origin") == "synthetic":
            continue
        key = (str(row.get("agent") or ""), str(row.get("model") or ""), str(row.get("profile") or ""),
               str(row.get("effort") or ""), str(row.get("kind") or "implement"))
        grouped[key].append(row)

    result = {}
    for key, samples in grouped.items():
        outcomes = [str(row.get("outcome") or bt_events.outcome_of(str(row.get("result") or ""), None))
                    for row in samples]
        successes = sum(outcome == "verified" for outcome in outcomes)
        verified_failures = sum(outcome in _VERIFIED_FAILURES for outcome in outcomes)
        claimed = sum(outcome in _CLAIMED for outcome in outcomes)
        failures = sum(outcome in _FAILURES for outcome in outcomes)
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
    kind = bt_agents.infer_kind(title)
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
    routes, _ = bt_agents.candidates(project, pool, tier, task_kind)
    router_rank = {route["profile"]: index for index, route in enumerate(routes)}
    histories = _history_snapshot(bt_events.read_all())
    candidates = []
    for profile in pool:
        spec = profiles.get(profile)
        if not isinstance(spec, Mapping):
            continue
        provider = str(spec.get("provider") or "")
        model, effort = bt_agents.model_for(provider, tier, kind=task_kind)
        if not isinstance(model, str):
            continue
        key = bt_agents.account_key(profile, provider)
        quota, auth, observed, valid_until, pressure, reason = _usage_facts(provider, key, model, usage, now)
        cooldown = bt_agents.cooling_until(profile, provider)
        source_status = "temporarily_unavailable" if cooldown is not None and cooldown > now else "available"
        source_reasons = ("cooldown_active",) if source_status != "available" else \
            ("capacity_exhausted",) if reason else ()
        binary = spec.get("bin") or provider
        runtime_status = "available" if shutil.which(str(binary)) else "unavailable"
        history_key = (provider, model, profile, effort or "", task_kind)
        history = histories.get(history_key, RouteHistory())
        route_id = candidate_route_id(provider, model, profile, effort)
        candidates.append(Candidate(
            route_id, provider, model, profile, account_reference(key), effort,
            source_status, source_reasons, True, auth, runtime_status, quota,
            observed, valid_until, pressure, router_rank.get(profile), history,
        ))
    return tuple(candidates)


__all__ = ["POLICY_VERSION", "_candidate_rows", "task_facts"]
