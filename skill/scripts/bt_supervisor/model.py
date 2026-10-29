"""Value objects of the supervisor interface (pydantic v2, frozen, closed to unknown fields).

The DBOS execution plane stores these in workflow step outputs, so they must round-trip through JSON
(`model_dump(mode="json")` / `model_validate`) without loss. Times are floats: `started_at`/`ended_at` are wall-clock
epoch seconds; `main_start_time` is the kernel start time in seconds since boot (the `/proc/<pid>/stat` starttime
field divided by CLK_TCK), which together with `boot_id` names one process incarnation exactly — a pid alone does not.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MIB = 1024 * 1024
ATTEMPT_KEY_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,100}$")
ENV_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
MARKER_ENV = "BT_ATTEMPT_KEY"           # set on every process of an attempt; reserved, callers may not pass it
SUPERVISOR_ENV = "BT_SUPERVISOR_ID"     # set on the unit and on the agent: recognise our own units and processes
# Variables the service manager sets for each unit. A caller that copies its own environment (an engine that itself
# runs as a systemd service) would otherwise hand the agent the ENGINE's INVOCATION_ID, and the supervisor's identity
# check would then see its own unit as foreign (REQ-030, pictures REQ-021 att a1, 2026-10-28).
MANAGER_ENV = frozenset({
    "INVOCATION_ID", "JOURNAL_STREAM", "SYSTEMD_EXEC_PID", "MANAGERPID", "MANAGERPIDFDID", "NOTIFY_SOCKET",
    "LISTEN_PID", "LISTEN_FDS", "LISTEN_FDNAMES", "WATCHDOG_PID", "WATCHDOG_USEC", "MEMORY_PRESSURE_WATCH",
    "MEMORY_PRESSURE_WRITE", "TRIGGER_UNIT", "TRIGGER_PATH", "TRIGGER_TIMER_REALTIME_USEC",
    "TRIGGER_TIMER_MONOTONIC_USEC", "RUNTIME_DIRECTORY", "STATE_DIRECTORY", "CACHE_DIRECTORY", "LOGS_DIRECTORY",
    "CONFIGURATION_DIRECTORY", "CREDENTIALS_DIRECTORY", "EXIT_CODE", "EXIT_STATUS", "SERVICE_RESULT",
})

Backend = Literal["systemd", "pgroup"]
State = Literal["running", "exited", "absent", "unknown"]


def validate_attempt_key(value: str) -> str:
    """Keys name directories and units, so they are restricted to a path- and unit-safe alphabet."""
    if not isinstance(value, str) or not ATTEMPT_KEY_PATTERN.match(value) or value in (".", ".."):
        raise ValueError("attempt_key must match [A-Za-z0-9._-]{1,100} and not be '.' or '..'")
    return value


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Limits(_Frozen):
    """Resource ceilings for one attempt. None = unlimited. The pgroup backend enforces only `runtime_max_seconds`
    (see README §Non-guarantees); the systemd backend maps each to the unit property of the same meaning."""

    memory_max_bytes: int | None = Field(default=None, gt=0)   # MemoryMax= (+ MemorySwapMax=0: RAM is the limit)
    tasks_max: int | None = Field(default=None, gt=0)          # TasksMax= (threads count as tasks)
    cpu_quota_percent: int | None = Field(default=None, gt=0)  # CPUQuota=; 200 = two full CPUs
    runtime_max_seconds: int | None = Field(default=None, gt=0)  # RuntimeMaxSec= -> result "timeout"


class LaunchSpec(_Frozen):
    """Everything needed to start one attempt. `env` is the COMPLETE environment of the agent (like
    `subprocess.Popen(env=...)`), plus the `BT_ATTEMPT_KEY` marker the supervisor adds; nothing leaks in from the
    orchestrator or from the systemd user manager, and the per-unit variables of the manager (`MANAGER_ENV`) are
    dropped: they belong to the unit that runs the agent, never to the caller. `argv`, `cwd` and `stdin_text` are stored 0600 in the attempt state
    directory; `env` and `stdin_text` are deleted from disk as soon as the attempt has started."""

    attempt_key: str
    argv: list[str] = Field(min_length=1)
    cwd: Path
    env: dict[str, str]
    log_dir: Path
    stdin_text: str | None = None
    limits: Limits = Field(default_factory=Limits)
    kill_grace_seconds: float = Field(default=30.0, gt=0, le=3600)
    output_cap_bytes: int = Field(default=8 * MIB, ge=1024)

    @field_validator("attempt_key")
    @classmethod
    def _key(cls, value: str) -> str:
        return validate_attempt_key(value)

    @field_validator("argv")
    @classmethod
    def _argv(cls, value: list[str]) -> list[str]:
        if any("\0" in arg for arg in value) or not value[0]:
            raise ValueError("argv items must not contain NUL and argv[0] must not be empty")
        return value

    @field_validator("cwd", "log_dir")
    @classmethod
    def _absolute(cls, value: Path) -> Path:
        if not value.is_absolute():
            raise ValueError("cwd and log_dir must be absolute paths")
        return value

    @field_validator("env")
    @classmethod
    def _env(cls, value: dict[str, str]) -> dict[str, str]:
        for name, item in value.items():
            if not ENV_NAME_PATTERN.match(name):
                raise ValueError(f"invalid environment variable name: {name!r}")
            if "\0" in item:
                raise ValueError(f"environment variable {name} contains NUL")
        if MARKER_ENV in value or SUPERVISOR_ENV in value:
            raise ValueError(f"{MARKER_ENV} and {SUPERVISOR_ENV} are reserved for the supervisor")
        return {name: item for name, item in value.items() if name not in MANAGER_ENV}

    @model_validator(mode="after")
    def _stdin(self) -> LaunchSpec:
        if self.stdin_text is not None and "\0" in self.stdin_text:
            raise ValueError("stdin_text must not contain NUL")
        return self


class ProcessIdentity(_Frozen):
    """What names one attempt incarnation. systemd: `unit` + `invocation_id` (a reused unit name gets a new
    invocation id); pgroup: `main_pid` + `main_start_time` + `boot_id` of the session leader, and `invocation_id` is a
    random id the reaper generates. `main_pid` is never signalled on its own (see README §Identity)."""

    attempt_key: str
    backend: Backend
    unit: str | None
    invocation_id: str | None
    control_group: str | None
    main_pid: int | None
    main_start_time: float | None
    boot_id: str


class Observation(_Frozen):
    """A point-in-time view, produced without side effects.

    `state`: running = something of the attempt is alive (frozen counts as running); exited = the main process has
    ended and its outcome is final; absent = nothing was launched under this key (or it was released, or a launch
    crashed before anything started — re-running `launch` is then safe); unknown = cannot tell right now (a launch is
    in progress, the service manager did not answer, or the unit name now belongs to another invocation).
    `live_pids` may be non-empty for an exited attempt: stragglers that escaped (call `terminate` before reusing the
    worktree). `result`: success | exit-code | signal | core-dump | timeout | oom-kill | start-limit | resources |
    terminated | spawn-error | lost (no exit record could ever be written: reboot, killed reaper, lost manager)."""

    identity: ProcessIdentity
    state: State
    exit_code: int | None
    signal: str | None
    result: str | None
    oom_killed: bool
    live_pids: list[int]
    started_at: float | None
    ended_at: float | None
    log_path: Path
