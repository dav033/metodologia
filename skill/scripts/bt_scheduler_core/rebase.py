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
