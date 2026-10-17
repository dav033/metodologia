"""Fail-closed, bounded transport for read-only Git snapshot commands."""

from __future__ import annotations

import os
import selectors
import signal
import subprocess
import time
from pathlib import Path

from .contracts import QualityError

GIT_TIMEOUT_SECONDS = 20


def git_environment() -> dict[str, str]:
    return {
        "PATH": "/usr/bin:/bin",
        "HOME": "/nonexistent",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_ATTR_NOSYSTEM": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
    }


def run_git(
    repo: Path, *arguments: str, check: bool = True
) -> subprocess.CompletedProcess[str]:
    command = ["git", "-c", "core.hooksPath=/dev/null", "-c", "gc.auto=0", *arguments]
    try:
        result = subprocess.run(
            command,
            cwd=repo,
            env=git_environment(),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=GIT_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise QualityError(
            "SNAPSHOT_INVALID",
            f"git could not inspect M3 snapshot ({type(error).__name__})",
        ) from None
    if check and result.returncode:
        raise QualityError("SNAPSHOT_INVALID", "git could not inspect M3 snapshot")
    return result


def start_git_stream(
    repo: Path, command: list[str], description: str
) -> subprocess.Popen[bytes]:
    try:
        return subprocess.Popen(
            command,
            cwd=repo,
            env=git_environment(),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            close_fds=True,
        )
    except OSError as error:
        raise QualityError(
            "SNAPSHOT_INVALID",
            f"cannot start {description} ({type(error).__name__})",
        ) from None


def read_bounded_stream(
    stream,
    maximum: int,
    deadline: float,
    *,
    timeout_message: str,
    limit_message: str,
) -> bytes:
    chunks = bytearray()
    with selectors.DefaultSelector() as selector:
        os.set_blocking(stream.fileno(), False)
        selector.register(stream, selectors.EVENT_READ)
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise QualityError("SNAPSHOT_INVALID", timeout_message)
            if not selector.select(min(remaining, 1.0)):
                continue
            try:
                chunk = os.read(stream.fileno(), 65_536)
            except BlockingIOError:
                continue
            if not chunk:
                break
            chunks.extend(chunk)
            if len(chunks) > maximum:
                raise QualityError("SNAPSHOT_INVALID", limit_message)
    return bytes(chunks)


def wait_git_process(
    process: subprocess.Popen[bytes],
    deadline: float,
    *,
    timeout_message: str,
    failure_message: str,
) -> None:
    try:
        return_code = process.wait(timeout=max(0.1, deadline - time.monotonic()))
    except subprocess.TimeoutExpired as error:
        raise QualityError("SNAPSHOT_INVALID", timeout_message) from error
    if return_code != 0:
        raise QualityError("SNAPSHOT_INVALID", failure_message)


def stop_process(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
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
        process.wait(timeout=1)
