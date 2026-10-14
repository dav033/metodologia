"""Process facts the relay needs (Linux /proc): who is the agent, is it the same process, is it gone.

Every reader returns None/False on any error: the relay only acts on a process it positively verified.
"""
from __future__ import annotations

import os
from pathlib import Path

AGENT_NAMES = ("claude", "codex")
TICKS = os.sysconf("SC_CLK_TCK") if hasattr(os, "sysconf") else 100


def read(pid: int) -> dict | None:
    """{ppid, comm, state, start, argv0, args, tty} of a live process, None when unreadable."""
    try:
        raw = Path(f"/proc/{int(pid)}/stat").read_text()
        head, _, tail = raw.rpartition(")")
        comm = head.split("(", 1)[1]
        fields = tail.split()
        try:
            argv = Path(f"/proc/{int(pid)}/cmdline").read_bytes().decode(errors="replace").split("\0")
        except OSError:
            argv = [""]
        return {"ppid": int(fields[1]), "comm": comm, "state": fields[0], "start": int(fields[19]),
                "argv0": os.path.basename(argv[0]),
                "args": [a for a in argv[1:] if a], "tty": int(fields[4]) != 0}
    except (OSError, ValueError, IndexError):
        return None


def is_agent(info: dict | None) -> bool:
    return bool(info) and (info["comm"] in AGENT_NAMES or info["argv0"] in AGENT_NAMES)


def find_agent(start_pid: int, reader=None) -> tuple[int, int] | None:
    """(pid, start time) of the nearest ancestor of `start_pid` that is a claude/codex process: the agent this
    command runs inside. None when no ancestor is one."""
    reader = reader or read
    pid, seen = start_pid, set()
    while pid and pid > 1 and pid not in seen:
        seen.add(pid)
        info = reader(pid)
        if info is None:
            return None
        if pid != start_pid and is_agent(info):
            return pid, info["start"]
        pid = info["ppid"]
    return None


def same_agent(pid: int, start: int, reader=None) -> bool:
    """The pid still is the agent recorded at handoff time (name and start time match: a recycled pid fails)."""
    reader = reader or read
    info = reader(pid)
    return bool(info) and info["state"] != "Z" and info["start"] == start and is_agent(info)


def alive(pid: int, start: int, reader=None) -> bool:
    reader = reader or read
    info = reader(pid)
    return bool(info) and info["state"] != "Z" and info["start"] == start


def environ_of(pid: int) -> dict | None:
    """Environment of a process of the same user (None when unreadable)."""
    try:
        raw = Path(f"/proc/{int(pid)}/environ").read_bytes().decode(errors="replace")
    except OSError:
        return None
    return dict(item.split("=", 1) for item in raw.split("\0") if "=" in item)


def ancestors(pid: int, reader=None) -> list[int]:
    """`pid` and its ancestors (nearest first)."""
    reader = reader or read
    out = []
    while pid and pid > 1 and pid not in out:
        out.append(pid)
        info = reader(pid)
        if info is None:
            break
        pid = info["ppid"]
    return out
