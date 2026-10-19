"""Read-only host mounts a sandboxed check may see: the Node/Playwright toolchain and one attempt's dependencies.

Everything here is mounted read-only and only when it exists. The sandbox keeps no network, no home and no writable
host path, so exposing the interpreter and the dependency tree the attempt itself installed adds no new capability:
the check commands are already attempt-authored code.
"""

from __future__ import annotations

import functools
import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from .policy import QualityPolicy

WORKSPACE = "/workspace"
NODE_OPTIONS = "--max-old-space-size=6144"  # tsc and next build need more than Node's default heap
DEPENDENCY_DIRECTORIES = ("node_modules",)


@dataclass(frozen=True)
class Mount:
    """One read-only bind: an existing host directory shown at an absolute sandbox path."""

    source: str
    target: str


@dataclass(frozen=True)
class Toolchain:
    mounts: tuple[Mount, ...] = ()
    path: tuple[str, ...] = ()
    environment: tuple[tuple[str, str], ...] = ()


@functools.lru_cache(maxsize=8)
def _discover(search_path: str, browsers: str, home: str) -> Toolchain:
    mounts: list[Mount] = []
    path: list[str] = []
    environment: list[tuple[str, str]] = []
    node = shutil.which("node", path=search_path)
    if node:
        # <prefix>/bin/node -> mount <prefix>: npm, npx and the global node_modules live next to it.
        prefix = Path(node).resolve(strict=True).parent.parent
        if prefix != Path("/usr") and (prefix / "bin" / "node").is_file() and _under(prefix, Path(home)):
            mounts.append(Mount(str(prefix), str(prefix)))
            path.append(str(prefix / "bin"))
            environment.append(("NODE_OPTIONS", NODE_OPTIONS))
    cache = Path(browsers) if browsers else Path(home) / ".cache" / "ms-playwright"
    if cache.is_dir() and _under(cache, Path(home)):
        mounts.append(Mount(str(cache), str(cache)))
        environment.append(("PLAYWRIGHT_BROWSERS_PATH", str(cache)))
    return Toolchain(tuple(mounts), tuple(path), tuple(environment))


def _under(path: Path, parent: Path) -> bool:
    try:
        path.resolve(strict=True).relative_to(parent.resolve(strict=True))
    except (OSError, ValueError):
        return False
    return True


def toolchain(policy: QualityPolicy) -> Toolchain:
    """Node and the Playwright browser cache of the operator running the scheduler, or nothing when disabled."""
    if not policy.toolchain:
        return Toolchain()
    home = os.environ.get("HOME", "")
    if not home:
        return Toolchain()
    return _discover(os.environ.get("PATH", ""), os.environ.get("PLAYWRIGHT_BROWSERS_PATH", ""), home)


def attempt_mounts(
    policy: QualityPolicy,
    worktree: Path | None,
    repository: Path | None = None,
    snapshot_root: Path | None = None,
) -> tuple[Mount, ...]:
    """What the attempt installed in its own worktree, shown inside the snapshot workspace: the dependency
    directories and, for a linked git worktree, its git metadata so `git` commands see the real branch and refs.

    An attempt that never ran `npm install` has no dependencies of its own. The repository's installed ones then stand
    in, but only when the snapshot's lockfile is byte-identical to the repository's: the same lock means the same tree."""
    if not policy.toolchain or worktree is None:
        return ()
    mounts = []
    for name in DEPENDENCY_DIRECTORIES:
        source = _dependency_source(name, worktree, repository, snapshot_root)
        if source is not None:
            mounts.append(Mount(str(source), f"{WORKSPACE}/{name}"))
    mounts.extend(_git_mounts(worktree, repository))
    return tuple(mounts)


LOCKFILES = {"node_modules": "package-lock.json"}


def _dependency_source(name: str, worktree: Path, repository: Path | None, snapshot_root: Path | None) -> Path | None:
    own = worktree / name
    if own.is_dir() and not own.is_symlink() and _under(own, worktree):
        return own.resolve(strict=True)
    lock = LOCKFILES.get(name)
    if repository is None or snapshot_root is None or lock is None:
        return None
    shared = repository / name
    try:
        same_lock = (snapshot_root / lock).read_bytes() == (repository / lock).read_bytes()
    except OSError:
        return None
    if same_lock and shared.is_dir() and not shared.is_symlink() and _under(shared, repository):
        return shared.resolve(strict=True)
    return None


def _git_mounts(worktree: Path, repository: Path | None) -> tuple[Mount, ...]:
    """`<worktree>/.git` is a file `gitdir: <repository>/.git/worktrees/<name>`: show it, and the repository's git
    directory at the same absolute path, both read-only. Anything that does not match that exact layout is ignored."""
    if repository is None:
        return ()
    try:
        gitfile = worktree / ".git"
        if gitfile.is_symlink() or not gitfile.is_file():
            return ()
        text = gitfile.read_text(encoding="utf-8", errors="strict").strip()
        if not text.startswith("gitdir: "):
            return ()
        common = (repository / ".git").resolve(strict=True)
        gitdir = Path(text.removeprefix("gitdir: ")).resolve(strict=True)
        gitdir.relative_to(common / "worktrees")
    except (OSError, ValueError):
        return ()
    if not common.is_dir():
        return ()
    return (Mount(str(gitfile.resolve(strict=True)), f"{WORKSPACE}/.git"), Mount(str(common), str(common)))
