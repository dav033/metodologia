"""Environment variables for the independent checks (M6), read from an owner-kept dotenv file.

The sandbox starts with a clean environment, so a check that needs a database URL or an API key gets it only from
here. The file lives outside the repositories (the config key `verifier.env_file`); its values never reach the
bitácora, the plan or argv, and the ones that look secret are registered so every output redacts them.
"""
from __future__ import annotations

import fnmatch
import os
import re
from pathlib import Path

from bt_scheduler_quality.policy import ENV_NAME, FORBIDDEN_ENV, MAX_ENV_BYTES, SENSITIVE_ENV

MAX_VALUE_BYTES = 4096
_LINE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$")
_CREDENTIAL_URL = re.compile(r"://[^/\s:@]+:[^/\s@]+@")


def _value(raw: str) -> str:
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        return raw[1:-1]
    return raw.split(" #", 1)[0].strip()


def path_for(template: object, project: str) -> str:
    """The env file of a project: `{project}` in the configured path is replaced, so one setting keeps each project's
    keys out of the checks of the others. A project without its own file simply gets none."""
    if not isinstance(template, str) or not template.strip():
        return ""
    return template.replace("{project}", re.sub(r"[^A-Za-z0-9_.-]", "", project or ""))


def load(path: str | Path | None) -> tuple[tuple[tuple[str, str], ...], tuple[str, ...]]:
    """(environment, secret values) from the dotenv file, or empty ones when it is unset, missing or unreadable.
    A name the sandbox protects, a value that is too long or has control characters is skipped, never an error."""
    if not path:
        return (), ()
    try:
        lines = Path(path).expanduser().read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return (), ()
    environment: dict[str, str] = {}
    total = 0
    for line in lines:
        match = None if line.lstrip().startswith("#") else _LINE.match(line)
        if not match:
            continue
        key, value = match.group(1), _value(match.group(2))
        if (not ENV_NAME.fullmatch(key) or key in FORBIDDEN_ENV or key.startswith(("LD_", "GIT_", "PYTHON"))
                or not value or len(value.encode()) > MAX_VALUE_BYTES or any(ord(c) < 32 for c in value)):
            continue
        total += len(key.encode()) + len(value.encode())
        if total > MAX_ENV_BYTES // 2:
            break
        environment[key] = value
    secrets = tuple(dict.fromkeys(value for key, value in environment.items()
                                  if SENSITIVE_ENV.search(key) or _CREDENTIAL_URL.search(value)))
    return tuple(environment.items()), secrets


def declared(rdir: str | Path | None) -> set[str]:
    """Variable names the checks of the run's latest frozen revision declare in `requires` (a `service:` probe is not a
    variable); empty when there is no frozen revision."""
    if not rdir:
        return set()
    from bt_planner import revisions as rev
    try:
        last = rev.latest(Path(rdir))
        plan = rev.load_revision(Path(rdir), last["revision"]) if last else {}
    except Exception:  # noqa: BLE001 - an unreadable store adds nothing; the frozen-plan gates report it
        return set()
    return {name for task in plan.get("tasks") or [] if isinstance(task, dict)
            for check in task.get("verification") or [] if isinstance(check, dict)
            for name in check.get("requires") or []
            if isinstance(name, str) and ENV_NAME.fullmatch(name)}


def _patterns(value: object) -> tuple[str, ...]:
    """`verifier.inherit_env`: True or "*" for everything, or a list of variable-name globs (PICTURES_*, DATABASE_URL)."""
    if value is True:
        return ("*",)
    if isinstance(value, str):
        value = [value]
    return tuple(p for p in value if isinstance(p, str) and p.strip()) if isinstance(value, list) else ()


def inherited(patterns: tuple[str, ...], sources: list[dict[str, str]], skip: set[str]) -> dict[str, str]:
    """The variables a check inherits instead of starting empty: those of `sources` (the owner's environment and its secret
    files) whose name matches a pattern, with the same refusals as the env file (sandbox-protected names, LD_/GIT_/PYTHON*,
    control characters, size). Names in `skip` (already set by the project's env file) keep their value."""
    found: dict[str, str] = {}
    total = 0
    for source in sources:
        for key, value in source.items():
            if (key in skip or key in found or not any(fnmatch.fnmatchcase(key, p) for p in patterns)
                    or not ENV_NAME.fullmatch(key) or key in FORBIDDEN_ENV or key.startswith(("LD_", "GIT_", "PYTHON"))
                    or not value or len(value.encode()) > MAX_VALUE_BYTES or any(ord(c) < 32 for c in value)):
                continue
            total += len(key.encode()) + len(value.encode())
            if total > MAX_ENV_BYTES // 4:
                return found
            found[key] = value
    return found


def for_run(project: str, rdir: str | Path | None = None) -> tuple[tuple[tuple[str, str], ...], tuple[str, ...]]:
    """What the checks of a run receive: the project's `verifier.env_file`, plus each variable a check of the frozen plan
    declares in `requires` that is missing there, taken from the owner's secret files (`verifier.secret_files`). Only
    declared names are copied, so a check never sees the rest of those files; nothing is written anywhere."""
    import bt_config
    environment, _ = load(path_for(bt_config.get("verifier.env_file", ""), project))
    merged = dict(environment)
    wanted = declared(rdir) - set(merged)
    for source in bt_config.get("verifier.secret_files", []) or []:
        if not wanted:
            break
        found = {key: value for key, value in load(path_for(source, project))[0] if key in wanted}
        merged.update(found)
        wanted -= set(found)
    secrets = tuple(dict.fromkeys(value for key, value in merged.items()
                                  if SENSITIVE_ENV.search(key) or _CREDENTIAL_URL.search(value)))
    return tuple(merged.items()), secrets


def ambient_for_run(project: str, explicit: set[str]) -> tuple[tuple[tuple[str, str], ...], tuple[str, ...]]:
    """(variables, secret-looking values) the checks INHERIT under `verifier.inherit_env`: the owner's environment and every
    variable of his secret files. They are handed to the sandbox but kept out of the evidence fingerprint (see
    `QualityPolicy.ambient_environment`); names the project's env file or the plan's `requires` already set keep that value."""
    import bt_config
    patterns = _patterns(bt_config.get("verifier.inherit_env", []))
    if not patterns:
        return (), ()
    files = [dict(load(path_for(source, project))[0]) for source in bt_config.get("verifier.secret_files", []) or []]
    found = inherited(patterns, [dict(os.environ), *files], set(explicit))
    secrets = tuple(dict.fromkeys(value for key, value in found.items() if SENSITIVE_ENV.search(key) or _CREDENTIAL_URL.search(value)))
    return tuple(found.items()), secrets
