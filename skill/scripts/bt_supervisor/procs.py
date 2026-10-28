"""Process-table and cgroup helpers for the orchestrator side (psutil + /proc + /sys/fs/cgroup).

Identity rule: a process is named by (pid, start seconds since boot) on one `boot_id`; every signal goes through a
pidfd opened BEFORE the start time is re-checked (`tee.send`), so a recycled pid is never signalled. Process groups
are signalled only when the group leader's incarnation is verified (alive or still an unreaped zombie: in both cases
its pid, hence the pgid, cannot have been recycled).
"""
from __future__ import annotations

import os
import signal
import time
from pathlib import Path

import psutil

from . import tee
from .model import MARKER_ENV

CGROUP_ROOT = Path("/sys/fs/cgroup")
boot_id = tee.boot_id


def start_time(pid: int | None, *, allow_zombie: bool = False) -> float | None:
    """Start seconds since boot of `pid`, or None when it does not exist (or is a zombie, unless allowed)."""
    if not pid or pid <= 0:
        return None
    fields = tee.stat_fields(pid)
    if fields is None or fields[0] == "X" or (fields[0] == "Z" and not allow_zombie):
        return None
    return fields[3]


def alive(pid: int | None, start: float | None) -> bool:
    """True only when `pid` is the live (non-zombie) process that started at `start`."""
    return start is not None and start_time(pid) == start


def same_incarnation(pid: int | None, start: float | None) -> bool:
    """Like `alive`, but an unreaped zombie still counts: its pid/pgid is still reserved."""
    return start is not None and start_time(pid, allow_zombie=True) == start


def marked(key: str) -> dict[int, float]:
    """Live processes of this user whose environment carries `BT_ATTEMPT_KEY=<key>` (catches `setsid` escapers).
    Limits: a process that rewrote or cleared its initial environment block is not recognised."""
    found: dict[int, float] = {}
    uid, me = os.getuid(), os.getpid()
    for proc in psutil.process_iter(["uids", "status"]):
        info = proc.info
        if proc.pid == me or info.get("uids") is None or info["uids"].real != uid:
            continue
        if info.get("status") in (psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD):
            continue
        try:
            if proc.environ().get(MARKER_ENV) != key:
                continue
        except (psutil.Error, OSError):
            continue
        start = start_time(proc.pid)
        if start is not None:
            found[proc.pid] = start
    return found


def group_members(pgid: int) -> dict[int, float]:
    """Live members of process group `pgid` (caller has verified the leader's incarnation)."""
    found: dict[int, float] = {}
    for pid in psutil.pids():
        fields = tee.stat_fields(pid)
        if fields is not None and fields[2] == pgid and fields[0] not in ("Z", "X"):
            found[pid] = fields[3]
    return found


def cgroup_of(pid: int) -> str | None:
    try:
        for line in Path(f"/proc/{pid}/cgroup").read_text().splitlines():
            if line.startswith("0::"):
                return line[3:]
    except OSError:
        pass
    return None


def inside(group: str | None, control_group: str | None) -> bool:
    return bool(group and control_group) and (group == control_group or group.startswith(control_group.rstrip("/") + "/"))


def cgroup_pids(control_group: str | None) -> list[int]:
    """Every pid in the cgroup subtree (a process may create child cgroups inside its own unit)."""
    if not control_group:
        return []
    base = CGROUP_ROOT / control_group.lstrip("/")
    pids: set[int] = set()
    try:
        for directory, _dirs, files in os.walk(base):
            if "cgroup.procs" in files:
                try:
                    pids.update(int(line) for line in Path(directory, "cgroup.procs").read_text().split())
                except (OSError, ValueError):
                    continue
    except OSError:
        return []
    return sorted(pids)


def cgroup_kill(control_group: str | None) -> bool:
    """Write 1 to cgroup.kill: SIGKILL to the whole subtree, atomic with respect to forks (kernel ≥ 5.14)."""
    if not control_group:
        return False
    try:
        (CGROUP_ROOT / control_group.lstrip("/") / "cgroup.kill").write_text("1")
        return True
    except OSError:
        return False


def signal_all(targets: dict[int, float], sig: int) -> int:
    return sum(1 for pid, start in targets.items() if tee.send(pid, start, sig))


def terminate_targets(targets_fn, grace: float, *, kill_window: float = 10.0) -> bool:
    """SIGTERM+SIGCONT what `targets_fn()` returns, wait up to `grace` for it to empty, then SIGKILL in sweeps for at
    most `kill_window` seconds (a process forked between scan and kill is caught by the next sweep). True when
    nothing is left."""
    sleep = time.sleep
    targets = targets_fn()
    if not targets:
        return True
    signal_all(targets, signal.SIGTERM)
    signal_all(targets, signal.SIGCONT)
    end = time.monotonic() + grace
    while time.monotonic() < end:
        sleep(0.05)
        if not targets_fn():
            return True
    end = time.monotonic() + kill_window
    while time.monotonic() < end:
        targets = targets_fn()
        if not targets:
            return True
        signal_all(targets, signal.SIGKILL)
        sleep(0.05)
    return not targets_fn()
