"""One disk pass over the scratch D-266 left uncollected (D-270).

The owner's mandate after `/home` reached 100 % (2026-10-31): fix the origin so it cannot happen again. D-266 removes the
durable attempts' worktrees; three other places grew without bound (measured read-only on the live machine):

| area | what | rule |
|---|---|---|
| `legacy_executor` (68 GB) | `<state>/executor/<run>/ws/worktrees` | `bt_scheduler_executor.retention` with `preserve` |
| `verify_copies` (23 GB) | «Probar» copies `~/.local/share/bitacora-verify` | `gc_verify` |
| `deps_cache` (2.7 GB) | M6 `npm ci` per lockfile `~/.cache/m6-deps` | `gc_deps` |

The engine runs the pass in a background thread every `disk_gc.interval_min` (60) minutes, the first one
`interval_min` after it starts (`service._loop`, next to D-266's worktree pass); `bt-durable gc-scratch` runs the same pass
from the shell, a dry run unless `--apply`. Switches and limits: the `disk_gc.*` settings (`bt_config`). The two folders
outside the bitácora (`verify_copies`, `deps_cache`) are only touched for the owner's live bitácora or when their
environment variable (`BITACORA_VERIFY_DIR`, `M6_DEPS_CACHE`) names them, so a test lab never reaches the owner's.

Telemetry: `disk_gc_removed` / `disk_gc_failed` per removal, `disk_gc_area` per area and pass.
"""
from __future__ import annotations

import logging
import os
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

LOG = logging.getLogger("bt_durable.gc_scratch")
AREAS = ("legacy_executor", "verify_copies", "deps_cache")
GB, MB, HOUR, DAY = 10 ** 9, 2 ** 20, 3600, 86400


def settings() -> dict:
    """The `disk_gc.*` settings (bt_config validates their types)."""
    import bt_config
    return {name: bt_config.get(f"disk_gc.{name}") for name in (
        "enabled", "interval_min", "legacy_executor", "legacy_archive_mb", "legacy_limit", "verify_copies",
        "verify_grace_days", "deps_cache", "deps_cache_max_gb", "deps_cache_max_age_days", "deps_min_idle_hours")}


def shared_dir(env: str, default: Callable[[], Path]) -> Path | None:
    """A folder outside the bitácora: the one `env` names, else its default only for the owner's live bitácora."""
    import bt_core
    if os.environ.get(env):
        return Path(os.environ[env])
    return default() if bt_core.is_live_root() else None


@dataclass
class AreaReport:
    area: str
    applied: bool
    path: str = ""
    skipped: str = ""                                         # why the area did not run (off, no folder)
    rows: list[dict] = field(default_factory=list)

    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for row in self.rows:
            out[row["action"]] = out.get(row["action"], 0) + 1
        return out

    def kept(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for row in self.rows:
            if row["action"] in ("keep", "skip"):
                reason = str(row.get("reason") or "").split(" (")[0]
                out[reason] = out.get(reason, 0) + 1
        return out

    def bytes(self) -> int | None:
        sized = [row["bytes"] for row in self.rows if row["action"] in ("remove", "eligible", "removed")
                 and row.get("bytes") is not None]
        return sum(sized) if sized else None

    def summary(self) -> dict:
        return {"area": self.area, "applied": self.applied, "path": self.path, "skipped": self.skipped,
                "counts": self.counts(), "kept": self.kept(), "bytes": self.bytes()}


# ----------------------------------------------------------------------------------------------------- areas
def legacy_executor(root: Path, *, apply: bool, archive_max_bytes: int, limit: int | None, sizes: bool,
                    emit: Callable[..., None] | None = None) -> list[dict]:
    """Every legacy executor run under `root`: `retain_run(preserve=True)`, superseded runs known."""
    from bt_scheduler_executor.retention import retain_run, superseded_runs

    from .scratch import size_of
    rows: list[dict] = []
    replaced = superseded_runs(root)
    left = limit
    for run in sorted(Path(root).iterdir()):
        if not run.is_dir() or run.is_symlink():
            continue
        found = retain_run(run, apply=apply, preserve=True, archive_max_bytes=archive_max_bytes,
                           superseded=run.name in replaced, limit=left,
                           measure=size_of if sizes else None)
        for result in found:
            row = {"path": result.get("worktree") or result["run"], "action": result["action"],
                   "reason": result.get("reason", ""), "bytes": result.get("bytes"),
                   **{k: result[k] for k in ("attempt_id", "retained_ref", "archive", "preserve") if k in result}}
            rows.append(row)
            if emit is not None and result["action"] == "removed":
                emit("disk_gc_removed", area="legacy_executor", path=row["path"], attempt_id=result.get("attempt_id"),
                     bytes=row["bytes"], **{k: result[k] for k in ("retained_ref", "archive") if k in result})
        if left is not None:
            left = max(0, left - sum(1 for r in found if r["action"] == "removed"))
    return rows


def run_pass(state_dir: Path, root: Path, *, apply: bool, conf: dict | None = None, sizes: bool = True,
             areas: tuple[str, ...] = AREAS, emit: Callable[..., None] | None = None,
             now: float | None = None) -> list[AreaReport]:
    """One pass over the chosen areas. `state_dir` is the engine's (`<state>/durable`); `root` the bitácora."""
    from . import gc_deps, gc_verify
    conf = {**settings(), **(conf or {})}
    reports = []
    for area in areas:
        report = AreaReport(area, apply)
        reports.append(report)
        if conf.get(area) is not True:
            report.skipped = f"disk_gc.{area} is off"
            continue
        try:
            if area == "legacy_executor":
                base = Path(state_dir).parent / "executor"
                report.path = str(base)
                if not base.is_dir():
                    report.skipped = "no folder"
                    continue
                report.rows = legacy_executor(base, apply=apply, archive_max_bytes=int(conf["legacy_archive_mb"]) * MB,
                                              limit=int(conf["legacy_limit"]) or None, sizes=sizes, emit=emit)
            elif area == "verify_copies":
                base = shared_dir("BITACORA_VERIFY_DIR", gc_verify.base_dir)
                report.path = str(base or "")
                if base is None or not base.is_dir():
                    report.skipped = "no folder" if base is not None else "not the live bitácora"
                    continue
                report.rows = gc_verify.collect(base, root, apply=apply, sizes=sizes, now=now, emit=emit,
                                                grace_seconds=int(conf["verify_grace_days"]) * DAY)
            elif area == "deps_cache":
                base = shared_dir("M6_DEPS_CACHE", gc_deps.cache_dir)
                report.path = str(base or "")
                if base is None or not base.is_dir():
                    report.skipped = "no folder" if base is not None else "not the live bitácora"
                    continue
                protected = gc_deps.protected_keys(state_dir, gc_deps.project_repos(root))
                report.rows = gc_deps.collect(base, apply=apply, protected=protected, now=now, emit=emit,
                                              max_bytes=int(conf["deps_cache_max_gb"]) * GB,
                                              max_age_seconds=int(conf["deps_cache_max_age_days"]) * DAY,
                                              min_idle_seconds=int(conf["deps_min_idle_hours"]) * HOUR)
        except Exception as error:  # noqa: BLE001 - one area failing never stops the others
            LOG.warning("disk pass, %s: %s", area, error)
            report.skipped = f"failed: {type(error).__name__}: {str(error)[:200]}"
        if emit is not None:
            emit("disk_gc_area", **report.summary())
    return reports


def render(reports: list[AreaReport]) -> str:
    lines = []
    for report in reports:
        head = f"{report.area}: {report.path or '-'}"
        if report.skipped:
            lines.append(f"{head} — skipped ({report.skipped})")
            continue
        counts, size = report.counts(), report.bytes()
        done = counts.get("removed", 0) if report.applied else counts.get("remove", 0) + counts.get("eligible", 0)
        lines.append(f"{head}\n  {'removed' if report.applied else 'eligible (dry run)'}: {done}"
                     + (f", {size / GB:.2f} GB allocated" if size is not None else ""))
        kept = report.kept()
        lines.append("  kept: " + (", ".join(f"{reason} {n}" for reason, n in sorted(kept.items())) or "none"))
        if counts.get("settled"):
            lines.append(f"  settled (already absent, indexed): {counts['settled']}")
        if counts.get("failed"):
            lines.append(f"  failed: {counts['failed']}")
        if report.applied and counts.get("eligible"):
            lines.append(f"  left for the next pass (limit): {counts['eligible']}")
    if reports and not reports[0].applied:
        lines.append("nothing was removed; run again with --apply")
    return "\n".join(lines)


# ---------------------------------------------------------------------------------------------- in the engine
_thread: threading.Thread | None = None


def interval_seconds() -> float:
    conf = settings()
    return max(5, int(conf.get("interval_min") or 60)) * 60.0


def start_background(state_dir: Path, root: Path, emit: Callable[..., None], *, wait: bool = False) -> threading.Thread | None:
    """One background pass unless one still runs or `disk_gc.enabled` is off. The engine loop never waits for it."""
    global _thread
    if settings().get("enabled") is not True or (_thread is not None and _thread.is_alive()):
        return None

    def run() -> None:
        started = time.monotonic()
        try:
            reports = run_pass(state_dir, root, apply=True, emit=emit)
        except Exception as error:  # noqa: BLE001 - the next pass tries again
            LOG.warning("disk pass failed: %s", error)
            return
        if any(r.counts().get("removed") or r.counts().get("failed") for r in reports):
            LOG.info("disk pass (%.0f s): %s", time.monotonic() - started, render(reports).replace("\n", "; "))

    _thread = threading.Thread(target=run, name="bt-disk-gc", daemon=True)
    _thread.start()
    if wait:
        _thread.join()
    return _thread
