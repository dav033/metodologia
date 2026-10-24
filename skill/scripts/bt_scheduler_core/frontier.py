"""M1-owned application of an explicit, evidence-bound M5 composition frontier."""
from __future__ import annotations

import re
from typing import Any

from .errors import SchedulerError
from .states import ATTEMPT_LIVE
from .states import AttemptState as A
from .states import TaskState as T
from .subplans import composition_members_current
from .transitions import Ctx, live_attempt, set_task

_ACTIONS = {"none", "reverify", "reintegrate", "audit", "adapt_contract", "modify", "reimplement"}
_EVIDENCE = re.compile(r"[a-z][a-z0-9_-]{0,31}:[0-9a-f]{64}")
_DIGEST = re.compile(r"[0-9a-f]{64}")
_TREE = re.compile(r"[0-9a-f]{40,64}")


def apply_demonstrated_frontier(ctx: Ctx, *, change_id: str, source_task_id: str, composition_id: str,
                                manifest_sha256: str, tree_digest: str, action: str,
                                task_ids: tuple[str, ...], evidence_refs: tuple[str, ...],
                                allow_prior_frontier: bool = False) -> tuple[str, ...]:
    """Apply exactly the named tasks. This deliberately does not traverse the dependency graph."""
    if (not isinstance(change_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", change_id) or
            not isinstance(source_task_id, str) or not isinstance(composition_id, str) or
            not isinstance(manifest_sha256, str) or not _DIGEST.fullmatch(manifest_sha256) or
            not isinstance(tree_digest, str) or not _TREE.fullmatch(tree_digest) or
            not isinstance(action, str) or action not in _ACTIONS or not isinstance(task_ids, tuple) or len(task_ids) > 128 or
            len(task_ids) != len(set(task_ids)) or not isinstance(evidence_refs, tuple) or
            not 1 <= len(evidence_refs) <= 32 or len(evidence_refs) != len(set(evidence_refs)) or
            any(not isinstance(ref, str) or not _EVIDENCE.fullmatch(ref) for ref in evidence_refs)):
        raise SchedulerError("CONTRACT_VIOLATION", "demonstrated frontier identity is malformed")
    plan, state = ctx.plan, ctx.state
    if plan.schema_version != "1.3.0" or not plan.subplans:
        raise SchedulerError("NOT_ALLOWED", "demonstrated frontier requires a 1.3.0 subplan plan")
    gate = next((item for item in plan.composition_gates if item.task == source_task_id), None)
    if gate is None:
        raise SchedulerError("NOT_ALLOWED", "frontier source must be a declared composition gate")
    if (action == "none") != (not task_ids):
        raise SchedulerError("CONTRACT_VIOLATION", "none action requires an empty frontier and other actions require tasks")
    if source_task_id in task_ids or any(task_id not in state.tasks for task_id in task_ids):
        raise SchedulerError("CONTRACT_VIOLATION", "frontier tasks must be declared tasks other than the source gate")
    if task_ids != tuple(task_id for task_id in plan.ids() if task_id in set(task_ids)):
        raise SchedulerError("CONTRACT_VIOLATION", "frontier tasks must be unique and in plan order")
    identity = {"source_task_id": source_task_id, "composition_id": composition_id,
                "manifest_sha256": manifest_sha256, "tree_digest": tree_digest,
                "action": action, "task_ids": list(task_ids), "evidence_refs": list(evidence_refs),
                "plan_id": state.plan_id, "revision": state.revision}
    previous = state.frontier_applications.get(change_id)
    if previous is not None:
        if {key: previous.get(key) for key in identity} != identity:
            raise SchedulerError("NOT_ALLOWED", "change_id was already applied with a different proof")
        return tuple(previous["applied_task_ids"])
    fact = state.compositions.get(composition_id)
    current_fact = (fact is not None and fact.get("plan_id") == state.plan_id and
                    fact.get("revision") == state.revision and fact.get("state") == "published" and
                    fact.get("manifest_sha256") == manifest_sha256 and fact.get("tree_digest") == tree_digest and
                    set(fact.get("members", {})) == set(gate.subplans) and
                    composition_members_current(plan, state, fact.get("members", {})))
    continuation = allow_prior_frontier and any(
        prior.get("source_task_id") == source_task_id and prior.get("composition_id") == composition_id and
        prior.get("manifest_sha256") == manifest_sha256 and prior.get("tree_digest") == tree_digest and
        prior.get("evidence_refs") == list(evidence_refs) and prior.get("plan_id") == state.plan_id and
        prior.get("revision") == state.revision
        for prior in state.frontier_applications.values())
    if not current_fact and not continuation:
        raise SchedulerError("NOT_ALLOWED", "frontier proof is not bound to the current published composition")
    if state.cancel_requested:
        raise SchedulerError("NOT_ALLOWED", "cannot apply a frontier to a cancelled run")
    # Reject the whole operation before changing anything. In particular, VERIFYING attempts are still live.
    for task_id in task_ids:
        rec = state.tasks[task_id]
        attempt = live_attempt(state, task_id)
        if attempt is not None and A(attempt.state) in ATTEMPT_LIVE:
            raise SchedulerError("NOT_ALLOWED", f"frontier task has a live attempt: {task_id}")
        if rec.state == T.CANCELLED.value:
            raise SchedulerError("NOT_ALLOWED", f"frontier task is cancelled: {task_id}")
    applied: list[str] = []
    for task_id in task_ids:
        rec = state.tasks[task_id]
        if rec.state == T.PENDING.value:
            continue
        if rec.state not in {T.READY.value, T.BLOCKED.value, T.RECOVERING.value, T.COMPLETED.value}:
            raise SchedulerError("NOT_ALLOWED", f"frontier task cannot be reset from {rec.state}: {task_id}")
        rec.budget_base = sum(state.attempts[attempt_id].budget_consumed for attempt_id in rec.attempts)
        rec.reason, rec.hold_until, rec.waits = "", 0.0, 0
        if rec.state == T.COMPLETED.value:
            rec.reworks += 1
        set_task(ctx, task_id, T.PENDING, by="M5-demonstrated-frontier", reason=action,
                 decision="demonstrated_frontier")
        applied.append(task_id)
    ctx.audit("demonstrated_frontier_applied", task_id=source_task_id, change_id=change_id,
              composition_id=composition_id, manifest_sha256=manifest_sha256, tree_digest=tree_digest,
              action=action, tasks=list(task_ids), applied_task_ids=applied, evidence_refs=list(evidence_refs))
    state.frontier_applications[change_id] = {**identity, "applied_task_ids": applied}
    return tuple(applied)


def apply_to_scheduler(scheduler, **proof) -> tuple[str, ...]:
    moved = scheduler.write(lambda ctx: apply_demonstrated_frontier(ctx, **proof))
    scheduler._wake.set()
    return moved


def apply_batch_to_scheduler(scheduler, applications: tuple[dict, ...]) -> tuple[str, ...]:
    if not isinstance(applications, tuple) or not applications:
        raise SchedulerError("CONTRACT_VIOLATION", "M5 frontier batch must be a nonempty tuple")

    def apply(ctx):
        moved = []
        required = {"change_id", "source_task_id", "composition_id", "manifest_sha256", "tree_digest",
                    "action", "frontier", "evidence_refs"}
        for proof in applications:
            if not isinstance(proof, dict) or set(proof) != required:
                raise SchedulerError("CONTRACT_VIOLATION", "M5 frontier batch entry is malformed")
            values = dict(proof)
            values["task_ids"] = values.pop("frontier")
            moved.extend(apply_demonstrated_frontier(ctx, **values, allow_prior_frontier=True))
        return tuple(moved)

    result = scheduler.write(apply)
    scheduler._wake.set()
    return result
