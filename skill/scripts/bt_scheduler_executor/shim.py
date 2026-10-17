"""Detached supervisor of ONE agent process (double-forked: it is re-parented to init, no longer a session leader). Runs as a script (`python shim.py <attempt dir>`), standard library only.

Why a shim: if the executor owned the agent directly, an executor restart would lose the pipe, the exit status and the
ability to stop it. The shim lives in its own session, owns the agent's process group, enforces the timeout, keeps the
output (head up to a cap + a tail window), and writes `exit.json` atomically as its last act. Everything the executor
needs after a restart is therefore on disk.

Files in the attempt directory: `spec.json` (read once, then removed: it may carry the prompt), `shim.json` (identity of
the shim and, once spawned, of the agent), `output.log` (head), `output.tail` (last window), `exit.json` (final).
"""
from __future__ import annotations

import errno
import json
import os
import selectors
import signal
import struct
import subprocess
import sys
import threading
import time
from pathlib import Path

DESCENDANT_LIMIT = 4096
DESCENDANT_SCAN_PROCESS_LIMIT = 16384
DESCENDANT_SCAN_SECONDS = 0.1
STREAM_MAGIC = b"BTM4"
STREAM_VERSION = 1
STREAM_MAX_DATA = 3840
STREAM_READER_STARTUP_GRACE_SECONDS = 0.5
STREAM_HEADER = struct.Struct("!4sBBHQQ")
STREAMS = {"stdout": 1, "stderr": 2}


def encode_stream_frame(stream: str, sequence: int, offset: int, data: bytes) -> bytes:
    """Encode one atomic FIFO frame; the binary header and payload fit within Linux PIPE_BUF."""
    if stream not in STREAMS or not 0 <= sequence < 1 << 64 or not 0 <= offset < 1 << 64:
        raise ValueError("invalid stream frame metadata")
    if not isinstance(data, bytes) or len(data) > STREAM_MAX_DATA:
        raise ValueError("stream frame payload exceeds 3840 bytes")
    return encode_stream_frame_id(STREAMS[stream], sequence, offset, data)


def encode_stream_frame_id(stream_id: int, sequence: int, offset: int, data: bytes) -> bytes:
    if stream_id not in (1, 2, 3, 4) or len(data) > STREAM_MAX_DATA:
        raise ValueError("invalid stream frame")
    return STREAM_HEADER.pack(STREAM_MAGIC, STREAM_VERSION, stream_id, len(data), sequence, offset) + data


def decode_stream_frame(raw: bytes) -> tuple[str, int, int, bytes]:
    if len(raw) < STREAM_HEADER.size:
        raise ValueError("truncated stream frame header")
    magic, version, stream_id, size, sequence, offset = STREAM_HEADER.unpack(raw[:STREAM_HEADER.size])
    if magic != STREAM_MAGIC or version != STREAM_VERSION or stream_id not in (1, 2):
        raise ValueError("unsupported stream frame header")
    if size > STREAM_MAX_DATA or len(raw) != STREAM_HEADER.size + size:
        raise ValueError("invalid stream frame length")
    return ("stdout" if stream_id == 1 else "stderr"), sequence, offset, raw[STREAM_HEADER.size:]


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
            out = subprocess.run(["ps", "-o", "lstart=", "-p", str(pid)], capture_output=True, text=True,
                                 timeout=5, check=False)
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


class StreamTap:
    """Best-effort nonblocking FIFO writer; output artifact draining never depends on a monitor reader."""

    def __init__(self, directory: Path):
        self.path = directory / "stream.fifo"
        self.fd: int | None = None
        self.streams = {name: {"read": 0, "sent": 0, "dropped": 0, "sequence": 0, "offset": 0,
                               "ranges": [], "pending": None} for name in STREAMS}
        self.directory = directory
        self.reader_deadline = time.monotonic() + STREAM_READER_STARTUP_GRACE_SECONDS
        self.lock = threading.Lock()
        self.persist_lock = threading.Lock()
        self.stop_summary = threading.Event()
        self.summary_thread = threading.Thread(target=self._summary_loop, daemon=True, name="m3-stream-summary")
        self.summary_thread.start()

    def feed(self, name: str, chunk: bytes) -> None:
        with self.lock:
            state = self.streams[name]
            state["read"] += len(chunk)
            for start in range(0, len(chunk), STREAM_MAX_DATA):
                data = chunk[start:start + STREAM_MAX_DATA]
                seq, offset = state["sequence"], state["offset"]
                state["sequence"] += 1
                state["offset"] += len(data)
                pending = state["pending"]
                if pending is not None:
                    gap_data = struct.pack("!QQ", pending["dropped_bytes"], pending["dropped_frames"])
                    gap_id = 3 if name == "stdout" else 4
                    if self._write(encode_stream_frame_id(gap_id, pending["first_sequence"], pending["first_offset"], gap_data)):
                        state["pending"] = None
                if state["pending"] is not None:
                    self._drop(state, seq, offset, len(data))
                    continue
                if self._write(encode_stream_frame(name, seq, offset, data)):
                    state["sent"] += len(data)
                else:
                    self._drop(state, seq, offset, len(data))

    def _write(self, frame: bytes) -> bool:
        try:
            while self.fd is None:
                try:
                    self.fd = os.open(self.path, os.O_WRONLY | os.O_NONBLOCK | getattr(os, "O_CLOEXEC", 0))
                except OSError as error:
                    if error.errno != errno.ENXIO or time.monotonic() >= self.reader_deadline:
                        raise
                    time.sleep(min(0.01, self.reader_deadline - time.monotonic()))
            written = os.write(self.fd, frame)
            if written != len(frame):
                raise OSError("partial atomic FIFO write")
            return True
        except OSError:
            if self.fd is not None:
                try:
                    os.close(self.fd)
                except OSError:
                    pass
                self.fd = None
            return False

    @staticmethod
    def _drop(state: dict, sequence: int, offset: int, size: int) -> None:
        state["dropped"] += size
        ranges = state["ranges"]
        if ranges and ranges[-1]["last_sequence"] + 1 == sequence:
            item = ranges[-1]
            item["last_sequence"], item["last_offset"] = sequence, offset + size
            item["dropped_bytes"] += size
            item["dropped_frames"] += 1
        elif len(ranges) < 64:
            ranges.append({"first_sequence": sequence, "last_sequence": sequence, "first_offset": offset,
                           "last_offset": offset + size, "dropped_bytes": size, "dropped_frames": 1})
        else:
            item = ranges[-1]
            item["last_sequence"], item["last_offset"] = sequence, offset + size
            item["dropped_bytes"] += size
            item["dropped_frames"] += 1
        pending = state["pending"]
        if pending is None:
            state["pending"] = {"first_sequence": sequence, "first_offset": offset,
                                "dropped_bytes": size, "dropped_frames": 1}
        else:
            pending["dropped_bytes"] += size
            pending["dropped_frames"] += 1

    def _summary(self) -> dict:
        with self.lock:
            def snapshot(name: str) -> dict:
                state = self.streams[name]
                copied = {key: value for key, value in state.items() if key not in ("ranges", "pending")}
                copied["ranges"] = [dict(item) for item in state["ranges"]]
                copied["pending"] = dict(state["pending"]) if state["pending"] is not None else None
                return copied

            return {"schema_version": "1.0.0", "stream_ref": "stream.fifo",
                    "stdout": snapshot("stdout"), "stderr": snapshot("stderr")}

    def persist(self) -> None:
        with self.persist_lock:
            try:
                _atomic(self.directory / "stream.json", self._summary())
            except OSError:
                pass

    def _summary_loop(self) -> None:
        while not self.stop_summary.wait(0.25):
            self.persist()

    def close(self) -> None:
        self.stop_summary.set()
        self.summary_thread.join(timeout=1)
        if self.fd is not None:
            try:
                os.close(self.fd)
            except OSError:
                pass
            self.fd = None
        self.persist()


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
    stream_tap = StreamTap(directory)
    reason, rc, error, child = "exited", None, "", None
    try:
        if state["cancel"] or (directory / "abort").exists():
            reason = "cancelled"
        else:
            try:
                child = subprocess.Popen(spec["argv"], stdin=subprocess.PIPE if spec.get("stdin") is not None
                                         else subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                         cwd=spec["cwd"], start_new_session=True, close_fds=True)
            except OSError as exc:
                reason, error = "spawn_error", f"{type(exc).__name__}: {exc.strerror or exc}"
        if child is not None:
            info.update(child_pid=child.pid, child_pgid=child.pid, child_ident=_ident(child.pid))
            _atomic(directory / "shim.json", info)
            descendants = DescendantRecorder(directory)

            def pump() -> None:
                selector = selectors.DefaultSelector()
                selector.register(child.stdout, selectors.EVENT_READ, "stdout")
                selector.register(child.stderr, selectors.EVENT_READ, "stderr")
                streams = {"stdout": child.stdout, "stderr": child.stderr}
                try:
                    while streams:
                        for key, _ in selector.select(timeout=0.5):
                            name = key.data
                            try:
                                chunk = os.read(key.fd, 65536)
                            except OSError:
                                chunk = b""
                            if not chunk:
                                selector.unregister(streams.pop(name))
                                continue
                            out.feed(chunk)
                            stream_tap.feed(name, chunk)
                finally:
                    selector.close()

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
        stream_tap.close()
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
