"""Integrate a metodologia branch into production: the procedure operators followed by hand on 2026-10-29 (REQ-031 T1).

Production of metodologia is this machine: `main` in the live checkout (`~/dev/metodologia`) plus the units that run
it (`bt-durable.service`, `bitacora-web.service`). The live checkout also holds the live bitácora (`~/bitacora` is a
symlink into it, with many uncommitted files): a `git merge --no-ff` there once refused the staged bitácora changes and
its abort reset them (D-160's integration). So the live checkout only ever sees `git merge --ff-only` and `git push`.

Under one machine-wide lock (flock on `<state>/integrate.lock`), in this order:
  1. preflight: the live checkout is on `main`; the branch is committed in its worktree, changes no `bitacora/` path
     and already holds main's code (bitácora commits on main are fine);
  2. full regression of the branch worktree (`bt_regress`; only `integrate.allowed_failures` may fail, any other
     failure is rerun alone once); a red regression integrates nothing and the branch stays;
  3. when runtime code changed: a DBOS backup (never printing the database URL), and in every case the release-log
     entry (previous main, backup, regression, rollback line);
  4. `git checkout -B deploy-<branch> main` + `git merge --no-ff <branch>` in a separate deploy worktree;
  5. `git merge --ff-only deploy-<branch>` in the live checkout (one rebuild when a bitácora commit moved main between
     4 and 5); `git push origin main`;
  6. restart the units the changed paths need, smoke them (unit active, web answers 200, the engine journal says it
     started); a failed smoke reverts the merge the same way (deploy worktree, ff-only, restart) and says so.

usage: bt_integrate.py --branch B --worktree WT --title "what it does (D-NNN)" [--session ID] [--dry-run] ...
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

LIVE = Path.home() / "dev" / "metodologia"
DEPLOY = Path.home() / ".local" / "share" / "bitacora-integrate" / "deploy"
ENGINE_UNIT, WEB_UNIT = "bt-durable.service", "bitacora-web.service"
WEB_URL = "http://127.0.0.1:8765/"
STARTED = "bt_durable engine started"
ENV_FILE = Path.home() / ".config" / "bitacora" / "durable.env"
PG_CONTAINER = "metodologia-dbos-pg"
BITACORA = "bitacora/"
SMOKE_SECONDS = 90
BUSY = 75


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
    try:
        while True:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    handle.seek(0)
                    holder = handle.read().strip()[:200]
                    raise Busy(f"another integration holds {path}" + (f" ({holder})" if holder else "")) from None
                time.sleep(poll)
        handle.seek(0)
        handle.truncate()
        handle.write(f"pid {os.getpid()} since {dt.datetime.now().isoformat(timespec='seconds')}\n")
        handle.flush()
        yield
    finally:
        handle.close()                                   # closing the descriptor releases the flock


def git(cwd: Path, *args: str, check: bool = True) -> str:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    done = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, env=env, check=False)
    if check and done.returncode:
        raise Refused(f"git {' '.join(args[:3])} in {cwd} failed: {(done.stderr or done.stdout).strip()[-400:]}")
    return done.stdout.strip() if not done.returncode else ""


def runtime_path(path: str) -> bool:
    """Code a running unit imports: the engine and the web load ~30 skill/scripts modules lazily, so any of them counts."""
    if path in ("pyproject.toml", "uv.lock"):
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


def code_paths(paths: list[str]) -> list[str]:
    return [p for p in paths if p and not p.startswith(BITACORA)]


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

    def regress(self, worktree: Path, scratch: Path, out: Path):
        import bt_regress
        return bt_regress.run(worktree, scratch, out)

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

    def restart(self, unit: str) -> None:
        done = subprocess.run(["systemctl", "--user", "restart", unit], capture_output=True, text=True, check=False)
        if done.returncode:
            raise Refused(f"systemctl restart {unit} failed: {done.stderr.strip()[:200]}", 3)

    def smoke(self, units: list[str], since: float) -> list[str]:
        """What is still wrong after SMOKE_SECONDS: an inactive unit, a web that does not answer 200, an engine whose
        journal never said it started."""
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
            if not problems or time.monotonic() >= deadline:
                return problems
            time.sleep(3)


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


@dataclass
class Outcome:
    code: int
    lines: list[str]
    merge: str = ""


def preflight(req: Request) -> list[str]:
    """Refuse what the procedure cannot integrate safely; returns the branch's changed paths."""
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
    missing = code_paths(git(req.live, "diff", "--name-only", f"{req.branch}...main").splitlines())
    if missing:
        raise Refused(f"main has code {req.branch} lacks ({', '.join(missing[:3])}): merge main into the branch in "
                      "its worktree, then run this again")
    return paths


def _deploy_merge(req: Request) -> str:
    """deploy-<branch> = main + merge --no-ff <branch>, in the deploy worktree. Returns the merge commit."""
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
    git(deploy, "checkout", "-q", "-B", f"deploy-{req.branch}", "main")
    message = "\n\n".join([f"Merge {req.branch}: {req.title}", *(["\n".join(req.trailers)] if req.trailers else [])])
    git(deploy, "merge", "--no-ff", "-q", "-m", message, req.branch)
    return git(deploy, "rev-parse", "HEAD")


def _fast_forward(req: Request, ref: str) -> bool:
    """`git merge --ff-only` in the live checkout: the only write it ever gets. False when git refused."""
    git(req.live, "merge", "--ff-only", "-q", ref, check=False)
    return git(req.live, "rev-parse", "HEAD") == git(req.live, "rev-parse", ref)


def _entry(req: Request, previous: str, backup: str, regression: str, units: list[str]) -> str:
    restarted = " + ".join("engine" if u == ENGINE_UNIT else "web" for u in units) or "no unit"
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


def _integrate(req: Request, services: Services, note: Callable[[str], None], lines: list[str]) -> Outcome:
    paths = preflight(req)
    units = units_for(paths)
    note(f"preflight ok: {len(paths)} path(s) changed; restart: {', '.join(units) or 'none'}")
    if req.dry_run:
        return Outcome(0, lines)
    start_main = git(req.live, "rev-parse", "main")
    scratch = Path(req.scratch or Path(req.deploy).parent / "regress" /     # fresh roots for every run
                   f"{req.branch.replace('/', '-')}-{dt.datetime.now():%Y%m%d-%H%M%S}")
    results = scratch / "results.txt"
    regression = services.regress(Path(req.worktree), scratch, results)
    note(f"regression: {regression.summary()} ({results})")
    if not regression.ok:
        raise Refused(f"the regression is red ({', '.join(regression.real)}): nothing was integrated, {req.branch} stays")
    moved = code_paths(git(req.live, "diff", "--name-only", start_main, "main").splitlines())
    if moved:
        raise Refused(f"main moved with code while the regression ran ({', '.join(moved[:3])}): merge main into "
                      f"{req.branch} and run this again")
    previous = git(req.live, "rev-parse", "main")
    backup = ""
    if ENGINE_UNIT in units:
        backup = services.backup()
        note(f"backup: {backup.split()[0]}")
    log = req.log or release_log()
    _append(log, _entry(req, previous, backup, f"{regression.summary()} ({results})", units))
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
    pushed = services.push(req.live)
    note("pushed origin main" if not pushed else f"WARNING push failed (main is integrated locally): {pushed}")
    problems = _restart(services, units, note)
    if not problems:
        _append(log, f"result: merged {merge[:12]}, restarted {', '.join(units) or 'nothing'}, smoke ok\n")
        return Outcome(0, lines, merge)
    note(f"SMOKE FAILED: {'; '.join(problems)}; reverting the merge")
    try:
        reverted = _revert(req, merge, services, units, note)
    except Refused as error:
        _append(log, f"result: merged {merge[:12]}, smoke failed ({'; '.join(problems)}), revert FAILED: {error}\n")
        raise Refused(f"smoke failed and the revert failed too: {error}. The owner must look", 4) from error
    _append(log, f"result: merged {merge[:12]}, smoke failed ({'; '.join(problems)}), reverted by {reverted[:12]}\n")
    return Outcome(3, lines, merge)


def _restart(services: Services, units: list[str], note: Callable[[str], None]) -> list[str]:
    if not units:
        return []
    since = time.time() - 1
    for unit in units:
        services.restart(unit)
    problems = services.smoke(units, since)
    note("smoke ok: " + ", ".join(units) if not problems else "smoke: " + "; ".join(problems))
    return problems


def _revert(req: Request, merge: str, services: Services, units: list[str], note: Callable[[str], None]) -> str:
    deploy = Path(req.deploy)
    git(deploy, "checkout", "-q", "-B", f"revert-{req.branch}", "main")
    git(deploy, "revert", "--no-edit", "-m", "1", merge)
    if not _fast_forward(req, f"revert-{req.branch}"):
        raise Refused("the live checkout refused the revert's fast-forward")
    reverted = git(req.live, "rev-parse", "HEAD")
    note(f"main reverted to the previous release by {reverted[:12]}")
    pushed = services.push(req.live)
    if pushed:
        note(f"WARNING push of the revert failed: {pushed}")
    if _restart(services, units, note):
        raise Refused("the previous release does not pass the smoke either")
    return reverted


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bt_integrate", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--worktree", required=True, type=Path, help="the branch's own worktree (regressed as is)")
    parser.add_argument("--title", required=True, help="what the change does, with its D-NNN")
    parser.add_argument("--session", default="", help="who integrates (session or Solucionador id), for the log")
    parser.add_argument("--live", type=Path, default=LIVE)
    parser.add_argument("--deploy", type=Path, default=DEPLOY, help="the deploy worktree (created when missing)")
    parser.add_argument("--scratch", type=Path, help="regression roots, logs and results")
    parser.add_argument("--release-log", type=Path)
    parser.add_argument("--wait-seconds", type=float, default=3600.0, help="how long to wait for another integration")
    parser.add_argument("--trailer", action="append", default=[], help="a line for the merge message (repeatable)")
    parser.add_argument("--dry-run", action="store_true", help="preflight only: what would be restarted")
    args = parser.parse_args(argv)
    outcome = integrate(Request(branch=args.branch, worktree=args.worktree, title=args.title, session=args.session,
                                live=args.live, deploy=args.deploy, scratch=args.scratch, log=args.release_log,
                                wait_seconds=args.wait_seconds, trailers=args.trailer, dry_run=args.dry_run))
    return outcome.code


if __name__ == "__main__":
    sys.exit(main())
