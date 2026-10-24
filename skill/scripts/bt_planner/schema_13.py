"""Schema 1.3.0 subplan, composition, UI and early-checkpoint contract rules."""
from __future__ import annotations

import re
from collections import defaultdict

from . import subplan_graph
from .subplan_graph import _BARRIERS, _dict_list

_SUBPLAN = re.compile(r"SP-[1-9][0-9]*")
_GATE = re.compile(r"CG-[1-9][0-9]*")
_CONTRACT = re.compile(r"[a-z0-9][a-z0-9-]{0,63}")
_RESOURCE = re.compile(r"(?:[A-Z][A-Z0-9_]{1,63}|service:[a-z0-9][a-z0-9-]{0,63})")
_UI_EXTENSIONS = (".tsx", ".jsx", ".vue", ".svelte", ".astro", ".css", ".scss", ".sass", ".less", ".html")


def _err(code: str, where: str, message: str) -> str:
    return f"{code}: {where}: {message}"


def _string_set(value: object) -> set[str]:
    return {item for item in value if isinstance(item, str)} if isinstance(value, list) else set()


def _task(tasks: dict[str, dict], task_id: object) -> dict | None:
    return tasks.get(task_id) if isinstance(task_id, str) else None


def unsupported_fields(plan: dict) -> list[str]:
    names = ("subplans", "composition_gates")
    found: list[tuple[str, object]] = [(key, plan[key]) for key in names if key in plan]
    tasks = plan.get("tasks")
    if isinstance(tasks, list):
        for i, task in enumerate(tasks):
            if isinstance(task, dict):
                found.extend((f"tasks[{i}].{key}", task[key]) for key in ("subplan_id", "ui") if key in task)
                if task.get("kind") == "design":
                    found.append((f"tasks[{i}].kind", task["kind"]))
                verifications = task.get("verification")
                if isinstance(verifications, list):
                    found.extend((f"tasks[{i}].verification[{j}].{key}", v[key])
                                 for j, v in enumerate(verifications) if isinstance(v, dict)
                                 for key in ("environment", "requires", "authorization_needed") if key in v)
    return [_err("SCHEMA_FIELD_UNSUPPORTED", where, f"{value!r} requires schema 1.3.0") for where, value in found]


def check(plan: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    tasks, ancestors = subplan_graph.graph(plan)
    requirements = _string_set(plan.get("requirements"))
    subplans_raw = plan.get("subplans", [])
    gates_raw = plan.get("composition_gates", [])
    if not isinstance(subplans_raw, list) or len(subplans_raw) > 64:
        errors.append(_err("SUBPLAN_INVALID", "subplans", "must be a list with at most 64 entries"))
    if not isinstance(gates_raw, list) or len(gates_raw) > 32:
        errors.append(_err("COMPOSITION_INVALID", "composition_gates", "must be a list with at most 32 entries"))
    milestones = {m.get("id") for m in _dict_list(plan.get("milestones")) if isinstance(m.get("id"), str)}
    if isinstance(subplans_raw, list):
        errors.extend(_err("SUBPLAN_INVALID", f"subplans[{i}]", "must be an object")
                      for i, item in enumerate(subplans_raw) if not isinstance(item, dict))
    if isinstance(gates_raw, list):
        errors.extend(_err("COMPOSITION_INVALID", f"composition_gates[{i}]", "must be an object")
                      for i, item in enumerate(gates_raw) if not isinstance(item, dict))
    subplans = _dict_list(subplans_raw)
    gates = _dict_list(gates_raw)
    by_sp: dict[str, dict] = {}
    for i, sp in enumerate(subplans):
        sid = sp.get("id")
        where = f"subplans[{i}]"
        if not isinstance(sid, str) or not _SUBPLAN.fullmatch(sid) or sid in by_sp:
            errors.append(_err("SUBPLAN_INVALID", where, "id must be unique and match SP-n"))
            continue
        by_sp[sid] = sp
        for field in ("produces", "consumes", "checkpoints"):
            if field in sp and not isinstance(sp[field], list):
                errors.append(_err("SUBPLAN_INVALID", f"{sid}.{field}", "must be a list"))
        milestone_id = sp.get("milestone_id")
        if not isinstance(milestone_id, str) or milestone_id not in milestones:
            errors.append(_err("SUBPLAN_MILESTONE", f"{sid}.milestone_id", "must name an existing milestone"))
        title, outcome = sp.get("title"), sp.get("outcome")
        if not isinstance(title, str) or not title.strip() or not isinstance(outcome, str) or len(outcome.split()) < 4 or outcome == title:
            errors.append(_err("SUBPLAN_NO_OUTCOME", sid, "needs a distinct observable outcome of at least four words"))
        covers = sp.get("covers")
        if not isinstance(covers, list) or not covers or not all(isinstance(x, str) for x in covers) or not _string_set(covers) <= requirements:
            errors.append(_err("SUBPLAN_COVERAGE", f"{sid}.covers", "must be a non-empty subset of requirements"))
        members = {tid for tid, task in tasks.items() if task.get("subplan_id") == sid}
        if not members:
            errors.append(_err("SUBPLAN_EMPTY", sid, "has no tasks"))
        for tid in members:
            task = tasks[tid]
            if task.get("milestone_id") != sp.get("milestone_id"):
                errors.append(_err("SUBPLAN_MILESTONE", tid, "task milestone differs from its subplan"))
            if not _string_set(task.get("covers")) <= _string_set(covers):
                errors.append(_err("SUBPLAN_COVERAGE", tid, "task covers requirements outside its subplan"))
        task_covers = set().union(*(_string_set(tasks[t].get("covers")) for t in members)) if members else set()
        if not _string_set(covers) <= task_covers:
            errors.append(_err("SUBPLAN_COVERAGE", sid, "each subplan requirement must be covered by a task"))
        criteria = sp.get("acceptance_criteria")
        task_criteria = set().union(*(_string_set(tasks[t].get("acceptance_criteria")) for t in members)) if members else set()
        if not isinstance(criteria, list) or not criteria or not all(isinstance(x, str) for x in criteria) or not _string_set(criteria) <= task_criteria:
            errors.append(_err("SUBPLAN_CRITERION_UNCARRIED", sid, "criteria must be carried exactly by own tasks"))
        if len(members) > 8 and not sp.get("checkpoints"):
            errors.append(_err("SUBPLAN_LATE_CHECKPOINT", sid, "more than eight tasks requires a checkpoint"))
        if subplan_graph.longest_unbarriered_chain(plan, members, tasks=tasks) > 6:
            errors.append(_err("SUBPLAN_LATE_CHECKPOINT", sid, "dependency exposure exceeds six before an own test/audit barrier"))
        for ci, checkpoint in enumerate(sp.get("checkpoints", []) if isinstance(sp.get("checkpoints"), list) else []):
            check_task = _task(tasks, checkpoint.get("task")) if isinstance(checkpoint, dict) else None
            if (not isinstance(checkpoint, dict) or not isinstance(checkpoint.get("purpose"), str)
                    or not checkpoint["purpose"].strip() or not check_task or check_task.get("subplan_id") != sid
                    or not isinstance(check_task.get("kind"), str) or check_task.get("kind") not in _BARRIERS):
                errors.append(_err("SUBPLAN_INVALID", f"{sid}.checkpoints[{ci}]", "must name an own test/audit task and purpose"))
        _validate_contracts(errors, warnings, sid, sp, members, tasks, ancestors, plan)
        _validate_ui(errors, sid, sp, members, tasks, ancestors)
        integration = _task(tasks, sp.get("integration_test_task"))
        if not integration or integration.get("subplan_id") != sid or integration.get("kind") != "test" or not _has_category(integration, "integration"):
            errors.append(_err("SUBPLAN_AUDIT", sid, "integration_test_task must be an own integration test"))
        audit_id = sp.get("audit_task")
        audit = _task(tasks, audit_id)
        if (not audit or audit.get("subplan_id") != sid or audit.get("kind") != "audit"
                or not isinstance(audit_id, str) or not (members - {audit_id}) <= ancestors.get(audit_id, set())):
            errors.append(_err("SUBPLAN_AUDIT", sid, "audit_task must be own audit after every task"))
    for tid, task in tasks.items():
        sid = task.get("subplan_id")
        if sid is not None and (not isinstance(sid, str) or sid not in by_sp):
            errors.append(_err("SUBPLAN_INVALID", tid, f"unknown subplan_id {sid}"))
    if subplans:
        _validate_contract_graph(errors, warnings, by_sp, tasks, ancestors, gates)
        _validate_gates(errors, plan, gates, tasks, ancestors, by_sp)
        _validate_subplan_edges(errors, tasks, by_sp, gates)
        _validate_requirements(errors, requirements, plan, tasks, subplans, gates)
        _validate_dependency_cycles(errors, warnings, by_sp, gates)
    _validate_verifications(errors, tasks)
    if subplan_graph.longest_unbarriered_chain(plan, tasks=tasks) > 6:
        errors.append(_err("LATE_CHECKPOINT", "tasks", "dependency exposure exceeds six before a test/audit barrier"))
    return errors, warnings


def _has_category(task: dict, category: str) -> bool:
    verifications = task.get("verification")
    return isinstance(verifications, list) and any(
        isinstance(v, dict) and v.get("type") == "command" and v.get("category") == category
        for v in verifications)


def _validate_contracts(errors: list[str], warnings: list[str], sid: str, sp: dict, members: set[str],
                        tasks: dict[str, dict], ancestors: dict[str, set[str]], plan: dict) -> None:
    interface_ids = {item.get("id") for item in _dict_list(plan.get("interfaces"))
                     if isinstance(item.get("id"), str)}
    producers = sp.get("produces", [])
    for i, item in enumerate(producers if isinstance(producers, list) else []):
        where = f"{sid}.produces[{i}]"
        if (not isinstance(item, dict) or not isinstance(item.get("contract"), str) or not _CONTRACT.fullmatch(item["contract"])
                or not isinstance(item.get("version"), int) or isinstance(item.get("version"), bool)
                or not 1 <= item["version"] <= 1000 or not isinstance(item.get("defined_by"), str)
                or item["defined_by"] not in tasks or tasks[item["defined_by"]].get("subplan_id") not in (None, sid)):
            errors.append(_err("SUBPLAN_CONTRACT", where, "invalid contract, version or defined_by task"))
        elif "interfaces" in item and (not isinstance(item["interfaces"], list)
                                        or not all(isinstance(value, str) and value in interface_ids for value in item["interfaces"])):
            errors.append(_err("SUBPLAN_CONTRACT", f"{where}.interfaces", "must list existing IF-n ids"))
    for i, item in enumerate(sp.get("consumes", []) if isinstance(sp.get("consumes"), list) else []):
        where = f"{sid}.consumes[{i}]"
        if (not isinstance(item, dict) or not isinstance(item.get("contract"), str) or not _CONTRACT.fullmatch(item["contract"])
                or not isinstance(item.get("version"), int) or isinstance(item.get("version"), bool)
                or not 1 <= item["version"] <= 1000 or item.get("dependency") not in ("contract", "implementation", "publication")):
            errors.append(_err("SUBPLAN_CONTRACT", where, "invalid consumed contract")); continue
        source = item.get("from")
        if source != "external":
            if not isinstance(source, str) or not _SUBPLAN.fullmatch(source):
                errors.append(_err("SUBPLAN_CONTRACT", where, "from must be SP-n or external"))
            elif item.get("dependency") in ("implementation", "publication") and source == sid:
                errors.append(_err("SUBPLAN_CYCLE", where, "cannot depend on own unfinished implementation"))
        elif item.get("dependency") != "contract":
            errors.append(_err("SUBPLAN_CONTRACT", where, "external dependencies must be contract"))
        if item.get("dependency") in ("implementation", "publication") and not item.get("verified_by"):
            warnings.append(_err("CONSUMER_CONTRACT_TEST_MISSING", where, "add consumer-side contract tests in verified_by"))
        elif "verified_by" in item and (not isinstance(item["verified_by"], list)
                                         or not item["verified_by"]
                                         or any(not isinstance(tid, str) or tid not in members or tasks[tid].get("kind") != "test"
                                                for tid in item["verified_by"])):
            errors.append(_err("SUBPLAN_CONTRACT", f"{where}.verified_by", "must name own consumer-side test tasks"))


def _validate_ui(errors: list[str], sid: str, sp: dict, members: set[str], tasks: dict[str, dict],
                 ancestors: dict[str, set[str]]) -> None:
    ui = sp.get("ui")
    ui_tasks = {tid for tid in members if tasks[tid].get("ui") is True}
    if ui_tasks and not isinstance(ui, dict):
        errors.append(_err("UI_GATE_MISSING", sid, "ui tasks require a subplan ui contract")); return
    if not isinstance(ui, dict):
        return
    design_id, review_id = ui.get("design_task"), ui.get("visual_review_task")
    design, review = _task(tasks, design_id), _task(tasks, review_id)
    if (not isinstance(ui.get("contract"), str) or not _CONTRACT.fullmatch(ui["contract"])
            or not isinstance(ui.get("version"), int) or isinstance(ui.get("version"), bool)
            or not 1 <= ui["version"] <= 1000):
        errors.append(_err("UI_GATE_MISSING", sid, "ui contract and integer version are required"))
    if not design or design.get("kind") != "design" or design.get("subplan_id") != sid or not review or review.get("kind") != "audit" or review.get("subplan_id") != sid:
        errors.append(_err("UI_GATE_MISSING", sid, "design_task and visual_review_task must be own design/audit tasks"))
    for tid in ui_tasks:
        if not isinstance(design_id, str) or design_id not in ancestors.get(tid, set()):
            errors.append(_err("UI_GATE_ORDER", tid, "must depend transitively on design_task"))
        if not isinstance(review_id, str) or tid not in ancestors.get(review_id, set()):
            errors.append(_err("UI_REVIEW_ORDER", tid, "visual review must follow every ui task"))
    audit_id = sp.get("audit_task")
    if ui_tasks and (not isinstance(review_id, str) or not isinstance(audit_id, str)
                     or review_id not in ancestors.get(audit_id, set())):
        errors.append(_err("UI_REVIEW_ORDER", sid, "subplan audit must follow visual review"))


def _validate_gates(errors: list[str], plan: dict, gates: list[dict], tasks: dict[str, dict],
                    ancestors: dict[str, set[str]], subplans: dict[str, dict]) -> None:
    seen: set[str] = set()
    for i, gate in enumerate(gates):
        gid, where = gate.get("id"), f"composition_gates[{i}]"
        listed = gate.get("subplans")
        task, audit = _task(tasks, gate.get("task")), _task(tasks, gate.get("audit_task"))
        valid = (isinstance(gid, str) and _GATE.fullmatch(gid) and gid not in seen and isinstance(listed, list)
                 and bool(listed) and all(isinstance(x, str) for x in listed)
                 and len(_string_set(listed)) == len(listed) and _string_set(listed) <= set(subplans)
                 and task is not None and task.get("kind") == "test" and task.get("subplan_id") is None
                 and _has_category(task, "integration")
                 and isinstance(gate.get("criteria"), list) and bool(gate["criteria"])
                 and all(isinstance(x, str) for x in gate["criteria"])
                 and _string_set(gate["criteria"]) <= _string_set(task.get("acceptance_criteria")))
        if not valid:
            errors.append(_err("COMPOSITION_INVALID", where, "invalid id, subplans, integration task or carried criteria"))
            continue
        seen.add(gid)
        if any(subplans[sid].get("audit_task") not in ancestors.get(task["id"], set()) for sid in listed):
            errors.append(_err("COMPOSITION_INVALID", gid, "gate task must follow each listed subplan audit"))
        if gate.get("audit_task") is not None and (not audit or audit.get("kind") != "audit" or audit.get("subplan_id") is not None or task["id"] not in ancestors.get(audit["id"], set())):
            errors.append(_err("COMPOSITION_INVALID", gid, "audit_task must be an unassigned audit after task"))
    for sid, sp in subplans.items():
        for consume in sp.get("consumes", []) if isinstance(sp.get("consumes"), list) else []:
            source = consume.get("from") if isinstance(consume, dict) else None
            if isinstance(source, str) and source in subplans and not any(
                    {sid, source} <= _string_set(g.get("subplans")) for g in gates if isinstance(g, dict)):
                errors.append(_err("COMPOSITION_MISSING", f"{sid}.consumes", f"no gate composes {sid} with {source}"))


def _validate_contract_graph(errors: list[str], warnings: list[str], subplans: dict[str, dict],
                             tasks: dict[str, dict], ancestors: dict[str, set[str]], gates: list[dict]) -> None:
    producers: dict[tuple[str, int], tuple[str, str]] = {}
    for sid, sp in subplans.items():
        for item in sp.get("produces", []) if isinstance(sp.get("produces"), list) else []:
            if not isinstance(item, dict):
                continue
            contract, version, defined_by = item.get("contract"), item.get("version"), item.get("defined_by")
            key = (contract, version) if isinstance(contract, str) and isinstance(version, int) else None
            if key is None:
                continue
            if key in producers:
                errors.append(_err("SUBPLAN_CONTRACT", f"{sid}.produces", f"{contract}@{version} already produced by {producers[key][0]}"))
            else:
                producers[key] = (sid, defined_by)
    for sid, sp in subplans.items():
        for index, item in enumerate(sp.get("consumes", []) if isinstance(sp.get("consumes"), list) else []):
            if not isinstance(item, dict):
                continue
            source = item.get("from")
            if source == "external":
                continue
            if (not isinstance(source, str) or not isinstance(item.get("contract"), str)
                    or not isinstance(item.get("version"), int) or isinstance(item.get("version"), bool)):
                continue
            key = (item["contract"], item["version"])
            producer = producers.get(key)
            where = f"{sid}.consumes[{index}]"
            if not producer or producer[0] != source:
                errors.append(_err("SUBPLAN_CONTRACT", where, "from must produce the exact consumed contract and version"))
                continue
            dependency = item.get("dependency")
            defined_by = producer[1]
            if dependency == "contract":
                required_task = defined_by
            elif dependency == "implementation":
                required_task = subplans[source].get("audit_task")
            elif dependency == "publication":
                consumer_tasks = [tid for tid, task in tasks.items()
                                  if task.get("subplan_id") == sid and task.get("kind") not in ("research", "docs")
                                  and tid not in {p.get("defined_by") for p in sp.get("produces", [])
                                                  if isinstance(p, dict) and isinstance(p.get("defined_by"), str)}]
                valid_gate_tasks = [gate.get("task") for gate in gates if isinstance(gate, dict)
                                    and source in _string_set(gate.get("subplans"))
                                    and sid not in _string_set(gate.get("subplans"))
                                    and isinstance(gate.get("task"), str)
                                    and all(gate["task"] in ancestors.get(tid, set()) for tid in consumer_tasks)]
                required_task = valid_gate_tasks[0] if valid_gate_tasks else None
                if required_task is None:
                    errors.append(_err("SUBPLAN_ORDER", where, "publication requires an accepted gate containing producer and excluding consumer"))
                    continue
            else:
                continue
            if not isinstance(required_task, str):
                errors.append(_err("SUBPLAN_ORDER", where, "required producer boundary task is missing"))
                continue
            own_definitions = {p.get("defined_by") for p in sp.get("produces", [])
                               if isinstance(p, dict) and isinstance(p.get("defined_by"), str)}
            for tid, task in tasks.items():
                if task.get("subplan_id") != sid or task.get("kind") in ("research", "docs") or tid in own_definitions:
                    continue
                if required_task not in ancestors.get(tid, set()):
                    errors.append(_err("SUBPLAN_ORDER", tid, f"must follow {dependency} boundary {required_task} from {source}"))


def _validate_subplan_edges(errors: list[str], tasks: dict[str, dict], subplans: dict[str, dict], gates: list[dict]) -> None:
    gate_tasks = {g.get("task") for g in gates if isinstance(g, dict) and isinstance(g.get("task"), str)}
    for tid, task in tasks.items():
        sid = task.get("subplan_id")
        if sid is None and tid in gate_tasks:
            continue
        for dep in task.get("after", []) if isinstance(task.get("after"), list) else []:
            other = _task(tasks, dep)
            source = other.get("subplan_id") if other else None
            if not isinstance(source, str) or source == sid or source not in subplans:
                continue
            current_subplan = subplans.get(sid, {}) if isinstance(sid, str) else {}
            edge = any(isinstance(c, dict) and c.get("from") == source
                       for c in current_subplan.get("consumes", []))
            allowed = (isinstance(dep, str) and
                       (dep in gate_tasks
                        or dep in {p.get("defined_by") for p in subplans[source].get("produces", [])
                                   if isinstance(p, dict) and isinstance(p.get("defined_by"), str)}
                        or dep == subplans[source].get("audit_task")))
            if not edge or not allowed:
                errors.append(_err("SUBPLAN_EDGE", f"{tid}.after", f"cross-subplan dependency on {dep} is undeclared or not a contract/audit/gate boundary"))


def _validate_requirements(errors: list[str], requirements: set[object], plan: dict, tasks: dict[str, dict],
                           subplans: list[dict], gates: list[dict]) -> None:
    covered = set().union(*(_string_set(sp.get("covers")) for sp in subplans if isinstance(sp.get("covers"), list)))
    gate_ids = {g.get("task") for g in gates if isinstance(g, dict) and isinstance(g.get("task"), str)}
    for req in requirements - covered:
        if not any(req in _string_set(tasks.get(tid, {}).get("covers")) for tid in gate_ids):
            errors.append(_err("REQUIREMENT_ORPHAN", "requirements", f"{req} is not covered by a subplan or composition task"))
    if subplans:
        for tid, task in tasks.items():
            if task.get("subplan_id") is None and task.get("kind") in ("implement", "design"):
                errors.append(_err("TASK_OUTSIDE_SUBPLAN", tid, "implement/design tasks need subplan_id when subplans exist"))


def _validate_dependency_cycles(errors: list[str], warnings: list[str], subplans: dict[str, dict],
                                gates: list[dict]) -> None:
    edges: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for sid, sp in subplans.items():
        for consume in sp.get("consumes", []) if isinstance(sp.get("consumes"), list) else []:
            if isinstance(consume, dict) and isinstance(consume.get("from"), str) and consume.get("from") in subplans:
                dependency = consume.get("dependency", "contract")
                source = consume.get("from")
                publication_gate = (dependency == "publication" and any(
                    isinstance(gate, dict) and source in _string_set(gate.get("subplans"))
                    and sid not in _string_set(gate.get("subplans")) for gate in gates))
                if not publication_gate:
                    edges[sid].append((source, dependency))
    visiting: set[str] = set()
    visited: set[str] = set()
    def walk(node: str, path: list[tuple[str, str]]) -> None:
        if node in visiting:
            cycle = path[path.index(next(edge for edge in path if edge[0] == node)):]
            if any(kind in ("implementation", "publication") for _, kind in cycle):
                errors.append(_err("SUBPLAN_CYCLE", node, "implementation/publication dependency cycle"))
            elif cycle:
                warnings.append(_err("SUBPLAN_CYCLE", node, "mutually consumed frozen contracts are permitted"))
            return
        if node in visited:
            return
        visiting.add(node)
        for target, kind in edges.get(node, []):
            walk(target, path + [(target, kind)])
        visiting.remove(node); visited.add(node)
    for sid in subplans:
        walk(sid, [])


def _validate_verifications(errors: list[str], tasks: dict[str, dict]) -> None:
    for tid, task in tasks.items():
        kind = task.get("kind")
        verifications = task.get("verification", [])
        if not isinstance(verifications, list):
            verifications = []
        command_checks = [v for v in verifications if isinstance(v, dict) and v.get("type") == "command"]
        if kind == "implement" and (not command_checks or all(v.get("environment", "sandbox") != "sandbox" for v in command_checks)):
            errors.append(_err("EXTERNAL_ONLY_IMPLEMENT", tid, "implement tasks need a sandbox command verification"))
        for i, verification in enumerate(v for v in verifications if isinstance(v, dict)):
            where = f"{tid}.verification[{i}]"
            env = verification.get("environment", "sandbox")
            if not isinstance(env, str) or env not in ("sandbox", "external_authorized", "production", "human_attestation"):
                errors.append(_err("VERIFICATION_ENV_INVALID", f"{where}.environment", "unknown environment"))
            requires = verification.get("requires", [])
            if not isinstance(requires, list) or any(not isinstance(r, str) or not _RESOURCE.fullmatch(r) for r in requires):
                errors.append(_err("SECRET_VALUE_IN_PLAN", f"{where}.requires", "use resource names, never secret values"))
            authorization = verification.get("authorization_needed")
            if env == "production" and (not isinstance(authorization, str) or not authorization.strip()):
                errors.append(_err("SECRET_VALUE_IN_PLAN", f"{where}.authorization_needed", "required for production"))
            if isinstance(authorization, str) and ("=" in authorization or re.search(r"https?://[^/@\s]+:[^/@\s]+@", authorization)
                                                   or re.search(r"\b(?:token|password|secret)\s*:\s*\S+", authorization, re.I)):
                errors.append(_err("SECRET_VALUE_IN_PLAN", f"{where}.authorization_needed", "must describe authorization without secret values"))
            if env == "human_attestation" and (verification.get("type") != "manual" or not verification.get("expected")):
                errors.append(_err("VERIFICATION_ENV_INVALID", where, "human_attestation requires manual type and expected"))
            if verification.get("type") == "command" and verification.get("category") in ("functional", "integration", "product") and _file_probe(verification.get("value", "")):
                errors.append(_err("FILE_EXISTENCE_CHECK", where, "file existence or syntax probes do not demonstrate behaviour"))
        expected_paths = task.get("expected_paths", [])
        if not isinstance(expected_paths, list):
            expected_paths = []
        if "ui" not in task and any(isinstance(path, str) and path.lower().endswith(_UI_EXTENSIONS) for path in expected_paths):
            errors.append(_err("UI_WORK_UNDECLARED", tid, "UI extension expected_paths requires explicit ui boolean"))
        if "ui" in task and not isinstance(task["ui"], bool):
            errors.append(_err("UI_GATE_MISSING", f"{tid}.ui", "must be a boolean"))
        if task.get("ui") is True and not task.get("subplan_id"):
            errors.append(_err("UI_GATE_MISSING", tid, "ui task requires subplan_id"))


def _file_probe(command: str) -> bool:
    if not isinstance(command, str):
        return False
    if any(operator in command for operator in ("|", "$(", "`", ">", "<")):
        return False
    probes = re.compile(r"^(?:test\s+-[sfed]\s+\S+(?:\s+-a\s+-[sfed]\s+\S+)*|\[\s+-f\s+[^]]+\]|ls(?:\s+\S+)*|stat(?:\s+\S+)*|python\s+-m\s+json\.tool(?:\s+\S+)*|jq\s+empty(?:\s+\S+)*|cat(?:\s+\S+)*|head(?:\s+\S+)*|tail(?:\s+\S+)*|wc(?:\s+\S+)*|grep\s+-q(?:\s+\S+)*|diff\s+-q(?:\s+\S+)*|cmp(?:\s+\S+)*|file(?:\s+\S+)*)$")
    return all(probes.fullmatch(part.strip()) for part in re.split(r"&&|;", command) if part.strip())
