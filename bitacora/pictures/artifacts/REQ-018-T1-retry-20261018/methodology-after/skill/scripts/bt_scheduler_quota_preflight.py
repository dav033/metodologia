"""Bounded Scheduler-boundary refresh with redacted quota status facts."""
from __future__ import annotations

import math
import re
import time

_MAX_ACCOUNTS = 32


def refresh(project: str, maximum_accounts: int = _MAX_ACCOUNTS) -> dict[str, dict[str, object]]:
    import bt_agents
    import bt_agy
    import bt_profiles
    import bt_subscriptions

    pool = bt_agents.pool_for(project)
    profiles = bt_profiles.load()
    groups = {}
    for pid in pool:
        if not isinstance(profiles.get(pid), dict):
            continue
        try:
            identity = bt_agents._pool_account_identity(pid, profiles[pid])
        except (SystemExit, KeyError, TypeError):
            identity = (profiles[pid].get("provider"), bt_agents.account_key(pid))
        groups.setdefault(identity, []).append(pid)
    if len(groups) > maximum_accounts:
        return {"*": {"status": "unavailable", "reason": "preflight_account_limit_exceeded"}}

    subscription_ids = [ids[0] for ids in groups.values()
                        if profiles[ids[0]].get("provider") in ("claude", "codex")]
    result: dict[str, dict[str, object]] = {}
    try:
        rows = bt_subscriptions.ensure_fresh(subscription_ids, project=project) if subscription_ids else []
        if not isinstance(rows, list):
            raise TypeError("quota poll returned an invalid result")
        poll_failed = False
    except Exception:  # noqa: BLE001 - a source failure invalidates this preflight snapshot.
        rows, poll_failed = [], True
    by_profile = {row.get("profile"): row for row in rows if isinstance(row, dict)}
    now = time.time()
    for identity, ids in groups.items():
        leader = ids[0]
        if profiles[leader].get("provider") not in ("claude", "codex"):
            continue
        row = by_profile.get(leader, {})
        status = row.get("status", "not_sampled")
        pressure = row.get("bottleneck_used_percent")
        observed = row.get("observed_at")
        valid_time = isinstance(observed, (int, float)) and not isinstance(observed, bool) and math.isfinite(observed)
        valid_pressure = isinstance(pressure, (int, float)) and not isinstance(pressure, bool) and \
            math.isfinite(pressure) and 0 <= pressure <= 100
        fresh = status == "ok" and valid_pressure and valid_time and observed <= now and \
            observed + bt_subscriptions.MAX_AGE_SECONDS > now
        if not isinstance(status, str) or re.fullmatch(r"[a-z][a-z0-9_]{0,39}", status) is None:
            status = "invalid_status"
            fresh = False
        if poll_failed:
            state, reason = "refresh_failed", "quota_refresh_failed"
        elif status == "invalid_status":
            state, reason = "malformed", "quota_data_malformed"
        elif status != "ok" and status != "not_sampled" and valid_time and \
                observed + bt_subscriptions.MAX_AGE_SECONDS <= now:
            state, reason = "stale", "quota_refresh_failed"
        elif status != "ok" and status != "not_sampled":
            state, reason = "refresh_failed", "quota_refresh_failed"
        elif fresh:
            state, reason = "fresh", "quota_fresh"
        elif status == "ok" and (not valid_pressure or not valid_time or observed > now):
            state, reason = "malformed", "quota_data_malformed"
        elif valid_time and observed + bt_subscriptions.MAX_AGE_SECONDS <= now:
            state, reason = "stale", "quota_observation_stale"
        else:
            state, reason = "missing", "quota_observation_missing"
        item = {"status": "available" if fresh else "unavailable", "reason": reason, "state": state,
                "observed_at": observed if valid_time else None,
                "valid_until": observed + bt_subscriptions.MAX_AGE_SECONDS if valid_time else None,
                "used_percent": pressure if valid_pressure else None}
        result.update({pid: dict(item) for pid in ids})

    google_groups = [ids for ids in groups.values() if profiles[ids[0]].get("provider") == "antigravity"]
    if google_groups:
        try:
            cache = bt_agy.refresh()
            pressure, _ = bt_agy.capacity()
            status = cache.get("status") if isinstance(cache, dict) else None
            observed = cache.get("observed_at") if isinstance(cache, dict) else None
            now = time.time()
            valid_time = isinstance(observed, (int, float)) and not isinstance(observed, bool) and math.isfinite(observed)
            valid_pressure = isinstance(pressure, (int, float)) and not isinstance(pressure, bool) and math.isfinite(pressure)
            fresh = status == "ok" and valid_pressure and valid_time and observed <= now and \
                observed + bt_agy.MAX_AGE_SEC > now
            state = "fresh" if fresh else "stale" if valid_time and observed + bt_agy.MAX_AGE_SEC <= now else \
                "malformed" if status == "ok" else "refresh_failed" if status == "error" else "missing"
            reasons = {"fresh": "quota_fresh", "stale": "quota_refresh_failed" if status == "error" else "quota_observation_stale",
                       "malformed": "quota_data_malformed", "refresh_failed": "quota_refresh_failed",
                       "missing": "quota_observation_missing"}
            reason = reasons[state]
        except Exception:  # noqa: BLE001 - source errors fail closed.
            fresh, reason, state, observed, valid_time, pressure = False, "quota_refresh_failed", "refresh_failed", None, False, None
        item = {"status": "available" if fresh else "unavailable", "reason": reason, "state": state,
                "observed_at": observed if valid_time else None,
                "valid_until": observed + bt_agy.MAX_AGE_SEC if valid_time else None,
                "used_percent": pressure if fresh else None}
        for ids in google_groups:
            result.update({pid: dict(item) for pid in ids})
    return result
