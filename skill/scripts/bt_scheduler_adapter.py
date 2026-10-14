"""The only place where the methodology touches the scheduler core (`bt_scheduler_core`).

Dependency direction: methodology -> this adapter -> bt_scheduler_core. The core knows nothing about the methodology;
the methodology-specific meaning (where a requirement keeps its frozen plan and its run database, what the legacy
`RUN.json` looks like, who is the authority of a requirement's run) lives here. No other file may import the core
(tests/test_scheduler_integration.py enforces it).

Opt-in and non-destructive: a requirement is run either by the legacy supervisor (`RUN.json`) or by the scheduler core
(its run database), never both. Nothing here writes into a legacy `RUN.json`, and `PLAN.json` is only read.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

import bt_plan_adapter as plan_adapter
import bt_scheduler_core as core

RUN_DB = "SCHEDULER.db"               # file name when a requirement does not live under <root>/<project>/requirements/
PROJECTION = "RUN.projection.json"    # never RUN.json: legacy controls (bt_runstate.update) must not be able to write it
RUN_JSON = "RUN.json"
AUTHORITY = "scheduler"
REVISIONS = "plan-revisions"          # the planner's documented layout: PLAN.r<N>.json next to MANIFEST.json

# legacy RUN.json vocabularies the projection speaks (bt_runstate): run status and task status
RUN_STATUS = {"running": "running", "paused": "paused", "completed": "done", "blocked": "blocked", "cancelled": "stopped"}
TASK_STATUS = {"pending": "todo", "ready": "todo", "active": "in_progress", "recovering": "in_progress",
               "completed": "done", "blocked": "blocked", "cancelled": "blocked"}


def run_db_path(rdir: Path) -> Path:
    """Where this requirement's scheduler database lives: `<bitacora root>/.state/scheduler/<project>-<REQ>.db` for a
    requirement of the bitácora layout (the root's `.state/` is local and untracked: a live SQLite file with its
    -wal/-shm companions does not belong in the versioned documents), else `<requirement>/SCHEDULER.db`."""
    rdir = Path(rdir)
    if rdir.parent.name == "requirements" and rdir.parent.parent.name:
        req = re.match(r"REQ-\d+", rdir.name)
        name = f"{rdir.parent.parent.name}-{req.group(0) if req else rdir.name}.db"
        return rdir.parent.parent.parent / ".state" / "scheduler" / name
    return rdir / RUN_DB


def authority(rdir: Path) -> str:
    """Who runs this requirement: 'scheduler' (its run database exists), 'legacy' (a RUN.json of the old supervisor
    exists) or 'none'. Decided by the database only: the projection is a different file and proves nothing."""
    rdir = Path(rdir)
    if run_db_path(rdir).exists():
        return "scheduler"
    return "legacy" if (rdir / RUN_JSON).exists() else "none"


def refuse_legacy_run(rdir: Path) -> None:
    """Called by the legacy supervisor before it opens a run: a scheduler-owned requirement is not its to run."""
    if authority(rdir) == "scheduler":
        raise SystemExit(f"AUTHORITY_CONFLICT: {Path(rdir).name} is run by the scheduler core ({run_db_path(rdir).name}); "
                         "the legacy supervisor will not take it over")


def approved_plan(rdir: Path) -> core.Plan:
    """The latest frozen revision of this requirement's PLAN.json, loaded against the hash the planner recorded.

    The planner's manifest is the record of approval; the core re-hashes the exact file text against it, so a file
    edited after the freeze is refused. A requirement without a frozen plan has nothing approved: refused."""
    rdir = Path(rdir)
    fields = plan_adapter.run_state_fields(rdir)
    ref = fields.get("plan_ref")
    if not ref:
        problem = fields.get("plan_ref_error", "no frozen PLAN.json revision")
        raise core.SchedulerError("PLAN_NOT_APPROVED", f"{rdir.name}: {problem}")
    path = rdir / REVISIONS / f"PLAN.r{ref['revision']}.json"
    return core.load_plan_file(path, approved_sha256=ref["sha256"], plan_id=ref["plan_id"], revision=ref["revision"])


def open_scheduler(rdir: Path, *, ports: core.Ports | None = None, config: core.Config | None = None,
                   clock: Callable[[], float] | None = None) -> core.SchedulerCore:
    """A core bound to this requirement's approved plan and its own run database (created on first use).

    Refuses when a legacy supervisor run exists: one authority per requirement."""
    rdir = Path(rdir)
    if authority(rdir) == "legacy":
        raise core.SchedulerError("NOT_ALLOWED", f"{rdir.name} already has a legacy run ({RUN_JSON}); "
                                  "its history is not migrated or shared")
    plan = approved_plan(rdir)
    kwargs: dict[str, Any] = {"ports": ports, "config": config}
    if clock is not None:
        kwargs["clock"] = clock
    db = run_db_path(rdir)
    db.parent.mkdir(parents=True, exist_ok=True)
    scheduler = core.SchedulerCore(plan, core.SqliteRepository(db), **kwargs)
    scheduler.start()
    return scheduler


def project(snapshot: core.Snapshot, plan: core.Plan) -> dict[str, Any]:
    """A RUN.json-shaped read model of a scheduler run, for the tools that already read RUN.json (watch, web page).

    Derived on demand from the core's snapshot; it carries `authority: "scheduler"` so nothing mistakes it for a legacy
    state and nothing writes to it as one. The true core states stay available under `scheduler_state`."""
    tasks = []
    for spec in plan.tasks:
        view = snapshot.tasks[spec.id]
        tasks.append({"id": spec.id, "title": spec.meta.get("title", spec.id), "repo": spec.repository or None,
                      "after": list(spec.after), "milestone": spec.milestone_id or None,
                      "status": TASK_STATUS[view["state"]], "scheduler_state": view["state"],
                      "unreachable": view["unreachable"], "attempts": view["attempts"],
                      "evidence": view["evidence"], "executor": view["executor"]})
    return {"req": snapshot.plan_id, "authority": AUTHORITY, "projection": True,
            "status": RUN_STATUS[snapshot.status], "scheduler_status": snapshot.status,
            "plan_ref": {"plan_id": snapshot.plan_id, "revision": snapshot.revision, "sha256": snapshot.plan_sha256},
            "sessions": sum(v["attempts"] for v in snapshot.tasks.values()), "tasks": tasks,
            "attention": list(snapshot.attention),
            "projected_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds")}


def write_projection(rdir: Path, scheduler: core.SchedulerCore) -> Path:
    """Write the read model next to the requirement as `RUN.projection.json` (atomic). It is never `RUN.json`, so a
    legacy state file can neither be overwritten by it nor receive a legacy control write meant for a scheduler run."""
    rdir = Path(rdir)
    target = rdir / PROJECTION
    body = json.dumps(project(scheduler.snapshot(), scheduler.plan), indent=1, sort_keys=True) + "\n"
    fd, tmp = tempfile.mkstemp(dir=rdir, prefix=".RUN.projection.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp, 0o644)                  # mkstemp makes it 0600; the file is read by other tools of the same user
        os.replace(tmp, target)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
    return target
