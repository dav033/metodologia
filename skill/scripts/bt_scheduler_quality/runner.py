"""Validated admission and concurrency control for sandboxed M6 checks."""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Literal

from .contracts import QualityError
from .policy import CheckSpec, QualityPolicy, _parse_command
from .runner_execution import SandboxExecution
from .runner_types import CommandOutcome


class SandboxRunner:
    """Runs only policy-compiled commands in a fresh OS namespace."""

    def __init__(self, policy: QualityPolicy):
        self.policy = policy
        self._slots = threading.BoundedSemaphore(policy.max_concurrent)
        self._execution = SandboxExecution(policy, self._outcome, self._redact)

    def run(
        self,
        check: CheckSpec,
        snapshot_root: Path,
        *,
        timeout_seconds: int | None = None,
    ) -> CommandOutcome:
        started = time.monotonic()
        requested_timeout = (
            self.policy.max_command_seconds
            if timeout_seconds is None
            else timeout_seconds
        )
        if (
            not isinstance(requested_timeout, int)
            or isinstance(requested_timeout, bool)
            or requested_timeout <= 0
        ):
            return self._outcome(
                "unknown", None, started, b"", b"", "CHECK_UNSUPPORTED", False
            )
        timeout = min(requested_timeout, self.policy.max_command_seconds)
        if not self._slots.acquire(timeout=min(timeout, self.policy.max_total_seconds)):
            return self._outcome(
                "unknown", None, started, b"", b"", "RUNNER_BUSY", False
            )
        try:
            try:
                root = snapshot_root.resolve(strict=True)
                if not root.is_dir():
                    raise QualityError(
                        "SNAPSHOT_INVALID", "snapshot root is not a directory"
                    )
                if check.kind != "command":
                    raise QualityError(
                        "CHECK_MANUAL", "manual verification requires an operator"
                    )
                parsed_argv, parsed_cwd = _parse_command(check.command, root)
                if parsed_argv != check.argv or parsed_cwd != check.cwd:
                    raise QualityError(
                        "CHECK_UNSUPPORTED",
                        "command was not compiled by the active policy",
                    )
                if any(
                    secret in check.command
                    or any(secret in value for value in check.argv)
                    for secret in self.policy.secret_values
                ):
                    raise QualityError(
                        "CHECK_UNSUPPORTED", "command contains a configured secret"
                    )
            except (OSError, ValueError, TypeError) as error:
                code = (
                    error.code
                    if isinstance(error, QualityError)
                    else "SNAPSHOT_INVALID"
                )
                return self._outcome("unknown", None, started, b"", b"", code, False)

            return self._execute(check, root, timeout, started)
        finally:
            self._slots.release()

    def _execute(
        self, check: CheckSpec, root: Path, timeout: int, started: float
    ) -> CommandOutcome:
        return self._execution.execute(check, root, timeout, started)

    def _redact(self, value: bytes) -> bytes:
        for secret in sorted(self.policy.secret_values, key=len, reverse=True):
            value = value.replace(secret.encode("utf-8"), b"[REDACTED]")
        return value

    def _outcome(
        self,
        status: Literal["pass", "fail", "unknown"],
        exit_code: int | None,
        started: float,
        stdout: bytes,
        stderr: bytes,
        issue_code: str | None,
        sandboxed: bool,
        output_truncated: bool = False,
        namespaces: tuple[tuple[str, int], ...] = (),
    ) -> CommandOutcome:
        return CommandOutcome(
            status,
            exit_code,
            int((time.monotonic() - started) * 1000),
            stdout,
            stderr,
            issue_code,
            sandboxed,
            output_truncated,
            namespaces,
        )
