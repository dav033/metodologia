"""Evidence checks shared by the opt-in T24 experiment and its offline contract tests."""
from __future__ import annotations

import os
import subprocess
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Protocol


class _Snapshot(Protocol):
    status: str


class _Scheduler(Protocol):
    def step(self) -> object: ...
    def snapshot(self) -> _Snapshot: ...


class _Executor(Protocol):
    def wait_idle(self, timeout: float = 30.0) -> bool: ...


def changed_paths(workspace: Path) -> tuple[str, ...]:
    """Return tracked and non-ignored untracked edits relative to the task worktree's HEAD."""
    commands = (
        ["git", "diff", "--name-only", "--no-renames", "-z", "HEAD", "--"],
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
    )
    paths: set[str] = set()
    for command in commands:
        result = subprocess.run(command, cwd=workspace, capture_output=True, timeout=10, check=False)
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, command, output=result.stdout, stderr=result.stderr)
        paths.update(os.fsdecode(path) for path in result.stdout.split(b"\0") if path)
    return tuple(sorted(paths))


def workspace_scope(workspace: Path, expected_paths: Sequence[str]) -> tuple[bool, tuple[str, ...], tuple[str, ...]]:
    root = workspace.resolve()
    present = True
    for relative in expected_paths:
        path = workspace / relative
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root):
            present = False
            break
        if any(parent.is_symlink() for parent in path.parents if parent != workspace.parent and parent.is_relative_to(workspace)):
            present = False
            break
    changed = changed_paths(workspace)
    undeclared = tuple(path for path in changed if path not in expected_paths)
    return present and not undeclared, changed, undeclared


def attempt_task_id(attempt: Mapping[str, object], task_rows: Mapping[str, Mapping[str, object]]) -> str | None:
    request = attempt.get("request") if isinstance(attempt.get("request"), dict) else {}
    requested = request.get("task_id")
    route = attempt.get("route") if isinstance(attempt.get("route"), dict) else {}
    executor_ref = route.get("reference")
    matched = [task_id for task_id, row in task_rows.items()
               if isinstance(executor_ref, str) and row.get("executor") == executor_ref]
    if len(matched) > 1:
        return None
    if isinstance(requested, str):
        if requested not in task_rows or (matched and matched[0] != requested):
            return None
        return requested
    return matched[0] if len(matched) == 1 else None


def settle_after_stop(scheduler: _Scheduler, executor: _Executor, deadline: float) -> tuple[bool, bool]:
    """Deliver cancellation, await bounded M3 shutdown, then reconcile M1 without dispatching new work."""
    scheduler.step()  # M1's cancellation flag prevents new starts; this delivers cancel orders.
    remaining = max(0.0, deadline - time.monotonic() - 5.0)
    idle = executor.wait_idle(min(55.0, remaining))
    while True:
        scheduler.step()
        status = scheduler.snapshot().status
        if status in ("completed", "blocked", "cancelled"):
            return idle, True
        if time.monotonic() >= deadline:
            return idle, False
        time.sleep(min(0.1, max(0.0, deadline - time.monotonic())))
