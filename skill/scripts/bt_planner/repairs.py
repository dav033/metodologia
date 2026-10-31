"""Bounded repairs (D-241): a draft change to an approved stage that only adds the repair of a confirmed defect.

The owner's rule (2026-10-30): «a bounded repair of a confirmed defect that changes no acceptance criteria or gates
needs no owner reconfirmation». This module decides, mechanically and with no knowledge of who confirms, whether the
draft projected onto the latest frozen stage's subplans differs from that frozen revision only by such a repair:

- tasks are only added, never removed; each new task is `implement` or `test`, belongs to a subplan the stage already
  holds, is not a UI task (the approved design stays as it is) and is a prerequisite (directly or through other new
  tasks) of at least one approved task, the one that found the defect: a new task nothing waits for is new scope;
- an approved task keeps every field as frozen (objective, acceptance criteria, verification, expected paths, kind,
  covers, ...) except `after`, which may only gain new tasks: it still waits, directly or through a new task, for
  everything it waited for, and never for an approved task it did not wait for;
- a subplan keeps its definition except `checkpoints`, which may only gain entries (a subplan past eight tasks must
  declare one);
- every plan-level field of the stage (milestones, covered requirements, composition gates, interfaces, ...) is as
  frozen.

Which evidence confirms the defect, and who may then keep the confirmations, is the caller's.
"""
from __future__ import annotations

import json

from . import contract as pc
from . import stages

REPAIR_KINDS = ("implement", "test")
_PLAN_LEVEL_SKIP = ("tasks", "subplans", "revision", stages.KEY)


def _dicts(value: object) -> list[dict]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _same(a: object, b: object) -> bool:
    return json.dumps(a, sort_keys=True, ensure_ascii=False) == json.dumps(b, sort_keys=True, ensure_ascii=False)


def _ids(value: object) -> list[str]:
    return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []


def classify(frozen: dict, draft: object) -> dict:
    """Whether `draft`, projected onto the subplans of the frozen stage `frozen`, is `frozen` plus a bounded repair.

    Returns {"bounded": bool, "reasons": [why not], "added": [new task ids], "detectors": [approved tasks that now wait
    for them], "subplans": [subplans the repair touches]}. Pure; never raises for a malformed draft."""
    out: dict = {"bounded": False, "reasons": [], "added": [], "detectors": [], "subplans": []}
    held = stages.subplans_in(frozen)
    try:
        projection = stages.project(draft, held)
    except pc.PlanContractError as exc:
        out["reasons"] = [f"the approved stage cannot be rebuilt from the draft ({exc.code}: {'; '.join(exc.issues[:3])})"]
        return out
    reasons: list[str] = []
    old = {t.get("id"): t for t in _dicts(frozen.get("tasks"))}
    new = {t.get("id"): t for t in _dicts(projection.get("tasks"))}
    reasons += [f"{tid}: removed" for tid in sorted(old.keys() - new.keys(), key=str)]
    added = [tid for tid in new if tid not in old]
    touched: list[str] = []
    detectors = []
    ancestors = stages._ancestors(new)
    for tid in [t for t in old if t in new]:
        before, after = old[tid], new[tid]
        fields = sorted(k for k in set(before) | set(after) if k != "after" and not _same(before.get(k), after.get(k)))
        if fields:
            reasons.append(f"{tid}: approved task changed ({', '.join(fields)})")
        was, now = _ids(before.get("after")), _ids(after.get("after"))
        if (lost := [d for d in was if d not in ancestors.get(tid, set())]):
            reasons.append(f"{tid}: approved task no longer waits for {', '.join(lost)}")
        gained = [d for d in now if d not in was]
        if (wrong := [d for d in gained if d not in added]):
            reasons.append(f"{tid}: approved task now waits for approved task(s) {', '.join(wrong)}")
        if gained:
            detectors.append(tid)
            touched.append(after.get("subplan_id"))
    for tid in added:
        task = new[tid]
        if task.get("kind") not in REPAIR_KINDS:
            reasons.append(f"{tid}: a repair task is {' or '.join(REPAIR_KINDS)}, not {task.get('kind')!r}")
        if task.get("subplan_id") not in held:
            reasons.append(f"{tid}: outside the approved subplans")
        if task.get("ui") is True:
            reasons.append(f"{tid}: a UI task changes the approved design")
        if not any(tid in ancestors.get(o, set()) for o in old if o in new):
            reasons.append(f"{tid}: no approved task waits for it (new scope, not a repair)")
        touched.append(task.get("subplan_id"))
    frozen_subplans = {s.get("id"): s for s in _dicts(frozen.get("subplans"))}
    for sp in _dicts(projection.get("subplans")):
        was = frozen_subplans.get(sp.get("id"), {})
        fields = sorted(k for k in set(was) | set(sp) if k != "checkpoints" and not _same(was.get(k), sp.get(k)))
        if fields:
            reasons.append(f"{sp.get('id')}: subplan definition changed ({', '.join(fields)})")
        old_points, new_points = _dicts(was.get("checkpoints")), _dicts(sp.get("checkpoints"))
        if any(not any(_same(p, q) for q in new_points) for p in old_points):
            reasons.append(f"{sp.get('id')}: a checkpoint was changed or removed")
        elif len(new_points) != len(old_points):
            touched.append(sp.get("id"))
    for key in sorted((set(frozen) | set(projection)) - set(_PLAN_LEVEL_SKIP)):
        if not _same(frozen.get(key), projection.get(key)):
            reasons.append(f"plan-level {key} of the stage changed")
    if not added and not reasons:
        reasons.append("no task was added: there is no repair to keep the confirmation for")
    out.update(bounded=not reasons, reasons=reasons, added=added, detectors=detectors,
               subplans=[s for s in dict.fromkeys(touched) if isinstance(s, str)])
    return out
