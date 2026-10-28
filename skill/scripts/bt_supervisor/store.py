"""On-disk state of a supervisor: one 0700 directory per attempt, one flock per key, atomic JSON records.

Layout under `state_dir` (all files 0600):

    locks/<key>.lock          flock taken by launch/terminate/release (outside the attempt dir so release can delete it)
    attempts/<key>/
        launch.json           what was asked (argv, cwd, limits...) + status starting|started + identity
        env | env.json        the agent environment (systemd EnvironmentFile | pgroup reaper input); deleted at start
        stdin                 stdin_text, deleted at start
        tee.py                private copy of the in-attempt helper
        reaper.json           pgroup: the reaper's identity, its first act
        started.json          the main process / agent identity, written right after the agent was spawned
        child.json            systemd: the agent's own wait status and output counters (written by `tee.py run`)
        exit.json             the exit record (ExecStopPost on systemd, the reaper on pgroup)
        terminate.json        terminate() was requested: the result becomes "terminated"
        runner.log            the helper's own diagnostics

Why records come first: `launch` writes `launch.json` with status "starting" BEFORE it starts anything, so a launcher
that crashes mid-way leaves evidence; a re-run adopts whatever exists instead of starting a duplicate.
"""
from __future__ import annotations

import fcntl
import hashlib
import os
import shutil
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from . import tee
from .errors import AttemptBusy
from .model import LaunchSpec, validate_attempt_key

TAIL_MAX = 256 * 1024
LAUNCH_VERSION = 1


def systemd_env_file(env: dict[str, str]) -> str:
    """EnvironmentFile syntax that round-trips any value (verified on systemd 261): double quotes, with backslash,
    double quote, dollar and backtick escaped; raw newlines are kept inside the quotes."""
    def quote(value: str) -> str:
        for char in ("\\", '"', "$", "`"):
            value = value.replace(char, "\\" + char)
        return f'"{value}"'
    return "".join(f"{name}={quote(value)}\n" for name, value in sorted(env.items()))


class AttemptStore:
    def __init__(self, state_dir: Path):
        self.root = Path(state_dir).expanduser().resolve()
        self.attempts = self.root / "attempts"
        self.locks = self.root / "locks"
        for directory in (self.root, self.attempts, self.locks):
            directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        # Stable per state directory: tags our systemd units so another state dir's units are never adopted.
        self.supervisor_id = hashlib.sha256(str(self.root).encode()).hexdigest()[:16]

    def dir(self, key: str) -> Path:
        return self.attempts / validate_attempt_key(key)

    # ------------------------------------------------------------------------------------------------- locking
    @contextmanager
    def lock(self, key: str, timeout: float = 120.0) -> Iterator[None]:
        path = self.locks / f"{validate_attempt_key(key)}.lock"
        fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
        try:
            end = time.monotonic() + timeout
            while True:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() >= end:
                        raise AttemptBusy(f"attempt {key} is locked by another caller") from None
                    time.sleep(0.05)
            yield
        finally:
            os.close(fd)                                 # closing the descriptor releases the flock

    def is_locked(self, key: str) -> bool:
        """Non-blocking probe used by observe() to tell 'a launch is in flight' from 'a launch crashed'."""
        path = self.locks / f"{validate_attempt_key(key)}.lock"
        try:
            fd = os.open(path, os.O_RDWR)
        except OSError:
            return False
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return False
        except BlockingIOError:
            return True
        finally:
            os.close(fd)

    # ------------------------------------------------------------------------------------------------- records
    def read(self, key: str, name: str) -> dict | None:
        return tee.read_json(self.dir(key) / name)

    def write(self, key: str, name: str, data: dict) -> None:
        tee.atomic_json(self.dir(key) / name, data)

    def exists(self, key: str, name: str) -> bool:
        return (self.dir(key) / name).exists()

    def attempt_keys(self) -> list[str]:
        try:
            return sorted(entry.name for entry in self.attempts.iterdir() if (entry / "launch.json").exists())
        except OSError:
            return []

    def new_record(self, spec: LaunchSpec, *, backend: str, unit: str | None, unenforced: list[str]) -> dict:
        """The launch record (no secrets: env NAMES only). Status starts as "starting"."""
        return {
            "version": LAUNCH_VERSION, "status": "starting", "attempt_key": spec.attempt_key, "backend": backend,
            "unit": unit, "supervisor_id": self.supervisor_id, "argv": list(spec.argv), "cwd": str(spec.cwd),
            "log_dir": str(spec.log_dir), "env_keys": sorted(spec.env), "has_stdin": spec.stdin_text is not None,
            "output_cap_bytes": spec.output_cap_bytes, "tail_bytes": min(TAIL_MAX, spec.output_cap_bytes),
            "kill_grace_seconds": spec.kill_grace_seconds, "runtime_max_seconds": spec.limits.runtime_max_seconds,
            "limits": spec.limits.model_dump(), "unenforced_limits": unenforced, "created_at": time.time(),
            "identity": None}

    def prepare(self, spec: LaunchSpec, record: dict, *, env_format: str) -> Path:
        """Create a fresh attempt directory (wiping a crashed, never-started one), write every input, then the record."""
        adir = self.dir(spec.attempt_key)
        if adir.exists():
            shutil.rmtree(adir)
        adir.mkdir(mode=0o700)
        spec.log_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        shutil.copyfile(Path(tee.__file__), adir / "tee.py")
        os.chmod(adir / "tee.py", 0o600)
        if env_format == "systemd":
            _write_private(adir / "env", systemd_env_file(spec.env))
        else:
            tee.atomic_json(adir / "env.json", dict(spec.env))
        if spec.stdin_text is not None:
            _write_private(adir / "stdin", spec.stdin_text)
        _write_private(adir / "runner.log", "")          # pre-created 0600: systemd's append: would use umask 022
        self.write(spec.attempt_key, "launch.json", record)
        return adir

    def adopt(self, spec: LaunchSpec, record: dict) -> None:
        """Record an attempt found running without a record (state dir wiped): launch.json only, no inputs."""
        self.dir(spec.attempt_key).mkdir(mode=0o700, parents=True, exist_ok=True)
        self.write(spec.attempt_key, "launch.json", record)

    def remove(self, key: str) -> None:
        adir = self.dir(key)
        if adir.exists():
            shutil.rmtree(adir)


def _write_private(path: Path, text: str) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
