"""Durable isolated worker worktrees and serialized candidate integration."""
from __future__ import annotations

import json
import os
import secrets
import subprocess
import time
from pathlib import Path, PurePosixPath
from typing import Iterable

from bt_integration_lock import IntegrationLock


class WorktreeError(RuntimeError):
    """A worktree operation cannot safely proceed."""


def _git(repo: Path | str, *args: str, check: bool = True) -> str:
    result = subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True, encoding="utf-8",
                            errors="replace", check=False)
    if check and result.returncode:
        raise WorktreeError(f"git {' '.join(args)} failed: {(result.stderr or result.stdout).strip()}")
    return result.stdout.strip()


def _record(journal: Path, task_id: str, stage: str, allowed_roots: tuple[Path, ...] = (),
            **fields: object) -> None:
    absolute = journal.absolute()
    if ".." in journal.parts or (allowed_roots and
            not any(absolute.is_relative_to(root) for root in allowed_roots)):
        raise WorktreeError(f"Unsafe journal path: {journal}")
    root = next((candidate for candidate in allowed_roots if absolute.is_relative_to(candidate)), None)
    cursor = absolute.parent
    while root is not None and cursor != cursor.parent and cursor.is_relative_to(root):
        if cursor.is_symlink() and not cursor.resolve(strict=False).is_relative_to(root.resolve(strict=False)):
            raise WorktreeError(f"Refusing journal symlink outside allocation root: {cursor}")
        cursor = cursor.parent
    journal.parent.mkdir(parents=True, exist_ok=True)
    row = {"time": time.time(), "task_id": task_id, "stage": stage, **fields}
    with journal.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(row, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def journal_path(allocation: dict) -> Path:
    return Path(allocation["journal"])


def record_stage(allocation: dict, stage: str, **fields: object) -> None:
    """Append an execution lifecycle stage to the allocation's durable journal."""
    roots = tuple(Path(root) for root in allocation.get("allowed_roots", ()))
    _record(journal_path(allocation), str(allocation["task_id"]), stage, allowed_roots=roots, **fields)


def allocate(repo: Path | str, task_id: str, base_sha: str, root: Path | str) -> dict:
    """Persist a unique allocation before asking Git to create its branch or worktree."""
    repo_path, root_path = Path(repo).resolve(), Path(root).resolve()
    if _git(repo_path, "rev-parse", "--verify", f"{base_sha}^{{commit}}", check=False) == "":
        raise WorktreeError(f"Unknown base commit: {base_sha}")
    root_path.mkdir(parents=True, exist_ok=True)
    safe_id = "".join(c if c.isalnum() or c in "-_" else "-" for c in task_id).strip("-") or "task"
    token = secrets.token_hex(4)
    branch, worktree = f"wt/{safe_id}-{token}", root_path / f"{safe_id}-{token}"
    if worktree.exists():
        raise WorktreeError(f"Refusing to reuse existing worktree directory: {worktree}")
    if subprocess.run(["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"], cwd=repo_path,
                      check=False).returncode == 0:
        raise WorktreeError(f"Refusing to reuse existing branch: {branch}")
    allocation = {"task_id": task_id, "branch": branch, "worktree": str(worktree), "base_sha": base_sha,
                  "repo": str(repo_path), "journal": str(root_path / "integration.jsonl"), "state": "allocated",
                  "allowed_roots": [str(root_path)]}
    manifest = root_path / f"{safe_id}-{token}.json"
    with manifest.open("x", encoding="utf-8") as stream:
        json.dump(allocation, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    allocation["manifest"] = str(manifest)
    _record(Path(allocation["journal"]), task_id, "allocated", allowed_roots=(root_path,), branch=branch, worktree=str(worktree),
            base_sha=base_sha)
    _git(repo_path, "worktree", "add", "-b", branch, str(worktree), base_sha)
    return allocation


def _changed_paths(allocation: dict) -> list[str]:
    worktree, base = Path(allocation["worktree"]), str(allocation["base_sha"])
    tracked = _git(worktree, "diff", "--no-renames", "--name-only", "-z", base, check=True).split("\0")
    untracked = _git(worktree, "ls-files", "--others", "--exclude-standard", "-z").split("\0")
    return sorted({p for p in tracked + untracked if p})


def _safe_relative(raw: str) -> PurePosixPath:
    path = PurePosixPath(raw)
    if (path.is_absolute() or not raw or str(path) in {".", ""} or ".." in path.parts or "\\" in raw or
            (path.parts and path.parts[0].endswith(":"))):
        raise WorktreeError(f"Unsafe path in scope or diff: {raw!r}")
    return path


def _within_scope(path: PurePosixPath, scopes: list[PurePosixPath]) -> bool:
    return any(path.parts[:len(scope.parts)] == scope.parts for scope in scopes)


def _check_symlinks(worktree: Path, relative: PurePosixPath) -> None:
    root = worktree.resolve()
    current = worktree
    for part in relative.parts:
        current = current / part
        if current.is_symlink() and not current.resolve(strict=False).is_relative_to(root):
            raise WorktreeError(f"Changed path escapes worktree through symlink: {relative}")


def check_scope(allocation: dict, allowed_paths: Iterable[str] | None) -> dict:
    """Validate changed paths against segment-scoped declarations and reject symlink escapes."""
    if allocation.get("allow_all"):
        return {"status": "serialize", "safe": False, "reason": "explicit repository-wide scope"}
    if not allowed_paths:
        return {"status": "serialize", "safe": False, "reason": "scope declarations are missing"}
    scopes = [_safe_relative(str(path)) for path in allowed_paths]
    changed = [_safe_relative(path) for path in _changed_paths(allocation)]
    for path in changed:
        if not _within_scope(path, scopes):
            raise WorktreeError(f"Changed path {path} is outside declared scopes")
        _check_symlinks(Path(allocation["worktree"]), path)
    return {"status": "parallel", "safe": True, "changed": [str(path) for path in changed]}


def candidate(allocation: dict) -> str:
    """Commit any worker changes and return the immutable branch tip."""
    worktree = Path(allocation["worktree"])
    _git(worktree, "add", "-A")
    status = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=worktree, check=False)
    if status.returncode == 1:
        _git(worktree, "-c", "user.name=Bitacora Worker", "-c", "user.email=worker@localhost", "commit", "-m",
             f"work: {allocation['task_id']}")
    elif status.returncode != 0:
        raise WorktreeError("Unable to inspect staged worker changes")
    sha = _git(worktree, "rev-parse", "HEAD")
    allocation["candidate_sha"], allocation["state"] = sha, "candidate"
    record_stage(allocation, "candidate", sha=sha)
    return sha


def _journal_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()
    rows = []
    for index, line in enumerate(lines):
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            if index == len(lines) - 1 and not content.endswith("\n"):
                break
            raise
    return rows


def _default_branch(repo: Path, integration: Path) -> str:
    origin = _git(repo, "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD", check=False)
    if origin.startswith("origin/"):
        return origin.removeprefix("origin/")
    configured = _git(repo, "config", "--get", "init.defaultBranch", check=False)
    if configured:
        return configured
    worktrees = _git(repo, "worktree", "list", "--porcelain", check=False).splitlines()
    primary_path = next((line.removeprefix("worktree ") for line in worktrees if line.startswith("worktree ")), "")
    return _git(Path(primary_path), "branch", "--show-current", check=False) if primary_path else ""


def _restore_parent(integration: Path, parent: str) -> None:
    if _git(integration, "status", "--porcelain"):
        raise WorktreeError("Refusing recovery rollback: integration worktree has uncommitted changes")
    merge_head = subprocess.run(["git", "rev-parse", "--verify", "MERGE_HEAD"], cwd=integration,
                                capture_output=True, check=False)
    if merge_head.returncode == 0:
        aborted = subprocess.run(["git", "merge", "--abort"], cwd=integration, capture_output=True, text=True,
                                 check=False)
        if aborted.returncode:
            raise WorktreeError(f"Unable to abort in-progress merge: {aborted.stderr.strip()}")
    else:
        reset = subprocess.run(["git", "reset", "--keep", parent], cwd=integration, capture_output=True,
                               text=True, check=False)
        if reset.returncode:
            raise WorktreeError(f"Unable to restore integration parent: {reset.stderr.strip()}")


def integrate(candidates: Iterable[dict], integration_worktree: Path | str, verify_cmd: str,
              lock: IntegrationLock, lock_held: bool = False) -> dict[str, str]:
    """Merge candidates serially under a strict lease and verify the combined integration tree."""
    integration = Path(integration_worktree).resolve()
    items = list(candidates)
    repo = Path(_git(integration, "rev-parse", "--show-toplevel"))
    common_dir = Path(_git(integration, "rev-parse", "--git-common-dir"))
    if not common_dir.is_absolute():
        common_dir = (integration / common_dir).resolve()
    common_repo = common_dir.parent
    first_allocation = items[0].get("allocation", items[0]) if items else {}
    for item in items:
        allocation = item.get("allocation", item)
        if allocation.get("repo") and Path(allocation["repo"]).resolve() != common_repo.resolve():
            raise WorktreeError(f"Candidate for {allocation.get('task_id')} belongs to another repository")
    journal = Path(first_allocation.get("journal", integration.parent / "integration.jsonl"))
    result: dict[str, str] = {}
    if not lock_held:
        lock.acquire()
    try:
        branch = _git(integration, "branch", "--show-current", check=False)
        if not branch or branch.lower() in {"main", "master", "trunk"} or branch == _default_branch(repo, integration):
            raise WorktreeError(f"Integration branch {branch!r} is detached, default, or protected; use a dedicated feature branch.")
        if _git(integration, "status", "--porcelain"):
            raise WorktreeError("Integration worktree must be clean before integration.")
        existing = _journal_rows(journal)
        accepted = {row.get("candidate_sha"): row.get("task_id") for row in existing if row.get("stage") == "accepted"}
        cleanup_done = {row.get("candidate_sha") for row in existing if row.get("stage") == "cleanup_eligible"}
        for item in items:
            allocation = item.get("allocation", item)
            task_id, sha = str(allocation["task_id"]), str(item.get("sha") or allocation.get("candidate_sha", ""))
            if not sha:
                raise WorktreeError(f"Candidate for {task_id} has no immutable SHA")
            if sha in accepted:
                allocation["state"] = "accepted"
                if sha not in cleanup_done:
                    record_stage(allocation, "cleanup_eligible", candidate_sha=sha, recovered=True)
                result[task_id] = "accepted"
                continue
            scopes = allocation.get("allowed_paths")
            try:
                scope = check_scope(allocation, scopes)
            except WorktreeError as exc:
                allocation["state"] = "blocked"
                record_stage(allocation, "blocked", reason=f"scope violation: {exc}", candidate_sha=sha)
                result[task_id] = "blocked"
                continue
            if scope["status"] == "serialize":
                allocation["state"] = "serialize-only"
                record_stage(allocation, "scope_unchecked", reason=scope["reason"], candidate_sha=sha)
                result[task_id] = "serialize-only"
                continue
            record_stage(allocation, "lock_acquired")
            ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", sha, "HEAD"], cwd=integration,
                                      capture_output=True, check=False)
            if ancestor.returncode == 0:
                checked = subprocess.run(verify_cmd, cwd=integration, shell=True, capture_output=True, text=True,
                                         encoding="utf-8", errors="replace", check=False)
                if checked.returncode:
                    reason = ((checked.stdout or "") + (checked.stderr or "")).strip()[-1000:]
                    parent = next((row.get("pre_merge_parent") for row in reversed(existing)
                                   if row.get("candidate_sha") == sha and row.get("stage") == "merge_started"), None)
                    if parent:
                        _restore_parent(integration, parent)
                    allocation["state"] = "blocked"
                    record_stage(allocation, "blocked", reason=f"recovery verification failed: {reason}",
                                 candidate_sha=sha)
                    result[task_id] = "blocked"
                else:
                    record_stage(allocation, "verified", candidate_sha=sha, recovered=True)
                    record_stage(allocation, "accepted", candidate_sha=sha,
                                 accepted_sha=_git(integration, "rev-parse", "HEAD"), recovered=True)
                    record_stage(allocation, "cleanup_eligible", candidate_sha=sha)
                    allocation["state"] = "accepted"
                    result[task_id] = "accepted"
                    accepted[sha] = task_id
                continue
            before = _git(integration, "rev-parse", "HEAD")
            record_stage(allocation, "merge_started", candidate_sha=sha, pre_merge_parent=before)
            merged = subprocess.run(["git", "merge", "--no-ff", "--no-edit", sha], cwd=integration,
                                    capture_output=True, text=True, check=False)
            if merged.returncode:
                subprocess.run(["git", "merge", "--abort"], cwd=integration, capture_output=True, check=False)
                reason = (merged.stderr or merged.stdout).strip()
                allocation["state"] = "blocked"
                record_stage(allocation, "blocked", reason=f"merge conflict: {reason}", candidate_sha=sha)
                result[task_id] = "blocked"
                continue
            record_stage(allocation, "merged", candidate_sha=sha, head=_git(integration, "rev-parse", "HEAD"))
            checked = subprocess.run(verify_cmd, cwd=integration, shell=True, capture_output=True, text=True,
                                     encoding="utf-8", errors="replace", check=False)
            if checked.returncode:
                reason = ((checked.stdout or "") + (checked.stderr or "")).strip()[-1000:]
                try:
                    _restore_parent(integration, before)
                except WorktreeError as exc:
                    reason += f"; integration rollback failed: {exc}"
                allocation["state"] = "blocked"
                record_stage(allocation, "blocked", reason=f"combined verification failed: {reason}",
                             candidate_sha=sha)
                result[task_id] = "blocked"
                continue
            record_stage(allocation, "verified", candidate_sha=sha)
            record_stage(allocation, "accepted", candidate_sha=sha, accepted_sha=_git(integration, "rev-parse", "HEAD"))
            allocation["state"] = "accepted"
            result[task_id] = "accepted"
            accepted[sha] = task_id
            record_stage(allocation, "cleanup_eligible", candidate_sha=sha)
            lock.renew()
    finally:
        if not lock_held:
            lock.release()
    return result


def recover(candidates: Iterable[dict], integration_worktree: Path | str, verify_cmd: str,
            lock: IntegrationLock, lock_held: bool = False) -> dict[str, str]:
    """Resume integration from candidate SHAs and append-only journal evidence."""
    return integrate(candidates, integration_worktree, verify_cmd, lock, lock_held)


def cleanup(allocation: dict) -> None:
    """Remove an accepted, clean worker worktree without forcing away local data."""
    if allocation.get("state") != "accepted":
        raise WorktreeError("Cleanup requires accepted integration state")
    worktree = Path(allocation["worktree"])
    if _git(worktree, "status", "--porcelain"):
        raise WorktreeError("Refusing cleanup: worktree is dirty; preserve or commit its files first")
    _git(allocation["repo"], "worktree", "remove", str(worktree))


def parallel_capacity(tasks: Iterable[dict], max_workers: int = 2, serial: bool = False) -> list[list[dict]]:
    """Greedily group disjoint declared scopes and resources; missing scopes serialize."""
    items = list(tasks)
    if serial:
        return [[task] for task in items]
    capacity = max(1, int(max_workers))
    groups: list[list[dict]] = []
    shared_lockfiles = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "uv.lock",
                        "Cargo.lock", "go.sum"}
    shared_prefixes = ("dist/", "build/", ".next/", "generated/", "migrations/")

    def resources_for(task: dict) -> set[str]:
        resources = set(task.get("resources") or [])
        paths = task.get("paths") or task.get("changed_paths") or task.get("files") or []
        for raw in paths:
            normalized = str(raw).replace("\\", "/").lstrip("./")
            path_parts = normalized.split("/")
            if (path_parts[-1] in shared_lockfiles or
                    any(part in {prefix[:-1] for prefix in shared_prefixes} for part in path_parts[:-1])):
                resources.add("default-shared-path")
        return resources

    for task in items:
        scopes = task.get("scopes") or task.get("allowed_paths")
        if not scopes:
            groups.append([task])
            continue
        paths = [_safe_relative(str(path)) for path in scopes]
        resources = resources_for(task)
        placed = False
        for group in groups:
            if len(group) >= capacity or len(group) == 1 and not (group[0].get("scopes") or group[0].get("allowed_paths")):
                continue
            compatible = True
            for other in group:
                other_scopes = other.get("scopes") or other.get("allowed_paths") or []
                other_paths = [_safe_relative(str(path)) for path in other_scopes]
                other_resources = resources_for(other)
                overlap = any(_within_scope(a, [b]) or _within_scope(b, [a]) for a in paths for b in other_paths)
                if overlap or resources & other_resources:
                    compatible = False
                    break
            if compatible:
                group.append(task)
                placed = True
                break
        if not placed:
            groups.append([task])
    return groups
