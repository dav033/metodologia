"""What both backends share: the store, the helper interpreter, outcome derivation and observation assembly."""
from __future__ import annotations

import os
import shutil
import signal
import sys
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from . import procs
from .errors import BackendMismatch
from .model import Observation, ProcessIdentity, validate_attempt_key
from .store import AttemptStore

SERVICE_RESULTS = {"timeout": "timeout", "start-limit-hit": "start-limit", "resources": "resources",
                   "protocol": "protocol", "watchdog": "watchdog", "core-dump": "core-dump"}


def default_helper_python() -> str:
    """The interpreter that runs tee.py for the whole life of an attempt. The system python3 outlives uv
    environments (a `uv sync` or a deleted worktree must not break a running attempt's ExecStopPost); the helper is
    stdlib-only, so any CPython ≥ 3.9 works. Fallback: the real path of the current interpreter."""
    found = shutil.which("python3", path="/usr/bin:/bin")
    return found or os.path.realpath(sys.executable)


def signal_name(number: int) -> str:
    try:
        return signal.Signals(number).name
    except ValueError:
        return f"SIG{number}"


def derive_outcome(exit_rec: dict | None, child_rec: dict | None, terminate_requested: bool,
                   fallback: dict | None = None) -> tuple[int | None, str | None, str | None, bool]:
    """(exit_code, signal, result, oom_killed) from the records. Sources by precedence: the agent's own wait status
    (child.json / pgroup exit.json), then systemd's `$EXIT_CODE/$EXIT_STATUS`, then `systemctl show` (`fallback`, used
    when no exit record exists). Result precedence: oom-kill > spawn-error > terminated > timeout > manager results >
    signal/core-dump > success/exit-code."""
    exit_rec, child_rec = exit_rec or {}, child_rec or {}
    if not exit_rec and fallback:
        code = {"1": "exited", "2": "killed", "3": "dumped"}.get(str(fallback.get("ExecMainCode")))
        exit_rec = {"service_result": fallback.get("Result"), "exit_kind": code,
                    "exit_status": str(fallback.get("ExecMainStatus", ""))}
    returncode = child_rec.get("returncode")
    if returncode is None:
        returncode = exit_rec.get("returncode")
    exit_code = sig = None
    kind = exit_rec.get("exit_kind")
    if returncode is not None:
        exit_code, sig = (returncode, None) if returncode >= 0 else (None, signal_name(-returncode))
    else:
        status = str(exit_rec.get("exit_status") or "")
        if kind == "exited" and status.isdigit():
            exit_code = int(status)
        elif kind in ("killed", "dumped") and status:
            sig = signal_name(int(status)) if status.isdigit() else (status if status.startswith("SIG") else f"SIG{status}")
    service, reason = exit_rec.get("service_result"), exit_rec.get("reason")
    oom = service == "oom-kill" or (exit_rec.get("oom_kill") or 0) > 0
    if oom:
        result = "oom-kill"
    elif child_rec.get("spawn_error") or exit_rec.get("spawn_error") or reason == "spawn-error":
        result = "spawn-error"
    elif terminate_requested or reason == "terminated":
        result = "terminated"
    elif reason == "timeout":
        result = "timeout"
    elif service in SERVICE_RESULTS:
        result = SERVICE_RESULTS[service]
    elif kind == "dumped":
        result = "core-dump"
    elif sig:
        result = "signal"
    elif exit_code == 0:
        result = "success"
    elif exit_code is not None:
        result = "exit-code"
    else:
        result = service or None
    return exit_code, sig, result, oom


class BaseSupervisor:
    backend: str = ""

    def __init__(self, state_dir: Path, *, helper_python: str | None = None):
        self.store = AttemptStore(state_dir)
        self.python = helper_python or default_helper_python()
        self._held = threading.local()           # keys whose lock THIS thread holds (observe must not probe them)

    @contextmanager
    def _locked(self, key: str) -> Iterator[None]:
        held = self._held.__dict__.setdefault("keys", set())
        with self.store.lock(key):
            held.add(key)
            try:
                yield
            finally:
                held.discard(key)

    def _launch_in_flight(self, key: str) -> bool:
        """Someone else holds the key's lock: a 'starting' record may still become a running attempt."""
        return key not in self._held.__dict__.get("keys", set()) and self.store.is_locked(key)

    # ------------------------------------------------------------------------------------------------ helpers
    def _record(self, key: str) -> dict | None:
        validate_attempt_key(key)
        record = self.store.read(key, "launch.json")
        if record is not None and record.get("backend") != self.backend:
            raise BackendMismatch(f"attempt {key} was launched by the {record.get('backend')} backend")
        return record

    @staticmethod
    def _log_path(record: dict | None) -> Path:
        return Path(record["log_dir"]) / "output.log" if record else Path(os.devnull)

    def _bare_identity(self, key: str, unit: str | None = None) -> ProcessIdentity:
        return ProcessIdentity(attempt_key=key, backend=self.backend, unit=unit, invocation_id=None,
                               control_group=None, main_pid=None, main_start_time=None, boot_id=procs.boot_id())

    def _observation(self, identity: ProcessIdentity, state: str, record: dict | None, *, live: list[int],
                     outcome: tuple | None = None) -> Observation:
        key = identity.attempt_key
        started = self.store.read(key, "started.json") if record else None
        exit_rec = self.store.read(key, "exit.json") if record else None
        exit_code, sig, result, oom = outcome or (None, None, None, False)
        return Observation(identity=identity, state=state, exit_code=exit_code, signal=sig, result=result,
                           oom_killed=oom, live_pids=sorted(set(live)),
                           started_at=(started or {}).get("started_at"),
                           ended_at=(exit_rec or {}).get("ended_at") if state == "exited" else None,
                           log_path=self._log_path(record))

    def _absent(self, key: str, unit: str | None = None) -> Observation:
        return self._observation(self._bare_identity(key, unit), "absent", None, live=[])

    def _terminate_requested(self, key: str) -> bool:
        return self.store.exists(key, "terminate.json")

    def _request_terminate(self, key: str, grace: float) -> None:
        if not self._terminate_requested(key):
            self.store.write(key, "terminate.json", {"requested_at": time.time(), "grace": grace})

    @staticmethod
    def _wait_for(predicate, timeout: float, step: float = 0.02) -> bool:
        end = time.monotonic() + timeout
        while True:
            if predicate():
                return True
            if time.monotonic() >= end:
                return False
            time.sleep(step)
