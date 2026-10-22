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
import hashlib
import json
import os
import re
import time
from pathlib import Path

REQUEST = "RUN.remediation.json"
LOG = "RUN.remediation.jsonl"
APPLY_JOURNAL = "RUN.remediation.apply.json"
MAX_PER_TASK = 4                 # findings one remediation task takes; a bigger set is chained into several
DEFAULT_ROUNDS = 2               # remediation rounds one audit gets before the owner is asked
MINUTES_PER_FINDING = 40
MAX_MINUTES = 240
COMPLEXITY = ("low", "medium", "high", "extreme")
LEVELS = ("low", "medium", "high")
ID = re.compile(r"T([0-9]+)(?:\.[0-9]+)?([a-z]?)\Z")
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, indent=1, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)
    if os.name != "nt":
        fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


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
    _atomic_json(path, payload)


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


EXTRA = "RUN.remediation.extra.json"


def extra_rounds(rdir: Path, audit: str) -> int:
    """Rounds beyond `gates.remediation_rounds` the self-healing granted this audit (one per audit, REQ-030): an audit that
    still finds problems after its rounds gets one more instead of sending 20 accepted tasks back."""
    try:
        return int(json.loads((Path(rdir) / EXTRA).read_text(encoding="utf-8")).get(audit, 0))
    except (OSError, ValueError, TypeError, AttributeError):
        return 0


def grant_round(rdir: Path, audit: str, limit: int = 1) -> bool:
    """One more round for `audit`, at most `limit` in all; False when it already has them."""
    if extra_rounds(rdir, audit) >= limit:
        return False
    path = Path(rdir) / EXTRA
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    data[audit] = extra_rounds(rdir, audit) + 1
    path.write_text(json.dumps(data, sort_keys=True) + "\n", encoding="utf-8")
    return True


def rounds_used(rdir: Path, audit: str) -> int:
    return sum(1 for row in history(rdir) if row.get("audit") == audit)


def record(rdir: Path, audit: str, round_no: int, new_tasks: list[str], findings: list[dict]) -> None:
    row = {"at": time.time(), "audit": audit, "round": round_no, "tasks": new_tasks,
           "findings": [{"id": f.get("id"), "severity": f.get("severity"), "tasks": f.get("tasks") or []} for f in findings]}
    with log_path(rdir).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


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


def _command_for(finding: dict, plan: dict) -> list[dict] | None:
    """Use T4b's coverage calculation for every declared owner path."""
    import bt_recovery_compiler
    from bt_recovery_compiler_verification import RecoveryCompilationError

    tasks = {task.get("id"): task for task in plan.get("tasks", []) if isinstance(task, dict)}
    owners = list(dict.fromkeys(name for name in finding.get("tasks") or () if name in tasks))
    paths = list(dict.fromkeys(path for owner in owners for path in tasks[owner].get("expected_paths", [])))
    if not owners or not paths:
        return None
    try:
        coverage = bt_recovery_compiler.coverage_checks(plan, owners, paths, "remediation verification")
    except RecoveryCompilationError:
        return None
    return coverage or None


def _top(values, order):
    ranked = [v for v in values if v in order]
    return max(ranked, key=order.index) if ranked else order[1]


def _task(task_id: str, audit_spec: dict, chunk: list[dict], tasks: dict[str, dict], after: list[str],
          round_no: int, spec_ref: str, plan: dict, commands: list[list[dict]] | None = None) -> dict | None:
    """`commands` (one list of {"command": ...} per finding) replaces the coverage calculation: the self-healing repair task
    (`bt_scheduler_healing`) states its own checks."""
    named = list(dict.fromkeys(t for f in chunk for t in f.get("tasks") or () if t in tasks))
    commands = commands if commands is not None else [_command_for(f, plan) for f in chunk]
    if not named or any(not command for command in commands):
        return None
    repositories = [tasks[t].get("repository") for t in named if tasks[t].get("repository")]
    repository = max(set(repositories), key=repositories.count) if repositories else audit_spec.get("repository")
    ids = ", ".join(f.get("id", "?") for f in chunk)
    criteria, verification = [], []
    for finding, owner_checks in zip(chunk, commands):
        criterion = f"{finding.get('id')} ({finding.get('severity')}) is fixed: {str(finding.get('summary'))[:200]}".strip()
        criteria.append(criterion)
        for command in owner_checks:
            row = {"type": "command", "value": command["command"], "purpose": criterion,
                   "expected": "pass", "created_by": task_id, "category": "functional"}
            if row not in verification:
                verification.append(row)
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
                         str(plan.get("spec_ref") or "SPEC.md").split(":")[-1], plan)
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
        if not getattr(policy, "remediate", False) or rounds_used(rdir, audit) >= getattr(policy, "remediation_rounds", 0) + extra_rounds(rdir, audit):
            return False
        plan = latest_plan(rdir)
        if plan is None or build_revision(plan, audit, findings, round_no=rounds_used(rdir, audit) + 1,
                                          parallel=parallel_for(rdir)) is None:
            return False
        write_request(rdir, audit, attempt, findings)
        return True
    return remediate


def apply(rdir: Path, hold_token: str | None = None) -> dict | None:
    """Turn the pending request into the next frozen plan revision and clear it. Returns {audit, round, tasks, revision} or
    None when there was nothing to apply or the revision cannot be built (the request is then dropped: the next rejection
    of the audit sends the named tasks back). The caller rebases the run onto the new revision."""
    import bt_plan_adapter
    import bt_scheduler_ops

    if bt_scheduler_ops.on_hold(rdir) and not bt_scheduler_ops.owns_hold(rdir, hold_token):
        return None                    # a hold that is not the caller's own is an operator's stop: nothing is frozen under it

    request = read_request(rdir)
    if request is None:
        clear_request(rdir)
        return None
    plan = latest_plan(rdir)
    audit, findings = str(request["audit"]), list(request["findings"])
    round_no = rounds_used(rdir, audit) + 1
    request_id = hashlib.sha256(json.dumps({"audit": audit, "attempt": request.get("attempt"),
        "findings": findings}, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    journal_path = Path(rdir) / APPLY_JOURNAL
    try:
        journal = json.loads(journal_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        revised = build_revision(plan, audit, findings, round_no=round_no,
                                    parallel=parallel_for(rdir)) if plan else None
        if revised is None:
            clear_request(rdir)
            return None
        journal = {"schema": "remediation-apply/1", "request_id": request_id, "stage": "prepared",
                   "audit": audit, "round": round_no, "revision": revised["revision"], "plan": revised}
        _atomic_json(journal_path, journal)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("remediation apply journal is unreadable") from exc
    if journal.get("request_id") != request_id:
        if journal.get("stage") != "committed":
            raise RuntimeError("a different remediation request owns the apply journal")
        revised = build_revision(plan, audit, findings, round_no=round_no,
                                    parallel=parallel_for(rdir)) if plan else None
        if revised is None:
            clear_request(rdir)
            return None
        journal = {"schema": "remediation-apply/1", "request_id": request_id, "stage": "prepared",
                   "audit": audit, "round": round_no, "revision": revised["revision"], "plan": revised}
        _atomic_json(journal_path, journal)
    round_no = journal.get("round")
    if type(round_no) is not int or round_no < 1:
        raise RuntimeError("remediation apply journal has an invalid round")
    revised = journal.get("plan")
    if not isinstance(revised, dict) or revised.get("revision") != journal.get("revision"):
        raise RuntimeError("remediation apply journal has no valid frozen candidate")
    if plan is None:
        raise RuntimeError("remediation base plan is unavailable")
    if plan.get("revision") >= revised["revision"]:
        plan = bt_plan_adapter.planner_revisions.load_revision(rdir, revised["revision"] - 1)
    frozen = bt_plan_adapter.freeze_revision(rdir, revised, "remediation")
    journal.update(stage="frozen", revision=frozen["revision"], sha256=frozen["sha256"])
    _atomic_json(journal_path, journal)
    old = {t["id"] for t in plan["tasks"]}
    added = [t["id"] for t in revised["tasks"] if t["id"] not in old]
    if not any(row.get("request_id") == request_id for row in history(rdir)):
        row = {"at": time.time(), "audit": audit, "round": round_no, "tasks": added,
               "findings": [{"id": f.get("id"), "severity": f.get("severity"), "tasks": f.get("tasks") or []}
                            for f in findings], "request_id": request_id}
        with log_path(rdir).open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
    journal["stage"] = "committed"
    _atomic_json(journal_path, journal)
    clear_request(rdir)
    return {"audit": audit, "round": round_no, "tasks": added, "revision": revised["revision"]}
