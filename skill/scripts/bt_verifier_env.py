"""Environment variables for the independent checks (M6), read from an owner-kept dotenv file.

The sandbox starts with a clean environment, so a check that needs a database URL or an API key gets it only from
here. The file lives outside the repositories (the config key `verifier.env_file`); its values never reach the
bitácora, the plan or argv, and the ones that look secret are registered so every output redacts them.
"""
from __future__ import annotations

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
