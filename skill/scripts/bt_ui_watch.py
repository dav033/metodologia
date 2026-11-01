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
  (a smoke that reverts the merge leaves no sync of the reverted pool behind). It also waits while the live checkout
  has uncommitted changes under `skill/ui` (D-295): the owner's half-written work is never committed onto a
  project's default branch; it is synced once committed. The systemd unit `deploy/bitacora-ui-watch.service` runs
  this mode.
- dev mode (`--into PATH`): the `--from` pool (a worktree's `skill/ui`) written into `PATH/packages/bitacora-ui`
  without committing (`bt_ui_sync.write_dev`), so `next dev` there hot-reloads. The copy says `"dev": true` and the
  project's guard fails on it: it must never be committed or deployed. `--restore` puts the committed copy back.
- `components dev [PROJECT]` (`dev`, D-295): dev mode with the owner's defaults: the live pool including uncommitted
  edits, into the main working tree of the project's UI repository, restored on Ctrl-C/SIGTERM/SIGHUP.

A failed sync or write (dirty target, git lock, no default branch) is logged once for that digest and tried again only
when the pool changes: never a retry loop. A project without `ui.sync` is never touched. When its own code changes on
disk (a merge into the live checkout) the long-running watcher re-executes itself, so the unit needs no restart.
Log lines are English, on stdout (the journal under systemd).
"""
from __future__ import annotations

import fcntl
import hashlib
import os
import signal
import subprocess
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


def pool_wip(ui: Path) -> str | None:
    """Why the live pool must not be committed anywhere yet: its checkout has uncommitted changes under `skill/ui`
    (the owner's work in progress, D-295), or git cannot tell. None when it is clean."""
    done = subprocess.run(["git", "-C", str(ui), "status", "--porcelain", "--untracked-files=all", "--", "."],
                          capture_output=True, text=True, check=False,
                          env={k: v for k, v in os.environ.items() if not k.startswith("GIT_")})
    if done.returncode:
        return f"git cannot tell whether {ui} is committed ({(done.stderr or '').strip()[-200:]})"
    if done.stdout.strip():
        return (f"{ui} has uncommitted changes (work in progress): not committed into any project until it is "
                "committed; `components dev` shows it in a project meanwhile")
    return None


def default_ready(ui: Path) -> Callable[[], str | None]:
    """Default mode's gate: no integration holding the machine lock, and a committed live pool."""
    return lambda: ("an integration is running: waiting for it" if integration_running() else None) or pool_wip(ui)


class Watch:
    """Acts once per stable new digest. `act(digest) -> bool` (False: failed, already logged); `ready()` returns why
    a stable digest must wait for a later poll (logged once per digest and reason), or None to act."""

    def __init__(self, ui: Path, act: Callable[[str], bool], ready: Callable[[], str | None] = lambda: None,
                 note: Callable[[str], None] = log):
        self.ui, self.act, self.ready, self.note = Path(ui), act, ready, note
        self.seen: str | None = None      # the previous poll's digest
        self.done: str | None = None      # the last digest acted on, successfully or not
        self.waiting: tuple[str, str] | None = None
        self.failures = 0

    def poll(self) -> bool:
        """One poll; True when it acted."""
        digest = pool_digest(self.ui)
        stable = digest is not None and digest == self.seen
        self.seen = digest
        if not stable or digest == self.done:
            return False
        reason = self.ready()
        if reason:
            if self.waiting != (digest, reason):
                self.note(f"pool {digest}: {reason}; waiting")
            self.waiting = (digest, reason)
            return False
        self.waiting = None
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


class Stopped(KeyboardInterrupt):
    """SIGTERM / SIGHUP (a closed terminal pane, `systemctl stop`): handled like Ctrl-C."""


def _stop(signum: int, _frame: object) -> None:
    raise Stopped(signal.Signals(signum).name)


def run(watch: Watch, interval: float = POLL_SECONDS, once: bool = False, sleep: Callable[[float], None] = time.sleep,
        reexec: bool = False, max_polls: int | None = None, on_stop: Callable[[], None] | None = None) -> int:
    """Poll until stopped. `once`: until the first action, then exit (0 ok, 1 failed). Ctrl-C, SIGTERM or SIGHUP
    run `on_stop` (the dev loop restores the committed package there); without it every file is left as it is."""
    code = code_digest() if reexec else ""
    polls = 0
    for sig in (signal.SIGTERM, signal.SIGHUP):
        try:
            signal.signal(sig, _stop)
        except (ValueError, OSError):                 # not the main thread (tests): Ctrl-C only
            pass
    try:
        while max_polls is None or polls < max_polls:
            polls += 1
            with _deferred_signals():                 # a stop never lands half-way through a write
                acted = watch.poll()
            if once and acted:
                return 1 if watch.failures else 0
            if reexec and code_digest() != code:
                watch.note("the watcher's code changed: re-executing")
                os.execv(sys.executable, [sys.executable, *sys.argv])
            sleep(interval)
    except KeyboardInterrupt:
        try:
            with _deferred_signals():                 # a second Ctrl-C waits for the restore, then is ignored
                if on_stop:
                    on_stop()
                else:
                    watch.note("stopped; files are left as they are")
        except KeyboardInterrupt:
            pass
    return 1 if watch.failures else 0


class _deferred_signals:
    """Ctrl-C / SIGTERM / SIGHUP held while the block runs and delivered right after it."""
    SIGNALS = (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)

    def __enter__(self) -> None:
        signal.pthread_sigmask(signal.SIG_BLOCK, self.SIGNALS)

    def __exit__(self, *exc: object) -> None:
        signal.pthread_sigmask(signal.SIG_UNBLOCK, self.SIGNALS)


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


def _source(source: str | None) -> Path:
    ui = Path(source).expanduser().resolve() if source else bt_ui.UI
    if ui.name != "ui" and (ui / "skill" / "ui").is_dir():
        ui = ui / "skill" / "ui"                     # `--from <worktree>` is accepted too
    if pool_digest(ui) is None:
        raise bt_ui_sync.SyncError(f"{ui} is not a component pool (no package.json)")
    return ui


def _opted(project: str, root: Path) -> str:
    if project not in bt_ui_sync.opted_in(root):
        raise bt_ui_sync.SyncError(f"{project} does not opt in to the pool (project.json ui.sync)")
    return project


def _dev_tree(tree: Path, project: str | None, root: Path) -> tuple[Path, str]:
    """A working tree a dev copy may go into, and its project (inferred from the repository when not given)."""
    tree = bt_ui_sync.check_dev_target(Path(tree))
    if not project:
        return tree, _project_of(tree, root)
    if _project_of(tree, root) != _opted(project, root):
        raise bt_ui_sync.SyncError(f"{tree} is not a working tree of {project}'s UI repository")
    return tree, project


def main(source: str | None, into: str | None, project: str | None, interval: float, once: bool,
         restore: bool, root: Path | None = None) -> int:
    from bt_core import ROOT
    root = Path(root or ROOT)
    try:
        if restore:
            if not into:
                raise bt_ui_sync.SyncError("--restore needs --into PATH")
            log(f"{Path(into).expanduser()}: {bt_ui_sync.restore(Path(into))}")
            return 0
        ui = _source(source)
        if into:
            tree, project = _dev_tree(Path(into), project, root)
            watch = Watch(ui, write_into(project, ui, tree))
            log(f"DEV mode: {ui} -> {tree / bt_ui_sync.TARGET} ({project}), every {interval:g} s. The copy is NOT "
                "committed and its SYNC.json says dev: the project's guard fails on it; never commit or deploy it. "
                f"Afterwards: `bitacora.py components watch --into {tree} --restore`.")
        else:
            if ui.resolve() != bt_ui.UI.resolve():
                raise bt_ui_sync.SyncError("without --into the source is the live checkout's pool: committing an "
                                           "unintegrated pool onto a project's default branch is the integration's "
                                           "job; develop with `components dev` or --into PATH")
            if project:
                _opted(project, root)
            def projects() -> list[str]:
                return [p for p in bt_ui_sync.opted_in(root) if not project or p == project]
            watch = Watch(ui, sync_projects(projects, root=root), ready=default_ready(ui))
            log(f"watching {ui} every {interval:g} s for {project or 'every project with ui.sync'} "
                f"(now: {', '.join(projects()) or 'none'}); only a committed pool is synced (uncommitted edits "
                "under skill/ui wait)")
    except bt_ui_sync.SyncError as exc:
        print(f"watch refused: {exc}", file=sys.stderr)
        return 1
    return run(watch, max(0.2, interval), once, reexec=not once)


def dev(project: str | None, source: str | None = None, into: str | None = None, interval: float = POLL_SECONDS,
        once: bool = False, restore: bool = False, keep: bool = False, root: Path | None = None) -> int:
    """`components dev [PROJECT]` (D-295): the owner's two-step loop. Edit the pool (the live checkout's `skill/ui`,
    uncommitted edits included, or `--from` a worktree's) and every page of the project that uses it hot-reloads in
    the `next dev` already running in its checkout: no commit, no integration, no restart. The target defaults to the
    main working tree of the project's UI repository (the owner's own checkout). On Ctrl-C, SIGTERM or SIGHUP the
    committed package is restored unless `keep`, so a forgotten loop never leaves a dirty tree."""
    from bt_core import ROOT
    root = Path(root or ROOT)
    try:
        if project:
            _opted(project, root)
        if into:
            tree = Path(into).expanduser().resolve()
        else:
            if not project:
                opted = bt_ui_sync.opted_in(root)
                if len(opted) != 1:
                    raise bt_ui_sync.SyncError("name the project: components dev PROJECT (opted in: "
                                               f"{', '.join(opted) or 'none'})")
                project = opted[0]
            repo = bt_ui_sync.repo_for(project, bt_ui_sync.config(project, root), root)
            tree = bt_ui_sync.main_worktree(repo)
        if restore:
            log(f"{tree / bt_ui_sync.TARGET}: {bt_ui_sync.restore(tree)}")
            return 0
        ui = _source(source)
        found = _project_of(tree, root)              # whose tree, then does its branch use the pool, then is it free
        if project and found != project:
            raise bt_ui_sync.SyncError(f"{tree} is not a working tree of {project}'s UI repository")
        warnings = bt_ui_sync.wiring(tree)
        tree, project = _dev_tree(tree, found, root)
    except bt_ui_sync.SyncError as exc:
        print(f"dev refused: {exc}", file=sys.stderr)
        return 1
    live = " (live checkout, uncommitted edits included)" if ui.resolve() == bt_ui.UI.resolve() else ""
    print(f"DEV loop for {project}: {ui}{live} -> {tree / bt_ui_sync.TARGET}, every {interval:g} s.\n"
          f"  Keep `npm run dev` running in {tree}: each saved pool change (stable ~{interval:g} s) is written there and "
          "every page using it hot-reloads; no commit, no integration, no restart.\n"
          "  WARNING: a DEV copy, uncommitted; its SYNC.json pool is \"dev-...\", so the project's guard fails on it on "
          f"purpose. Never commit or deploy it: no `git commit -a` / `git add -A` in {tree} while this runs.\n"
          + "".join(f"  WARNING: {w}\n" for w in warnings)
          + ("  Stop: Ctrl-C (or closing this terminal) leaves the dev copy (--keep); "
             f"`bitacora.py components dev {project} --into {tree} --restore` puts the committed package back."
             if keep else
             "  Stop: Ctrl-C (or closing this terminal) restores the committed package (--keep leaves the dev copy)."),
          flush=True)

    def stop() -> None:
        if keep:
            log(f"stopped; the DEV copy stays in {tree / bt_ui_sync.TARGET} (--keep)")
            return
        try:
            log(f"stopped; {tree / bt_ui_sync.TARGET}: {bt_ui_sync.restore(tree)} (the committed package)")
        except bt_ui_sync.SyncError as exc:
            log(f"WARNING stopped, nothing restored: {exc}")

    watch = Watch(ui, write_into(project, ui, tree))
    return run(watch, max(0.2, interval), once, reexec=not once, on_stop=stop)
