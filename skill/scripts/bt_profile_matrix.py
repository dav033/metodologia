"""Per-identity installation diagnostics without network authentication probes."""
from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

import bt_profiles


IDENTITIES = ("claude-personal", "claude-work", "codex-1", "codex-luis", "antigravity")
FALLBACKS = {"claude-personal": "claude", "codex-1": "codex"}


def _account_directory(spec: dict[str, Any], home: Path, environ: dict[str, str]) -> Path:
    provider = spec.get("provider")
    selectors = {"claude": ("CLAUDE_CONFIG_DIR", ".claude"),
                 "codex": ("CODEX_HOME", ".codex"), "antigravity": (None, ".gemini")}
    variable, default = selectors.get(provider, (None, ".unknown"))
    selected = (spec.get("env") or {}).get(variable) if variable else None
    if not selected:
        return home / default
    expanded = str(selected)
    for key, value in environ.items():
        expanded = expanded.replace(f"${key}", value).replace(f"${{{key}}}", value)
    if expanded == "~" or expanded.startswith("~/"):
        expanded = str(home / expanded[2:]) if expanded.startswith("~/") else str(home)
    return Path(expanded)


def diagnose(profile_id: str, project: str, home: str | Path | None = None,
             environ: dict[str, str] | None = None, path: str | None = None) -> dict[str, Any]:
    """Report local profile readiness; authentication and smoke are unknown without evidence."""
    profiles = bt_profiles.load()
    selected_home = Path(home) if home is not None else Path.home()
    selected_env = dict(os.environ) if environ is None else environ
    return _diagnose(profile_id, profiles.get(profile_id), project, selected_home, selected_env,
                     selected_env.get("PATH", "") if path is None else path)


def _diagnose(profile_id: str, spec: dict[str, Any] | None, project: str,
              home: str | Path, env: dict[str, str], path: str | None = None) -> dict[str, Any]:
    if not isinstance(spec, dict):
        return {"profile_id": profile_id, "present": False, "binary_found": False,
                "directory_provisioned": False, "authenticated": None,
                "authorized_for_project": False, "smoke_verified": None}

    binary = shutil.which(str(spec.get("bin", "")), path=env.get("PATH", "") if path is None else path)
    try:
        authorized = not bool(spec.get("work_only")) or bt_profiles.is_work_project(project)
    except (OSError, ValueError):
        authorized = False
    config_dir = _account_directory(spec, Path(home), env)
    return {"profile_id": profile_id, "present": True, "binary_found": binary is not None,
            "directory_provisioned": config_dir.is_dir(), "authenticated": None,
            "authorized_for_project": authorized, "smoke_verified": None}


def matrix(project: str, profiles: dict[str, dict[str, Any]], home: str | Path | None = None,
           environ: dict[str, str] | None = None, path: str | None = None) -> list[dict[str, Any]]:
    """Return exactly one row per supported identity and mark shared accounts as duplicates."""
    rows = []
    first_by_account: dict[tuple[str, str], str] = {}
    home_path = Path(home) if home is not None else Path.home()
    env = dict(os.environ) if environ is None else environ
    binary_path = env.get("PATH", "") if path is None else path
    for identity in IDENTITIES:
        profile_id = identity if identity in profiles else FALLBACKS.get(identity)
        spec = profiles.get(profile_id) if profile_id else None
        if not isinstance(spec, dict):
            rows.append({"identity": identity, "profile_id": identity, "present": False,
                         "binary_found": False, "directory_provisioned": False, "authenticated": None,
                         "authorized_for_project": False, "smoke_verified": None, "duplicate_of": None})
            continue
        provider = str(spec.get("provider", ""))
        account = _account_directory(spec, home_path, env).resolve(strict=False)
        key = (provider, str(account))
        duplicate_of = first_by_account.get(key)
        first_by_account.setdefault(key, identity)
        detail = _diagnose(profile_id, spec, project, home_path, env, binary_path)
        rows.append({"identity": identity, **detail, "duplicate_of": duplicate_of})
    return rows
