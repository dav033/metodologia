"""The supervisor contract the DBOS execution plane depends on, and the factory that picks a backend.

Guarantees every backend gives (details and limits in README.md):

- `launch` is idempotent per attempt_key: while a record exists (running, or exited and not released) it returns the
  existing identity and never starts a second process — also after the orchestrator crashed half-way through it.
- `observe` never signals anything.
- `terminate` returns only when no process of the attempt is alive; otherwise it raises `TerminationUncertain`.
- `release` refuses while anything of the attempt is alive; after it, the key is free for a new launch.
- Exit status and output survive the orchestrator: both are written to disk by a process that is not the
  orchestrator (systemd's ExecStopPost, or the pgroup reaper).
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal, Protocol, runtime_checkable

from .errors import BackendUnavailable
from .model import LaunchSpec, Observation, ProcessIdentity


@runtime_checkable
class Supervisor(Protocol):
    backend: str

    def launch(self, spec: LaunchSpec) -> ProcessIdentity:
        """Start the attempt, or return the identity of the one already recorded under `spec.attempt_key`."""
        ...

    def observe(self, attempt_key: str) -> Observation:
        """Pure observation of the attempt (never kills)."""
        ...

    def terminate(self, attempt_key: str, *, grace: float | None = None) -> Observation:
        """SIGTERM the whole tree, wait `grace` (default: the spec's kill_grace_seconds), SIGKILL what is left.
        Raises TerminationUncertain when something may still be alive."""
        ...

    def freeze(self, attempt_key: str) -> None:
        """Suspend every process of the attempt (idempotent; no-op once it has exited)."""
        ...

    def thaw(self, attempt_key: str) -> None:
        """Resume a frozen attempt (idempotent; no-op once it has exited)."""
        ...

    def release(self, attempt_key: str) -> None:
        """Forget an exited attempt and its unit state (logs in log_dir are kept). Raises AttemptAlive."""
        ...

    def list_attempts(self, prefix: str = "") -> list[ProcessIdentity]:
        """Every attempt this supervisor started that still exists (running, or exited and not released)."""
        ...


def make_supervisor(state_dir: Path, backend: Literal["auto", "systemd", "pgroup"] = "auto", *,
                    unit_prefix: str = "bt-att-", helper_python: str | None = None) -> Supervisor:
    """Open the supervisor of `state_dir`. "auto" = systemd when a user manager on cgroup v2 answers, else pgroup.
    The same state dir must always be opened with the same backend (a mismatch raises BackendMismatch per attempt)."""
    from . import systemd
    if backend not in ("auto", "systemd", "pgroup"):
        raise ValueError(f"unknown backend {backend!r}")
    if backend in ("auto", "systemd"):
        usable, why = systemd.available()
        if usable:
            return systemd.SystemdSupervisor(Path(state_dir), unit_prefix=unit_prefix, helper_python=helper_python)
        if backend == "systemd":
            raise BackendUnavailable(why)
    from .pgroup import PgroupSupervisor
    return PgroupSupervisor(Path(state_dir), helper_python=helper_python)
