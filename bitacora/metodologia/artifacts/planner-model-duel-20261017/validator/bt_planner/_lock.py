"""Advisory exclusive lock for one plan directory: an in-process lock plus an O_EXCL lock file with stale recovery.

Not re-entrant: a nested `exclusive()` on the same file waits for itself until the timeout. Critical sections here are
short (one manifest write) and never nest."""
from __future__ import annotations

import contextlib
import os
import threading
import time
from pathlib import Path

from .contract import PlanContractError

STALE_SECONDS = 60.0
_registry_guard = threading.Lock()
_guards: dict[str, threading.Lock] = {}


@contextlib.contextmanager
def exclusive(lock_file: Path, timeout: float = 30.0):
    """Serialise writers of the same plan directory. A lock file older than STALE_SECONDS (crashed holder) is broken;
    waiting longer than `timeout` raises REVISION_STORE_BUSY instead of writing unlocked."""
    lock_file = Path(lock_file)
    with _registry_guard:
        guard = _guards.setdefault(str(lock_file), threading.Lock())
    if not guard.acquire(timeout=timeout):
        raise PlanContractError("REVISION_STORE_BUSY", [f"another writer holds {lock_file.parent.name}"])
    fd = None
    try:
        try:
            lock_file.parent.mkdir(exist_ok=True)
        except OSError as exc:
            raise PlanContractError("REVISION_STORE_UNWRITABLE", [f"{type(exc).__name__}: cannot create "
                                                                  f"{lock_file.parent.name}"]) from exc
        deadline = time.monotonic() + timeout
        while fd is None:
            try:
                fd = os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            except FileExistsError:
                try:
                    if time.time() - lock_file.stat().st_mtime > STALE_SECONDS:
                        lock_file.unlink(missing_ok=True)
                        continue
                except OSError:
                    pass
                if time.monotonic() > deadline:
                    raise PlanContractError("REVISION_STORE_BUSY", [f"another writer holds {lock_file.name}"]) from None
                time.sleep(0.02)
            except OSError as exc:
                raise PlanContractError("REVISION_STORE_UNWRITABLE",
                                        [f"{type(exc).__name__}: cannot lock {lock_file.parent.name}"]) from exc
        yield
    finally:
        if fd is not None:
            os.close(fd)
            with contextlib.suppress(OSError):
                lock_file.unlink()
        guard.release()
