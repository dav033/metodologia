"""The rules behind the plan contract (bt_contracts.plan): value grammars the field types apply, and the identity and
reference checks across a shape-valid plan. Kept apart so the models read as the schema they generate.
"""
from __future__ import annotations

import json
import re
from collections.abc import Iterable
from typing import Any

EVIDENCE_KINDS = ("file", "command", "precedent", "spec", "task", "assumption")
SECRET_URL = re.compile(r"https?://[^/@\s]+:[^/@\s]+@")
SECRET_PAIR = re.compile(r"\b(?:token|password|secret)\s*:\s*\S+", re.IGNORECASE)
_DRIVE = re.compile(r"^[A-Za-z]:")


# ---------------------------------------------------------------------------------------------------- value grammars

def nonblank(value: str) -> str:
    if not value.strip():
        raise ValueError("must be non-blank text")
    return value


def relative_path(value: str) -> str:
    """The planner's rule for paths inside a repository or the requirement folder (no absolute, drive or `..`)."""
    path = value.replace("\\", "/")
    if "\0" in path or path.startswith("/") or _DRIVE.match(path) or ".." in path.split("/"):
        raise ValueError("must be a relative path without '..'")
    return value


def generated_path(value: str) -> str:
    if (not 1 <= len(value) <= 1024 or value != value.strip() or value.startswith("/") or "\\" in value
            or ":" in value or any(ord(c) < 32 for c in value)
            or any(part in ("", ".", "..") for part in value.split("/"))):
        raise ValueError("a relative path/glob of 1..1024 characters without empty, '.' or '..' components, "
                         "backslashes, colons or control characters")
    return value


def command(value: str) -> str:
    if not value.strip() or len(value) > 4096 or "\0" in value:
        raise ValueError("a non-empty command of at most 4096 characters")
    return value


def evidence_ref(value: str) -> str:
    kind, sep, rest = value.partition(":")
    if not sep or kind.strip().lower() not in EVIDENCE_KINDS or not rest.strip():
        raise ValueError(f"must look like kind:value with kind in {', '.join(EVIDENCE_KINDS)}")
    return value


def _reject_constant(name: str):
    raise ValueError(f"non-standard JSON constant {name}")


def _no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    seen: dict[str, object] = {}
    for key, value in pairs:
        if key in seen:
            raise ValueError(f"duplicate key {key!r} (the later value would silently win)")
        seen[key] = value
    return seen


def strict_json(text: str) -> object:
    """json.loads that refuses NaN/Infinity and duplicate keys, as the planner's reader does."""
    return json.loads(text, parse_constant=_reject_constant, object_pairs_hook=_no_duplicate_keys)


# ---------------------------------------------------------------------------------------------------- references

def _duplicates(values: Iterable[str]) -> list[str]:
    seen, twice = set(), []
    for value in values:
        if value in seen and value not in twice:
            twice.append(value)
        seen.add(value)
    return twice


def _cycle(edges: dict[str, list[str]]) -> list[str]:
    """One dependency cycle as a list of ids, or [] (iterative three-colour DFS: plans may be deep)."""
    colour: dict[str, int] = {}
    for root, deps in edges.items():
        if colour.get(root):
            continue
        colour[root], path, stack = 1, [root], [(root, iter(deps))]
        while stack:
            node, children = stack[-1]
            for child in children:
                if colour.get(child) == 1:
                    return path[path.index(child):] + [child]
                if not colour.get(child):
                    colour[child] = 1
                    path.append(child)
                    stack.append((child, iter(edges[child])))
                    break
            else:
                colour[node] = 2
                path.pop()
                stack.pop()
    return []


def reference_issues(plan: Any) -> list[str]:
    """Identity and reference rules across the plan (a shape-valid plan is assumed). [] when consistent."""
    out: list[str] = []
    milestones = [m.id for m in plan.milestones]
    out += [f"milestones: duplicate milestone id {mid}" for mid in _duplicates(milestones)]
    task_ids = [t.id for t in plan.tasks]
    out += [f"tasks: duplicate task id {tid}" for tid in _duplicates(task_ids)]
    tasks, known_milestones = set(task_ids), set(milestones)
    requirements = getattr(plan, "requirements", None)
    if requirements is not None:
        out += [f"requirements: duplicate requirement id {rid}" for rid in _duplicates(requirements)]
    declared = set(requirements or ())
    subplans = getattr(plan, "subplans", [])
    subplan_ids = {s.id for s in subplans}
    edges: dict[str, list[str]] = {}
    for task in plan.tasks:
        where = task.id
        if task.milestone_id not in known_milestones:
            out.append(f"{where}.milestone_id: {task.milestone_id!r} is not a milestone of this plan")
        out += [f"{where}.after: duplicate prerequisite {dep}" for dep in _duplicates(task.after)]
        for dep in dict.fromkeys(task.after):
            if dep == task.id:
                out.append(f"{where}.after: a task cannot depend on itself")
            elif dep not in tasks:
                out.append(f"{where}.after: {dep!r} is not a task of this plan")
            else:
                edges.setdefault(task.id, []).append(dep)
        for index, check in enumerate(task.verification):
            if check.created_by is not None and check.created_by not in tasks:
                out.append(f"{where}.verification[{index}].created_by: {check.created_by!r} is not a task of this plan")
        covers = getattr(task, "covers", None)
        if covers is not None:
            out += [f"{where}.covers: duplicate requirement {rid}" for rid in _duplicates(covers)]
            out += [f"{where}.covers: {rid} is not declared in requirements" for rid in dict.fromkeys(covers)
                    if rid not in declared]
        subplan_id = getattr(task, "subplan_id", None)
        if subplan_id is not None and subplan_id not in subplan_ids:
            out.append(f"{where}.subplan_id: {subplan_id!r} is not a subplan of this plan")
    for tid in tasks:
        edges.setdefault(tid, [])
    cycle = _cycle(edges) if len(_duplicates(task_ids)) == 0 else []
    if cycle:
        out.append("tasks: dependency cycle " + " -> ".join(cycle))
    interfaces = getattr(plan, "interfaces", [])
    out += [f"interfaces: duplicate interface id {iid}" for iid in _duplicates(i.id for i in interfaces)]
    for interface in interfaces:
        where = interface.id
        named = [("producer_task", interface.producer_task)]
        named += [(f"consumer_tasks[{n}]", tid) for n, tid in enumerate(interface.consumer_tasks)]
        if interface.integration_task is not None:
            named.append(("integration_task", interface.integration_task))
        out += [f"{where}.{field}: {tid!r} is not a task of this plan" for field, tid in named if tid not in tasks]
    out += _subplan_issues(plan, tasks, known_milestones, declared, {i.id for i in interfaces})
    return out


def _subplan_issues(plan: Any, tasks: set[str], milestones: set[str], requirements: set[str],
                    interfaces: set[str]) -> list[str]:
    subplans = getattr(plan, "subplans", [])
    gates = getattr(plan, "composition_gates", [])
    out = [f"subplans: duplicate subplan id {sid}" for sid in _duplicates(s.id for s in subplans)]
    out += [f"composition_gates: duplicate gate id {gid}" for gid in _duplicates(g.id for g in gates)]
    subplan_ids = {s.id for s in subplans}
    produced: dict[tuple[str, int], str] = {}
    for subplan in subplans:
        for item in subplan.produces:
            key = (item.contract, item.version)
            if key in produced:
                out.append(f"{subplan.id}.produces: {item.contract}@{item.version} is already produced by {produced[key]}")
            else:
                produced[key] = subplan.id
    for subplan in subplans:
        where = subplan.id
        if subplan.milestone_id not in milestones:
            out.append(f"{where}.milestone_id: {subplan.milestone_id!r} is not a milestone of this plan")
        out += [f"{where}.covers: {rid} is not declared in requirements" for rid in subplan.covers
                if rid not in requirements]
        named = [("integration_test_task", subplan.integration_test_task), ("audit_task", subplan.audit_task)]
        named += [(f"checkpoints[{n}].task", c.task) for n, c in enumerate(subplan.checkpoints)]
        named += [(f"produces[{n}].defined_by", p.defined_by) for n, p in enumerate(subplan.produces)]
        named += [(f"consumes[{n}].verified_by", tid) for n, c in enumerate(subplan.consumes) for tid in c.verified_by]
        if subplan.ui is not None:
            named += [("ui.design_task", subplan.ui.design_task), ("ui.visual_review_task", subplan.ui.visual_review_task)]
        out += [f"{where}.{field}: {tid!r} is not a task of this plan" for field, tid in named if tid not in tasks]
        for n, item in enumerate(subplan.produces):
            out += [f"{where}.produces[{n}].interfaces: {iid} is not an interface of this plan"
                    for iid in item.interfaces if iid not in interfaces]
        for n, item in enumerate(subplan.consumes):
            if item.from_ == "external":
                continue
            if item.from_ not in subplan_ids:
                out.append(f"{where}.consumes[{n}].from: {item.from_} is not a subplan of this plan")
            elif produced.get((item.contract, item.version)) != item.from_:
                out.append(f"{where}.consumes[{n}]: {item.from_} does not produce {item.contract}@{item.version}")
    for gate in gates:
        where = gate.id
        out += [f"{where}.subplans: {sid} is not a subplan of this plan" for sid in gate.subplans
                if sid not in subplan_ids]
        named = [("task", gate.task)] + ([("audit_task", gate.audit_task)] if gate.audit_task is not None else [])
        out += [f"{where}.{field}: {tid!r} is not a task of this plan" for field, tid in named if tid not in tasks]
    stage = getattr(plan, "stage", None)
    if stage is not None and stage.subplans != [s.id for s in subplans]:
        out.append(f"stage.subplans: {stage.subplans} must be exactly the subplans of this revision "
                   f"{[s.id for s in subplans]}")
    return out
