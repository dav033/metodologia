"""The M6 dependency cache, bounded (D-270).

`bt_scheduler_quality.sandbox_provision.provision` keeps one `npm ci` per lockfile under `M6_DEPS_CACHE` (default
`~/.cache/m6-deps/<key>/node_modules`, ~0.4–0.7 GB each) and never removed one. Each use touches `<key>/.m6-ready`, so
its mtime is the last use. A pass:

- protects the entries whose key is the lockfile of a live durable run's current tip (every `refs/bt/line/…` and
  `refs/bt/subplan/…` of a run whose projection is not terminal, every `package-lock.json` with its `package.json` in
  that commit) and every entry used in the last `disk_gc.deps_min_idle_hours` (a check may have it mounted);
- removes, least recently used first, entries unused for `disk_gc.deps_cache_max_age_days`, then more until the cache
  fits `disk_gc.deps_cache_max_gb`;
- removes build folders a crashed provision left (`<key>.<random>`, older than a day).

A removed entry is rebuilt offline from the lockfile the next time a check needs it.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from collections.abc import Callable, Iterable
from pathlib import Path

READY = ".m6-ready"
_KEY = re.compile(r"[0-9a-f]{32}")
_BUILDING = re.compile(r"[0-9a-f]{32}\..+")
TERMINAL = frozenset({"SUCCESS", "ERROR", "CANCELLED", "MAX_RECOVERY_ATTEMPTS_EXCEEDED"})
HOUR, DAY, GB = 3600, 86400, 10 ** 9


def cache_dir() -> Path:
    from bt_scheduler_quality.sandbox_provision import cache_root
    return cache_root()


def _git(repo: Path, *args: str, binary: bool = False):
    env = {**{k: v for k, v in os.environ.items() if not k.startswith("GIT_")}, "GIT_OPTIONAL_LOCKS": "0",
           "GIT_TERMINAL_PROMPT": "0"}                     # inspecting never refreshes (writes) an index
    done = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, timeout=120, env=env, check=False)
    if done.returncode:
        return None
    return done.stdout if binary else done.stdout.decode("utf-8", "replace")


def live_runs(state_dir: Path) -> list[tuple[str, str, int]]:
    """(project, req, revision) of every durable run whose projection is not terminal."""
    out = []
    for path in sorted((Path(state_dir) / "projections").glob("*/*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        run = str(data.get("run_id") or "") if isinstance(data, dict) else ""
        parts = run.split(":")
        if len(parts) == 3 and parts[2].startswith("r") and parts[2][1:].isdigit() \
                and str(data.get("workflow_status") or "") not in TERMINAL and data.get("status") not in ("cancelled",):
            out.append((parts[0], parts[1], int(parts[2][1:])))
    return out


def tips(repo: Path, project: str, req: str, revision: int) -> set[str]:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", project)
    listed = _git(repo, "for-each-ref", "--format=%(refname) %(objectname)",
                  f"refs/bt/line/{safe}/{req}/r{revision}/", f"refs/bt/subplan/{safe}/{req}/r{revision}/") or ""
    return {oid for name, _, oid in (line.partition(" ") for line in listed.splitlines())
            if oid and not name.endswith("-base")}


def keys_at(repo: Path, commit: str, memo: dict[tuple[str, str], str] | None = None) -> set[str]:
    """The cache keys of every lockfile in `commit` (`package-lock.json` beside a `package.json`, outside node_modules)."""
    from bt_scheduler_quality.sandbox_provision import key_of_bytes
    memo = {} if memo is None else memo
    listing = _git(repo, "ls-tree", "-r", "-z", commit, binary=True) or b""
    blobs: dict[str, str] = {}
    for item in listing.split(b"\0"):
        meta, _, path = item.partition(b"\t")
        name = os.fsdecode(path)
        if name.endswith(("package.json", "package-lock.json")) and "node_modules/" not in name and meta:
            blobs[name] = meta.split()[2].decode()
    keys = set()
    for name, lock in blobs.items():
        if not name.endswith("package-lock.json"):
            continue
        manifest = blobs.get(name[:-len("package-lock.json")] + "package.json")
        if manifest is None:
            continue
        if (manifest, lock) not in memo:
            left, right = _git(repo, "cat-file", "blob", manifest, binary=True), _git(repo, "cat-file", "blob", lock,
                                                                                         binary=True)
            if left is None or right is None:
                continue
            memo[(manifest, lock)] = key_of_bytes(left, right)
        keys.add(memo[(manifest, lock)])
    return keys


def protected_keys(state_dir: Path, repos_for: Callable[[str], Iterable[Path]]) -> set[str]:
    keys: set[str] = set()
    memo: dict[tuple[str, str], str] = {}
    for project, req, revision in live_runs(state_dir):
        for repo in repos_for(project):
            if not Path(repo).is_dir():
                continue
            for tip in tips(Path(repo), project, req, revision):
                keys |= keys_at(Path(repo), tip, memo)
    return keys


def project_repos(root: Path) -> Callable[[str], list[Path]]:
    def repos_for(project: str) -> list[Path]:
        try:
            import bt_workspace
            return [Path(p) for p in bt_workspace.repos(root, project, discover=False).values()]
        except Exception:  # noqa: BLE001 - no workspace record: nothing to protect from it
            return []
    return repos_for


def collect(cache: Path, *, apply: bool, protected: set[str], max_bytes: int, max_age_seconds: float,
            min_idle_seconds: float, now: float | None = None, emit: Callable[..., None] | None = None) -> list[dict]:
    """One pass over the cache (see the module docstring). Rows: {path, key, action, reason, bytes, last_used}."""
    from .scratch import size_of
    now = time.time() if now is None else now
    cache = Path(cache)
    if not cache.is_dir() or cache.is_symlink():
        return []
    rows, entries = [], []
    for entry in sorted(cache.iterdir()):
        if entry.is_symlink() or not entry.is_dir():
            continue
        if _BUILDING.fullmatch(entry.name):
            age = now - entry.lstat().st_mtime
            stale = age > DAY or ".gc-" in entry.name                  # a removal a restart cut short
            rows.append({"path": str(entry), "key": entry.name[:32], "action": "remove" if stale else "keep",
                         "reason": "abandoned-build" if stale else "building", "bytes": size_of(entry),
                         "last_used": entry.lstat().st_mtime})
            continue
        if not _KEY.fullmatch(entry.name):
            rows.append({"path": str(entry), "key": "", "action": "keep", "reason": "unknown", "bytes": None,
                         "last_used": None})
            continue
        try:
            used = (entry / READY).stat().st_mtime
        except OSError:
            used = entry.lstat().st_mtime
        entries.append({"path": str(entry), "key": entry.name, "action": "keep", "reason": "", "bytes": size_of(entry),
                        "last_used": used})
    total = sum(e["bytes"] for e in entries)
    for entry in sorted(entries, key=lambda e: e["last_used"]):            # least recently used first
        idle = now - entry["last_used"]
        if entry["key"] in protected:
            entry["reason"] = "live-run"
        elif idle < min_idle_seconds:
            entry["reason"] = "recent"
        elif idle >= max_age_seconds:
            entry.update(action="remove", reason="unused")
            total -= entry["bytes"]
        elif total > max_bytes:
            entry.update(action="remove", reason="over-cap")
            total -= entry["bytes"]
        else:
            entry["reason"] = "within-cap"
    rows += entries
    for row in rows:
        if row["action"] != "remove" or not apply:
            continue
        path = Path(row["path"])
        doomed = path
        if _KEY.fullmatch(path.name):
            # out of the key's name first: a provision running meanwhile builds a fresh entry, never half of this one
            doomed = path.with_name(f"{path.name}.gc-{int(now)}")
            try:
                os.rename(path, doomed)
            except OSError:
                doomed = path
        shutil.rmtree(doomed, ignore_errors=True)
        row["action"] = "failed" if doomed.exists() else "removed"
        if emit is not None:
            emit("disk_gc_removed" if row["action"] == "removed" else "disk_gc_failed", area="deps_cache",
                 path=row["path"], reason=row["reason"], bytes=row["bytes"])
    return rows
