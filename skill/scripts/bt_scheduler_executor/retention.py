"""Schema-1 retention: retire captured terminal worktrees, never their evidence or Git refs."""
from __future__ import annotations

import fcntl
import json
import math
import os
import re
import sqlite3
import subprocess
import tempfile
import time
from contextlib import closing
from pathlib import Path

from . import gitutil
from .errors import ExecutorError
from .model import TERMINAL

RETENTION_SECONDS = 3 * 86400
_SHA = re.compile(r"[0-9a-f]{40}(?:[0-9a-f]{24})?")
_GENERATED_DIRS = {"node_modules", ".next", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}
_GENERATED_FILES = {"next-env.d.ts", "tsconfig.tsbuildinfo"}


def _json(path: Path) -> dict:
    if path.is_symlink() or path.stat().st_size > 2**20:
        raise ValueError("unsafe_or_oversized_manifest")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError("invalid_manifest")
    return data


def _in_use(tree: Path) -> bool:
    """Linux owner processes: include detached servers whose argv still names the checkout."""
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            if entry.stat().st_uid != os.getuid():
                continue
            if os.fsencode(tree) in (entry / "cmdline").read_bytes():
                return True
            try:
                cwd = Path(os.readlink(entry / "cwd"))
            except PermissionError:
                # Bounded read-only probe. Without passwordless inspection,
                # a live process keeps the checkout protected.
                probe = subprocess.run(
                    ["sudo", "-n", "readlink", str(entry / "cwd")],
                    capture_output=True, text=True, timeout=3, check=False,
                )
                if probe.returncode:
                    if not entry.exists():
                        continue
                    return True
                cwd = Path(probe.stdout.strip())
            if cwd == tree or tree in cwd.parents:
                return True
        except (FileNotFoundError, ProcessLookupError):
            continue
        except PermissionError:
            return True
    return False


def _ignored_generated(path: str) -> bool:
    parts = Path(path.rstrip("/")).parts
    if not parts or Path(path).is_absolute() or ".." in parts:
        return False
    if any(part in _GENERATED_DIRS for part in parts):
        return True
    if parts[-1] in _GENERATED_FILES or parts[-1].endswith(".tsbuildinfo"):
        return True
    return len(parts) >= 3 and parts[0] == "packages" and parts[-1] == "dist"


def _validate(tree: Path, run: Path, row: sqlite3.Row) -> tuple[Path, str]:
    """No writes to the real index; compare all nonignored data to the pinned handoff tree."""
    if tree.is_symlink() or tree.resolve() != tree or tree.parent != run / "ws" / "worktrees":
        raise ValueError("unmanaged_or_symlinked_worktree")
    allocation = _json(tree.with_suffix(".json"))
    workspace = json.loads(row["workspace"])
    saved = json.loads(row["handoff"])
    if not isinstance(workspace, dict) or not isinstance(saved, dict):
        raise TypeError("invalid_workspace_or_handoff")
    repo = Path(allocation["repo"])
    if not repo.is_absolute() or not repo.is_dir():
        raise ValueError("repository_missing")
    if (allocation.get("attempt_id") != row["attempt_id"]
            or allocation.get("worktree") != str(tree) or workspace.get("path") != str(tree)
            or workspace.get("repo") != str(repo) or saved.get("repository") != str(repo)
            or saved.get("worktree") != str(tree) or saved.get("attempt_id") != row["attempt_id"]):
        raise ValueError("identity_mismatch")
    if saved.get("status") != "captured" or saved.get("handoff_mode", "snapshot") != "snapshot":
        raise ValueError("no_durable_snapshot")
    snapshot, head = saved.get("snapshot_sha"), saved.get("head_sha")
    refs = saved.get("refs")
    ref = refs.get("snapshot") if isinstance(refs, dict) else None
    if (not isinstance(snapshot, str) or not _SHA.fullmatch(snapshot)
            or not isinstance(ref, str) or not ref.startswith("refs/m3/handoff/")):
        raise ValueError("invalid_snapshot_ref")
    if gitutil.run(repo, ["rev-parse", "--verify", ref]) != snapshot:
        raise ValueError("snapshot_ref_changed")
    if gitutil.run(tree, ["rev-parse", "HEAD"]) != head:
        raise ValueError("head_changed_since_capture")
    if not gitutil.ok(tree, ["diff", "--cached", "--quiet", "HEAD", "--"]):
        raise ValueError("staged_changes_preserved")
    entries = gitutil.run(tree, ["ls-files", "--stage", "-z"], binary=True).split(b"\0")
    if any(entry.startswith(b"160000 ") for entry in entries):
        raise ValueError("submodules_preserved")
    common = gitutil.run(tree, ["rev-parse", "--path-format=absolute", "--git-common-dir"])
    if common != gitutil.run(repo, ["rev-parse", "--path-format=absolute", "--git-common-dir"]):
        raise ValueError("repository_identity_mismatch")
    listing = gitutil.run(repo, ["worktree", "list", "--porcelain"])
    record = next((r for r in listing.split("\n\n") if r.splitlines()[0] == f"worktree {tree}"), "")
    if not record or any(line.startswith("locked") for line in record.splitlines()):
        raise ValueError("unregistered_or_locked")
    ignored = gitutil.run(tree, ["ls-files", "--others", "--ignored", "--exclude-standard", "--directory", "-z"],
                          binary=True).split(b"\0")
    if any(not _ignored_generated(os.fsdecode(path)) for path in ignored if path):
        raise ValueError("unknown_ignored_data")
    if _in_use(tree):
        raise ValueError("process_using_worktree")
    with tempfile.TemporaryDirectory(prefix="m3-retention-") as scratch:
        env = {"GIT_INDEX_FILE": str(Path(scratch) / "index")}
        gitutil.run(tree, ["read-tree", snapshot], env=env)
        gitutil.run(tree, ["add", "-A"], env=env)
        current = gitutil.run(tree, ["write-tree"], env=env)
    if current != gitutil.run(repo, ["rev-parse", f"{snapshot}^{{tree}}"]):
        raise ValueError("content_changed_since_capture")
    return repo, snapshot


def _record(run: Path, result: dict) -> None:
    with (run / "retention.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"schema": 1, "time": time.time(), **result}, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def retain_run(run: Path, *, apply: bool = False, now: float | None = None) -> list[dict]:
    """Acquire the exact executor lock before inspecting or removing any checkout; dry-run by default."""
    if run.is_symlink() or not run.is_dir():
        return [{"run": str(run), "action": "skip", "reason": "unsafe_run"}]
    run = run.resolve()
    now = time.time() if now is None else now
    results: list[dict] = []
    try:
        # Never create or replace ownership state during inspection.
        fd = os.open(run / "executor.lock", os.O_RDWR | os.O_NOFOLLOW)
        with os.fdopen(fd, "r+") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return [{"run": str(run), "action": "skip", "reason": "executor_busy"}]
            db = run / "ledger.db"
            if db.is_symlink():
                raise ValueError("symlinked_ledger")
            with closing(sqlite3.connect(f"{db.as_uri()}?mode=ro", uri=True, timeout=3)) as connection:
                connection.row_factory = sqlite3.Row
                rows = list(connection.execute("SELECT attempt_id, dirname, state, ended_at, workspace, handoff FROM attempts"))
            for row in rows:
                result = {"run": str(run), "attempt_id": row["attempt_id"], "action": "skip"}
                try:
                    if not isinstance(row["dirname"], str) or not re.fullmatch(r"att-[A-Za-z0-9_-]+", row["dirname"]):
                        raise ValueError("invalid_directory_name")
                    tree = run / "ws" / "worktrees" / row["dirname"]
                    if row["state"] not in TERMINAL:
                        raise ValueError("attempt_not_terminal")
                    ended = row["ended_at"]
                    if not isinstance(ended, (int, float)) or not math.isfinite(ended) or ended > now - RETENTION_SECONDS:
                        raise ValueError("younger_than_three_days")
                    if not tree.exists() and not tree.is_symlink():
                        raise ValueError("already_absent")
                    repo, snapshot = _validate(tree, run, row)
                    result.update(worktree=str(tree), snapshot_sha=snapshot)
                    if apply:
                        # Keep refs, branch, intent manifest and ledger: a retired checkout is reconstructable.
                        _record(run, {**result, "action": "removing"})
                        gitutil.run(repo, ["worktree", "remove", "--force", str(tree)])
                    result["action"] = "removed" if apply else "eligible"
                except (ValueError, TypeError, KeyError, OSError, subprocess.SubprocessError, ExecutorError) as error:
                    result["reason"] = str(error)[:300]
                results.append(result)
                if apply:
                    _record(run, result)
    except (ValueError, OSError, sqlite3.Error) as error:
        results.append({"run": str(run), "action": "error", "reason": str(error)[:300]})
    return results
