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
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise UsageError("invalid_response")
    return float(value)


def window(used: object, reset: object, minutes: object) -> dict:
    used, reset, minutes = number(used), number(reset), number(minutes)
    if not 0 <= used <= 100 or reset <= 0 or minutes <= 0:
        raise UsageError("invalid_response")
    return {"used_percent": used, "resets_at": reset, "window_minutes": minutes}


def parse_codex(payload: object) -> dict:
    if not isinstance(payload, dict):
        raise UsageError("invalid_response")
    buckets = payload.get("rateLimitsByLimitId")
    bucket = buckets.get("codex") if isinstance(buckets, dict) else None
    bucket = bucket or payload.get("rateLimits")
    if not isinstance(bucket, dict):
        raise UsageError("missing_windows")
    windows = {}
    for key in ("primary", "secondary"):
        value = bucket.get(key)
        if value is None:
            continue
        if not isinstance(value, dict):
            raise UsageError("invalid_response")
        item = window(value.get("usedPercent"), value.get("resetsAt"), value.get("windowDurationMins"))
        name = {300: "five_hour", 10080: "seven_day"}.get(item["window_minutes"])
        if name:
            windows[name] = item
    if not windows:
        raise UsageError("missing_windows")
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
        if not isinstance(value, dict) or not isinstance(value.get("resets_at"), str):
            raise UsageError("invalid_response")
        try:
            stamp = dt.datetime.fromisoformat(value["resets_at"].replace("Z", "+00:00"))
            if stamp.tzinfo is None:
                raise ValueError("timezone required")
            reset = stamp.timestamp()
        except ValueError as exc:
            raise UsageError("invalid_response") from exc
        windows[name] = window(value.get("utilization"), reset, minutes)
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
