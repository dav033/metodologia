"""Machine-local subscription samples and deterministic account headroom decisions (schema v1)."""
from __future__ import annotations

import datetime as dt
import json
import os
import time
from pathlib import Path

import bt_profiles
from bt_core import STATE
from bt_lock import central_lock
from bt_subscription_sources import UsageError, number, read_claude, read_codex, window

POLL_SECONDS = 3600
# Match the timer's 60s accuracy + 60s jitter without accidentally skipping every other hour.
MIN_POLL_SECONDS = POLL_SECONDS - 120
MAX_AGE_SECONDS = 7200


def load(state: Path | None = None) -> dict:
    try:
        data = json.loads(((state or STATE) / "subscription-usage.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict) or data.get("schema_version") != 1 or not isinstance(data.get("accounts"), dict):
        return {}
    return data["accounts"]


def capacity(row: object, model: str, now: float | None = None) -> tuple[float | None, float | None]:
    """Return bottleneck usage and exhausted-until; unknown data is never treated as unused capacity."""
    now = time.time() if now is None else now
    if not isinstance(row, dict):
        return None, None
    try:
        observed = number(row.get("observed_at"))
        if now < observed:
            return None, None
        raw = row.get("windows")
        if not isinstance(raw, dict):
            return None, None
        allow_unknown_reset = row.get("provider") == "claude"
        names = ["five_hour", "seven_day"]
        if model in ("sonnet", "opus"):
            names.append("seven_day_" + model)
        active = {}
        for name in names:
            item = raw.get(name)
            if item is None:
                continue
            if not isinstance(item, dict) or "resets_at" not in item:
                raise UsageError("invalid_response")
            item = window(item.get("used_percent"), item.get("resets_at"), item.get("window_minutes"),
                          allow_unknown_reset=allow_unknown_reset)
            if item["window_minutes"] != (300 if name == "five_hour" else 10080):
                raise UsageError("invalid_response")
            if item["resets_at"] is None or item["resets_at"] > now:
                active[name] = item
        model_buckets = raw.get("_model_buckets")
        if model_buckets is not None:
            if not isinstance(model_buckets, dict):
                raise UsageError("invalid_response")
            scoped = model_buckets.get(model)
            if scoped is not None:
                if not isinstance(scoped, list) or not scoped or len(scoped) > 32:
                    raise UsageError("invalid_response")
                for index, bucket in enumerate(scoped):
                    if not isinstance(bucket, dict) or not bucket or bucket.get("quota_unknown") is True:
                        raise UsageError("invalid_response")
                    for name, item in bucket.items():
                        if name not in ("five_hour", "seven_day") or not isinstance(item, dict):
                            raise UsageError("invalid_response")
                        item = window(item.get("used_percent"), item.get("resets_at"), item.get("window_minutes"))
                        expected = 300 if name == "five_hour" else 10080
                        if item["window_minutes"] != expected:
                            raise UsageError("invalid_response")
                        if item["resets_at"] > now:
                            active[f"model_{index}_{name}"] = item
        exhausted = [item["resets_at"] for item in active.values()
                     if item["used_percent"] >= 100 and item["resets_at"] is not None]
        fresh = row.get("status") == "ok" and now - observed <= MAX_AGE_SECONDS
        pressure = max(item["used_percent"] for item in active.values()) if fresh and all(
            name in active for name in ("five_hour", "seven_day")) else None
        return pressure, max(exhausted) if exhausted else None
    except UsageError:
        return None, None


def _write_samples(accounts: dict) -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    path = STATE / "subscription-usage.json"
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps({"schema_version": 1, "accounts": accounts}, indent=1) + "\n", encoding="utf-8")
    tmp.chmod(0o600)
    tmp.replace(path)


def _reserve(key: str, profile: str, provider: str, now: float) -> dict | None:
    """Reserve this account's hourly attempt under a short lock, before external I/O."""
    with central_lock("subscription-usage"):
        current = load()
        old = current.get(key)
        old = old if isinstance(old, dict) else {}
        if old.get("status") == "manual_challenge":
            return None
        try:
            due = max(number(old.get("attempted_at", 0)) + MIN_POLL_SECONDS, number(old.get("retry_at") or 0))
        except UsageError:
            due = 0
        if now < due:
            return None
        current[key] = {**old, "profile": profile, "provider": provider,
                        "status": "sampling", "attempted_at": now}
        _write_samples(current)
        return old


def poll(selected_profiles: list[str] | tuple[str, ...] | None = None) -> list[dict]:
    """One bounded sequential read per unique registered account per hour; no model calls."""
    import bt_agents
    updates, seen = {}, set()
    profiles = bt_profiles.load()
    selected = set(selected_profiles) if selected_profiles is not None else None
    for pid, spec in profiles.items():
        if selected is not None and pid not in selected:
            continue
        provider = spec.get("provider")
        if provider not in ("claude", "codex"):
            continue
        try:
            identity = bt_agents._pool_account_identity(pid, spec)
        except SystemExit:
            env = spec.get("env") if isinstance(spec.get("env"), dict) else {}
            identity = (provider, tuple(sorted((key, os.path.normpath(os.path.expanduser(str(env[key]))))
                                                for key in bt_profiles.ACCOUNT_VARS.get(provider, ())
                                                if env.get(key))))
        if identity in seen:
            continue
        seen.add(identity)
        key = bt_agents.account_key(pid)
        now = time.time()
        old = _reserve(key, pid, provider, now)
        if old is None:
            continue
        row = {"profile": pid, "provider": provider, "attempted_at": now}
        try:
            windows = read_claude(pid) if provider == "claude" else read_codex(pid)
            row.update(status="ok", observed_at=time.time(), windows=windows)
        except UsageError as exc:
            row.update(status=exc.code, windows=old.get("windows", {}),
                       observed_at=old.get("observed_at"), retry_at=exc.retry_at)
        updates[key] = row
    if updates:
        with central_lock("subscription-usage"):
            current = load()
            accepted = {}
            for key, row in updates.items():
                existing = current.get(key)
                existing = existing if isinstance(existing, dict) else {}
                try:
                    newer = number(existing.get("attempted_at", 0)) > row["attempted_at"]
                except UsageError:
                    newer = False
                if not newer:
                    current[key] = row
                    accepted[key] = row
            _write_samples(current)
            events = STATE / "events"
            events.mkdir(exist_ok=True)
            history = events / f"subscription-usage-{dt.datetime.now(dt.timezone.utc):%Y-%m}.jsonl"
            with history.open("a", encoding="utf-8") as stream:
                for key, row in accepted.items():
                    stream.write(json.dumps({"schema_version": 1, "account": key, **row}) + "\n")
            history.chmod(0o600)
    return summary(selected_profiles)


def summary(selected_profiles: list[str] | tuple[str, ...] | None = None) -> list[dict]:
    import bt_agents
    data, rows = load(), []
    selected = set(selected_profiles) if selected_profiles is not None else None
    for pid, spec in bt_profiles.load().items():
        if selected is not None and pid not in selected:
            continue
        if spec.get("provider") not in ("claude", "codex"):
            continue
        row = data.get(bt_agents.account_key(pid), {})
        row = row if isinstance(row, dict) else {}
        pressure, exhausted = capacity(row, "sonnet" if spec["provider"] == "claude" else "gpt-6.1-sol")
        rows.append({"profile": pid, "provider": spec["provider"], "status": row.get("status", "not_sampled"),
                     "observed_at": row.get("observed_at"), "attempted_at": row.get("attempted_at"),
                     "windows": row.get("windows", {}), "bottleneck_used_percent": pressure,
                     "exhausted_until": exhausted})
    return rows
