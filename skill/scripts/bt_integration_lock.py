"""Fail-closed process lease for serialized integration work."""
from __future__ import annotations

import json
import fcntl
import os
import secrets
import socket
import subprocess
import time
from pathlib import Path


class LockTimeout(TimeoutError):
    """The integration lease was not acquired before its deadline."""


class LockHeld(RuntimeError):
    """A lease exists whose owner cannot safely be reclaimed."""


class _UnreadableLock(LockHeld):
    """A lease is being atomically published or replaced."""


def process_start_time(pid: int) -> str:
    """Return a stable process start marker, or unknown when the OS cannot prove it."""
    try:
        stat_line = Path(f"/proc/{pid}/stat").read_text()
        fields = stat_line[stat_line.rfind(")") + 2:].split()
        return fields[19]
    except (OSError, IndexError):
        try:
            result = subprocess.run(["ps", "-o", "lstart=", "-p", str(pid)], capture_output=True,
                                    text=True, timeout=2, check=False)
            value = result.stdout.strip()
            return value if result.returncode == 0 and value else "unknown"
        except (OSError, subprocess.SubprocessError):
            return "unknown"


def _alive(pid: int, start: str) -> bool | None:
    if start == "unknown":
        return None
    if not Path(f"/proc/{pid}").exists():
        try:
            result = subprocess.run(["ps", "-o", "pid=", "-p", str(pid)], capture_output=True,
                                    text=True, timeout=2, check=False)
            if result.returncode == 1 or not result.stdout.strip():
                return False
        except (OSError, subprocess.SubprocessError):
            pass
    observed = process_start_time(pid)
    if observed == "unknown":
        return None
    return observed == start


class IntegrationLock:
    """An O_EXCL lease that only reclaims a provably dead local process."""

    def __init__(self, directory: Path | str, host_id: str | None = None) -> None:
        self.directory = Path(directory)
        self.path = self.directory / "integration.lock"
        self.host_id = host_id or socket.gethostname()
        self.owner: dict[str, object] | None = None

    def _identity(self) -> dict[str, object]:
        return {"host": self.host_id, "pid": os.getpid(), "start": process_start_time(os.getpid()),
                "heartbeat": time.time()}

    def acquire(self, timeout: float = 30.0, poll_interval: float = 0.05) -> "IntegrationLock":
        self.directory.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + timeout
        self.owner = self._identity()
        guard = self.directory / ".integration.lock.guard"
        while True:
            guard_fd = os.open(guard, os.O_CREAT | os.O_RDWR, 0o600)
            try:
                fcntl.flock(guard_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                os.close(guard_fd)
                if time.monotonic() >= deadline:
                    raise LockTimeout(f"Integration lock reclaim in progress at {self.path}.")
                time.sleep(min(poll_interval, max(0.0, deadline - time.monotonic())))
                continue
            acquired = False
            try:
                temporary = self.directory / f".integration.lock.{os.getpid()}.{secrets.token_hex(8)}"
                try:
                    fd = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                    with os.fdopen(fd, "w", encoding="utf-8") as stream:
                        json.dump(self.owner, stream)
                        stream.flush()
                        os.fsync(stream.fileno())
                    try:
                        os.link(temporary, self.path)
                        acquired = True
                    except FileExistsError:
                        try:
                            self._reclaim_if_proven_dead()
                        except _UnreadableLock:
                            pass
                finally:
                    temporary.unlink(missing_ok=True)
            finally:
                fcntl.flock(guard_fd, fcntl.LOCK_UN)
                os.close(guard_fd)
            if acquired:
                return self
            if not self.path.exists():
                continue
            if time.monotonic() >= deadline:
                raise LockTimeout(f"Integration lock held at {self.path}; inspect its owner before retrying.")
            time.sleep(min(poll_interval, max(0.0, deadline - time.monotonic())))

    def _read_owner(self, path: Path | None = None) -> tuple[dict[str, object], os.stat_result]:
        selected = self.path if path is None else path
        try:
            info = selected.stat()
            owner = json.loads(selected.read_text(encoding="utf-8"))
            if (not isinstance(owner, dict) or not isinstance(owner.get("host"), str) or
                    not isinstance(owner.get("pid"), int) or not isinstance(owner.get("start"), str) or
                    not isinstance(owner.get("heartbeat"), (int, float))):
                raise ValueError("owner record is incomplete")
            return owner, info
        except (OSError, ValueError) as exc:
            raise _UnreadableLock(f"Integration lock at {selected} is unreadable; retry while it is published.") from exc

    def _reclaim_if_proven_dead(self) -> bool:
        tombstone = self.directory / f".integration.lock.reclaim-{os.getpid()}-{secrets.token_hex(8)}"
        try:
            os.rename(self.path, tombstone)
        except FileNotFoundError:
            return False
        try:
            owner, _ = self._read_owner(tombstone)
        except _UnreadableLock:
            self._restore_tombstone(tombstone)
            raise
        if owner.get("host") != self.host_id:
            self._restore_tombstone(tombstone)
            raise LockHeld(f"Integration lock belongs to host {owner.get('host')!r}; verify that host and remove it manually.")
        pid, start = owner.get("pid"), owner.get("start")
        if not isinstance(pid, int) or not isinstance(start, str):
            self._restore_tombstone(tombstone)
            raise LockHeld("Integration lock has unknown owner liveness; inspect it and remove it manually.")
        alive = _alive(pid, start)
        if alive is True:
            self._restore_tombstone(tombstone)
            return False
        if alive is None:
            self._restore_tombstone(tombstone)
            raise LockHeld(f"Integration lock owner {pid}/{start} is unverifiable; inspect it and remove it manually.")
        tombstone.unlink(missing_ok=True)
        return True

    def _restore_tombstone(self, tombstone: Path) -> None:
        try:
            os.link(tombstone, self.path)
        except FileExistsError:
            raise LockHeld(f"Integration lock changed during reclaim at {self.path}; inspect both lease files.")
        tombstone.unlink(missing_ok=True)

    def renew(self) -> None:
        """Refresh heartbeat only while this exact process still owns the lease."""
        current, info = self._read_owner()
        if not self.owner or any(current.get(k) != self.owner.get(k) for k in ("host", "pid", "start")):
            raise LockHeld("Integration lease ownership changed; refusing to renew.")
        updated = {**current, "heartbeat": time.time()}
        temporary = self.directory / f".integration.lock.renew-{os.getpid()}-{secrets.token_hex(8)}"
        fd = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(updated, stream)
            stream.flush()
            os.fsync(stream.fileno())
        if not self.path.exists() or self.path.stat().st_ino != info.st_ino:
            temporary.unlink(missing_ok=True)
            raise LockHeld("Integration lease changed while renewing.")
        os.replace(temporary, self.path)

    def release(self) -> None:
        """Remove only a lease still owned by this process identity."""
        if not self.owner or not self.path.exists():
            return
        current, info = self._read_owner()
        if all(current.get(k) == self.owner.get(k) for k in ("host", "pid", "start")):
            after = self.path.stat()
            if info.st_ino == after.st_ino:
                self.path.unlink()
        self.owner = None

    def __enter__(self) -> "IntegrationLock":
        return self

    def __exit__(self, *_: object) -> None:
        self.release()
