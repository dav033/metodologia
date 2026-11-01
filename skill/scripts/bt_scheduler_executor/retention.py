"""Schema-1 retention: retire captured terminal worktrees, never their evidence or Git refs.

D-270 (2026-10-31, after `/home` filled to 100 %): the hourly pass skipped every one of 262 attempts (196
`already_absent`, 49 `unknown_ignored_data`, 15 `attempt_not_terminal`, 2 `staged_changes_preserved`) while their 66
checkouts held 68 GB. With `preserve=True` (the engine's disk pass, `bt_durable.gc_scratch`) a checkout is retired once
everything in it that is not regenerable is preserved somewhere else first:

- unknown ignored data (test reports, local data files: everything but the recognised dependency/build caches) is
  archived into the attempt's evidence folder (`attempts/<dirname>/retained-ignored.tar.gz`) when it fits
  `archive_max_bytes`; bigger, it is reported (`unpreserved_ignored_data`) and the checkout is kept;
- work the snapshot does not hold (staged content, edits or commits after the capture, or an attempt never captured)
  becomes ONE commit under `refs/m3/retained/<run>/<dirname>`: its tree is the checkout as it is, its parents HEAD and,
  when the index differs, a commit of the staged tree;
- an attempt the ledger still calls live is retired only when its run was superseded by a later revision of the same
  requirement, its supervisor is gone, and nothing touched it for the retention period;
Without `preserve` (the operator CLI's default) every rule above fails closed exactly as before. In both modes an absent
checkout of a finished attempt is settled: reported once (`settled`, `already_absent`), recorded by an applying pass in
`retention-index.json`, and never inspected or reported again.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import math
import os
import re
import shutil
import sqlite3
import subprocess
import tarfile
import tempfile
import time
from collections.abc import Callable
from contextlib import closing
from dataclasses import dataclass, field
from pathlib import Path

from . import gitutil, procinfo
from .errors import ExecutorError
from .model import TERMINAL

RETENTION_SECONDS = 3 * 86400
ARCHIVE_NAME = "retained-ignored.tar.gz"
INDEX_NAME = "retention-index.json"
RETAINED_PREFIX = "refs/m3/retained/"
_RUN_NAME = re.compile(r"(?P<req>.+)-r(?P<rev>\d+)-[0-9a-f]{6,}-\d+")
_SAFE_REF = re.compile(r"[^A-Za-z0-9._-]+")
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


@dataclass
class Inspection:
    """What a checkout holds beyond what is already preserved, and how removing it would preserve that first."""
    repo: Path
    snapshot: str | None
    head: str
    current: str                                    # the tree of the checkout as it is (temporary index)
    staged: str                                     # the tree of its real index
    needs: list[str] = field(default_factory=list)  # why a retained commit is required (empty: nothing to add)
    ignored: list[str] = field(default_factory=list)
    ignored_bytes: int = 0


def _tree_bytes(path: Path) -> int:
    """Apparent bytes under `path` (lstat; symlinks are not followed)."""
    if path.is_symlink() or not path.is_dir():
        return path.lstat().st_size
    total = 0
    for base, dirs, files in os.walk(path, followlinks=False):
        for name in dirs + files:
            total += os.lstat(os.path.join(base, name)).st_size
    return total


def _identity(tree: Path, run: Path, row: sqlite3.Row, *, captured: bool) -> tuple[Path, dict]:
    if tree.is_symlink() or tree.resolve() != tree or tree.parent != run / "ws" / "worktrees":
        raise ValueError("unmanaged_or_symlinked_worktree")
    allocation = _json(tree.with_suffix(".json"))
    workspace = json.loads(row["workspace"])
    saved = json.loads(row["handoff"]) if captured else {}
    if not isinstance(workspace, dict) or not isinstance(saved, dict):
        raise TypeError("invalid_workspace_or_handoff")
    repo = Path(allocation["repo"])
    if not repo.is_absolute() or not repo.is_dir():
        raise ValueError("repository_missing")
    if (allocation.get("attempt_id") != row["attempt_id"] or allocation.get("worktree") != str(tree)
            or workspace.get("path") != str(tree) or workspace.get("repo") != str(repo)):
        raise ValueError("identity_mismatch")
    if captured and (saved.get("repository") != str(repo) or saved.get("worktree") != str(tree)
                     or saved.get("attempt_id") != row["attempt_id"]):
        raise ValueError("identity_mismatch")
    return repo, saved


def _validate(tree: Path, run: Path, row: sqlite3.Row, *, preserve: bool = False, captured: bool = True,
              archive_max_bytes: int = 0) -> Inspection:
    """No writes to the real index; compare all nonignored data to the pinned handoff tree. `captured=False` (only with
    `preserve`): the attempt has no snapshot, so its whole checkout goes into the retained commit."""
    repo, saved = _identity(tree, run, row, captured=captured)
    snapshot = head = None
    needs: list[str] = []
    if captured:
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
    current_head = gitutil.run(tree, ["rev-parse", "HEAD"])
    if captured and current_head != head:
        if not preserve:
            raise ValueError("head_changed_since_capture")
        needs.append("head_changed_since_capture")
    if not captured:
        needs.append("uncaptured")
    staged_differs = not gitutil.ok(tree, ["diff", "--cached", "--quiet", "HEAD", "--"])
    if staged_differs and not preserve:
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
    unknown = [os.fsdecode(path).rstrip("/") for path in ignored if path and not _ignored_generated(os.fsdecode(path))]
    unknown_bytes = 0
    if unknown:
        if not preserve or archive_max_bytes <= 0:
            raise ValueError("unknown_ignored_data")
        if any(Path(path).is_absolute() or ".." in Path(path).parts for path in unknown):
            raise ValueError("unknown_ignored_data")
        unknown_bytes = sum(_tree_bytes(tree / path) for path in unknown)
        if unknown_bytes > archive_max_bytes:
            raise ValueError(f"unpreserved_ignored_data ({unknown_bytes} bytes > {archive_max_bytes}: "
                             + ", ".join(unknown[:5]) + ")")
    if _in_use(tree):
        raise ValueError("process_using_worktree")
    with tempfile.TemporaryDirectory(prefix="m3-retention-") as scratch:
        env = {"GIT_INDEX_FILE": str(Path(scratch) / "index")}
        gitutil.run(tree, ["read-tree", snapshot or current_head], env=env)
        gitutil.run(tree, ["add", "-A"], env=env)
        current = gitutil.run(tree, ["write-tree"], env=env)
        staged = current
        if staged_differs:
            # the real index is copied, never written (write-tree would refresh its cache-tree extension)
            real = Path(gitutil.run(tree, ["rev-parse", "--path-format=absolute", "--git-path", "index"]))
            shutil.copyfile(real, Path(scratch) / "staged")
            staged = gitutil.run(tree, ["write-tree"], env={"GIT_INDEX_FILE": str(Path(scratch) / "staged")})
    snapshot_tree = gitutil.run(repo, ["rev-parse", f"{snapshot}^{{tree}}"]) if snapshot else None
    if captured and current != snapshot_tree:
        if not preserve:
            raise ValueError("content_changed_since_capture")
        needs.append("content_changed_since_capture")
    if staged_differs and not any(_holds(tree, staged, other, current_head) for other in (snapshot_tree, current) if other):
        needs.append("staged_changes")
    return Inspection(repo, snapshot, current_head, current, staged, needs, unknown, unknown_bytes)


def _entries(tree: Path, treeish: str, paths: list[str]) -> dict[str, str]:
    out = gitutil.run(tree, ["ls-tree", "-r", "-z", "--full-tree", treeish, "--", *paths], binary=True)
    found = {}
    for item in out.split(b"\0"):
        if item:
            meta, _, path = item.partition(b"\t")
            found[os.fsdecode(path)] = meta.split()[2].decode()
    return found


def _holds(tree: Path, staged: str, other: str, head: str) -> bool:
    """Every path the index changed against HEAD has the same content (or the same absence) in `other`."""
    changed = gitutil.run(tree, ["diff-tree", "-r", "-z", "--no-renames", "--name-only", head, staged],
                          binary=True).split(b"\0")
    paths = [os.fsdecode(path) for path in changed if path]
    if len(paths) > 2000:                       # too many to compare by argument: preserve the index instead
        return False
    return not paths or _entries(tree, staged, paths) == _entries(tree, other, paths)


def retained_ref(run: Path, dirname: str) -> str:
    return f"{RETAINED_PREFIX}{_SAFE_REF.sub('-', run.name)}/{dirname}"


def _preserve(run: Path, row: sqlite3.Row, tree: Path, found: Inspection) -> dict:
    """Write what removal would lose: the retained commit (when `needs`) and the archive of unknown ignored data."""
    out: dict = {}
    if found.needs:
        identity = {"GIT_AUTHOR_NAME": "m3 retention", "GIT_AUTHOR_EMAIL": "retention@localhost",
                    "GIT_COMMITTER_NAME": "m3 retention", "GIT_COMMITTER_EMAIL": "retention@localhost"}
        parents = ["-p", found.head]
        if "staged_changes" in found.needs:
            index_commit = gitutil.run(found.repo, ["commit-tree", found.staged, "-p", found.head, "-m",
                                                    f"m3 retained index {row['attempt_id']}"], env=identity)
            parents += ["-p", index_commit]
        message = (f"m3 retained {row['attempt_id']}\n\nThe checkout {tree} as it was when retention removed it "
                   f"({', '.join(found.needs)}); snapshot {found.snapshot or 'none'}.")
        commit = gitutil.run(found.repo, ["commit-tree", found.current, *parents, "-m", message], env=identity)
        ref = retained_ref(run, row["dirname"])
        gitutil.run(found.repo, ["update-ref", ref, commit])
        out.update(retained_ref=ref, retained_commit=commit)
    if found.ignored:
        folder = run / "attempts" / row["dirname"]
        folder.mkdir(parents=True, exist_ok=True, mode=0o700)
        target = folder / ARCHIVE_NAME
        fd, temp = tempfile.mkstemp(prefix=".retained-", dir=folder)
        os.close(fd)
        try:
            with tarfile.open(temp, "w:gz") as archive:
                for path in found.ignored:
                    archive.add(tree / path, arcname=path, recursive=True)
            digest = hashlib.sha256(Path(temp).read_bytes()).hexdigest()
            os.chmod(temp, 0o600)
            os.replace(temp, target)
        finally:
            Path(temp).unlink(missing_ok=True)
        out.update(archive=str(target), archive_sha256=digest, archived=found.ignored[:50],
                   archived_bytes=found.ignored_bytes)
    return out


def superseded_runs(root: Path) -> set[str]:
    """Executor run folders a later revision of the same requirement replaced (`<project>-<REQ>-r<N>-<id>-<ms>`): the
    legacy scheduler only ever resumes a requirement's latest revision."""
    latest: dict[str, int] = {}
    named: list[tuple[str, str, int]] = []
    for entry in Path(root).iterdir() if Path(root).is_dir() else ():
        found = _RUN_NAME.fullmatch(entry.name)
        if found and entry.is_dir() and not entry.is_symlink():
            rev = int(found.group("rev"))
            named.append((entry.name, found.group("req"), rev))
            latest[found.group("req")] = max(latest.get(found.group("req"), 0), rev)
    return {name for name, req, rev in named if rev < latest[req]}


def _settled(run: Path) -> set[str]:
    try:
        data = json.loads((run / INDEX_NAME).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return set()
    absent = data.get("absent") if isinstance(data, dict) else None
    return {str(item) for item in absent} if isinstance(absent, list) else set()


def _settle(run: Path, ids: set[str]) -> None:
    temp = run / f".{INDEX_NAME}.tmp"
    temp.write_text(json.dumps({"schema": 1, "absent": sorted(ids)}, indent=0) + "\n", encoding="utf-8")
    os.replace(temp, run / INDEX_NAME)


def _orphaned(row: sqlite3.Row, now: float) -> str:
    """'' when a live-looking attempt is abandoned (its supervisor and agent are gone and nothing touched it for the
    retention period), else why it is kept."""
    try:
        shim = json.loads(row["shim"] or "null") if "shim" in row.keys() else None  # noqa: SIM118 - a Row's `in` reads values
    except ValueError:
        shim = None
    if isinstance(shim, dict) and any(procinfo.alive(shim.get(pid), shim.get(ident)) for pid, ident in
                                      (("pid", "ident"), ("child_pid", "child_ident"))):
        return "attempt_live"
    updated = row["updated"] if "updated" in row.keys() else None  # noqa: SIM118 - a Row's `in` reads values
    if not isinstance(updated, (int, float)) or not math.isfinite(updated) or updated > now - RETENTION_SECONDS:
        return "younger_than_three_days"
    return ""


def _record(run: Path, result: dict) -> None:
    with (run / "retention.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"schema": 1, "time": time.time(), **result}, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def retain_run(run: Path, *, apply: bool = False, now: float | None = None, preserve: bool = False,
               archive_max_bytes: int = 0, superseded: bool = False, limit: int | None = None,
               measure: Callable[[Path], int] | None = None) -> list[dict]:
    """Acquire the exact executor lock before inspecting or removing any checkout; dry-run by default.

    `preserve` (D-270): preserve what a checkout holds beyond its snapshot, then remove it (see the module docstring);
    `archive_max_bytes` bounds the unknown ignored data archived per checkout; `superseded`: a later revision of the
    requirement replaced this run, so an attempt it still calls live may be abandoned; `limit`: removals at most (the
    rest are reported `eligible` with reason `limit`); `measure(tree)` fills `bytes` for every removable checkout.
    Attempts already settled in `retention-index.json` are skipped without a result."""
    if run.is_symlink() or not run.is_dir():
        return [{"run": str(run), "action": "skip", "reason": "unsafe_run"}]
    run = run.resolve()
    now = time.time() if now is None else now
    results: list[dict] = []
    removed = 0
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
                rows = list(connection.execute("SELECT * FROM attempts"))
            settled = _settled(run)
            newly: set[str] = set()
            for row in rows:
                if row["attempt_id"] in settled:
                    continue
                result = {"run": str(run), "attempt_id": row["attempt_id"], "action": "skip"}
                try:
                    if not isinstance(row["dirname"], str) or not re.fullmatch(r"att-[A-Za-z0-9_-]+", row["dirname"]):
                        raise ValueError("invalid_directory_name")
                    tree = run / "ws" / "worktrees" / row["dirname"]
                    terminal = row["state"] in TERMINAL
                    if not tree.exists() and not tree.is_symlink():
                        if terminal or (preserve and superseded):
                            result.update(action="settled", reason="already_absent")
                            newly.add(row["attempt_id"])
                            results.append(result)
                            continue
                        raise ValueError("attempt_not_terminal")
                    if terminal:
                        ended = row["ended_at"]
                        if not isinstance(ended, (int, float)) or not math.isfinite(ended) or ended > now - RETENTION_SECONDS:
                            raise ValueError("younger_than_three_days")
                        captured = not preserve or _has_capture(row)
                    else:
                        if not (preserve and superseded):
                            raise ValueError("attempt_not_terminal")
                        why = _orphaned(row, now)
                        if why:
                            raise ValueError(why)
                        captured = False
                    found = _validate(tree, run, row, preserve=preserve, captured=captured,
                                      archive_max_bytes=archive_max_bytes)
                    result.update(worktree=str(tree), snapshot_sha=found.snapshot)
                    if found.needs:
                        result["preserve"] = found.needs
                    if found.ignored:
                        result.update(archive_paths=len(found.ignored), archive_bytes=found.ignored_bytes)
                    if measure is not None:
                        result["bytes"] = measure(tree)
                    if apply and limit is not None and removed >= limit:
                        result.update(action="eligible", reason="limit")
                        results.append(result)
                        continue
                    if apply:
                        # Keep refs, branch, intent manifest and ledger: a retired checkout is reconstructable.
                        _record(run, {**result, "action": "removing"})
                        result.update(_preserve(run, row, tree, found))
                        gitutil.run(found.repo, ["worktree", "remove", "--force", str(tree)])
                        removed += 1
                    result["action"] = "removed" if apply else "eligible"
                except (ValueError, TypeError, KeyError, OSError, subprocess.SubprocessError, ExecutorError,
                        tarfile.TarError) as error:
                    result["reason"] = str(error)[:300]
                results.append(result)
                if apply:
                    _record(run, result)
            if apply and newly:
                _settle(run, settled | newly)
    except (ValueError, OSError, sqlite3.Error) as error:
        results.append({"run": str(run), "action": "error", "reason": str(error)[:300]})
    return results


def _has_capture(row: sqlite3.Row) -> bool:
    """The ledger holds a captured snapshot handoff for the attempt (else, under `preserve`, it is treated as never
    captured: the retained commit holds the whole checkout)."""
    try:
        saved = json.loads(row["handoff"] or "null")
    except ValueError:
        return False
    return isinstance(saved, dict) and saved.get("status") == "captured"
