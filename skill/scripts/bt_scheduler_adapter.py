"""The only place where the methodology touches the scheduler core (`bt_scheduler_core`).

Dependency direction: methodology -> this adapter -> bt_scheduler_core. The core knows nothing about the methodology;
the methodology-specific meaning (where a requirement keeps its frozen plan and its run database, what the legacy
`RUN.json` looks like, who is the authority of a requirement's run) lives here. No other file may import the core
(tests/test_scheduler_integration.py enforces it).

M4's read-only/operator and stream bridges live in `bt_scheduler_monitor_adapter`; this adapter keeps M1 as the sole
owner of scheduler state and does not import monitor internals.

Opt-in and non-destructive: a requirement is run either by the legacy supervisor (`RUN.json`) or by the scheduler core
(its run database), never both. Nothing here writes into a legacy `RUN.json`, and `PLAN.json` is only read.
"""
from __future__ import annotations

import contextlib
import datetime as dt
import json
import os
import re
import sqlite3
import tempfile
from collections.abc import Callable, Iterator
from dataclasses import replace
from pathlib import Path
from typing import Any

import bt_plan_adapter as plan_adapter
import bt_scheduler_core as core
import bt_scheduler_core.plan as m1_plan
import bt_scheduler_decision_adapter as decision_sources
import bt_scheduler_plan_compat as plan_compat
import bt_scheduler_metadata as task_metadata
from bt_scheduler_core.subplans import (adapter_record_composition as record_composition,
                                        adapter_record_subplan_version as record_subplan_version)
from bt_scheduler_decision import (
    DecisionEngine,
    DecisionInputError,
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
SCHEDULER_STALE_MINUTES = 2
M1_INCIDENT_CONTRACT = "1.2.0"
_PLAN_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
DOWNSTREAM_PLAN_SCHEMA_VERSION = plan_compat.DEFAULT_PLAN_SCHEMA_VERSION
DOWNSTREAM_PLAN_SCHEMA_SINCE = plan_compat.PLAN_SCHEMA_CAPABILITY_SINCE
_M2_MAX_BATCH_TASKS = 128  # Frozen batch_decision.maximum_tasks; this bound survives record version 1.3.0.
_QUOTA_PREFLIGHT_MAX_ACCOUNTS = 32


def refresh_quota_preflight(project: str) -> dict[str, dict[str, object]]:
    """Refresh due quota sources for this project's authorized, effective account pool only."""
    from bt_scheduler_quota_preflight import refresh
    return refresh(project, _QUOTA_PREFLIGHT_MAX_ACCOUNTS)


def supports_incident_observed(scheduler: object) -> bool:
    """Check the installed M1 capability before the M4 adapter claims any incident reference."""
    version = getattr(scheduler, "contract_version", None)
    if not isinstance(version, str):
        return False
    try:
        major, minor, _patch = (int(part) for part in version.split("."))
    except ValueError:
        return False
    return major == 1 and minor >= 2


def downstream_compatibility(schema_version: str = DOWNSTREAM_PLAN_SCHEMA_VERSION) -> dict[str, object]:
    """Report Planner and M1/M2/M6 schema capabilities; missing or malformed markers stay unknown."""
    planner_version = getattr(plan_adapter.planner, "SCHEMA_VERSION", None)
    return plan_compat.downstream_compatibility(
        schema_version, planner_version=planner_version,
        m1_capabilities=getattr(m1_plan, "PLAN_SCHEMA_CAPABILITIES", None),
    )


def plan_compatibility_report(rdir: Path, *, plan_path: Path | None = None) -> dict[str, object]:
    """Build a fresh report for the schema version in this working or frozen PLAN.json."""
    path = Path(plan_path) if plan_path is not None else Path(rdir) / plan_adapter.planner.PLAN_JSON
    return plan_compat.compatibility_report(
        path, planner_version=getattr(plan_adapter.planner, "SCHEMA_VERSION", None),
        m1_capabilities=getattr(m1_plan, "PLAN_SCHEMA_CAPABILITIES", None),
    )


def plan_consumer_problem(rdir: Path, *, plan_path: Path | None = None) -> str | None:
    """Reject schema 1.2.0+ when Planner, M1, M2 or M6 does not declare exact support."""
    path = Path(plan_path) if plan_path is not None else Path(rdir) / plan_adapter.planner.PLAN_JSON
    return plan_compat.consumer_problem(
        rdir, plan_path=path, planner_version=getattr(plan_adapter.planner, "SCHEMA_VERSION", None),
        m1_capabilities=getattr(m1_plan, "PLAN_SCHEMA_CAPABILITIES", None),
    )


def build_incident_observed_event(scheduler: core.SchedulerCore, reference: dict[str, object], *,
                                  confidence: str, idempotency_key: str, observed_at: str) -> dict[str, object]:
    """Translate a validated M4 reference into M1's versioned event envelope."""
    payload = {**reference, "confidence": confidence, "observed_at": observed_at,
               "idempotency_key": idempotency_key}
    plan = scheduler.plan
    return {"event_id": idempotency_key, "plan_id": plan.plan_id, "revision": plan.revision,
            "task_id": reference.get("task_id"), "attempt_id": reference.get("attempt_id"), "source": "m4",
            "kind": "incident_observed", "occurred_at": observed_at, "payload": payload,
            "contract_version": M1_INCIDENT_CONTRACT}


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


@contextlib.contextmanager
def owner_lock(rdir: Path) -> Iterator[None]:
    """Serialize legacy-run initialization with the Scheduler owner for this requirement."""
    lock_path = run_db_path(rdir).with_suffix(".owner.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = lock_path.open("a+b")
    try:
        if os.name == "nt":
            import msvcrt
            try:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise core.SchedulerError("OWNER_ACTIVE", "another Scheduler or legacy owner is starting") from exc
        else:
            import fcntl
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise core.SchedulerError("OWNER_ACTIVE", "another Scheduler or legacy owner is starting") from exc
        yield
    finally:
        if os.name == "nt":
            import msvcrt
            try:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            except OSError:
                pass
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def authority(rdir: Path) -> str:
    """Who runs this requirement: 'scheduler' (its run database exists), 'legacy' (a RUN.json of the old supervisor
    exists) or 'none'. Decided by the database only: the projection is a different file and proves nothing."""
    rdir = Path(rdir)
    if run_db_path(rdir).exists():
        return "scheduler"
    return "legacy" if (rdir / RUN_JSON).exists() else "none"


def scheduler_authority(rdir: Path) -> bool:
    """Whether the durable M1 database, rather than a projection, owns this requirement."""
    return authority(rdir) == AUTHORITY


def read_projection(rdir: Path) -> dict[str, Any] | None:
    """Read only the projection belonging to an existing Scheduler database; never fall back to RUN.json."""
    if not scheduler_authority(rdir):
        return None
    try:
        data = json.loads((Path(rdir) / PROJECTION).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    plan_ref = data.get("plan_ref") if isinstance(data, dict) else None
    if (not isinstance(data, dict) or data.get("authority") != AUTHORITY or data.get("projection") is not True
            or data.get("status") not in RUN_STATUS.values() or not isinstance(data.get("tasks"), list)
            or not isinstance(plan_ref, dict) or not isinstance(plan_ref.get("plan_id"), str)
            or not plan_ref["plan_id"].strip() or type(plan_ref.get("revision")) is not int
            or plan_ref["revision"] < 1 or not isinstance(plan_ref.get("sha256"), str)
            or not _PLAN_SHA256.fullmatch(plan_ref["sha256"])
            or not isinstance(data.get("attention", []), list)):
        return None
    for task in data["tasks"]:
        if (not isinstance(task, dict) or not isinstance(task.get("id"), str)
                or not isinstance(task.get("title"), str) or task.get("status") not in TASK_STATUS.values()
                or type(task.get("attempts")) is not int or task["attempts"] < 0):
            return None
        for key in ("complexity", "provider", "model", "effort", "profile", "account_ref", "route_status",
                    "route_reason", "selection_reason", "quota_state", "quota_reason", "quota_observed_at",
                    "quota_valid_until", "quota_used_percent"):
            if key in task and not isinstance(task[key], str):
                return None
        if task.get("quota_state", "") not in {"", "fresh", "stale", "missing", "malformed", "refresh_failed",
                                                 "exhausted"}:
            return None
        if task.get("route_status", "unplanned") not in {"unplanned", "recommended", "unavailable", "assigned"}:
            return None
    heartbeat = data.get("heartbeat_at")
    if heartbeat is not None and not isinstance(heartbeat, str):
        return None
    data["heartbeat"] = {"at": heartbeat} if heartbeat else {}
    return data


def projection_is_stale(data: dict[str, Any]) -> bool:
    if data.get("status") not in ("running", "waiting", "paused"):
        return False
    heartbeat = data.get("heartbeat_at")
    if not isinstance(heartbeat, str) or not heartbeat:
        return True
    try:
        at = dt.datetime.fromisoformat(heartbeat)
    except ValueError:
        return True
    if at.tzinfo is None:
        at = at.replace(tzinfo=dt.UTC)
    age = (dt.datetime.now(dt.UTC) - at.astimezone(dt.UTC)).total_seconds() / 60
    return age > SCHEDULER_STALE_MINUTES


def apply_control(rdir: Path, action: str, *, by: str = "web") -> None:
    """Route operator controls to M1 without starting/reconciling the Scheduler runtime."""
    methods = {"pause": "pause", "resume": "resume", "stop": "cancel"}
    method = methods.get(action)
    if method is None:
        raise SystemExit(f"Acción desconocida: {action}")
    if not scheduler_authority(rdir):
        raise SystemExit("Este requerimiento no tiene autoridad Scheduler.")
    db = run_db_path(rdir)
    if not db.is_file():
        raise SystemExit("La base Scheduler no está disponible; no se cambió el control.")
    try:
        plan = None
        try:
            conn = sqlite3.connect(f"{db.resolve().as_uri()}?mode=ro", uri=True, timeout=1)
            try:
                row = conn.execute("SELECT doc FROM state WHERE id = 1").fetchone()
            finally:
                conn.close()
            identity = json.loads(row[0]) if row else None
            if (isinstance(identity, dict) and isinstance(identity.get("plan_id"), str) and identity["plan_id"] and
                    type(identity.get("revision")) is int and identity["revision"] >= 1 and
                    isinstance(identity.get("plan_sha256"), str) and
                    _PLAN_SHA256.fullmatch(identity["plan_sha256"])):
                plan_path = rdir / REVISIONS / f"PLAN.r{identity['revision']}.json"
                if plan_path.is_file() and not plan_consumer_problem(rdir, plan_path=plan_path):
                    plan = core.load_plan_file(plan_path, approved_sha256=identity["plan_sha256"],
                                               plan_id=identity["plan_id"], revision=identity["revision"])
        except (OSError, sqlite3.Error, TypeError, ValueError, KeyError, core.SchedulerError):
            plan = None
        if plan is None:
            plan = approved_plan(rdir)
        repository = core.SqliteRepository(db, create=False)
        scheduler = core.SchedulerCore(plan, repository)
        scheduler.inspect()
        getattr(scheduler, method)(by)
    except core.SchedulerError as exc:
        raise SystemExit(f"Control Scheduler rechazado [{exc.code}]: {exc}") from exc


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
    if problem := plan_consumer_problem(rdir, plan_path=path):
        raise core.SchedulerError("PLAN_CONSUMER_INCOMPATIBLE", problem)
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
                 quality_artifacts: tuple[str | Path, str | Path, str | Path, str | Path, str | Path] | None = None,
                 classification_overlay: Callable[[], dict[str, dict[str, object]]] | None = None):
        self.classification_overlay = classification_overlay
        self.run_dir: Path | None = None
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

    def effective_meta(self, task_id: str, meta: Any) -> Any:
        """The task's classification as it stands NOW: the plan's `meta` with the amendments in force laid over it.
        Only the next decision sees a change; an attempt already running keeps the route it was started with."""
        return task_metadata.effective_task_meta(task_id, meta, self.classification_overlay)

    @staticmethod
    def _route_metadata(decision_id: str, route, candidate) -> dict[str, str]:
        return {"schema_version": core.ROUTING_CONTRACT_VERSION, "decision_id": decision_id,
                "route_id": route.route_id, "provider": route.provider,
                "model": route.model, "profile": route.profile, "effort": route.effort or "",
                "account_ref": route.account_ref, "selection_reason": ";".join(route.factor_codes),
                "quota_state": "fresh" if candidate.quota_status == "available" else candidate.quota_status,
                "quota_reason": ";".join(candidate.source_reason_codes),
                "quota_observed_at": "" if candidate.quota_observed_at is None else str(candidate.quota_observed_at),
                "quota_valid_until": "" if candidate.quota_valid_until is None else str(candidate.quota_valid_until),
                "quota_used_percent": "" if candidate.quota_used_percent is None else str(candidate.quota_used_percent)}

    def plan(self, request: core.PlanRoutingRequest) -> tuple[core.PlannedRoute, ...]:
        """Map every task in the approved DAG to a current M2 recommendation without reserving capacity."""
        if not isinstance(request, core.PlanRoutingRequest):
            return ()
        from bt_scheduler_plan_routing import plan_full_dag
        return plan_full_dag(core, self, request, refresh_quota_preflight)

    def propose(self, request: core.AssignmentRequest) -> tuple[core.Assignment, ...]:
        if not isinstance(request, core.AssignmentRequest) or not request.ready or request.free_slots < 1:
            return ()
        if not isinstance(request.plan_sha256, str) or not _PLAN_SHA256.fullmatch(request.plan_sha256):
            return ()
        checkpoint_revision = CHECKPOINTS[self.checkpoint][1]
        if len(request.ready) > _M2_MAX_BATCH_TASKS:
            raise DecisionInputError(["ready_batch:task_limit_exceeded"])
        views = request.ready
        try:
            quota_preflight = refresh_quota_preflight(self.project)
        except Exception:  # noqa: BLE001 - an unavailable refresh must not reuse cached quota as current.
            quota_preflight = {"*": {"status": "unavailable", "reason": "quota_refresh_failed"}}
        from bt_scheduler_plan_routing import (
            _quota_evidence,
            persist_dispatch_batch,
            quota_aware_requested_at,
        )
        requested_at = quota_aware_requested_at(request.now, quota_preflight)
        decision_requests = []
        candidates_by_task = {}
        preserve_baseline_by_task = {}
        quota_evidence_by_task = {}
        for view in views:
            task, kind, classifications = decision_sources.task_facts(
                view.id, self.effective_meta(view.id, view.meta), view.dependencies, view.acceptance_criteria,
                view.verification, view.shared_resources, view.expected_paths,
            )
            candidates = decision_sources._candidate_rows(self.project, kind, classifications, requested_at)
            pinned = False
            if self.run_dir is not None:
                import bt_route_pins
                pinned = bt_route_pins.get(self.run_dir, view.id) is not None
                candidates = bt_route_pins.narrow(self.run_dir, view.id, candidates)
            candidates = tuple(
                replace(candidate, quota_status="unknown")
                if candidate.provider in {"claude", "codex", "antigravity"} and
                (not isinstance(quota_preflight, dict) or
                 not isinstance(quota_preflight.get(candidate.profile), dict) or
                 quota_preflight[candidate.profile].get("status") != "available")
                else candidate
                for candidate in candidates
            )
            decision_request = DecisionRequest(
                request.plan_id, request.revision, request.plan_sha256, request.free_slots, requested_at, task,
                candidates,
                decision_sources.POLICY_VERSION, checkpoint_revision,
                dispatch_generation=view.attempts,
            )
            decision_requests.append(decision_request)
            preserve_baseline_by_task[view.id] = kind != "docs"
            quota_evidence_by_task[view.id] = _quota_evidence(view.id, candidates, quota_preflight)
            candidates_by_task[view.id] = {
                (candidate.route_id, candidate.account_ref): candidate
                for candidate in decision_request.candidates
            }
            if pinned and not candidates:
                # A stale pin pauses this task rather than silently assigning it elsewhere.
                decision_requests.pop()
                candidates_by_task.pop(view.id, None)
                preserve_baseline_by_task.pop(view.id, None)
                quota_evidence_by_task.pop(view.id, None)
        if not decision_requests:
            return ()

        batch = persist_dispatch_batch(
            self.ledger, tuple(decision_requests), preserve_baseline_by_task=preserve_baseline_by_task,
            quota_evidence_by_task=quota_evidence_by_task,
        )
        requests_by_task = {item.task.task_id: item for item in decision_requests}
        view_order = {view.id: index for index, view in enumerate(views)}
        output = []
        for assignment in sorted(batch.assignments, key=lambda item: view_order[item.task_id]):
            decision_request = requests_by_task.get(assignment.task_id)
            candidate = candidates_by_task.get(assignment.task_id, {}).get(
                (assignment.route_id, assignment.account_ref)
            )
            if decision_request is None or candidate is None:
                continue
            decision = self.engine.decide(replace(decision_request, candidates=(candidate,)))
            selected = decision.selected
            if selected is None or (selected.route_id, selected.account_ref) != (
                    assignment.route_id, assignment.account_ref):
                continue
            stable_reference = executor_reference(decision.decision_id, selected.route_id)
            output.append(core.Assignment(
                assignment.task_id, f"route:{stable_reference}", f"decision:{decision.decision_id}",
                self._route_metadata(decision.decision_id, selected, candidate),
            ))
            if len(output) >= request.free_slots:
                break
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


def project(snapshot: core.Snapshot, plan: core.Plan,
            task_budgets: dict[str, dict[str, int | bool | str]] | None = None) -> dict[str, Any]:
    """A RUN.json-shaped read model of a scheduler run, for the tools that already read RUN.json (watch, web page).

    Derived on demand from the core's snapshot; it carries `authority: "scheduler"` so nothing mistakes it for a legacy
    state and nothing writes to it as one. The true core states stay available under `scheduler_state`."""
    tasks = []
    for spec in plan.tasks:
        view = snapshot.tasks[spec.id]
        route = view.get("route_metadata", {})
        if not isinstance(route, dict):
            route = {}
        complexity = spec.meta.get("complexity")
        row = {"id": spec.id, "title": spec.meta.get("title", spec.id), "repo": spec.repository or None,
                      "after": list(spec.after), "milestone": spec.milestone_id or None,
                      "status": TASK_STATUS[view["state"]], "scheduler_state": view["state"],
                      "unreachable": view["unreachable"], "attempts": view["attempts"],
                      "evidence": view["evidence"], "executor": view["executor"],
                      "complexity": complexity if isinstance(complexity, str) else "",
                      "provider": route.get("provider", ""), "model": route.get("model", ""),
                      "effort": route.get("effort", ""),
                      "profile": route.get("profile", ""), "account_ref": route.get("account_ref", ""),
                      "selection_reason": route.get("assignment_reason", route.get("selection_reason", "")),
                      "quota_state": route.get("quota_state", ""), "quota_reason": route.get("quota_reason", ""),
                      "quota_observed_at": route.get("quota_observed_at", ""),
                      "quota_valid_until": route.get("quota_valid_until", ""),
                      "quota_used_percent": route.get("quota_used_percent", ""),
                      "route_status": view.get("route_status", "unplanned"),
                      "route_reason": view.get("route_reason", "")}
        if task_budgets and spec.id in task_budgets:
            row.update(task_budgets[spec.id])
        tasks.append(row)
    heartbeat = dt.datetime.now(dt.UTC).isoformat(timespec="seconds")
    return {"req": snapshot.plan_id, "authority": AUTHORITY, "projection": True,
            "status": RUN_STATUS[snapshot.status], "scheduler_status": snapshot.status,
            "plan_ref": {"plan_id": snapshot.plan_id, "revision": snapshot.revision, "sha256": snapshot.plan_sha256},
            "sessions": sum(v["attempts"] for v in snapshot.tasks.values()), "tasks": tasks,
            "attention": list(snapshot.attention), "heartbeat_at": heartbeat, "projected_at": heartbeat}


def write_projection(rdir: Path, scheduler: core.SchedulerCore) -> Path:
    """Write the read model next to the requirement as `RUN.projection.json` (atomic). It is never `RUN.json`, so a
    legacy state file can neither be overwritten by it nor receive a legacy control write meant for a scheduler run."""
    rdir = Path(rdir)
    target = rdir / PROJECTION
    import bt_scheduler_projection

    task_budgets = bt_scheduler_projection.attempt_budgets(scheduler)
    body = json.dumps(project(scheduler.snapshot(), scheduler.plan, task_budgets), indent=1, sort_keys=True) + "\n"
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
    _refresh_plan_block(rdir)
    return target


def _refresh_plan_block(rdir: Path) -> None:
    """Keep the generated status block of PLAN.md in step with the projection; best-effort, never raises."""
    try:
        if authority(rdir) != AUTHORITY:  # a projection beside a legacy run owns nothing: leave that PLAN.md alone
            return
        import bt_planblock
        bt_planblock.refresh_plan_block(Path(rdir).resolve().parents[1].name, rdir)
    except Exception:
        pass


def is_stalled(scheduler: core.SchedulerCore, snapshot: core.Snapshot | None = None) -> bool:
    """Expose M1's idle-stop decision to the owner without duplicating its state rules."""
    return scheduler._stalled(snapshot or scheduler.snapshot())


def simulate_audit(plan_path: Path, *, fail: dict[str, int] | None = None, reject: dict[str, int] | None = None,
                   start: float | None = None) -> list[dict[str, Any]]:
    """Run a plan file through the core's deterministic doubles (no provider, no database, nothing written) and return
    its audit trail as rows `{seq, at, kind, plan_id, task_id, attempt_id, detail}`. `fail` / `reject` script how many
    attempts of a task fail to execute / are rejected by the verifier. Time is simulated: one step = one second after
    `start` (default: now). The frozen-plan check is bypassed on purpose: a demonstration runs any valid plan."""
    import hashlib

    from bt_scheduler_core.simulation import Script, simulate
    from bt_scheduler_core.simulators import ManualClock
    path = Path(plan_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    plan = core.load_plan_file(path, approved_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                               plan_id=data["plan_id"], revision=data["revision"])
    clock = ManualClock(dt.datetime.now(dt.UTC).timestamp() if start is None else start)
    _, scheduler = simulate(plan, core.InMemoryRepository(), script=Script(fail=fail or {}, reject=reject or {}),
                            recovery=core.ScriptedRecovery(), config=core.Config(max_attempts=3), clock=clock)  # M5 double: retry
    return [entry.to_dict() for entry in scheduler.audit_log()]


def record_amendment(rdir: Path, record: dict[str, Any]) -> bool:
    """Note an applied amendment in the run's audit (`amendment_applied`), as an observation: no task or attempt state
    changes and nothing is decided. False when the requirement has no Scheduler run (nothing to note)."""
    if authority(rdir) != AUTHORITY:
        return False
    repository = core.SqliteRepository(run_db_path(rdir))
    with repository.transaction() as tx:
        if tx.state is None:
            return False
        tx.audit("amendment_applied", at=dt.datetime.now(dt.UTC).timestamp(), task_id=record["task"],
                 field=record["field"], old=record["from"], new=record["to"], by=record["by"],
                 proposed_by=record["proposed_by"], reason=record["reason"][:160], seq=record["seq"])
    return True


def rebase_cascade() -> bool:
    """`gates.rebase_cascade`: "content" (default since REQ-030: an accepted task whose own content did not change is kept
    whatever happened to its prerequisites) or "downstream" (the original: a reset prerequisite resets what depends on it)."""
    import bt_config

    try:
        return bt_config.get("gates.rebase_cascade", "content") == "downstream"
    except (KeyError, TypeError):
        return False


def rebase_to_latest(rdir: Path) -> Any:
    """Move this requirement's Scheduler run onto the latest frozen plan revision, keeping accepted work that did not
    change (M1's `rebase_run`). Refused while an owner process holds the run or any attempt is alive."""
    rdir = Path(rdir)
    if authority(rdir) != AUTHORITY:
        raise core.SchedulerError("NOT_ALLOWED", f"{rdir.name} has no Scheduler run to rebase")
    new = approved_plan(rdir)
    db = run_db_path(rdir)
    try:
        conn = sqlite3.connect(f"{db.resolve().as_uri()}?mode=ro", uri=True, timeout=1)
        try:
            row = conn.execute("SELECT doc FROM state WHERE id = 1").fetchone()
        finally:
            conn.close()
        doc = json.loads(row[0])
    except (sqlite3.Error, TypeError, ValueError) as exc:
        raise core.SchedulerError("STATE_UNREADABLE", f"cannot read the run of {rdir.name}") from exc
    old_path = rdir / REVISIONS / f"PLAN.r{doc['revision']}.json"
    old = core.load_plan_file(old_path, approved_sha256=doc["plan_sha256"], plan_id=doc["plan_id"],
                              revision=doc["revision"])
    with owner_lock(rdir):
        return core.rebase_run(core.SqliteRepository(db), old, new, cascade=rebase_cascade())


def revision_plan(rdir: Path, revision: int, sha256: str, plan_id: str) -> core.Plan:
    """Load one known frozen revision by its exact M1 plan identity."""
    if type(revision) is not int or revision < 1 or not _PLAN_SHA256.fullmatch(str(sha256)) or not plan_id:
        raise core.SchedulerError("PLAN_MISMATCH", "revision plan identity is invalid")
    path = Path(rdir) / REVISIONS / f"PLAN.r{revision}.json"
    return core.load_plan_file(path, approved_sha256=sha256, plan_id=plan_id, revision=revision)


def revision_identity(rdir: Path) -> dict[str, Any]:
    """Fresh M1 identity used by the recovery CAS; read-only and independent of the projection."""
    if authority(rdir) != AUTHORITY:
        raise core.SchedulerError("NOT_ALLOWED", "no Scheduler run")
    import bt_recovery_m1_bridge
    return bt_recovery_m1_bridge.revision_identity(core, run_db_path(rdir))


def apply_plan_revision(rdir: Path, old: core.Plan, new: core.Plan, guard: dict[str, Any]) -> dict[str, Any]:
    """Thin M1 forward used only by journaled recovery application; ordinary rebase semantics are unchanged."""
    import bt_recovery_m1_bridge
    return bt_recovery_m1_bridge.apply_plan_revision(core, run_db_path(rdir), owner_lock, rdir, old, new, guard)


def abort_revision_barrier(rdir: Path, operation_key: str, reason: str) -> bool:
    if authority(rdir) != AUTHORITY:
        return False
    import bt_recovery_m1_bridge
    return bt_recovery_m1_bridge.abort_revision_barrier(core, run_db_path(rdir), operation_key, reason)
