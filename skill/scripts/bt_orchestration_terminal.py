"""Foreground milestone process lifecycle; provider decisions belong to the runtime adapter.

Workers retain their separate sessions. A reasoning child receives its own foreground
process group in the supervisor's controlling terminal/session; the group is reclaimed.
"""
from __future__ import annotations

import os
import selectors
import signal
import subprocess
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from bt_orchestration_context import encode


class TerminalError(ValueError):
    """Foreground execution cannot be established safely."""


@dataclass(frozen=True)
class ForegroundRuntime:
    """External reasoning boundary consumed by the existing deterministic supervisor."""

    run_session: Callable
    session_route: Callable
    check_capabilities: Callable
    version: int = 1


def require_foreground(fd: int = 0) -> None:
    if not all(hasattr(os, name) for name in ('tcgetpgrp', 'tcsetpgrp', 'waitid', 'WNOWAIT')):
        raise TerminalError('FOREGROUND_JOB_CONTROL_UNAVAILABLE: this platform lacks required POSIX lifecycle support')
    try:
        if not os.isatty(fd) or os.tcgetpgrp(fd) != os.getpgrp():
            raise TerminalError("CONTROLLING_TTY_REQUIRED: run from the foreground terminal")
        with open('/dev/tty', 'rb', buffering=0):
            pass
    except OSError as exc:
        raise TerminalError("CONTROLLING_TTY_REQUIRED: no accessible controlling terminal") from exc


def preflight(runtime: ForegroundRuntime | None) -> ForegroundRuntime:
    if not isinstance(runtime, ForegroundRuntime):
        raise TerminalError(
            "FOREGROUND_RUNTIME_NOT_ACTIVATED: the bounded reasoning/action adapter is required "
            "(REQ-008 T4); no native-tool fallback or existing-session replacement was attempted"
        )
    if type(runtime.version) is not int or runtime.version != 1:
        raise TerminalError('INVALID_FOREGROUND_RUNTIME: unsupported boundary version')
    if not all(callable(value) for value in (runtime.run_session, runtime.session_route, runtime.check_capabilities)):
        raise TerminalError("INVALID_FOREGROUND_RUNTIME: capability and dispatch boundaries are required")
    require_foreground()
    runtime.check_capabilities()
    return runtime


def configured_runtime() -> ForegroundRuntime | None:
    from bt_orchestration_provider import check_capabilities
    from bt_orchestration_runtime import run_session, session_route
    return ForegroundRuntime(run_session, session_route, check_capabilities)


def _exited(child: subprocess.Popen) -> bool:
    return child.returncode is not None or os.waitid(os.P_PID, child.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is not None


def _stop(child: subprocess.Popen) -> None:
    if child.returncode is not None:
        return
    # Keep the leader unreaped until containment is complete. Its PID/PGID cannot
    # be reused even when it exited before a descendant closed stdout or the TTY.
    if os.getpgid(child.pid) != child.pid or child.pid == os.getpgrp():
        raise TerminalError('CHILD_GROUP_OWNERSHIP_LOST: no unrelated group was signalled')
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(child.pid, sig)
        except ProcessLookupError:
            pass
        if sig == signal.SIGTERM:
            time.sleep(.15)
    child.wait(timeout=1)


def run_child(argv: list[str], package: dict, workdir: Path, environ: dict[str, str], *,
              timeout: float, output_bytes: int, input_bytes: int = 16384,
              should_stop: Callable[[], bool] = lambda: False, on_start: Callable | None = None,
              send_input: bool = True) -> dict:
    """Run a fresh bounded child, restoring terminal and handlers even on failed startup.

The provider adapter must validate inventory and structured output before dispatching
actions. This transport's instance ID is not evidence of a provider conversation ID.
"""
    require_foreground()
    if (not isinstance(argv, list) or not argv or not argv[0] or any(not isinstance(a, str) or '\0' in a for a in argv)
            or not Path(argv[0]).is_absolute() or not os.access(argv[0], os.X_OK)):
        raise TerminalError("INVALID_CHILD_ARGV: use an absolute executable and argument list")
    if timeout <= 0 or type(output_bytes) is not int or output_bytes < 1:
        raise TerminalError("INVALID_CHILD_LIMITS")
    payload = encode(package).encode('utf-8') if send_input else b''
    if len(payload) > input_bytes:
        raise TerminalError("OVERSIZED_CHILD_INPUT: mandatory scope was not truncated")
    import termios

    saved = termios.tcgetattr(0)
    foreground = os.tcgetpgrp(0)
    handlers = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGTTOU)}
    interrupted: list[int] = []
    for sig in handlers:
        signal.signal(sig, signal.SIG_IGN if sig == signal.SIGTTOU else
                      lambda received, _frame: interrupted.append(received))
    started, instance = time.monotonic(), str(uuid.uuid4())
    child = None
    output = bytearray()
    timed_out = overflow = stopped = False
    try:
        child = subprocess.Popen(argv, cwd=workdir, env={**environ, 'BITACORA_ORCHESTRATOR_INSTANCE': instance},
                                 stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, process_group=0)
        os.tcsetpgrp(0, child.pid)
        # A provider can read /dev/tty before Popen returns and stop on SIGTTIN.
        os.killpg(child.pid, signal.SIGCONT)
        if on_start:
            on_start(child.pid, instance)
        with selectors.DefaultSelector() as selector:
            os.set_blocking(child.stdin.fileno(), False)
            os.set_blocking(child.stdout.fileno(), False)
            selector.register(child.stdin, selectors.EVENT_WRITE)
            selector.register(child.stdout, selectors.EVENT_READ)
            offset = 0
            while selector.get_map():
                stopped = bool(interrupted) or should_stop()
                timed_out = time.monotonic() - started >= timeout
                if stopped or timed_out or overflow:
                    _stop(child)
                    break
                for key, _events in selector.select(.05):
                    if key.fileobj is child.stdin:
                        try:
                            offset += os.write(child.stdin.fileno(), payload[offset:])
                        except BrokenPipeError:
                            offset = len(payload)
                        if offset == len(payload):
                            selector.unregister(child.stdin)
                            child.stdin.close()
                    else:
                        chunk = os.read(child.stdout.fileno(), min(4096, output_bytes + 1 - len(output)))
                        if not chunk:
                            selector.unregister(child.stdout)
                        else:
                            output.extend(chunk)
                            overflow = len(output) > output_bytes
                            if overflow:
                                break
            while not _exited(child):
                stopped = bool(interrupted) or should_stop()
                timed_out = time.monotonic() - started >= timeout
                if stopped or timed_out or overflow:
                    _stop(child)
                    break
                time.sleep(.05)
    finally:
        try:
            if child is not None:
                _stop(child)
                for stream in (child.stdin, child.stdout):
                    if stream is not None and not stream.closed:
                        stream.close()
        finally:
            try:
                os.tcsetpgrp(0, foreground)
                termios.tcsetattr(0, termios.TCSANOW, saved)
            finally:
                for sig, handler in handlers.items():
                    signal.signal(sig, handler)
    stopped = stopped or bool(interrupted) or (
        not timed_out and not overflow and child.returncode in (-signal.SIGINT, 128 + signal.SIGINT))
    return {'transport_schema': 1, 'rc': child.returncode, 'text': bytes(output[:output_bytes]).decode('utf-8', errors='replace'),
            'timed_out': timed_out, 'overflow': overflow, 'stopped': stopped,
            'signal': interrupted[0] if interrupted else None, 'instance_id': instance,
            'pid': child.pid, 'seconds': time.monotonic() - started}
