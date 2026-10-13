"""Serialize writes to bitácora files shared by concurrent sessions (PLAN.md, PENDING.md, the bitácora's git index).

One named lock = a per-process re-entrant thread lock plus an O_EXCL lock file under <root>/.state/locks, so several
supervisor threads and several processes on this machine queue instead of interleaving read-modify-write cycles.
A lock file left by a crashed process is broken after STALE_SEC; a holder that never lets go makes waiters proceed
after `timeout` rather than hang a marathon (a rare unlocked write beats a stuck supervisor).
"""
from __future__ import annotations

import contextlib
import os
import threading
import time
from pathlib import Path

STALE_SEC = 60
_guards: dict[str, threading.RLock] = {}
_depth = threading.local()
_registry = threading.Lock()


def _lock_dir() -> Path:
    from bt_core import STATE
    path = Path(STATE) / "locks"
    path.mkdir(parents=True, exist_ok=True)
    return path


@contextlib.contextmanager
def central_lock(name: str, timeout: float = 30.0):
    with _registry:
        guard = _guards.setdefault(name, threading.RLock())
    with guard:
        depth = getattr(_depth, "d", None)
        if depth is None:
            depth = _depth.d = {}
        if depth.get(name, 0) > 0:  # re-entered by the same thread
            depth[name] += 1
            try:
                yield
            finally:
                depth[name] -= 1
            return
        lock = _lock_dir() / f"central-{name}.lock"
        deadline, fd = time.time() + timeout, None
        while fd is None:
            try:
                fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                try:
                    if time.time() - lock.stat().st_mtime > STALE_SEC:
                        lock.unlink(missing_ok=True)
                        continue
                except OSError:
                    pass
                if time.time() > deadline:
                    break
                time.sleep(0.05)
        depth[name] = 1
        try:
            yield
        finally:
            depth[name] = 0
            if fd is not None:
                os.close(fd)
                lock.unlink(missing_ok=True)
