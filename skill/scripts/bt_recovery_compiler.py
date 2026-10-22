"""Pure compiler for narrowly scoped repeated-audit recovery plan revisions."""
from __future__ import annotations

import copy
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from bt_plan_adapter import second_auditor_required, validate_candidate
from bt_scheduler_recovery_adapter import parse_conflict_observation, parse_verification_map
from bt_recovery_compiler_verification import (
    RecoveryCompilationError, _commands, _path, _refuse, _safe_command, _slug, _task_id, _task_record,
    coverage_checks, replan_verification,
)


@dataclass(frozen=True)
class RecoveryRevision:
    plan: dict[str, Any]
    scope: tuple[str, ...]
    verification_map: dict[str, Any]


def compile_recovery_revision(plan: Mapping[str, Any], evidence: Mapping[str, Any], proposal: Mapping[str, Any], *,
                              convergence: Mapping[str, Any] | None = None) -> RecoveryRevision:
    """Compile a validated proposal into a fresh, Planner-validated plan revision, without performing I/O."""
    if not isinstance(plan, Mapping) or not isinstance(plan.get("tasks"), list):
        _refuse("current frozen plan is malformed", "INVALID_PLAN")
    input_errors = validate_candidate(plan)
    if input_errors:
        _refuse("current frozen plan is not Planner-valid: " + "; ".join(input_errors[:5]), "INVALID_PLAN")
    if not isinstance(evidence, Mapping) or evidence.get("schema_version") != "recovery-evidence/1" or evidence.get("diagnosable") is not True:
        _refuse("recovery evidence is not complete and diagnosable", "INVALID_EVIDENCE")
    ledger = evidence.get("snapshot_ledger")
    sources = evidence.get("sources")
    identity = evidence.get("identity")
    required_sources = {"m1", "plan", "m6", "remediation", "m3_manifest"}
    if (not isinstance(ledger, Mapping) or not isinstance(ledger.get("files"), list)
            or ledger.get("file_count") != len(ledger["files"])
            or not isinstance(ledger.get("total_bytes"), int)
            or not isinstance(ledger.get("base_sha"), str)
            or re.fullmatch(r"(?:[a-f0-9]{40}|[a-f0-9]{64})", ledger["base_sha"]) is None
            or not isinstance(ledger.get("snapshot_sha"), str)
            or re.fullmatch(r"(?:[a-f0-9]{40}|[a-f0-9]{64})", ledger["snapshot_sha"]) is None
            or not isinstance(sources, Mapping) or not required_sources <= set(sources)
            or not isinstance(identity, Mapping)):
        _refuse("complete source-bound captured snapshot ledger is required", "INVALID_EVIDENCE")
    source_digests: dict[str, str] = {}
    for name in required_sources:
        source = sources[name]
        if (not isinstance(source, Mapping) or not isinstance(source.get("document"), Mapping)
                or not isinstance(source.get("sha256"), str)
                or re.fullmatch(r"[a-f0-9]{64}", source["sha256"]) is None):
            _refuse("recovery evidence contains a missing, clipped, or unbound source", "INVALID_EVIDENCE")
        source_digests[name] = source["sha256"]
    ledger_rows = ledger["files"]
    ledger_paths = [row.get("path") for row in ledger_rows if isinstance(row, Mapping)]
    ledger_sizes = [row.get("size") for row in ledger_rows if isinstance(row, Mapping)]
    if (len(ledger_paths) != len(ledger_rows) or not all(isinstance(path, str) for path in ledger_paths)
            or len(ledger_paths) != len(set(ledger_paths)) or len(ledger_sizes) != len(ledger_rows)
            or not all(type(size) is int and size >= 0 for size in ledger_sizes)
            or sum(ledger_sizes) != ledger["total_bytes"]
            or any(not isinstance(row.get("path"), str) or not _path(row["path"])
                   or not isinstance(row.get("sha256"), str) or re.fullmatch(r"[a-f0-9]{64}", row["sha256"]) is None
                   or not isinstance(row.get("blob"), str) or re.fullmatch(r"(?:[a-f0-9]{40}|[a-f0-9]{64})", row["blob"]) is None
                   or type(row.get("size")) is not int or row["size"] < 0
                   for row in ledger_rows if isinstance(row, Mapping))):
        _refuse("snapshot ledger is clipped or contains malformed file provenance", "INVALID_EVIDENCE")
    if (identity.get("plan_sha256") != source_digests["plan"]
            or identity.get("plan_id") != plan.get("plan_id") or identity.get("revision") != plan.get("revision")):
        _refuse("recovery evidence does not bind to the supplied frozen plan", "INVALID_EVIDENCE")
    path_fields = [evidence[key] for key in ("actual_changed_paths", "changed_paths", "actual_paths") if key in evidence]
    if len(path_fields) > 1 and any(value != path_fields[0] for value in path_fields[1:]):
        _refuse("evidence contains conflicting changed-path declarations", "UNKNOWN_PATH")
    actual_paths = path_fields[0] if path_fields else None
    if (not isinstance(actual_paths, (list, tuple)) or not actual_paths or len(actual_paths) != len(set(actual_paths))
            or not all(_path(p) for p in actual_paths)):
        _refuse("evidence must include actual changed paths", "UNKNOWN_PATH")
    file_rows = {row.get("path"): row for row in ledger["files"] if isinstance(row, Mapping)}
    if (set(actual_paths) - set(file_rows) or any(
            not isinstance(file_rows[path].get("sha256"), str)
            or re.fullmatch(r"[a-f0-9]{64}", file_rows[path]["sha256"]) is None for path in actual_paths)):
        _refuse("changed paths are absent from complete snapshot", "UNKNOWN_PATH")
    if not isinstance(proposal, Mapping) or proposal.get("schema_version") != "recovery-proposal/1":
        _refuse("proposal schema is not recovery-proposal/1", "INVALID_PROPOSAL")
    if proposal.get("confidence") not in {"confirmed", "reported"}:
        _refuse("proposal is not supported by confirmed evidence", "TEXT_ONLY_PROPOSAL")
    proposal_refs = proposal.get("evidence_refs", [])
    if (not isinstance(proposal_refs, list)
            or any(not isinstance(ref, str) or re.fullmatch(r"[a-z][a-z0-9_-]{0,31}:[a-f0-9]{64}", ref) is None
                   or ref.split(":", 1)[1] not in source_digests.values() for ref in proposal_refs)):
        _refuse("proposal references evidence outside the captured, source-bound record", "INVALID_EVIDENCE")
    actions = proposal.get("actions")
    if not isinstance(actions, list) or not actions:
        _refuse("proposal has no executable constrained actions", "UNSUPPORTED_ACTION")
    tasks = copy.deepcopy(plan["tasks"])
    by_id = {row.get("id"): row for row in tasks if isinstance(row, dict)}
    if len(by_id) != len(tasks):
        _refuse("plan contains malformed or duplicate task identities", "INVALID_PLAN")
    audit_ids = [row["id"] for row in tasks if row.get("kind") == "audit"]
    if len(audit_ids) == 1 and second_auditor_required(dict(plan)):
        original = by_id[audit_ids[0]]
        taken = set(by_id)
        match = re.fullmatch(r"(T[0-9]+(?:\.[0-9]+)?)", original["id"])
        cross_id = next((original["id"] + letter for letter in "bcdefghijklmnopqrstuvwxyz"
                         if match and original["id"] + letter not in taken), None)
        if cross_id is None:
            cross_id = f"T{max([int(m.group(1)) for task_id in taken
                                  if isinstance(task_id, str) and (m := re.match(r"T([0-9]+)", task_id))] or [0]) + 1}"
        clone = copy.deepcopy(original)
        clone["id"] = cross_id
        clone["title"] = f"Cross-check audit of {original['id']}: {original.get('title', '')}"[:200]
        clone["objective"] = (f"An independent second audit of the scope of {original['id']}. Do not read its report or ledger "
                               "first: confirm findings yourself and record every one in your own ledger.")
        paths = original.get("expected_paths", [])
        old_report = next((path for path in paths if isinstance(path, str) and path.endswith(".md")), None)
        stem = old_report[:-3] if old_report else next(
            (path[:-len(".findings.json")] for path in paths
             if isinstance(path, str) and path.endswith(".findings.json")), original["id"].lower())
        new_stem = f"{stem}-crosscheck"
        clone["expected_paths"] = ([f"{new_stem}.md"] if old_report else []) + [f"{new_stem}.findings.json"]
        if old_report:
            for check in clone.get("verification", []):
                if isinstance(check, dict) and isinstance(check.get("value"), str):
                    check["value"] = check["value"].replace(old_report, f"{new_stem}.md")
        clone["estimate_rationale"] = (f"Independent cross-check of {original['id']}: "
                                       + str(original.get("estimate_rationale", "")))[:400]
        tasks.append(clone)
        by_id[cross_id] = clone
        audit_ids.append(cross_id)
    scope: set[str] = set()
    owners: set[str] = set()
    bootstrap_consumers: list[str] = []
    convergence_task_id: str | None = None
    convergence_consumer_ids: set[str] = set()
    for action in actions:
        if not isinstance(action, Mapping) or action.get("type") not in {"correct_tasks", "repair_verification", "refresh_integrated_audit"}:
            _refuse("unsupported recovery action", "UNSUPPORTED_ACTION")
        action_fields = {
            "correct_tasks": {"type", "owner_task_id", "task_ids", "replacements"},
            "repair_verification": {"type", "owner_task_id", "task_ids", "verification"},
            "refresh_integrated_audit": {"type", "owner_task_id", "task_ids", "after"},
        }[action["type"]]
        if set(action) - action_fields:
            _refuse("recovery action contains unsupported fields", "INVALID_ACTION")
        owner_id = action.get("owner_task_id")
        if not _task_id(owner_id) or owner_id not in by_id:
            _refuse("action names unknown owner task", "UNKNOWN_TASK")
        owners.add(owner_id)
        task_ids = action.get("task_ids", [owner_id])
        if not isinstance(task_ids, list) or not task_ids:
            _refuse("action task scope is missing", "UNKNOWN_TASK")
        for task_id in task_ids:
            if task_id not in by_id:
                _refuse("action names unknown task", "UNKNOWN_TASK")
            owner_scopes = by_id[owner_id].get("expected_paths", [])
            task_scopes = by_id[task_id].get("expected_paths", [])
            if not isinstance(owner_scopes, list) or not isinstance(task_scopes, list) or any(
                    not any(path == owner_path or path.startswith(owner_path.rstrip("/") + "/")
                            for owner_path in owner_scopes if isinstance(owner_path, str))
                    for path in task_scopes if isinstance(path, str)):
                _refuse("action task is outside the named owner scope", "OWNER_SCOPE_CHANGED")
        if action["type"] == "correct_tasks":
            replacements = action.get("replacements")
            if not isinstance(replacements, list) or not replacements:
                _refuse("correct_tasks requires scoped task replacements", "INVALID_ACTION")
            for replacement in replacements:
                if not isinstance(replacement, Mapping) or replacement.get("id") not in task_ids:
                    _refuse("replacement escapes the named task scope", "UNKNOWN_TASK")
                old = by_id[replacement["id"]]
                if replacement.get("kind", old.get("kind")) != old.get("kind"):
                    _refuse("corrective replacement cannot change task kind", "WEAKENED_CRITERIA")
                if old.get("kind") == "audit":
                    _refuse("correct_tasks cannot replace an independent audit scope", "WEAKENED_GATES")
                for frozen_key in ("repository", "milestone_id", "covers", "expected_paths", "shared_resources"):
                    if frozen_key in replacement and replacement[frozen_key] != old.get(frozen_key, []):
                        _refuse(f"replacement cannot change frozen {frozen_key}", "WEAKENED_CRITERIA")
                if "after" in replacement and not set(old.get("after", [])) <= set(replacement["after"]):
                    _refuse("replacement cannot remove frozen task dependencies", "WEAKENED_GATES")
                if "expected_paths" in replacement and replacement["expected_paths"] != old.get("expected_paths", []):
                    _refuse("replacement cannot change inherited owner paths", "OWNER_SCOPE_CHANGED")
                for key in ("acceptance_criteria",):
                    if key in replacement and not set(old.get(key, [])) <= set(replacement[key] if isinstance(replacement[key], list) else []):
                        _refuse(f"replacement weakens frozen {key}", "WEAKENED_CRITERIA")
                updated = copy.deepcopy(dict(replacement))
                old_verification = old.get("verification", [])
                new_verification = updated.get("verification", old_verification)
                if (not isinstance(old_verification, list) or not isinstance(new_verification, list)
                        or not all(item in new_verification for item in old_verification)):
                    _refuse("corrective replacement must preserve every frozen verification check", "WEAKENED_CHECKS")
                for item in new_verification:
                    if isinstance(item, Mapping) and item not in old_verification:
                        if (item.get("type") != "command" or item.get("created_by") != replacement["id"]
                                or not _safe_command(item.get("value"))):
                            _refuse("new corrective verification must be a safe command authored by its task", "UNSAFE_COMMAND")
                if updated != old:
                    scope.add(replacement["id"])
                by_id[replacement["id"]].update(updated)
        elif action["type"] == "repair_verification":
            for task_id in task_ids:
                extra = action.get("verification", [])
                if not isinstance(extra, list):
                    _refuse("verification repair must be additive", "INVALID_ACTION")
                for row in extra:
                    if (not isinstance(row, Mapping) or row.get("type") != "command" or not _safe_command(row.get("value"))
                            or row.get("created_by") != task_id):
                        _refuse("verification repair contains unsafe or invalid command", "UNSAFE_COMMAND")
                current = by_id[task_id].get("verification", [])
                if not isinstance(current, list):
                    _refuse("existing task verification checks are malformed", "INVALID_PLAN")
                by_id[task_id]["verification"] = current + copy.deepcopy(extra)
                if extra:
                    scope.add(task_id)
        else:
            task = by_id[owner_id]
            if task.get("kind") != "audit":
                _refuse("refresh_integrated_audit must target an audit task", "INVALID_ACTION")
            after = action.get("after", [])
            if not isinstance(after, list) or not all(item in by_id for item in after):
                _refuse("audit refresh names unknown dependencies", "INVALID_ACTION")
            updated_after = list(dict.fromkeys(task.get("after", []) + after))
            if updated_after != task.get("after", []):
                task["after"] = updated_after
                scope.add(owner_id)
    integration_predecessors = set(scope) - set(audit_ids)
    if convergence is not None:
        if not isinstance(convergence, Mapping) or convergence.get("schema_version") != "convergence-work/1":
            _refuse("convergence input schema is invalid", "INVALID_CONVERGENCE")
        allowed_convergence = {"schema_version", "convergence_task", "rebuilt_tasks", "consumer_updates", "bootstrap",
                               "exclusive_side", "side_choice", "actions", "evidence_refs", "replaced_task_ids"}
        if set(convergence) - allowed_convergence:
            _refuse("convergence input contains unsupported fields", "INVALID_CONVERGENCE")
        if convergence.get("exclusive_side") or convergence.get("side_choice"):
            _refuse("exclusive-side convergence is forbidden", "EXCLUSIVE_SIDE")
        rebuilds = convergence.get("rebuilt_tasks", [])
        if not isinstance(rebuilds, list):
            _refuse("convergence rebuilt_tasks is malformed", "INVALID_CONVERGENCE")
        producer = convergence.get("convergence_task")
        owner_rows = [by_id[owner_id] for owner_id in sorted(owners)]

        def validate_convergence_scope(row: Mapping[str, Any]) -> None:
            allowed_paths = [path for owner in owner_rows for path in owner.get("expected_paths", [])
                             if isinstance(path, str)]
            expected_paths = row.get("expected_paths")
            if (not isinstance(expected_paths, list) or not expected_paths
                    or any(not isinstance(path, str) or not any(
                        path == owner_path or path.startswith(owner_path.rstrip("/") + "/")
                        for owner_path in allowed_paths) for path in expected_paths)):
                _refuse("convergence task escapes the named recovery owners' paths", "OWNER_SCOPE_CHANGED")
            if not owner_rows or not any(row.get("repository") == owner.get("repository")
                                         and row.get("milestone_id") == owner.get("milestone_id")
                                         for owner in owner_rows):
                _refuse("convergence task changes repository or milestone ownership", "OWNER_SCOPE_CHANGED")
            inherited_requirements = {item for owner in owner_rows for item in owner.get("covers", [])}
            if not isinstance(row.get("covers"), list) or not set(row["covers"]) <= inherited_requirements:
                _refuse("convergence task adds requirements outside the named owners", "WEAKENED_CRITERIA")

        if isinstance(producer, Mapping):
            row = _task_record(producer, existing_ids=set(by_id), label="convergence_task")
            validate_convergence_scope(row)
            convergence_task_id = row["id"]
            if row.get("kind") != "implement":
                _refuse("convergence producer must be an implement task", "INVALID_CONVERGENCE")
            if not isinstance(row.get("acceptance_criteria"), list) or not row["acceptance_criteria"]:
                _refuse("convergence producer must retain explicit behavior acceptance criteria", "INVALID_CONVERGENCE")
            for check in row.get("verification", []):
                if isinstance(check, Mapping) and check.get("type") == "command" and check.get("created_by") != convergence_task_id:
                    _refuse("new convergence checks must be authored by the convergence task", "INVALID_CONVERGENCE")
            tasks.append(row)
            by_id[convergence_task_id] = row
            scope.add(convergence_task_id)
            integration_predecessors.add(convergence_task_id)
        elif isinstance(producer, str) and producer in {row.get("id") for row in rebuilds if isinstance(row, Mapping)}:
            convergence_task_id = producer
            scope.add(producer)
            integration_predecessors.add(producer)
        else:
            _refuse("convergence_task must be a new complete task or a declared new rebuilt task", "INVALID_CONVERGENCE")
        for raw in rebuilds:
            row = _task_record(raw, existing_ids=set(by_id), label="rebuilt_task")
            validate_convergence_scope(row)
            if row.get("kind") != "implement":
                _refuse("rebuilt convergence work must be an implement task", "INVALID_CONVERGENCE")
            if not isinstance(row.get("acceptance_criteria"), list) or not row["acceptance_criteria"]:
                _refuse("rebuilt task must retain explicit acceptance criteria", "INVALID_CONVERGENCE")
            for check in row.get("verification", []):
                if isinstance(check, Mapping) and check.get("type") == "command" and check.get("created_by") != row["id"]:
                    _refuse("new rebuilt checks must be authored by their task", "INVALID_CONVERGENCE")
            tasks.append(row)
            by_id[row["id"]] = row
            scope.add(row["id"])
            integration_predecessors.add(row["id"])
        if len(rebuilds) + (1 if isinstance(producer, Mapping) else 0) > 8:
            _refuse("convergence work exceeds the shared eight-task allowance", "CONVERGENCE_BUDGET")
        replaced_ids_raw = convergence.get("replaced_task_ids", [])
        if (not isinstance(replaced_ids_raw, list) or len(replaced_ids_raw) != len(set(replaced_ids_raw))
                or not all(_task_id(task_id) and task_id in by_id for task_id in replaced_ids_raw)):
            _refuse("convergence replacement references unknown tasks", "INVALID_CONVERGENCE")
        if convergence.get("actions", []) != []:
            _refuse("structural work must use convergence-work fields, not embedded proposal actions", "INVALID_CONVERGENCE")
        evidence_refs = convergence.get("evidence_refs", [])
        if not isinstance(evidence_refs, list) or any(
                not isinstance(ref, str) or re.fullmatch(r"[a-z][a-z0-9_-]{0,31}:[a-f0-9]{64}", ref) is None
                for ref in evidence_refs):
            _refuse("convergence evidence references are malformed or text-only", "INVALID_CONVERGENCE")
        updates = convergence.get("consumer_updates", [])
        if updates:
            if not isinstance(updates, list):
                _refuse("convergence consumer_updates is malformed", "INVALID_CONVERGENCE")
            update_ids: set[str] = set()
            for update in updates:
                if (not isinstance(update, Mapping) or set(update) - {"task_id", "after", "remove_after"}
                        or update.get("task_id") not in by_id or not isinstance(update.get("after"), list)
                        or not isinstance(update.get("remove_after", []), list)):
                    _refuse("convergence consumer update is invalid", "INVALID_CONVERGENCE")
                if update["task_id"] in update_ids:
                    _refuse("convergence consumer is updated more than once", "INVALID_CONVERGENCE")
                update_ids.add(update["task_id"])
                task = by_id[update["task_id"]]
                previous = task.get("after", [])
                removals = update.get("remove_after", [])
                replacements = replaced_ids_raw
                if (not isinstance(previous, list) or not set(removals) <= set(previous)
                        or not set(removals) <= set(replacements)
                        or not all(item in by_id for item in update["after"])):
                    _refuse("consumer rewire removes unrelated prerequisites or adds unknown tasks", "INVALID_CONVERGENCE")
                task["after"] = [item for item in previous if item not in removals]
                task["after"] = list(dict.fromkeys(task["after"] + update["after"]))
                convergence_consumer_ids.add(update["task_id"])
                scope.add(update["task_id"])
                integration_predecessors.add(update["task_id"])
        bootstrap = convergence.get("bootstrap")
        if bootstrap is None:
            _refuse("structural convergence requires its validated conflict envelope", "INVALID_CONVERGENCE")
        if bootstrap is not None:
            if not isinstance(bootstrap, Mapping) or convergence_task_id is None:
                _refuse("convergence bootstrap must be a complete task-bound conflict envelope", "INVALID_CONVERGENCE")
            bootstrap_schema = bootstrap.get("schema_version")
            if bootstrap_schema == "conflict-observation/1":
                try:
                    observation = parse_conflict_observation(bootstrap)
                except (TypeError, ValueError) as error:
                    _refuse(f"T3a conflict observation is invalid: {type(error).__name__}", "INVALID_CONVERGENCE")
                if (observation.task_id not in by_id or not observation.paths
                        or not set(observation.paths) <= set(actual_paths)
                        or not set(observation.paths) <= set(file_rows)):
                    _refuse("T3a conflict paths or task are outside the captured frozen plan", "INVALID_CONVERGENCE")
                preservation_inputs = [side.to_dict() for side in observation.sides]
                bootstrap_consumers = sorted(convergence_consumer_ids)
            elif (bootstrap_schema != "conflict-bootstrap/1" or bootstrap.get("task_id") != convergence_task_id
                    or not isinstance(bootstrap.get("paths"), list) or not bootstrap["paths"]
                    or not all(_path(path) and path in file_rows for path in bootstrap["paths"])):
                _refuse("convergence bootstrap must be a complete task-bound conflict envelope", "INVALID_CONVERGENCE")
            else:
                bootstrap_consumers = bootstrap.get("consumer_task_ids", [])
                if (not isinstance(bootstrap_consumers, list)
                        or not all(_task_id(task_id) and task_id in by_id for task_id in bootstrap_consumers)
                        or not set(bootstrap_consumers) <= convergence_consumer_ids):
                    _refuse("convergence bootstrap names an unknown descendant", "INVALID_CONVERGENCE")
                preservation_inputs = bootstrap.get("preservation_inputs", bootstrap.get("sides"))
            if not isinstance(preservation_inputs, list) or len(preservation_inputs) < 2 or not all(
                    isinstance(item, Mapping) for item in preservation_inputs):
                _refuse("conflict bootstrap must retain both accepted-side preservation inputs", "INVALID_CONVERGENCE")
            side_ids, side_digests = [], []
            for item in preservation_inputs:
                side_id = next((item.get(key) for key in ("side", "task_id", "source_id", "role")
                                if isinstance(item.get(key), str) and item.get(key)), None)
                digest_value = next((item.get(key) for key in ("sha256", "source_digest", "snapshot_sha", "snapshot_digest")
                                     if isinstance(item.get(key), str)), None)
                if (side_id is None or digest_value is None
                        or re.fullmatch(r"(?:[a-f0-9]{40}|[a-f0-9]{64})", digest_value) is None):
                    _refuse("conflict bootstrap preservation input lacks a bound side identity", "INVALID_CONVERGENCE")
                side_ids.append(side_id)
                side_digests.append(digest_value)
            if len(set(side_ids)) != len(side_ids) or len(set(side_digests)) != len(side_digests):
                _refuse("conflict bootstrap preservation sides must be distinct", "INVALID_CONVERGENCE")
            replaced_ids = set(replaced_ids_raw)
            for consumer_id in bootstrap_consumers:
                after = by_id[consumer_id].get("after", [])
                if convergence_task_id not in after or replaced_ids.intersection(after):
                    _refuse("bootstrap consumer must depend on accepted convergence and remove replaced ancestors", "INVALID_CONVERGENCE")
            if len(preservation_inputs) < 2 or preservation_inputs[0] == preservation_inputs[1]:
                _refuse("both original sides must be preserved as distinct inputs", "INVALID_CONVERGENCE")
            scope.update(bootstrap_consumers)
    oracle = proposal.get("symptom_oracle")
    if (not isinstance(oracle, Mapping) or not _safe_command(oracle.get("red_command"))
            or not _safe_command(oracle.get("command")) or not isinstance(oracle.get("symptom"), str)
            or not oracle["symptom"].strip()):
        _refuse("a symptom oracle with captured-source red and integrated-tree green commands is required", "MISSING_ORACLE")
    affected_owners = []
    frozen_tasks = [row for row in plan["tasks"] if isinstance(row, Mapping)]
    for path in actual_paths:
        matches = [task for task in frozen_tasks if any(path == p or path.startswith(p.rstrip("/") + "/") for p in task.get("expected_paths", []) if isinstance(p, str))]
        if len(matches) != 1:
            _refuse(f"changed path has ambiguous or unknown owner: {path}", "UNKNOWN_OWNER")
        affected_owners.append(matches[0]["id"])
    if not set(affected_owners) <= owners:
        _refuse("proposal actions do not name every owner of the changed paths", "UNKNOWN_OWNER")
    integration_predecessors.update(affected_owners)
    checks = coverage_checks({"tasks": tasks}, list(dict.fromkeys(affected_owners)), actual_paths, oracle["symptom"])
    oracle_owner = affected_owners[0]
    checks.append({"check_id": f"{oracle_owner}:oracle", "owner_task_id": oracle_owner,
                   "command": oracle["command"], "symptom": _slug(oracle["symptom"])})
    vm = {"schema_version": "recovery-verification-map/1",
          "changed_paths": [{"path": path, "source_digest": file_rows[path].get("sha256"), "owner_task_id": owner}
                            for path, owner in zip(actual_paths, affected_owners)],
          "checks": [], "existing_owner_commands": sorted({c for owner in affected_owners for c in _commands(by_id[owner])} | {oracle["command"]}),
          "uncovered_paths": [], "uncovered_checks": []}
    for check_index, check in enumerate(checks, start=1):
        vm["checks"].append({"check_id": f"CHECK-{check_index:03d}", "owner_task_id": check["owner_task_id"],
                             "command": check["command"], "symptom": _slug(check["symptom"]),
                             "verdict_identity": "m6:" + source_digests["m6"]})
    new_id_num = max([int(m.group(1)) for t in tasks if isinstance(t.get("id"), str) and (m := re.fullmatch(r"T([0-9]+)", t["id"]))] or [0]) + 1
    integration_id = f"T{new_id_num}"
    if not audit_ids:
        _refuse("frozen plan has no independent audit scopes", "MISSING_AUDIT")
    # Add an integration command task to run the union; both audit scopes depend on it.
    template = copy.deepcopy(by_id[affected_owners[0]])
    integration = {**template, "id": integration_id, "title": "Run integrated recovery verification",
                   "objective": "Run all owner verification and the symptom regression oracle on the integrated tree.",
                   "kind": "test", "after": sorted(integration_predecessors), "expected_paths": list(dict.fromkeys(actual_paths)),
                   "acceptance_criteria": ["All affected owner checks and the symptom regression oracle pass on the integrated tree."],
                   "verification": [{"type": "command", "value": row["command"], "purpose": "Run union owner verification", "created_by": integration_id,
                                     "category": "integration"} for row in checks] +
                                  [{"type": "command", "value": oracle["red_command"],
                                    "purpose": f"Red step: reproduce {oracle['symptom']} on the captured broken source using only the test overlay",
                                    "created_by": integration_id, "category": "regression"}] +
                                  [{"type": "command", "value": oracle["command"], "purpose": oracle["symptom"], "created_by": integration_id, "category": "regression"}]}
    owner_verification = by_id[oracle_owner].setdefault("verification", [])
    owner_verification.append({"type": "command", "value": oracle["command"],
                               "purpose": f"Symptom oracle: {oracle['symptom']}",
                               "created_by": integration_id, "category": "regression"})
    tasks.append(integration)
    scope.add(integration_id)
    integration_ancestors = set(integration_predecessors)
    pending = list(integration_predecessors)
    while pending:
        current_id = pending.pop()
        dependencies = by_id.get(current_id, {}).get("after", [])
        if not isinstance(dependencies, list):
            continue
        for dependency in dependencies:
            if dependency in by_id and dependency not in integration_ancestors:
                integration_ancestors.add(dependency)
                pending.append(dependency)
    for task in tasks:
        task_id = task.get("id")
        if task_id == integration_id or task_id in integration_ancestors or task_id in audit_ids:
            continue
        dependencies = task.get("after", [])
        if isinstance(dependencies, list) and integration_predecessors.intersection(dependencies):
            task["after"] = [dependency for dependency in dependencies if dependency not in integration_predecessors]
            task["after"] = list(dict.fromkeys(task["after"] + [integration_id]))
            scope.add(task_id)
    for task in tasks:
        if task.get("id") in audit_ids:
            task["after"] = list(dict.fromkeys(task.get("after", []) + [integration_id]))
            scope.add(task["id"])
    original_by_id = {row.get("id"): row for row in plan["tasks"] if isinstance(row, Mapping)}
    revised_by_id = {row.get("id"): row for row in tasks if isinstance(row, Mapping)}
    scope = {task_id for task_id in set(original_by_id) | set(revised_by_id)
             if original_by_id.get(task_id) != revised_by_id.get(task_id)}
    result_plan = copy.deepcopy(dict(plan))
    result_plan["tasks"] = tasks
    result_plan["revision"] = int(plan.get("revision", 0)) + 1
    errors = validate_candidate(result_plan)
    if errors:
        _refuse("Planner rejected compiled candidate: " + "; ".join(errors[:5]), "PLANNER_INVALID")
    try:
        parse_verification_map(vm)
    except (TypeError, ValueError) as error:
        _refuse(f"M5 rejected the compiled verification map: {type(error).__name__}", "INVALID_VERIFICATION_MAP")
    return RecoveryRevision(result_plan, tuple(sorted(scope)), vm)
