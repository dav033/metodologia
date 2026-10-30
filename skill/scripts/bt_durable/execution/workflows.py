"""Durable workflows: run → task → (agent | verification | integration), each on the queue of its load class.

Workflow bodies are deterministic: time comes from the `bt.now` step, every external effect is a step, and every
decision is a pure control-plane function of checkpointed step results. Workflow IDs are derived from the run,
task and attempt identity, so starting or enqueueing the same work twice returns the existing workflow.

Messages (DBOS.send/recv, durable):
- topic `run` of the run workflow: task_done, retry_task, pause, resume (owner commands carry a request id, and may
  carry the state they were built against, `expect_paused`/`expect_round`: a stale one is refused, never applied);
- topic `owner:<task>` of a task workflow: the owner's answer to the open decision (stale answers are refused).
Events (DBOS.set_event): `state`, `decision` on task workflows; `summary` on the run workflow (the projection).
"""
from __future__ import annotations

from bt_contracts.execution import (
    AgentReport,
    AttemptOutcome,
    AttemptRef,
    AttemptStatus,
    LegacyProgress,
    LegacyTask,
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
from bt_contracts.failure import (
    FailureClass,
    FailureReport,
    RecoveryAction,
    RecoveryDecision,
)
from bt_contracts.owner import OwnerAnswer, RunCommand
from dbos import DBOS, SetWorkflowID
from dbos._error import (
    DBOSMaxStepRetriesExceeded,  # dbos pinned in uv.lock; not re-exported by the package
)

from ..control import classify, frontier, policy, subplans
from ..settings import Settings
from . import engine, steps

TOPIC_RUN = "run"
STANDARD, RELAXED = "standard", "relaxed"
OWNER_FIRST = frozenset({FailureClass.PRODUCT_DECISION, FailureClass.PERMISSION})   # never answered by a new agent run
# DBOS.patch names (README "Upgrading workflows"): each sits right before a plain step, never before a wait
PATCH_OWNER_REVERIFY = "bt-task-owner-reverify"
PATCH_RECONCILE_ASKS_OWNER = "bt-task-reconcile-asks-owner"
PATCH_RUN_SUBPLANS = "bt-run-subplans"
PATCH_TASK_PAUSE = "bt-task-respects-pause"
PATCH_RUN_AUDITS = "bt-run-audit-remediation"
PATCH_RUN_STEP_FAILURES = "bt-run-survives-step-failures"
PATCH_RUN_REOPENED = "bt-run-reopened"
PATCH_RUN_RECOMPOSE = "bt-run-recompose-gate"
# what a step the run workflow calls itself raises once its retries are spent; before PATCH_RUN_STEP_FAILURES the run
# ended in ERROR there (never recovered), so no recorded history goes on past such a failure
RUN_STEP_ERRORS = (steps.StepFailure, DBOSMaxStepRetriesExceeded)
COMPOSE_TURNS = 3                        # turns a gate's composition may fail before the gate counts as rejected
# DBOS counts every dispatch of a workflow, each recovery after an engine restart included, never resets the count, and
# dead-letters the workflow (MAX_RECOVERY_ATTEMPTS_EXCEEDED, never recovered) past `max_recovery_attempts`, 100 by
# default. The run and task workflows wait for days through every deploy (pictures REQ-021 r25: 7 recoveries in its
# first day), so they have no such limit; they only orchestrate, and the work that could crash the engine runs in the
# agent/verify/integrate children, which keep DBOS's poison-workflow limit.
LONG_LIVED = {"max_recovery_attempts": None}


def run_workflow_id(run: RunRef) -> str:
    """The run's first incarnation; `bt-durable reopen` forks an ended run into `<this>@<N>` (client.reopen)."""
    return f"bt:{run.run_id}"


def task_workflow_id(run: RunRef, task_id: str, round_no: int) -> str:
    return f"bt:{run.run_id}:{task_id}:k{round_no}"


# ---------------------------------------------------------------------------------------------------------- run
@DBOS.workflow(name="bt.run", **LONG_LIVED)
def run_workflow(run_data: dict, settings_data: dict, legacy_data: dict) -> dict:
    """Start every ready task, wait for news, repeat; ends when nothing is left to run. `legacy_data` is the progress
    the migration bridge re-proved (LegacyProgress): inherited snapshots are integrated into the new line first, in
    plan order, so dependents build on them; reconcilable ones are verified again before they count."""
    run, settings = RunRef.model_validate(run_data), Settings.model_validate(settings_data)
    legacy = LegacyProgress.model_validate(legacy_data)
    plan = steps.workflow_plan(run)
    states: dict[str, str] = {}
    results: dict[str, dict] = {}
    reconcile = legacy.of("reconcile")
    inherit = legacy.of("inherit")
    for task in plan.tasks:
        item = inherit.get(task.id)
        if item is None:
            continue
        if item.integrated:     # a later stage (stage_join): its copied lines hold it already; no step, so a run started
            states[task.id] = "inherited"           # from an older input replays exactly the steps it recorded
            results[task.id] = {"task_id": task.id, "status": "inherited", "provenance": item.provenance,
                                "snapshot_sha": item.snapshot_sha}
            continue
        snapshot = Snapshot(snapshot_sha=item.snapshot_sha, base_sha=item.base_sha, manifest_path=item.manifest_path)
        merged = _enqueue(engine.INTEGRATE, f"bt:{run.run_id}:seed:{task.id}", integrate_workflow, run_data, task.id,
                          snapshot.model_dump(mode="json"))
        if merged.get("ref") and not merged.get("conflict") and not merged.get("internal_error"):
            states[task.id] = "inherited"
            results[task.id] = {"task_id": task.id, "status": "inherited", "provenance": item.provenance,
                                "integrated_ref": merged["ref"]}
        else:                                       # it no longer fits the line: verify it and continue from it
            reconcile[task.id] = item
            steps.emit("inherit_refused", {"run_id": run.run_id, "task_id": task.id,
                                           "reason": merged.get("conflict") or merged.get("internal_error")})
    rounds: dict[str, int] = {}
    paused = legacy.paused                  # False in every input recorded before stage joins carried the owner's pause
    seen_commands: set[str] = set()
    # plan 1.3.0: subplan lines and composition gates, switched on by a patch so that a run recorded before it replays
    # its old iterations unchanged (the patch returns False where they already recorded a step)
    lines_on = False
    composed: dict[str, str] = {}
    rejected: dict[str, str] = {}
    synced: frozenset = frozenset()
    # milestone audits (REQ-030 item 4): an accepted audit's ledger is judged; blocking findings become coordinated
    # repairs (one per group of related findings), then the audit runs again, at most `remediation_rounds` times
    audits_on = False
    remediations: dict[str, dict] = {}
    compose_failures: dict[str, int] = {}
    # an incarnation forked by `reopen` from a run that ended blocked waits for the owner's command that reopened it
    # (a retry) instead of ending again at once; the original run never takes this path. Incarnation `@N` replays the
    # reopenings of `@2`..`@N-1` from its history, so it waits once more than they did: N-1 reopenings in all
    reopenings, awaiting_command = 0, False
    incarnation = _incarnation(DBOS.workflow_id, run)
    DBOS.set_event("summary", _summary(run, states, results, paused))
    while True:
        if not lines_on and subplans.enabled(plan) and DBOS.patch(PATCH_RUN_SUBPLANS):
            lines_on = True
            steps.emit("subplans_enabled", {"run_id": run.run_id, "subplans": [sp.id for sp in plan.subplans],
                                            "gates": [gate.id for gate in plan.composition_gates]})
        if lines_on:
            accepted = _accepted_snapshots(states, results, inherit)
            if frozenset(accepted) != synced or not synced:
                complete = True
                for role, items in _line_items(plan, accepted).items():
                    try:
                        report = steps.sync_lines(run_data, role, items)
                    except RUN_STEP_ERRORS as error:    # e.g. a stale ref lock: reported, tried again next turn
                        if not DBOS.patch(PATCH_RUN_STEP_FAILURES):
                            raise
                        report = {"error": _step_error(error)}
                    if "error" in report:               # e.g. LINE_BASE_UNKNOWN: reported, tried again next turn
                        complete = False
                        steps.emit("subplan_lines_unavailable", {"run_id": run.run_id, "role": role,
                                                                 "reason": report["error"]})
                    elif any(item["conflicts"] for item in report.values()):
                        steps.emit("subplan_line_conflict", {"run_id": run.run_id, "report": report})
                synced = frozenset(accepted) if complete else frozenset()
            for gate in subplans.to_compose(plan, states, subplans.Gates(composed, rejected)):
                try:
                    built = steps.compose(run_data, gate.id, {sp: subplans.evidence(plan, sp, results)
                                                              for sp in gate.subplans})
                except RUN_STEP_ERRORS as error:
                    if not DBOS.patch(PATCH_RUN_STEP_FAILURES):
                        raise
                    compose_failures[gate.id] = compose_failures.get(gate.id, 0) + 1
                    steps.emit("gate_compose_failed", {"run_id": run.run_id, "gate": gate.id,
                                                       "turn": compose_failures[gate.id], "reason": _step_error(error)})
                    if compose_failures[gate.id] < COMPOSE_TURNS:
                        continue                        # composed again on a later turn
                    built = {"state": "rejected", "reason": f"COMPOSE_FAILED {COMPOSE_TURNS} turns: {_step_error(error)}"}
                if built.get("state") == "rejected":
                    rejected[gate.id] = str(built.get("reason") or "rejected")[:300]
                else:
                    composed[gate.id] = str(built.get("candidate_id"))
                steps.emit("gate_composed", {"run_id": run.run_id, "gate": gate.id, **built})
        gates = subplans.Gates(composed, rejected) if lines_on else None
        front = frontier.compute(plan, states, max_parallel=settings.max_parallel, gates=gates)
        if not paused:
            for task_id in front.ready:
                rounds[task_id] = rounds.get(task_id, 0) + 1
                _start_task(run, task_id, rounds[task_id], settings, note="",
                            legacy=reconcile.get(task_id) if rounds[task_id] == 1 else None)
                states[task_id] = "running"
        DBOS.set_event("summary", _summary(run, states, results, paused, gates))
        if front.finished:
            break
        retrying = [g for g in compose_failures if g not in composed and g not in rejected]
        if not paused and not any(s == "running" for s in states.values()) and not front.ready and not retrying \
                and not awaiting_command:
            if reopenings < incarnation - 1 and DBOS.patch(PATCH_RUN_REOPENED):
                reopenings, awaiting_command = reopenings + 1, True
                steps.emit("run_reopened", {"run_id": run.run_id, "workflow_id": DBOS.workflow_id})
            else:
                break                               # only blocked work and its dependents remain
        message = DBOS.recv(TOPIC_RUN, timeout_seconds=settings.run_poll_seconds)
        if message is None:
            continue
        kind = message.get("kind") if isinstance(message, dict) else None
        if kind == "task_done":
            outcome = TaskOutcome.model_validate(message["outcome"])
            states[outcome.task_id] = outcome.status.value
            results[outcome.task_id] = outcome.model_dump(mode="json")
            repaired = next((audit for audit, entry in remediations.items() if entry["running"] == outcome.task_id), None)
            if repaired is not None:
                _repair_settled(run, repaired, outcome, remediations[repaired], states, results, rounds, settings)
            elif outcome.status == TaskStatus.COMPLETED and _is_audit(plan, outcome.task_id) \
                    and (audits_on or DBOS.patch(PATCH_RUN_AUDITS)):
                audits_on = True
                try:
                    verdict = steps.audit_gate(run_data, outcome.task_id, outcome.snapshot_sha or "",
                                               outcome.snapshot_base or "")
                except RUN_STEP_ERRORS as error:
                    if not DBOS.patch(PATCH_RUN_STEP_FAILURES):
                        raise
                    verdict = {"audit": True, "ok": False, "gate_error": _step_error(error)}
                _audit_judged(run, outcome.task_id, verdict, remediations, states, results, rounds, settings)
            continue
        try:
            command = RunCommand.model_validate(message)
        except ValueError:
            steps.emit("command_refused", {"run_id": run.run_id, "reason": "invalid run command"})
            continue
        if command.request_id in seen_commands:
            continue                                # an idempotent repeat of a command already applied
        seen_commands.add(command.request_id)
        awaiting_command = False
        stale = _stale_command(command, paused, rounds)
        if stale:                                   # built against a state the run has left: never applied
            steps.emit("command_refused", {"run_id": run.run_id, "request_id": command.request_id,
                                           "reason": stale})
        elif command.kind == "pause":
            paused = True
        elif command.kind == "resume":
            paused = False
        elif command.kind == "retry_task" and _rejected_gate(plan, command.task_id, rejected) \
                and DBOS.patch(PATCH_RUN_RECOMPOSE):
            # the owner's retry of a gate task held by a rejected candidate composes the gate again (as the legacy
            # owner rebuilds a candidate on every pass); its members' lines may have changed since
            gate_id = _rejected_gate(plan, command.task_id, rejected)
            steps.emit("gate_recompose", {"run_id": run.run_id, "gate": gate_id, "previous": rejected.pop(gate_id)})
            compose_failures.pop(gate_id, None)
        elif command.kind == "retry_task" and command.task_id and states.get(command.task_id) in frontier.STOPPED:
            if command.task_id in remediations:         # the owner retrying a blocked audit grants it one more round
                remediations[command.task_id]["extra"] += 1
            rounds[command.task_id] = rounds.get(command.task_id, 1) + 1
            _start_task(run, command.task_id, rounds[command.task_id], settings, note=command.note)
            states[command.task_id] = "running"
        else:
            steps.emit("command_refused", {"run_id": run.run_id, "request_id": command.request_id,
                                           "reason": f"{command.kind} does not apply to the current state"})
    summary = _summary(run, states, results, paused, subplans.Gates(composed, rejected) if lines_on else None,
                       final=True, finished=front.finished)
    DBOS.set_event("summary", summary)
    steps.emit("run_settled", {"run_id": run.run_id, "status": summary["status"]})
    return summary


def _is_audit(plan, task_id: str) -> bool:
    return str(plan.task(task_id).meta.get("kind") or "") == "audit"


def _audit_judged(run: RunRef, audit: str, verdict: dict, remediations: dict, states: dict, results: dict,
                  rounds: dict, settings: Settings) -> None:
    """What an accepted audit's judgement means for the run (deterministic: `verdict` is the step's checkpoint)."""
    if not verdict.get("audit") or verdict.get("ok"):
        steps.emit("audit_passed", {"run_id": run.run_id, "task_id": audit, "skipped": verdict.get("skipped", "")})
        return
    if verdict.get("gate_error"):                 # the gate itself failed: nothing was judged, the owner decides
        steps.emit("audit_gate_failed", {"run_id": run.run_id, "task_id": audit, "reason": verdict["gate_error"]})
        _audit_stuck(audit, f"the audit gate could not judge it ({verdict['gate_error']}); retry-task runs the audit "
                            "again", states, results)
        return
    entry = remediations.setdefault(audit, {"round": 0, "queue": [], "running": "", "extra": 0, "findings": []})
    limit = int(verdict.get("rounds") or 0) + entry["extra"]
    repairs = list(verdict.get("repairs") or ())
    steps.emit("audit_blocked", {"run_id": run.run_id, "task_id": audit, "round": entry["round"], "limit": limit,
                                 "problems": verdict.get("problems", []),
                                 "findings": [f["id"] for f in verdict.get("blocking", ())],
                                 "repairs": [{"owner": r["owner"], "findings": r["findings"]} for r in repairs]})
    if verdict.get("structural"):
        _audit_stuck(audit, "the plan must change: " + "; ".join(verdict.get("problems", ())), states, results)
        return
    if entry["round"] >= limit:
        _audit_stuck(audit, f"{len(verdict.get('blocking', ()))} blocking finding(s) or problems remain after "
                            f"{entry['round']} remediation round(s) (limit {limit}): {verdict.get('summary', '')}",
                     states, results)
        return
    entry["round"] += 1
    if verdict.get("problems"):                   # the audit itself is unusable: it runs again, told what was wrong
        note = ("Your previous audit could not be used: " + "; ".join(verdict["problems"])[:3000] +
                ". Audit again and write the declared report and findings ledger only.")
        _start_round(run, audit, note, rounds, states, settings)
        return
    if not verdict.get("remediate") or not repairs or any(not repair["owner"] for repair in repairs):
        _audit_stuck(audit, "blocking findings that cannot be repaired automatically (remediation off, or a finding "
                            f"names no task of the plan): {verdict.get('summary', '')}", states, results)
        return
    entry["queue"] = repairs[1:]
    entry["findings"] = [f["id"] for f in verdict.get("blocking", ())]
    entry["running"] = repairs[0]["owner"]
    states[audit] = "remediating"
    _start_round(run, repairs[0]["owner"], repairs[0]["note"], rounds, states, settings)


def _repair_settled(run: RunRef, audit: str, outcome: TaskOutcome, entry: dict, states: dict, results: dict,
                    rounds: dict, settings: Settings) -> None:
    """One coordinated repair ended: the next one of the round, or the audit again once all are in."""
    entry["running"] = ""
    if outcome.status != TaskStatus.COMPLETED:
        _audit_stuck(audit, f"the coordinated repair {outcome.task_id} ended {outcome.status.value}", states, results)
        return
    if entry["queue"]:
        repair = entry["queue"].pop(0)
        entry["running"] = repair["owner"]
        _start_round(run, repair["owner"], repair["note"], rounds, states, settings)
        return
    note = (f"Re-audit after remediation round {entry['round']}: the findings {', '.join(entry['findings'])} were "
            "repaired in the tree you start from. Check every earlier finding again and record each one's status "
            "(`fixed` only with the command you ran and its result as evidence), and keep auditing everything else.")
    _start_round(run, audit, note, rounds, states, settings)


def _start_round(run: RunRef, task_id: str, note: str, rounds: dict, states: dict, settings: Settings) -> None:
    rounds[task_id] = rounds.get(task_id, 0) + 1
    _start_task(run, task_id, rounds[task_id], settings, note=note)
    states[task_id] = "running"


def _audit_stuck(audit: str, reason: str, states: dict, results: dict) -> None:
    """The audit's dependents stay waiting; the owner sees why (`retry-task` grants one more round)."""
    states[audit] = "blocked"
    results[audit] = {**(results.get(audit) or {}), "status": "blocked", "audit": reason[:1000]}


def _rejected_gate(plan, task_id: str | None, rejected: dict) -> str:
    """The rejected composition gate that `task_id` runs ('' when it is not such a gate task)."""
    return next((gate.id for gate in getattr(plan, "composition_gates", ()) or ()
                 if gate.task == task_id and gate.id in rejected), "")


def _incarnation(workflow_id: str, run: RunRef) -> int:
    """1 for the run's own workflow, N for `bt:<run>@N` (a reopened incarnation, client.reopen)."""
    suffix = workflow_id[len(run_workflow_id(run)):]
    return int(suffix[1:]) if suffix.startswith("@") and suffix[1:].isdigit() else 1


def _step_error(error: Exception, limit: int = 500) -> str:
    """The error as a fact, with the cause a spent step hides: DBOSMaxStepRetriesExceeded only says the step ran out of
    retries, so pictures REQ-021 r25's gate CG-7 was rejected as «COMPOSE_FAILED 3 turns: … bt.compose has exceeded its
    maximum of 3 retries» without the GitCommandError that caused it (2026-10-29). Text only: no step changes."""
    text = f"{type(error).__name__}: {error}"
    errors = getattr(error, "errors", None) if isinstance(error, DBOSMaxStepRetriesExceeded) else None
    if errors:
        text += f" (last: {type(errors[-1]).__name__}: {errors[-1]})"
    return text[:limit]


def _stale_command(command: RunCommand, paused: bool, rounds: dict[str, int]) -> str:
    """Why a command that names the state it was built against no longer applies ('' when it does). Commands
    without `expect_*` (every command sent before REQ-030 M7) return '' and take exactly the path they took before,
    so replaying a recorded history runs the same steps; a refusal is a plain `bt.emit` step on a live message."""
    if command.expect_paused is not None and command.expect_paused != paused:
        return f"stale: the run is {'paused' if paused else 'running'} now"
    if command.expect_round is not None and rounds.get(command.task_id or "") != command.expect_round:
        return (f"stale: {command.task_id} is in round {rounds.get(command.task_id or '')}, the command was built "
                f"for round {command.expect_round}")
    return ""


def _start_task(run: RunRef, task_id: str, round_no: int, settings: Settings, note: str,
                legacy: LegacyTask | None = None) -> None:
    with SetWorkflowID(task_workflow_id(run, task_id, round_no)):
        DBOS.start_workflow(task_workflow, run.model_dump(mode="json"), task_id, round_no,
                            settings.model_dump(mode="json"), note, DBOS.workflow_id,
                            legacy.model_dump(mode="json") if legacy else None)


def _summary(run: RunRef, states: dict, results: dict, paused: bool, gates: subplans.Gates | None = None,
             final: bool = False, finished: bool = False) -> dict:
    """`finished`: every task of the PLAN is done (`states` holds only the tasks that started: a run that stops with a
    gate task never started is not completed)."""
    values = set(states.values())
    if final:
        stuck = bool(values & frontier.STOPPED) or bool(gates is not None and gates.rejected)
        status = "completed" if finished and values <= frontier.DONE else ("blocked" if stuck else "settled")
    else:
        status = "paused" if paused else "running"
    out = {"run_id": run.run_id, "status": status, "tasks": dict(states), "results": results}
    if gates is not None:
        out["gates"] = {"composed": dict(gates.composed), "rejected": dict(gates.rejected)}
    return out


def _accepted_snapshots(states: dict, results: dict, inherit: dict) -> dict[str, str]:
    """Task -> the snapshot it was accepted with (its own work, not the line tip it was merged into)."""
    out = {}
    for task_id, state in states.items():
        if state not in frontier.DONE:
            continue
        snapshot = (results.get(task_id) or {}).get("snapshot_sha") or (
            inherit[task_id].snapshot_sha if task_id in inherit else "")
        if snapshot:
            out[task_id] = snapshot
    return out


def _line_items(plan, accepted: dict[str, str]) -> dict[str, dict[str, list[list[str]]]]:
    """Role -> subplan -> [[task, snapshot], ...] in plan order, for the accepted tasks of each subplan's scope."""
    order = [t.id for t in plan.tasks]
    out: dict[str, dict[str, list[list[str]]]] = {}
    for subplan_id, scope in subplans.scopes(plan).items():
        # every line exists from the start (even empty), so a member never falls back to the run line
        role = plan.task(next(t for t in order if plan.task(t).meta.get("subplan_id") == subplan_id)).repository
        out.setdefault(role, {}).setdefault(subplan_id, [])
        for task_id in order:
            if task_id in scope and task_id in accepted:
                role = plan.task(task_id).repository
                out.setdefault(role, {}).setdefault(subplan_id, []).append([task_id, accepted[task_id]])
    return out


# --------------------------------------------------------------------------------------------------------- task
@DBOS.workflow(name="bt.task", **LONG_LIVED)
def task_workflow(run_data: dict, task_id: str, round_no: int, settings_data: dict, note: str,
                  parent_id: str, legacy_data: dict | None = None) -> dict:
    run, settings = RunRef.model_validate(run_data), Settings.model_validate(settings_data)
    legacy = LegacyTask.model_validate(legacy_data) if legacy_data else None
    outcome = _run_task(run, task_id, round_no, settings, note, legacy, parent_id)
    DBOS.send(parent_id, {"kind": "task_done", "outcome": outcome.model_dump(mode="json")}, TOPIC_RUN,
              idempotency_key=f"{DBOS.workflow_id}:done")
    return outcome.model_dump(mode="json")


def _run_task(run: RunRef, task_id: str, round_no: int, settings: Settings, note: str,
              legacy: LegacyTask | None = None, parent_id: str = "") -> TaskOutcome:
    budget = settings.budget
    pause_on = False
    started = steps.now()
    outcomes: list[AttemptOutcome] = []
    exclude: list[str] = []
    limits = dict(settings.agent_limits)
    waits = repairs = route_changes = 0
    remediated = False
    number = (round_no - 1) * 100
    base_override = ""
    decisions = 0
    if legacy is not None:                       # a legacy snapshot counts only after it passes verification again
        reconciled, failure_note, failure = _reconcile(run, task_id, round_no, legacy)
        if reconciled is not None:
            return reconciled
        base_override, note = legacy.snapshot_sha, failure_note or note
        if failure is not None and failure.failure_class in OWNER_FIRST and DBOS.patch(PATCH_RECONCILE_ASKS_OWNER):
            # missing manual evidence or an authorization is not fixed by an agent: the owner attests or decides first
            steps.emit("reconcile_needs_owner", {"run_id": run.run_id, "task_id": task_id, "code": failure.code})
            decision = RecoveryDecision(action=RecoveryAction.ESCALATE, reason=f"{failure.failure_class.value}: "
                                        f"{failure.summary}"[:500], failure=failure, note_for_agent=failure.agent_note)
            decisions, answer = _owner(run, task_id, decisions, decision, settings, outcomes,
                                       _legacy_target(run, task_id, round_no, legacy))
            if isinstance(answer, TaskOutcome):
                return answer
            if answer.action == "stop":
                return _finish(run, task_id, TaskStatus.BLOCKED, outcomes, None, decision)
            note = answer.note or note
    while True:
        DBOS.set_event("state", {"task_id": task_id, "state": "routing", "attempts": len(outcomes)})
        if not pause_on and parent_id and DBOS.patch(PATCH_TASK_PAUSE):
            pause_on = True                     # right before a plain step (bt.now); old histories hold bt.now here
        at = steps.now()
        if pause_on:
            # a paused run starts no agent attempt at all: neither a new task nor a retry of a running one
            summary = DBOS.get_event(parent_id, "summary", timeout_seconds=0)
            if isinstance(summary, dict) and summary.get("status") == "paused":
                DBOS.set_event("state", {"task_id": task_id, "state": "paused", "attempts": len(outcomes)})
                DBOS.sleep(settings.run_poll_seconds)
                continue
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
            target = ((attempt, choice.route, agent) if agent.get("snapshot") else
                      _legacy_target(run, task_id, round_no, legacy) if legacy is not None else None)
            decisions, answer = _owner(run, task_id, decisions, decision, settings, outcomes, target)
            if isinstance(answer, TaskOutcome):
                return answer
            if answer.action == "stop":
                return _finish(run, task_id, TaskStatus.BLOCKED, outcomes, outcome, decision)
            note = answer.note or decision.note_for_agent
            if answer.action == "retry_other_route":
                exclude.append(_route_key(choice.route))
            budget = budget.model_copy(update={"max_attempts": budget.max_attempts + (answer.extra_attempts or 1)})
            remediated = False


def _legacy_target(run: RunRef, task_id: str, round_no: int, legacy: LegacyTask) -> tuple[AttemptRef, None, dict]:
    """The legacy snapshot as something to verify: its own attempt reference (number 99 of the round) and material."""
    attempt = AttemptRef(run=run, task_id=task_id, number=(round_no - 1) * 100 + 99, workflow_id=DBOS.workflow_id)
    material = Prepared(worktree=legacy.worktree or legacy.attempt_dir, branch="legacy", base_sha=legacy.base_sha,
                        repository=legacy.repository, attempt_dir=legacy.attempt_dir, prompt_path=legacy.manifest_path,
                        argv=("legacy-evidence",), env_file=legacy.manifest_path, timeout_seconds=1)
    snapshot = Snapshot(snapshot_sha=legacy.snapshot_sha, base_sha=legacy.base_sha, manifest_path=legacy.manifest_path)
    return attempt, None, {"prepared": material.model_dump(mode="json"), "snapshot": snapshot.model_dump(mode="json"),
                           "producer": _legacy_producer(legacy)}


def _legacy_producer(legacy: LegacyTask) -> str:
    """The legacy attempt that made the snapshot (`legacy att-0059 m6://…` -> att-0059): what a receipt is bound to."""
    words = legacy.provenance.split()
    return words[1] if len(words) > 1 and words[0] == "legacy" else ""


def _reconcile(run: RunRef, task_id: str, round_no: int,
               legacy: LegacyTask) -> tuple[TaskOutcome | None, str, FailureReport | None]:
    attempt, _route, agent = _legacy_target(run, task_id, round_no, legacy)
    DBOS.set_event("state", {"task_id": task_id, "state": "reconciling", "attempt": attempt.attempt_key})
    outcome = _evaluate(attempt, None, agent, None, STANDARD)
    steps.emit("legacy_reconciled", {"run_id": run.run_id, "task_id": task_id, "status": outcome.status.value,
                                     "provenance": legacy.provenance})
    if outcome.status == AttemptStatus.ACCEPTED:
        done = _finish(run, task_id, TaskStatus.COMPLETED, [], outcome, None)
        return done.model_copy(update={"provenance": f"reconciled {legacy.provenance}"[:500]}), "", None
    return None, outcome.failure.agent_note if outcome.failure else "", outcome.failure


def _owner(run: RunRef, task_id: str, decisions: int, decision: RecoveryDecision, settings: Settings,
           outcomes: list[AttemptOutcome], target: tuple[AttemptRef, Route | None, dict] | None
           ) -> tuple[int, OwnerAnswer | TaskOutcome]:
    """Ask the owner. `reverify` verifies `target` (the task's latest snapshot) again, without an agent run — after the
    coordinator attested its manual checks, or to rule out a flaky check — and finishes the task when it now passes;
    while it does not, the owner is asked again with the new evidence. Anything else is returned for the caller."""
    while True:
        decisions += 1
        answer = _ask_owner(run, task_id, decisions, decision, settings, target)
        if not (answer.action == "reverify" and target is not None and DBOS.patch(PATCH_OWNER_REVERIFY)):
            return decisions, answer
        attempt, route, agent = target
        profile = f"owner{decisions}"
        steps.emit("owner_reverify", {"run_id": run.run_id, "task_id": task_id, "attempt_key": attempt.attempt_key,
                                      "request_id": answer.request_id})
        verify = _enqueue(engine.VERIFY, f"bt:{attempt.attempt_key}:verify:{profile}", verify_workflow,
                          attempt.model_dump(mode="json"), agent["prepared"], agent["snapshot"], profile)
        outcome = _evaluate(attempt, route, agent, verify, profile)
        if outcome.status == AttemptStatus.ACCEPTED:
            outcomes.append(outcome)
            done = _finish(run, task_id, TaskStatus.COMPLETED, outcomes, outcome, None)
            if agent.get("producer"):
                done = done.model_copy(update={"provenance": f"reconciled legacy {agent['producer']} after the "
                                                             f"owner's re-verification {answer.request_id}"[:500]})
            return decisions, done
        failure = outcome.failure
        decision = RecoveryDecision(action=RecoveryAction.ESCALATE,
                                    reason=f"still not proven after re-verification: {failure.summary if failure else ''}"[:500],
                                    failure=failure, note_for_agent=failure.agent_note if failure else "")
        steps.emit_decision(attempt, decision)


def _evaluate(attempt: AttemptRef, route: Route | None, agent: dict, verify: dict | None, profile: str) -> AttemptOutcome:
    """Verify (if there is something to verify), integrate a pass, and classify whatever went wrong."""
    if agent.get("internal_error"):
        failure = classify.classify(classify.AttemptFacts(internal_error=agent["internal_error"]))
        return AttemptOutcome(attempt=attempt, status=AttemptStatus.EXECUTION_FAILED, route=route, failure=failure)
    process = ProcessRecord.model_validate(agent["process"]) if agent.get("process") else None
    report = AgentReport.model_validate(agent["agent"]) if agent.get("agent") else None
    snapshot = Snapshot.model_validate(agent["snapshot"]) if agent.get("snapshot") else None
    unverifiable = report is not None and report.status in ("limit", "timeout", "cancelled")   # cut short: retry, not judge
    if verify is None and snapshot is not None and snapshot.snapshot_sha and not unverifiable:
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
    if failure is None and snapshot is not None and verdict is not None:
        merged = _enqueue(engine.INTEGRATE, f"bt:{attempt.attempt_key}:integrate", integrate_workflow,
                          attempt.run.model_dump(mode="json"), attempt.task_id, agent["snapshot"])
        if merged.get("internal_error"):
            failure = classify.classify(classify.AttemptFacts(internal_error=merged["internal_error"]))
        elif merged.get("conflict"):
            failure = classify.classify(classify.AttemptFacts(process=process, agent=report, verify=verdict,
                                                              integration_conflict=merged["conflict"]))
        else:
            integrated = merged.get("ref")
    if failure is None and (snapshot is None or verdict is None):
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
        return {"internal_error": _step_error(error, 2000)}


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


def _ask_owner(run: RunRef, task_id: str, sequence: int, decision: RecoveryDecision, settings: Settings,
               target: tuple[AttemptRef, Route | None, dict] | None = None) -> OwnerAnswer:
    """Publish the decision request and wait durably for a matching answer. Answers to older requests are refused.
    With a snapshot to verify again, `reverify` is offered, and the request names the attempt a coordinator receipt
    must be bound to (`verify_attempt`) and the command that attests and answers in one go."""
    request_id = f"{task_id}:d{sequence}"
    request = {"request_id": request_id, "task_id": task_id, "reason": decision.reason,
               "failure": decision.failure.model_dump(mode="json") if decision.failure else None,
               "limit_hit": decision.limit_hit,
               "options": ["retry", "retry_with_note", "retry_other_route", "stop"]}
    if target is not None:
        request["options"] = ["reverify", *request["options"]]
        request["verify_attempt"] = target[2].get("producer") or target[0].attempt_key
        if decision.failure is not None and decision.failure.code == classify.MANUAL_EVIDENCE:
            request["attest"] = (f"uv run bt-durable attest {run.project} {run.req} {task_id} --request {request_id} "
                                 "--evidence '<what was done and what was seen>'")
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
                          integrated_ref=last.integrated_ref if last else None, decision=decision,
                          verdict_ref=last.verify.result_ref if last and last.verify else "",
                          snapshot_base=last.snapshot.base_sha if last and last.snapshot else None)
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
    spec = frontier.task(steps.workflow_plan(AttemptRef.model_validate(attempt_data).run),
                         AttemptRef.model_validate(attempt_data).task_id)
    return {"prepared": material, "process": process, "agent": report, "snapshot": snapshot,
            "requires": _requires(spec), "paths": list(spec.expected_paths)}


def _requires(task) -> list[str]:
    names = []
    for check in task.verification:
        names += [r for r in check.get("requires", ()) if isinstance(r, str) and not r.startswith("service:")]
    return names


@DBOS.workflow(name="bt.verify")
def verify_workflow(attempt_data: dict, prepared: dict, snapshot: dict, profile: str) -> dict:
    return steps.verify(attempt_data, prepared, snapshot, profile)


@DBOS.workflow(name="bt.integrate")
def integrate_workflow(run_data: dict, task_id: str, snapshot: dict) -> dict:
    return steps.integrate(run_data, task_id, snapshot)


__all__ = ["Prepared", "agent_workflow", "integrate_workflow", "run_workflow", "task_workflow", "verify_workflow"]
