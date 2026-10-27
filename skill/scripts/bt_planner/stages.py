"""Stages (D-134): every approval freezes a *stage*, the projection of the draft onto a cumulative set of subplans S.

The working PLAN.json is always a draft. Approving subplans freezes revision N+1 = the draft projected onto S (the
subplans already approved plus the new ones), marked `stage: {"version": 1, "subplans": [...]}`; approving the whole
plan is the stage that holds every subplan and every task. Consumers see a complete, valid, hash-checked plan; a run
moves to a later stage with the usual rebase. A plan without subplans is one stage holding everything (no `stage`
field); a frozen revision without `stage` reads as the complete stage of its own content.

Projection of the draft onto S keeps:
- the tasks of the subplans in S;
- tasks without a subplan that are ancestors of a task of S, or whose subplan ancestors are all in S (at least one),
  or every task when S is every subplan of the draft;
- the milestones those tasks use, the requirements they (and the subplans of S) cover in plan order, the composition
  gates whose subplans are all in S and whose tasks are kept, the interfaces whose producer is kept (consumers filtered);
- every other top-level key as it is.

A kept task whose prerequisite is not kept is refused (`STAGE_NOT_CLOSED`). The planner owns the projection, its
validation and the drift gate; who may approve a stage (the owner's subplan confirmations) is the caller's.

Drift (the launch/join gate, `bind`): the draft projected onto the frozen stage's subplans must be exactly that
revision (`PLAN_DRIFT`), the PLAN.md lines of its tasks and milestones must be the approved ones (`PLAN_PROSE_DRIFT`)
and so must the SPEC requirement items it covers (`PLAN_REQUIREMENTS_DRIFT`). Edits outside the stage never matter.

Codes: STAGE_INVALID, STAGE_NOT_CLOSED, STAGE_NOT_CUMULATIVE, STAGE_INCOMPLETE, PLAN_NOT_FROZEN, PLAN_MISSING,
PLAN_INVALID, PLAN_DRIFT, PLAN_PROSE_DRIFT, PLAN_REQUIREMENTS_DRIFT.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Callable, Iterable
from pathlib import Path

from . import contract as pc
from . import markdown as md
from . import revisions as rev
from . import traceability

KEY = "stage"
VERSION = 1
_SUBPLAN = re.compile(r"SP-[1-9][0-9]*")


def stage_of(plan: object) -> dict | None:
    """The `stage` object of a plan document, or None for a whole-plan revision."""
    value = plan.get(KEY) if isinstance(plan, dict) else None
    return value if isinstance(value, dict) else None


def field_errors(plan: dict) -> list[str]:
    """Validation of the `stage` field itself (called by `contract.validate` only when the field is present)."""
    stage = plan.get(KEY)
    where = "plan.stage"
    if pc.schema_tuple(plan) < pc.SCHEMA_13:
        return [f"STAGE_INVALID: {where}: requires schema 1.3.0"]
    if not isinstance(stage, dict) or set(stage) != {"version", "subplans"}:
        return [f"STAGE_INVALID: {where}: must be {{version, subplans}}"]
    if type(stage["version"]) is not int or stage["version"] != VERSION:
        return [f"STAGE_INVALID: {where}.version: unsupported stage contract {stage['version']!r} (this reader: {VERSION})"]
    listed = stage["subplans"]
    if (not isinstance(listed, list) or not listed or not all(isinstance(x, str) and _SUBPLAN.fullmatch(x) for x in listed)
            or len(set(listed)) != len(listed)):
        return [f"STAGE_INVALID: {where}.subplans: a non-empty list of distinct SP-n ids"]
    declared = [s.get("id") for s in plan.get("subplans") or [] if isinstance(s, dict)] \
        if isinstance(plan.get("subplans"), list) else []
    errors = []
    if listed != declared:
        errors.append(f"STAGE_INVALID: {where}.subplans: {listed} must be exactly the subplans of this revision {declared}")
    for task in plan.get("tasks") or [] if isinstance(plan.get("tasks"), list) else []:
        if isinstance(task, dict) and task.get("subplan_id") is not None and task.get("subplan_id") not in listed:
            errors.append(f"STAGE_INVALID: {task.get('id')}: subplan {task.get('subplan_id')!r} is not in the stage")
    return errors


# ------------------------------------------------------------------ projection

def _dicts(value: object) -> list[dict]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def declared_subplans(plan: dict) -> list[str]:
    return [s["id"] for s in _dicts(plan.get("subplans")) if isinstance(s.get("id"), str)]


def _ancestors(tasks: dict[str, dict]) -> dict[str, set[str]]:
    memo: dict[str, set[str]] = {}

    def visit(tid: str, path: frozenset[str]) -> set[str]:
        if tid in memo:
            return memo[tid]
        found: set[str] = set()
        after = tasks[tid].get("after")
        for dep in after if isinstance(after, list) else []:
            if isinstance(dep, str) and dep in tasks and dep not in path:
                found.add(dep)
                found |= visit(dep, path | {dep})
        memo[tid] = found
        return found

    for tid in tasks:
        visit(tid, frozenset({tid}))
    return memo


def project(plan: object, subplans: Iterable[str]) -> dict:
    """The stage of `plan` for subplans S (see the module docstring). Pure; raises PlanContractError."""
    if not isinstance(plan, dict):
        raise pc.PlanContractError("STAGE_INVALID", ["PLAN.json must be an object"])
    declared = declared_subplans(plan)
    wanted = list(dict.fromkeys(subplans))
    if not declared:                       # no subplans: the plan is one stage, approved and run whole
        if wanted:
            raise pc.PlanContractError("STAGE_INVALID", [f"the draft declares no subplans (asked for {', '.join(wanted)})"])
        return {key: copy.deepcopy(value) for key, value in plan.items() if key != KEY}
    unknown = [sid for sid in wanted if sid not in declared]
    if not wanted or unknown:
        raise pc.PlanContractError("STAGE_INVALID", [(f"unknown subplan(s) {', '.join(unknown)}; the draft declares "
                                                     f"{', '.join(declared)}")] if unknown else ["a stage needs at least one subplan"])
    chosen = set(wanted)
    every = chosen == set(declared)
    rows = [t for t in _dicts(plan.get("tasks")) if isinstance(t.get("id"), str)]
    tasks = {t["id"]: t for t in rows}
    ancestors = _ancestors(tasks)
    members = {tid for tid, t in tasks.items() if t.get("subplan_id") in chosen}
    needed = set().union(*(ancestors[tid] for tid in members)) if members else set()
    kept = set(members)
    for tid, task in tasks.items():
        if task.get("subplan_id") is not None:
            continue
        upstream = {tasks[a].get("subplan_id") for a in ancestors[tid] if tasks[a].get("subplan_id") is not None}
        if tid in needed or every or (upstream and upstream <= chosen):
            kept.add(tid)
    missing = []
    for tid in sorted(kept):
        for dep in tasks[tid].get("after") or []:
            if isinstance(dep, str) and dep in tasks and dep not in kept:
                owner = tasks[dep].get("subplan_id")
                missing.append(f"{tid} needs {dep} ({owner or 'a plan-wide task'})"
                               + (f": add {owner} to the stage" if owner else ""))
    if missing:
        raise pc.PlanContractError("STAGE_NOT_CLOSED", missing)
    out = {key: copy.deepcopy(value) for key, value in plan.items()
           if key not in ("tasks", "milestones", "subplans", "composition_gates", "requirements", "interfaces", KEY)}
    out["tasks"] = [copy.deepcopy(t) for t in rows if t["id"] in kept]
    used = {t.get("milestone_id") for t in out["tasks"]}
    out["milestones"] = [copy.deepcopy(m) for m in _dicts(plan.get("milestones")) if m.get("id") in used]
    out["subplans"] = [copy.deepcopy(s) for s in _dicts(plan.get("subplans")) if s.get("id") in chosen]
    if "requirements" in plan:
        covered = {r for s in out["subplans"] for r in (s.get("covers") or []) if isinstance(r, str)}
        covered |= {r for t in out["tasks"] for r in (t.get("covers") or []) if isinstance(r, str)}
        raw = plan["requirements"]
        out["requirements"] = [r for r in raw if r in covered] if isinstance(raw, list) else copy.deepcopy(raw)
    if "composition_gates" in plan:
        out["composition_gates"] = [copy.deepcopy(g) for g in _dicts(plan.get("composition_gates"))
                                    if isinstance(g.get("subplans"), list) and set(g["subplans"]) <= chosen
                                    and g.get("task") in kept and g.get("audit_task", g.get("task")) in kept]
    if "interfaces" in plan:
        dropped: set[str] = set()
        interfaces = []
        for item in _dicts(plan.get("interfaces")):
            consumers = [c for c in item.get("consumer_tasks") or [] if c in kept] \
                if isinstance(item.get("consumer_tasks"), list) else []
            if item.get("producer_task") not in kept or not consumers:
                dropped.add(item.get("id"))
                continue
            kept_item = copy.deepcopy(item)
            kept_item["consumer_tasks"] = consumers
            if "integration_task" in kept_item and kept_item["integration_task"] not in kept:
                del kept_item["integration_task"]
            interfaces.append(kept_item)
        out["interfaces"] = interfaces
        for sp in out["subplans"]:
            for produced in _dicts(sp.get("produces")):
                if isinstance(produced.get("interfaces"), list):
                    produced["interfaces"] = [i for i in produced["interfaces"] if i not in dropped]
    out[KEY] = {"version": VERSION, "subplans": [sid for sid in declared if sid in chosen]}
    return out


def subplans_in(doc: dict) -> list[str]:
    """The subplans a frozen revision holds: its `stage`, or all of its own subplans for a whole revision."""
    stage = stage_of(doc)
    return list(stage["subplans"]) if stage else declared_subplans(doc)


def complete(plan: dict, projection: dict) -> bool:
    """The stage holds the whole draft: every subplan and every task."""
    return (set(subplans_in(projection)) == set(declared_subplans(plan))
            and {t.get("id") for t in _dicts(projection.get("tasks"))} == {t.get("id") for t in _dicts(plan.get("tasks"))})


def _as_revision(projection: dict, revision: int) -> dict:
    out = dict(projection)
    out["revision"] = revision
    return out


def differences(frozen: dict, projection: dict) -> list[str]:
    """What differs between a frozen stage and the draft's projection onto the same subplans (empty = no drift)."""
    out = []
    old = {t.get("id"): t for t in _dicts(frozen.get("tasks"))}
    new = {t.get("id"): t for t in _dicts(projection.get("tasks"))}
    for tid in sorted(old.keys() - new.keys()):
        out.append(f"{tid}: removed from the draft")
    for tid in sorted(new.keys() - old.keys()):
        out.append(f"{tid}: added to an approved subplan")
    for tid in sorted(old.keys() & new.keys()):
        if pc.dumps({"schema_version": "1.3.0", "tasks": [old[tid]]}) != pc.dumps({"schema_version": "1.3.0", "tasks": [new[tid]]}):
            out.append(f"{tid}: changed")
    olds = {s.get("id"): s for s in _dicts(frozen.get("subplans"))}
    for s in _dicts(projection.get("subplans")):
        if json.dumps(olds.get(s.get("id")), sort_keys=True) != json.dumps(s, sort_keys=True):
            out.append(f"{s.get('id')}: subplan definition changed")
    if not out:
        out.append("plan-level fields of the stage changed (milestones, requirements, gates, interfaces or other keys)")
    return out


# ------------------------------------------------------------------ approval-time pins

def requirements_digest(directory: Path, plan: dict, *, all_requirements: bool = False) -> str:
    """Digest of the SPEC requirement items the stage covers (an edit to one of them is an edit to approved scope)."""
    root = Path(directory).resolve()
    try:
        target = (root / str(plan.get("spec_ref") or "SPEC.md")).resolve()
        text = target.read_text(encoding="utf-8") if target.is_relative_to(root) and target.is_file() else ""
    except (OSError, UnicodeError, ValueError):
        text = ""
    items = traceability.requirement_items_from_spec(text) or {}
    ids = sorted(items) if all_requirements else [r for r in plan.get("requirements") or [] if isinstance(r, str)]
    body = json.dumps({rid: items.get(rid) for rid in ids}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def plan_md_digest(directory: Path, plan: dict) -> str:
    """Digest of the PLAN.md task lines and milestone headings of the stage's own tasks (other lines may change)."""
    doc = md.read_document(Path(directory) / "PLAN.md")
    ids = {t.get("id") for t in _dicts(plan.get("tasks"))}
    milestones = {m.get("id") for m in _dicts(plan.get("milestones"))}
    tasks = sorted(({k: v for k, v in t.items() if k not in ("line", "done")} for t in doc["tasks"] if t["id"] in ids),
                   key=lambda t: t["id"])
    stones = sorted(({"id": m["id"], "title": m["title"]} for m in doc["milestones"] if m["id"] in milestones),
                    key=lambda m: m["id"])
    body = json.dumps({"tasks": tasks, "milestones": stones}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


# ------------------------------------------------------------------ the revision store

def latest(directory: Path) -> tuple[dict, dict] | None:
    """(manifest entry, document) of the latest frozen revision; None when nothing is frozen. Store damage raises."""
    last = rev.latest(directory)
    return (last, rev.load_revision(directory, last["revision"])) if last else None


def _pins(directory: Path) -> tuple[dict, dict] | None:
    """The newest manifest entry that carries approval pins (a stage freeze) and its document."""
    for entry in reversed(rev.list_revisions(directory)):
        if isinstance(entry.get(KEY), dict):
            return entry, rev.load_revision(directory, entry["revision"])
    return None


def bind(directory: Path, draft: object) -> dict:
    """The launch/join gate: the draft projected onto the latest frozen stage's subplans is exactly that revision, and
    the PLAN.md lines and SPEC requirement items it was approved with are unchanged. Edits outside the stage never
    matter. Returns the latest manifest entry."""
    found = latest(directory)
    if not found:
        raise pc.PlanContractError("PLAN_NOT_FROZEN", [
            "nothing was approved: approve subplans (`stage run`) or the plan (`plan approve`) first"])
    entry, frozen = found
    if not isinstance(draft, dict):
        raise pc.PlanContractError("PLAN_INVALID", ["PLAN.json cannot be read (it may be being written); retry"])
    try:
        projection = project(draft, subplans_in(frozen))
    except pc.PlanContractError as exc:
        raise pc.PlanContractError("PLAN_DRIFT", [(f"the approved stage r{entry['revision']} cannot be rebuilt from the "
                                                  f"draft ({exc.code})"), *exc.issues]) from exc
    if pc.dumps(_as_revision(projection, entry["revision"])) != pc.dumps(_as_revision(frozen, entry["revision"])):
        raise pc.PlanContractError("PLAN_DRIFT", [*differences(frozen, projection)[:8],
                                                  (f"approved scope of r{entry['revision']} changed: re-confirm the "
                                                  "subplan and approve a new stage, or restore it in PLAN.json")])
    pinned = _pins(directory)
    if pinned:
        pins, doc = pinned[0][KEY], pinned[1]
        if pins.get("plan_md_sha256") and plan_md_digest(directory, doc) != pins["plan_md_sha256"]:
            raise pc.PlanContractError("PLAN_PROSE_DRIFT", [
                f"PLAN.md lines of the tasks approved in r{pinned[0]['revision']} changed since; approve a new stage"])
        if pins.get("requirements_sha256") and requirements_digest(directory, doc, all_requirements=bool(pins.get("complete"))) != pins["requirements_sha256"]:
            raise pc.PlanContractError("PLAN_REQUIREMENTS_DRIFT", [
                f"a SPEC requirement covered by r{pinned[0]['revision']} changed since it was approved; approve a new stage"])
    return entry


def approval_pins(directory: Path, draft: dict, projection: dict) -> dict:
    """Approval identity includes covered prose/SPEC and the scope still outside the stage."""
    return {"subplans": subplans_in(projection),
            "pending_subplans": [s for s in declared_subplans(draft) if s not in subplans_in(projection)],
            "complete": complete(draft, projection),
            "requirements_sha256": requirements_digest(directory, projection, all_requirements=complete(draft, projection)),
            "plan_md_sha256": plan_md_digest(directory, projection)}


def freeze(directory: Path, subplans: Iterable[str], draft: dict, report_for, *, require_complete: bool = False,
           ledger_command: str = "engine audit-ledger check", before_freeze: Callable[[], None] | None = None) -> dict:
    """Freeze the next stage: S = the subplans already approved plus `subplans`. `report_for(projection)` is the
    caller's publication check of the projection (a `contract.Report`). Idempotent when the projection is the latest
    revision (the same entry is returned). `require_complete` (approving the whole plan) refuses a stage short of the draft."""
    found = latest(directory)
    previous = subplans_in(found[1]) if found else []
    gone = [sid for sid in previous if sid not in declared_subplans(draft)]
    if gone:
        raise pc.PlanContractError("STAGE_NOT_CUMULATIVE", [
            f"{', '.join(gone)} were approved in r{found[0]['revision']} but are no longer in the draft; a stage only grows"])
    projection = project(draft, [*previous, *subplans])
    if require_complete and not complete(draft, projection):
        missing = [sid for sid in declared_subplans(draft) if sid not in subplans_in(projection)]
        raise pc.PlanContractError("STAGE_INCOMPLETE", [
            "approving the plan needs the whole draft in one stage" + (f"; missing {', '.join(missing)}" if missing else
                                                                      "; some tasks depend on nothing approved")])
    pins = approval_pins(directory, draft, projection)
    unchanged = (found and pc.dumps(_as_revision(projection, found[0]["revision"])) == pc.dumps(found[1])
                 and found[0].get(KEY) == pins)
    projection = _as_revision(projection, found[0]["revision"] if unchanged else ((found[0]["revision"] + 1) if found else 1))
    report = report_for(projection)
    if not report.ok:
        raise pc.PlanContractError("PLAN_INVALID", report.errors)
    if before_freeze is not None:
        before_freeze()
    if unchanged:
        return found[0]
    return rev.freeze(directory, projection, "approval", ledger_command=ledger_command, extra={KEY: pins})


def spec_ids_for(projection: dict, spec_ids: set[str] | None) -> tuple[set[str] | None, list[str]]:
    """SPEC ids restricted to the stage, plus errors for stage requirements SPEC does not declare."""
    if spec_ids is None:
        return None, []
    own = {r for r in projection.get("requirements") or [] if isinstance(r, str)}
    return spec_ids & own, [f"requirements: {r} is declared in the stage but missing from SPEC Requirements"
                            for r in sorted(own - spec_ids)]


def splice(draft: dict, old: dict, new: dict) -> dict:
    """Carry a revision the scheduler made from stage `old` (healing, remediation, recovery) into the draft, so the draft's
    projection is `new`: changed and added tasks, removed tasks and the stage's subplan objects. Other draft content
    is kept. Raises STAGE_INVALID when the draft no longer holds the stage."""
    out = copy.deepcopy(draft)
    tasks = [t for t in _dicts(out.get("tasks"))]
    old_ids = {t.get("id") for t in _dicts(old.get("tasks"))}
    new_tasks = [t for t in _dicts(new.get("tasks"))]
    new_ids = {t.get("id") for t in new_tasks}
    by_id = {t.get("id"): t for t in new_tasks}
    result = [copy.deepcopy(by_id[t.get("id")]) if t.get("id") in by_id else t for t in tasks
              if not (t.get("id") in old_ids and t.get("id") not in new_ids)]
    present = {t.get("id") for t in result}
    for index, task in enumerate(new_tasks):
        if task.get("id") in present:
            continue
        before = next((new_tasks[i].get("id") for i in range(index - 1, -1, -1) if new_tasks[i].get("id") in present), None)
        at = next((i + 1 for i, t in enumerate(result) if t.get("id") == before), 0)
        result.insert(at, copy.deepcopy(task))
        present.add(task.get("id"))
    out["tasks"] = result
    stage_subplans = {s.get("id"): s for s in _dicts(new.get("subplans"))}
    if not set(stage_subplans) <= set(declared_subplans(out)):
        raise pc.PlanContractError("STAGE_NOT_CUMULATIVE", ["the draft no longer declares every subplan of the run"])
    out["subplans"] = [copy.deepcopy(stage_subplans[s.get("id")]) if s.get("id") in stage_subplans else s
                       for s in _dicts(out.get("subplans"))]
    out.pop(KEY, None)
    out["revision"] = new.get("revision", out.get("revision"))     # informative: the store numbers revisions
    return out


def summary(directory: Path) -> dict:
    """Read-only view for people: every approved stage with its subplans and whether it held the whole draft."""
    rows = []
    for entry in rev.list_revisions(directory):
        pins = entry.get(KEY)
        if isinstance(pins, dict):
            rows.append({"revision": entry["revision"], "frozen_at": entry.get("frozen_at"),
                         "subplans": list(pins.get("subplans") or []),
                         "pending_subplans": list(pins.get("pending_subplans") or []),
                         "complete": bool(pins.get("complete"))})
    return {"stages": rows, "complete": bool(rows) and rows[-1]["complete"]}
