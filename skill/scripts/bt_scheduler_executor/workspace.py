"""Default `WorkspaceManager`: one git worktree + branch per attempt, allocated under a per-repository lock.

Layout under `root`: `worktrees/<dirname>/` (the checkout), `worktrees/<dirname>.json` (intent manifest, written BEFORE
git is asked to create anything, so a crash leaves a recoverable record), `journal.jsonl` (append-only, fsync'd).
Allocation is idempotent per attempt: a second call after a crash reuses what the first one made. Nothing is ever
deleted here; cleanup is an explicit operator action (`release`).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import time
from collections.abc import Callable, Mapping
from contextlib import contextmanager
from pathlib import Path

from . import gitutil
from .errors import ExecutorError
from .model import StartRequest, Workspace

_LOCKS: dict[str, threading.Lock] = {}
_LOCKS_GUARD = threading.Lock()


def dirname_of(attempt_id: str) -> str:
    """A filesystem- and ref-safe name for an attempt id: a readable slug (lossy) plus 64 bits of the id's hash; the
ledger additionally enforces uniqueness."""
    slug = re.sub(r"[^A-Za-z0-9_-]+", "-", attempt_id).strip("-")[:60] or "attempt"   # no dots: ".." is not a valid ref
    return f"{slug}-{hashlib.sha256(attempt_id.encode()).hexdigest()[:16]}"


class GitWorkspaces:
    def __init__(self, root: Path | str, repositories: Mapping[str, Path | str] | Callable[[str], Path | None]):
        self.root = Path(root).resolve()
        self._repos = repositories

    # ------------------------------------------------------------------------------------------ resolution
    def repository(self, role: str) -> Path:
        found = self._repos(role) if callable(self._repos) else self._repos.get(role)
        if not found or not Path(found).is_dir():
            raise ExecutorError("REPOSITORY_UNKNOWN", f"no checkout for repository {role!r}")
        path = Path(found).resolve()
        if not gitutil.ok(path, ["rev-parse", "--git-dir"]):
            raise ExecutorError("REPOSITORY_UNKNOWN", f"{role!r} is not a git repository")
        return path

    def _base(self, repo: Path, ref: str) -> str:
        if ref.startswith("-"):
            raise ExecutorError("BASE_UNRESOLVED", "base ref may not start with '-'")
        out = gitutil.run(repo, ["rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"], check=False)
        if not re.fullmatch(r"[0-9a-f]{40,64}", out or ""):
            raise ExecutorError("BASE_UNRESOLVED", f"{ref!r} does not name a commit in {repo.name}")
        return out

    def check(self, request: StartRequest) -> str:
        """Refuse an unknown repository or base before anything exists; returns the commit the base ref names NOW, so the
        executor can pin it (a queued order or a restart must not start from whatever branch is checked out later)."""
        repo = self.repository(request.repository)
        self._root_commit(repo)
        return self._base(repo, request.base_ref)

    def _root_commit(self, repo: Path) -> None:
        """A brand-new repository (a greenfield plan: david-ui REQ-001 T1) has no commit to start an attempt from: the run would block on
        BASE_UNRESOLVED before the first task. One empty root commit gives it a base and changes no file."""
        if gitutil.run(repo, ["rev-list", "-n", "1", "--all"], check=False):
            return
        gitutil.run(repo, ["-c", "user.name=scheduler", "-c", "user.email=scheduler@localhost", "commit", "--allow-empty", "-q", "-m",
                           "chore: root commit (the scheduler needs a base to start from)"], check=False)

    # ------------------------------------------------------------------------------------------ allocation
    @contextmanager
    def _repo_lock(self, repo: Path):
        key = str(repo)
        with _LOCKS_GUARD:
            guard = _LOCKS.setdefault(key, threading.Lock())
        with guard:
            lock_dir = self.root / "locks"
            lock_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
            import fcntl
            with open(lock_dir / (hashlib.sha256(key.encode()).hexdigest()[:16] + ".lock"), "a+") as handle:
                fcntl.flock(handle, fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(handle, fcntl.LOCK_UN)

    def _journal(self, attempt_id: str, stage: str, **fields: object) -> str:
        path = self.root / "journal.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600), "a", encoding="utf-8") as stream:
            stream.write(json.dumps({"time": time.time(), "attempt_id": attempt_id, "stage": stage, **fields},
                                    sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        return str(path)

    def allocate(self, request: StartRequest) -> Workspace:
        repo = self.repository(request.repository)
        name = dirname_of(request.attempt_id)
        trees = self.root / "worktrees"
        # the branch and handoff refs live in the SHARED repo: scope them by this executor root so a second run of the
        # same plan (same attempt ids) never collides with, or overwrites, the first run's branches and refs
        scope = hashlib.sha256(str(self.root.resolve()).encode()).hexdigest()[:8]
        worktree, manifest, branch = trees / name, trees / f"{name}.json", f"m3/{name}-{scope}"
        with self._repo_lock(repo):
            self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
            trees.mkdir(parents=True, exist_ok=True, mode=0o700)
            if manifest.exists():
                data = json.loads(manifest.read_text(encoding="utf-8"))
                if data.get("attempt_id") != request.attempt_id or data.get("repo") != str(repo):
                    raise ExecutorError("WORKSPACE_ERROR", f"manifest {manifest.name} belongs to another attempt")
                base_sha = data["base_sha"]
            else:
                base_sha = self._base(repo, request.base_ref)
                tmp = manifest.with_name(f".{manifest.name}.tmp")
                tmp.write_text(json.dumps({"attempt_id": request.attempt_id, "repo": str(repo), "branch": branch,
                                           "base_sha": base_sha, "base_ref": request.base_ref,
                                           "worktree": str(worktree)}, sort_keys=True), encoding="utf-8")
                os.replace(tmp, manifest)
            journal = self._journal(request.attempt_id, "allocating", branch=branch, worktree=str(worktree),
                                    base_sha=base_sha)
            branch_exists = gitutil.ok(repo, ["show-ref", "--verify", "--quiet", f"refs/heads/{branch}"])
            if worktree.exists():
                if not self._registered(repo, worktree):
                    raise ExecutorError("WORKSPACE_ERROR", f"{worktree} exists but is not a worktree of {repo.name}")
            else:
                gitutil.run(repo, ["worktree", "prune"], check=False)
                args = ["worktree", "add", str(worktree), branch] if branch_exists else \
                       ["worktree", "add", "-b", branch, str(worktree), base_sha]
                gitutil.run(repo, args)
            self._journal(request.attempt_id, "allocated", branch=branch, worktree=str(worktree))
        return Workspace(path=str(worktree), branch=branch, base_sha=base_sha, repo=str(repo), journal=journal)

    @staticmethod
    def _registered(repo: Path, worktree: Path) -> bool:
        listing = gitutil.run(repo, ["worktree", "list", "--porcelain"], check=False)
        target = str(worktree.resolve())
        return any(line == f"worktree {target}" for line in listing.splitlines())

    def release(self, workspace: Workspace) -> None:
        """Explicit operator cleanup: remove the checkout and its branch. The handoff refs under refs/m3/ stay."""
        repo = Path(workspace.repo)
        with self._repo_lock(repo):
            gitutil.run(repo, ["worktree", "remove", "--force", workspace.path], check=False)
            gitutil.run(repo, ["branch", "-D", workspace.branch], check=False)
            self._journal(Path(workspace.path).name, "released", branch=workspace.branch)
