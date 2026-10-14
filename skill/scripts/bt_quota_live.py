"""Live subscription quota readings shared by globalusage and the quota relay.

Read-only: no model calls and no credential refresh. Never touches the hourly timer's store (subscription-usage.json).
"""
from __future__ import annotations

import json
import os
import time

from bt_core import STATE

CACHE_SECONDS = 60  # avoids repeated reads (the usage API answers 429 when asked too often)


def cache_path():
    return STATE / "globalusage-cache.json"


def read_row(profile: str, provider: str, timeout: float = 20) -> dict:
    """One account's live reading as a row; a failure is the row's status, never an exception."""
    import bt_subscriptions as subs
    try:
        reader = subs.read_claude if provider == "claude" else subs.read_codex
        return {"profile": profile, "provider": provider, "status": "ok", "observed_at": time.time(),
                "windows": reader(profile, timeout)}
    except Exception as exc:
        return {"profile": profile, "provider": provider, "status": getattr(exc, "code", type(exc).__name__),
                "observed_at": None, "windows": {}}


def read_all_live() -> list[dict]:
    """Every Claude/Codex account, read in parallel (cached for CACHE_SECONDS). Each account fails on its own."""
    import concurrent.futures as cf
    import bt_profiles
    try:
        saved = json.loads(cache_path().read_text())
        if time.time() - saved["at"] < CACHE_SECONDS:
            return saved["rows"]
    except Exception:
        pass
    profiles = {p: c for p, c in bt_profiles.load().items() if c.get("provider") in ("claude", "codex")}
    with cf.ThreadPoolExecutor(max_workers=len(profiles) or 1) as ex:
        rows = list(ex.map(lambda pid: read_row(pid, profiles[pid]["provider"]), profiles))
    try:
        cache_path().write_text(json.dumps({"at": time.time(), "rows": rows}))
    except OSError:
        pass
    return rows


def current_profile(environ: dict | None = None) -> str | None:
    """The profile this session runs from: the one whose env matches the environment variables (CLAUDE_CONFIG_DIR,
    CODEX_HOME...); a provider without its own variables falls back to that provider's default profile."""
    environ = os.environ if environ is None else environ
    try:
        profiles = json.loads((STATE / "profiles.json").read_text())
    except Exception:
        return None
    for name, spec in profiles.items():
        if spec["env"] and all(environ.get(k) == v for k, v in spec["env"].items()):
            return name
    provider = "claude" if environ.get("CLAUDECODE") or environ.get("CLAUDE_CONFIG_DIR") else \
        "codex" if any(k.startswith("CODEX_") for k in environ) else None
    for name, spec in profiles.items():
        if not spec["env"] and spec["provider"] == provider:
            return name
    return None
