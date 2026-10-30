"""After a selective integration (D-NNN): the full regression of the merge in the background, and the revert it
proposes when that regression is red. `bt_integrate.py --post-merge MERGE` and `--revert MERGE` land here.

A post-merge regression runs in a detached worktree of the merge (the live checkout's environment linked in: a
selective integration never changes dependencies), one at a time (`<state>/post-regress.lock`). Green: one line in the
release log. Red: a loud line in the release log, a notification and the revert command; nothing is reverted here.
The revert is the one a failed smoke runs (deploy worktree, `merge --ff-only` in the live checkout, push, restart,
smoke), under the integration lock.
"""
from __future__ import annotations

import datetime as dt
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import bt_integrate as integ

POST_WAIT_SECONDS = 6 * 3600                     # post-merge regressions queue behind each other, one at a time


def _stamp() -> str:
    return f"{dt.datetime.now():%Y%m%d-%H%M%S}"


def start(req: integ.Request, merge: str, log: Path, services: integ.Services, note: Callable[[str], None]) -> None:
    """Start the full regression of `merge` detached from this integration. A failure to start it is loud too."""
    script = Path(req.live) / "skill" / "scripts" / "bt_integrate.py"
    argv = [sys.executable, str(script), "--post-merge", merge, "--branch", req.branch, "--title", req.title,
            "--live", str(req.live), "--deploy", str(req.deploy), "--release-log", str(log)]
    argv += ["--session", req.session] if req.session else []
    safe = "".join(c if c.isalnum() or c in "-_" else "-" for c in req.branch)
    name = f"bt-post-regress-{safe}-{_stamp()}"
    try:
        where = services.spawn(argv, name, Path(req.deploy).parent / "post" / f"{name}.log")
    except OSError as error:
        note(f"WARNING the post-merge full regression could NOT start ({error}); run it: {' '.join(argv)}")
        integ._append(log, f"post-merge: full regression of {merge[:12]} could NOT start ({error}); "
                           f"run: {' '.join(argv)}\n")
        return
    note(f"post-merge: the full regression of {merge[:12]} runs in the background: {where}")
    integ._append(log, f"post-merge: full regression of {merge[:12]} started ({where})\n")


def _revert_command(req: integ.Request, merge: str) -> str:
    import shlex
    script = Path(req.live) / "skill" / "scripts" / "bt_integrate.py"
    return (f"python3 {script} --revert {merge} --branch {shlex.quote(req.branch)} --title {shlex.quote(req.title)}"
            + (f" --release-log {shlex.quote(str(req.log))}" if req.log else ""))


def post_merge(req: integ.Request, merge: str, services: integ.Services | None = None,
               say: Callable[[str], None] = print) -> int:
    """The full regression of an integrated merge, in a worktree of its own (the live checkout's environment linked
    in: a selective integration never changes dependencies). Green: one line in the release log. Red: a loud line,
    a notification and the revert command; nothing is reverted here. One post-merge run at a time."""
    services = services or integ.Services()
    log = req.log or integ.release_log()
    stamp, safe = _stamp(), req.branch.replace("/", "-")
    base = Path(req.deploy).parent
    worktree = base / "post" / f"{safe}-{stamp}"
    scratch = Path(req.scratch or base / "regress" / f"post-{safe}-{stamp}")
    results = scratch / "results.txt"
    lock = Path(req.lock or integ.lock_file()).with_name("post-regress.lock")
    command = _revert_command(req, merge)
    try:
        with integ.machine_lock(lock, POST_WAIT_SECONDS):
            worktree.parent.mkdir(parents=True, exist_ok=True)
            integ.git(req.live, "worktree", "add", "--detach", str(worktree), merge)
            venv = worktree / ".venv"
            if (Path(req.live) / ".venv").is_dir():
                venv.symlink_to(Path(req.live).resolve() / ".venv")
            try:
                result = services.regress(worktree, scratch, results)
            finally:
                if venv.is_symlink():
                    venv.unlink()
                integ.git(req.live, "worktree", "remove", "--force", str(worktree), check=False)
    except Exception as error:  # noqa: BLE001 - a post-merge check that cannot run must still be heard
        text = f"POST-MERGE FULL REGRESSION of {merge[:12]} ({req.branch}) could not run: {error}"
        integ._append(log, text + "\n")
        services.notify("metodologia: post-merge regression did not run", text)
        say(text)
        return 1
    if result.ok:
        text = f"post-merge full regression of {merge[:12]} ({req.branch}): {result.summary()} ({results}): green"
        integ._append(log, text + "\n")
        say(text)
        return 0
    text = (f"POST-MERGE FULL REGRESSION RED for {merge[:12]} ({req.branch}): {result.summary()} ({results}). "
            f"Main keeps the merge; nothing was reverted. Proposed revert: {command}")
    integ._append(log, text + "\n")
    services.notify("metodologia: post-merge regression RED",
                    f"{req.branch} ({merge[:12]}): {', '.join(result.real)}. Revert: {command}")
    say(text)
    return 1


def revert(req: integ.Request, merge: str, services: integ.Services | None = None,
           say: Callable[[str], None] = print) -> int:
    """Revert an integrated merge the way a failed smoke does (deploy worktree, ff-only, push, restart, smoke), under
    the integration lock. Exit 0 reverted, 1 refused before any change, 4 the revert failed (the owner must look)."""
    services = services or integ.Services()
    lines: list[str] = []

    def note(text: str) -> None:
        lines.append(text)
        say(text)

    try:
        with integ.machine_lock(req.lock or integ.lock_file(), req.wait_seconds):
            if integ.git(req.live, "symbolic-ref", "--short", "HEAD") != "main":
                raise integ.Refused(f"the live checkout {req.live} is not on main")
            full = integ.git(req.live, "rev-parse", "--verify", "-q", f"{merge}^{{commit}}", check=False)
            if not full or not integ.git(req.live, "rev-parse", "--verify", "-q", f"{full}^2", check=False):
                raise integ.Refused(f"{merge} is not a merge commit")
            if subprocess.run(["git", "-C", str(req.live), "merge-base", "--is-ancestor", full, "main"],
                              capture_output=True, check=False).returncode:
                raise integ.Refused(f"{merge} is not on main")
            paths = integ.git(req.live, "diff", "--name-only", f"{full}^1", full).splitlines()
            units = integ.units_for(integ.code_paths(paths))
            log = req.log or integ.release_log()
            integ._deploy_worktree(req)
            session = f", session {req.session}" if req.session else ""
            integ._append(log, f"\n# revert of the merge {full[:12]} of {req.branch} ({req.title}), "
                               f"{dt.datetime.now():%Y-%m-%d %H:%M}{session}\n")
            try:
                reverted = integ._revert(req, full, services, units, note)
            except integ.Refused as error:
                integ._append(log, f"result: revert FAILED: {error}\n")
                raise integ.Refused(f"the revert failed: {error}. The owner must look", 4) from error
            integ._append(log, f"result: reverted by {reverted[:12]}, restarted {', '.join(units) or 'nothing'}\n")
            return 0
    except integ.Refused as refused:
        note(f"REFUSED ({refused.code}): {refused}")
        return refused.code
