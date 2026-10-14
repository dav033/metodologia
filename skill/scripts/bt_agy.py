"""Antigravity CLI (`agy`) as a supervised provider: command line, result parsing and quota windows.

Role in the orchestration (decision D-004): the default AUDITOR (Gemini 3.8 Flash at low effort) and a reserve when
the other subscriptions are exhausted. Not the default builder: measured 3-6x slower than Claude/Codex, and its
effort levels only cost time (flash-high timed out twice on a task low solved). Rules and numbers:
references/agents.md. Google's FAQ states that wrapping `agy -p` in applications or rotating accounts is not
supported under consumer plans; the owner accepted that risk for audits on 2026-10-13. One account only, no rotation.

The effort is part of the model id (`gemini-3.8-flash-low|medium|high`), so the tier ladder carries no separate effort.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil
import subprocess
import tempfile

BIN = "agy"
DEFAULT_MODEL = "gemini-3.8-flash-low"
POOL_GEMINI = "Gemini Models"
POOL_OTHER = "Claude and GPT models"
_ROW = re.compile(r"^(?P<pool>.+?)\t(?P<window>Five Hour|Weekly) Limit Remaining\t(?P<left>\d+(?:\.\d+)?)%\t(?P<reset>\S+)\s*$")


def exe() -> str:
    return shutil.which(BIN) or BIN


def argv(model: str | None, prompt: str, timeout_sec: int | None = None) -> list[str]:
    """Headless command: the prompt is attached to `--print=` because `-p` swallows the next token as its prompt.
    --print-timeout makes a runaway turn end by itself instead of being killed after the supervisor's own timeout."""
    out = [exe(), "--model", model or DEFAULT_MODEL, "--dangerously-skip-permissions", "--output-format", "stream-json"]
    if timeout_sec:
        out += ["--print-timeout", f"{int(timeout_sec)}s"]
    return out + [f"--print={prompt}"]


# ---------------------------------------------------------------- usage windows (`agy --print=/usage`)

def parse_usage(text: str, now: float | None = None) -> dict:
    """windows in the schema of bt_subscriptions: five_hour / seven_day = the Gemini pool; the shared Claude+GPT pool of
    Antigravity goes under *_claude_gpt keys (informational: the router reads only the Gemini pool for Flash)."""
    windows: dict[str, dict] = {}
    for line in (text or "").splitlines():
        m = _ROW.match(line.strip("\r"))
        if not m:
            continue
        try:
            reset = dt.datetime.fromisoformat(m["reset"].replace("Z", "+00:00")).timestamp()
        except ValueError:
            continue
        suffix = "" if m["pool"].strip() == POOL_GEMINI else "_claude_gpt" if m["pool"].strip() == POOL_OTHER else None
        if suffix is None:
            continue
        name = ("five_hour" if m["window"] == "Five Hour" else "seven_day") + suffix
        windows[name] = {"used_percent": round(100.0 - float(m["left"]), 2), "resets_at": reset,
                         "window_minutes": 300 if m["window"] == "Five Hour" else 10080}
    return windows


def read_usage(timeout: float = 60) -> dict:
    """One bounded local call to the CLI's own quota report; no model turn. Raises RuntimeError on failure."""
    with tempfile.TemporaryDirectory(prefix="agy-usage-") as cwd:
        try:
            res = subprocess.run([exe(), "--dangerously-skip-permissions", "--output-format", "text",
                                  "--print=/usage"], cwd=cwd, capture_output=True, text=True, timeout=timeout,
                                 env={**os.environ})
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise RuntimeError(f"agy usage unavailable: {type(exc).__name__}") from exc
    windows = parse_usage(res.stdout)
    if "five_hour" not in windows or "seven_day" not in windows:
        raise RuntimeError("agy usage report had no Gemini windows (signed out?)")
    return windows


# ---------------------------------------------------------------- results

def result_event(raw: str) -> dict | None:
    """The last `{"event": "result", ...}` line of a stream-json session (its `result` object), or None."""
    for line in reversed((raw or "").splitlines()):
        if line.startswith("{") and '"result"' in line:
            try:
                obj = json.loads(line)
            except ValueError:
                continue
            if isinstance(obj, dict) and obj.get("event") == "result" and isinstance(obj.get("result"), dict):
                return obj["result"]
    return None


def parse_result(raw: str) -> dict | None:
    """{text, cost, is_error} in bt_runsettle's shape, or None when the output has no result event."""
    res = result_event(raw)
    if res is None:
        return None
    ok = str(res.get("status") or "").upper() == "SUCCESS"
    return {"text": str(res.get("response") or res.get("error") or ""), "cost": None, "is_error": not ok,
            "limit": "EXHAUSTED" in json.dumps(res).upper() or "RESOURCE_EXHAUSTED" in str(res.get("error") or "")}


def usage_of(raw: str) -> dict | None:
    """The conversation's token usage as the provider reported it, or None."""
    res = result_event(raw)
    u = (res or {}).get("usage")
    return u if isinstance(u, dict) else None


# ---------------------------------------------------------------- quota cache (read by the router, refreshed by the supervisor)

MAX_AGE_SEC = 7200      # older than this = unknown headroom, never "unused" (same rule as bt_subscriptions)
REFRESH_AFTER_SEC = 900  # a supervisor iteration refreshes at most every 15 minutes


def _cache_path():
    from bt_core import STATE
    return STATE / "agy-usage.json"


def load_cache() -> dict:
    try:
        data = json.loads(_cache_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def refresh(max_age: float = REFRESH_AFTER_SEC, now: float | None = None) -> dict:
    """Re-read the quota report when the cache is older than `max_age`. Failures keep the previous windows and record
    the error: the router then sees stale data (unknown headroom), and nothing stops."""
    import time as _t
    now = _t.time() if now is None else now
    cache = load_cache()
    if cache.get("observed_at") and now - float(cache["observed_at"]) < max_age:
        return cache
    try:
        windows = read_usage()
        cache = {"observed_at": now, "windows": windows, "status": "ok"}
    except RuntimeError as exc:
        cache = {**cache, "status": "error", "error": str(exc)[:120], "attempted_at": now}
    path = _cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(cache, indent=1) + "\n", encoding="utf-8")
    tmp.chmod(0o600)
    tmp.replace(path)
    return cache


def capacity(now: float | None = None) -> tuple[float | None, float | None]:
    """(most consumed percent of the active Gemini windows, exhausted-until epoch) from the cache. The percent is None
    when the data is missing, stale (> 2 h) or lacks a window: unknown headroom, never "unused". A KNOWN exhaustion
    persists until its reported reset even when the cache is stale, as in bt_subscriptions.capacity: a failed later
    read must not put an exhausted account back in rotation."""
    import time as _t
    now = _t.time() if now is None else now
    cache = load_cache()
    try:
        observed = float(cache.get("observed_at") or 0)
        windows = cache.get("windows") or {}
        active = {k: w for k, w in windows.items() if k in ("five_hour", "seven_day") and float(w["resets_at"]) > now}
        exhausted = [float(w["resets_at"]) for w in active.values() if float(w["used_percent"]) >= 100]
        fresh = cache.get("status") == "ok" and 0 <= now - observed <= MAX_AGE_SEC
        pressure = max(float(w["used_percent"]) for w in active.values()) \
            if fresh and len(active) == 2 else None
        return pressure, (max(exhausted) if exhausted else None)
    except (KeyError, TypeError, ValueError):
        return None, None
