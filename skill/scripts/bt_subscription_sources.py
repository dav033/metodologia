"""Read subscription quota metadata without starting a conversation or refreshing credentials."""
from __future__ import annotations

import asyncio
import datetime as dt
import email.utils
import json
import math
import time
import urllib.error
import urllib.request
from pathlib import Path

import bt_profiles


class UsageError(Exception):
    def __init__(self, code: str, retry_at: float | None = None):
        super().__init__(code)
        self.code, self.retry_at = code, retry_at


def number(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise UsageError("invalid_response")
    try:
        result = float(value)
    except OverflowError as exc:
        raise UsageError("invalid_response") from exc
    if not math.isfinite(result):
        raise UsageError("invalid_response")
    return result


def window(used: object, reset: object, minutes: object, *, allow_unknown_reset: bool = False) -> dict:
    used, minutes = number(used), number(minutes)
    if reset is None:
        if not allow_unknown_reset:
            raise UsageError("invalid_response")
    else:
        reset = number(reset)
    if not 0 <= used <= 100 or (reset is not None and reset <= 0) or minutes <= 0:
        raise UsageError("invalid_response")
    return {"used_percent": used, "resets_at": reset, "window_minutes": minutes}


def _codex_windows(bucket: dict, *, allow_missing: bool = False) -> dict:
    windows = {}
    for key in ("primary", "secondary"):
        value = bucket.get(key)
        if value is None:
            continue
        if not isinstance(value, dict):
            raise UsageError("invalid_response")
        item = window(value.get("usedPercent"), value.get("resetsAt"), value.get("windowDurationMins"))
        name = {300: "five_hour", 10080: "seven_day"}.get(item["window_minutes"])
        if name is None:
            raise UsageError("unsupported_window")
        windows[name] = item
    if not windows and not allow_missing:
        raise UsageError("missing_windows")
    return windows


def _validate_codex_bucket_controls(bucket: dict) -> None:
    reached = bucket.get("rateLimitReachedType")
    spend_control = bucket.get("spendControlReached")
    if reached is not None or spend_control is True:
        raise UsageError("usage_denied")
    if "spendControlReached" in bucket and spend_control is not False:
        raise UsageError("usage_unknown")


def parse_codex(payload: object) -> dict:
    if not isinstance(payload, dict):
        raise UsageError("invalid_response")
    allowed = payload.get("ordinaryUsageAllowed")
    if allowed is False:
        raise UsageError("usage_denied")
    if "ordinaryUsageAllowed" in payload and allowed is not True:
        raise UsageError("usage_unknown")
    buckets = payload.get("rateLimitsByLimitId")
    if buckets is not None and not isinstance(buckets, dict):
        raise UsageError("invalid_response")
    bucket = buckets.get("codex") if isinstance(buckets, dict) else None
    if bucket is None:
        legacy = payload.get("rateLimits")
        if not isinstance(legacy, dict) or legacy.get("limitId") != "codex":
            raise UsageError("missing_windows")
        bucket = legacy
    if not isinstance(bucket, dict):
        raise UsageError("missing_windows")
    _validate_codex_bucket_controls(bucket)
    windows = _codex_windows(bucket)
    model_buckets: dict[str, list[dict]] = {}
    if isinstance(buckets, dict):
        for limit_id, model_bucket in buckets.items():
            if limit_id == "codex":
                continue
            if not isinstance(model_bucket, dict):
                raise UsageError("invalid_response")
            model_slug = model_bucket.get("normalModelSlug")
            if not isinstance(model_slug, str) or not model_slug.strip():
                raise UsageError("model_quota_unknown")
            try:
                _validate_codex_bucket_controls(model_bucket)
                scoped_windows = _codex_windows(model_bucket, allow_missing=True)
            except UsageError as exc:
                if exc.code in {"unsupported_window", "usage_denied", "usage_unknown"}:
                    scoped_windows = {"quota_unknown": True}
                else:
                    raise
            if not scoped_windows:
                scoped_windows = {"quota_unknown": True}
            model_buckets.setdefault(model_slug, []).append(scoped_windows)
    if model_buckets:
        windows["_model_buckets"] = model_buckets
    return windows


def parse_claude(payload: object) -> dict:
    if not isinstance(payload, dict):
        raise UsageError("invalid_response")
    windows = {}
    for name, minutes in (("five_hour", 300), ("seven_day", 10080),
                          ("seven_day_sonnet", 10080), ("seven_day_opus", 10080)):
        value = payload.get(name)
        if value is None:
            continue
        if not isinstance(value, dict) or "resets_at" not in value:
            raise UsageError("invalid_response")
        reset_value = value["resets_at"]
        if reset_value is None:
            reset = None
        elif isinstance(reset_value, str):
            try:
                stamp = dt.datetime.fromisoformat(reset_value.replace("Z", "+00:00"))
                if stamp.tzinfo is None:
                    raise ValueError("timezone required")
                reset = stamp.timestamp()
            except (OverflowError, ValueError) as exc:
                raise UsageError("invalid_response") from exc
        else:
            raise UsageError("invalid_response")
        windows[name] = window(value.get("utilization"), reset, minutes, allow_unknown_reset=True)
    if not windows:
        raise UsageError("missing_windows")
    return windows


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise UsageError("unexpected_redirect")


def read_claude(profile: str, timeout: float = 20) -> dict:
    env = bt_profiles.env_of(profile)
    root = Path(env.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude")))
    try:
        path = root / ".credentials.json"
        if path.stat().st_size > 1_000_000:
            raise UsageError("invalid_credentials")
        credentials = json.loads(path.read_text(encoding="utf-8"))
        oauth = credentials.get("claudeAiOauth") if isinstance(credentials, dict) else None
        token = oauth.get("accessToken") if isinstance(oauth, dict) else None
        if not isinstance(token, str) or not token:
            raise UsageError("auth_unavailable")
    except (OSError, ValueError) as exc:
        raise UsageError("auth_unavailable") from exc
    request = urllib.request.Request("https://api.anthropic.com/api/oauth/usage", headers={
        "Authorization": "Bearer " + token, "anthropic-beta": "oauth-2025-04-20", "Accept": "application/json"})
    try:
        with urllib.request.build_opener(_NoRedirect).open(request, timeout=timeout) as response:
            raw = response.read(262145)
        if len(raw) > 262144:
            raise UsageError("response_too_large")
        return parse_claude(json.loads(raw))
    except urllib.error.HTTPError as exc:
        if exc.headers.get("cf-mitigated") == "challenge":
            raise UsageError("manual_challenge") from exc
        if exc.code == 429:
            delay = exc.headers.get("Retry-After", "3600")
            retry = retry_after(delay)
            raise UsageError("http_429", retry) from exc
        raise UsageError(f"http_{exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise UsageError("network_unavailable") from exc
    except (ValueError, UnicodeError) as exc:
        raise UsageError("invalid_response") from exc


def retry_after(value: str) -> float:
    now = time.time()
    try:
        until = now + float(value) if value.isdigit() else email.utils.parsedate_to_datetime(value).timestamp()
    except (TypeError, ValueError, OverflowError):
        until = now + 3600
    return max(now + 3600, until)


async def _read_codex(profile: str, timeout: float) -> dict:
    spec = bt_profiles.get(profile)
    process = await asyncio.create_subprocess_exec(spec.get("bin") or "codex", "app-server", "--stdio",
        env=bt_profiles.session_env(profile, "codex"), stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)

    async def send(message: dict):
        process.stdin.write((json.dumps(message) + "\n").encode())
        await process.stdin.drain()

    async def receive(request_id: int) -> dict:
        for _ in range(100):
            raw = await process.stdout.readline()
            if not raw:
                raise UsageError("app_server_eof")
            value = json.loads(raw)
            if not isinstance(value, dict):
                raise UsageError("invalid_response")
            if value.get("id") == request_id:
                if "error" in value:
                    raise UsageError("app_server_request_failed")
                result = value.get("result")
                if not isinstance(result, dict):
                    raise UsageError("invalid_response")
                return result
        raise UsageError("app_server_response_missing")

    try:
        await send({"method": "initialize", "id": 1, "params": {
            "clientInfo": {"name": "metodologia_usage", "version": "1.0.0"}}})
        await asyncio.wait_for(receive(1), timeout)
        await send({"method": "initialized", "params": {}})
        await send({"method": "account/rateLimits/read", "id": 2})
        return parse_codex(await asyncio.wait_for(receive(2), timeout))
    finally:
        if process.returncode is None:
            process.terminate()
        try:
            await asyncio.wait_for(process.wait(), 3)
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()


def read_codex(profile: str, timeout: float = 20) -> dict:
    try:
        return asyncio.run(_read_codex(profile, timeout))
    except TimeoutError as exc:
        raise UsageError("app_server_timeout") from exc
    except (OSError, ValueError) as exc:
        raise UsageError("app_server_unavailable") from exc
