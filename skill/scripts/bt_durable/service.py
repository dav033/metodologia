"""The engine process: wire the real ports, launch DBOS (which recovers this executor's workflows), reap orphans.

Run it as a systemd user service (`deploy/bt-durable.service`): `Restart=always` replaces the legacy watchdog, and
DBOS recovery replaces the owner's reconciliation loop. The reaper closes the one gap DBOS cannot see: an agent unit
whose workflow was cancelled or finished while the unit kept running (cancellation must stop every writer).
"""
from __future__ import annotations

import logging
import signal
import threading
import time
from collections.abc import Callable
from pathlib import Path

from bt_contracts.execution import AttemptRef, Route
from dbos import DBOS

from .adapters.audit import AuditGate
from .adapters.briefs import DurableBriefs
from .adapters.composition import CompositionComposer
from .adapters.integration import GitLineIntegrator
from .adapters.m3 import M3Attempts
from .adapters.m6 import M6Verifier
from .adapters.plans import FilePlans
from .adapters.routes import build_router
from .adapters.runtime import SupervisorRuntime
from .adapters.telemetry import JsonlTelemetry
from .execution import engine, steps
from .ports import Ports
from .settings import EngineConfig

LOG = logging.getLogger("bt_durable.service")
TERMINAL = frozenset({"SUCCESS", "ERROR", "CANCELLED", "MAX_RECOVERY_ATTEMPTS_EXCEEDED"})


def wire(cfg: EngineConfig, *, repositories_for: Callable[[str], object], driver_for: Callable[[str], object],
         routes: list[Route], verifier: M6Verifier | None = None, runtime=None, capacity=None,
         briefs_for=None, router: str = "m2") -> Ports:
    """`router`: `m2` ranks the allowed routes with the M2 decision engine (static list if it cannot be built),
    `static` keeps the ordered list. Either way `capacity` is the live quota signal."""
    cfg.state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    cfg.state_dir.chmod(0o700)                             # M6 and the supervisor refuse a shared directory
    plans = FilePlans()
    attempts = M3Attempts(root=cfg.state_dir / "attempts-root", repositories_for=repositories_for,
                          plan_for=lambda attempt: steps.plan(attempt.run), driver_for=driver_for,
                          briefs_for=briefs_for or DurableBriefs(repositories_for=repositories_for))

    integrator = _ProjectIntegrator(repositories_for, cfg.state_dir)
    telemetry = JsonlTelemetry(cfg.state_dir / "telemetry.jsonl")
    attempts.telemetry = telemetry                           # capture-time file guard events (adapters/size_guard.py)
    return Ports(plans=plans, router=build_router(router, routes, capacity, telemetry=telemetry.emit),
                 preparer=attempts, runtime=runtime or SupervisorRuntime(cfg.state_dir / "supervisor"), reader=attempts,
                 capturer=attempts, verifier=verifier or operator_verifier(cfg.state_dir / "m6-quality.sqlite3"),
                 integrator=integrator, telemetry=telemetry, composer=integrator,
                 auditor=AuditGate(repositories_for))


def requirement_dir(run) -> Path:
    return Path(run.plan_path).parent.parent              # <req dir>/plan-revisions/PLAN.rN.json


def operator_verifier(store_path: Path) -> M6Verifier:
    """M6 with the operator's per-run policy, authorization callbacks and coordinator receipts for manual checks, and
    the notes trail the legacy owner keeps (`RUN.notes/<task>.history.jsonl`, `<task>.verify.md`)."""
    from bt_scheduler_executor_wiring import operator_quality_policy
    from bt_scheduler_verification_authority import owner_verification_authority

    from .legacy import attestations
    verifier = M6Verifier(store_path=store_path,
                          policy_for=lambda run: operator_quality_policy(run.project, requirement_dir(run)),
                          authority_for=lambda run: owner_verification_authority(requirement_dir(run), run.project),
                          attestations_for=lambda run: attestations(requirement_dir(run)),
                          on_verdict=record_verdict)
    for key in verifier.recover_interrupted():                # D-171: a restart never leaves a verification orphaned
        LOG.info("verification %s was interrupted by the restart: queued to run again", key)
    return verifier


def record_verdict(attempt: AttemptRef, outcome) -> None:
    """What the legacy quality port writes after a verdict: a FAIL's digest becomes the last-failure note and one line
    of the task's history; a PASS clears the note. A verdict that is not about the code (needs review) writes nothing."""
    from .legacy import record_history, write_verify_notes
    rdir = requirement_dir(attempt.run)
    if outcome.status.value == "FAIL" and outcome.digest:
        write_verify_notes(rdir, attempt.task_id, outcome.digest)
        record_history(rdir, attempt.task_id, attempt.attempt_key, outcome.digest)
    elif outcome.status.value == "PASS":
        write_verify_notes(rdir, attempt.task_id, "")


class _ProjectIntegrator:
    """Integration lines and composition gates are per project; the run tells which project's repositories to use."""

    def __init__(self, repositories_for: Callable[[str], object], state_dir: Path):
        self.repositories_for = repositories_for
        self.state_dir = Path(state_dir)
        self._lines: dict[str, GitLineIntegrator] = {}

    def _for(self, project: str) -> GitLineIntegrator:
        if project not in self._lines:
            line = GitLineIntegrator(self.repositories_for(project))
            line.composer = CompositionComposer(self.state_dir, lines=line, plan_for=steps.plan)
            self._lines[project] = line
        return self._lines[project]

    def base_ref(self, run, task, *, home="", lines=()):
        return self._for(run.project).base_ref(run, task, home=home, lines=lines)

    def integrate(self, run, task, snapshot, *, lines=()):
        return self._for(run.project).integrate(run, task, snapshot, lines=lines)

    def sync(self, run, role, items):
        return self._for(run.project).sync(run, role, items)

    def compose(self, run, gate_id, evidence):
        return self._for(run.project).composer.compose(run, gate_id, evidence)


def reap_once(prefix: str = "") -> list[str]:
    """Terminate agent units whose workflow is terminal (cancelled, failed, finished) but which are still alive."""
    ports = engine.ports()
    reaped = []
    for key in ports.runtime.owned(prefix):
        status = DBOS.get_workflow_status(f"bt:{key}:agent")
        if status is not None and status.status not in TERMINAL:
            continue
        stub = _stub(key)
        try:
            record = ports.runtime.observe(stub)
            if record.state in ("running", "unknown"):
                ports.runtime.terminate(stub)
                reaped.append(key)
                ports.telemetry.emit("orphan_reaped", attempt_key=key,
                                     workflow_status=status.status if status else None)
            ports.runtime.release(stub)
        except Exception as error:  # noqa: BLE001 - the next pass tries again; the unit stays "busy" meanwhile
            LOG.warning("reaper could not settle %s: %s", key, error)
    return reaped


def _stub(key: str) -> AttemptRef:
    """The runtime only needs the attempt key; a minimal reference that renders exactly that key."""
    return _KeyRef(key)


class _KeyRef:
    def __init__(self, key: str):
        self.attempt_key = key
        self.workflow_id = f"bt:{key}:agent"


def serve(cfg: EngineConfig, ports: Ports, *, reap_seconds: float = 30.0, project_seconds: float = 5.0,
          stop: threading.Event | None = None, marker: Path | None = None) -> None:
    """Run the engine until SIGTERM/SIGINT: reap orphan units and refresh the panels' projections of every run
    (`bt_durable.projection`; a read model the workflows never read back). `marker` (default
    `<state>/engine.json`) tells operator tools which message features this engine's workflows understand."""
    from .projection import EngineProjector
    from .remote import write_marker
    stop = stop or threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: stop.set())
    engine.start(cfg, ports)
    write_marker(marker or cfg.state_dir / "engine.json")
    projector = EngineProjector(DBOS)
    tick = max(0.2, min(reap_seconds, project_seconds))
    last_reap = time.monotonic()
    try:
        while True:
            try:
                projector.refresh()
            except Exception as error:  # noqa: BLE001 - the panels show the last projection until the next pass
                LOG.warning("projection pass failed: %s", error)
            if stop.wait(tick):
                break
            if time.monotonic() - last_reap >= reap_seconds:
                last_reap = time.monotonic()
                try:
                    reap_once()
                except Exception as error:  # noqa: BLE001
                    LOG.warning("reaper pass failed: %s", error)
                try:
                    _drain_joins(cfg, ports)
                except Exception as error:  # noqa: BLE001 - a join is tried again on the next pass
                    LOG.warning("stage join pass failed: %s", error)
                try:
                    _heal_decisions(cfg)
                except Exception as error:  # noqa: BLE001 - an open decision is looked at again on the next pass
                    LOG.warning("healing pass failed: %s", error)
    finally:
        engine.stop()


def _drain_joins(cfg: EngineConfig, ports: Ports) -> None:
    """Complete the stage joins that waited for a quiet run (bt_durable.stage_join, `RUN.join.json`)."""
    import bt_core

    from . import stage_join
    if not any(Path(bt_core.ROOT).glob(f"*/requirements/*/{stage_join.PENDING}")):
        return
    from .client import Client
    client = Client(cfg.system_database_url)
    try:
        for outcome in stage_join.drain(Path(bt_core.ROOT), client, state_dir=cfg.state_dir,
                                        repositories_for=ports.integrator.repositories_for, emit=ports.telemetry.emit):
            LOG.info("stage join: %s", outcome)
    finally:
        client.close()


def _heal_decisions(cfg: EngineConfig) -> None:
    """Answer the open decisions a diagnosing model may answer (bt_durable.healing, D-167), then hand what healing left
    for a person, and runs that are stuck or in error, to the Solucionador (bt_durable.solver, REQ-031)."""
    import bt_core

    from . import healing, solver
    if not healing.enabled():
        return
    global _healing_client
    if _healing_client is None:                     # one client for the engine's life: a pass runs every 30 s
        from .client import Client
        _healing_client = Client(cfg.system_database_url)
    client = _PassStatus(_healing_client)           # both rungs read each run's status once per pass
    left: list[dict] = []
    try:
        for said in healing.heal(Path(bt_core.ROOT), client, escalate=left.append):
            LOG.info("healing: %s", said)
    finally:
        if solver.enabled():
            for said in solver.Solver(Path(bt_core.ROOT), client, state_dir=cfg.state_dir).run_pass(left):
                LOG.info("solver: %s", said)


class _PassStatus:
    """The client, with `status(run)` read once per maintenance pass (it reads every task workflow of the run)."""

    def __init__(self, client):
        self._client, self._status = client, {}

    def status(self, run):
        if run.run_id not in self._status:
            self._status[run.run_id] = self._client.status(run)
        return self._status[run.run_id]

    def __getattr__(self, name):
        return getattr(self._client, name)


_healing_client = None


__all__ = ["Path", "reap_once", "serve", "wire"]
