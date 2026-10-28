"""Durable workflows: run → task → (agent | verification | integration), each on the queue of its load class.

Workflow bodies are deterministic: time comes from the `bt.now` step, every external effect is a step, and every
decision is a pure control-plane function of checkpointed step results. Workflow IDs are derived from the run,
task and attempt identity, so starting or enqueueing the same work twice returns the existing workflow.

Messages (DBOS.send/recv, durable):
- topic `run` of the run workflow: task_done, retry_task, pause, resume (owner commands carry a request id);
- topic `owner:<task>` of a task workflow: the owner's answer to the open decision (stale answers are refused).
Events (DBOS.set_event): `state`, `decision` on task workflows; `summary` on the run workflow (the projection).
"""
from __future__ import annotations

from bt_contracts.execution import (
    AgentReport,
    AttemptOutcome,
    AttemptRef,
    AttemptStatus,
    Prepared,
    ProcessRecord,
    Route,
    RouteDecision,
    RunRef,
    Snapshot,
    TaskOutcome,
    TaskStatus,
    VerifyOutcome,
)
from bt_contracts.failure import FailureReport, RecoveryAction, RecoveryDecision
from bt_contracts.owner import OwnerAnswer, RunCommand
from dbos import DBOS, SetWorkflowID

from ..control import classify, frontier, policy
from ..settings import Settings
from . import engine, steps

TOPIC_RUN = "run"
STANDARD, RELAXED = "standard", "relaxed"


def run_workflow_id(run: RunRef) -> str:
    return f"bt:{run.run_id}"


def task_workflow_id(run: RunRef, task_id: str, round_no: int) -> str:
    return f"bt:{run.run_id}:{task_id}:k{round_no}"


# ---------------------------------------------------------------------------------------------------------- run
@DBOS.workflow(name="bt.run")
def run_workflow(run_data: dict, settings_data: dict, inherited: dict) -> dict:
    """Start every ready task, wait for news, repeat; ends when nothing is left to run. `inherited` maps task ids
    the migration bridge proved complete to their provenance."""
    run, settings = RunRef.model_validate(run_data), Settings.model_validate(settings_data)
    plan = steps.plan(run)
    states: dict[str, str] = {task_id: "inherited" for task_id in inherited}
    rounds: dict[str, int] = {}
    paused = False
    seen_commands: set[str] = set()
    results: dict[str, dict] = {}
    DBOS.set_event("summary", _summary(run, states, results, paused))
    while True:
        front = frontier.compute(plan, states, max_parallel=settings.max_parallel)
        if not paused:
            for task_id in front.ready:
                rounds[task_id] = rounds.get(task_id, 0) + 1
                _start_task(run, task_id, rounds[task_id], settings, note="")
                states[task_id] = "running"
        DBOS.set_event("summary", _summary(run, states, results, paused))
        if front.finished:
            break
        if not paused and not any(s == "running" for s in states.values()) and not front.ready:
            break                                   # only blocked work and its dependents remain
        message = DBOS.recv(TOPIC_RUN, timeout_seconds=settings.run_poll_seconds)
        if message is None:
            continue
        kind = message.get("kind") if isinstance(message, dict) else None
        if kind == "task_done":
            outcome = TaskOutcome.model_validate(message["outcome"])
            states[outcome.task_id] = outcome.status.value
            results[outcome.task_id] = outcome.model_dump(mode="json")
            continue
        try:
            command = RunCommand.model_validate(message)
        except ValueError:
            steps.emit("command_refused", {"run_id": run.run_id, "reason": "invalid run command"})
            continue
        if command.request_id in seen_commands:
            continue                                # an idempotent repeat of a command already applied
        seen_commands.add(command.request_id)
        if command.kind == "pause":
            paused = True
        elif command.kind == "resume":
            paused = False
        elif command.kind == "retry_task" and command.task_id and states.get(command.task_id) in frontier.STOPPED:
            rounds[command.task_id] = rounds.get(command.task_id, 1) + 1
            _start_task(run, command.task_id, rounds[command.task_id], settings, note=command.note)
            states[command.task_id] = "running"
        else:
            steps.emit("command_refused", {"run_id": run.run_id, "request_id": command.request_id,
                                           "reason": f"{command.kind} does not apply to the current state"})
    summary = _summary(run, states, results, paused, final=True)
    DBOS.set_event("summary", summary)
    steps.emit("run_settled", {"run_id": run.run_id, "status": summary["status"]})
    return summary


def _start_task(run: RunRef, task_id: str, round_no: int, settings: Settings, note: str) -> None:
    with SetWorkflowID(task_workflow_id(run, task_id, round_no)):
        DBOS.start_workflow(task_workflow, run.model_dump(mode="json"), task_id, round_no,
                            settings.model_dump(mode="json"), note, DBOS.workflow_id)


def _summary(run: RunRef, states: dict, results: dict, paused: bool, final: bool = False) -> dict:
    values = set(states.values())
    if final:
        status = "completed" if values <= frontier.DONE and states else ("blocked" if values & frontier.STOPPED else "settled")
    else:
        status = "paused" if paused else "running"
    return {"run_id": run.run_id, "status": status, "tasks": dict(states), "results": results}


# --------------------------------------------------------------------------------------------------------- task
@DBOS.workflow(name="bt.task")
def task_workflow(run_data: dict, task_id: str, round_no: int, settings_data: dict, note: str,
                  parent_id: str) -> dict:
    run, settings = RunRef.model_validate(run_data), Settings.model_validate(settings_data)
    outcome = _run_task(run, task_id, round_no, settings, note)
    DBOS.send(parent_id, {"kind": "task_done", "outcome": outcome.model_dump(mode="json")}, TOPIC_RUN,
              idempotency_key=f"{DBOS.workflow_id}:done")
    return outcome.model_dump(mode="json")


def _run_task(run: RunRef, task_id: str, round_no: int, settings: Settings, note: str) -> TaskOutcome:
    budget = settings.budget
    started = steps.now()
    outcomes: list[AttemptOutcome] = []
    exclude: list[str] = []
    limits = dict(settings.agent_limits)
    waits = repairs = route_changes = 0
    remediated = False
    number = (round_no - 1) * 100
    base_override = ""
    decisions = 0
    while True:
        DBOS.set_event("state", {"task_id": task_id, "state": "routing", "attempts": len(outcomes)})
        at = steps.now()
        choice = RouteDecision.model_validate(steps.route(run.model_dump(mode="json"), task_id, exclude, at))
        if choice.kind == "wait":
            waits += 1
            if waits <= budget.max_waits:
                DBOS.set_event("state", {"task_id": task_id, "state": "waiting_quota", "until": choice.not_before})
                DBOS.sleep(max(1.0, (choice.not_before or at) - at))
                continue
        if choice.kind != "run":
            decisions += 1
            answer = _ask_owner(run, task_id, decisions, RecoveryDecision(
                action=RecoveryAction.ESCALATE, reason=f"no allowed route: {choice.reason or choice.kind}"), settings)
            if answer.action == "stop":
                return _finish(run, task_id, TaskStatus.BLOCKED, outcomes, None, None)
            note, waits = answer.note or note, 0
            continue
        number += 1
        attempt = AttemptRef(run=run, task_id=task_id, number=number, workflow_id=DBOS.workflow_id)
        base = base_override or steps.base_ref(run.model_dump(mode="json"), task_id)
        DBOS.set_event("state", {"task_id": task_id, "state": "running", "attempt": attempt.attempt_key})
        agent = _enqueue(engine.AGENTS, f"bt:{attempt.attempt_key}:agent", agent_workflow,
                         attempt.model_dump(mode="json"), choice.route.model_dump(mode="json"), base, note, limits,
                         settings.poll_seconds)
        verify = None
        profile = STANDARD
        while True:                                       # re-verification of the same snapshot needs no new agent run
            outcome = _evaluate(attempt, choice.route, agent, verify, profile)
            if outcome.status == AttemptStatus.ACCEPTED or outcome.failure is None:
                outcomes.append(outcome)
                return _finish(run, task_id, TaskStatus.COMPLETED, outcomes, outcome, None)
            now = steps.now()
            used = policy.spent([*outcomes, outcome], waits=waits, repairs=repairs, route_changes=route_changes,
                                started_at=started, now=now)
            others = steps.alternatives(run.model_dump(mode="json"), task_id, [*exclude, _route_key(choice.route)])
            decision = policy.decide(outcome.failure, used, budget, now=now, other_route=others > 0,
                                     reset_epoch=outcome.agent.reset_epoch if outcome.agent else None,
                                     remediated=remediated)
            steps.emit_decision(attempt, decision)
            if decision.action == RecoveryAction.REPAIR_ENVIRONMENT and outcome.failure.code in policy.REVERIFY \
                    and agent.get("snapshot"):
                repairs += 1
                profile = RELAXED
                verify = _enqueue(engine.VERIFY, f"bt:{attempt.attempt_key}:verify:{profile}", verify_workflow,
                                  attempt.model_dump(mode="json"), agent["prepared"], agent["snapshot"], profile)
                continue
            outcomes.append(outcome)
            break
        # a retry continues from the attempt's own snapshot (its partial work is kept), never from scratch
        continued = outcome.snapshot.snapshot_sha if outcome.snapshot and outcome.snapshot.snapshot_sha else ""
        if decision.action in (RecoveryAction.RETRY, RecoveryAction.REMEDIATE):
            note = decision.note_for_agent if decision.action == RecoveryAction.RETRY else _remediation_note(outcomes)
            remediated = remediated or decision.action == RecoveryAction.REMEDIATE
            base_override = continued
        elif decision.action == RecoveryAction.RETRY_OTHER_ROUTE:
            exclude.append(_route_key(choice.route))
            route_changes += 1
            base_override = continued
        elif decision.action == RecoveryAction.WAIT:
            waits += 1
            DBOS.set_event("state", {"task_id": task_id, "state": "recovering", "until": decision.not_before})
            DBOS.sleep(max(1.0, (decision.not_before or now) - now))
        elif decision.action == RecoveryAction.REPAIR_ENVIRONMENT:      # AGENT_OOM: a bounded memory raise
            repairs += 1
            limits["memory_max_bytes"] = min(int(limits.get("memory_max_bytes") or 0) * 2 or settings.max_agent_memory_bytes,
                                             settings.max_agent_memory_bytes)
        elif decision.action == RecoveryAction.RECONCILE_INTEGRATION:
            base_override = ""                                           # next base is the current line tip
            note = decision.note_for_agent
        else:                                                            # escalate / stop: the owner decides
            decisions += 1
            answer = _ask_owner(run, task_id, decisions, decision, settings)
            if answer.action == "stop":
                return _finish(run, task_id, TaskStatus.BLOCKED, outcomes, outcome, decision)
            note = answer.note or decision.note_for_agent
            if answer.action == "retry_other_route":
                exclude.append(_route_key(choice.route))
            budget = budget.model_copy(update={"max_attempts": budget.max_attempts + (answer.extra_attempts or 1)})
            remediated = False


def _evaluate(attempt: AttemptRef, route: Route, agent: dict, verify: dict | None, profile: str) -> AttemptOutcome:
    """Verify (if there is something to verify), integrate a pass, and classify whatever went wrong."""
    if agent.get("internal_error"):
        failure = classify.classify(classify.AttemptFacts(internal_error=agent["internal_error"]))
        return AttemptOutcome(attempt=attempt, status=AttemptStatus.EXECUTION_FAILED, route=route, failure=failure)
    process = ProcessRecord.model_validate(agent["process"]) if agent.get("process") else None
    report = AgentReport.model_validate(agent["agent"]) if agent.get("agent") else None
    snapshot = Snapshot.model_validate(agent["snapshot"]) if agent.get("snapshot") else None
    if verify is None and snapshot is not None and snapshot.snapshot_sha:
        verify = _enqueue(engine.VERIFY, f"bt:{attempt.attempt_key}:verify:{profile}", verify_workflow,
                          attempt.model_dump(mode="json"), agent["prepared"], agent["snapshot"], profile)
    if verify and verify.get("internal_error"):
        failure = classify.classify(classify.AttemptFacts(internal_error=verify["internal_error"]))
        return AttemptOutcome(attempt=attempt, status=AttemptStatus.NEEDS_REVIEW, route=route, process=process,
                              agent=report, snapshot=snapshot, failure=failure)
    verdict = VerifyOutcome.model_validate(verify) if verify else None
    facts = classify.AttemptFacts(start_error=agent.get("start_error", ""), process=process, agent=report,
                                  verify=verdict, failing_output=verdict.digest if verdict else "",
                                  declared_requires=tuple(agent.get("requires", ())),
                                  known_paths=tuple(agent.get("paths", ())))
    failure: FailureReport | None = classify.classify(facts)
    integrated = None
    if failure is None and snapshot is not None:
        merged = _enqueue(engine.INTEGRATE, f"bt:{attempt.attempt_key}:integrate", integrate_workflow,
                          attempt.run.model_dump(mode="json"), attempt.task_id, agent["snapshot"])
        if merged.get("internal_error"):
            failure = classify.classify(classify.AttemptFacts(internal_error=merged["internal_error"]))
        elif merged.get("conflict"):
            failure = classify.classify(classify.AttemptFacts(process=process, agent=report, verify=verdict,
                                                              integration_conflict=merged["conflict"]))
        else:
            integrated = merged.get("ref")
    if failure is None and snapshot is None:
        failure = classify.classify(classify.AttemptFacts(process=process, agent=report))
    status = (AttemptStatus.ACCEPTED if failure is None else
              AttemptStatus.REJECTED if verdict and verdict.status.value == "FAIL" else
              AttemptStatus.NEEDS_REVIEW if verdict else AttemptStatus.EXECUTION_FAILED)
    return AttemptOutcome(attempt=attempt, status=status, route=route, process=process, agent=report,
                          snapshot=snapshot, verify=verdict, failure=failure, integrated_ref=integrated)


def _enqueue(queue: str, workflow_id: str, func, *args) -> dict:
    """Run a child workflow on its queue and wait for it. A child that failed is a FACT for the classifier
    (`internal_error`), never an exception that would leave the task, and with it the run, without an outcome."""
    with SetWorkflowID(workflow_id):
        handle = DBOS.enqueue_workflow(queue, func, *args)
    try:
        return handle.get_result()
    except Exception as error:  # noqa: BLE001 - classified as an internal failure with its message as evidence
        return {"internal_error": f"{type(error).__name__}: {error}"[:2000]}


def _route_key(route: Route) -> str:
    return f"{route.provider}:{route.profile}:{route.model}"


def _remediation_note(outcomes: list[AttemptOutcome]) -> str:
    """One coordinated repair: every distinct failure of the task so far, with the checks that reproduce it."""
    seen: dict[str, AttemptOutcome] = {}
    for outcome in outcomes:
        if outcome.failure is not None:
            seen.setdefault(outcome.failure.signature, outcome)
    parts = [("REMEDIATION. The same failure repeated. Fix the cause of EVERY failure below in one change; the "
              "failing checks are the probes that reproduce them. Do not weaken or remove any check.")]
    for outcome in seen.values():
        failing = ", ".join(outcome.verify.failing_checks) if outcome.verify else ""
        parts.append(f"- {outcome.failure.code} ({failing}): {outcome.failure.summary}\n{outcome.failure.agent_note[:2500]}")
    return "\n\n".join(parts)[:6000]


def _ask_owner(run: RunRef, task_id: str, sequence: int, decision: RecoveryDecision, settings: Settings) -> OwnerAnswer:
    """Publish the decision request and wait durably for a matching answer. Answers to older requests are refused."""
    request_id = f"{task_id}:d{sequence}"
    request = {"request_id": request_id, "task_id": task_id, "reason": decision.reason,
               "failure": decision.failure.model_dump(mode="json") if decision.failure else None,
               "limit_hit": decision.limit_hit,
               "options": ["retry", "retry_with_note", "retry_other_route", "stop"]}
    DBOS.set_event("decision", request)
    DBOS.set_event("state", {"task_id": task_id, "state": "needs_decision", "request_id": request_id})
    steps.emit("decision_requested", {"run_id": run.run_id, "task_id": task_id, "request_id": request_id,
                                      "reason": decision.reason})
    while True:
        message = DBOS.recv(f"owner:{task_id}", timeout_seconds=settings.owner_wait_seconds)
        if message is None:
            continue
        try:
            answer = OwnerAnswer.model_validate(message)
        except ValueError:
            steps.emit("command_refused", {"run_id": run.run_id, "task_id": task_id, "reason": "invalid answer"})
            continue
        if answer.request_id != request_id:
            steps.emit("command_refused", {"run_id": run.run_id, "task_id": task_id, "reason": "stale answer",
                                           "request_id": answer.request_id, "open": request_id})
            continue
        DBOS.set_event("decision", None)
        steps.emit("decision_answered", {"run_id": run.run_id, "task_id": task_id, "request_id": request_id,
                                         "action": answer.action, "by": answer.by})
        return answer


def _finish(run: RunRef, task_id: str, status: TaskStatus, outcomes: list[AttemptOutcome],
            last: AttemptOutcome | None, decision: RecoveryDecision | None) -> TaskOutcome:
    outcome = TaskOutcome(run_id=run.run_id, task_id=task_id, status=status, attempts=len(outcomes),
                          snapshot_sha=last.snapshot.snapshot_sha if last and last.snapshot else None,
                          integrated_ref=last.integrated_ref if last else None, decision=decision)
    DBOS.set_event("state", {"task_id": task_id, "state": status.value})
    steps.emit("task_settled", {"run_id": run.run_id, "task_id": task_id, "status": status.value,
                                "attempts": len(outcomes)})
    return outcome


# ------------------------------------------------------------------------------------------- agent / verify / merge
@DBOS.workflow(name="bt.agent")
def agent_workflow(attempt_data: dict, route_data: dict, base: str, note: str, limits: dict,
                   poll_seconds: float) -> dict:
    """One agent process from worktree to snapshot. Runs on the agents queue: its slot is held only while it runs."""
    prepared = steps.prepare(attempt_data, route_data, base, note, limits)
    if "start_error" in prepared:
        return {"start_error": prepared["start_error"]}
    material = prepared["prepared"]
    process = steps.launch(attempt_data, material, limits)
    steps.emit("attempt_started", {"attempt_key": AttemptRef.model_validate(attempt_data).attempt_key,
                                   "unit": process.get("unit"), "provider": route_data["provider"],
                                   "model": route_data["model"]})
    while process["state"] == "running":
        DBOS.sleep(poll_seconds)
        process = steps.observe(attempt_data)
    if process["state"] == "unknown" or process.get("live_pids"):
        # never capture or release while something of the attempt may still write: stragglers or an unreadable unit
        ended = process
        process = {**steps.terminate(attempt_data), **{k: ended[k] for k in ("exit_code", "result", "oom_killed")
                                                       if ended.get(k) is not None}}
    report = steps.read(attempt_data, route_data, process)
    snapshot = steps.capture(attempt_data, material)
    steps.release(attempt_data)
    return {"prepared": material, "process": process, "agent": report, "snapshot": snapshot,
            "requires": _requires(attempt_data), "paths": _paths(attempt_data)}


def _requires(attempt_data: dict) -> list[str]:
    ref = AttemptRef.model_validate(attempt_data)
    task = frontier.task(steps.plan(ref.run), ref.task_id)
    names = []
    for check in task.verification:
        names += [r for r in check.get("requires", ()) if isinstance(r, str) and not r.startswith("service:")]
    return names


def _paths(attempt_data: dict) -> list[str]:
    ref = AttemptRef.model_validate(attempt_data)
    return list(frontier.task(steps.plan(ref.run), ref.task_id).expected_paths)


@DBOS.workflow(name="bt.verify")
def verify_workflow(attempt_data: dict, prepared: dict, snapshot: dict, profile: str) -> dict:
    return steps.verify(attempt_data, prepared, snapshot, profile)


@DBOS.workflow(name="bt.integrate")
def integrate_workflow(run_data: dict, task_id: str, snapshot: dict) -> dict:
    return steps.integrate(run_data, task_id, snapshot)


__all__ = ["Prepared", "agent_workflow", "integrate_workflow", "run_workflow", "task_workflow", "verify_workflow"]
