"""Which processes belong to a test version («Probar»), and stopping exactly those.

Owner, 2026-10-30: clicking a version's URL «must kill every process associated with that URL and start the correct
worktree clean», and never a process of another version or an unrelated service (pictures: pid 2419 on port 8000 is a
long-running service of its own). So nothing is ever killed by port alone. A process belongs to a version when

- its environment carries the version's mark (`BITACORA_VERIFY_ID=<project>/<REQ>/<SP>-v<N>`, set by the start script
  and inherited by every child: Next's workers, uvicorn's reloader), or
- it descends from the version's tmux pane, or
- it listens on a TCP port and works inside the version's copy (its cwd or a path in its command line), which catches
  servers started before the mark existed or by hand in the copy (pictures SP-1/SP-2, 2026-10-29).

`listeners()` maps ports to the pids listening on them (from /proc, own user's processes only); `terminate()` stops a
set of pids with SIGTERM, whole process groups only when every member of the group is in the set, then SIGKILL after a
grace period. Linux /proc only; standard library only.
"""
from __future__ import annotations

import os
import signal
import time
from pathlib import Path

MARK = "BITACORA_VERIFY_ID"
PROC = Path("/proc")


def _pids() -> list[int]:
    return [int(p.name) for p in PROC.iterdir() if p.name.isdigit()]


def _stat(pid: int) -> tuple[int, int] | None:
    """(ppid, pgid) of a process, None when it is gone."""
    try:
        raw = (PROC / str(pid) / "stat").read_text()
    except OSError:
        return None
    fields = raw[raw.rfind(")") + 2:].split()          # the command name may contain spaces and parentheses
    try:
        return int(fields[1]), int(fields[2])
    except (IndexError, ValueError):
        return None


def alive(pid: int) -> bool:
    try:
        state = (PROC / str(pid) / "stat").read_text()
    except OSError:
        return False
    return state[state.rfind(")") + 2:][:1] not in ("Z", "X", "")


def environ_mark(pid: int) -> str:
    try:
        raw = (PROC / str(pid) / "environ").read_bytes()
    except OSError:
        return ""
    prefix = (MARK + "=").encode()
    for item in raw.split(b"\0"):
        if item.startswith(prefix):
            return item[len(prefix):].decode("utf-8", "replace")
    return ""


def _inside(path: str, root: str) -> bool:
    return bool(path) and (path == root or path.startswith(root.rstrip("/") + "/"))


def works_in(pid: int, copy: Path) -> bool:
    """The process runs inside `copy`: its working directory, or a path argument of its command line."""
    root = str(Path(copy).resolve()) if Path(copy).exists() else str(copy)
    try:
        if _inside(os.readlink(PROC / str(pid) / "cwd"), root):
            return True
        args = (PROC / str(pid) / "cmdline").read_bytes().split(b"\0")
    except OSError:
        return False
    return any(_inside(a.decode("utf-8", "replace"), root) for a in args if a.startswith(b"/"))


def _listening_ports() -> dict[str, int]:
    """socket inode -> port, for every TCP socket in LISTEN state."""
    found: dict[str, int] = {}
    for table in ("tcp", "tcp6"):
        try:
            rows = (PROC / "net" / table).read_text().splitlines()[1:]
        except OSError:
            continue
        for row in rows:
            cols = row.split()
            if len(cols) > 9 and cols[3] == "0A":
                found[cols[9]] = int(cols[1].rsplit(":", 1)[1], 16)
    return found


def listeners() -> dict[int, set[int]]:
    """port -> pids listening on it (processes whose descriptors we may read: the owner's own)."""
    inodes = _listening_ports()
    out: dict[int, set[int]] = {}
    if not inodes:
        return out
    for pid in _pids():
        try:
            fds = list((PROC / str(pid) / "fd").iterdir())
        except OSError:
            continue
        for fd in fds:
            try:
                link = os.readlink(fd)
            except OSError:
                continue
            if link.startswith("socket:[") and link[8:-1] in inodes:
                out.setdefault(inodes[link[8:-1]], set()).add(pid)
    return out


def port_busy(port: int, table: dict[int, set[int]] | None = None) -> bool:
    """Something listens on the port: in our table, or (a process of another user) it accepts a connection."""
    if table is not None and table.get(port):
        return True
    import socket
    for family, host in ((socket.AF_INET, "127.0.0.1"), (socket.AF_INET6, "::1")):
        try:
            with socket.socket(family, socket.SOCK_STREAM) as probe:
                probe.settimeout(0.3)
                if probe.connect_ex((host, port)) == 0:
                    return True
        except OSError:
            continue
    return False


def children() -> dict[int, list[int]]:
    tree: dict[int, list[int]] = {}
    for pid in _pids():
        stat = _stat(pid)
        if stat:
            tree.setdefault(stat[0], []).append(pid)
    return tree


def descendants(roots: set[int], tree: dict[int, list[int]] | None = None) -> set[int]:
    tree = children() if tree is None else tree
    seen, todo = set(), list(roots)
    while todo:
        pid = todo.pop()
        if pid in seen:
            continue
        seen.add(pid)
        todo.extend(tree.get(pid, []))
    return seen


def owned(mark: str, copy: Path, roots: set[int] = frozenset(), table: dict[int, set[int]] | None = None) -> set[int]:
    """Every live process of the version: marked with `mark`, descending from `roots` (its tmux pane), or listening
    while working inside `copy`. Never this process or its ancestors (the panel itself)."""
    me = {os.getpid()}
    stat = _stat(os.getpid())
    while stat and stat[0] > 1:                          # the panel and whatever started it
        me.add(stat[0])
        stat = _stat(stat[0])
    tree = children()
    found = descendants({r for r in roots if alive(r)}, tree)
    found |= {pid for pid in _pids() if environ_mark(pid) == mark}
    table = listeners() if table is None else table
    found |= {pid for pids in table.values() for pid in pids if works_in(pid, copy)}
    found = descendants(found, tree)                     # a marked or listening server's own children go with it
    return {p for p in found if p not in me and alive(p)}


def terminate(pids: set[int], grace: float = 8.0) -> set[int]:
    """Stop `pids`: SIGTERM (a whole process group when the group has no member outside `pids`), SIGKILL whatever is
    left after `grace` seconds. Returns the pids that were signalled."""
    pids = {p for p in pids if alive(p)}
    if not pids:
        return set()
    groups: dict[int, set[int]] = {}
    for pid in _pids():
        stat = _stat(pid)
        if stat:
            groups.setdefault(stat[1], set()).add(pid)
    whole = {g for g, members in groups.items() if members <= pids and g > 1}
    for group in whole:
        try:
            os.killpg(group, signal.SIGTERM)
        except OSError:
            pass
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
    deadline = time.monotonic() + grace
    while time.monotonic() < deadline and any(alive(p) for p in pids):
        time.sleep(0.2)
    for pid in pids:
        if alive(pid):
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline and any(alive(p) for p in pids):
        time.sleep(0.1)
    return pids
