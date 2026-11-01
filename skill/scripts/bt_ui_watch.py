"""`components watch`: a change to the component pool reaches the projects with no manual step (D-293).

Owner, 2026-11-01: in development a change to `@bitacora/ui` must reach the project without a manual step or an
integration. A polling watcher, no dependencies: every `interval` seconds it takes a content digest of the source pool
(`skill/ui`, every file but README/.DS_Store/node_modules) and acts only when two consecutive polls agree on a digest
it has not acted on yet. An editor or a `git checkout` half-way through gives two different digests, so a half-written
tree is never carried anywhere; the wait is one interval (~2 s).

- default mode (no `--into`): the live checkout's pool; a new digest runs `bt_ui_sync.sync` for every project whose
  `project.json` says `ui.sync` (or the one `--project`), exactly what `bt_integrate` runs after a merge that changes
  `skill/ui/`: commit on the project's default branch, `push` as configured. Same digest, same tree: nothing. It waits
  while an integration holds the machine lock, so the integrate trigger syncs first and the watcher finds nothing to do
  (a smoke that reverts the merge leaves no sync of the reverted pool behind). The systemd unit
  `deploy/bitacora-ui-watch.service` runs this mode.
- dev mode (`--into PATH`): the `--from` pool (a worktree's `skill/ui`) written into `PATH/packages/bitacora-ui`
  without committing (`bt_ui_sync.write_dev`), so `next dev` there hot-reloads. The copy says `"dev": true` and the
  project's guard fails on it: it must never be committed or deployed. `--restore` puts the committed copy back.

A failed sync or write (dirty target, git lock, no default branch) is logged once for that digest and tried again only
when the pool changes: never a retry loop. A project without `ui.sync` is never touched. When its own code changes on
disk (a merge into the live checkout) the long-running watcher re-executes itself, so the unit needs no restart.
Log lines are English, on stdout (the journal under systemd).
"""
from __future__ import annotations

import fcntl
import hashlib
import os
import sys
import time
from collections.abc import Callable
from pathlib import Path

import bt_ui
import bt_ui_sync

POLL_SECONDS = 2.0
SKIP = {"README.md", ".DS_Store"}
OWN_CODE = ("bt_ui_watch.py", "bt_ui_sync.py", "bt_ui.py")


def log(text: str) -> None:
    print(f"{time.strftime('%H:%M:%S')} {text}", flush=True)


# ------------------------------------------------------------------------------------------------ what changed
def pool_digest(ui: Path) -> str | None:
    """Content digest of the whole source pool (themes included), or None while it cannot be read whole (missing, or a
    file vanished between listing and reading: a tree being written)."""
    ui = Path(ui)
    if not (ui / "package.json").is_file():
        return None
    h = hashlib.sha256()
    try:
        for p in sorted(ui.rglob("*")):
            rel = p.relative_to(ui)
            if p.is_file() and p.name not in SKIP and "node_modules" not in rel.parts:
                h.update(rel.as_posix().encode() + b"\0" + p.read_bytes() + b"\0")
    except OSError:
        return None
    return h.hexdigest()[:12]


def code_digest() -> str:
    here = Path(__file__).resolve().parent
    h = hashlib.sha256()
    for name in OWN_CODE:
        try:
            h.update((here / name).read_bytes())
        except OSError:
            h.update(b"missing")
    return h.hexdigest()


def integration_running() -> bool:
    """True while `bt_integrate` holds the machine lock (flock; a crashed holder frees it)."""
    import bt_core
    path = Path(bt_core.STATE) / "integrate.lock"
    if not path.is_file():
        return False
    try:
        with open(path, encoding="utf-8") as handle:
            fcntl.flock(handle, fcntl.LOCK_SH | fcntl.LOCK_NB)
            fcntl.flock(handle, fcntl.LOCK_UN)
    except BlockingIOError:
        return True
    except OSError:
        return False
    return False


class Watch:
    """Acts once per stable new digest. `act(digest) -> bool` (False: failed, already logged); `ready()` False makes
    a stable digest wait for the next poll."""

    def __init__(self, ui: Path, act: Callable[[str], bool], ready: Callable[[], bool] = lambda: True,
                 note: Callable[[str], None] = log):
        self.ui, self.act, self.ready, self.note = Path(ui), act, ready, note
        self.seen: str | None = None      # the previous poll's digest
        self.done: str | None = None      # the last digest acted on, successfully or not
        self.waiting = False
        self.failures = 0

    def poll(self) -> bool:
        """One poll; True when it acted."""
        digest = pool_digest(self.ui)
        stable = digest is not None and digest == self.seen
        self.seen = digest
        if not stable or digest == self.done:
            return False
        if not self.ready():
            if not self.waiting:
                self.note("an integration is running: waiting for it before syncing")
            self.waiting = True
            return False
        self.waiting = False
        self.done = digest
        if not self.act(digest):
            self.failures += 1
            self.note(f"pool {digest}: not carried; next try when the pool changes")
        return True


# ------------------------------------------------------------------------------------------------ the two modes
def sync_projects(projects: Callable[[], list[str]], note: Callable[[str], None] = log, root: Path | None = None,
                  ui: Path | None = None) -> Callable[[str], bool]:
    """Default mode's action: `bt_ui_sync.sync` for each project `projects()` names when the digest is new (read then,
    so a project that opts in later is included), failures logged (once: the watch acts once per digest)."""
    def act(digest: str) -> bool:
        ok = True
        for project in projects():
            try:
                r = bt_ui_sync.sync(project, root=root, ui=ui)
                note(f"pool {digest} -> {project}: {r['status']} {r['commit'][:12]} on {r['branch']} (package "
                     f"{r['pool']})" + (f", push: {r['pushed']}" if r["pushed"] not in (None, True)
                                        else ", pushed" if r["pushed"] else ""))
            except (bt_ui_sync.SyncError, OSError) as exc:
                ok = False
                note(f"WARNING pool {digest} not synced into {project}: {exc}")
        return ok
    return act


def write_into(project: str, ui: Path, tree: Path, note: Callable[[str], None] = log) -> Callable[[str], bool]:
    """Dev mode's action: the pool written into the working tree, uncommitted."""
    def act(digest: str) -> bool:
        try:
            r = bt_ui_sync.write_dev(project, ui, tree)
        except (bt_ui_sync.SyncError, OSError) as exc:
            note(f"WARNING pool {digest} not written into {tree}: {exc}")
            return False
        note(f"pool {digest} -> {r['path']}: {r['status']} (DEV copy, uncommitted: never commit or deploy it)")
        return True
    return act


def run(watch: Watch, interval: float = POLL_SECONDS, once: bool = False, sleep: Callable[[float], None] = time.sleep,
        reexec: bool = False, max_polls: int | None = None) -> int:
    """Poll until stopped. `once`: until the first action, then exit (0 ok, 1 failed). Ctrl-C leaves every file as
    it is."""
    code = code_digest() if reexec else ""
    polls = 0
    try:
        while max_polls is None or polls < max_polls:
            polls += 1
            acted = watch.poll()
            if once and acted:
                return 1 if watch.failures else 0
            if reexec and code_digest() != code:
                watch.note("the watcher's code changed: re-executing")
                os.execv(sys.executable, [sys.executable, *sys.argv])
            sleep(interval)
    except KeyboardInterrupt:
        watch.note("stopped; files are left as they are")
    return 1 if watch.failures else 0


# ------------------------------------------------------------------------------------------------ command line
def _project_of(tree: Path, root: Path) -> str:
    """The opted-in project whose UI repository `tree` is a working tree of (same git common dir)."""
    def common(path: Path) -> str:
        out = bt_ui_sync._git(path, "rev-parse", "--path-format=absolute", "--git-common-dir", check=False)
        return str(Path(out).resolve()) if out else ""
    mine, found = common(tree), []
    for project in bt_ui_sync.opted_in(root):
        try:
            repo = bt_ui_sync.repo_for(project, bt_ui_sync.config(project, root), root)
        except bt_ui_sync.SyncError:
            continue
        if mine and common(repo) == mine:
            found.append(project)
    if len(found) != 1:
        raise bt_ui_sync.SyncError(f"{tree}: " + ("no opted-in project uses this repository" if not found else
                                   f"several projects use it ({', '.join(found)})") + "; pass --project")
    return found[0]


def main(source: str | None, into: str | None, project: str | None, interval: float, once: bool,
         restore: bool, root: Path | None = None) -> int:
    from bt_core import ROOT
    root = Path(root or ROOT)
    ui = Path(source).expanduser().resolve() if source else bt_ui.UI
    if ui.name != "ui" and (ui / "skill" / "ui").is_dir():
        ui = ui / "skill" / "ui"                     # `--from <worktree>` is accepted too
    try:
        if restore:
            if not into:
                raise bt_ui_sync.SyncError("--restore needs --into PATH")
            log(f"{Path(into).expanduser()}: {bt_ui_sync.restore(Path(into))}")
            return 0
        if pool_digest(ui) is None:
            raise bt_ui_sync.SyncError(f"{ui} is not a component pool (no package.json)")
        if into:
            tree = bt_ui_sync.check_dev_target(Path(into))
            if project:
                if project not in bt_ui_sync.opted_in(root):
                    raise bt_ui_sync.SyncError(f"{project} does not opt in to the pool (project.json ui.sync)")
                if _project_of(tree, root) != project:
                    raise bt_ui_sync.SyncError(f"{tree} is not a working tree of {project}'s UI repository")
            else:
                project = _project_of(tree, root)
            watch = Watch(ui, write_into(project, ui, tree))
            log(f"DEV mode: {ui} -> {tree / bt_ui_sync.TARGET} ({project}), every {interval:g} s. The copy is NOT "
                "committed and its SYNC.json says dev: the project's guard fails on it; never commit or deploy it. "
                f"Afterwards: `bitacora.py components watch --into {tree} --restore`.")
        else:
            if ui.resolve() != bt_ui.UI.resolve():
                raise bt_ui_sync.SyncError("without --into the source is the live checkout's pool: committing an "
                                           "unintegrated pool onto a project's default branch is the integration's "
                                           "job; develop with --into PATH")
            if project and project not in bt_ui_sync.opted_in(root):
                raise bt_ui_sync.SyncError(f"{project} does not opt in to the pool (project.json ui.sync)")
            def projects() -> list[str]:
                return [p for p in bt_ui_sync.opted_in(root) if not project or p == project]
            watch = Watch(ui, sync_projects(projects, root=root), ready=lambda: not integration_running())
            log(f"watching {ui} every {interval:g} s for {project or 'every project with ui.sync'} "
                f"(now: {', '.join(projects()) or 'none'})")
    except bt_ui_sync.SyncError as exc:
        print(f"watch refused: {exc}", file=sys.stderr)
        return 1
    return run(watch, max(0.2, interval), once, reexec=not once)
