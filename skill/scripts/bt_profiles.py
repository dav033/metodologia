"""Execution profiles (one per account identity) and the work gate.

A profile is a provider (claude / codex) plus the environment that selects its account. Profiles hold
no credentials: authentication lives in each provider's own config directory. Only `work_only` profiles are gated:
they may run solely for projects whose project.json says `"work": true` (missing means false). Everything else may
run anywhere. The gate is a launcher guarantee, not an OS sandbox: invoking the provider binary directly bypasses it.

<root>/.state/profiles.json may add or override profiles: {"id": {"provider": ..., "env": {...}, ...}}.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
from pathlib import Path

import sys

import bt_workspace as ws
from bt_core import ROOT, SCRIPT, STATE

HOME = Path.home()
LAUNCHABLE = ("claude", "codex", "antigravity")  # providers the launcher/supervisor can drive
# Variables that select a provider's account. A session of one account must never leak them into a session of another.
DEFAULT_BIN = {"claude": "claude", "codex": "codex", "antigravity": "agy"}  # provider CLI executables
ACCOUNT_VARS = {"claude": ("CLAUDE_CONFIG_DIR",), "codex": ("CODEX_HOME",), "antigravity": ()}  # agy: one account, token in ~/.gemini

# Generic, machine-independent: each provider's default account. Named accounts (a second Claude config dir, a team
# Codex login, which one is work-only) are machine facts: `bitacora.py profiles add`, stored in .state/profiles.json.
DEFAULTS: dict[str, dict] = {
    "claude": {"provider": "claude", "bin": "claude", "env": {}, "work_only": False},
    "codex": {"provider": "codex", "bin": "codex", "env": {}, "work_only": False},
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
    if provider not in LAUNCHABLE:
        raise ProfileError(f"Unknown provider '{provider}' ({', '.join(LAUNCHABLE)})")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", pid or "") or pid in (".", ".."):
        raise ProfileError(f"Invalid profile id '{pid}': letters, digits, dot, dash and underscore only")
    for key in (env or {}):
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            raise ProfileError(f"Invalid environment variable name '{key}'")
        if key in _foreign_selectors(provider):
            raise ProfileError(f"A {provider} profile cannot set {key}: it selects another provider's account")
    path = STATE / "profiles.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    data[pid] = {"provider": provider, "env": env or {}, "work_only": work_only,
                 "bin": binary or DEFAULT_BIN[provider]}
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)
    return path


def _foreign_selectors(provider: str) -> set:
    return {k for other, keys in ACCOUNT_VARS.items() if other != provider for k in keys}


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


def ambient(provider: str, environ: dict | None = None) -> str | None:
    """The profile the current environment selects for `provider` (its account variables match), preferring a named
    profile over the generic one. None when the environment points at an account no profile describes."""
    environ = os.environ if environ is None else environ
    current = {k: os.path.expanduser(environ[k]).rstrip("/") for k in ACCOUNT_VARS.get(provider, ()) if environ.get(k)}
    profiles = load()
    for pid in sorted(profiles, key=lambda p: (p in DEFAULTS, p)):
        spec = profiles[pid]
        if spec.get("provider") != provider:
            continue
        env = {k: os.path.expanduser(str(v)).rstrip("/") for k, v in (spec.get("env") or {}).items()
               if k in ACCOUNT_VARS.get(provider, ())}
        if env == current:
            return pid
    return None


def ambient_provider(environ: dict | None = None) -> str | None:
    """The provider of the agent session this process runs inside, when it can be told (used to send an audit to
    another provider than the builder's)."""
    environ = os.environ if environ is None else environ
    if environ.get("CLAUDECODE") or environ.get("CLAUDE_CODE_ENTRYPOINT"):
        return "claude"
    if environ.get("ANTIGRAVITY_AGENT") or environ.get("ANTIGRAVITY_CONVERSATION_ID"):
        return "antigravity"
    if any(k.startswith("CODEX_") and k != "CODEX_HOME" for k in environ):
        return "codex"
    return None


def session_env(pid: str | None, provider: str, environ: dict | None = None, project: str | None = None
                ) -> dict[str, str]:
    """The full environment of an agent session. With a profile: the inherited account selectors of EVERY provider
    are dropped and only the profile's own applied, so a session started from inside another account runs with the
    account it asked for and cannot hand an inherited one down to whatever it launches next. Without a profile the
    environment is inherited (callers gate the ambient account of their provider with authorize_ambient), minus any
    selector that belongs to a work-only profile when `project` is not a work project."""
    env = {k: v for k, v in (os.environ if environ is None else environ).items()
           if not k.startswith("ANTIGRAVITY_")}  # session-scoped state of a parent agy session, never inherited
    if pid:
        for keys in ACCOUNT_VARS.values():
            for key in keys:
                env.pop(key, None)
        foreign = _foreign_selectors(provider)  # also for profiles saved before `add` refused them
        env.update({k: v for k, v in env_of(pid).items() if k not in foreign})
        return env
    if project is not None and not is_work_project(project):
        for other in ACCOUNT_VARS:
            found = ambient(other, env)
            if found and load().get(found, {}).get("work_only"):
                for key in ACCOUNT_VARS[other]:
                    env.pop(key, None)
    return env


def authorize_ambient(provider: str, project: str, cwd: str | Path | None = None) -> None:
    """No profile was named: the inherited account runs. If that account is a work-only profile, it is gated like one
    (project and, when given, the working folder); an account no profile describes is allowed (a plain
    single-account machine)."""
    pid = ambient(provider)
    if pid:
        authorize(pid, project)
        if cwd is not None:
            ok, why = gate_cwd(pid, cwd)
            if not ok:
                raise ProfileError(why + " Nothing was sent.")


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


def gate_cwd(pid: str, cwd: str | Path) -> tuple[bool, str]:
    """May profile `pid` run in `cwd`? Work-only profiles need the folder to belong to a project marked work."""
    spec = get(pid)
    if not spec.get("work_only"):
        return True, ""
    project = ws.project_for_path(ROOT, cwd)
    if project and is_work_project(project):
        return True, ""
    where = f"project '{project}'" if project else "no registered project"
    return False, (f"Profile '{pid}' only runs inside work projects, and {cwd} belongs to {where}. "
                   f"Mark a project with: bitacora.py --project <name> work true")


def wrapper_text(pid: str, binary: str, windows: bool, relay: bool = False) -> str:
    """Launcher that checks the gate for the current folder, selects the account and execs the provider CLI."""
    env = env_of(pid)
    gate = f'"{sys.executable}" "{SCRIPT}" --cwd'
    if windows:
        bad = [k for k, v in env.items() if re.search(r'["%\r\n&|<>^]', v)]
        if bad:
            raise ProfileError(f"Profile '{pid}': the value of {', '.join(bad)} cannot be written safely to a .cmd file")
        lines = ["@echo off", f"{gate} \"%CD%\" profiles gate {pid} || exit /b 1"]
        lines += [f'set "{k}={v}"' for k, v in env.items()]
        lines.append(f'"{binary}" %*')
        return "\r\n".join(lines) + "\r\n"
    lines = ["#!/usr/bin/env bash", f"# generated by metodologia: bitacora.py profiles wrapper {pid}",
             f'{gate} "$PWD" profiles gate {pid} || exit 1']
    lines += [f"export {k}={shlex.quote(v)}" for k, v in env.items()]
    if relay:  # the quota relay's parent launcher runs the agent as a child and can start its successor in place
        runner = Path(SCRIPT).with_name("relay_run.py")
        lines.append(f'exec {shlex.quote(sys.executable)} {shlex.quote(str(runner))} {shlex.quote(pid)} -- '
                     f'{shlex.quote(binary)} "$@"')
    else:
        lines.append(f'exec "{binary}" "$@"')
    return "\n".join(lines) + "\n"


def write_wrapper(pid: str, directory: Path, relay: bool = False) -> Path:
    """Write <directory>/<pid>[.cmd]; a hand-made file or a name that would shadow the provider CLI is refused."""
    spec = get(pid)
    configured_binary = str(spec.get("bin", ""))
    resolved_binary = shutil.which(configured_binary)
    if not resolved_binary:
        raise ProfileError(f"'{spec.get('bin')}' is not on PATH; install the provider CLI first")
    # Keep PATH-based commands dynamic. In particular, fnm multishell paths expire when their shell exits.
    binary = configured_binary if os.path.basename(configured_binary) == configured_binary else resolved_binary
    windows = os.name == "nt"
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", pid):
        raise ProfileError(f"Profile id '{pid}' cannot be used as a file name")
    path = Path(directory) / (pid + (".cmd" if windows else ""))
    if path.resolve() == Path(resolved_binary).resolve() or path.stem == Path(resolved_binary).stem:
        raise ProfileError(f"A wrapper named '{path.name}' would shadow the provider CLI; use another profile id")
    marker = "generated by metodologia" if not windows else f"profiles gate {pid}"
    if path.exists() and marker not in path.read_text(encoding="utf-8", errors="replace"):
        raise ProfileError(f"{path} exists and was not generated by metodologia; preserved")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(wrapper_text(pid, binary, windows, relay and not windows), encoding="utf-8", newline="")
    if not windows:
        path.chmod(0o755)
    return path


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
    if provider == "antigravity":  # no login-status command: the OAuth token file is the signed-in marker
        token = HOME / ".gemini" / "antigravity-cli" / "antigravity-oauth-token"
        return "token present (usage: agy --print=/usage)" if token.exists() else "NOT signed in: run `agy`"
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
