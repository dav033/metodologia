"""Integrate a metodologia branch into production: the procedure operators followed by hand on 2026-10-29 (REQ-031 T1).

Production of metodologia is this machine: `main` in the live checkout (`~/dev/metodologia`) plus the units that run
it (`bt-durable.service`, `bitacora-web.service`). The live checkout also holds the live bitácora (`~/bitacora` is a
symlink into it, with many uncommitted files): a `git merge --no-ff` there once refused the staged bitácora changes and
its abort reset them (D-160's integration). So the live checkout only ever sees `git merge --ff-only` and `git push`.

Under one machine-wide lock (flock on `<state>/integrate.lock`), in this order:
  1. preflight: the live checkout is on `main`; the branch is committed in its worktree, changes no `bitacora/` path
     and holds main's code: when main has code it lacks, main is merged into it in its worktree and this turn goes on
     (`catch_up`, D-260; a conflict is aborted there and refused with its files; bitácora commits on main are fine);
  2. regression of the branch worktree (`bt_regress`; only `integrate.allowed_failures` may fail, any other failure is
     rerun alone once); a red regression integrates nothing and the branch stays. By `integrate.regression` (D-NNN):
     `staged` (default) runs first the suites the changes can reach (`bt_regress_select`) and refuses at once when
     they are red, then the rest; `selective` (`--selective`) integrates on the selected suites alone and, after a
     passing smoke, starts the full regression of the merge in the background (`--post-merge`, its own transient
     unit): a red one is written to the release log, notified and answered with the revert command (`--revert
     MERGE`), never reverted silently; `full` (`--full`) skips the selection. An untrusted selection runs everything;
  3. when runtime code changed: a DBOS backup (never printing the database URL), and in every case the release-log
     entry (previous main, backup, regression, rollback line);
  4. `git checkout -B deploy-<branch> main` + `git merge --no-ff <branch>` in a separate deploy worktree;
  5. `git merge --ff-only deploy-<branch>` in the live checkout (one rebuild when a bitácora commit moved main between
     4 and 5); `git push origin main`;
  6. restart the units the changed paths need, smoke them (unit active, web answers 200, the engine journal says it
     started); a failed smoke reverts the merge the same way (deploy worktree, ff-only, restart) and says so. When the
     remote API's pinned release copy lacks what the merge changed in the paths it runs, the copy of the merge is made,
     the drop-in repinned and `bitacora-remote-api.service` restarted and smoked with the others; a failed smoke puts
     the previous pin back; a passing one prunes old copies (`bt_remote_pin`, D-274);
  7. after a passing smoke, clean up: when the branch's worktree is clean (no tracked change, no untracked file),
     `git worktree remove` it and `git branch -d` the branch (never -D). `--keep-worktree` skips this; a caller whose
     cwd is inside that worktree keeps it and gets the command instead; the live checkout and the deploy worktree are
     never removed. By 2026-10-29 integrations had left 14 merged worktrees and 64 merged branches behind.

usage: bt_integrate.py --branch B --worktree WT --title "what it does (D-NNN)" [--session ID] [--dry-run]
                       [--keep-worktree] [--selective | --full] ...
       bt_integrate.py --post-merge MERGE --branch B --title T     (what --selective starts in the background)
       bt_integrate.py --revert MERGE --branch B --title T         (the revert a red post-merge regression proposes)
Exit codes: 0 integrated, 1 refused before any change, 2 refused at the fast-forward (live unchanged), 3 smoke failed and
the merge was reverted, 4 the revert failed too (the owner must look), 75 another integration holds the lock.
"""
from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import hashlib
import os
import subprocess
import sys
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

import bt_package_modules as package_modules
import bt_remote_pin as remote_pin

LIVE = Path.home() / "dev" / "metodologia"
DEPLOY = Path.home() / ".local" / "share" / "bitacora-integrate" / "deploy"
ENGINE_UNIT, WEB_UNIT = "bt-durable.service", "bitacora-web.service"
DETACHED, RC_FILE = "BT_INTEGRATE_DETACHED", "BT_INTEGRATE_RC"   # set inside the integration's own unit
REGRESS_SLOT_WAIT = 7200.0                # a full regression is ~30 min; two queued at most
DRAIN_POLL = 10.0                       # seconds between looks at the running verifications
WEB_URL = "http://127.0.0.1:8765/"
STARTED = "bt_durable engine started"
ENV_FILE = Path.home() / ".config" / "bitacora" / "durable.env"
PG_CONTAINER = "metodologia-dbos-pg"
BITACORA = "bitacora/"
SMOKE_SECONDS = 90
BUSY = 75
MODES = ("staged", "selective", "full", "none")
# owner 2026-10-31 17:05: «hasta nuevo aviso no vamos a correr pruebas de regresión en metodología» (D-261). `none`
# integrates on preflight and smoke alone and writes every such integration to this ledger, where the defects a
# regression would have caught are recorded too (`--escaped`), so the owner can decide later with evidence.
LEDGER = "REGRESSION-OFF.md"


class Refused(RuntimeError):
    """The integration stopped; `code` says how far it got (see the module's exit codes)."""

    def __init__(self, message: str, code: int = 1):
        super().__init__(message)
        self.code = code


class Busy(Refused):
    def __init__(self, message: str):
        super().__init__(message, BUSY)


# ------------------------------------------------------------------------------------------------ pieces
@contextmanager
def machine_lock(path: Path, wait_seconds: float = 0.0, poll: float = 1.0) -> Iterator[None]:
    """One integration at a time on this machine. The lock is the kernel's (flock), so a crashed holder frees it."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = open(path, "a+", encoding="utf-8")        # noqa: SIM115 - held for the whole integration
    deadline = time.monotonic() + max(0.0, wait_seconds)
    queue = path.with_name(f"{path.name}.queue")         # first come, first served (D-230)
    queue.mkdir(exist_ok=True)
    ticket = queue / f"{time.time_ns():020d}-{os.getpid()}"
    ticket.touch()
    try:
        while True:
            if _first_in(queue, ticket):
                try:
                    fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    pass
            if time.monotonic() >= deadline:
                handle.seek(0)
                holder = handle.read().strip()[:200]
                raise Busy(f"another integration holds {path}" + (f" ({holder})" if holder else "")) from None
            time.sleep(poll)
        ticket.unlink(missing_ok=True)
        handle.seek(0)
        handle.truncate()
        handle.write(f"pid {os.getpid()} since {dt.datetime.now().isoformat(timespec='seconds')}\n")
        handle.flush()
        yield
    finally:
        ticket.unlink(missing_ok=True)
        handle.close()                                   # closing the descriptor releases the flock


def _first_in(queue: Path, ticket: Path) -> bool:
    """Is `ticket` the oldest live waiter? Tickets of dead waiters are removed. flock alone is not fair: whoever polls
    at the right moment wins, and on 2026-10-30 an integration waited 90 min while three later ones went first (D-230)."""
    for entry in sorted(queue.iterdir()):
        if entry == ticket:
            return True
        try:
            os.kill(int(entry.name.rsplit("-", 1)[1]), 0)
        except (ValueError, IndexError, ProcessLookupError):
            entry.unlink(missing_ok=True)
            continue
        except PermissionError:
            pass
        return False
    return True


def git(cwd: Path, *args: str, check: bool = True) -> str:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    done = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, env=env, check=False)
    if check and done.returncode:
        raise Refused(f"git {' '.join(args[:3])} in {cwd} failed: {(done.stderr or done.stdout).strip()[-400:]}")
    return done.stdout.strip() if not done.returncode else ""


# how many times one turn merges main again when it moved during the regression, before giving the turn up
CATCH_UP_RUNS = 2

# what the live venv's install is made from: a merge that changes one refreshes it before the restart (D-277)
VENV_PATHS = ("pyproject.toml", "uv.lock")
VENV_SYNC_SECONDS = 600

def runtime_path(path: str) -> bool:
    """Code a running unit imports: the engine and the web load ~30 skill/scripts modules lazily, so any of them counts."""
    if path in VENV_PATHS:
        return True
    return path.startswith("skill/scripts/") and "/tests/" not in path and \
        (path.endswith(".py") or path.startswith("skill/scripts/bt_durable/deploy/"))


def units_for(paths: list[str]) -> list[str]:
    """Which units a change needs restarted: runtime code -> engine and web; web assets -> web; anything else none."""
    units = []
    if any(runtime_path(p) for p in paths):
        units = [ENGINE_UNIT, WEB_UNIT]
    elif any(p.startswith("skill/assets/") for p in paths):
        units = [WEB_UNIT]
    return units


def _units(req: "Request", paths: list[str]) -> list[str]:
    """`units_for` plus the remote API when this integration owns its pin and the pinned copy will lack what `paths`
    change (or already lacks main's) in the paths the listener runs (D-274)."""
    units = units_for(paths)
    if req.remote is not None and remote_pin.UNIT not in units and (
            any(remote_pin.relevant(p) for p in paths) or remote_pin.stale(req.remote, req.live, "main")):
        units.append(remote_pin.UNIT)
    return units


def code_paths(paths: list[str]) -> list[str]:
    return [p for p in paths if p and not p.startswith(BITACORA)]


def ledger() -> Path:
    import bt_core
    return Path(bt_core.ROOT) / "metodologia" / LEDGER


def _ledger_add(section: str, line: str, path: Path | None = None) -> None:
    """Append `line` under `section` («Integrated without regression» / «Escaped defects») of the ledger."""
    path = path or ledger()
    text = path.read_text(encoding="utf-8") if path.exists() else (
        "# Integrations without regression (D-261)\n\nOwner, 2026-10-31 17:05: until further notice metodologia "
        "integrations run no regression tests (`integrate.regression: none`). Every integration made that way is "
        "listed here, and so is every defect found later that a regression would have caught, to decide with "
        "evidence whether to turn regressions back on.\n\n## Integrated without regression\n\n## Escaped defects\n")
    head = f"## {section}\n"
    at = text.index(head) + len(head)
    following = text.find("\n## ", at)
    end = len(text) if following < 0 else following
    body = text[at:end].rstrip("\n")
    text = text[:at] + (body + "\n" if body.strip() else "\n") + line.rstrip("\n") + "\n" + text[end:]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def record_escape(text: str, merge: str = "", path: Path | None = None) -> None:
    """A defect found after an integration without regression that a regression would have caught."""
    _ledger_add("Escaped defects", f"- {dt.datetime.now():%Y-%m-%d %H:%M}" + (f" · merge `{merge[:12]}`" if merge else "")
                + f" · {text}", path)


def release_log() -> Path:
    import bt_core
    found = sorted((Path(bt_core.ROOT) / "metodologia" / "requirements").glob(
        "REQ-030-*/evidence/iter2/pre-deploy.txt"))
    return found[0] if found else Path(bt_core.ROOT) / "metodologia" / "releases.txt"


def lock_file() -> Path:
    import bt_core
    return Path(bt_core.STATE) / "integrate.lock"


# --------------------------------------------------------------------------------------- side effects
class Services:
    """What touches the machine beyond git: the regression, the database backup, the units. Tests pass a fake."""

    def regress(self, worktree: Path, scratch: Path, out: Path, selection=None, mode: str = "full"):
        """One full regression at a time on this machine (`<state>/regress-slot.lock`), integrations and post-merge
        runs alike: on 2026-10-30 three ran at once (a post-merge run took 1 h 40) and the shared load produced the
        «load flake, passes alone» lines that every integration then had to judge (D-220)."""
        import bt_regress
        with machine_lock(Path(lock_file()).with_name("regress-slot.lock"), REGRESS_SLOT_WAIT):
            return bt_regress.staged(worktree, scratch, out, selection=selection, mode=mode)

    def select(self, worktree: Path):
        """The suites the branch's changes can reach (bt_regress_select), diffed against main."""
        import bt_regress_select
        return bt_regress_select.select(worktree, base="main")

    def spawn(self, argv: list[str], name: str, log: Path) -> str:
        """Start `argv` detached from this integration (and from the units it restarts): a transient user unit when
        systemd is there, else a new session. Returns where it runs."""
        env = [f"--setenv={k}={os.environ[k]}" for k in ("PATH", "BITACORA_ROOT", "HOME") if os.environ.get(k)]
        done = subprocess.run(["systemd-run", "--user", f"--unit={name}", "--collect", "--quiet", *env, *argv],
                              capture_output=True, text=True, check=False) if _which("systemd-run") else None
        if done is not None and done.returncode == 0:
            return f"unit {name} (journalctl --user -u {name})"
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a", encoding="utf-8") as out:
            process = subprocess.Popen(argv, stdout=out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                       start_new_session=True)
        return f"pid {process.pid} (log {log})"

    def notify(self, title: str, message: str) -> None:
        import bt_notify
        bt_notify.notify(title, message)

    def backup(self) -> str:
        """pg_dump (custom format) of the live DBOS database, or a copy of the SQLite one, 0600 with its SHA-256.
        Returns `<path> <bytes> <sha256>`. The URL (with its password) is never printed."""
        import bt_core
        from urllib.parse import unquote, urlparse
        url = os.environ.get("BT_DURABLE_DATABASE_URL", "")
        if not url and ENV_FILE.is_file():
            url = next((line.split("=", 1)[1].strip().strip('"') for line in ENV_FILE.read_text().splitlines()
                        if line.startswith("BT_DURABLE_DATABASE_URL=")), "")
        out_dir = Path(bt_core.STATE) / "durable" / "backups"
        out_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        stamp = f"{dt.datetime.now():%Y%m%d-%H%M%S}"
        if url.startswith("postgres"):
            u = urlparse(url)
            out = out_dir / f"bt_durable-{stamp}.dump"
            with open(os.open(out, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as fh:
                done = subprocess.run(["docker", "exec", "-e", f"PGPASSWORD={unquote(u.password or '')}", PG_CONTAINER,
                                       "pg_dump", "-Fc", "-h", "127.0.0.1", "-p", "5432", "-U", unquote(u.username or ""),
                                       u.path.lstrip("/")], stdout=fh, stderr=subprocess.PIPE, check=False)
            if done.returncode or out.stat().st_size == 0:
                raise Refused(f"pg_dump failed: {done.stderr.decode(errors='replace')[:300]}")
        else:
            import sqlite3
            source = Path(bt_core.STATE) / "durable" / "dbos.sqlite3"
            if not source.is_file():
                raise Refused("no DBOS database to back up (no PostgreSQL URL and no SQLite file)")
            out = out_dir / f"bt_durable-{stamp}.sqlite3"
            os.close(os.open(out, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600))
            with sqlite3.connect(source) as src, sqlite3.connect(out) as dst:
                src.backup(dst)
        digest = hashlib.sha256(out.read_bytes()).hexdigest()
        side = out.with_name(out.name + ".sha256")
        side.write_text(f"{digest}  {out}\n", encoding="utf-8")
        side.chmod(0o600)
        return f"{out} {out.stat().st_size} {digest}"

    def push(self, live: Path) -> str:
        done = subprocess.run(["git", "-C", str(live), "push", "origin", "main"], capture_output=True, text=True,
                              check=False)
        return "" if done.returncode == 0 else (done.stderr or done.stdout).strip()[-300:]

    def verifying(self) -> list[str]:
        """The verifications the engine is running now: M6 requests in state `running` (read-only, stdlib sqlite)."""
        import bt_core
        import sqlite3
        store = Path(bt_core.STATE) / "durable" / "m6-quality.sqlite3"
        if not store.is_file():
            return []
        try:
            with sqlite3.connect(f"file:{store}?mode=ro", uri=True, timeout=5) as db:
                return [row[0] for row in db.execute("SELECT idempotency_key FROM requests WHERE state='running'")]
        except sqlite3.Error:
            return []

    def drain(self, timeout: float) -> tuple[float, list[str]]:
        """Wait until no verification runs (or `timeout`): (seconds waited, verifications still running)."""
        started = time.monotonic()
        running = self.verifying()
        while running and time.monotonic() - started < timeout:
            time.sleep(DRAIN_POLL)
            running = self.verifying()
        return time.monotonic() - started, running

    def daemon_reload(self) -> None:
        done = subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True, text=True, check=False)
        if done.returncode:
            raise remote_pin.PinError(f"systemctl daemon-reload failed: {done.stderr.strip()[:200]}")

    def restart(self, unit: str) -> None:
        done = subprocess.run(["systemctl", "--user", "restart", unit], capture_output=True, text=True, check=False)
        if done.returncode:
            raise Refused(f"systemctl restart {unit} failed: {done.stderr.strip()[:200]}", 3)

    def smoke(self, units: list[str], since: float) -> list[str]:
        """What is still wrong after SMOKE_SECONDS: an inactive unit, a web that does not answer 200, an engine whose
        journal never said it started, a remote API that does not answer HTTP."""
        import urllib.request
        deadline = time.monotonic() + SMOKE_SECONDS
        while True:
            problems = []
            for unit in units:
                state = subprocess.run(["systemctl", "--user", "is-active", unit], capture_output=True, text=True,
                                       check=False).stdout.strip()
                if state != "active":
                    problems.append(f"{unit} is {state or 'unknown'}")
            if WEB_UNIT in units:
                try:
                    with urllib.request.urlopen(WEB_URL, timeout=10) as response:
                        if response.status != 200:
                            problems.append(f"web answered {response.status}")
                except OSError as error:
                    problems.append(f"web did not answer: {error}")
            if ENGINE_UNIT in units:
                journal = subprocess.run(["journalctl", "--user", "-u", ENGINE_UNIT, "--since", f"@{int(since)}",
                                          "--no-pager", "-o", "cat"], capture_output=True, text=True, check=False).stdout
                if STARTED not in journal:
                    problems.append(f"the engine journal has no «{STARTED}» since the restart")
            if remote_pin.UNIT in units:
                problems += [p for p in [remote_pin.answers()] if p]
            if not problems or time.monotonic() >= deadline:
                return problems
            time.sleep(3)

    def refresh_venv(self, live: Path) -> str:
        """Reinstall the live checkout's project into its venv from the lock (`uv sync --frozen`: the lock is never
        rewritten; `--inexact` removes nothing, like the engine's own `uv run`; the project reinstalled so its editable
        finder maps the current py-modules). "" when it worked, else why not."""
        import shutil
        live = Path(live)
        name = tomllib_name(live / "pyproject.toml")
        uv = shutil.which("uv") or str(Path.home() / ".local" / "bin" / "uv")
        env = {k: v for k, v in os.environ.items() if k not in ("VIRTUAL_ENV", "UV_PROJECT_ENVIRONMENT")}
        try:
            done = subprocess.run([uv, "sync", "--frozen", "--inexact", "--quiet", "--reinstall-package", name],
                                  cwd=str(live), env=env, capture_output=True, text=True, timeout=VENV_SYNC_SECONDS,
                                  check=False)
        except (OSError, subprocess.SubprocessError) as error:
            return f"uv sync could not run: {error}"
        return "" if done.returncode == 0 else f"uv sync failed: {(done.stderr or done.stdout).strip()[-300:]}"

    def install_problems(self, live: Path) -> list[str]:
        """What the live venv cannot import of the distribution pyproject.toml lists (`bt_package_modules`)."""
        return package_modules.install_problems(Path(live) / ".venv" / "bin" / "python", Path(live))


def tomllib_name(pyproject: Path) -> str:
    import tomllib
    return tomllib.loads(Path(pyproject).read_text(encoding="utf-8")).get("project", {}).get("name", "bitacora")


def _which(command: str) -> bool:
    import shutil
    return shutil.which(command) is not None


# ------------------------------------------------------------------------------------------ the procedure
@dataclass
class Request:
    branch: str
    worktree: Path
    title: str
    session: str = ""
    live: Path = LIVE
    deploy: Path = DEPLOY
    scratch: Path | None = None
    log: Path | None = None
    lock: Path | None = None
    wait_seconds: float = 3600.0
    trailers: list[str] = field(default_factory=list)
    dry_run: bool = False
    keep_worktree: bool = False
    cwd: Path | None = None                      # the caller's working directory (default: this process's)
    regression: str = ""                         # staged | selective | full | none; "" = integrate.regression
    ledger: Path | None = None                   # D-261's ledger (tests); default <bitácora>/metodologia/REGRESSION-OFF.md
    remote: remote_pin.Pin | None = None         # the remote API's pin this integration refreshes (the CLI on the live
                                                 # checkout sets it; None leaves the listener alone, D-274)


@dataclass
class Outcome:
    code: int
    lines: list[str]
    merge: str = ""


def catch_up(req: Request, note: Callable[[str], None] = lambda text: None) -> str:
    """Merge main into the branch in its own worktree (never the live checkout), keeping this integration's turn in the
    queue. A conflict is aborted in that worktree and refused with its files. Returns the new tip, or "" when main had
    nothing for it. 2026-10-31: 13 of 33 integrations were refused for «main has code the branch lacks» and went back
    to the end of the queue after a hand merge (D-260)."""
    if not code_paths(git(req.live, "diff", "--name-only", f"{req.branch}...main").splitlines()):
        return ""
    merged = subprocess.run(["git", "-C", str(req.worktree), "merge", "--no-edit", "-q", "main"], capture_output=True,
                            text=True)
    if merged.returncode != 0:
        conflicts = git(req.worktree, "diff", "--name-only", "--diff-filter=U", check=False).splitlines()
        git(req.worktree, "merge", "--abort", check=False)
        detail = ", ".join(conflicts[:4]) or merged.stderr.strip()[:200]
        raise Refused(f"main has code {req.branch} lacks and merging it conflicts ({detail}): resolve the merge in its "
                      "worktree, commit, then run this again")
    tip = git(req.worktree, "rev-parse", "HEAD")
    note(f"merged main into {req.branch} in its worktree ({tip[:12]}): this turn continues with it")
    return tip


def preflight(req: Request, note: Callable[[str], None] = lambda text: None) -> list[str]:
    """Refuse what the procedure cannot integrate safely; returns the branch's changed paths. Main's newer code is
    merged into the branch first (`catch_up`)."""
    if git(req.live, "symbolic-ref", "--short", "HEAD") != "main":
        raise Refused(f"the live checkout {req.live} is not on main: nothing is integrated there")
    tip = git(req.live, "rev-parse", "--verify", f"refs/heads/{req.branch}^{{commit}}", check=False)
    if not tip:
        raise Refused(f"branch {req.branch} does not exist")
    if git(req.worktree, "rev-parse", "HEAD") != tip:
        raise Refused(f"{req.worktree} is not at {req.branch}'s tip: the regression must test what is merged")
    if git(req.worktree, "status", "--porcelain", "--untracked-files=no"):
        raise Refused(f"{req.worktree} has uncommitted changes: commit them first")
    if Path(req.worktree).resolve() == Path(req.live).resolve():
        raise Refused("the branch worktree is the live checkout: work in a worktree of your own")
    paths = git(req.live, "diff", "--name-only", f"main...{req.branch}").splitlines()
    if not paths:
        raise Refused(f"{req.branch} changes nothing that main lacks")
    touched = [p for p in paths if p.startswith(BITACORA)]
    if touched:
        raise Refused(f"{req.branch} changes the live bitácora ({', '.join(touched[:3])}): bitácora files are written "
                      "in ~/bitacora directly, never merged")
    catch_up(req, note)
    drifted = module_drift(req)
    if drifted:
        raise Refused(f"{req.branch} would integrate a distribution the live venv cannot install whole: {drifted} "
                      "(D-277)")
    return git(req.live, "diff", "--name-only", f"main...{req.branch}").splitlines()


def module_drift(req: Request) -> str:
    """Why the branch's tree (with main merged in) does not package every skill/scripts module, or "" when it does.
    Checked on every integration, whatever the regression setting: with it off (D-261) nothing else ran
    `test_package_modules`, and five unlisted modules stopped the engine (D-277). A tree without pyproject.toml is not
    this repository's shape and is not checked."""
    import tomllib
    text = git(req.live, "show", f"{req.branch}:pyproject.toml", check=False)
    if not text:
        return ""
    try:
        if "py-modules" not in package_modules.setuptools_table(text):
            return ""                                # modules not listed by hand: nothing can drift
    except tomllib.TOMLDecodeError as error:
        return f"pyproject.toml does not parse ({error})"
    prefix = package_modules.SCRIPTS + "/"
    files = [p[len(prefix):] for p in git(req.live, "ls-tree", "--name-only", req.branch, prefix).splitlines()]
    return package_modules.drift_message(*package_modules.drift(files, text))


def _deploy_worktree(req: Request) -> Path:
    """The deploy worktree, created when missing; refused when it is not this repository's or holds changes."""
    deploy = Path(req.deploy)
    if not (deploy / ".git").exists():
        deploy.parent.mkdir(parents=True, exist_ok=True)
        git(req.live, "worktree", "prune")
        git(req.live, "worktree", "add", "--detach", str(deploy), "main")
    if Path(git(deploy, "rev-parse", "--path-format=absolute", "--git-common-dir")).resolve() != \
            Path(git(req.live, "rev-parse", "--path-format=absolute", "--git-common-dir")).resolve():
        raise Refused(f"{deploy} is not a worktree of {req.live}")
    if git(deploy, "status", "--porcelain", "--untracked-files=no"):
        raise Refused(f"the deploy worktree {deploy} has uncommitted changes")
    return deploy


def _deploy_merge(req: Request) -> str:
    """deploy-<branch> = main + merge --no-ff <branch>, in the deploy worktree. Returns the merge commit."""
    deploy = _deploy_worktree(req)
    git(deploy, "checkout", "-q", "-B", f"deploy-{req.branch}", "main")
    message = "\n\n".join([f"Merge {req.branch}: {req.title}", *(["\n".join(req.trailers)] if req.trailers else [])])
    git(deploy, "merge", "--no-ff", "-q", "-m", message, req.branch)
    return git(deploy, "rev-parse", "HEAD")


def _drop_branch(req: Request, name: str) -> None:
    """The deploy worktree's own branch is history once main holds it: detach the worktree on main and delete the
    branch with -d (never -D). 17 merged deploy-* branches had piled up by 2026-10-30 (D-220)."""
    deploy = Path(req.deploy)
    git(deploy, "checkout", "-q", "--detach", "main", check=False)
    git(req.live, "branch", "-d", "-q", name, check=False)


def _fast_forward(req: Request, ref: str) -> bool:
    """`git merge --ff-only` in the live checkout: the only write it ever gets. False when git refused."""
    git(req.live, "merge", "--ff-only", "-q", ref, check=False)
    return git(req.live, "rev-parse", "HEAD") == git(req.live, "rev-parse", ref)


def _entry(req: Request, previous: str, backup: str, regression: str, units: list[str]) -> str:
    names = {ENGINE_UNIT: "engine", WEB_UNIT: "web", remote_pin.UNIT: "remote API"}
    restarted = " + ".join(names.get(u, u) for u in units) or "no unit"
    session = f", session {req.session}" if req.session else ""
    return (f"\n# integration of {req.title}, local restart of {restarted}, "
            f"{dt.datetime.now():%Y-%m-%d %H:%M}{session}\n"
            f"previous main: {previous}\n"
            f"{backup or 'backup: not needed (no runtime code changed)'}\n"
            f"regression: {regression}\n"
            f"rollback: git revert the merge of {req.branch} on main"
            + (f", restart {' and '.join(units)}" if units else "") + "\n")


def _append(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(text)


def integrate(req: Request, services: Services | None = None, say: Callable[[str], None] = print) -> Outcome:
    services = services or Services()
    lines: list[str] = []

    def note(text: str) -> None:
        lines.append(text)
        say(text)

    try:
        with machine_lock(req.lock or lock_file(), req.wait_seconds):
            return _integrate(req, services, note, lines)
    except Refused as refused:
        note(f"REFUSED ({refused.code}): {refused}")
        return Outcome(refused.code, lines)


def regression_mode(req: Request) -> str:
    if req.regression:
        return req.regression
    try:
        import bt_config
        mode = bt_config.get("integrate.regression", MODES[0])
    except Exception:  # noqa: BLE001 - outside a bitácora the default holds
        mode = MODES[0]
    return mode if mode in MODES else MODES[0]


def _selection(req: Request, services: Services, mode: str, note: Callable[[str], None]):
    """The selection for a staged or selective run, or None (a full run). It never stops an integration: a selection
    that cannot be made is a full regression."""
    if mode == "full":
        note("regression: full (no selection)")
        return None
    try:
        selection = services.select(Path(req.worktree))
    except Exception as error:  # noqa: BLE001 - the full regression is always safe
        note(f"selection failed ({error}): full regression")
        return None
    for line in selection.describe() if req.dry_run else [selection.headline()]:
        note(line)
    if mode == "selective" and not selection.trusted:
        note("selective requested, but the selection is not trusted: full regression first")
    return selection


def _integrate(req: Request, services: Services, note: Callable[[str], None], lines: list[str]) -> Outcome:
    paths = preflight(req, note)
    units = _units(req, paths)
    note(f"preflight ok: {len(paths)} path(s) changed; restart: {', '.join(units) or 'none'}")
    if remote_pin.UNIT in units and req.remote is not None:
        pinned = remote_pin.current(req.remote)
        note(f"remote API: pinned to {pinned[:12]}, repinned to the merge after it lands" if pinned else
             "remote API: runs no release copy, restarted after the merge")
    mode = regression_mode(req)
    selection = None if mode == "none" else _selection(req, services, mode, note)
    if mode == "none":
        note("regression: skipped (integrate.regression = none: owner, 2026-10-31, until further notice; D-261)")
    if req.dry_run:
        return Outcome(0, lines)
    selective = mode == "selective" and selection is not None and selection.trusted
    start_main = git(req.live, "rev-parse", "main")
    scratch = Path(req.scratch or Path(req.deploy).parent / "regress" /     # fresh roots for every run
                   f"{req.branch.replace('/', '-')}-{dt.datetime.now():%Y%m%d-%H%M%S}")
    results = scratch / "results.txt"
    for attempt in range(0 if mode == "none" else CATCH_UP_RUNS + 1):
        regression = services.regress(Path(req.worktree), scratch, results, selection=selection, mode=mode)
        note(f"regression: {regression.summary()} ({results})")
        if not regression.ok:
            stage = "the selected suites are" if getattr(regression, "stopped", "") else "the regression is"
            raise Refused(f"{stage} red ({', '.join(regression.real)}): nothing was integrated, {req.branch} stays")
        moved = code_paths(git(req.live, "diff", "--name-only", start_main, "main").splitlines())
        if not moved:
            break
        if attempt == CATCH_UP_RUNS:
            raise Refused(f"main moved with code while the regression ran ({', '.join(moved[:3])}), "
                          f"{CATCH_UP_RUNS + 1} times: merge main into {req.branch} and run this again")
        start_main = git(req.live, "rev-parse", "main")
        catch_up(req, note)
        paths = git(req.live, "diff", "--name-only", f"main...{req.branch}").splitlines()
        units = _units(req, paths)
        if not set(moved) & set(paths):
            # owner 2026-10-31 («perdemos mucho tiempo»): main's new code touches none of the branch's files, so the
            # merged tree is integrated on this regression and the full regression of the merge runs in the background
            # after the smoke, like `selective`: a red one is loud and proposes the revert, never reverts silently
            note(f"main moved with code while the regression ran ({', '.join(moved[:3])}), none of it in "
                 f"{req.branch}'s files: merged, integrating; the full regression of the merge runs after the smoke")
            selective = True
            break
        note(f"main moved with code while the regression ran ({', '.join(moved[:3])}), in {req.branch}'s files: "
             "merging it and running again")
        scratch = scratch.with_name(f"{scratch.name}-{attempt + 2}")
        results = scratch / "results.txt"
        selection = _selection(req, services, mode, note)
        selective = mode == "selective" and selection is not None and selection.trusted
    if mode == "none":
        moved = code_paths(git(req.live, "diff", "--name-only", start_main, "main").splitlines())
        if moved:                                    # nothing ran meanwhile, but the merge must hold main's code
            catch_up(req, note)
            paths = git(req.live, "diff", "--name-only", f"main...{req.branch}").splitlines()
            units = _units(req, paths)
    previous = git(req.live, "rev-parse", "main")
    backup = ""
    if ENGINE_UNIT in units:
        backup = services.backup()
        note(f"backup: {backup.split()[0]}")
    log = req.log or release_log()
    summary = "skipped (D-261: integrate.regression = none)" if mode == "none" else f"{regression.summary()} ({results})"
    if selective:
        summary += "; the full regression of the merge runs in the background after the smoke"
    _append(log, _entry(req, previous, backup, summary, units))
    note(f"release log: {log}")
    try:
        merge = _deploy_merge(req)
        if not _fast_forward(req, f"deploy-{req.branch}"):
            merge = _deploy_merge(req)                   # a bitácora commit moved main between the merge and here
            if not _fast_forward(req, f"deploy-{req.branch}"):
                raise Refused("the live checkout refused the fast-forward twice: live main is unchanged", 2)
    except Refused as refused:
        _append(log, f"result: not integrated ({refused})\n")
        raise
    note(f"main is now {merge[:12]} (merge of {req.branch})")
    _drop_branch(req, f"deploy-{req.branch}")
    pushed = services.push(req.live)
    note("pushed origin main" if not pushed else f"WARNING push failed (main is integrated locally): {pushed}")
    units, swap = _repin(req, merge, services, units, note, log)
    problems = _refresh_venv(req, services, paths, note) or _restart(services, units, note)
    if not problems:
        _append(log, f"result: merged {merge[:12]}, restarted {', '.join(units) or 'nothing'}, smoke ok\n")
        if swap is not None:
            _prune(req, swap, note)
        if mode == "none":
            _ledger_add("Integrated without regression", f"- {dt.datetime.now():%Y-%m-%d %H:%M} · `{merge[:12]}` · "
                        f"{req.title} · {len(paths)} path(s): {', '.join(paths[:6])}" + (" …" if len(paths) > 6 else ""),
                        req.ledger)
        if selective:
            import bt_integrate_post
            bt_integrate_post.start(req, merge, log, services, note)
        _clean_up(req, note)
        return Outcome(0, lines, merge)
    note(f"SMOKE FAILED: {'; '.join(problems)}; reverting the merge")
    if mode == "none":
        record_escape(f"{req.title}: the smoke failed after an integration without regression ({'; '.join(problems)[:300]})",
                      merge, req.ledger)
    if swap is not None:
        try:
            remote_pin.rollback(req.remote, swap, services.daemon_reload)
            note(f"remote API: drop-in back on {swap.previous[:12]} (restarted with the revert)")
            _append(log, f"remote API pin: back on {swap.previous[:12]}\n")
        except Exception as error:  # noqa: BLE001 - the revert must still run
            note(f"WARNING remote API rollback failed ({error}): {req.remote.dropin} still pins {swap.current[:12]}; "
                 f"restore {swap.backup} by hand")
    try:
        reverted = _revert(req, merge, services, units, note)
    except Refused as error:
        _append(log, f"result: merged {merge[:12]}, smoke failed ({'; '.join(problems)}), revert FAILED: {error}\n")
        raise Refused(f"smoke failed and the revert failed too: {error}. The owner must look", 4) from error
    _append(log, f"result: merged {merge[:12]}, smoke failed ({'; '.join(problems)}), reverted by {reverted[:12]}\n")
    return Outcome(3, lines, merge)


def _inside(path: Path, base: Path) -> bool:
    try:
        Path(path).resolve().relative_to(Path(base).resolve())
        return True
    except ValueError:
        return False


def _clean_up(req: Request, note: Callable[[str], None]) -> None:
    """Remove the integrated branch's worktree and branch when that is safe; say what was kept and why. Never fails the
    integration: main is already integrated and smoked when this runs."""
    worktree, live = Path(req.worktree).resolve(), Path(req.live).resolve()
    command = f"git -C {live} worktree remove {worktree} && git -C {live} branch -d {req.branch}"
    if req.keep_worktree:
        note(f"kept {worktree} and branch {req.branch} (--keep-worktree)")
        return
    if worktree in (live, Path(req.deploy).resolve()):
        note(f"kept {worktree}: the live checkout and the deploy worktree are never removed")
        return
    if _inside(req.cwd or Path.cwd(), worktree):
        note(f"kept {worktree}: it is the current directory. Clean up later with: {command}")
        return
    if git(worktree, "status", "--porcelain", check=False):
        note(f"kept {worktree}: it has uncommitted or untracked files. Clean up by hand: {command}")
        return
    git(live, "worktree", "remove", str(worktree), check=False)
    if Path(worktree).exists():
        note(f"kept {worktree}: git worktree remove refused (locked?). Clean up by hand: {command}")
        return
    git(live, "branch", "-d", req.branch, check=False)
    if git(live, "rev-parse", "--verify", "-q", f"refs/heads/{req.branch}", check=False):
        note(f"removed {worktree}; branch {req.branch} kept: git branch -d refused it")
        return
    note(f"removed {worktree} and branch {req.branch}")


def _repin(req: Request, sha: str, services: Services, units: list[str], note: Callable[[str], None],
           log: Path | None = None) -> tuple[list[str], remote_pin.Swap | None]:
    """Before the restart: pin the remote API to `sha` (copy, drop-in, daemon-reload). When the copy cannot be made the
    listener keeps its pin and is not restarted; the integration goes on and says so (D-274)."""
    if remote_pin.UNIT not in units or req.remote is None:
        return units, None
    try:
        swap = remote_pin.refresh(req.remote, Path(req.live), sha, services.daemon_reload)
    except Exception as error:  # noqa: BLE001 - the listener still runs its previous copy
        note(f"WARNING remote API not repinned ({error}): it keeps {remote_pin.current(req.remote)[:12] or 'its code'} "
             "and is not restarted")
        if log is not None:
            _append(log, f"remote API pin: NOT refreshed to {sha[:12]} ({str(error)[:200]})\n")
        return [u for u in units if u != remote_pin.UNIT], None
    if swap is not None:
        note(f"remote API: repinned {swap.previous[:12]} -> {swap.current[:12]} "
             f"({Path(req.remote.releases) / swap.current}; previous drop-in kept as {swap.backup.name})")
        if log is not None:
            _append(log, f"remote API pin: {swap.previous[:12]} -> {swap.current[:12]} (backup {swap.backup})\n")
    return units, swap


def _prune(req: Request, swap: remote_pin.Swap, note: Callable[[str], None]) -> None:
    """After a passing smoke: old release copies go, the current and the previous pin stay. Never fails the run."""
    try:
        removed, kept = remote_pin.prune(req.remote, Path(req.live), {swap.current, swap.previous})
    except Exception as error:  # noqa: BLE001 - main is integrated and smoked
        note(f"WARNING remote API copies not pruned: {error}")
        return
    if removed or kept:
        note(f"remote API copies: removed {', '.join(s[:12] for s in removed) or 'none'}"
             + (f"; kept {'; '.join(kept)}" if kept else ""))


def _refresh_venv(req: Request, services: Services, paths: list[str], note: Callable[[str], None]) -> list[str]:
    """Before the restart, when `paths` change what the live venv is installed from: reinstall it and check that its
    interpreter finds every module the distribution lists, under the live checkout. A problem is a failed smoke (the
    units are not restarted; the caller reverts). Until 2026-10-31 nothing refreshed it: the engine's `uv run` resyncs
    only when it notices, and the CLI on `.venv/bin/python` never does (D-277)."""
    if not any(p in VENV_PATHS for p in paths):
        return []
    error = services.refresh_venv(Path(req.live))
    problems = [f"the live venv was not refreshed ({error})"] if error else \
        [f"the live venv: {p}" for p in services.install_problems(Path(req.live))]
    note("live venv refreshed; every packaged module imports from the live checkout" if not problems else
         "live venv: " + "; ".join(problems))
    return problems


def _restart(services: Services, units: list[str], note: Callable[[str], None]) -> list[str]:
    if not units:
        return []
    if ENGINE_UNIT in units:                 # a restart cuts a running verification: wait for it (D-204)
        import bt_config
        minutes = bt_config.get("integrate.drain_minutes", 20)
        waited, left = services.drain(60.0 * (minutes if isinstance(minutes, (int, float)) and minutes >= 0 else 20))
        if waited >= 1 or left:
            note(f"waited {int(waited)} s for running verifications" + (
                 f"; restarting with {len(left)} still running (each is recovered once, D-171): {', '.join(left[:3])}"
                 if left else ""))
    since = time.time() - 1
    for unit in units:
        services.restart(unit)
    problems = services.smoke(units, since)
    note("smoke ok: " + ", ".join(units) if not problems else "smoke: " + "; ".join(problems))
    return problems


def _revert(req: Request, merge: str, services: Services, units: list[str], note: Callable[[str], None],
            repin: bool = False) -> str:
    """Revert `merge` on main and restart `units`. `repin` (a revert asked for after the merge was smoked and kept,
    `bt_integrate_post.revert`) pins the remote API to the revert; a failed smoke's revert has put the previous pin
    back already."""
    deploy = Path(req.deploy)
    git(deploy, "checkout", "-q", "-B", f"revert-{req.branch}", "main")
    git(deploy, "revert", "--no-edit", "-m", "1", merge)
    if not _fast_forward(req, f"revert-{req.branch}"):
        raise Refused("the live checkout refused the revert's fast-forward")
    reverted = git(req.live, "rev-parse", "HEAD")
    _drop_branch(req, f"revert-{req.branch}")
    note(f"main reverted to the previous release by {reverted[:12]}")
    pushed = services.push(req.live)
    if pushed:
        note(f"WARNING push of the revert failed: {pushed}")
    swap = None
    if repin:
        units, swap = _repin(req, reverted, services, units, note)
    changed = git(req.live, "diff", "--name-only", f"{merge}^1", merge, check=False).splitlines()
    if _refresh_venv(req, services, changed, note) or _restart(services, units, note):
        if swap is not None:
            try:
                remote_pin.rollback(req.remote, swap, services.daemon_reload)
            except Exception as error:  # noqa: BLE001 - the owner looks at it anyway
                note(f"WARNING remote API rollback failed: {error}")
        raise Refused("the previous release does not pass the smoke either")
    if swap is not None:
        _prune(req, swap, note)
    return reverted


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bt_integrate", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    # --branch/--title are required by an integration, --post-merge and --revert (their logs, notices and revert
    # command name both), never by --escaped: the D-261 command `--escaped TEXT --merge SHA` failed on them (D-264)
    parser.add_argument("--branch", help="the branch to integrate (required except with --escaped)")
    parser.add_argument("--worktree", type=Path, help="the branch's own worktree (regressed as is)")
    parser.add_argument("--title", help="what the change does, with its D-NNN (required except with --escaped)")
    parser.add_argument("--session", default="", help="who integrates (session or Solucionador id), for the log")
    parser.add_argument("--live", type=Path, default=LIVE)
    parser.add_argument("--deploy", type=Path, default=DEPLOY, help="the deploy worktree (created when missing)")
    parser.add_argument("--scratch", type=Path, help="regression roots, logs and results")
    parser.add_argument("--release-log", type=Path)
    parser.add_argument("--wait-seconds", type=float, default=3600.0, help="how long to wait for another integration")
    parser.add_argument("--trailer", action="append", default=[], help="a line for the merge message (repeatable)")
    parser.add_argument("--dry-run", action="store_true", help="preflight and the selection only: what would run and be restarted")
    parser.add_argument("--keep-worktree", action="store_true",
                        help="keep the branch's worktree and branch after a successful integration")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--selective", dest="regression", action="store_const", const="selective",
                       help="integrate on the selected suites alone; the full regression of the merge runs afterwards")
    modes.add_argument("--full", dest="regression", action="store_const", const="full",
                       help="run the full regression without a selection first")
    modes.add_argument("--no-regression", dest="regression", action="store_const", const="none",
                       help="integrate on preflight and smoke alone and list it in the D-261 ledger")
    modes.add_argument("--staged", dest="regression", action="store_const", const="staged",
                       help="the selected suites first, then the rest (the default unless integrate.regression says)")
    parser.add_argument("--attached", action="store_true",
                        help="run in this process; by default an integration re-runs itself in its own transient unit, "
                             "so killing its caller (an agent session, its tmux) never cuts it half way (D-225)")
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--post-merge", metavar="MERGE", help="run the full regression of an integrated merge")
    actions.add_argument("--revert", metavar="MERGE", help="revert an integrated merge (deploy worktree, ff-only)")
    actions.add_argument("--escaped", metavar="TEXT", help="record a defect a regression would have caught (D-261 "
                         "ledger); --merge names the integration it came from")
    parser.add_argument("--merge", default="", help="with --escaped: the merge commit the defect came from")
    args = parser.parse_args(argv)
    if args.escaped:
        record_escape(args.escaped, args.merge)
        print(f"recorded in {ledger()}")
        return 0
    missing = [flag for flag, value in (("--branch", args.branch), ("--title", args.title)) if not value]
    if missing:
        parser.error(f"the following arguments are required: {', '.join(missing)} (all but --escaped need them)")
    req = Request(branch=args.branch, worktree=args.worktree or Path("."), title=args.title, session=args.session,
                  live=args.live, deploy=args.deploy, scratch=args.scratch, log=args.release_log,
                  wait_seconds=args.wait_seconds, trailers=args.trailer, dry_run=args.dry_run,
                  keep_worktree=args.keep_worktree, regression=args.regression or "",
                  remote=remote_pin.Pin.installed() if Path(args.live).resolve() == LIVE.resolve() else None)
    if not (args.dry_run or args.attached or args.post_merge or os.environ.get(DETACHED)) and _which("systemd-run"):
        return detached(list(sys.argv[1:] if argv is None else argv), args.branch)
    if args.post_merge or args.revert:
        import bt_integrate_post
        return (bt_integrate_post.post_merge(req, args.post_merge) if args.post_merge
                else bt_integrate_post.revert(req, args.revert))
    if args.worktree is None:
        parser.error("--worktree is required to integrate")
    return integrate(req).code


def detached(argv: list[str], branch: str, *, poll: float = 1.0, out=None) -> int:
    """Run this integration again in a transient user unit and follow it: its log is printed as it grows and its exit
    code is returned. If the caller dies, the integration goes on and finishes: a merge without its restart and smoke,
    or a regression killed at minute 20, was one tmux kill away when an agent integrated from its session
    (2026-10-30: the Solucionador's watchdog would have cut its own D-203 integration; D-225)."""
    out = out or sys.stdout
    stamp = f"{dt.datetime.now():%Y%m%d-%H%M%S}"
    name = f"bt-integrate-{''.join(c if c.isalnum() else '-' for c in branch)[:60]}-{stamp}"
    runs = Path(DEPLOY).parent / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    log, rc = runs / f"{name}.log", runs / f"{name}.rc"
    keep = ("PATH", "HOME", "BITACORA_ROOT", "PYTHONPATH", "BITACORA_SOLVER", "BITACORA_TMUX_SOCKET")
    env = [f"--setenv={k}={os.environ[k]}" for k in keep if os.environ.get(k)]
    command = ["systemd-run", "--user", f"--unit={name}", "--collect", "--quiet", f"--working-directory={os.getcwd()}",
               f"--property=StandardOutput=append:{log}", f"--property=StandardError=append:{log}",
               f"--setenv={DETACHED}=1", f"--setenv={RC_FILE}={rc}", *env,
               sys.executable, str(Path(__file__).resolve()), *argv]
    started = subprocess.run(command, capture_output=True, text=True, check=False)
    if started.returncode:
        print(f"could not start the integration unit ({started.stderr.strip()[:200]}); running attached", file=out)
        return main([*argv, "--attached"])
    print(f"integration runs in unit {name} (log {log}); it finishes even if this caller stops", file=out, flush=True)
    shown = 0
    while True:
        text = log.read_text(encoding="utf-8", errors="replace") if log.is_file() else ""
        if len(text) > shown:
            print(text[shown:], end="", file=out, flush=True)
            shown = len(text)
        if rc.is_file():
            try:
                return int(rc.read_text().strip() or 1)
            except ValueError:
                return 1
        state = subprocess.run(["systemctl", "--user", "is-active", name], capture_output=True, text=True,
                               check=False).stdout.strip()
        if state not in ("active", "activating", "reloading") and not rc.is_file():
            time.sleep(poll)
            if not rc.is_file():
                print(f"the integration unit {name} ended without an exit code ({state}); see {log}", file=out)
                return 4
        time.sleep(poll)


if __name__ == "__main__":
    code = 1
    try:
        code = main()
    finally:
        if os.environ.get(RC_FILE):
            Path(os.environ[RC_FILE]).write_text(f"{code}\n", encoding="utf-8")
    sys.exit(code)
