"""Process identity and signalling helpers (POSIX). A pid alone proves nothing: it can be recycled, so every signal is
sent only after the process's start-time identity matches what was recorded when it was spawned."""
from __future__ import annotations

import os
import signal
import subprocess
from collections.abc import Collection
from pathlib import Path

from .errors import ExecutorError


def require_posix() -> None:
    if os.name != "posix":
        raise ExecutorError("PLATFORM_UNSUPPORTED", "the agent executor needs POSIX sessions and process groups")


def _boot_id() -> str:
    try:
        return Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    except OSError:
        return "noboot"


class IdentityUnknown(OSError):
    """The process table could not be read right now (descriptor/memory pressure, permissions): NOT the same as "gone"."""


def _proc_stat(pid: int) -> tuple[str, str] | None:
    """(state, starttime ticks) from /proc/<pid>/stat, or None when the process does not exist / no /proc."""
    try:
        text = Path(f"/proc/{int(pid)}/stat").read_text()
    except (FileNotFoundError, ProcessLookupError, NotADirectoryError, ValueError):
        return None
    except OSError as error:
        raise IdentityUnknown(str(error)) from None
    tail = text[text.rfind(")") + 2:].split()
    if len(tail) < 20:
        return None
    return tail[0], tail[19]


def start_ident(pid: int) -> str | None:
    """A string that identifies THIS process incarnation (None: it does not exist, or is a zombie)."""
    stat = _proc_stat(pid)
    if stat is not None:
        state, ticks = stat
        return None if state in ("Z", "X") else f"{_boot_id()}:{ticks}"
    if Path("/proc/self").exists():       # /proc exists but this pid does not
        return None
    try:                                  # hosts without /proc: ps reports the start time
        out = subprocess.run(["ps", "-o", "lstart=", "-p", str(int(pid))], capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError, ValueError):
        return None
    return f"ps:{out.stdout.strip()}" if out.returncode == 0 and out.stdout.strip() else None


def alive(pid: int | None, ident: str | None) -> bool:
    """True only when `pid` exists and is the process recorded as `ident`."""
    if not pid or not ident:
        return False
    try:
        return start_ident(pid) == ident
    except IdentityUnknown:
        return True            # cannot tell: the safe answer is "still there" (nothing gets killed on a guess)


def signal_group(pgid: int, sig: int) -> bool:
    """Signal a whole process group. The caller has already verified the leader's identity."""
    try:
        os.killpg(int(pgid), sig)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def signal_pid(pid: int, sig: int) -> bool:
    try:
        os.kill(int(pid), sig)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def _stat_tail(pid: int) -> tuple[int, int] | None:
    """(ppid, controlling tty number) of a process, from /proc; None when unreadable."""
    try:
        raw = Path(f"/proc/{int(pid)}/stat").read_text(encoding="utf-8", errors="replace")
        fields = raw[raw.rindex(")") + 2:].split()
        return int(fields[1]), int(fields[4])         # state ppid pgrp session tty_nr ...
    except (OSError, ValueError, IndexError):
        return None


def descends_from(pid: int, roots: Collection[int]) -> bool:
    """True when `pid` is one of `roots` or has one of them as an ancestor (bounded walk through the parent links)."""
    current = int(pid)
    for _ in range(64):
        if current in roots:
            return True
        tail = _stat_tail(current)
        if tail is None or tail[0] <= 1:
            return False
        current = tail[0]
    return False


def kill_in_cwd(directory: str, sig: int = signal.SIGKILL, *, roots: Collection[int] = (),
                spare_interactive: bool = False) -> int:
    """Signal every process (but this one) whose working directory is inside `directory`: the stragglers an agent left
    behind, even ones that called setsid and escaped its process group. Linux /proc only; returns how many were signalled.
    A process that moved away from the worktree is out of reach (stated limit).

    With `spare_interactive`, a process that has a controlling terminal and is NOT a descendant of one of `roots` (the
    attempt's shim and agent) is left alone: it is an operator's shell or editor that happens to be in the worktree, not
    something the agent started. An agent's own pty children are still swept while they remain its descendants."""
    proc, base, hit = Path("/proc"), os.path.realpath(directory), 0
    if not proc.exists():
        return 0
    for entry in proc.iterdir():
        if not entry.name.isdigit() or int(entry.name) == os.getpid():
            continue
        try:
            cwd = os.readlink(entry / "cwd")
        except OSError:
            continue
        if cwd == base or cwd.startswith(base + os.sep):
            if spare_interactive:
                tail = _stat_tail(int(entry.name))
                if tail is not None and tail[1] != 0 and not descends_from(int(entry.name), roots):
                    continue
            try:
                os.kill(int(entry.name), sig)
                hit += 1
            except OSError:
                pass
    return hit


def find_by_argv(shim: str, directory: str) -> list[int]:
    """Pids of shims started for `directory`: the command line must be exactly `<python> <shim> <directory>` (Linux). Used only
    to find a shim whose identity record was never written; an unrelated `tail`/`vim` of those paths does not match."""
    found: list[int] = []
    proc = Path("/proc")
    if not proc.exists():
        return found
    for entry in proc.iterdir():
        if not entry.name.isdigit() or int(entry.name) == os.getpid():
            continue
        try:
            parts = (entry / "cmdline").read_bytes().decode("utf-8", "replace").split("\0")
            exact = len(parts) == 4 and parts[3] == ""                     # <python> <shim> <directory> and nothing else
            if exact and os.path.realpath(parts[1]) == os.path.realpath(shim) and parts[2] == directory \
                    and start_ident(int(entry.name)):
                found.append(int(entry.name))
        except (OSError, IdentityUnknown):
            continue
    return found



SIGNALS = {int(s): s.name for s in signal.Signals}


def signal_name(returncode: int | None) -> str:
    if returncode is None or returncode >= 0:
        return ""
    return SIGNALS.get(-returncode, f"SIG{-returncode}")

