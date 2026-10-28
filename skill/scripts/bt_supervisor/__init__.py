"""Linux process runtime for agent attempts (REQ-030 M3): systemd user units on cgroup v2, with a process-group
backend for environments without a user systemd manager. Needs the uv-managed environment (pydantic, psutil); the
in-attempt helper `tee.py` is stdlib-only and runs under the system interpreter. See README.md."""
from .api import Supervisor, make_supervisor
from .errors import (
    AttemptAlive,
    AttemptBusy,
    BackendMismatch,
    BackendUnavailable,
    LaunchConflict,
    LaunchFailed,
    ManagerUnavailable,
    SupervisorError,
    TerminationUncertain,
    UnknownAttempt,
)
from .model import LaunchSpec, Limits, Observation, ProcessIdentity

__all__ = ["AttemptAlive", "AttemptBusy", "BackendMismatch", "BackendUnavailable", "LaunchConflict", "LaunchFailed",
           "LaunchSpec", "Limits", "ManagerUnavailable", "Observation", "ProcessIdentity", "Supervisor",
           "SupervisorError", "TerminationUncertain", "UnknownAttempt", "make_supervisor"]
