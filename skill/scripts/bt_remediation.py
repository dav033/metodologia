"""Remediation tasks: what a blocking audit finding becomes, instead of a rebuild of the tasks it names (REQ-028).

An audit that finds blocking defects used to send the tasks it names back to be redone; every task built on them went stale
and was rebuilt one by one (REQ-027: a 25-task finding set cost days). Here the plan grows instead: the findings become new
tasks that run on the tree the run has already integrated, the audit is moved after them, and the audit runs again. No
accepted result is reopened, so nothing cascades.

  gate (owner process) --request--> `RUN.remediation.json` --> the owner exits --> the watcher calls `apply`
  apply: new plan revision (`build_revision`) -> freeze -> rebase the run onto it -> the owner is started again

`build_revision` is pure: a plan dict and the audit's blocking findings in, the next revision (or None when it cannot be
built soundly, and the caller then falls back to sending the named tasks back). Standard library only, no scheduler import.
"""
from __future__ import annotations

import copy
import json
import re
import time
from pathlib import Path

REQUEST = "RUN.remediation.json"
LOG = "RUN.remediation.jsonl"
MAX_PER_TASK = 4                 # findings one remediation task takes; a bigger set is chained into several
DEFAULT_ROUNDS = 2               # remediation rounds one audit gets before the owner is asked
MINUTES_PER_FINDING = 40
MAX_MINUTES = 240
COMPLEXITY = ("low", "medium", "high", "extreme")
LEVELS = ("low", "medium", "high")
ID = re.compile(r"T([0-9]+)(?:\.[0-9]+)?([a-z]?)\Z")
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def request_path(rdir: Path) -> Path:
    return Path(rdir) / REQUEST


def log_path(rdir: Path) -> Path:
    return Path(rdir) / LOG


def requested(rdir: Path) -> bool:
    return request_path(rdir).is_file()


def read_request(rdir: Path) -> dict | None:
    try:
        data = json.loads(request_path(rdir).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) and isinstance(data.get("findings"), list) and data.get("audit") else None


def write_request(rdir: Path, audit: str, attempt: str, findings: list[dict]) -> None:
    """The gate's record of what to remediate: the audit, the attempt that found it and its blocking findings."""
    payload = {"audit": audit, "attempt": attempt, "at": time.time(), "findings": findings}
    path = request_path(rdir)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    tmp.replace(path)


def clear_request(rdir: Path) -> None:
    request_path(rdir).unlink(missing_ok=True)


def history(rdir: Path) -> list[dict]:
    """Every applied remediation, oldest first: {at, audit, round, tasks, findings: [{id, severity, tasks}]}."""
    out = []
    try:
        for line in log_path(rdir).read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if isinstance(row, dict):
                out.append(row)
    except OSError:
        pass
    return out


def rounds_used(rdir: Path, audit: str) -> int:
    return sum(1 for row in history(rdir) if row.get("audit") == audit)


def record(rdir: Path, audit: str, round_no: int, new_tasks: list[str], findings: list[dict]) -> None:
    row = {"at": time.time(), "audit": audit, "round": round_no, "tasks": new_tasks,
           "findings": [{"id": f.get("id"), "severity": f.get("severity"), "tasks": f.get("tasks") or []} for f in findings]}
    with log_path(rdir).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row) + "\n")


def events(rdir: Path) -> list[dict]:
    """One event per remediated finding, shaped like M1's `rework_requested` rows so the attempt log can charge a finding
    to the (few) tasks that own it: {at, by, named, tasks}."""
    out = []
    for row in history(rdir):
        for finding in row.get("findings") or ():
            named = set(finding.get("tasks") or ())
            out.append({"at": float(row.get("at") or 0), "by": "audit-gate", "named": named, "tasks": named})
    return out


# ------------------------------------------------------------------------------------------------ plan growth
def _digits(task_id: str) -> tuple[str, str]:
    match = ID.match(task_id)
    return (match.group(1), match.group(2)) if match else ("0", "")


def _next_ids(plan_ids: set[str], audit: str, count: int) -> list[str]:
    """T18 -> T18.1, T18.2 ...; T18b -> T18.1b, T18.2b ...: the audit's number and letter with a counter in between."""
    number, letter = _digits(audit)
    out, counter = [], 1
    while len(out) < count:
        candidate = f"T{number}.{counter}{letter}"
        if candidate not in plan_ids:
            out.append(candidate)
        counter += 1
    return out


def _paths_overlap(a: str, b: str) -> bool:
    import bt_plan_adapter

    return bt_plan_adapter.paths_overlap(a, b)


def _groups(findings: list[dict], tasks: dict[str, dict]) -> list[list[dict]]:
    """Findings that touch the same task, or tasks that declare overlapping paths, travel together; a set bigger than
    `MAX_PER_TASK` is cut into consecutive pieces (the caller chains them)."""
    parent = list(range(len(findings)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def paths(finding: dict) -> list[str]:
        return [p for t in finding.get("tasks") or () for p in (tasks.get(t) or {}).get("expected_paths") or ()]

    for i, a in enumerate(findings):
        for j in range(i + 1, len(findings)):
            b = findings[j]
            if set(a.get("tasks") or ()) & set(b.get("tasks") or ()) or \
                    any(_paths_overlap(p, q) for p in paths(a) for q in paths(b)):
                parent[find(i)] = find(j)
    components: dict[int, list[dict]] = {}
    for i, finding in enumerate(findings):
        components.setdefault(find(i), []).append(finding)
    pieces = []
    for members in components.values():
        members.sort(key=lambda f: (SEVERITY_ORDER.get(f.get("severity"), 9), _number(f.get("id"))))
        pieces.append([members[i:i + MAX_PER_TASK] for i in range(0, len(members), MAX_PER_TASK)])
    pieces.sort(key=lambda chain: _number(chain[0][0].get("id")))
    return pieces  # type: ignore[return-value]


def _number(identifier) -> int:
    match = re.search(r"(\d+)", str(identifier or ""))
    return int(match.group(1)) if match else 0


def _command_for(finding: dict, tasks: dict[str, dict]) -> dict | None:
    """The check that proves the area of a finding still works: the first command of the first task it names."""
    for name in finding.get("tasks") or ():
        for item in (tasks.get(name) or {}).get("verification") or ():
            if isinstance(item, dict) and item.get("type") == "command" and item.get("value"):
                return item
    return None


def _top(values, order):
    ranked = [v for v in values if v in order]
    return max(ranked, key=order.index) if ranked else order[1]


def _task(task_id: str, audit_spec: dict, chunk: list[dict], tasks: dict[str, dict], after: list[str],
          round_no: int, spec_ref: str) -> dict | None:
    named = list(dict.fromkeys(t for f in chunk for t in f.get("tasks") or () if t in tasks))
    commands = [_command_for(f, tasks) for f in chunk]
    if not named or any(command is None for command in commands):
        return None
    repositories = [tasks[t].get("repository") for t in named if tasks[t].get("repository")]
    repository = max(set(repositories), key=repositories.count) if repositories else audit_spec.get("repository")
    ids = ", ".join(f.get("id", "?") for f in chunk)
    criteria, verification = [], []
    for finding, command in zip(chunk, commands):
        criterion = f"{finding.get('id')} ({finding.get('severity')}) is fixed: {str(finding.get('summary'))[:200]}".strip()
        criteria.append(criterion)
        verification.append({"type": "command", "value": command["value"], "purpose": criterion,
                             "category": command.get("category") or "functional"})
    details = "\n".join(
        f"- {f.get('id')} ({f.get('severity')}; owned by {', '.join(f.get('tasks') or ()) or 'no task'}): {f.get('summary')}"
        + (f" Evidence from the audit: {f.get('evidence')}" if f.get("evidence") else "") for f in chunk)
    objective = (f"Fix these confirmed audit findings of {audit_spec['id']} (remediation round {round_no}) on the tree "
                 f"already integrated, without rewriting the tasks that built it:\n{details}\nFor each finding add a "
                 "regression test that exercises the real entry point, in the test file that this task's verification "
                 "commands run, and keep every behaviour that works.")
    complexity = _top((tasks[t].get("complexity") for t in named), COMPLEXITY[:3])
    risk = _top((tasks[t].get("risk") for t in named), LEVELS)
    paths = list(dict.fromkeys(p for t in named for p in tasks[t].get("expected_paths") or ()))
    covers = sorted({c for t in named for c in tasks[t].get("covers") or ()})
    ref = f"task:{named[0]}"
    minutes = min(MAX_MINUTES, MINUTES_PER_FINDING * len(chunk))
    evidence = lambda text: {"evidence": [ref, f"spec:{spec_ref}"], "justification": text}  # noqa: E731
    return {
        "id": task_id, "milestone_id": audit_spec["milestone_id"],
        "title": f"Remediate {audit_spec['id']} findings {ids}"[:120], "objective": objective,
        "repository": repository, "after": after, "complexity": complexity,
        "scope": "small_change" if len(chunk) == 1 else "large_change", "estimated_minutes": minutes, "risk": risk,
        "coupling": "high", "confidence": "medium",
        "estimate_rationale": f"{len(chunk)} confirmed finding(s), {MINUTES_PER_FINDING} min each, on the integrated tree",
        "classification_evidence": {
            "complexity": evidence(f"Defects in {', '.join(named)}, found by an independent audit"),
            "scope": evidence(f"{len(chunk)} finding(s) with known symptoms and owners"),
            "duration": evidence(f"{MINUTES_PER_FINDING} minutes per finding, regression tests included"),
            "risk": evidence("Changes code that other accepted tasks were built on"),
            "coupling": evidence("Touches what several accepted tasks share"),
            "confidence": evidence("The audit states the symptom; the cause is found while fixing"),
        },
        "expected_paths": paths, "shared_resources": sorted({r for t in named for r in tasks[t].get("shared_resources") or ()}),
        "acceptance_criteria": criteria, "verification": verification, "covers": covers, "kind": "implement",
    }


def _parallel() -> bool:
    import bt_config

    return bt_config.get("gates.remediation_parallel", False) is True


def parallel_for(rdir: Path) -> bool:
    """Side-by-side remediation only on a run that integrates through the line (`RUN.integration-line`): on the predecessor
    merge, remediation tasks of different components sent each other back over shared files (REQ-027 T18.2, D-114), and the
    line is what makes a clash resolve on top of the current tip instead."""
    return _parallel() and (Path(rdir) / "RUN.integration-line").exists()


def build_revision(plan: dict, audit: str, findings: list[dict], *, round_no: int = 1,
                   parallel: bool | None = None) -> dict | None:
    """The next revision of `plan`: remediation tasks for `findings`, `audit` moved after them. None when a task cannot be
    built soundly (a finding names no task with a command that checks its area) or the result is not a valid plan."""
    import bt_plan_adapter

    by_id = {t["id"]: t for t in plan.get("tasks", []) if isinstance(t, dict) and isinstance(t.get("id"), str)}
    spec = by_id.get(audit)
    if spec is None or not findings:
        return None
    known = [f for f in findings if isinstance(f, dict) and any(t in by_id for t in f.get("tasks") or ())]
    if len(known) != len(findings):
        return None                                    # a finding that names no task of this plan has no owner to infer
    base_after = list(spec.get("after") or ())
    chains = _groups(known, by_id)
    new_ids = _next_ids(set(by_id), audit, sum(len(chain) for chain in chains))
    created, last_ids = [], []
    cursor = iter(new_ids)
    # One after another unless the owner allows parallel areas: remediation tasks of different components still edit the
    # same files in practice (REQ-027 T18.1/.2/.3/.5 each sent each other back six times over server.py)
    serial = not (_parallel() if parallel is None else parallel)
    for chain in chains:
        previous: str | None = last_ids[-1] if serial and last_ids else None
        for chunk in chain:
            task_id = next(cursor)
            task = _task(task_id, spec, chunk, by_id, [*base_after, *([previous] if previous else [])], round_no,
                         str(plan.get("spec_ref") or "SPEC.md").split(":")[-1])
            if task is None:
                return None
            created.append(task)
            previous = task_id
        last_ids.append(previous)
    revised = copy.deepcopy(plan)
    revised["revision"] = int(plan.get("revision") or 0) + 1
    for task in revised["tasks"]:
        if task.get("id") == audit:
            task["after"] = list(dict.fromkeys([*base_after, *last_ids]))
    revised["tasks"] = [*revised["tasks"], *created]
    return None if bt_plan_adapter.plan_errors(revised) else revised


# ------------------------------------------------------------------------------------------------ gate and owner side
def latest_plan(rdir: Path) -> dict | None:
    import bt_plan_adapter

    return bt_plan_adapter.latest_plan(rdir)


def hook(rdir: Path, policy):
    """The gate's `remediate(audit, attempt, findings)` for one run: True when the findings were recorded as a request
    the owner will turn into a plan revision, False when the audit has no rounds left or a task cannot be built soundly
    (the gate then sends the named tasks back, as it always did)."""
    def remediate(audit: str, attempt: str, findings: list[dict]) -> bool:
        if not getattr(policy, "remediate", False) or rounds_used(rdir, audit) >= getattr(policy, "remediation_rounds", 0):
            return False
        plan = latest_plan(rdir)
        if plan is None or build_revision(plan, audit, findings, round_no=rounds_used(rdir, audit) + 1,
                                          parallel=parallel_for(rdir)) is None:
            return False
        write_request(rdir, audit, attempt, findings)
        return True
    return remediate


def apply(rdir: Path) -> dict | None:
    """Turn the pending request into the next frozen plan revision and clear it. Returns {audit, round, tasks, revision} or
    None when there was nothing to apply or the revision cannot be built (the request is then dropped: the next rejection
    of the audit sends the named tasks back). The caller rebases the run onto the new revision."""
    import bt_plan_adapter

    request = read_request(rdir)
    if request is None:
        clear_request(rdir)
        return None
    plan = latest_plan(rdir)
    audit, findings = str(request["audit"]), list(request["findings"])
    round_no = rounds_used(rdir, audit) + 1
    revised = build_revision(plan, audit, findings, round_no=round_no, parallel=parallel_for(rdir)) if plan else None
    if revised is None:
        clear_request(rdir)
        return None
    bt_plan_adapter.freeze_revision(rdir, revised, "remediation")
    old = {t["id"] for t in plan["tasks"]}
    added = [t["id"] for t in revised["tasks"] if t["id"] not in old]
    record(rdir, audit, round_no, added, findings)
    clear_request(rdir)
    return {"audit": audit, "round": round_no, "tasks": added, "revision": revised["revision"]}
