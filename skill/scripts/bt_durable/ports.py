"""The ports the durable runtime calls (REQ-030 M2). Structural protocols: any object with these methods fits.

Every port method is called from inside exactly one DBOS step, so it may have external effects, but it must be
idempotent for the identifiers it receives: a step that crashed after its effect and before its checkpoint runs
again with the same `AttemptRef`, and must adopt what the first run did instead of doing it twice.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from bt_contracts.execution import (
    AgentReport,
    AttemptRef,
    Prepared,
    ProcessRecord,
    Route,
    RouteDecision,
    RunRef,
    Snapshot,
    VerifyOutcome,
)

from .legacy import Plan, TaskSpec


@runtime_checkable
class PlanSource(Protocol):
    def load(self, run: RunRef) -> Plan: ...                     # validated and bound to run.plan_sha256
    def text(self, run: RunRef) -> str: ...                      # the exact approved bytes (decoded), for replay


@runtime_checkable
class Router(Protocol):
    def decide(self, run: RunRef, task: TaskSpec, *, exclude: tuple[str, ...], now: float) -> RouteDecision: ...
    def alternatives(self, run: RunRef, task: TaskSpec, *, exclude: tuple[str, ...]) -> int: ...


@runtime_checkable
class Preparer(Protocol):
    """Worktree, brief, prompt and launch material. Idempotent per attempt key (an existing worktree is reused)."""
    def prepare(self, attempt: AttemptRef, task: TaskSpec, route: Route, *, base_ref: str, note: str,
                limits: dict) -> Prepared: ...


@runtime_checkable
class Runtime(Protocol):
    """The Linux process runtime. `launch` adopts an existing process for the same key instead of starting one."""
    def launch(self, attempt: AttemptRef, prepared: Prepared, limits: dict) -> ProcessRecord: ...
    def observe(self, attempt: AttemptRef) -> ProcessRecord: ...
    def terminate(self, attempt: AttemptRef) -> ProcessRecord: ...   # raises when termination cannot be proven
    def release(self, attempt: AttemptRef) -> None: ...
    def owned(self, prefix: str) -> list[str]: ...                   # attempt keys with something still known


@runtime_checkable
class Reader(Protocol):
    def read(self, attempt: AttemptRef, route: Route, process: ProcessRecord) -> AgentReport: ...


@runtime_checkable
class Capturer(Protocol):
    def capture(self, attempt: AttemptRef, prepared: Prepared, task: TaskSpec) -> Snapshot: ...


@runtime_checkable
class Verifier(Protocol):
    """Independent verification of a snapshot. Idempotent per (attempt, profile): a repeat returns the stored verdict."""
    def verify(self, attempt: AttemptRef, task: TaskSpec, prepared: Prepared, snapshot: Snapshot, *,
               profile: str) -> VerifyOutcome: ...


@runtime_checkable
class Integrator(Protocol):
    """One integration line per run and repository (plus one per 1.3.0 subplan). `integrate` is compare-and-swap: it
    never loses accepted work. `home`/`lines` come from `control.subplans` ("" / () for plans without subplans)."""
    def base_ref(self, run: RunRef, task: TaskSpec, *, home: str = "", lines: tuple[str, ...] = ()) -> str: ...
    def integrate(self, run: RunRef, task: TaskSpec, snapshot: Snapshot, *, lines: tuple[str, ...] = (),
                  home: str = "") -> tuple[str | None, str, str, dict[str, str]]: ...
    # (ref, conflict, run-line note, other subplan lines left out): a subplan member counts once its own subplan line
    # takes it (legacy SubplanLineRouter); a conflict on the run line or on another subplan's line is reported, left to
    # the composition gates
    def sync(self, run: RunRef, role: str, items: dict[str, list[tuple[str, str]]]) -> dict[str, dict]: ...


@runtime_checkable
class Auditor(Protocol):
    """Judges an accepted audit's findings ledger and compiles the coordinated repairs of its blocking findings."""
    def judge(self, run: RunRef, plan: Plan, task: TaskSpec, snapshot_sha: str, *, base_sha: str = "") -> dict: ...


@runtime_checkable
class Composer(Protocol):
    """Composition gates: subplan versions and the gate's candidate (idempotent per member versions)."""
    def compose(self, run: RunRef, gate_id: str, evidence: dict[str, list[dict]]) -> dict: ...


@runtime_checkable
class Telemetry(Protocol):
    def emit(self, event: str, **fields: object) -> None: ...      # structured, secret-free


@dataclass(frozen=True)
class Ports:
    plans: PlanSource
    router: Router
    preparer: Preparer
    runtime: Runtime
    reader: Reader
    capturer: Capturer
    verifier: Verifier
    integrator: Integrator
    telemetry: Telemetry
    composer: Composer | None = None            # plan 1.3.0 composition gates
    auditor: Auditor | None = None              # milestone audits: findings ledger -> coordinated remediation
