"""Trusted verification limits and the non-shell command parser."""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass
from pathlib import Path

from .contracts import MAX_CHECKS, QualityError, VerificationSpec, VerifyRequest

ENV_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,127}\Z")
FORBIDDEN_ENV = frozenset(
    {
        "HOME",
        "PATH",
        "TMPDIR",
        "LANG",
        "LC_ALL",
        "PYTHONPATH",
        "PYTHONHOME",
        "PYTHONDONTWRITEBYTECODE",
        "PYTHONNOUSERSITE",
        "LD_PRELOAD",
        "LD_LIBRARY_PATH",
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_CONFIG",
        "GIT_CONFIG_GLOBAL",
        "GIT_CONFIG_SYSTEM",
        "GIT_CONFIG_NOSYSTEM",
    }
)
SENSITIVE_ENV = re.compile(
    r"(?:SECRET|TOKEN|PASSWORD|PRIVATE|CREDENTIAL|API[_-]?KEY|ACCESS[_-]?KEY)",
    re.IGNORECASE,
)
MAX_ENV_BYTES = 65_536
SHELL_OPERATORS = frozenset({";", "|", "||", "&", "&&", ">", ">>", "<", "<<"})
FORBIDDEN_COMMAND_CHARS = frozenset(";|<>`$\n\r")
ACTION_TOKEN = re.compile(
    r"(?:^|[^a-z0-9])(deploy|deployment|publish|release|migrate|migration)(?:$|[^a-z0-9])",
    re.IGNORECASE,
)
PRODUCTION_TARGET = re.compile(
    r"(?:^|[^a-z0-9])(prod|production)(?:$|[^a-z0-9])", re.IGNORECASE
)
MUTATING_INFRASTRUCTURE = {
    "terraform": frozenset({"apply", "destroy"}),
    "kubectl": frozenset({"apply", "delete", "patch", "replace", "scale", "rollout"}),
    "helm": frozenset({"install", "upgrade", "uninstall", "rollback"}),
    "pulumi": frozenset({"up", "destroy"}),
    "alembic": frozenset({"upgrade", "downgrade"}),
    "flyway": frozenset({"migrate", "clean"}),
    "liquibase": frozenset({"update", "dropall"}),
    "vercel": frozenset({"--prod", "--production"}),
}


@dataclass(frozen=True)
class QualityPolicy:
    """Local operator policy. Values are never read from an agent order or report."""

    version: str = "m6-policy/1"
    verifier_identity: str = "m6-quality/checker-v1"
    bubblewrap_binary: str = "/usr/bin/bwrap"
    max_concurrent: int = 2
    max_pending_requests: int = 128
    max_checks: int = MAX_CHECKS
    max_command_seconds: int = 120
    max_total_seconds: int = 300
    max_cpu_seconds: int = 300
    max_output_bytes: int = 262_144
    max_snapshot_bytes: int = 536_870_912
    max_snapshot_files: int = 20_000
    max_workspace_bytes: int = 1_073_741_824
    max_tmp_bytes: int = 134_217_728
    max_address_space_bytes: int = 2_147_483_648
    environment: tuple[tuple[str, str], ...] = ()
    secret_values: tuple[str, ...] = ()
    require_independent_review: bool = False

    def __post_init__(self) -> None:
        _validate_policy_identity(self)
        _validate_positive_limits(self)
        _validate_policy_bounds(self)
        _validate_policy_controls(self)
        _validate_policy_secrets(self)


def _validate_policy_identity(policy: QualityPolicy) -> None:
    if (
        not isinstance(policy.version, str)
        or not policy.version
        or len(policy.version.encode("utf-8")) > 64
        or not isinstance(policy.verifier_identity, str)
        or not policy.verifier_identity
        or len(policy.verifier_identity.encode("utf-8")) > 256
    ):
        raise ValueError("policy version and verifier identity must be bounded text")


def _validate_positive_limits(policy: QualityPolicy) -> None:
    names = (
        "max_concurrent",
        "max_pending_requests",
        "max_command_seconds",
        "max_total_seconds",
        "max_cpu_seconds",
        "max_checks",
        "max_output_bytes",
        "max_snapshot_bytes",
        "max_snapshot_files",
        "max_workspace_bytes",
        "max_tmp_bytes",
        "max_address_space_bytes",
    )
    for name in names:
        value = getattr(policy, name)
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValueError(f"{name} must be positive")


def _validate_policy_bounds(policy: QualityPolicy) -> None:
    if (
        policy.max_concurrent > 4
        or policy.max_pending_requests > 4096
        or policy.max_checks > MAX_CHECKS
        or policy.max_total_seconds < policy.max_command_seconds
    ):
        raise ValueError(
            "policy concurrency or total timeout exceeds its supported bound"
        )
    if policy.max_snapshot_files > 100_000 or policy.max_output_bytes > 4_194_304:
        raise ValueError("policy file or output cap exceeds its supported bound")


def _validate_policy_controls(policy: QualityPolicy) -> None:
    if not isinstance(
        policy.bubblewrap_binary, str
    ) or not policy.bubblewrap_binary.startswith("/"):
        raise ValueError("bubblewrap path must be absolute")
    if not isinstance(policy.environment, tuple) or not isinstance(
        policy.secret_values, tuple
    ):
        raise TypeError("environment and secret values must be immutable tuples")
    if not isinstance(policy.require_independent_review, bool):
        raise TypeError("review policy must be boolean")


def _validate_policy_secrets(policy: QualityPolicy) -> None:
    secrets: list[str] = []
    for secret in policy.secret_values:
        if (
            not isinstance(secret, str)
            or not secret
            or len(secret.encode("utf-8")) > 4096
            or any(ord(char) < 32 for char in secret)
        ):
            raise ValueError("secret values must be bounded, non-empty text")
        secrets.append(secret)
    if len(set(secrets)) != len(secrets):
        raise ValueError("secret values must be unique")
    _validate_environment(policy.environment, frozenset(secrets))


@dataclass(frozen=True)
class CheckSpec:
    id: str
    kind: str
    command: str
    argv: tuple[str, ...]
    cwd: str
    purpose: str
    expected: str = ""


def _validate_environment(
    entries: tuple[tuple[str, str], ...], secrets: frozenset[str]
) -> None:
    seen: set[str] = set()
    total_bytes = 0
    for pair in entries:
        if not isinstance(pair, tuple) or len(pair) != 2:
            raise ValueError("environment entries must be key/value tuples")
        key, value = pair
        if (
            not isinstance(key, str)
            or not ENV_NAME.fullmatch(key)
            or key in FORBIDDEN_ENV
            or key.startswith(("LD_", "GIT_", "PYTHON"))
        ):
            raise ValueError("environment contains a protected or invalid name")
        if (
            not isinstance(value, str)
            or len(value.encode("utf-8")) > 4096
            or any(ord(c) < 32 for c in value)
        ):
            raise ValueError("environment values must be bounded text")
        total_bytes += len(key.encode("utf-8")) + len(value.encode("utf-8"))
        if total_bytes > MAX_ENV_BYTES:
            raise ValueError("environment exceeds its aggregate byte cap")
        if SENSITIVE_ENV.search(key) and value and value not in secrets:
            raise ValueError(
                "sensitive environment values must be explicitly registered for redaction"
            )
        if key in seen:
            raise ValueError("environment keys must be unique")
        seen.add(key)


def compile_verification(
    order: VerifyRequest, snapshot_root: Path, policy: QualityPolicy
) -> tuple[CheckSpec, ...]:
    root = snapshot_root.resolve(strict=True)
    if not root.is_dir():
        raise QualityError("SNAPSHOT_INVALID", "snapshot root is not a directory")
    if len(order.verification) > policy.max_checks:
        raise QualityError(
            "ORDER_INVALID", "verification exceeds the supported check count"
        )
    if any(
        secret and secret in item.value
        for secret in policy.secret_values
        for item in order.verification
    ):
        raise QualityError(
            "CHECK_UNSUPPORTED", "verification command contains a configured secret"
        )
    return tuple(
        _compile_item(item, index, root)
        for index, item in enumerate(order.verification, start=1)
    )


def _compile_item(item: VerificationSpec, index: int, root: Path) -> CheckSpec:
    check_id = f"CHECK-{index:03d}"
    if item.kind == "manual":
        return CheckSpec(
            check_id, "manual", item.value, (), ".", item.purpose, item.expected
        )
    argv, cwd = _parse_command(item.value, root)
    return CheckSpec(check_id, "command", item.value, argv, cwd, item.purpose)


def _parse_command(command: str, root: Path) -> tuple[tuple[str, ...], str]:
    if any(char in FORBIDDEN_COMMAND_CHARS for char in command):
        raise QualityError("CHECK_UNSUPPORTED", "command contains shell syntax")
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError as error:
        raise QualityError(
            "CHECK_UNSUPPORTED", "command quoting is malformed"
        ) from error
    if not tokens:
        raise QualityError("CHECK_UNSUPPORTED", "command is empty")
    cwd = "."
    if tokens[0] == "cd":
        if len(tokens) < 4 or tokens[2] != "&&":
            raise QualityError(
                "CHECK_UNSUPPORTED", "only a leading cd <path> && <argv> is supported"
            )
        cwd = _contained_cwd(root, tokens[1])
        tokens = tokens[3:]
    if not tokens or any(token in SHELL_OPERATORS for token in tokens):
        raise QualityError(
            "CHECK_UNSUPPORTED", "command contains unsupported shell operators"
        )
    if any(
        not isinstance(token, str)
        or any(ord(char) < 32 or ord(char) == 127 for char in token)
        for token in tokens
    ):
        raise QualityError(
            "CHECK_UNSUPPORTED", "command argument contains control characters"
        )
    if (
        sum(len(token.encode("utf-8")) for token in tokens) > 65_536
        or len(tokens) > 256
    ):
        raise QualityError("CHECK_UNSUPPORTED", "command exceeds argument bounds")
    if _requires_operator_review(tokens):
        raise QualityError(
            "CHECK_PRODUCTION_ACTION",
            "verification requests a deployment or migration action",
        )
    _validate_executable(tokens[0], root, cwd)
    return tuple(tokens), cwd


def _requires_operator_review(tokens: list[str]) -> bool:
    normalized = [Path(token).name.lower() for token in tokens]
    action_tokens = [token for token in normalized if ACTION_TOKEN.search(token)]
    if any(
        re.search(
            r"(?:^|[^a-z0-9])(deploy|deployment|publish|release|migrate)(?:$|[^a-z0-9])",
            token,
        )
        for token in action_tokens
    ):
        return True
    if any(PRODUCTION_TARGET.search(token) for token in normalized) and action_tokens:
        return True
    executable = normalized[0]
    mutating = MUTATING_INFRASTRUCTURE.get(executable)
    if mutating and any(token in mutating for token in normalized[1:]):
        return True
    return any(
        token == "migration" or token.endswith(":migration") for token in normalized
    ) and not any(
        token in {"check", "test", "tests", "verify", "validate", "lint"}
        for token in normalized
    )


def _contained_cwd(root: Path, raw: str) -> str:
    relative = Path(raw)
    if relative.is_absolute():
        raise QualityError(
            "CHECK_UNSUPPORTED", "working directory must be snapshot-relative"
        )
    try:
        resolved = (root / relative).resolve(strict=True)
        child = resolved.relative_to(root)
    except (OSError, ValueError) as error:
        raise QualityError(
            "CHECK_UNSUPPORTED", "working directory is missing or outside the snapshot"
        ) from error
    if not resolved.is_dir():
        raise QualityError("CHECK_UNSUPPORTED", "working directory is not a directory")
    return child.as_posix() or "."


def _validate_executable(executable: str, root: Path, cwd: str) -> None:
    path = Path(executable)
    if path.is_absolute():
        if path.parts[:2] not in (("/", "usr"), ("/", "bin")):
            raise QualityError(
                "CHECK_UNSUPPORTED",
                "absolute executable is outside the sandbox runtime",
            )
        return
    if "/" not in executable:
        return
    relative_cwd = Path() if cwd == "." else Path(cwd)
    try:
        resolved = (root / relative_cwd / path).resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError) as error:
        raise QualityError(
            "CHECK_UNSUPPORTED",
            "relative executable is missing or outside the snapshot",
        ) from error
    if not resolved.is_file():
        raise QualityError("CHECK_UNSUPPORTED", "relative executable is not a file")
