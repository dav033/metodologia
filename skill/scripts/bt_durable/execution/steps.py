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

from ..control import frontier, subplans
from . import engine

_PLANS: dict[tuple[str, str], object] = {}


class StepFailure(RuntimeError):
    """What a step raises: a plain, picklable error carrying the port's code and detail. DBOS stores step errors
    (pickled) and replays them; a port's own exception class may not survive that round trip."""


def _port(call):
    try:
        return call()
    except StepFailure:
        raise
    except Exception as error:  # noqa: BLE001 - re-raised as a picklable failure with the same code and detail
        code = getattr(error, "code", type(error).__name__)
        raise StepFailure(f"{code}: {getattr(error, 'detail', str(error))}"[:2000]) from None


def plan(run: RunRef):
    """The validated Plan for a run: rebuilt from the checkpointed approved text, cached per process."""
    key = (run.run_id, run.plan_sha256)
    if key not in _PLANS:
        from ..legacy import load_plan
        _PLANS[key] = load_plan(plan_text(run.model_dump(mode="json")), approved_sha256=run.plan_sha256,
                                plan_id=run.plan_id, revision=run.revision)
    return _PLANS[key]


@DBOS.step(name="bt.plan_text")
def plan_text(run: dict) -> str:
    return _port(lambda: engine.ports().plans.text(RunRef.model_validate(run)))


@DBOS.step(name="bt.now")
def now() -> float:
    return time.time()


@DBOS.step(name="bt.route")
def route(run: dict, task_id: str, exclude: list[str], at: float) -> dict:
    ref = RunRef.model_validate(run)
    task = frontier.task(plan(ref), task_id)
    return _port(lambda: engine.ports().router.decide(ref, task, exclude=tuple(exclude), now=at)).model_dump(mode="json")


@DBOS.step(name="bt.alternatives")
def alternatives(run: dict, task_id: str, exclude: list[str]) -> int:
    ref = RunRef.model_validate(run)
    return _port(lambda: engine.ports().router.alternatives(ref, frontier.task(plan(ref), task_id),
                                                            exclude=tuple(exclude)))


@DBOS.step(name="bt.base_ref", retries_allowed=True, max_attempts=3, interval_seconds=2)
def base_ref(run: dict, task_id: str) -> str:
    ref = RunRef.model_validate(run)
    home = subplans.home(plan(ref), task_id)          # "" for plans without subplans: the run line, as before
    return _port(lambda: engine.ports().integrator.base_ref(ref, frontier.task(plan(ref), task_id), home=home))


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
    return _port(lambda: engine.ports().runtime.launch(AttemptRef.model_validate(attempt),
                                                       Prepared.model_validate(prepared), limits)).model_dump(mode="json")


@DBOS.step(name="bt.observe", retries_allowed=True, max_attempts=5, interval_seconds=1)
def observe(attempt: dict) -> dict:
    return _port(lambda: engine.ports().runtime.observe(AttemptRef.model_validate(attempt))).model_dump(mode="json")


@DBOS.step(name="bt.terminate", retries_allowed=True, max_attempts=3, interval_seconds=2)
def terminate(attempt: dict) -> dict:
    return _port(lambda: engine.ports().runtime.terminate(AttemptRef.model_validate(attempt))).model_dump(mode="json")


@DBOS.step(name="bt.release", retries_allowed=True, max_attempts=3, interval_seconds=1)
def release(attempt: dict) -> None:
    _port(lambda: engine.ports().runtime.release(AttemptRef.model_validate(attempt)))


@DBOS.step(name="bt.read")
def read(attempt: dict, route_data: dict, process: dict) -> dict:
    return _port(lambda: engine.ports().reader.read(AttemptRef.model_validate(attempt), Route.model_validate(route_data),
                                                    ProcessRecord.model_validate(process))).model_dump(mode="json")


@DBOS.step(name="bt.capture", retries_allowed=True, max_attempts=3, interval_seconds=2)
def capture(attempt: dict, prepared: dict) -> dict:
    ref = AttemptRef.model_validate(attempt)
    task = frontier.task(plan(ref.run), ref.task_id)
    return _port(lambda: engine.ports().capturer.capture(ref, Prepared.model_validate(prepared), task)).model_dump(mode="json")


@DBOS.step(name="bt.verify")
def verify(attempt: dict, prepared: dict, snapshot: dict, profile: str) -> dict:
    ref = AttemptRef.model_validate(attempt)
    task = frontier.task(plan(ref.run), ref.task_id)
    return _port(lambda: engine.ports().verifier.verify(ref, task, Prepared.model_validate(prepared),
                                                        Snapshot.model_validate(snapshot),
                                                        profile=profile)).model_dump(mode="json")


@DBOS.step(name="bt.integrate", retries_allowed=True, max_attempts=3, interval_seconds=2)
def integrate(run: dict, task_id: str, snapshot: dict) -> dict:
    ref = RunRef.model_validate(run)
    lines = subplans.lines_of(plan(ref), task_id)
    integrated, conflict = _port(lambda: engine.ports().integrator.integrate(ref, frontier.task(plan(ref), task_id),
                                                                             Snapshot.model_validate(snapshot),
                                                                             lines=lines))
    return {"ref": integrated, "conflict": conflict}


@DBOS.step(name="bt.sync_lines", retries_allowed=True, max_attempts=3, interval_seconds=2)
def sync_lines(run: dict, role: str, items: dict) -> dict:
    """Seed/catch up the subplan lines of a 1.3.0 run from its accepted snapshots (idempotent)."""
    ref = RunRef.model_validate(run)
    return _port(lambda: engine.ports().integrator.sync(ref, role, {k: [tuple(e) for e in v] for k, v in items.items()}))


@DBOS.step(name="bt.compose", retries_allowed=True, max_attempts=3, interval_seconds=2)
def compose(run: dict, gate_id: str, evidence: dict) -> dict:
    """Publish the gate's member subplan versions and build its candidate (idempotent per member versions)."""
    ref = RunRef.model_validate(run)
    composer = engine.ports().composer
    if composer is None:
        return {"state": "rejected", "reason": "GATE_UNSUPPORTED: no composition port is wired"}
    return _port(lambda: composer.compose(ref, gate_id, evidence))


@DBOS.step(name="bt.emit")
def emit(event: str, fields: dict) -> None:
    engine.ports().telemetry.emit(event, **fields)


def emit_decision(attempt: AttemptRef, decision: RecoveryDecision) -> None:
    emit("recovery_decision", {"run_id": attempt.run.run_id, "task_id": attempt.task_id,
                               "attempt_key": attempt.attempt_key, "action": decision.action.value,
                               "reason": decision.reason, "limit_hit": decision.limit_hit,
                               "failure_class": decision.failure.failure_class.value if decision.failure else None,
                               "code": decision.failure.code if decision.failure else None})
