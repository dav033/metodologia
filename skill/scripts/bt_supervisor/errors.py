"""Errors of the supervisor. Every one carries a stable `code` so the DBOS layer can branch without parsing text."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .model import Observation


class SupervisorError(RuntimeError):
    code = "SUPERVISOR_ERROR"


class BackendUnavailable(SupervisorError):
    """The requested backend cannot run here (no user systemd manager, no cgroup v2, not Linux)."""
    code = "BACKEND_UNAVAILABLE"


class BackendMismatch(SupervisorError):
    """The attempt was launched by the other backend; open the state directory with that backend."""
    code = "BACKEND_MISMATCH"


class ManagerUnavailable(SupervisorError):
    """systemctl/systemd-run did not answer, or failed in a way that says nothing about the unit."""
    code = "MANAGER_UNAVAILABLE"


class LaunchFailed(SupervisorError):
    """Nothing is running for the attempt (systemd-run refused, cwd missing, reaper never came up)."""
    code = "LAUNCH_FAILED"


class LaunchConflict(SupervisorError):
    """The unit name is held by something this supervisor did not start (another state dir, or a reused name)."""
    code = "LAUNCH_CONFLICT"


class AttemptBusy(SupervisorError):
    """Another caller holds the attempt's lock (a launch/terminate/release in flight) for too long."""
    code = "ATTEMPT_BUSY"


class UnknownAttempt(SupervisorError):
    """No record and no process for the key (freeze/thaw need something to act on)."""
    code = "UNKNOWN_ATTEMPT"


class AttemptAlive(SupervisorError):
    """`release` refuses while any process of the attempt is alive."""
    code = "ATTEMPT_ALIVE"


class TerminationUncertain(SupervisorError):
    """After SIGTERM, the grace period and SIGKILL, something of the attempt may still be alive (a process stuck in
    uninterruptible sleep, an unreadable process table, a manager that did not answer). The caller must keep the
    worktree marked busy and retry later; `observation` is the last view taken."""
    code = "TERMINATION_UNCERTAIN"

    def __init__(self, message: str, observation: Observation | None = None):
        super().__init__(message)
        self.observation = observation
