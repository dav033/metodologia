"""Git versioning + multi-machine sync of the bitácora. Never raises; never blocks a session for long.

The bitácora normally lives inside the `metodologia` monorepo (bitacora/ next to skill/). Auto-commits are scoped
to the bitácora folder only, so work-in-progress on the skill itself is never swept into them. After each commit a
detached `git push` runs in the background; `pull()` (SessionStart, before handing out IDs) brings other machines'
changes with `--rebase --autostash`.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import bt_nowindow  # noqa: F401  (no console windows on Windows)
from bt_platform import detached_options

GITIGNORE = ".state/\n__pycache__/\n*.tmp\n"


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
    from bt_lock import central_lock
    with central_lock("git"):  # one add/scan/commit at a time: concurrent sessions would fight over index.lock
        return _commit_locked(root, message, push)


def _commit_locked(root: Path, message: str, push: bool) -> bool:
    ensure_repo(root)
    if not _ok(_run(root, "add", "-A", "--", ".")):
        return False
    status = _run(root, "status", "--porcelain", "--", ".")
    if not status or not status.stdout.strip():
        return False
    from bt_secrets import clear_alert, scan_staged, set_alert
    clean, report = scan_staged(root)
    if not clean:  # never commit (or push) a secret: unstage and leave an alert for the next hook to surface
        _run(root, "reset", "-q", "--", ".")
        set_alert(root, report)
        return False
    clear_alert(root)
    if not _ok(_run(root, "commit", "-q", "-m", message, "--", ".")):
        return False
    if push:
        push_async(root)
    return True


def push_async(root: Path) -> None:
    if not has_remote(root):
        return
    try:
        subprocess.Popen(["git", "push", "-q"], cwd=root, **detached_options(), stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True)
    except OSError as exc:
        print(f"bitácora push could not start: {exc}", file=sys.stderr)


def pull(root: Path, timeout: int = 8) -> str:
    """Bring other machines' changes. Returns "" on success/offline/no remote/up to date, or a warning for the agent.

    Only the fetch is time-bounded: killing it loses nothing. The rebase is local and never killed, because a git
    killed between saving its autostash and applying it back leaves the working tree reset and the work in the stash
    (it happened on 2026-10-20: a slow pull at session start emptied the skill's uncommitted changes). Nor does it run
    while code outside the bitácora has uncommitted changes: rebasing stashes them for a moment and running schedulers
    import the skill lazily."""
    if not has_remote(root):
        return ""
    fetched = _run(root, "fetch", "-q", timeout=timeout)
    if fetched is None:
        return ""  # offline or slow: keep working with the local copy
    if fetched.returncode != 0:
        return f"bitácora sync failed (local copy kept, nothing lost): {_last_line(fetched)}"
    behind = _run(root, "rev-list", "--count", "HEAD..@{upstream}")
    if not _ok(behind) or behind.stdout.strip() in ("", "0"):
        return ""
    outside = _dirty_outside(root)
    if outside:
        return (f"bitácora sync skipped: other machines' changes are not applied while {outside} has uncommitted "
                "changes outside the bitácora; commit them, then pull")
    res = _run(root, "rebase", "--autostash", "-q", "@{upstream}", timeout=600)
    if res is None or res.returncode != 0:
        _run(root, "rebase", "--abort")
        return (f"bitácora sync failed (local copy kept; if work is missing, it is in `git stash list` as autostash): "
                f"{_last_line(res) if res else 'git did not finish'}")
    return ""


def _last_line(res: subprocess.CompletedProcess) -> str:
    return ((res.stderr or res.stdout).strip().splitlines()[-1:] or [""])[0][:200]


def _dirty_outside(root: Path) -> str:
    """The first changed path of the repository outside `root` (the bitácora), or ''."""
    top = _run(root, "rev-parse", "--show-toplevel")
    status = _run(root, "status", "--porcelain", "--untracked-files=no", "--", ":/")
    if not _ok(top) or not _ok(status):
        return ""
    try:
        inside = Path(root).resolve().relative_to(Path(top.stdout.strip()).resolve()).as_posix()
    except ValueError:
        return ""
    if inside in ("", "."):
        return ""                       # the bitácora is its own repository: nothing lives outside it
    for line in status.stdout.splitlines():
        path = line[3:].split(" -> ")[-1].strip('"')
        if not path.startswith(inside + "/"):
            return path
    return ""