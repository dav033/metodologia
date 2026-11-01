"""The remote API's pinned release copy, refreshed by the integration itself (D-274).

`bitacora-remote-api.service` (the listener the AdvIn gateway reaches) does not run the live checkout: a drop-in
(`~/.config/systemd/user/bitacora-remote-api.service.d/exec.conf`) points its ExecStart at a release copy
`~/.local/share/bitacora-remote/<sha>/skill`, made by `git archive <sha> skill`, so a half-edited live tree never reaches
the phone (P-144). Until D-274 every integration left that pin behind and the operator refreshed it by hand (2026-10-31:
aaf31a8d6 -> 7e8d4e638). `bt_integrate` now calls this module in its restart phase:

  `stale`     which paths the listener can load differ between the pinned copy and a commit (none: no refresh);
  `refresh`   create-only copy of the merge (extracted to a temporary folder, then renamed), the drop-in rewritten
              atomically with the previous one kept as `exec.conf.bak-<old sha12>`, `daemon-reload`;
  `rollback`  the previous drop-in back and `daemon-reload` (a failed smoke: the listener restarts on the old pin);
  `prune`     after a passing smoke, keep the newest `keep` copies (always the current and the previous pin), remove
              older ones only when their commit is in the repository (regenerable) and no process runs from them.

What the listener runs (read from `bitacora.py serve-remote`): `/usr/bin/python3` (stdlib only: no venv, so neither
`pyproject.toml` nor `uv.lock` matter) importing `skill/scripts/**` lazily (`bt_server` -> `bt_remote_*`, the panel
routes `bt_remote_panel` proxies, `bt_live_api`, `bt_planstatus`, ...), `/static/` from `skill/assets/`, `skill/templates/`
(`bt_core.render`), `skill/vendor/` (`bt_diagram`), `skill/ui/` (the component pool and project themes behind
`/ui/`, D-280) and `skill/agents/*.md` (briefs of the sessions a panel action starts from the copy). Tests, `skill/references/`, `skill/githooks/` and `SKILL.md` are never read by it.
"""
from __future__ import annotations

import datetime as dt
import os
import re
import shutil
import subprocess
import tarfile
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

UNIT = "bitacora-remote-api.service"
URL = "http://127.0.0.1:8766/api/remote/v1"     # answers 401 without the gateway key: any answer below 500 is alive
UNIT_FILE = Path.home() / ".config" / "systemd" / "user" / UNIT
DROPIN = UNIT_FILE.with_name(UNIT + ".d") / "exec.conf"
RELEASES = Path.home() / ".local" / "share" / "bitacora-remote"
KEEP = 3                                       # the current pin, the previous one (rollback) and one more
RUNS = ("skill/scripts/", "skill/assets/", "skill/templates/", "skill/vendor/", "skill/agents/", "skill/ui/")
ENTRY = "skill/scripts/bitacora.py"
SHA = re.compile(r"^[0-9a-f]{40}$")
PINNED = re.compile(r"(?P<prefix>\S*/)(?P<sha>[0-9a-f]{40})(?P<suffix>/skill/scripts/bitacora\.py)")   # <releases>/<sha>
BACKUP = re.compile(r"^exec\.conf\.bak-(?P<sha>[0-9a-f]{12})$")   # the ones this module writes (operators' have 7)
STALE_TMP_SECONDS = 3600


class PinError(RuntimeError):
    """The pin could not be refreshed; the listener still runs the copy it ran before."""


@dataclass
class Pin:
    releases: Path = RELEASES
    dropin: Path = DROPIN
    keep: int = KEEP
    home: Path = field(default_factory=Path.home)    # what `%h` means in the drop-in

    @classmethod
    def installed(cls) -> Pin | None:
        """The live listener's pin, or None when this machine has no remote API unit."""
        return cls() if UNIT_FILE.is_file() else None


@dataclass
class Swap:
    """One refresh: what to restore when the smoke fails, and what pruning must keep."""
    previous: str          # the sha the drop-in pinned before
    current: str           # the sha it pins now
    text: str              # the previous drop-in, verbatim
    backup: Path


def relevant(path: str) -> bool:
    return path.startswith(RUNS) and "/tests/" not in path


def current(pin: Pin) -> str:
    """The sha the drop-in pins, or "" when there is no drop-in or it does not run a release copy."""
    try:
        text = pin.dropin.read_text(encoding="utf-8")
    except OSError:
        return ""
    found = [m for line in text.splitlines() if line.strip().startswith("ExecStart=")
             for m in [PINNED.search(line)] if m]
    return found[-1].group("sha") if found else ""


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=env, check=False)


def _known(repo: Path, sha: str) -> bool:
    return _git(repo, "cat-file", "-e", f"{sha}^{{commit}}").returncode == 0


def stale(pin: Pin, repo: Path, ref: str) -> list[str]:
    """The paths the listener can load that differ between the pinned copy and `ref` ([] when not pinned or equal).
    A pin the repository does not know is stale as a whole."""
    sha = current(pin)
    if not sha:
        return []
    if not _known(repo, sha):
        return [f"<pinned {sha[:12]} is not in {repo}>"]
    done = _git(repo, "diff", "--name-only", sha, ref, "--", "skill/")
    return [p for p in done.stdout.splitlines() if relevant(p)]


def _check_prefix(pin: Pin, text: str) -> None:
    for match in PINNED.finditer(text):
        folder = Path(match.group("prefix").replace("%h", str(pin.home)).rstrip("/"))
        if folder.resolve() != Path(pin.releases).resolve():
            raise PinError(f"the drop-in pins a copy outside {pin.releases} ({folder}): refresh it by hand")


def materialize(pin: Pin, repo: Path, sha: str) -> Path:
    """`<releases>/<sha>`, created once: `git archive <sha> skill` extracted into a temporary folder that is renamed
    into place. An existing complete copy is reused (create-only); an incomplete one is refused, never overwritten."""
    if not SHA.match(sha):
        raise PinError(f"not a full commit sha: {sha!r}")
    releases = Path(pin.releases)
    target = releases / sha
    if target.is_dir() and not target.is_symlink():
        if (target / ENTRY).is_file():
            os.utime(target)                      # newest again: pruning orders copies by when they were last pinned
            return target
        raise PinError(f"{target} exists without {ENTRY}: move it aside by hand")
    if target.exists() or target.is_symlink():
        raise PinError(f"{target} exists and is not a release folder")
    releases.mkdir(parents=True, exist_ok=True)
    temporary = releases / f".tmp-{sha[:12]}-{os.getpid()}-{time.monotonic_ns()}"
    temporary.mkdir()
    try:
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        archive = subprocess.Popen(["git", "-C", str(repo), "archive", "--format=tar", sha, "skill"],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        try:
            with tarfile.open(fileobj=archive.stdout, mode="r|") as tar:
                tar.extractall(temporary, filter="data")
        finally:
            archive.stdout.close()
            error = archive.stderr.read().decode(errors="replace")
            archive.stderr.close()
            code = archive.wait()
        if code:
            raise PinError(f"git archive {sha[:12]} failed: {error.strip()[:200]}")
        if not (temporary / ENTRY).is_file():
            raise PinError(f"the archive of {sha[:12]} has no {ENTRY}")
        os.rename(temporary, target)              # atomic; refuses a target another process created meanwhile
    except (OSError, tarfile.TarError) as error:
        shutil.rmtree(temporary, ignore_errors=True)
        if (target / ENTRY).is_file():
            return target
        raise PinError(f"could not extract {sha[:12]} into {releases}: {error}") from error
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return target


def render(text: str, sha: str, when: dt.datetime | None = None) -> str:
    """The drop-in pinned to `sha`: the leading comment says who refreshed it, every pinned ExecStart names the new
    copy, everything else is kept as the operator wrote it."""
    lines = text.splitlines()
    while lines and lines[0].startswith("#"):
        lines.pop(0)
    note = (f"# Local override: run the pinned release copy of the remote API (P-144); refreshed to {sha} by "
            f"bt_integrate, {(when or dt.datetime.now()):%Y-%m-%d %H:%M} (D-274).")
    body = [PINNED.sub(lambda m: m.group("prefix") + sha + m.group("suffix"), line)
            if line.strip().startswith("ExecStart=") else line for line in lines]
    return "\n".join([note, *body]) + "\n"


def _write(path: Path, text: str) -> None:
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def refresh(pin: Pin, repo: Path, sha: str, reload: Callable[[], None]) -> Swap | None:
    """Pin the listener to `sha`. None when the unit runs no release copy (nothing to pin) or already runs `sha`.
    Raises PinError with the drop-in unchanged when the copy cannot be made."""
    previous = current(pin)
    if not previous or previous == sha:
        return None
    text = pin.dropin.read_text(encoding="utf-8")
    _check_prefix(pin, text)
    materialize(pin, repo, sha)
    backup = pin.dropin.with_name(f"exec.conf.bak-{previous[:12]}")
    _write(backup, text)
    _write(pin.dropin, render(text, sha))
    try:
        reload()
    except Exception:
        _write(pin.dropin, text)
        raise
    return Swap(previous, sha, text, backup)


def rollback(pin: Pin, swap: Swap, reload: Callable[[], None]) -> None:
    """The drop-in as it was before `swap` (the listener restarts on the previous copy, which pruning never removed)."""
    _write(pin.dropin, swap.text)
    reload()


def _in_use(folder: Path) -> bool:
    """A process whose command line names the copy (the listener, a session a panel action started from it)."""
    needle = str(folder).encode()
    proc = Path("/proc")
    if not proc.is_dir():
        return False
    for entry in proc.iterdir():
        if not entry.name.isdigit():
            continue
        try:
            if needle in (entry / "cmdline").read_bytes():
                return True
        except OSError:
            continue
    return False


def prune(pin: Pin, repo: Path, protect: set[str], in_use: Callable[[Path], bool] = _in_use) -> tuple[list[str], list[str]]:
    """Remove release copies beyond the newest `pin.keep` (the drop-in's pin and `protect` always stay). A copy is
    removed only when its commit is in `repo` (it can be made again) and no process runs from it; this module's own
    drop-in backups go with their copy. Returns (removed, kept-with-reason)."""
    releases = Path(pin.releases)
    if not releases.is_dir():
        return [], []
    protect = {s for s in (*protect, current(pin)) if s}
    copies = sorted((p for p in releases.iterdir() if SHA.match(p.name) and p.is_dir() and not p.is_symlink()),
                    key=lambda p: p.stat().st_mtime, reverse=True)
    keep = {p.name for p in copies if p.name in protect}
    for copy in copies:
        if len(keep) >= max(pin.keep, 2):
            break
        keep.add(copy.name)
    removed, kept = [], []
    for copy in copies:
        if copy.name in keep:
            continue
        if not _known(repo, copy.name):
            kept.append(f"{copy.name[:12]}: its commit is not in {repo}")
            continue
        if in_use(copy):
            kept.append(f"{copy.name[:12]}: a process runs from it")
            continue
        shutil.rmtree(copy)
        removed.append(copy.name)
    now = time.time()
    for leftover in releases.glob(".tmp-*"):      # an extraction a killed integration left half way
        try:
            if now - leftover.stat().st_mtime > STALE_TMP_SECONDS and not leftover.is_symlink():
                shutil.rmtree(leftover)
        except OSError:
            continue
    present = {p.name for p in releases.iterdir() if SHA.match(p.name)}
    for backup in pin.dropin.parent.glob("exec.conf.bak-*"):
        match = BACKUP.match(backup.name)
        if match and not any(name.startswith(match.group("sha")) for name in present):
            backup.unlink(missing_ok=True)
    return removed, kept


def answers(url: str = URL, timeout: float = 10.0) -> str:
    """"" when the listener answers HTTP (401 without the key is an answer), else what is wrong."""
    import urllib.error
    import urllib.request
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            status = response.status
    except urllib.error.HTTPError as error:
        status = error.code
    except OSError as error:
        return f"remote API did not answer: {error}"
    return "" if status < 500 else f"remote API answered {status}"
