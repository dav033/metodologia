"""Bubblewrap process setup, bounded output collection, and verdict mapping."""

from __future__ import annotations

import json
import os
import selectors
import signal
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from .policy import CheckSpec, QualityPolicy
from .runner_sandbox_process import NAMESPACE_FIELDS, SandboxSession, sandbox_available
from .runner_types import CommandOutcome
from .sandbox_mounts import Mount


@dataclass
class _Collection:
    streams: dict[str, bytearray] = field(
        default_factory=lambda: {"stdout": bytearray(), "stderr": bytearray()}
    )
    info_buffer: bytearray = field(default_factory=bytearray)
    namespaces: tuple[tuple[str, int], ...] = ()
    handshake: bool = False
    timed_out: bool = False
    output_exceeded: bool = False
    sandbox_failed: bool = False
    eof: set[str] = field(default_factory=set)
    return_code: int = 125
    command_started: bool = False
    stdout: bytes = b""
    stderr: bytes = b""


class SandboxExecution:
    """Own one bubblewrap process and convert its observed result to a safe outcome."""

    def __init__(
        self,
        policy: QualityPolicy,
        make_outcome: Callable[..., CommandOutcome],
        redact: Callable[[bytes], bytes],
    ):
        self.policy = policy
        self.make_outcome = make_outcome
        self.redact = redact

    def execute(
        self,
        check: CheckSpec,
        root: Path,
        timeout: int,
        started: float,
        mounts: tuple[Mount, ...] = (),
    ) -> CommandOutcome:
        if not sandbox_available(self.policy):
            return self.make_outcome(
                "unknown", None, started, b"", b"", "SANDBOX_UNAVAILABLE", False
            )
        session = SandboxSession()
        try:
            session.start(check, root, self.policy, mounts)
            collected = self._collect(session, started, timeout)
            return self._to_outcome(collected, started)
        except (OSError, subprocess.SubprocessError, ValueError, TypeError):
            if session.process is not None:
                _terminate(session.process)
            return self.make_outcome(
                "unknown", None, started, b"", b"", "SANDBOX_UNAVAILABLE", False
            )
        finally:
            session.close()

    def _collect(
        self, session: SandboxSession, started: float, timeout: int
    ) -> _Collection:
        if session.process is None or session.selector is None:
            raise OSError("sandbox process did not start")
        state = _Collection()
        deadline = started + timeout
        setup_deadline = min(deadline, time.monotonic() + 5)
        while session.selector.get_map():
            if self._deadline_reached(session, state, deadline, setup_deadline):
                break
            events = self._wait_for_events(
                session.selector, state, deadline, setup_deadline
            )
            for key, _ in events:
                self._consume_event(session, state, key)
                if state.sandbox_failed or state.output_exceeded:
                    break
            if state.sandbox_failed or state.output_exceeded:
                break
        if session.process.poll() is None:
            _terminate(session.process)
        state.return_code = session.process.wait(timeout=2)
        self._finish_streams(session.start_marker, state)
        return state

    def _deadline_reached(
        self,
        session: SandboxSession,
        state: _Collection,
        deadline: float,
        setup_deadline: float,
    ) -> bool:
        now = time.monotonic()
        if now >= deadline:
            state.timed_out = state.handshake
            state.sandbox_failed = not state.handshake
        elif not state.handshake and now >= setup_deadline:
            state.sandbox_failed = True
        if state.timed_out or state.sandbox_failed:
            if session.process is not None:
                _terminate(session.process)
            return True
        return False

    def _wait_for_events(
        self,
        selector: selectors.BaseSelector,
        state: _Collection,
        deadline: float,
        setup_deadline: float,
    ) -> list[tuple[selectors.SelectorKey, int]]:
        remaining = deadline - time.monotonic()
        setup_remaining = setup_deadline - time.monotonic()
        wait_for = min(
            remaining, 0.1, setup_remaining if not state.handshake else remaining
        )
        return selector.select(max(0, wait_for))

    def _consume_event(
        self,
        session: SandboxSession,
        state: _Collection,
        key: selectors.SelectorKey,
    ) -> None:
        try:
            chunk = os.read(key.fd, 65_536)
        except BlockingIOError:
            return
        except OSError:
            chunk = b""
        if not chunk:
            self._mark_eof(session, state, key)
        elif key.data == "info":
            self._consume_info(session, state, key, chunk)
        else:
            self._consume_output(session, state, key.data, chunk)

    def _mark_eof(
        self,
        session: SandboxSession,
        state: _Collection,
        key: selectors.SelectorKey,
    ) -> None:
        if session.selector is not None:
            session.selector.unregister(key.fileobj)
        state.eof.add(key.data)
        if key.data == "info" and not state.handshake:
            state.sandbox_failed = True

    def _consume_info(
        self,
        session: SandboxSession,
        state: _Collection,
        key: selectors.SelectorKey,
        chunk: bytes,
    ) -> None:
        state.info_buffer.extend(chunk)
        if len(state.info_buffer) > 65_536:
            state.sandbox_failed = True
            _terminate(session.process)
            return
        try:
            info_value = json.loads(state.info_buffer.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            return
        namespaces = _validate_namespaces(info_value)
        if not namespaces:
            state.sandbox_failed = True
            _terminate(session.process)
            return
        state.handshake = True
        state.namespaces = namespaces
        if session.selector is not None:
            session.selector.unregister(key.fileobj)
        state.eof.add("info")
        self._close_info_fd(session)
        self._release_launcher(session, state)

    def _close_info_fd(self, session: SandboxSession) -> None:
        if session.info_read is not None:
            os.close(session.info_read)
            session.info_read = None

    def _release_launcher(self, session: SandboxSession, state: _Collection) -> None:
        if session.process is None or session.process.stdin is None:
            state.sandbox_failed = True
            return
        try:
            session.process.stdin.write(b"\x01")
            session.process.stdin.flush()
        except (BrokenPipeError, OSError):
            state.sandbox_failed = True
            _terminate(session.process)
            return
        session.process.stdin.close()

    def _consume_output(
        self,
        session: SandboxSession,
        state: _Collection,
        stream_name: str,
        chunk: bytes,
    ) -> None:
        current_size = sum(len(value) for value in state.streams.values())
        remaining = self.policy.max_output_bytes - current_size
        state.streams[stream_name].extend(chunk[: max(0, remaining)])
        if len(chunk) > remaining:
            state.output_exceeded = True
            _terminate(session.process)

    def _finish_streams(self, marker: str, state: _Collection) -> None:
        raw_stdout = bytes(state.streams["stdout"])
        raw_stderr = bytes(state.streams["stderr"])
        marker_bytes = (marker + "\n").encode("ascii")
        state.command_started = marker_bytes in raw_stderr
        raw_stderr = raw_stderr.replace(marker_bytes, b"")
        stdout, stderr = self.redact(raw_stdout), self.redact(raw_stderr)
        state.stdout, state.stderr = _fit_output(
            stdout, stderr, self.policy.max_output_bytes
        )

    def _to_outcome(self, state: _Collection, started: float) -> CommandOutcome:
        if state.sandbox_failed or not state.handshake:
            return self.make_outcome(
                "unknown",
                None,
                started,
                state.stdout,
                state.stderr,
                "SANDBOX_UNAVAILABLE",
                False,
                state.output_exceeded,
                (),
            )
        if state.timed_out:
            return self.make_outcome(
                "unknown",
                None,
                started,
                state.stdout,
                state.stderr,
                "CHECK_TIMEOUT",
                True,
                state.output_exceeded,
                state.namespaces,
            )
        if state.output_exceeded:
            return self.make_outcome(
                "unknown",
                None,
                started,
                state.stdout,
                state.stderr,
                "OUTPUT_LIMIT",
                True,
                True,
                state.namespaces,
            )
        return self._command_outcome(state, started)

    def _command_outcome(self, state: _Collection, started: float) -> CommandOutcome:
        if not state.command_started:
            return self.make_outcome(
                "unknown",
                None,
                started,
                state.stdout,
                state.stderr,
                "CHECK_UNAVAILABLE",
                True,
                False,
                state.namespaces,
            )
        if state.return_code in (124, 125, 126, 127):
            return self.make_outcome(
                "unknown",
                state.return_code,
                started,
                state.stdout,
                state.stderr,
                "CHECK_UNAVAILABLE",
                True,
                False,
                state.namespaces,
            )
        status = "pass" if state.return_code == 0 else "fail"
        return self.make_outcome(
            status,
            state.return_code,
            started,
            state.stdout,
            state.stderr,
            None,
            True,
            False,
            state.namespaces,
        )


def _validate_namespaces(value: object) -> tuple[tuple[str, int], ...]:
    if not isinstance(value, dict):
        return ()
    found: list[tuple[str, int]] = []
    for name, field_name in NAMESPACE_FIELDS.items():
        namespace_id = value.get(field_name)
        if not isinstance(namespace_id, int) or isinstance(namespace_id, bool):
            return ()
        if namespace_id <= 0 or _matches_host_namespace(name, namespace_id):
            return ()
        found.append((name, namespace_id))
    child_pid = value.get("child-pid")
    if not isinstance(child_pid, int) or isinstance(child_pid, bool) or child_pid <= 0:
        return ()
    return tuple(found)


def _matches_host_namespace(name: str, namespace_id: int) -> bool:
    try:
        return namespace_id == os.stat(f"/proc/self/ns/{name}").st_ino
    except OSError:
        return True


def _fit_output(stdout: bytes, stderr: bytes, maximum: int) -> tuple[bytes, bytes]:
    stdout = stdout[:maximum]
    return stdout, stderr[: max(0, maximum - len(stdout))]


def _terminate(process: subprocess.Popen[bytes] | None) -> None:
    if process is None or process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=0.25)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            pass
