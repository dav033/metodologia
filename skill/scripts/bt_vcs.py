"""Git versioning + multi-machine sync of the bitácora. Never raises; never blocks a session for long.

The bitácora normally lives inside the `metodologia` monorepo (bitacora/ next to skill/). Auto-commits are scoped
to the bitácora folder only, so work-in-progress on the skill itself is never swept into them. After each commit a
detached `git push` runs in the background; `pull()` (SessionStart, before handing out IDs) brings other machines'
changes with `--rebase --autostash`.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

GITIGNORE = ".state/\n__pycache__/\n*.tmp\n"
_DETACHED = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)


def _run(root: Path, *args: str, timeout: int = 20) -> subprocess.CompletedProcess | None:
    try:
        return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=timeout)
    except Exception:
        return None


def _ok(res: subprocess.CompletedProcess | None) -> bool:
    return bool(res and res.returncode == 0)


def ensure_repo(root: Path) -> None:
    """Make sure the bitácora is versioned: inside a repo (the monorepo) or its own repo as a fallback."""
    root.mkdir(parents=True, exist_ok=True)
    if _ok(_run(root, "rev-parse", "--show-toplevel")):
        return
    if not _ok(_run(root, "init", "-q")):
        return
    gi = root / ".gitignore"
    if not gi.exists():
        gi.write_text(GITIGNORE, encoding="utf-8")
    res = _run(root, "config", "user.email")
    if not (res and res.stdout.strip()):
        _run(root, "config", "user.email", "bitacora@localhost")
        _run(root, "config", "user.name", "bitacora")


def has_remote(root: Path) -> bool:
    res = _run(root, "remote")
    return bool(res and res.stdout.strip())


def commit(root: Path, message: str, push: bool = True) -> bool:
    """Commit changes under `root` only (pathspec), then push in the background. Concurrent sessions may collide
    on the index lock; that's fine — the next commit picks the changes up."""
    ensure_repo(root)
    if not _ok(_run(root, "add", "-A", "--", ".")):
        return False
    status = _run(root, "status", "--porcelain", "--", ".")
    if not status or not status.stdout.strip():
        return False
    if not _ok(_run(root, "commit", "-q", "-m", message, "--", ".")):
        return False
    if push:
        push_async(root)
    return True


def push_async(root: Path) -> None:
    if not has_remote(root):
        return
    try:
        subprocess.Popen(["git", "push", "-q"], cwd=root, creationflags=_DETACHED, stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True)
    except Exception:
        pass


def pull(root: Path, timeout: int = 8) -> str:
    """Bring other machines' changes. Returns "" on success/offline/no remote, or a warning for the agent."""
    if not has_remote(root):
        return ""
    res = _run(root, "pull", "--rebase", "--autostash", "-q", timeout=timeout)
    if res is None:
        return ""  # offline or slow: keep working with the local copy
    if res.returncode != 0:
        _run(root, "rebase", "--abort")
        detail = (res.stderr or res.stdout).strip().splitlines()[-1:] or [""]
        return f"bitácora sync failed (local copy kept, nothing lost): {detail[0][:200]}"
    return ""
