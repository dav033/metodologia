"""Detached supervisor of ONE agent process (double-forked: it is re-parented to init, no longer a session leader). Runs as a script (`python shim.py <attempt dir>`), standard library only.

Why a shim: if the executor owned the agent directly, an executor restart would lose the pipe, the exit status and the
ability to stop it. The shim lives in its own session, owns the agent's process group, enforces the timeout, keeps the
output (head up to a cap + a tail window), and writes `exit.json` atomically as its last act. Everything the executor
needs after a restart is therefore on disk.

Files in the attempt directory: `spec.json` (read once, then removed: it may carry the prompt), `shim.json` (identity of
the shim and, once spawned, of the agent), `output.log` (head), `output.tail` (last window), `exit.json` (final).
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

DESCENDANT_LIMIT = 4096
DESCENDANT_SCAN_PROCESS_LIMIT = 16384
DESCENDANT_SCAN_SECONDS = 0.1


def _atomic(path: Path, data: dict) -> None:
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with os.fdopen(os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "w", encoding="utf-8") as handle:
        json.dump(data, handle, sort_keys=True)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)
    try:
        fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except OSError:
        pass


def _descendants(root_pid: int, root_ident: str) -> tuple[dict[int, str], bool]:
    """Snapshot descendant PID/start identities from Linux /proc, bounded to one attempt's configured safety ceiling."""
    proc = Path("/proc")
    try:
        boot_id = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    except OSError:
        boot_id = "noboot"
    children: dict[int, list[int]] = {}
    identities: dict[int, str] = {}
    truncated = False
    scanned = 0
    try:
        for entry in proc.iterdir():
            if not entry.name.isdigit():
                continue
            scanned += 1
            if scanned > DESCENDANT_SCAN_PROCESS_LIMIT:
                truncated = True
                break
            try:
                raw = (entry / "stat").read_text()
                fields = raw[raw.rfind(")") + 2:].split()
                if len(fields) < 20 or fields[0] in ("Z", "X"):
                    continue
                pid, parent, start_ticks = int(entry.name), int(fields[1]), fields[19]
            except (OSError, ValueError, IndexError):
                continue
            children.setdefault(parent, []).append(pid)
            identities[pid] = f"{boot_id}:{start_ticks}"
    except OSError:
        truncated = True

    if identities.get(root_pid) != root_ident:
        return {}, truncated

    found: dict[int, str] = {}
    queue = [root_pid]
    while queue and len(found) < DESCENDANT_LIMIT:
        for pid in children.get(queue.pop(), ()):
            identity = identities.get(pid)
            if identity is None or pid in found:
                continue
            found[pid] = identity
            queue.append(pid)
            if len(found) >= DESCENDANT_LIMIT:
                break
    if queue and len(found) >= DESCENDANT_LIMIT:
        truncated = True
    return found, truncated


class DescendantRecorder:
    """Persist newly observed descendants so an orphaned terminal process can still be identified at settle time."""

    def __init__(self, directory: Path):
        self.path = directory / "descendants.json"
        self.processes: dict[int, str] = {}
        self.truncated = False
        self.dirty = False

    def capture(self, root_pid: int, root_ident: str) -> None:
        found, truncated = _descendants(root_pid, root_ident)
        if truncated and not self.truncated:
            self.truncated = True
            self.dirty = True
        for pid, ident in found.items():
            if self.processes.get(pid) == ident:
                continue
            if pid not in self.processes and len(self.processes) >= DESCENDANT_LIMIT:
                if not self.truncated:
                    self.truncated = True
                    self.dirty = True
                continue
            self.processes[pid] = ident
            self.dirty = True
        if self.dirty:
            try:
                _atomic(self.path, {"version": 1, "truncated": self.truncated, "processes": [
                    {"pid": pid, "ident": ident} for pid, ident in sorted(self.processes.items())]})
                self.dirty = False
            except OSError:
                pass


def _ident(pid: int) -> str:
    try:
        text = Path(f"/proc/{pid}/stat").read_text()
        ticks = text[text.rfind(")") + 2:].split()[19]
        boot = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
        return f"{boot}:{ticks}"
    except (OSError, IndexError):
        try:
            out = subprocess.run(["ps", "-o", "lstart=", "-p", str(pid)], capture_output=True, text=True, timeout=5)
            return f"ps:{out.stdout.strip()}"
        except (OSError, subprocess.SubprocessError):
            return ""


class Output:
    """Head up to `head` bytes in output.log; the last `tail` bytes (of everything) in output.tail."""

    def __init__(self, directory: Path, head: int, tail: int):
        self.head_cap, self.tail_cap = head, tail
        self.log = os.fdopen(os.open(directory / "output.log", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "wb")
        self.failed = False
        self.tail_path = directory / "output.tail"
        self.tail = bytearray()
        self.total = 0
        self.head_written = 0
        self._tail_at = 0.0
        self._tail_dirty = False

    def feed(self, chunk: bytes) -> None:
        self.total += len(chunk)
        room = self.head_cap - self.head_written
        if room > 0 and not self.failed:
            part = chunk[:room]
            try:
                self.log.write(part)
                self.log.flush()
                self.head_written += len(part)
            except OSError:               # disk full: keep draining the pipe (the agent must not block) and keep counting
                self.failed = True
        self.tail += chunk
        if len(self.tail) > self.tail_cap:
            del self.tail[: len(self.tail) - self.tail_cap]
        self._tail_dirty = True
        if time.monotonic() - self._tail_at > 2.0:
            self.flush_tail()

    def flush_tail(self) -> None:
        if self._tail_dirty and self.total > self.head_written:   # nothing is lost until the head overflows
            try:
                tmp = self.tail_path.with_name(".output.tail.tmp")
                tmp.write_bytes(bytes(self.tail))
                os.replace(tmp, self.tail_path)
            except OSError:
                pass
        self._tail_dirty = False
        self._tail_at = time.monotonic()

    def close(self) -> None:
        self.flush_tail()
        try:
            self.log.close()
        except OSError:
            pass

    @property
    def dropped(self) -> int:
        return max(0, self.total - self.head_written - len(self.tail)) if self.total > self.head_written else 0


def main(argv: list[str]) -> int:
    if os.fork() != 0:      # the launcher's child exits at once (and is reaped); the real shim is re-parented to init,
        os._exit(0)         # so it never becomes a zombie of an executor that may have died, and owns no pipe of it
    directory = Path(argv[1])
    spec_path = directory / "spec.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    spec_path.unlink()                                  # the prompt may be inside; it is also in prompt.txt
    started = time.time()
    state = {"cancel": False}
    for name in (signal.SIGTERM, signal.SIGINT):
        signal.signal(name, lambda *_: state.__setitem__("cancel", True))
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
    me = os.getpid()
    info = {"attempt_id": spec["attempt_id"], "pid": me, "pgid": os.getpgid(0), "ident": _ident(me),
            "started_at": started, "child_pid": None, "child_pgid": None, "child_ident": None}
    _atomic(directory / "shim.json", info)
    out = Output(directory, int(spec["head_bytes"]), int(spec["tail_bytes"]))
    reason, rc, error, child = "exited", None, "", None
    try:
        if state["cancel"] or (directory / "abort").exists():
            reason = "cancelled"
        else:
            try:
                child = subprocess.Popen(spec["argv"], stdin=subprocess.PIPE if spec.get("stdin") is not None
                                         else subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                         cwd=spec["cwd"], start_new_session=True, close_fds=True)
            except OSError as exc:
                reason, error = "spawn_error", f"{type(exc).__name__}: {exc.strerror or exc}"
        if child is not None:
            info.update(child_pid=child.pid, child_pgid=child.pid, child_ident=_ident(child.pid))
            _atomic(directory / "shim.json", info)
            descendants = DescendantRecorder(directory)

            def pump() -> None:
                while True:
                    try:
                        chunk = os.read(child.stdout.fileno(), 65536)
                    except OSError:
                        break
                    if not chunk:
                        break
                    out.feed(chunk)

            def feed_stdin() -> None:
                try:
                    child.stdin.write(spec["stdin"].encode("utf-8"))
                    child.stdin.close()
                except (OSError, ValueError):
                    pass

            reader = threading.Thread(target=pump, daemon=True)
            reader.start()
            if spec.get("stdin") is not None:
                threading.Thread(target=feed_stdin, daemon=True).start()
            deadline = time.monotonic() + float(spec["timeout_seconds"])
            stopping_since = None
            next_descendant_scan = 0.0
            while True:
                now = time.monotonic()
                if now >= next_descendant_scan:
                    descendants.capture(child.pid, info["child_ident"])
                    next_descendant_scan = now + DESCENDANT_SCAN_SECONDS
                if child.poll() is not None:
                    break
                if stopping_since is None and (state["cancel"] or time.monotonic() > deadline):
                    reason = "cancelled" if state["cancel"] else "timeout"
                    stopping_since = time.monotonic()
                    _kill(child.pid, signal.SIGTERM)
                elif stopping_since is not None and time.monotonic() - stopping_since > float(spec["grace_seconds"]):
                    _kill(child.pid, signal.SIGKILL)
                time.sleep(0.05)
            rc = child.returncode
            _kill(child.pid, signal.SIGKILL)            # nothing of the agent may outlive it and keep writing
            reader.join(timeout=5)
    finally:
        out.close()
    ended = time.time()
    _atomic(directory / "exit.json", {
        "attempt_id": spec["attempt_id"], "reason": reason, "returncode": rc, "error": error,
        "started_at": started, "ended_at": ended, "output_bytes": out.total, "head_bytes": out.head_written,
        "dropped_bytes": out.dropped, "child_pid": info["child_pid"]})
    return 0


def _kill(pgid: int, sig: int) -> None:
    try:
        os.killpg(pgid, sig)
    except (ProcessLookupError, PermissionError):
        pass


if __name__ == "__main__":
    sys.exit(main(sys.argv))
