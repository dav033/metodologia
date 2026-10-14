"""A deterministic 'world' around the core: scripted executor outcomes and a validator, no provider, no network.

Used by the CLI (`simulate`) and by the end-to-end tests. Each started attempt finishes (or fails) as scripted, each
verification request is accepted (or rejected) as scripted, until the run reaches a state that needs no outside help.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from .config import Config
from .contracts import Event, Verdict
from .plan import Plan
from .repository import StateRepository
from .scheduler import Ports, SchedulerCore
from .simulators import FakeExecutor, FakeVerifier, ManualClock, ScriptedRecovery
from .states import EventKind, RunStatus
from .views import Snapshot

SAFETY_LIMIT = 10_000


@dataclass
class Script:
    fail: Mapping[str, int] = field(default_factory=dict)    # task id -> how many attempts fail to execute
    reject: Mapping[str, int] = field(default_factory=dict)  # task id -> how many verdicts reject the work


def simulate(plan: Plan, repository: StateRepository, config: Config | None = None, script: Script | None = None,
             *, recovery: ScriptedRecovery | None = None, clock: ManualClock | None = None) -> tuple[Snapshot, SchedulerCore]:
    script, clock = script or Script(), clock or ManualClock()
    executor, verifier = FakeExecutor(), FakeVerifier()
    core = SchedulerCore(plan, repository, ports=Ports(execution=executor, verification=verifier, recovery=recovery),
                         config=config, clock=clock)
    core.start()
    failed, rejected, done_exec, done_verify = dict(script.fail), dict(script.reject), set(), set()
    for _ in range(SAFETY_LIMIT):
        core.step()
        moved = False
        for attempt_id, order in list(executor.started.items()):
            if attempt_id in done_exec:
                continue
            done_exec.add(attempt_id)
            moved = True
            bad = failed.get(order.task_id, 0) > 0
            if bad:
                failed[order.task_id] -= 1
            kind = EventKind.EXECUTION_FAILED if bad else EventKind.EXECUTION_FINISHED
            core.ingest(Event(f"sim-ev-{attempt_id}", plan.plan_id, plan.revision, order.task_id, attempt_id, "simulated-executor",
                              kind.value, "", {"reason": "scripted failure"} if bad else {}, order.token))
        for attempt_id, order in list(verifier.requests.items()):
            if attempt_id in done_verify:
                continue
            done_verify.add(attempt_id)
            moved = True
            bad = rejected.get(order.task_id, 0) > 0
            if bad:
                rejected[order.task_id] -= 1
            core.submit_verdict(Verdict(f"sim-vd-{attempt_id}", plan.plan_id, plan.revision, order.task_id, attempt_id,
                                        not bad, "simulated-validator", "scripted rejection" if bad else "scripted acceptance",
                                        order.token))
        snap = core.snapshot()
        if not moved and snap.status in (RunStatus.COMPLETED.value, RunStatus.CANCELLED.value, RunStatus.BLOCKED.value,
                                         RunStatus.PAUSED.value) and snap.counts.get("live_attempts", 0) == 0:
            return snap, core
        clock.advance(1.0)
    raise RuntimeError("simulation did not settle")
