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
import bt_scheduler_decision_adapter as decision_sources
from bt_scheduler_decision import (
    DecisionEngine,
    DecisionLedger,
    DecisionRequest,
    QualityGate,
    executor_reference,
)
from bt_scheduler_decision.identity import parse_executor_reference
from bt_scheduler_decision.quality_evidence import QualityEvidenceError
from bt_scheduler_laya import CHECKPOINTS, LocalLayaClient, LocalLayaConfig

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


class DecisionAssignmentPort:
    """M1's assignment boundary: M2 recommends; this adapter translates the opaque result for M1 to validate."""

    def __init__(self, project: str, ledger_path: str | Path, *, laya_root: str | Path,
                 checkpoint: str = "typed-decisions",
                 quality_artifacts: tuple[str | Path, str | Path, str | Path, str | Path, str | Path] | None = None):
        if checkpoint not in CHECKPOINTS:
            raise ValueError("unsupported Laya checkpoint")
        if quality_artifacts is None:
            quality_gate = QualityGate()
        else:
            if not isinstance(quality_artifacts, tuple) or len(quality_artifacts) != 5:
                raise ValueError("quality artifacts must include decision, calibration, held-out, corpus and manifest paths")
            try:
                quality_gate = QualityGate.from_artifacts(*quality_artifacts)
            except (OSError, ValueError, QualityEvidenceError):
                quality_gate = QualityGate()
            if quality_gate.enabled and quality_gate.checkpoint_revision != CHECKPOINTS[checkpoint][1]:
                quality_gate = QualityGate()
        self.project = project
        self.ledger = DecisionLedger(ledger_path)
        self.checkpoint = checkpoint
        self.quality_gate = quality_gate
        self.chooser = LocalLayaClient(LocalLayaConfig(Path(laya_root).expanduser(), checkpoint, device="auto")) \
            if quality_gate.enabled else None
        self.engine = DecisionEngine(self.ledger, chooser=self.chooser, quality_gate=quality_gate)

    def propose(self, request: core.AssignmentRequest) -> tuple[core.Assignment, ...]:
        if not isinstance(request, core.AssignmentRequest) or not request.ready or request.free_slots < 1:
            return ()
        if not isinstance(request.plan_sha256, str) or len(request.plan_sha256) != 64:
            return ()
        checkpoint_revision = CHECKPOINTS[self.checkpoint][1]
        output = []
        for view in request.ready:
            if len(output) >= request.free_slots:
                break
            task, kind, classifications = decision_sources.task_facts(
                view.id, view.meta, view.dependencies, view.acceptance_criteria, view.verification,
                view.shared_resources, view.expected_paths,
            )
            decision_request = DecisionRequest(
                request.plan_id, request.revision, request.plan_sha256, request.free_slots, request.now, task,
                decision_sources._candidate_rows(self.project, kind, classifications, request.now),
                decision_sources.POLICY_VERSION, checkpoint_revision,
            )
            decision = self.engine.decide(decision_request)
            if decision.selected is None:
                continue
            stable_reference = executor_reference(decision.decision_id, decision.selected.route_id)
            # M3's current resolver accepts route:<opaque M2 ref>; it receives details via its injected lookup seam.
            output.append(core.Assignment(view.id, f"route:{stable_reference}", f"decision:{decision.decision_id}"))
        return tuple(output)

    def close(self) -> None:
        if self.chooser is not None:
            self.chooser.close()


def resolve_m2_route(ledger_path: str | Path, reference: str) -> dict[str, str] | None:
    """Resolve an M2-selected route read-only for a future executor lookup callback."""
    raw = reference[6:] if isinstance(reference, str) and reference.startswith("route:") else reference
    if parse_executor_reference(raw) is None:
        return None
    route = DecisionLedger(ledger_path, create=False).resolve_executor_reference(raw)
    if route is None:
        return None
    return {"provider": route.provider, "model": route.model, "profile": route.profile,
            "effort": route.effort or ""}


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
