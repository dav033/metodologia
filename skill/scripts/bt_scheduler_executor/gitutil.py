"""One way to run git: no prompts, no hooks, no inherited repository/index variables, bounded time."""
from __future__ import annotations

import os
import subprocess
import time
from collections.abc import Mapping, Sequence
from pathlib import Path

from .errors import ExecutorError

GIT_TIMEOUT = 120.0
_STRIP = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
          "GIT_COMMON_DIR", "GIT_NAMESPACE", "GIT_PREFIX")


def git_env(extra: Mapping[str, str] | None = None) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in _STRIP}
    env.update({"GIT_TERMINAL_PROMPT": "0", "GIT_OPTIONAL_LOCKS": "0", "LC_ALL": "C"})
    if extra:
        env.update(extra)
    return env


def run(cwd: Path | str, args: Sequence[str], *, env: Mapping[str, str] | None = None, check: bool = True,
        timeout: float = GIT_TIMEOUT, binary: bool = False, code: str = "WORKSPACE_ERROR"):
    """Run `git -c core.hooksPath=/dev/null <args>`; returns stdout (text unless `binary`)."""
    cmd = ["git", "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false", "-c", "gc.auto=0", *args]
    try:
        done = subprocess.run(cmd, cwd=str(cwd), env=git_env(env), capture_output=True, timeout=timeout, check=False)
    except (OSError, subprocess.SubprocessError) as error:
        raise ExecutorError(code, f"git {args[0] if args else ''}: {type(error).__name__}") from None
    if check and done.returncode:
        message = done.stderr.decode("utf-8", "replace").strip() or done.stdout.decode("utf-8", "replace").strip()
        raise ExecutorError(code, f"git {' '.join(args[:3])} failed: {message[:300]}")
    return done.stdout if binary else done.stdout.decode("utf-8", "replace").strip()


def run_capped(cwd: Path | str, args: Sequence[str], cap: int, timeout: float = GIT_TIMEOUT) -> bytes | None:
    """stdout of a git command, or None as soon as it exceeds `cap` bytes (the process is stopped, nothing is buffered
    beyond the cap)."""
    cmd = ["git", "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false", *args]
    try:
        proc = subprocess.Popen(cmd, cwd=str(cwd), env=git_env(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError as error:
        raise ExecutorError("WORKSPACE_ERROR", f"git {args[0]}: {type(error).__name__}") from None
    out, over, deadline = bytearray(), False, time.monotonic() + timeout
    try:
        while True:
            chunk = proc.stdout.read(65536)
            if not chunk:
                break
            out += chunk
            if len(out) > cap:
                over = True
                break
            if time.monotonic() > deadline:
                raise ExecutorError("WORKSPACE_ERROR", f"git {args[0]} timed out")
    finally:
        if over or proc.poll() is None:
            proc.kill()
        proc.stdout.close()
        err = proc.stderr.read()[:300] if not over else b""
        proc.stderr.close()
        proc.wait()
    if over:
        return None
    if proc.returncode:
        raise ExecutorError("WORKSPACE_ERROR", f"git {' '.join(args[:3])} failed: {err.decode('utf-8', 'replace').strip()}")
    return bytes(out)


def ok(cwd: Path | str, args: Sequence[str]) -> bool:
    """True when `git <args>` exits 0 (any failure, including a missing git, is False)."""
    try:
        done = subprocess.run(["git", "-c", "core.hooksPath=/dev/null", *args], cwd=str(cwd), env=git_env(),
                              capture_output=True, timeout=GIT_TIMEOUT, check=False)
    except (OSError, subprocess.SubprocessError):
        return False
    return done.returncode == 0
