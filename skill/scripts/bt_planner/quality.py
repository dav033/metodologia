"""Plan-level coherence beyond the schema: what the dependency graph and the classifications say together.

`conflicts` and `redundant_edges` are linted by `contract.validate`; `analyze` is a read-only summary (critical path,
widest antichain level, distributions, evidence coverage) that a planner reads to judge whether a plan is sound and that
a scheduler may ignore. Pure functions over a parsed PLAN.json; they assume nothing about execution.
"""
from __future__ import annotations

import fnmatch
import re

LEDGER_SUFFIX = ".findings.json"   # the findings ledger an audit task declares
VERIFICATION_CATEGORIES = ("static", "functional", "integration", "regression", "product")

_WILD = re.compile(r"[*?\[]")


def _static(path: str) -> str:
    flat = path.replace("\\", "/").strip().strip("/")
    parts = flat.split("/")
    out = []
    for part in parts:
        if _WILD.search(part):
            break
        out.append(part)
    return "/".join(out)


def paths_overlap(a: str, b: str) -> bool:
    """Two path patterns can name the same file: equal static prefixes, one directory containing the other, an empty
    prefix (`**`) or a glob that matches the other."""
    sa, sb = _static(a), _static(b)
    if not sa or not sb or sa == sb or sa.startswith(sb + "/") or sb.startswith(sa + "/"):
        return True
    return fnmatch.fnmatchcase(a, b) or fnmatch.fnmatchcase(b, a)


def _tasks(plan: dict) -> dict[str, dict]:
    return {t["id"]: t for t in plan.get("tasks", []) if isinstance(t, dict) and isinstance(t.get("id"), str)}


def _after(task: dict) -> list[str]:
    after = task.get("after")
    return [a for a in after if isinstance(a, str)] if isinstance(after, list) else []


MAX_LINTED_TASKS = 1500  # pairwise checks are quadratic; a plan this size is reported, not silently slow


def _order(plan: dict) -> tuple[list[str], dict[str, dict]]:
    """Task ids in dependency order (prerequisites first). Ids caught in a cycle are left out: the validator reports
    cycles itself. Iterative, so a long chain cannot exhaust the recursion limit."""
    tasks = _tasks(plan)
    pending = {tid: {d for d in _after(task) if d in tasks and d != tid} for tid, task in tasks.items()}
    users: dict[str, list[str]] = {}
    for tid, deps in pending.items():
        for dep in deps:
            users.setdefault(dep, []).append(tid)
    ready = sorted(tid for tid, deps in pending.items() if not deps)
    order: list[str] = []
    while ready:
        node = ready.pop(0)
        order.append(node)
        for user in users.get(node, ()):
            pending[user].discard(node)
            if not pending[user] and user not in order and user not in ready:
                ready.append(user)
    return order, tasks


def ancestors(plan: dict) -> dict[str, set[str]]:
    """task id -> every task that must finish before it (transitive)."""
    order, _, bit, mask = _ordered_masks(plan)
    return {tid: {other for other in order if mask[tid] & bit[other]} for tid in order}


def _ordered_masks(plan: dict) -> tuple[list[str], dict[str, dict], dict[str, int], dict[str, int]]:
    order, tasks = _order(plan)
    bit = {tid: 1 << i for i, tid in enumerate(order)}
    mask: dict[str, int] = {}
    for tid in order:
        value = 0
        for dep in _after(tasks[tid]):
            if dep in mask:
                value |= mask[dep] | bit[dep]
        mask[tid] = value
    return order, tasks, bit, mask


def conflicts(plan: dict) -> list[str]:
    """Tasks that nothing orders yet share a path or a resource while one of them claims `coupling: low`: a
    scheduler reading `low` would run them side by side and they would collide."""
    order, tasks, bit, mask = _ordered_masks(plan)
    if len(order) > MAX_LINTED_TASKS:
        return []
    out = []
    for i, a in enumerate(order):
        ta = tasks[a]
        for b in order[i + 1:]:
            if mask[b] & bit[a] or mask[a] & bit[b]:
                continue
            tb = tasks[b]
            if ta.get("coupling") != "low" and tb.get("coupling") != "low":
                continue
            if str(ta.get("repository")) != str(tb.get("repository")):
                continue
            paths = [(p, q) for p in _strs(ta.get("expected_paths")) for q in _strs(tb.get("expected_paths"))
                     if paths_overlap(p, q)]
            shared = sorted(set(_strs(ta.get("shared_resources"))) & set(_strs(tb.get("shared_resources"))))
            if paths or shared:
                what = f"path {paths[0][0]!r}~{paths[0][1]!r}" if paths else f"resource {shared[0]!r}"
                first, second = sorted((a, b))
                out.append(f"{first} and {second}: nothing orders them yet both touch {what}, and one declares "
                           "coupling low; add `after` between them or raise the coupling")
    return sorted(out)


def shared_unordered(plan: dict) -> list[str]:
    """Same overlap as `conflicts`, but where nobody claims `coupling: low`: the plan admits the interaction yet leaves
    the two tasks unordered, so whoever schedules them has to serialise or coordinate. A warning, never a decision."""
    order, tasks, bit, mask = _ordered_masks(plan)
    if len(order) > MAX_LINTED_TASKS:
        return []
    out = []
    for i, a in enumerate(order):
        ta = tasks[a]
        for b in order[i + 1:]:
            if mask[b] & bit[a] or mask[a] & bit[b]:
                continue
            tb = tasks[b]
            if ta.get("coupling") == "low" or tb.get("coupling") == "low":
                continue  # reported as an error by `conflicts`
            if str(ta.get("repository")) != str(tb.get("repository")):
                continue
            shared = sorted(set(_strs(ta.get("shared_resources"))) & set(_strs(tb.get("shared_resources"))))
            paths = [p for p in _strs(ta.get("expected_paths")) for q in _strs(tb.get("expected_paths"))
                     if paths_overlap(p, q)]
            if shared or paths:
                what = f"resource {shared[0]!r}" if shared else f"path {paths[0]!r}"
                first, second = sorted((a, b))
                out.append(f"{first} and {second}: unordered but both touch {what}; order them with `after` or the "
                           "scheduler must serialise them")
    return sorted(out)


def unconsumed_results(plan: dict) -> list[str]:
    """A task that nothing waits for, outside the plan's last milestone: its result can be lost or arrive after the
    final verification already ran (an `after`-driven scheduler may overlap them). Warning only."""
    tasks = _tasks(plan)
    raw = plan.get("milestones")
    milestones = [m.get("id") for m in raw if isinstance(m, dict)] if isinstance(raw, list) else []
    if len(tasks) < 2 or not milestones:
        return []
    depended = {d for t in tasks.values() for d in _after(t)}
    last = milestones[-1]
    out = []
    for tid, task in tasks.items():
        if tid in depended or task.get("milestone_id") == last:
            continue
        out.append(f"{tid}: no task waits for it (nothing lists it in `after`) and it is not in the last milestone; "
                   "a final verification could run before its result exists")
    return sorted(out)


def redundant_edges(plan: dict) -> list[str]:
    """`after` entries already implied by another prerequisite (T3 after T1, T2 while T2 after T1)."""
    order, tasks, bit, mask = _ordered_masks(plan)
    out = []
    for tid in order:
        deps = [d for d in _after(tasks[tid]) if d in bit]
        for dep in deps:
            if any(mask.get(other, 0) & bit[dep] for other in deps if other != dep):
                out.append(f"{tid}.after: {dep} is already implied by another prerequisite; drop it to keep the "
                           "graph honest")
    return out


def _strs(value: object) -> list[str]:
    return [v for v in value if isinstance(v, str)] if isinstance(value, list) else []


def _minutes(task: dict) -> int:
    m = task.get("estimated_minutes")
    return m if isinstance(m, int) and not isinstance(m, bool) and m > 0 else 0


HOTSPOT_TASKS = 4  # tasks that declare the same file before the plan is told it has no owner for it


def file_hotspots(plan: dict) -> list[str]:
    """One file declared by `HOTSPOT_TASKS` or more tasks of the same repository (audits and tests excluded: they only
    read it). Whoever fixes a late audit finding in such a file changes the work of every task that built on it, and
    the scheduler redoes them one by one (REQ-027: five tasks edited the gateway entry point). A warning: split the
    file by responsibility so each task owns its own module, or give it one owner task and let the others import it."""
    seen: dict[tuple[str, str], list[str]] = {}
    for tid, task in _tasks(plan).items():
        if task.get("kind") in ("audit", "test"):
            continue
        for path in {p for p in _strs(task.get("expected_paths")) if not any(c in p for c in "*?[") and "." in p.split("/")[-1]}:
            seen.setdefault((str(task.get("repository")), path), []).append(tid)
    return sorted(f"{path}: declared by {len(ids)} tasks ({', '.join(sorted(ids)[:6])}); give it one owner or split it "
                  "by responsibility, or an audit fix in it will force those tasks to be redone"
                  for (_, path), ids in seen.items() if len(ids) >= HOTSPOT_TASKS)


_LEADING_CD = re.compile(r"^\s*cd\s+\S+\s*&&\s*")
_SHELL_SYNTAX = re.compile(r"&&|\|\||[;|<>`$]")
_GIT = re.compile(r"^\s*(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*git\s")


def chained_verifications(plan: dict) -> list[str]:
    """Command checks written as a shell chain (`a && b`, pipes, redirects). The verifier runs one program per check
    and rejects shell syntax (only a leading `cd <dir> &&` and `NAME=value` assignments are allowed), so such a check can never pass: write one
    verification per command."""
    out = []
    for task_id, task in _plan_tasks(plan):
        for index, item in enumerate(task.get("verification") if isinstance(task.get("verification"), list) else []):
            if not isinstance(item, dict) or item.get("type") != "command" or not isinstance(item.get("value"), str):
                continue
            command = _LEADING_CD.sub("", item["value"], count=1)
            if _SHELL_SYNTAX.search(command):
                out.append(f"{task_id}.verification[{index}]: `{item['value'][:90]}` uses shell syntax (`&&`, `|`, `;`, "
                           "redirects) and the verifier rejects it; split it into one verification per command")
            elif _GIT.match(command):
                out.append(f"{task_id}.verification[{index}]: `{item['value'][:90]}` runs git, and the verifier's copy "
                           "has no .git, so it can never pass; make it a manual check")
    return out


def analyze(plan: dict) -> dict:
    """Read-only quality summary of a (valid) plan."""
    order, tasks, _, _ = _ordered_masks(plan)
    finish: dict[str, int] = {}
    parent: dict[str, str | None] = {}
    level: dict[str, int] = {}
    for tid in order:
        best, via, depth = 0, None, 0
        for dep in _after(tasks[tid]):
            if dep in finish:
                if finish[dep] > best:
                    best, via = finish[dep], dep
                depth = max(depth, level[dep])
        finish[tid] = best + _minutes(tasks[tid])
        parent[tid] = via
        level[tid] = depth + 1
    end = max(order, key=lambda t: (finish[t], t)) if order else None
    path: list[str] = []
    node = end
    while node:
        path.append(node)
        node = parent.get(node)
    width: dict[int, int] = {}
    for value in level.values():
        width[value] = width.get(value, 0) + 1

    def dist(key: str) -> dict[str, int]:
        out: dict[str, int] = {}
        for task in tasks.values():
            out[str(task.get(key))] = out.get(str(task.get(key)), 0) + 1
        return dict(sorted(out.items()))

    def has_command(task: dict) -> bool:
        return any(isinstance(v, dict) and v.get("type") == "command" for v in task.get("verification") or [])

    return {
        "tasks": len(tasks), "milestones": len(plan["milestones"]) if isinstance(plan.get("milestones"), list) else 0,
        "total_minutes": sum(_minutes(t) for t in tasks.values()),
        "critical_path": {"tasks": path[::-1], "minutes": finish.get(end, 0) if end else 0},
        "widest_level": max(width.values(), default=0),
        "distribution": {k: dist(k) for k in ("complexity", "scope", "risk", "coupling", "confidence")},
        "without_command_verification": sorted(t["id"] for t in tasks.values() if not has_command(t)),
        "low_confidence": sorted(t["id"] for t in tasks.values() if t.get("confidence") == "low"),
        "with_evidence": sorted(t["id"] for t in tasks.values() if isinstance(t.get("classification_evidence"), dict)),
        "unordered_conflicts": conflicts(plan),
        "unordered_shared": shared_unordered(plan),
        "unconsumed_results": unconsumed_results(plan),
        "redundant_edges": redundant_edges(plan),
    }


def _plan_tasks(plan: object) -> list[tuple[str, dict]]:
    if not isinstance(plan, dict) or not isinstance(plan.get("tasks"), list):
        return []
    return [(task.get("id") if isinstance(task.get("id"), str) else f"tasks[{index}]", task)
            for index, task in enumerate(plan["tasks"]) if isinstance(task, dict)]


def verification_categories(plan: dict) -> dict[str, dict[str, object]]:
    """Project declared verification categories and planned work onto each requirement; never reports acceptance."""
    requirements = plan.get("requirements") if isinstance(plan, dict) else None
    if not isinstance(requirements, list):
        return {}
    coverage: dict[str, dict[str, object]] = {}
    for requirement_id in requirements:
        if isinstance(requirement_id, str) and requirement_id not in coverage:
            coverage[requirement_id] = {"categories": [], "verifications": [], "planned_work": [],
                                        "manual_only": False}

    category_sets: dict[str, set[str]] = {requirement_id: set() for requirement_id in coverage}
    manual_state: dict[str, list[str]] = {requirement_id: [] for requirement_id in coverage}
    for task_id, task in _plan_tasks(plan):
        covers = task.get("covers") if isinstance(task.get("covers"), list) else []
        task_requirements = {item for item in covers if isinstance(item, str)} & coverage.keys()
        verifications = task.get("verification") if isinstance(task.get("verification"), list) else []
        for requirement_id in task_requirements:
            for index, item in enumerate(verifications):
                if not isinstance(item, dict):
                    continue
                category = item.get("category")
                kind = item.get("type")
                created_by = item.get("created_by")
                planned = isinstance(created_by, str) and bool(created_by.strip())
                record = {"task_id": task_id, "verification_index": index,
                          "type": kind if isinstance(kind, str) else None,
                          "category": category if isinstance(category, str) else None,
                          "planned": planned}
                coverage[requirement_id]["verifications"].append(record)
                if kind in ("command", "manual"):
                    manual_state[requirement_id].append(kind)
                if category in VERIFICATION_CATEGORIES:
                    category_sets[requirement_id].add(category)
                if planned:
                    planned_record = {**record, "created_by": created_by,
                                      "purpose": item.get("purpose") if isinstance(item.get("purpose"), str) else ""}
                    coverage[requirement_id]["planned_work"].append(planned_record)

    for requirement_id, details in coverage.items():
        details["categories"] = [category for category in VERIFICATION_CATEGORIES
                                 if category in category_sets[requirement_id]]
        types = manual_state[requirement_id]
        details["manual_only"] = bool(types) and all(kind == "manual" for kind in types)
    return coverage


def planned_verifications(plan: dict) -> list[dict[str, object]]:
    """List verification items with `created_by` as planned work, not existing evidence."""
    planned: list[dict[str, object]] = []
    for task_id, task in _plan_tasks(plan):
        verifications = task.get("verification") if isinstance(task.get("verification"), list) else []
        for index, item in enumerate(verifications):
            if not isinstance(item, dict):
                continue
            created_by = item.get("created_by")
            if not isinstance(created_by, str) or not created_by.strip():
                continue
            planned.append({"task_id": task_id, "verification_index": index,
                            "type": item.get("type") if isinstance(item.get("type"), str) else None,
                            "category": item.get("category") if isinstance(item.get("category"), str) else None,
                            "purpose": item.get("purpose") if isinstance(item.get("purpose"), str) else "",
                            "created_by": created_by, "status": "planned_work"})
    return planned


def criteria_without_command(plan: dict) -> list[dict[str, object]]:
    """Report criteria without one unique command after trim or whose purpose fails M6's exact-match rule."""
    missing: list[dict[str, object]] = []
    for task_id, task in _plan_tasks(plan):
        criteria = task.get("acceptance_criteria") if isinstance(task.get("acceptance_criteria"), list) else []
        verifications = task.get("verification") if isinstance(task.get("verification"), list) else []
        valid_verifications = [(index, item) for index, item in enumerate(verifications) if isinstance(item, dict)]
        for criterion in criteria:
            if not isinstance(criterion, str):
                continue
            normalized = criterion.strip()
            if not normalized:
                continue
            normalized_matches = [(index, item) for index, item in valid_verifications
                                  if isinstance(item.get("purpose"), str) and item["purpose"].strip() == normalized]
            exact_matches = [(index, item) for index, item in valid_verifications
                             if item.get("purpose") == criterion]
            exact_commands = [(index, item) for index, item in exact_matches if item.get("type") == "command"]
            if len(exact_matches) == 1 and len(exact_commands) == 1:
                continue

            if len(exact_matches) > 1:
                reason = "ambiguous_purpose"
            elif normalized_matches and not exact_matches:
                reason = "whitespace_mismatch"
            elif exact_matches and exact_matches[0][1].get("type") == "manual":
                reason = "manual_verification"
            elif exact_matches:
                reason = "no_command"
            else:
                reason = "purpose_not_found"
            missing.append({"task_id": task_id, "criterion": criterion, "reason": reason,
                            "m6_criterion_status": "NEEDS_REVIEW",
                            "verification_indexes": [index for index, _ in normalized_matches]})
    return missing


def verification_report(plan: dict) -> dict[str, object]:
    """Stable Planner report fields for T10 to expose without changing legacy analysis output."""
    return {"verification_categories": verification_categories(plan),
            "criteria_without_command": criteria_without_command(plan)}


def audit_findings(plan: dict) -> list[str]:
    """Schema 1.2.0 errors for audits that cannot reject anything. A passing «the report file exists» says nothing about
    what the audit found, so an audit task must declare its machine-readable findings ledger (the Scheduler rejects it
    while a critical/high finding is open and sends the named tasks back), and a plan with an audit must run, before it,
    an end-to-end test over the real entry points: components that pass alone but were never started together are what
    an audit finds too late."""
    if not isinstance(plan, dict) or not isinstance(plan.get("tasks"), list):
        return []
    tasks = {t["id"]: t for t in plan["tasks"] if isinstance(t, dict) and isinstance(t.get("id"), str)}
    audits = [tid for tid, t in tasks.items() if t.get("kind") == "audit"]
    errors: list[str] = []
    for tid in audits:
        paths = tasks[tid].get("expected_paths")
        ledgers = [p for p in paths if isinstance(p, str) and p.endswith(LEDGER_SUFFIX)] if isinstance(paths, list) else []
        if len(ledgers) != 1:
            errors.append(f"{tid}.expected_paths: an audit task must list exactly one findings ledger "
                          f"(a path ending {LEDGER_SUFFIX}); the Scheduler rejects the audit while a critical or high "
                          "finding in it is open")
    if not audits:
        return errors
    before = ancestors(plan)

    def integration(task: dict) -> bool:
        verification = task.get("verification")
        return task.get("kind") == "test" and isinstance(verification, list) and any(
            isinstance(v, dict) and v.get("type") == "command" and v.get("category") == "integration"
            for v in verification)

    integration_ids = {tid for tid, t in tasks.items() if integration(t)}
    for tid in audits:
        if not integration_ids & before.get(tid, set()):
            errors.append(f"{tid}: an audit needs a `kind: test` task with an `integration` command verification "
                          "among the tasks it follows; that test must start the real entry points (server, worker, "
                          "CLI) together, not only import their modules")
    return errors


def audit_advice(plan: dict) -> list[str]:
    """Warnings for the audit shape that the Scheduler can only recommend: a single audit relies on one auditor's
    honesty. A second, independent `audit` task over the same scope (cheap, bounded, its own ledger) catches what the
    first one omits; whether it is required is the owner's choice (`gates.second_auditor`)."""
    if not isinstance(plan, dict) or not isinstance(plan.get("tasks"), list):
        return []
    audits = [t["id"] for t in plan["tasks"] if isinstance(t, dict) and t.get("kind") == "audit" and isinstance(t.get("id"), str)]
    if len(audits) == 1:
        return [f"{audits[0]}: the plan has a single audit; add an independent cross-check audit (own report and "
                f"findings ledger) so one auditor's omissions do not decide the outcome"]
    return []


def verification_findings(plan: dict) -> list[str]:
    """Return deterministic schema 1.2.0 warnings; M6 remains authoritative for every runtime verdict."""
    if not isinstance(plan, dict):
        return []
    warnings: list[str] = []
    for item in planned_verifications(plan):
        warnings.append(f"{item['task_id']}.verification[{item['verification_index']}]: created_by "
                        f"{item['created_by']!r} is planned work, not existing evidence")

    for item in criteria_without_command(plan):
        task_id = item["task_id"]
        criterion = item["criterion"]
        reason = item["reason"]
        if reason == "whitespace_mismatch":
            detail = "purpose matches after whitespace trim, but M6 currently compares it exactly"
        elif reason == "manual_verification":
            detail = "manual verification cannot produce an automatic PASS"
        elif reason == "ambiguous_purpose":
            detail = "multiple verifications have the same purpose"
        elif reason == "no_command":
            detail = "no command verification matches the purpose"
        else:
            detail = "no verification purpose matches after whitespace trim"
        warnings.append(f"{task_id}.acceptance_criteria: {criterion!r}; {detail}; M6 will mark this criterion "
                        "NEEDS_REVIEW")

    for requirement_id, details in verification_categories(plan).items():
        records = details["verifications"]
        if details["manual_only"]:
            warnings.append(f"requirements.{requirement_id}: covering tasks have only manual verification; M6 will "
                            "leave criteria NEEDS_REVIEW")
        categories = details["categories"]
        if not records or not categories:
            continue
        product_checks = [record for record in records
                          if record["category"] == "product" and not record["planned"]]
        if product_checks:
            continue
        if any(record["category"] == "product" for record in records):
            detail = "product-category verification is only planned work, not existing evidence"
        else:
            detail = f"declared categories are {', '.join(categories)} and include no product-level verification"
        warnings.append(f"requirements.{requirement_id}: Planner review whether user-visible/product claims need "
                        f"product-level verification; {detail}; lower-level tests are not product acceptance")

    return warnings
