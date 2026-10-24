"""Trusted operator-owned probes for external M6 verification prerequisites."""
from __future__ import annotations

import json
import os
import re
import stat
from pathlib import Path
from typing import Mapping

from bt_scheduler_quality.authority import VerificationAuthority

_ENV_NAME = re.compile(r"[A-Z][A-Z0-9_]{1,63}\Z")
_ALLOWED_ENVIRONMENTS = {"staging", "production"}
_MAX_AUTHORITY_BYTES = 64 * 1024


def _open_regular(path: Path) -> int:
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    descriptor = os.open(path, flags)
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > _MAX_AUTHORITY_BYTES:
            raise OSError("authority file is not a bounded regular file")
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _declared_names(path: Path) -> frozenset[str]:
    """Read only assignment names from secrets.env; values are discarded immediately."""
    try:
        with os.fdopen(_open_regular(path), "rb") as source:
            names = set()
            total = 0
            while line := source.readline(_MAX_AUTHORITY_BYTES + 1 - total):
                total += len(line)
                if total > _MAX_AUTHORITY_BYTES:
                    return frozenset()
                try:
                    assignment = line.decode("utf-8").strip()
                except UnicodeError:
                    continue
                if assignment.startswith("export "):
                    assignment = assignment[7:].lstrip()
                name, separator, value = assignment.partition("=")
                value = value.strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                    value = value[1:-1].strip()
                if separator and value and _ENV_NAME.fullmatch(name):
                    names.add(name)
            return frozenset(names)
    except (OSError, UnicodeError, ValueError, RecursionError):
        return frozenset()


def _policy_allows(path: Path, environment: str, authorization_needed: str | None, req_id: str) -> bool | str:
    if environment == "sandbox":
        return True
    if environment not in _ALLOWED_ENVIRONMENTS:
        return False
    try:
        with os.fdopen(_open_regular(path), "rb") as source:
            raw = source.read(_MAX_AUTHORITY_BYTES + 1)
        if len(raw) > _MAX_AUTHORITY_BYTES:
            return False
        policy = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, ValueError, RecursionError):
        return False
    if not isinstance(policy, Mapping) or set(policy) != {"allow"} or not isinstance(policy["allow"], list):
        return False
    if not isinstance(authorization_needed, str) or not authorization_needed.strip() or not req_id:
        return False
    for item in policy["allow"]:
        if not isinstance(item, Mapping) or item.get("environment") != environment:
            continue
        requirements = item.get("requirements")
        if requirements is not None and (not isinstance(requirements, list) or req_id not in requirements):
            continue
        if "authorization" not in item:
            return "POLICY_ENTRY_MISSING_AUTHORIZATION"
        if item.get("authorization") != authorization_needed.strip():
            continue
        return True
    return False


def owner_verification_authority(rdir: Path | str, project: str, *,
                                 environ: Mapping[str, str] | None = None,
                                 secrets_file: Path | str | None = None) -> VerificationAuthority:
    """Build M6 callbacks from the owner process and its external verification policy."""
    run_dir = Path(rdir).resolve()
    bitacora_root = run_dir.parent.parent.parent
    policy_file = bitacora_root / project / "verification-policy.json"
    secret_path = Path(secrets_file) if secrets_file is not None else Path.home() / ".config/flow/secrets.env"
    process_environment = os.environ if environ is None else environ
    req_match = re.match(r"(REQ-[0-9]+)(?:-|$)", run_dir.name)
    req_id = req_match.group(1) if req_match else ""

    def resource_available(name: str) -> bool:
        if not isinstance(name, str) or not _ENV_NAME.fullmatch(name):
            return False
        return bool(process_environment.get(name)) or name in _declared_names(secret_path)

    def authorize_environment(environment: str, authorization_needed: str | None) -> bool:
        return _policy_allows(policy_file, environment, authorization_needed, req_id)

    return VerificationAuthority(resource_available=resource_available,
                                 authorize_environment=authorize_environment)


__all__ = ["owner_verification_authority"]
