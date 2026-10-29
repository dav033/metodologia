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

from .adapters.integration import GitLineIntegrator
from .adapters.m3 import M3Attempts
from .adapters.m6 import M6Verifier
from .adapters.plans import FilePlans
from .adapters.routes import StaticRouter
from .adapters.runtime import SupervisorRuntime
from .adapters.telemetry import JsonlTelemetry
from .execution import engine, steps
from .ports import Ports
from .settings import EngineConfig

LOG = logging.getLogger("bt_durable.service")
TERMINAL = frozenset({"SUCCESS", "ERROR", "CANCELLED", "MAX_RECOVERY_ATTEMPTS_EXCEEDED"})


def wire(cfg: EngineConfig, *, repositories_for: Callable[[str], object], driver_for: Callable[[str], object],
         routes: list[Route], verifier: M6Verifier | None = None, runtime=None, capacity=None,
         briefs_for=None) -> Ports:
    cfg.state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    cfg.state_dir.chmod(0o700)                             # M6 and the supervisor refuse a shared directory
    plans = FilePlans()
    attempts = M3Attempts(root=cfg.state_dir / "attempts-root", repositories_for=repositories_for,
                          plan_for=lambda attempt: steps.plan(attempt.run), driver_for=driver_for,
                          briefs_for=briefs_for)

    integrator = _ProjectIntegrator(repositories_for)
    return Ports(plans=plans, router=StaticRouter(routes, capacity), preparer=attempts,
                 runtime=runtime or SupervisorRuntime(cfg.state_dir / "supervisor"), reader=attempts,
                 capturer=attempts, verifier=verifier or operator_verifier(cfg.state_dir / "m6-quality.sqlite3"),
                 integrator=integrator, telemetry=JsonlTelemetry(cfg.state_dir / "telemetry.jsonl"))


def requirement_dir(run) -> Path:
    return Path(run.plan_path).parent.parent              # <req dir>/plan-revisions/PLAN.rN.json


def operator_verifier(store_path: Path) -> M6Verifier:
    """M6 with the operator's per-run policy and authorization callbacks (shared with the legacy owner)."""
    from bt_scheduler_executor_wiring import operator_quality_policy
    from bt_scheduler_verification_authority import owner_verification_authority
    return M6Verifier(store_path=store_path,
                      policy_for=lambda run: operator_quality_policy(run.project, requirement_dir(run)),
                      authority_for=lambda run: owner_verification_authority(requirement_dir(run), run.project))


class _ProjectIntegrator:
    """Integration lines are per project; the run tells which project's repositories to use."""

    def __init__(self, repositories_for: Callable[[str], object]):
        self.repositories_for = repositories_for
        self._lines: dict[str, GitLineIntegrator] = {}

    def _for(self, project: str) -> GitLineIntegrator:
        if project not in self._lines:
            self._lines[project] = GitLineIntegrator(self.repositories_for(project))
        return self._lines[project]

    def base_ref(self, run, task):
        return self._for(run.project).base_ref(run, task)

    def integrate(self, run, task, snapshot):
        return self._for(run.project).integrate(run, task, snapshot)


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
    finally:
        engine.stop()


__all__ = ["Path", "reap_once", "serve", "wire"]
