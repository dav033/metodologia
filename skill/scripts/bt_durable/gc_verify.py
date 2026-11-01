"""«Probar» copies nothing needs any more (D-270).

`bt_verification.open_local` and `bt_verify_servers` open every subplan version the owner tries as a detached worktree
`<base>/<project>/<REQ>/<SP>-v<N>` (and a task snapshot as `<T>-a<n>-<hash>`), with sidecars `<slug>.env` (0600,
secrets), `.lock`, `.logs`, `.run.sh` and `.servers.json`; `<base>` is `BITACORA_VERIFY_DIR`, else
`~/.local/share/bitacora-verify`. Each copy gets its own `npm ci` and Next build (~2 GB): on 2026-10-31 eleven copies of
pictures REQ-021 held 23 GB and nothing ever removed one.

Per copy (one pass, facts read once):

- kept while a server runs: a process carrying its `BITACORA_VERIFY_ID` mark, a process working inside it, or its tmux
  session (`server-running`); while another start holds its `.lock` (`locked`); when its sidecars changed less than an
  hour ago (`recent`); with edits or new files git would keep (`local-edits`, reported: close_local refuses those too);
- a subplan copy is removed when a newer version of the same subplan is published (`superseded`), or when the owner
  decided its version (approved or rejected) more than `disk_gc.verify_grace_days` ago (`decided`); the latest
  undecided version is kept (`latest`);
- a task copy (the evidence of an open manual decision) is removed once no open decision of the durable run names its
  attempt and it was untouched for the grace period (`decision-closed`);
- a name that is neither, or a requirement whose folder is unknown, is never touched (`unknown`).
- a copy the owner kept aside (`<SP>-v<N>-kept-<sha7>`, bt_verify_copy, D-278) is such a name. A copy left at an
  older publication of its version is not this pass's business: opening it moves it (bt_verify_copy).

Removal: `git worktree remove --force` from the copy's own repository, then `prune`; the sidecars of a removed version
go with it. Published commits live in the project's refs (`refs/bt/subplan/...`), so a removed copy can be opened again
from the panel.
"""
from __future__ import annotations

import contextlib
import fcntl
import os
import re
import shutil
import subprocess
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path

SIDECARS = (".servers.json", ".env", ".run.sh", ".logs", ".lock")
_SUBPLAN = re.compile(r"(?P<sid>[A-Za-z0-9][A-Za-z0-9._-]{0,40}?)-v(?P<version>\d+)")
_TASK = re.compile(r"(?P<sid>T\d+(?:\.\d+)*)-(?P<attempt>a\d+-[0-9a-f]{4,})")
MARK = "BITACORA_VERIFY_ID"
RECENT_SECONDS = 3600
DAY = 86400


def base_dir() -> Path:
    """Where «Probar» opens its copies (the same rule as `bt_verification.workdir`)."""
    return Path(os.environ.get("BITACORA_VERIFY_DIR") or Path.home() / ".local" / "share" / "bitacora-verify")


@dataclass
class Copy:
    project: str
    req: str
    slug: str
    kind: str                         # subplan | task | unknown
    sid: str = ""
    version: int | None = None
    attempt: str = ""
    path: Path | None = None          # the worktree (None: only sidecars are left)
    sidecars: list[Path] = field(default_factory=list)

    @property
    def mark(self) -> str:
        return f"{self.project}/{self.req}/{self.slug}"

    @property
    def session(self) -> str:
        return re.sub(r"[.:]", "_", f"bv-{self.project}-{self.req}-{self.slug}")[:80]


def _slug_of(name: str) -> tuple[str, str]:
    for suffix in SIDECARS:
        if name.endswith(suffix):
            return name[:-len(suffix)], suffix
    return name, ""


def inventory(base: Path) -> list[Copy]:
    """Every copy (or sidecar set) under `<base>/<project>/<REQ>/`; hidden files (`.ports.lock`) are not copies."""
    found: dict[tuple[str, str, str], Copy] = {}
    for project in sorted(p for p in Path(base).iterdir() if p.is_dir() and not p.is_symlink()) \
            if Path(base).is_dir() else ():
        for req in sorted(p for p in project.iterdir() if p.is_dir() and not p.is_symlink()):
            for entry in sorted(req.iterdir()):
                if entry.name.startswith("."):
                    continue
                slug, suffix = _slug_of(entry.name)
                item = found.get((project.name, req.name, slug))
                if item is None:
                    item = Copy(project.name, req.name, slug, "unknown")
                    if match := _TASK.fullmatch(slug):
                        item.kind, item.sid, item.attempt = "task", match.group("sid"), match.group("attempt")
                    elif match := _SUBPLAN.fullmatch(slug):
                        item.kind, item.sid, item.version = "subplan", match.group("sid"), int(match.group("version"))
                    found[(project.name, req.name, slug)] = item
                if suffix:
                    item.sidecars.append(entry)
                elif entry.is_dir() and not entry.is_symlink():
                    item.path = entry
                else:
                    item.kind = "unknown"                       # a file or link named like a copy: not ours
    return list(found.values())


# ------------------------------------------------------------------------------------------------- the facts
@dataclass
class ReqFacts:
    """What the bitácora says about one requirement: per subplan its latest published version and the owner's decision
    ({decision, version, at}); the attempts open manual decisions name."""
    latest: dict[str, int] = field(default_factory=dict)
    decisions: dict[str, dict] = field(default_factory=dict)
    open_attempts: set[str] = field(default_factory=set)


def requirement_dir(root: Path, project: str, req: str) -> Path | None:
    hits = sorted(p for p in (Path(root) / project / "requirements").glob(f"{req}-*") if p.is_dir()) \
        if re.fullmatch(r"REQ-\d+", req) else []
    return hits[0] if hits else None


def req_facts(rdir: Path) -> ReqFacts:
    import bt_durable_panel
    import bt_verification
    facts = ReqFacts()
    for row in bt_verification.state(rdir)["subplans"]:
        if isinstance(row.get("version"), int):
            facts.latest[row["id"]] = row["version"]
        if isinstance(row.get("decision"), dict) and row["decision"]:
            facts.decisions[row["id"]] = row["decision"]
    for decision in bt_durable_panel.decisions(rdir):
        manual = decision.get("manual") or {}
        if manual.get("attempt"):
            facts.open_attempts.add(str(manual["attempt"]))
    return facts


def _decided_at(decision: dict) -> float | None:
    import datetime as dt
    try:
        return dt.datetime.fromisoformat(str(decision.get("at"))).timestamp()
    except (TypeError, ValueError):
        return None


def marks_in_use(proc: Path = Path("/proc")) -> set[str]:
    """Every `BITACORA_VERIFY_ID` some process of this user carries (one scan of /proc)."""
    marks, uid, prefix = set(), os.getuid(), (MARK + "=").encode()
    for entry in proc.iterdir() if proc.is_dir() else ():
        if not entry.name.isdigit():
            continue
        try:
            if entry.stat().st_uid != uid:
                continue
            raw = (entry / "environ").read_bytes()
        except OSError:
            continue
        for item in raw.split(b"\0"):
            if item.startswith(prefix):
                marks.add(item[len(prefix):].decode("utf-8", "replace"))
    return marks


def _session_alive(name: str) -> bool:
    try:
        import bt_agent_terminal
        return bt_agent_terminal.exists(name)
    except Exception:  # noqa: BLE001 - tmux unreadable: the process scan still protects a running server
        return False


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    env = {**{k: v for k, v in os.environ.items() if not k.startswith("GIT_")}, "GIT_OPTIONAL_LOCKS": "0",
           "GIT_TERMINAL_PROMPT": "0"}                     # inspecting never refreshes (writes) an index
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, timeout=600, env=env,
                          check=False)


def local_edits(copy: Path) -> str:
    """'' when git would discard nothing but ignored files (dependencies, builds, logs), else what it would."""
    done = _git(copy, "status", "--porcelain", "--untracked-files=normal")
    if done.returncode:
        return "git status failed: " + (done.stderr or "").strip()[:120]
    lines = [line[3:] for line in done.stdout.splitlines() if line.strip()]
    return ", ".join(lines[:5]) + (" …" if len(lines) > 5 else "") if lines else ""


def _last_touch(item: Copy) -> float:
    times = []
    for path in [*item.sidecars, *([item.path] if item.path else [])]:
        with contextlib.suppress(OSError):
            times.append(path.lstat().st_mtime)
    return max(times) if times else 0.0


# ---------------------------------------------------------------------------------------------- the decision
def decide(item: Copy, facts: ReqFacts | None, *, now: float, grace_seconds: float, busy: Iterable[str],
           marks: set[str], session_alive: Callable[[str], bool] = _session_alive) -> tuple[str, str]:
    """(action, reason): action `remove` or `keep`. Pure over the facts of the pass, except the tmux probe."""
    if item.kind == "unknown" or facts is None:
        return "keep", "unknown"
    if item.mark in marks or (item.path is not None and os.path.normpath(str(item.path)) in busy) \
            or session_alive(item.session):
        return "keep", "server-running"
    if now - _last_touch(item) < RECENT_SECONDS:
        return "keep", "recent"
    if item.kind == "subplan":
        latest = facts.latest.get(item.sid)
        if latest is not None and item.version is not None and item.version < latest:
            return "remove", "superseded"
        decision = facts.decisions.get(item.sid) or {}
        at = _decided_at(decision)
        if latest is not None and decision.get("version") == item.version and \
                decision.get("decision") in ("approved", "rejected") and at is not None and now - at >= grace_seconds:
            return "remove", "decided"
        return "keep", "latest" if latest is not None else "unpublished"
    if any(attempt.endswith(item.attempt) for attempt in facts.open_attempts):
        return "keep", "decision-open"
    if now - _last_touch(item) < grace_seconds:
        return "keep", "grace"
    return "remove", "decision-closed"


@contextlib.contextmanager
def _version_lock(item: Copy):
    """The version's own `.lock` (the one `bt_verify_servers.start` holds), taken without waiting; None if busy."""
    lock = next((p for p in item.sidecars if p.name.endswith(".lock")), None)
    if lock is None or lock.is_symlink():
        yield True
        return
    with lock.open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            yield False
            return
        yield True


def remove(item: Copy, base: Path) -> str:
    """Remove the copy and its sidecars; '' or why not. Nothing outside `base` is ever deleted."""
    base = Path(base).resolve()
    for path in [*([item.path] if item.path else []), *item.sidecars]:
        if path.is_symlink() or not path.resolve().is_relative_to(base):
            return f"a link or outside the verify folder: {path}"
    with _version_lock(item) as free:
        if not free:
            return "locked"
        if item.path is not None and item.path.exists():
            edits = local_edits(item.path)
            if edits:
                return f"local-edits: {edits}"
            common = _git(item.path, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip()
            repo = Path(common).parent if common else None
            if repo is not None and repo.is_dir():
                _git(repo, "worktree", "remove", "--force", str(item.path))
            if item.path.exists():
                shutil.rmtree(item.path, ignore_errors=True)
            if repo is not None and repo.is_dir():
                _git(repo, "worktree", "prune")
            if item.path.exists():
                return "still present"
        for path in item.sidecars:
            if path.is_dir() and not path.is_symlink():
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink(missing_ok=True)
    return ""


def collect(base: Path, root: Path, *, apply: bool, grace_seconds: float, sizes: bool = True,
            now: float | None = None, proc: Path = Path("/proc"),
            session_alive: Callable[[str], bool] = _session_alive,
            facts_for: Callable[[Path], ReqFacts] = req_facts, emit: Callable[..., None] | None = None) -> list[dict]:
    """One pass over `base` (see the module docstring). Returns one row per copy: {path, action, reason, bytes}."""
    from .scratch import processes_inside, size_of
    now = time.time() if now is None else now
    items = inventory(base)
    if not items:
        return []
    busy = processes_inside([i.path for i in items if i.path is not None], proc)
    marks = marks_in_use(proc)
    cache: dict[tuple[str, str], ReqFacts | None] = {}
    rows = []
    for item in items:
        key = (item.project, item.req)
        if key not in cache:
            rdir = requirement_dir(root, *key)
            try:
                cache[key] = facts_for(rdir) if rdir is not None else None
            except Exception:  # noqa: BLE001 - unreadable facts: nothing of this requirement is touched
                cache[key] = None
        action, reason = decide(item, cache[key], now=now, grace_seconds=grace_seconds, busy=busy, marks=marks,
                                session_alive=session_alive)
        where = item.path or (item.sidecars[0] if item.sidecars else Path(base))
        row = {"path": str(where), "slug": f"{item.project}/{item.req}/{item.slug}", "action": action, "reason": reason,
               "bytes": None}
        if action == "remove" and item.path is not None and item.path.exists() and item.path.is_dir():
            edits = local_edits(item.path)
            if edits:
                row.update(action="keep", reason="local-edits", detail=edits)
        if row["action"] == "remove" and sizes:
            row["bytes"] = sum(size_of(p) if p.is_dir() else p.lstat().st_size
                               for p in [*([item.path] if item.path else []), *item.sidecars] if p.exists())
        if row["action"] == "remove" and apply:
            why = remove(item, base)
            row["action"] = "failed" if why else "removed"
            if why:
                row["detail"] = why
            if emit is not None:
                emit("disk_gc_removed" if not why else "disk_gc_failed", area="verify_copies", path=row["path"],
                     reason=reason, bytes=row["bytes"], **({"error": why} if why else {}))
        rows.append(row)
    return rows
