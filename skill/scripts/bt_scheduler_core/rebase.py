"""Rebase a run onto a later revision of the same plan, keeping the accepted work that did not change.

A new approved revision used to mean a new run: everything already accepted was thrown away. `rebase_run` moves the
persisted run from revision N to N+1 in ONE transaction instead:

- an accepted (COMPLETED) task whose fingerprint is unchanged keeps its state, attempts and route, as long as every
  prerequisite it had is kept too (a reset prerequisite invalidates what was built on it);
- a task whose fingerprint changed, whose prerequisites were reset, or that was not accepted goes back to PENDING with a
  fresh attempt budget (its old attempts stay in the history), and its route is forgotten so M2 plans it again;
- a task that is new in N+1 starts PENDING; a task that disappeared is dropped from the run (its attempts stay as history);
- a run with a live attempt is refused (finish or cancel it first): nothing is half-moved.

Two policies. `cascade=True` (the original): a task is kept only if every prerequisite it had is kept too. `cascade=False`
(content): a task is kept when ITS OWN content (`content_fingerprint`: objective, scope, checks) is unchanged, whatever
happened to its prerequisites: what depends on a redone task keeps its accepted result and the integration line merges
the redo into it, exactly as an audit rework `named` does. The one exception is a task that only judges others (`kind`
test or audit) with a prerequisite reset: its result proves nothing about the new tree, so it is redone. REQ-029's r4 -> r5
reset 28 of 33 accepted tasks because T4 changed; 21 of them had not changed at all.

The fingerprint is what the work IS: id, prerequisites, repository, acceptance criteria and verification. The
classification (complexity, risk, estimates...) is deliberately not part of it: it says how hard, not what to do.
The audit gets one `run_rebased {from_rev, to_rev, kept, reset, added, removed}` entry plus a `task_transition` for each
reset task. M1 stays the only authority of task and attempt state: this is its own operation, never a side door.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Callable
from dataclasses import dataclass
from time import time as _now

from .config import Config
from .errors import SchedulerError
from .model import RunState, TaskRec
from .plan import Plan, TaskSpec
from .repository import StateRepository
from .states import ATTEMPT_LIVE
from .states import AttemptState as A
from .states import TaskState as T
from .transitions import Ctx


@dataclass(frozen=True)
class RebaseReport:
    from_revision: int
    to_revision: int
    kept: tuple[str, ...]
    reset: tuple[str, ...]
    added: tuple[str, ...]
    removed: tuple[str, ...]


@dataclass(frozen=True)
class RevisionGuard:
    operation_key: str
    source_sha256: str
    target_sha256: str
    accepted_map_digest: str
    stop_generation: int
    scope: tuple[str, ...]
    base_digest: str
    current_base: Callable[[], str] | None
    barrier_deadline: float


@dataclass(frozen=True)
class RevisionApplication:
    outcome: str
    reason: str = ""
    report: dict | None = None
    live_attempt_ids: tuple[str, ...] = ()


def _accepted_map(state: RunState) -> dict[str, str]:
    """Map completed tasks to their accepted attempt ids, in a stable task-id order."""
    accepted = {}
    for task_id, rec in state.tasks.items():
        if rec.state != T.COMPLETED.value or not rec.attempts:
            continue
        attempt_id = rec.attempts[-1]
        attempt = state.attempts.get(attempt_id)
        if attempt is not None and A(attempt.state) == A.ACCEPTED:
            accepted[task_id] = attempt_id
    return accepted


def accepted_map_digest(state: RunState) -> str:
    """Digest the last accepted attempt for every completed task, in stable task-id order."""
    body = json.dumps(_accepted_map(state), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(body.encode("ascii")).hexdigest()


def stop_generation(state: RunState) -> int:
    """Read the owner stop counter, treating older states without it as generation zero."""
    return state.counters.get("stop", 0)


def _revision_fingerprint(spec: TaskSpec) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    return fingerprint(spec), tuple(spec.expected_paths), tuple(spec.shared_resources)


def _revision_refusal(state: RunState, operation_key: str, reason: str) -> RevisionApplication:
    barrier = state.revision_barrier
    if barrier is not None and barrier.get("operation_key") == operation_key:
        state.revision_barrier = None
    return RevisionApplication("refused", reason)


def _valid_guard(guard: RevisionGuard) -> bool:
    return (isinstance(guard.operation_key, str) and 1 <= len(guard.operation_key) <= 128 and
            all(32 <= ord(char) <= 126 for char in guard.operation_key) and
            isinstance(guard.source_sha256, str) and re.fullmatch(r"[0-9a-f]{64}", guard.source_sha256) is not None and
            isinstance(guard.target_sha256, str) and re.fullmatch(r"[0-9a-f]{64}", guard.target_sha256) is not None and
            isinstance(guard.accepted_map_digest, str) and
            re.fullmatch(r"[0-9a-f]{64}", guard.accepted_map_digest) is not None and
            isinstance(guard.stop_generation, int) and not isinstance(guard.stop_generation, bool) and
            guard.stop_generation >= 0 and isinstance(guard.scope, tuple) and
            all(isinstance(task_id, str) and bool(task_id) for task_id in guard.scope) and
            isinstance(guard.base_digest, str) and
            (guard.current_base is None or callable(guard.current_base)) and
            isinstance(guard.barrier_deadline, (int, float)) and not isinstance(guard.barrier_deadline, bool) and
            math.isfinite(guard.barrier_deadline))


def apply_plan_revision(repository: StateRepository, old: Plan, new: Plan, guard: RevisionGuard, *,
                        config: Config | None = None, clock: Callable[[], float] = _now) -> RevisionApplication:
    """Atomically apply a guarded, scoped revision while preserving attempt history and unrelated accepted work."""
    cfg = config or Config()
    with repository.transaction() as tx:
        if tx.state is None:
            return RevisionApplication("refused", "no_run")
        state = tx.state
        applied = state.revision_applications.get(guard.operation_key) if isinstance(guard.operation_key, str) else None
        if applied is not None:
            if applied["source"] == guard.source_sha256 and applied["target"] == guard.target_sha256:
                return RevisionApplication("adopted", report=dict(applied["report"]))
            return _revision_refusal(state, guard.operation_key, "key_conflict")
        if ((state.plan_id, state.revision, state.plan_sha256) != (old.plan_id, old.revision, guard.source_sha256) or
                old.sha256 != guard.source_sha256 or new.sha256 != guard.target_sha256 or
                new.plan_id != old.plan_id or new.revision <= old.revision):
            return _revision_refusal(state, guard.operation_key, "stale_source")
        now = clock()
        if not _valid_guard(guard):
            return _revision_refusal(state, guard.operation_key, "invalid_guard")
        if state.paused or state.cancel_requested or stop_generation(state) != guard.stop_generation:
            return _revision_refusal(state, guard.operation_key, "stopped")
        accepted = _accepted_map(state)
        barrier = state.revision_barrier
        if barrier is not None and barrier.get("operation_key") == guard.operation_key:
            baseline = barrier.get("accepted_map")
            captured_live = set(barrier.get("live_attempt_ids", []))
            if (barrier.get("accepted_map_digest") != guard.accepted_map_digest or not isinstance(baseline, dict)
                    or any(accepted.get(task_id) != attempt_id for task_id, attempt_id in baseline.items())
                    or any(attempt_id not in captured_live for task_id, attempt_id in accepted.items()
                           if task_id not in baseline)):
                return _revision_refusal(state, guard.operation_key, "stale_accepted_map")
        elif accepted_map_digest(state) != guard.accepted_map_digest:
            return _revision_refusal(state, guard.operation_key, "stale_accepted_map")
        if guard.current_base is not None:
            try:
                if guard.current_base() != guard.base_digest:
                    return _revision_refusal(state, guard.operation_key, "stale_base")
            except Exception:
                return _revision_refusal(state, guard.operation_key, "stale_base")
        old_by_id, new_by_id = ({spec.id: spec for spec in plan.tasks} for plan in (old, new))
        all_ids = set(old_by_id) | set(new_by_id)
        changed = {task_id for task_id in all_ids if task_id not in old_by_id or task_id not in new_by_id or
                   _revision_fingerprint(old_by_id[task_id]) != _revision_fingerprint(new_by_id[task_id])}
        plan_ids = set(old_by_id) | set(new_by_id)
        if not set(guard.scope) <= plan_ids or not changed <= set(guard.scope):
            return _revision_refusal(state, guard.operation_key, "out_of_scope")
        live = tuple(sorted(attempt.id for attempt in state.attempts.values() if A(attempt.state) in ATTEMPT_LIVE))
        if live:
            barrier = state.revision_barrier
            if barrier is not None and barrier["deadline"] <= now and barrier["operation_key"] == guard.operation_key:
                state.revision_barrier = None
                return RevisionApplication("waiting", "barrier_expired", live_attempt_ids=live)
            if barrier is not None and barrier["deadline"] <= now:
                state.revision_barrier = None
                barrier = None
            if barrier is not None and barrier["operation_key"] == guard.operation_key and (
                    barrier["source"] != guard.source_sha256 or barrier["target"] != guard.target_sha256):
                return _revision_refusal(state, guard.operation_key, "key_conflict")
            if guard.barrier_deadline <= now or guard.barrier_deadline > now + cfg.max_recovery_wait:
                return _revision_refusal(state, guard.operation_key, "invalid_guard")
            if barrier is not None and barrier["deadline"] > now and barrier["operation_key"] != guard.operation_key:
                return RevisionApplication("refused", "revision_pending", live_attempt_ids=live)
            if barrier is None:
                state.revision_barrier = {"operation_key": guard.operation_key, "source": guard.source_sha256,
                                          "target": guard.target_sha256, "deadline": guard.barrier_deadline,
                                          "accepted_map_digest": guard.accepted_map_digest,
                                          "accepted_map": accepted, "live_attempt_ids": list(live)}
                ctx = Ctx(old, cfg, tx, now)
                ctx.audit("revision_barrier", operation_key=guard.operation_key, source=guard.source_sha256,
                          target=guard.target_sha256, deadline=guard.barrier_deadline)
            return RevisionApplication("waiting", live_attempt_ids=live)
        barrier = state.revision_barrier
        if barrier is not None and barrier["deadline"] <= now and barrier["operation_key"] == guard.operation_key:
            state.revision_barrier = None
            return RevisionApplication("waiting", "barrier_expired")
        if barrier is not None and barrier["deadline"] > now and barrier["operation_key"] != guard.operation_key:
            return RevisionApplication("refused", "revision_pending")
        roots = set(guard.scope) | changed
        impacted = set(roots)
        for task_id in tuple(roots):
            for plan in (old, new):
                if task_id in plan.ids():
                    impacted.update(plan.descendants(task_id))
        removed = tuple(sorted(set(state.tasks) - set(new_by_id)))
        added = tuple(spec.id for spec in new.tasks if spec.id not in old_by_id)
        reset = tuple(spec.id for spec in new.tasks if spec.id in state.tasks and spec.id in impacted)
        kept = tuple(spec.id for spec in new.tasks if spec.id in state.tasks and spec.id not in impacted and
                     state.tasks[spec.id].state == T.COMPLETED.value)
        report = {"from_rev": old.revision, "to_rev": new.revision, "kept": list(kept), "reset": list(reset),
                  "added": list(added), "removed": list(removed)}
        for task_id in removed:
            for item in state.outbox:
                attempt = state.attempts.get(item.attempt_id)
                if item.status == "pending" and attempt is not None and attempt.task_id == task_id:
                    item.status = "void"
            del state.tasks[task_id]
        for task_id in reset:
            rec = state.tasks[task_id]
            before = rec.state
            state.tasks[task_id] = TaskRec(T.PENDING.value, attempts=list(rec.attempts), budget_base=rec.budget_base,
                                           hold_until=rec.hold_until, waits=rec.waits, reworks=rec.reworks)
            Ctx(new, cfg, tx, now).audit("task_transition", task_id, **{"from": before, "to": T.PENDING.value},
                                         reason="plan_revision", decision="plan_revision")
        for task_id in added:
            state.tasks[task_id] = TaskRec(T.PENDING.value)
        state.revision, state.plan_sha256 = new.revision, new.sha256
        state.routing_complete = False
        state.revision_applications[guard.operation_key] = {"source": guard.source_sha256,
            "target": guard.target_sha256, "report": report, "at": now}
        state.revision_applications = dict(list(state.revision_applications.items())[-200:])
        state.revision_barrier = None
        ctx = Ctx(new, cfg, tx, now)
        ctx.audit("revision_applied", key=guard.operation_key, from_rev=old.revision, to_rev=new.revision,
                  kept=list(kept), reset=list(reset), added=list(added), removed=list(removed))
        from .transitions import promote_ready
        promote_ready(ctx)
        return RevisionApplication("applied", report=report)


def fingerprint(spec: TaskSpec) -> str:
    """Hash of what the task asks for. Same fingerprint = the accepted work still satisfies the plan."""
    body = {"id": spec.id, "after": sorted(spec.after), "repository": spec.repository,
            "acceptance_criteria": list(spec.acceptance_criteria),
            "verification": [dict(item) for item in spec.verification]}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def content_fingerprint(spec: TaskSpec) -> str:
    """Hash of everything the task asks for EXCEPT where it sits in the graph: objective, scope (paths and resources),
    repository, acceptance criteria and checks. Unchanged = the accepted work still answers the same question."""
    body = {"id": spec.id, "repository": spec.repository, "objective": spec.meta.get("objective", ""),
            "expected_paths": sorted(spec.expected_paths), "shared_resources": sorted(spec.shared_resources),
            "acceptance_criteria": list(spec.acceptance_criteria), "verification": [dict(item) for item in spec.verification]}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def _refuse(why: str) -> SchedulerError:
    return SchedulerError("NOT_ALLOWED", f"cannot rebase: {why}")


JUDGES = frozenset({"test", "audit"})


def plan_rebase(state: RunState, old: Plan, new: Plan, *, cascade: bool = True) -> RebaseReport:
    """What a rebase would do (pure, writes nothing); raises SchedulerError when it must be refused."""
    if (state.plan_id, state.revision, state.plan_sha256) != (old.plan_id, old.revision, old.sha256):
        raise SchedulerError("PLAN_MISMATCH", f"the run is {state.plan_id} r{state.revision}, not the given old plan")
    if new.plan_id != old.plan_id:
        raise _refuse(f"{new.plan_id} is not {old.plan_id}")
    if new.revision <= old.revision:
        raise _refuse(f"revision {new.revision} is not later than r{old.revision}")
    if state.cancel_requested:
        raise _refuse("a cancellation was requested")
    live = [a.id for a in state.attempts.values() if A(a.state) in ATTEMPT_LIVE]
    if live:
        raise _refuse(f"attempts still alive ({', '.join(sorted(live)[:5])}): finish or cancel them first")
    old_prints = {spec.id: (fingerprint(spec) if cascade else content_fingerprint(spec)) for spec in old.tasks}
    reset_set: set[str] = set()
    kept: list[str] = []
    reset: list[str] = []
    added: list[str] = []
    kept_set: set[str] = set()
    for spec in _topological(new):          # prerequisites first, so a reset one is known before its dependents
        rec = state.tasks.get(spec.id)
        if rec is None:
            added.append(spec.id)
            reset_set.add(spec.id)
        elif cascade and (rec.state == T.COMPLETED.value and old_prints.get(spec.id) == fingerprint(spec)
                          and all(dep in kept_set for dep in spec.after)):
            kept.append(spec.id)
            kept_set.add(spec.id)
        elif not cascade and rec.state == T.COMPLETED.value and old_prints.get(spec.id) == content_fingerprint(spec) \
                and not (spec.meta.get("kind") in JUDGES and reset_set & set(new.ancestors(spec.id))):
            kept.append(spec.id)
            kept_set.add(spec.id)
        else:
            reset.append(spec.id)
            reset_set.add(spec.id)
    removed = sorted(set(state.tasks) - {spec.id for spec in new.tasks})
    order = {spec.id: index for index, spec in enumerate(new.tasks)}
    return RebaseReport(old.revision, new.revision, tuple(sorted(kept, key=order.get)),
                        tuple(sorted(reset, key=order.get)), tuple(sorted(added, key=order.get)), tuple(removed))


def _topological(plan: Plan) -> list[TaskSpec]:
    done: set[str] = set()
    out: list[TaskSpec] = []
    pending = list(plan.tasks)
    while pending:
        ready = [spec for spec in pending if all(dep in done for dep in spec.after)]
        if not ready:                 # a validated plan has no cycle; never loop forever on a damaged one
            raise SchedulerError("PLAN_UNREADABLE", "the dependency graph has a cycle")
        for spec in ready:
            out.append(spec)
            done.add(spec.id)
        pending = [spec for spec in pending if spec.id not in done]
    return out


def rebase_run(repository: StateRepository, old: Plan, new: Plan, *, config: Config | None = None,
               clock: Callable[[], float] = _now, cascade: bool = True) -> RebaseReport:
    """Move the persisted run from `old` to `new` (see the module docstring). All or nothing."""
    with repository.transaction() as tx:
        if tx.state is None:
            raise SchedulerError("NOT_ALLOWED", "cannot rebase: there is no run yet (just start one on the new plan)")
        state = tx.state
        report = plan_rebase(state, old, new, cascade=cascade)
        ctx = Ctx(new, config or Config(), tx, clock())
        for task_id in report.removed:
            for item in state.outbox:
                if item.status == "pending" and state.attempts.get(item.attempt_id) \
                        and state.attempts[item.attempt_id].task_id == task_id:
                    item.status = "void"
            del state.tasks[task_id]
        for task_id in report.reset:
            rec = state.tasks[task_id]
            before = rec.state
            state.tasks[task_id] = TaskRec(T.PENDING.value, attempts=list(rec.attempts), budget_base=len(rec.attempts))
            ctx.audit("task_transition", task_id, **{"from": before, "to": T.PENDING.value}, reason="rebase",
                      decision="rebase")
        for task_id in report.added:
            state.tasks[task_id] = TaskRec(T.PENDING.value)
        state.revision, state.plan_sha256 = new.revision, new.sha256
        state.routing_complete = False            # M2 plans the changed DAG again; kept tasks keep what they have
        ctx.audit("run_rebased", from_rev=report.from_revision, to_rev=report.to_revision, kept=list(report.kept),
                  reset=list(report.reset), added=list(report.added), removed=list(report.removed))
        from .transitions import promote_ready
        promote_ready(ctx)
    return report
