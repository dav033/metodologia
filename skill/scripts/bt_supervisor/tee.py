"""In-attempt helper, standard library only, run as a script under an isolated interpreter (`python -I tee.py ...`).

The supervisor copies this file into each attempt's state directory, so a running attempt never depends on the
repository checkout or on the uv environment that launched it. Three subcommands:

`run <attempt dir>`  (systemd ExecStart) — the unit's main process. Spawns the agent with EXACTLY the environment the
    caller gave (systemd's manager environment is filtered out), captures stdout+stderr with a size cap, writes
    `started.json` / `child.json`, and exits with the agent's status (re-raising its signal) so systemd's
    `ExecMainStatus`/`$EXIT_STATUS` describe the agent, not the wrapper.
`reap <attempt dir> <launch id>`  (pgroup) — double-forks away from the launcher, starts the agent as a new session leader, captures
    output, enforces `runtime_max_seconds`, kills stragglers when the leader exits (the analogue of
    `KillMode=control-group`) and writes `exit.json` with the true wait status. This is how exit codes survive the
    orchestrator's death: the reaper, not the orchestrator, is the agent's parent.
`exit-record <attempt dir>`  (systemd ExecStopPost) — writes `exit.json` from `$SERVICE_RESULT $EXIT_CODE $EXIT_STATUS`
    plus the cgroup's `memory.events` oom_kill counter. Runs even after SIGKILL, OOM and RuntimeMaxSec.

Output cap (both backends): `output.log` keeps the first `output_cap_bytes` bytes, then one marker line; `output.tail`
keeps the last `tail_bytes` of everything (rewritten atomically at most once a second, only after an overflow).
stdout and stderr are merged chronologically at LINE granularity: a partial line is held (≤64 KiB, ≤1 s) so a JSON
event on stdout is never split by a stderr chunk.
"""
from __future__ import annotations

import json
import os
import selectors
import signal
import subprocess
import sys
import time
import uuid
from pathlib import Path

MARKER = "BT_ATTEMPT_KEY"
LINE_HOLD_MAX = 64 * 1024
PARTIAL_FLUSH_SECONDS = 1.0
TAIL_FLUSH_SECONDS = 1.0
DRAIN_SECONDS = 2.0          # after the main process ends, a straggler may keep the pipe open: stop reading then
CLK_TCK = os.sysconf("SC_CLK_TCK")


# --------------------------------------------------------------------------------------------- small primitives
def atomic_json(path: Path, data: dict) -> None:
    """Write-then-rename with fsync of file and directory: a reader sees the old file or the whole new one."""
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(data, handle, sort_keys=True)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)
    try:
        dfd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    except OSError:
        pass


def read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def unlink(path: Path) -> None:
    try:
        path.unlink()
    except OSError:
        pass


def boot_id() -> str:
    try:
        return Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    except OSError:
        return "noboot"


def stat_fields(pid: int) -> tuple[str, int, int, float] | None:
    """(state, ppid, pgrp, start seconds since boot) from /proc/<pid>/stat, or None when it does not exist."""
    try:
        raw = Path(f"/proc/{pid}/stat").read_text()
        fields = raw[raw.rfind(")") + 2:].split()
        return fields[0], int(fields[1]), int(fields[2]), int(fields[19]) / CLK_TCK
    except (OSError, ValueError, IndexError):
        return None


def send(pid: int, start: float, sig: int) -> bool:
    """Signal through a pidfd after re-checking the start time: a recycled pid is never hit."""
    try:
        fd = os.pidfd_open(pid)
    except OSError:
        return False
    try:
        current = stat_fields(pid)
        if current is None or current[3] != start:
            return False
        signal.pidfd_send_signal(fd, sig)
        return True
    except OSError:
        return False
    finally:
        os.close(fd)


def scan(key: str, pgid: int | None = None) -> dict[int, float]:
    """Live (non-zombie) processes of this user that carry the attempt marker or belong to process group `pgid`."""
    needle, me, uid = f"{MARKER}={key}".encode(), os.getpid(), os.getuid()
    found: dict[int, float] = {}
    for entry in os.scandir("/proc"):
        if not entry.name.isdigit() or int(entry.name) == me:
            continue
        try:
            if entry.stat().st_uid != uid:
                continue
        except OSError:
            continue
        pid = int(entry.name)
        fields = stat_fields(pid)
        if fields is None or fields[0] in ("Z", "X"):
            continue
        if pgid is not None and fields[2] == pgid:
            found[pid] = fields[3]
            continue
        try:
            with open(f"/proc/{pid}/environ", "rb") as handle:
                environ = handle.read()
        except OSError:
            continue
        if needle in environ.split(b"\0"):
            found[pid] = fields[3]
    return found


# ------------------------------------------------------------------------------------------------ output capture
class Output:
    """Capped, line-preserving merge of stdout and stderr into `output.log` (head) + `output.tail` (rolling tail)."""

    def __init__(self, log_dir: Path, cap: int, tail_cap: int):
        log_dir.mkdir(parents=True, exist_ok=True)
        self.cap, self.tail_cap = cap, tail_cap
        self.log = os.fdopen(os.open(log_dir / "output.log", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "wb")
        self.tail_path = log_dir / "output.tail"
        self.tail = bytearray()
        self.total = self.head = 0
        self.failed = self.marked = False
        self.pending: dict[str, bytes] = {"stdout": b"", "stderr": b""}
        self.pending_since: dict[str, float] = {"stdout": 0.0, "stderr": 0.0}
        self._tail_at = 0.0
        self._tail_dirty = False

    def feed(self, stream: str, chunk: bytes) -> None:
        data = self.pending[stream] + chunk
        cut = data.rfind(b"\n") + 1
        if cut == 0 and len(data) < LINE_HOLD_MAX:
            self.pending[stream] = data
            self.pending_since[stream] = self.pending_since[stream] or time.monotonic()
            return
        cut = cut or len(data)
        self._write(data[:cut])
        self.pending[stream] = data[cut:]
        self.pending_since[stream] = time.monotonic() if self.pending[stream] else 0.0

    def note(self, text: str) -> None:
        self._write(text.encode("utf-8", "replace") + b"\n")

    def tick(self, final: bool = False) -> None:
        now = time.monotonic()
        for stream, since in self.pending_since.items():
            if self.pending[stream] and (final or now - since >= PARTIAL_FLUSH_SECONDS):
                data, self.pending[stream], self.pending_since[stream] = self.pending[stream], b"", 0.0
                self._write(data)
        if self._tail_dirty and (final or now - self._tail_at >= TAIL_FLUSH_SECONDS):
            self._flush_tail()

    def _write(self, data: bytes) -> None:
        self.total += len(data)
        room = self.cap - self.head
        if room > 0 and not self.failed:
            try:
                self.log.write(data[:room])
                self.log.flush()
                self.head += min(room, len(data))
            except OSError:              # disk full: keep draining (the agent must never block on a pipe) and counting
                self.failed = True
        if len(data) > room and not self.marked and not self.failed:
            self.marked = True
            try:
                self.log.write(f"\n[bt_supervisor] output exceeded {self.cap} bytes; only the last {self.tail_cap} "
                               f"bytes of the rest are kept, in output.tail\n".encode())
                self.log.flush()
            except OSError:
                self.failed = True
        self.tail += data
        if len(self.tail) > self.tail_cap:
            del self.tail[: len(self.tail) - self.tail_cap]
        self._tail_dirty = self.total > self.head      # nothing to keep apart until the head overflows

    def _flush_tail(self) -> None:
        try:
            tmp = self.tail_path.with_name(".output.tail.tmp")
            tmp.write_bytes(bytes(self.tail))
            os.replace(tmp, self.tail_path)
        except OSError:
            pass
        self._tail_dirty = False
        self._tail_at = time.monotonic()

    def close(self) -> None:
        self.tick(final=True)
        try:
            self.log.close()
        except OSError:
            pass

    def counters(self) -> dict:
        kept_tail = len(self.tail) if self.total > self.head else 0
        return {"output_bytes": self.total, "head_bytes": self.head,
                "dropped_bytes": max(0, self.total - self.head - kept_tail)}


class Pump:
    """Single-threaded reader of the agent's two pipes; `step` never blocks longer than `timeout`."""

    def __init__(self, child: subprocess.Popen, out: Output):
        self.out = out
        self.selector = selectors.DefaultSelector()
        self.files = {}               # fd -> file object: closed through the object, never by bare fd (no reuse race)
        for name, stream in (("stdout", child.stdout), ("stderr", child.stderr)):
            os.set_blocking(stream.fileno(), False)
            self.files[stream.fileno()] = stream
            self.selector.register(stream.fileno(), selectors.EVENT_READ, name)

    @property
    def eof(self) -> bool:
        return not self.selector.get_map()

    def step(self, timeout: float) -> None:
        if self.eof:
            time.sleep(timeout)
        else:
            for key, _ in self.selector.select(timeout):
                try:
                    chunk = os.read(key.fd, 65536)
                except BlockingIOError:
                    continue
                except OSError:
                    chunk = b""
                if chunk:
                    self.out.feed(key.data, chunk)
                else:
                    self.selector.unregister(key.fd)
                    self.files.pop(key.fd).close()
        self.out.tick()

    def drain(self) -> None:
        end = time.monotonic() + DRAIN_SECONDS
        while not self.eof and time.monotonic() < end:
            self.step(0.1)

    def close(self) -> None:
        for key in list(self.selector.get_map().values()):
            self.selector.unregister(key.fd)
            self.files.pop(key.fd).close()
        self.selector.close()


def _self_identity() -> dict:
    fields = stat_fields(os.getpid())
    return {"pid": os.getpid(), "start": fields[3] if fields else None, "boot_id": boot_id()}


def _own_cgroup() -> str | None:
    try:
        for line in Path("/proc/self/cgroup").read_text().splitlines():
            if line.startswith("0::"):
                return line[3:]
    except OSError:
        pass
    return None


def _open_stdin(adir: Path):
    """The stdin file, opened and already unlinked (the prompt is not kept at rest), or DEVNULL."""
    try:
        handle = open(adir / "stdin", "rb")  # noqa: SIM115 - handed to the child, closed by the caller
    except FileNotFoundError:
        return subprocess.DEVNULL
    unlink(adir / "stdin")
    return handle


def _spawn(spec: dict, env: dict, stdin, new_session: bool, out: Output) -> subprocess.Popen | str:
    try:
        return subprocess.Popen(spec["argv"], cwd=spec["cwd"], env=env, stdin=stdin, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, close_fds=True, start_new_session=new_session)
    except OSError as error:
        message = f"{type(error).__name__}: {error.strerror or error}"
        out.note(f"[bt_supervisor] could not start {spec['argv'][0]!r}: {message}")
        return message


def _signal_name(returncode: int | None) -> str | None:
    if returncode is None or returncode >= 0:
        return None
    try:
        return signal.Signals(-returncode).name
    except ValueError:
        return f"SIG{-returncode}"


# ----------------------------------------------------------------------------------------------- subcommands
def cmd_run(adir: Path) -> int:
    """systemd ExecStart. SIGTERM is NOT fatal here: KillMode=control-group delivers it to the agent directly, and
    the wrapper keeps draining until the agent is gone (systemd SIGKILLs everyone after TimeoutStopSec)."""
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(sig, lambda *_: None)
    spec = read_json(adir / "launch.json") or {}
    env = {name: os.environ[name] for name in spec.get("env_keys", []) if name in os.environ}
    env[MARKER] = spec["attempt_key"]
    unlink(adir / "env")          # secrets at rest only until the start: systemd has already read it
    stdin = _open_stdin(adir)     # not StandardInput=file: ExecStopPost would re-open it after we deleted it
    out = Output(Path(spec["log_dir"]), int(spec["output_cap_bytes"]), int(spec["tail_bytes"]))
    started = {**_self_identity(), "invocation_id": os.environ.get("INVOCATION_ID"), "control_group": _own_cgroup(),
               "started_at": time.time(), "child_pid": None, "child_start": None}
    child = _spawn(spec, env, stdin, False, out)
    if stdin is not subprocess.DEVNULL:
        stdin.close()
    if isinstance(child, str):
        out.close()
        atomic_json(adir / "started.json", started)
        atomic_json(adir / "child.json", {"returncode": None, "spawn_error": child, "ended_at": time.time(),
                                          **out.counters()})
        return 127
    fields = stat_fields(child.pid)
    atomic_json(adir / "started.json", {**started, "child_pid": child.pid, "child_start": fields[3] if fields else None})
    pump = Pump(child, out)
    while child.poll() is None:
        pump.step(0.25)
    pump.drain()
    pump.close()
    out.close()
    atomic_json(adir / "child.json", {"returncode": child.returncode, "spawn_error": None, "ended_at": time.time(),
                                      **out.counters()})
    if child.returncode < 0:      # mirror the agent's death so ExecMainStatus/EXIT_STATUS name its signal
        import resource
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        if -child.returncode not in (signal.SIGKILL, signal.SIGSTOP):
            signal.signal(-child.returncode, signal.SIG_DFL)
        os.kill(os.getpid(), -child.returncode)
        time.sleep(1)
        return 128 - child.returncode
    return child.returncode


def _leader_exited(pid: int) -> bool:
    """waitid(WNOWAIT): learn that the leader exited WITHOUT reaping it, so its pid — and therefore the pgid we are
    about to signal — cannot be recycled until the stragglers are dealt with."""
    try:
        return os.waitid(os.P_PID, pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is not None
    except ChildProcessError:
        return True


def _stop_tree(key: str, pgid: int, grace: float, pump: Pump) -> None:
    """SIGTERM(+SIGCONT, in case it is frozen) everything in the group or carrying the marker, wait `grace`, then
    SIGKILL in sweeps until nothing is left (a process forked between a scan and a kill is caught next sweep)."""
    targets = scan(key, pgid)
    if not targets:
        return
    for pid, start in targets.items():
        send(pid, start, signal.SIGTERM)
        send(pid, start, signal.SIGCONT)
    end = time.monotonic() + grace
    while time.monotonic() < end:
        pump.step(0.1)
        if not scan(key, pgid):
            return
    for _ in range(200):
        targets = scan(key, pgid)
        if not targets:
            return
        for pid, start in targets.items():
            send(pid, start, signal.SIGKILL)
        pump.step(0.05)


def cmd_reap(adir: Path, launch_id: str = "") -> int:
    if os.fork() != 0:            # the launcher's child exits at once; the reaper is re-parented (init/subreaper)
        os._exit(0)
    if (read_json(adir / "launch.json") or {}).get("launch_id") != launch_id:
        return 0                  # the attempt dir was wiped and re-prepared for another launch: not ours
    devnull = os.open(os.devnull, os.O_RDONLY)
    log = os.open(adir / "runner.log", os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    os.dup2(devnull, 0)
    os.dup2(log, 1)
    os.dup2(log, 2)
    flags = {"term": False}
    signal.signal(signal.SIGTERM, lambda *_: flags.__setitem__("term", True))
    signal.signal(signal.SIGINT, lambda *_: flags.__setitem__("term", True))
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
    reaper = _self_identity()
    atomic_json(adir / "reaper.json", reaper)
    spec = read_json(adir / "launch.json") or {}
    key, grace = spec["attempt_key"], float(spec["kill_grace_seconds"])
    env = dict(read_json(adir / "env.json") or {})
    env[MARKER] = key
    unlink(adir / "env.json")
    stdin = _open_stdin(adir)
    out = Output(Path(spec["log_dir"]), int(spec["output_cap_bytes"]), int(spec["tail_bytes"]))
    base = {"reaper_pid": reaper["pid"], "reaper_start": reaper["start"], "boot_id": reaper["boot_id"],
            "invocation_id": uuid.uuid4().hex, "started_at": time.time()}
    child = _spawn(spec, env, stdin, True, out)
    if stdin is not subprocess.DEVNULL:
        stdin.close()
    if isinstance(child, str):
        out.close()
        atomic_json(adir / "started.json", {**base, "child_pid": None, "child_start": None, "pgid": None})
        atomic_json(adir / "exit.json", {"backend": "pgroup", "reason": "spawn-error", "spawn_error": child,
                                         "returncode": None, "invocation_id": base["invocation_id"],
                                         "ended_at": time.time(), **out.counters()})
        return 0
    fields = stat_fields(child.pid)
    atomic_json(adir / "started.json", {**base, "child_pid": child.pid, "pgid": child.pid,
                                        "child_start": fields[3] if fields else None})
    runtime = spec.get("runtime_max_seconds")
    deadline = time.monotonic() + float(runtime) if runtime else None
    reason = "exited"
    pump = Pump(child, out)
    while not _leader_exited(child.pid):
        if flags["term"] or (adir / "terminate.json").exists():
            reason = "terminated"
            break
        if deadline is not None and time.monotonic() >= deadline:
            reason = "timeout"
            break
        pump.step(0.1)
    _stop_tree(key, child.pid, grace, pump)      # with the leader still unreaped, the pgid is still ours
    returncode = child.wait()
    if reason == "exited" and (flags["term"] or (adir / "terminate.json").exists()):
        reason = "terminated"
    pump.drain()
    pump.close()
    out.close()
    atomic_json(adir / "exit.json", {"backend": "pgroup", "reason": reason, "spawn_error": None,
                                     "returncode": returncode, "signal": _signal_name(returncode),
                                     "invocation_id": base["invocation_id"], "ended_at": time.time(),
                                     **out.counters()})
    return 0


def cmd_exit_record(adir: Path) -> int:
    """Never fails: a failing ExecStopPost must not change how systemd reports the attempt."""
    try:
        oom = None
        group = _own_cgroup()
        if group:
            try:
                for line in Path(f"/sys/fs/cgroup{group}/memory.events").read_text().splitlines():
                    name, _, value = line.partition(" ")
                    if name == "oom_kill":
                        oom = int(value)
            except (OSError, ValueError):
                pass
        atomic_json(adir / "exit.json", {
            "backend": "systemd", "service_result": os.environ.get("SERVICE_RESULT"),
            "exit_kind": os.environ.get("EXIT_CODE"), "exit_status": os.environ.get("EXIT_STATUS"),
            "invocation_id": os.environ.get("INVOCATION_ID"), "oom_kill": oom, "ended_at": time.time()})
    except Exception as error:  # noqa: BLE001 - report and exit 0, see docstring
        print(f"bt_supervisor exit-record failed: {type(error).__name__}: {error}", file=sys.stderr)
    return 0


def main(argv: list[str]) -> int:
    if len(argv) == 4 and argv[1] == "reap":
        return cmd_reap(Path(argv[2]), argv[3])
    commands = {"run": cmd_run, "exit-record": cmd_exit_record}
    if len(argv) != 3 or argv[1] not in commands:
        print("usage: tee.py run|exit-record <attempt dir> | tee.py reap <attempt dir> <launch id>", file=sys.stderr)
        return 2
    return commands[argv[1]](Path(argv[2]))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
