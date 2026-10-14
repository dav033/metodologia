"""PLAN.md <-> PLAN.json for one plan directory: skeleton derivation, consistency by ids/milestones/dependencies,
approval freeze, and a read-only compatibility report for plans written before the contract existed.

PLAN.json owns the classification; PLAN.md stays the human narrative. Only identifiers, milestone membership and
`after` links are compared (never free prose). Nothing here invents classification values; the only files written are
PLAN.json (init) and `plan-revisions/` (freeze).
"""
from __future__ import annotations

import re
from pathlib import Path

from . import contract as pc
from . import markdown as md
from . import revisions as rev

PLAN_MD = "PLAN.md"
PLAN_JSON = "PLAN.json"
DEFAULT_SPEC_REF = "SPEC.md"
APPROVED_STATES = ("approved", "launched", "done", "merged")  # PLAN.md `status:` words that allow a freeze


def default_plan_id(directory: Path) -> str:
    """`REQ-042-some-slug` -> `REQ-042`; any other directory name is used as it is."""
    name = Path(directory).resolve().name
    found = re.match(r"[A-Za-z][A-Za-z0-9]*-[0-9]+", name)
    return found.group(0) if found else name


def plan_status(directory: Path) -> str:
    try:
        return md.status((Path(directory) / PLAN_MD).read_text(encoding="utf-8"))
    except (OSError, UnicodeError):
        return ""


def skeleton(directory: Path, plan_id: str | None = None) -> dict:
    """Everything PLAN.md already states, in contract shape. Classification, objective, criteria and rationale are NOT
    invented: they stay absent so `check` lists them as missing."""
    parsed, stones = md.read(Path(directory) / PLAN_MD)
    titles = {m["id"]: m["title"] for m in stones}
    tasks = []
    for item in parsed:
        entry: dict = {"id": item["id"], "title": item["title"], "after": list(item["after"])}
        if item.get("milestone"):
            entry["milestone_id"] = item["milestone"]
        if item.get("repo"):
            entry["repository"] = item["repo"]
        if item.get("files"):
            entry["expected_paths"] = list(item["files"])
        if item.get("resources"):
            entry["shared_resources"] = list(item["resources"])
        if item.get("verify"):
            entry["verification"] = [{"type": "command", "value": item["verify"],
                                      "purpose": "verify command declared in PLAN.md"}]
        tasks.append(entry)
    seen = list(dict.fromkeys(t["milestone_id"] for t in tasks if "milestone_id" in t))
    last = rev.latest(directory)
    return {"schema_version": pc.SCHEMA_VERSION, "plan_id": plan_id or default_plan_id(directory), "revision": (last["revision"] + 1) if last else 1,
            "spec_ref": DEFAULT_SPEC_REF,
            "milestones": [{"id": mid, "title": titles.get(mid, "")} for mid in seen], "tasks": tasks}


def write_skeleton(directory: Path, force: bool = False, plan_id: str | None = None) -> Path:
    target = Path(directory) / PLAN_JSON
    if target.exists() and not force:
        raise pc.PlanContractError("PLAN_EXISTS", [f"{target.name} already exists; edit it, or pass --force to rebuild"])
    data = skeleton(directory, plan_id)
    if not data["tasks"]:
        raise pc.PlanContractError("PLAN_MD_EMPTY", ["PLAN.md has no task lines (`- [ ] T1 — title · …`) to derive from"])
    # Skeleton is incomplete by design: write it as-is (not canonicalised through validation).
    target.write_text(pc.dumps(data), encoding="utf-8")
    return target


def consistency(directory: Path, plan: dict, plan_id: str | None = None) -> list[str]:
    """Differences between PLAN.md and PLAN.json by ids, milestone membership and `after` (empty list = consistent)."""
    parsed, stones = md.read(Path(directory) / PLAN_MD)
    problems: list[str] = []
    md_tasks = {t["id"]: t for t in parsed}
    if not md_tasks:
        return ["PLAN.md: no task lines found to compare with PLAN.json"]
    expected_id = plan_id or default_plan_id(directory)
    if plan.get("plan_id") != expected_id:
        problems.append(f"plan.plan_id: {plan.get('plan_id')!r} does not match the plan directory ({expected_id})")
    spec = (Path(directory) / str(plan.get("spec_ref") or DEFAULT_SPEC_REF)).resolve()
    if not (spec.is_relative_to(Path(directory).resolve()) and spec.is_file()):
        problems.append(f"plan.spec_ref: {plan.get('spec_ref')!r} does not exist in the plan directory")
    json_tasks = {t["id"]: t for t in plan.get("tasks", []) if isinstance(t, dict) and isinstance(t.get("id"), str)}
    for tid in md_tasks.keys() - json_tasks.keys():
        problems.append(f"{tid}: in PLAN.md but missing from PLAN.json")
    for tid in json_tasks.keys() - md_tasks.keys():
        problems.append(f"{tid}: in PLAN.json but missing from PLAN.md")
    for tid in sorted(md_tasks.keys() & json_tasks.keys()):
        doc, js = md_tasks[tid], json_tasks[tid]
        if doc.get("milestone") != js.get("milestone_id"):
            problems.append(f"{tid}.milestone_id: PLAN.md puts it under {doc.get('milestone') or 'no milestone'}, "
                            f"PLAN.json says {js.get('milestone_id')}")
        if set(doc["after"]) != set(js.get("after") or []):
            problems.append(f"{tid}.after: PLAN.md has {sorted(doc['after'])}, PLAN.json has "
                            f"{sorted(js.get('after') or [])}")
    md_milestones = {m["id"] for m in stones}
    json_milestones = {m["id"] for m in plan.get("milestones", []) if isinstance(m, dict) and "id" in m}
    for mid in sorted(md_milestones - json_milestones):
        problems.append(f"{mid}: milestone heading in PLAN.md missing from PLAN.json")
    for mid in sorted(json_milestones - md_milestones):
        problems.append(f"{mid}: milestone in PLAN.json has no `### {mid}` heading with tasks in PLAN.md")
    return problems


def read_plan(directory: Path) -> tuple[object | None, pc.Report]:
    """The parsed PLAN.json (None when unusable) and a report holding why."""
    report = pc.Report()
    path = Path(directory) / PLAN_JSON
    try:
        return pc.loads(path.read_text(encoding="utf-8")), report
    except FileNotFoundError:
        report.errors.append(f"{PLAN_JSON}: not found (legacy plan; run `init` to derive a skeleton)")
    except (OSError, ValueError, UnicodeError) as exc:
        report.errors.append(f"{PLAN_JSON}: unreadable ({type(exc).__name__})")
    return None, report


def check(directory: Path, plan: object | None = None, plan_id: str | None = None) -> pc.Report:
    """Full publication gate: schema + graph rules, PLAN.md consistency, revision store and frozen-revision immutability.
    Pass `plan` to check an already parsed object (so a caller can freeze exactly what was checked)."""
    if plan is None:
        plan, report = read_plan(directory)
        if plan is None:
            return report
    report = pc.Report()
    inner = pc.validate(plan)
    report.errors += inner.errors
    report.warnings += inner.warnings
    if isinstance(plan, dict):
        if inner.ok:
            report.errors += consistency(directory, plan, plan_id)
        else:
            report.warnings.append("PLAN.md consistency is not evaluated until the schema errors above are fixed")
        try:
            last = rev.latest(directory)
            expected = last["revision"] + 1 if last else 1
            report.errors += rev.verify_store(directory, tolerate=expected)  # freeze() adopts or rejects that one itself
            if expected in rev.orphans(directory):
                report.warnings.append(f"PLAN.r{expected}.json exists but is not in the manifest (freeze in progress or "
                                       "interrupted); `freeze` adopts it if identical, rejects it otherwise")
            frozen = next((r for r in rev.list_revisions(directory) if r["revision"] == plan.get("revision")), None)
            if frozen and rev.sha256(pc.dumps(plan)) != frozen["sha256"]:
                report.errors.append(f"plan.revision: r{frozen['revision']} is frozen and PLAN.json differs from it; "
                                     f"set revision to {frozen['revision'] + 1} for the change")
            if isinstance(plan.get("revision"), int) and plan["revision"] > expected:
                report.errors.append(f"plan.revision: next revision is {expected}, got {plan['revision']}")
        except pc.PlanContractError as exc:
            report.errors += exc.issues
    return report


def approve_freeze(directory: Path, plan_id: str | None = None,
                   approved_states: tuple[str, ...] = APPROVED_STATES) -> dict:
    """Freeze the current PLAN.json as an immutable revision. Requires an approved PLAN.md status and a clean check."""
    status = plan_status(directory)
    if status not in approved_states:
        raise pc.PlanContractError("PLAN_NOT_APPROVED", [f"PLAN.md status is {status or 'missing'!r}; freeze after approval"])
    plan, report = read_plan(directory)
    if plan is not None:
        report = check(directory, plan, plan_id)  # the very object that is frozen below: no re-read between check and freeze
    if not report.ok:
        raise pc.PlanContractError("PLAN_INVALID", report.errors)
    return rev.freeze(directory, plan)


def freeze_if_present(directory: Path, plan_id: str | None = None,
                      approved_states: tuple[str, ...] = APPROVED_STATES) -> dict | None:
    """Opt-in contract. No PLAN.json -> None (legacy plan). With one and an approved PLAN.md, freeze it (idempotent) or
    raise PlanContractError; a not-yet-approved plan is left alone."""
    if not (Path(directory) / PLAN_JSON).exists() or plan_status(directory) not in approved_states:
        return None
    return approve_freeze(directory, plan_id, approved_states)


def compat(directory: Path, plan_id: str | None = None) -> dict:
    """Read-only: what an existing plan already provides for the contract and what needs explicit enrichment.
    Never writes anything, never reads values as if they were estimates; legacy labels are reported as such."""
    tasks, stones = md.read(Path(directory) / PLAN_MD)
    skel = skeleton(directory, plan_id)
    required = [k for k in pc.TASK_KEYS]
    per_task = []
    derived_by_id = {t["id"]: t for t in skel["tasks"]}
    for item in tasks:
        derived = derived_by_id[item["id"]]
        missing = [k for k in required if k not in derived]
        per_task.append({"id": item["id"], "derived": sorted(k for k in derived if k in required),
                         "needs_enrichment": missing, "done_in_md": item["done"],
                         "legacy_complexity": item.get("complexity"), "legacy_risk": item.get("risk")})
    return {"plan_id": plan_id or default_plan_id(directory), "plan_status": plan_status(directory),
            "has_plan_json": (Path(directory) / PLAN_JSON).exists(), "task_count": len(tasks),
            "milestones_in_md": [m["id"] for m in stones],
            "tasks_without_milestone": [t["id"] for t in tasks if not t.get("milestone")], "tasks": per_task,
            "skeleton_errors": len(pc.validate(skel).errors)}
