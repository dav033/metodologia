"""DBOS steps: the only places where the durable runtime touches the outside world.

Each step takes and returns JSON values (model dumps), so checkpoints stay readable and do not depend on pickled
class paths. Each one calls exactly one idempotent port method; DBOS retries are enabled only where the port is
safe to repeat and the failure is plausibly transient (git index locks, systemd bus hiccups).
"""
from __future__ import annotations

import time

from bt_contracts.execution import (
    AttemptRef,
    Prepared,
    ProcessRecord,
    Route,
    RunRef,
    Snapshot,
)
from bt_contracts.failure import RecoveryDecision
from dbos import DBOS

from ..control import frontier
from . import engine

_PLANS: dict[tuple[str, str], object] = {}


def plan(run: RunRef):
    """The validated Plan for a run: rebuilt from the checkpointed approved text, cached per process."""
    key = (run.run_id, run.plan_sha256)
    if key not in _PLANS:
        from bt_scheduler_core.plan import load_plan
        _PLANS[key] = load_plan(plan_text(run.model_dump(mode="json")), approved_sha256=run.plan_sha256,
                                plan_id=run.plan_id, revision=run.revision)
    return _PLANS[key]


@DBOS.step(name="bt.plan_text")
def plan_text(run: dict) -> str:
    return engine.ports().plans.text(RunRef.model_validate(run))


@DBOS.step(name="bt.now")
def now() -> float:
    return time.time()


@DBOS.step(name="bt.route")
def route(run: dict, task_id: str, exclude: list[str], at: float) -> dict:
    ref = RunRef.model_validate(run)
    task = frontier.task(plan(ref), task_id)
    return engine.ports().router.decide(ref, task, exclude=tuple(exclude), now=at).model_dump(mode="json")


@DBOS.step(name="bt.alternatives")
def alternatives(run: dict, task_id: str, exclude: list[str]) -> int:
    ref = RunRef.model_validate(run)
    return engine.ports().router.alternatives(ref, frontier.task(plan(ref), task_id), exclude=tuple(exclude))


@DBOS.step(name="bt.base_ref", retries_allowed=True, max_attempts=3, interval_seconds=2)
def base_ref(run: dict, task_id: str) -> str:
    ref = RunRef.model_validate(run)
    return engine.ports().integrator.base_ref(ref, frontier.task(plan(ref), task_id))


@DBOS.step(name="bt.prepare")
def prepare(attempt: dict, route_data: dict, base: str, note: str, limits: dict) -> dict:
    """{"prepared": ...} or {"start_error": "CODE: detail"} — a refused start is a fact, not an exception."""
    ref = AttemptRef.model_validate(attempt)
    task = frontier.task(plan(ref.run), ref.task_id)
    try:
        prepared = engine.ports().preparer.prepare(ref, task, Route.model_validate(route_data), base_ref=base,
                                                   note=note, limits=limits)
    except Exception as error:  # noqa: BLE001 - every refusal is classified downstream from its code
        code = getattr(error, "code", type(error).__name__)
        return {"start_error": f"{code}: {getattr(error, 'detail', str(error))}"[:2000]}
    return {"prepared": prepared.model_dump(mode="json")}


@DBOS.step(name="bt.launch", retries_allowed=True, max_attempts=3, interval_seconds=2)
def launch(attempt: dict, prepared: dict, limits: dict) -> dict:
    return engine.ports().runtime.launch(AttemptRef.model_validate(attempt), Prepared.model_validate(prepared),
                                         limits).model_dump(mode="json")


@DBOS.step(name="bt.observe", retries_allowed=True, max_attempts=5, interval_seconds=1)
def observe(attempt: dict) -> dict:
    return engine.ports().runtime.observe(AttemptRef.model_validate(attempt)).model_dump(mode="json")


@DBOS.step(name="bt.terminate", retries_allowed=True, max_attempts=3, interval_seconds=2)
def terminate(attempt: dict) -> dict:
    return engine.ports().runtime.terminate(AttemptRef.model_validate(attempt)).model_dump(mode="json")


@DBOS.step(name="bt.release", retries_allowed=True, max_attempts=3, interval_seconds=1)
def release(attempt: dict) -> None:
    engine.ports().runtime.release(AttemptRef.model_validate(attempt))


@DBOS.step(name="bt.read")
def read(attempt: dict, route_data: dict, process: dict) -> dict:
    return engine.ports().reader.read(AttemptRef.model_validate(attempt), Route.model_validate(route_data),
                                      ProcessRecord.model_validate(process)).model_dump(mode="json")


@DBOS.step(name="bt.capture", retries_allowed=True, max_attempts=3, interval_seconds=2)
def capture(attempt: dict, prepared: dict) -> dict:
    ref = AttemptRef.model_validate(attempt)
    task = frontier.task(plan(ref.run), ref.task_id)
    return engine.ports().capturer.capture(ref, Prepared.model_validate(prepared), task).model_dump(mode="json")


@DBOS.step(name="bt.verify")
def verify(attempt: dict, prepared: dict, snapshot: dict, profile: str) -> dict:
    ref = AttemptRef.model_validate(attempt)
    task = frontier.task(plan(ref.run), ref.task_id)
    return engine.ports().verifier.verify(ref, task, Prepared.model_validate(prepared),
                                          Snapshot.model_validate(snapshot), profile=profile).model_dump(mode="json")


@DBOS.step(name="bt.integrate", retries_allowed=True, max_attempts=3, interval_seconds=2)
def integrate(run: dict, task_id: str, snapshot: dict) -> dict:
    ref = RunRef.model_validate(run)
    integrated, conflict = engine.ports().integrator.integrate(ref, frontier.task(plan(ref), task_id),
                                                               Snapshot.model_validate(snapshot))
    return {"ref": integrated, "conflict": conflict}


@DBOS.step(name="bt.emit")
def emit(event: str, fields: dict) -> None:
    engine.ports().telemetry.emit(event, **fields)


def emit_decision(attempt: AttemptRef, decision: RecoveryDecision) -> None:
    emit("recovery_decision", {"run_id": attempt.run.run_id, "task_id": attempt.task_id,
                               "attempt_key": attempt.attempt_key, "action": decision.action.value,
                               "reason": decision.reason, "limit_hit": decision.limit_hit,
                               "failure_class": decision.failure.failure_class.value if decision.failure else None,
                               "code": decision.failure.code if decision.failure else None})
