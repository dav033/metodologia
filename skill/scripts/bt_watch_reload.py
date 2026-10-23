"""Code reload for a running watch: a fix merged while a run is alive reaches the run without a person restarting anything.

The scheduler is long-lived (days) and Python loads its code once, so every fix of the engine used to need a hand-restart of the watcher
and the owner (REQ-020, 2026-10-22: seven times in one day). Two decisions, both about a fingerprint of the engine's `.py` files
(tests excluded):

- the WATCHER is stateless supervision: when the fingerprint changed and stayed the same for two checks (an edit still landing is not a
  release), it re-executes itself in place (same pid, same log);
- the OWNER holds the run's live work: it is restarted onto the new code at once when it has no live attempt; after PATIENCE_VERIFYING
  when only verifications are in flight (they lose a few minutes); after PATIENCE_BUSY when an agent works (`running`, `dispatched`,
  `reserved` would lose it). The run state is durable: the next owner resumes it.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

MARKER = "RUN.owner-code"
DIRTY = "dirty"                        # the working copy of the engine has uncommitted source edits: nothing is released
PATIENCE_VERIFYING = 1800.0            # seconds a pending reload waits while only verifications are in flight (the long gate takes 10-18 min: 600 s killed it mid-way)
PATIENCE_BUSY = 5400.0                 # ... while an agent works (a run that is never idle still gets the fix)
BUSY = frozenset({"running", "dispatched", "reserved"})


def committed_tree(root: Path) -> str | None:
    """The git tree id of the engine when its working copy is CLEAN (`DIRTY` when someone is still editing; None without git).
    Reloading onto an uncommitted half-edit could start an owner that crashes: only committed code is released."""
    import subprocess

    try:
        dirty = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--", "."], capture_output=True, text=True, timeout=20)
        tree = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD:" + _prefix(root)], capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    if dirty.returncode or tree.returncode:
        return None
    sources = [line for line in dirty.stdout.splitlines() if line[3:].endswith(".py") and "/tests/" not in line and not line[3:].startswith("tests/")]
    return DIRTY if sources else tree.stdout.strip()[:16]


def _prefix(root: Path) -> str:
    import subprocess

    out = subprocess.run(["git", "-C", str(root), "rev-parse", "--show-prefix"], capture_output=True, text=True, timeout=20).stdout.strip()
    return out.rstrip("/") or "."


def fingerprint(root: Path | str | None = None) -> str:
    """The committed engine's tree id (a fix counts once it is committed and the working copy is clean); the digest of (path, size, mtime)
    of the engine's `.py` files when there is no git."""
    root = Path(root) if root else Path(__file__).resolve().parent
    tree = committed_tree(root)
    if tree is not None:
        return tree
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*.py")):
        parts = path.relative_to(root).parts
        if "tests" in parts or "__pycache__" in parts or ".claude" in parts or any(p.startswith("worktree") for p in parts):
            continue
        try:
            stat = path.stat()
        except OSError:
            continue
        digest.update(f"{'/'.join(parts)}:{stat.st_size}:{stat.st_mtime_ns}\n".encode())
    return digest.hexdigest()[:16]


def read_marker(rdir: Path | str) -> str:
    try:
        return (Path(rdir) / MARKER).read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def write_marker(rdir: Path | str, value: str) -> None:
    try:
        (Path(rdir) / MARKER).write_text(value + "\n", encoding="utf-8")
    except OSError:
        pass


def decide(*, current: str, stable: bool, watcher_started_with: str, owner_started_with: str, owner_alive: bool,
           live_states: list[str], waited: float) -> str:
    """'reexec' (the watcher itself), 'restart_owner', or 'none'. `stable`: the fingerprint was the same at the previous check too;
    `waited`: seconds the owner has been running older code than the files."""
    if not stable or current == DIRTY or not current:
        return "none"
    if current != watcher_started_with:
        return "reexec"
    if owner_alive and owner_started_with and current != owner_started_with:
        if any(state in BUSY for state in live_states):
            return "restart_owner" if waited >= PATIENCE_BUSY else "none"
        if live_states:
            return "restart_owner" if waited >= PATIENCE_VERIFYING else "none"
        return "restart_owner"
    return "none"


def reexec(project: str, req: str) -> None:                  # pragma: no cover - replaces the process
    cli = Path(__file__).with_name("bitacora.py")
    import sys

    os.execv(sys.executable, [sys.executable, str(cli), "--project", project, "scheduler-watch", req])
