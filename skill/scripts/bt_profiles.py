"""Execution profiles (one per account identity) and the work gate.

A profile is a provider (claude / codex / antigravity) plus the environment that selects its account. Profiles hold
no credentials: authentication lives in each provider's own config directory. Only `work_only` profiles are gated:
they may run solely for projects whose project.json says `"work": true` (missing means false). Everything else may
run anywhere. The gate is a launcher guarantee, not an OS sandbox: invoking the provider binary directly bypasses it.

<root>/.state/profiles.json may add or override profiles: {"id": {"provider": ..., "env": {...}, ...}}.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from bt_core import ROOT, STATE

HOME = Path.home()
LAUNCHABLE = ("claude", "codex", "antigravity")  # providers the launcher/supervisor can drive

# Generic, machine-independent: each provider's default account. Named accounts (a second Claude config dir, a team
# Codex login, which one is work-only) are machine facts: `bitacora.py profiles add`, stored in .state/profiles.json.
DEFAULTS: dict[str, dict] = {
    "claude": {"provider": "claude", "bin": "claude", "env": {}, "work_only": False},
    "codex": {"provider": "codex", "bin": "codex", "env": {}, "work_only": False},
    "antigravity": {"provider": "antigravity", "bin": "agy", "env": {}, "work_only": False},
}


class ProfileError(SystemExit):
    """Unknown profile, or a profile that may not run this project."""


def load() -> dict[str, dict]:
    profiles = {k: dict(v) for k, v in DEFAULTS.items()}
    try:
        extra = json.loads((STATE / "profiles.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        extra = {}
    if isinstance(extra, dict):
        for pid, spec in extra.items():
            if isinstance(spec, dict) and isinstance(spec.get("provider"), str):
                profiles[pid] = {**profiles.get(pid, {"env": {}, "work_only": False, "bin": spec["provider"]}), **spec}
    return profiles


def add(pid: str, provider: str, env: dict[str, str] | None = None, work_only: bool = False,
        binary: str | None = None) -> Path:
    """Create or replace a machine-local profile in <root>/.state/profiles.json (no credentials involved)."""
    if provider not in ("claude", "codex", "antigravity"):
        raise ProfileError(f"Unknown provider '{provider}' (claude, codex, antigravity)")
    path = STATE / "profiles.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    data[pid] = {"provider": provider, "env": env or {}, "work_only": work_only,
                 "bin": binary or DEFAULTS[provider]["bin"]}
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)
    return path


def get(pid: str) -> dict:
    profiles = load()
    if pid not in profiles:
        raise ProfileError(f"Unknown profile '{pid}'. Known: {', '.join(sorted(profiles))}")
    return profiles[pid]


def provider_of(pid: str) -> str:
    return get(pid)["provider"]


def env_of(pid: str | None) -> dict[str, str]:
    """Environment overlay selecting the profile's account; {} for no profile."""
    if not pid:
        return {}
    return {k: os.path.expanduser(str(v)) for k, v in (get(pid).get("env") or {}).items()}


def is_work_project(project: str) -> bool:
    try:
        data = json.loads((ROOT / project / "project.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return isinstance(data, dict) and data.get("work") is True


def set_work(project: str, value: bool) -> Path:
    path = ROOT / project / "project.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    data["work"] = value
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)
    return path


def authorize(pid: str | None, project: str) -> None:
    """Raise ProfileError when `pid` may not run `project`. Call before any prompt with project content is built."""
    if not pid:
        return
    spec = get(pid)
    if spec.get("work_only") and not is_work_project(project):
        raise ProfileError(f"Profile '{pid}' is restricted to work projects and '{project}' is not marked "
                           f"work (set it with: bitacora.py --project {project} work true). Nothing was sent.")


def require_launchable(pid: str) -> str:
    provider = provider_of(pid)
    if provider not in LAUNCHABLE:
        raise ProfileError(f"Profile '{pid}' uses provider '{provider}', which the launcher does not drive yet "
                           f"(launchable: {', '.join(LAUNCHABLE)}).")
    return provider


def _probe(argv: list[str], env: dict[str, str]) -> str:
    try:
        res = subprocess.run(argv, capture_output=True, text=True, timeout=20, env={**os.environ, **env})
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"error: {type(exc).__name__}"
    return (res.stdout + res.stderr).strip()


def _auth_summary(spec: dict, env: dict[str, str]) -> str:
    """One line: whether the account is signed in. Never prints tokens."""
    provider = spec["provider"]
    if provider == "claude":
        out = _probe([spec["bin"], "auth", "status"], env)
        try:
            info = json.loads(out)
            return f"signed in as {info.get('email')}" if info.get("loggedIn") else "NOT signed in"
        except ValueError:
            return out.splitlines()[0] if out else "unknown"
    if provider == "codex":
        out = _probe([spec["bin"], "login", "status"], env)
        return out.splitlines()[-1] if out else "unknown"
    if provider == "antigravity":
        token = HOME / ".gemini" / "antigravity-cli" / "antigravity-oauth-token"
        return "token present (verify with: agy -p ok)" if token.exists() else "NOT signed in"
    return "unknown"


def doctor() -> list[dict]:
    rows = []
    for pid, spec in sorted(load().items()):
        exe = shutil.which(spec.get("bin", ""))
        env = env_of(pid)
        row = {"profile": pid, "provider": spec["provider"], "work_only": bool(spec.get("work_only")),
               "binary": exe or "MISSING", "launchable": spec["provider"] in LAUNCHABLE}
        for key in ("CLAUDE_CONFIG_DIR", "CODEX_HOME"):
            if key in env:
                row["auth_dir"] = env[key]
                row["auth_dir_exists"] = Path(env[key]).is_dir()
        row["auth"] = _auth_summary(spec, env) if exe else "binary missing"
        rows.append(row)
    return rows
