"""Trusted operator-owned probes for external M6 verification prerequisites."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Mapping

from bt_scheduler_quality.authority import VerificationAuthority

_ENV_NAME = re.compile(r"[A-Z][A-Z0-9_]{1,63}\Z")
_ALLOWED_ENVIRONMENTS = {"staging", "production"}


def _declared_names(path: Path) -> frozenset[str]:
    """Read only assignment names from secrets.env; values are discarded immediately."""
    try:
        with path.open("r", encoding="utf-8") as source:
            names = set()
            for line in source:
                assignment = line.strip()
                if assignment.startswith("export "):
                    assignment = assignment[7:].lstrip()
                name, separator, _value = assignment.partition("=")
                if separator and _ENV_NAME.fullmatch(name):
                    names.add(name)
            return frozenset(names)
    except (OSError, UnicodeError):
        return frozenset()


def _policy_allows(path: Path, environment: str) -> bool:
    if environment == "sandbox":
        return True
    if environment not in _ALLOWED_ENVIRONMENTS:
        return False
    try:
        with path.open("r", encoding="utf-8") as source:
            policy = json.load(source)
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False
    if not isinstance(policy, Mapping) or set(policy) != {"allow"} or not isinstance(policy["allow"], list):
        return False
    return any(isinstance(item, Mapping) and item.get("environment") == environment
               for item in policy["allow"])


def owner_verification_authority(rdir: Path | str, project: str, *,
                                 environ: Mapping[str, str] | None = None,
                                 secrets_file: Path | str | None = None) -> VerificationAuthority:
    """Build M6 callbacks from the owner process and its external verification policy."""
    run_dir = Path(rdir).resolve()
    bitacora_root = run_dir.parent.parent.parent
    policy_file = bitacora_root / project / "verification-policy.json"
    secret_path = Path(secrets_file) if secrets_file is not None else Path.home() / ".config/flow/secrets.env"
    process_environment = os.environ if environ is None else environ

    def resource_available(name: str) -> bool:
        if not isinstance(name, str) or not _ENV_NAME.fullmatch(name):
            return False
        return name in process_environment or name in _declared_names(secret_path)

    def authorize_environment(environment: str, _authorization_needed: str | None) -> bool:
        return _policy_allows(policy_file, environment)

    return VerificationAuthority(resource_available=resource_available,
                                 authorize_environment=authorize_environment)


__all__ = ["owner_verification_authority"]
