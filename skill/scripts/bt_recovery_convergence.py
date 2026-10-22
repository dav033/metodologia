"""Pure compiler for provenance-preserving structural conflict convergence work.

The compiler never changes plan state or accepts an attempt. It emits a bounded work
package whose eventual base is selected through the ordinary accepted-attempt ledger.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re

import bt_recovery_cycle
from bt_scheduler_recovery.conflict_contracts import (
    ConflictLineageFacts,
    ConflictObservation,
    ConflictPlanFacts,
    ConflictStrategy,
)

SCHEMA = "convergence-work/1"
_HEX = re.compile(r"[0-9a-f]{64}")
_SHA = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})")
class ConvergenceError(ValueError):
    """Conflict strategy is stale, unjustified, unsafe, or incomplete."""


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _path(value: object) -> bool:
    return (type(value) is str and bool(value) and len(value) <= 512 and not value.startswith("/") and
            "\\" not in value and "\x00" not in value and
            all(part not in ("", ".", "..") for part in value.split("/")))


def _command(check: object) -> bool:
    return (isinstance(check, dict) and check.get("type") == "command" and
            isinstance(check.get("value"), str) and bool(check["value"].strip()))


def _unique(values: object, label: str) -> list:
    if not isinstance(values, list) or any(type(value) is not str or not value for value in values):
        raise ConvergenceError(f"{label} is missing or invalid")
    if len(values) != len(set(values)):
        raise ConvergenceError(f"{label} contains duplicates")
    return values


def _source_sides(observation: dict, evidence: dict) -> list[dict]:
    """Bind full source identities to the compact, hash-only T3b observation."""
    sources = evidence.get("sources")
    if not isinstance(sources, list) or len(sources) != len(observation["sides"]):
        raise ConvergenceError("immutable source snapshots are incomplete")
    by_key = {(item.get("role"), item.get("task_id"), item.get("attempt_id")): item
              for item in sources if isinstance(item, dict)}
    result = []
    for side in observation["sides"]:
        source = by_key.get((side["role"], side["task_id"], side["attempt_id"]))
        if not isinstance(source, dict):
            raise ConvergenceError("immutable source snapshot identity mismatch")
        for field, digest_field in (("base_sha", "base_digest"), ("snapshot_sha", "snapshot_digest"),
                                    ("tree_sha", "tree_digest")):
            value = source.get(field)
            if not isinstance(value, str) or not _SHA.fullmatch(value) or \
                    hashlib.sha256(value.encode()).hexdigest() != side[digest_field]:
                raise ConvergenceError("immutable source snapshot digest mismatch")
        result.append({"role": side["role"], "task_id": side["task_id"], "attempt_id": side["attempt_id"],
                       "base_sha": source["base_sha"], "snapshot_sha": source["snapshot_sha"],
                       "tree_sha": source["tree_sha"]})
    return result


def plan_conflict_convergence(plan, observation, strategy) -> dict:
    """Compile T3a conflict facts and immutable evidence into ``convergence-work/1``.

    Expected auxiliary evidence fields are ``lineage_facts``, ``plan_facts``,
    ``sources``, ``owners`` (task ID to owned paths/requirements), ``current_base``
    (repository ID to accepted snapshot), and ``symptom_oracle``. Checks are copied
    from frozen owner tasks and cannot be weakened by strategy input.
    """
    if not isinstance(plan, dict) or not isinstance(observation, dict) or not isinstance(strategy, dict):
        raise ConvergenceError("plan, observation and strategy must be objects")
    envelope = observation
    observation = envelope.get("observation")
    if not isinstance(observation, dict):
        raise ConvergenceError("validated conflict observation envelope is missing")
    try:
        observed = ConflictObservation.from_dict(observation)
        selected = ConflictStrategy.from_dict(strategy)
        plan_facts = ConflictPlanFacts.from_dict(envelope.get("plan_facts"))
        lineage = ConflictLineageFacts.from_dict(envelope.get("lineage_facts"))
    except (TypeError, ValueError, KeyError) as error:
        raise ConvergenceError("T3a facts, observation or strategy failed validation") from error

    if plan.get("plan_id") != observed.plan_id or plan.get("revision") != observed.revision or \
            plan.get("sha256") != observed.plan_sha256:
        raise ConvergenceError("observation is stale for the frozen plan")
    if (plan_facts.run_id != observed.run_id or plan_facts.plan_id != observed.plan_id or
            plan_facts.revision != observed.revision or plan_facts.plan_sha256 != observed.plan_sha256 or
            plan_facts.source_type != observed.source_type or plan_facts.task_id != observed.task_id or
            plan_facts.attempt_id != observed.attempt_id or plan_facts.token != observed.token or
            plan_facts.consumer_id != observed.consumer_id or plan_facts.repository_id != observed.repository_id or
            plan_facts.authority_status != "authorized"):
        raise ConvergenceError("current immutable plan authority does not match the observation")
    authorized_paths = (plan_facts.approved_start_paths if observed.source_type == "start"
                        else plan_facts.approved_integration_paths)
    if not set(observed.paths) <= set(authorized_paths):
        raise ConvergenceError("conflict paths exceed current immutable authorization")
    if lineage.status == "unknown" or not lineage.evidence_complete:
        raise ConvergenceError("complete current lineage evidence is required")
    if lineage.semantic_conflict or lineage.incompatible_requirements:
        raise ConvergenceError("product-semantic conflict requires an owner ruling")
    if selected.source_digests != tuple(observed.evidence_digests) or \
            selected.accepted_map_digest not in observed.evidence_digests:
        raise ConvergenceError("strategy is not bound to current immutable evidence")

    task_rows = plan.get("tasks")
    if not isinstance(task_rows, list):
        raise ConvergenceError("frozen plan tasks are missing")
    tasks = {row.get("id"): row for row in task_rows if isinstance(row, dict) and isinstance(row.get("id"), str)}
    if len(tasks) != len(task_rows):
        raise ConvergenceError("frozen task identities are invalid")
    owners = envelope.get("owners")
    current_base = envelope.get("current_base")
    accepted_map = envelope.get("accepted_map")
    if not isinstance(owners, dict) or not isinstance(current_base, dict):
        raise ConvergenceError("current owner scopes and accepted bases are required")
    if not isinstance(accepted_map, dict) or _digest(accepted_map) != selected.accepted_map_digest:
        raise ConvergenceError("current accepted-attempt map is missing or stale")
    source_sides = _source_sides(observation, envelope)
    for side in source_sides:
        if side["role"] == "accepted" and accepted_map.get(side["task_id"]) != side["attempt_id"]:
            raise ConvergenceError("accepted conflict source is no longer current")
    relevant_paths = set(observed.paths)
    path_digests = {_digest(path): path for path in relevant_paths}
    if set(selected.path_digests) != set(path_digests):
        raise ConvergenceError("strategy paths differ from the complete observed conflict paths")

    stale = lineage.status == "stale"
    owned_defect = lineage.ownership_or_order_defect
    needed = set()
    if stale:
        needed.add("rebuild_stale_descendant")
    if owned_defect:
        needed.add("converge_owned_paths")
    if lineage.demonstrated_future_defect:
        needed.add("repair_demonstrated_future_ownership_order")
    # Frozen owner checks are always included. Record their union as an explicit
    # strategy action even when stale and future defects consume all other actions.
    if owned_defect:
        needed.add("inherit_additive_checks")
    if not needed or set(selected.actions) != needed:
        raise ConvergenceError("strategy actions do not match the minimum justified recovery actions")
    if not owned_defect:
        raise ConvergenceError("stale lineage alone cannot authorize an owned-path convergence writer")

    affected_ids = sorted({side["task_id"] for side in source_sides})
    if any(task_id not in tasks or task_id not in owners for task_id in affected_ids):
        raise ConvergenceError("conflict source lacks a frozen task or ownership record")
    if any(not isinstance(tasks[task_id].get("acceptance_criteria"), list)
           or not tasks[task_id]["acceptance_criteria"]
           or not isinstance(tasks[task_id].get("covers", []), list) for task_id in affected_ids):
        raise ConvergenceError("both frozen source acceptance contracts are required")
    # Preserve the exact deltas and accepted snapshots. A source can be rebuilt only when
    # the evidence names the descendant and its old base explicitly.
    preservation = []
    delta_map = envelope.get("delta_paths")
    if not isinstance(delta_map, dict):
        raise ConvergenceError("exact source delta paths are required for preservation")
    for side in source_sides:
        owner = owners[side["task_id"]]
        owned = set(owner.get("paths", [])) if isinstance(owner, dict) else set()
        if not relevant_paths <= owned:
            raise ConvergenceError("conflict source does not own every observed conflict path")
        delta_paths = _unique(delta_map.get(side["attempt_id"]), "source delta paths")
        if not set(delta_paths) <= owned:
            raise ConvergenceError("source preservation delta escapes its frozen owner scope")
        preservation.append({**side, "preserve_delta": {"from": side["base_sha"], "snapshot": side["snapshot_sha"],
                            "paths": sorted(delta_paths)}})

    # One convergence writer owns each concrete path; it must preserve both requirements.
    requirements = []
    for task_id in affected_ids:
        values = owners[task_id].get("requirements")
        if not isinstance(values, list) or not values or any(not isinstance(value, str) or not value.strip() for value in values):
            raise ConvergenceError("both source requirements must be explicit")
        requirements.extend({"owner_task_id": task_id, "text": value} for value in values)
    checks = []
    for task_id in affected_ids:
        frozen_checks = tasks[task_id].get("verification", [])
        if not isinstance(frozen_checks, list):
            raise ConvergenceError("frozen owner verification is malformed")
        for check in frozen_checks:
            if _command(check):
                checks.append({**copy.deepcopy(check), "owner_task_id": task_id})
    if not checks:
        raise ConvergenceError("union of frozen owner verification commands is empty")
    if {check["owner_task_id"] for check in checks} != set(affected_ids):
        raise ConvergenceError("frozen verification command union must cover both conflict owners")
    # The final symptom oracle is separately bound below; strategy hashes cover the
    # inherited owner checks only, so callers cannot smuggle in a weaker subset.
    inherited_check_digests = {_digest(check) for check in checks}
    if set(selected.check_digests) != inherited_check_digests:
        raise ConvergenceError("strategy verification checks differ from the frozen owner command union")

    oracle = envelope.get("symptom_oracle")
    red_provenance = oracle.get("red_provenance") if isinstance(oracle, dict) else None
    if not isinstance(oracle, dict) or not _path(oracle.get("path")) or not isinstance(oracle.get("command"), str) or \
            not oracle["command"].strip() or not isinstance(oracle.get("red_command"), str) or \
            not oracle["red_command"].strip() or oracle["path"] not in relevant_paths or \
            oracle.get("red_on_conflict") is not True or oracle.get("green_on_result") is not True or \
            not isinstance(red_provenance, dict) or \
            red_provenance.get("captured_attempt_id") not in {side["attempt_id"] for side in source_sides} or \
            red_provenance.get("failure_kind") != "symptom" or \
            not isinstance(red_provenance.get("source_digest"), str) or \
            not _HEX.fullmatch(red_provenance["source_digest"]) or \
            red_provenance.get("source_digest") not in {
                side.tree_digest for side in observed.sides
                if side.attempt_id == red_provenance.get("captured_attempt_id")} | {
                side.snapshot_digest for side in observed.sides
                if side.attempt_id == red_provenance.get("captured_attempt_id")} or \
            red_provenance.get("command_digest") != _digest(oracle["red_command"]):
        raise ConvergenceError("a conflict-red symptom oracle on an authorized path is required")
    checks.append({"type": "command", "value": oracle["red_command"],
                   "purpose": "Red step: reproduce the conflict symptom on the captured source",
                   "category": "regression", "owner_task_id": oracle.get("owner_task_id")})
    checks.append({"type": "command", "value": oracle["command"], "purpose": "Conflict symptom oracle",
                   "category": "regression", "owner_task_id": oracle.get("owner_task_id")})
    marker_check = envelope.get("marker_check")
    if not _command(marker_check):
        raise ConvergenceError("a marker-free result check is required")
    checks.append({**copy.deepcopy(marker_check), "purpose": "No unresolved conflict markers", "category": "integration"})

    task_id = envelope.get("convergence_task_id")
    if not isinstance(task_id, str) or not re.fullmatch(r"T[0-9]+(?:\.[0-9]+)?[a-z]?", task_id) or task_id in tasks:
        raise ConvergenceError("a fresh convergence task identity is required")
    repo_id = observed.repository_id
    owner_rows = [tasks[owner_id] for owner_id in affected_ids]
    milestone_ids = {row.get("milestone_id") for row in owner_rows}
    if len(milestone_ids) != 1 or None in milestone_ids:
        raise ConvergenceError("conflict owners must share their frozen milestone")
    covers = sorted({requirement for row in owner_rows for requirement in row.get("covers", [])
                     if isinstance(requirement, str)})
    prior_acceptance = [criterion for row in owner_rows for criterion in row.get("acceptance_criteria", [])
                        if isinstance(criterion, str) and criterion.strip()]
    if len(prior_acceptance) != sum(len(row.get("acceptance_criteria", [])) for row in owner_rows):
        raise ConvergenceError("both source acceptance contracts must remain explicit")
    base = current_base.get(repo_id)
    base_manifest = base.get("m3_manifest") if isinstance(base, dict) else None
    if not isinstance(base, dict) or not isinstance(base.get("accepted_attempt_id"), str) or \
            not isinstance(base.get("snapshot_sha"), str) or not _SHA.fullmatch(base["snapshot_sha"]) or \
            base.get("accepted_map_digest") != selected.accepted_map_digest or \
            accepted_map.get(base.get("task_id")) != base.get("accepted_attempt_id") or \
            not isinstance(base_manifest, dict) or base_manifest.get("attempt_id") != base.get("accepted_attempt_id") or \
            base_manifest.get("snapshot_sha") != base.get("snapshot_sha") or \
            _digest(base_manifest) not in observed.evidence_digests:
        raise ConvergenceError("current accepted predecessor base is missing")
    predecessor_ids = envelope.get("nonconflicting_predecessor_closure")
    if not isinstance(predecessor_ids, list) or any(item not in tasks for item in predecessor_ids):
        raise ConvergenceError("current nonconflicting predecessor closure is invalid")
    if set(predecessor_ids) & set(affected_ids):
        raise ConvergenceError("bootstrap must not depend on either incompatible source task")
    marker_paths = _unique(envelope.get("marker_paths"), "authorized marker paths")
    owner_union = {path for owner_id in affected_ids for path in owners[owner_id].get("paths", [])}
    if set(marker_paths) != relevant_paths or not relevant_paths <= owner_union:
        raise ConvergenceError("authorized marker paths differ from the owned conflict paths")
    future_defect = lineage.demonstrated_future_defect
    consumers = envelope.get("affected_consumers", [])
    if not isinstance(consumers, list) or any(item not in tasks for item in consumers):
        raise ConvergenceError("affected consumer list is invalid")
    receipt = envelope.get("lineage_receipt")
    if consumers:
        if not isinstance(receipt, dict):
            raise ConvergenceError("validated lineage receipt is required to rewire consumers")
        receipt_payload = {key: value for key, value in receipt.items() if key != "sha256"}
        if receipt.get("schema_version") != "conflict-lineage-receipt/1" or \
                receipt.get("source_digests") != list(observed.evidence_digests) or \
                receipt.get("affected_consumers") != sorted(consumers) or \
                receipt.get("sha256") != _digest(receipt_payload):
            raise ConvergenceError("lineage receipt is stale or tampered")
        obsolete_edges = receipt.get("obsolete_edges")
        if not isinstance(obsolete_edges, list) or any(not isinstance(edge, dict) or
                edge.get("consumer_id") not in consumers or edge.get("source_task_id") not in affected_ids
                for edge in obsolete_edges):
            raise ConvergenceError("lineage receipt contains unauthorized dependency removals")
    else:
        obsolete_edges = []
    consumer_updates = []
    for consumer in consumers:
        old = tasks[consumer]
        old_after = old.get("after", [])
        if not isinstance(old_after, list):
            raise ConvergenceError("frozen consumer prerequisites are malformed")
        removals = {edge["source_task_id"] for edge in obsolete_edges if edge["consumer_id"] == consumer}
        required_removals = set(old_after) & set(affected_ids)
        if not required_removals <= removals:
            raise ConvergenceError("lineage receipt leaves a conflicting source dependency in place")
        if not removals <= set(old_after):
            raise ConvergenceError("lineage receipt removes a dependency absent from the frozen DAG")
        consumer_updates.append({"task_id": consumer,
            "after": [dependency for dependency in old_after if dependency not in removals and dependency != task_id] + [task_id],
            "remove_after": sorted(removals)})
    expected_predecessors = set()
    pending = [dependency for consumer in consumers for dependency in tasks[consumer].get("after", [])
               if dependency not in affected_ids]
    while pending:
        dependency = pending.pop()
        if dependency in expected_predecessors:
            continue
        if dependency not in tasks or dependency in affected_ids:
            raise ConvergenceError("nonconflicting predecessor closure contains an invalid task")
        expected_predecessors.add(dependency)
        dependencies = tasks[dependency].get("after", [])
        if not isinstance(dependencies, list):
            raise ConvergenceError("predecessor task prerequisites are malformed")
        pending.extend(dependencies)
    if set(predecessor_ids) != expected_predecessors:
        raise ConvergenceError("bootstrap prerequisite closure is not the minimum frozen closure")

    convergence = {"id": task_id, "kind": "implement", "title": "Converge authorized conflict paths",
                   "objective": "Combine both frozen owner requirements on the current nonconflicting base, preserving both source deltas.",
                   "after": sorted(set(predecessor_ids)), "repository": repo_id,
                   "milestone_id": next(iter(milestone_ids)), "covers": covers,
                   "expected_paths": sorted(relevant_paths), "owned_paths": sorted(relevant_paths),
                   "requirements": requirements,
                   "acceptance_criteria": [*prior_acceptance,
                       "Both original accepted snapshots remain immutable source evidence",
                       "Both source requirements are satisfied in the converged result",
                       "No conflict markers remain on authorized paths",
                       "Every nonconflicting source blob remains byte-identical; overlapping deltas satisfy both requirements",
                       "Every source delta is preserved byte-for-byte or its semantic equivalent is demonstrated",
                       "Candidate remains unaccepted until independent checks pass"],
                   "verification": [{**check, "created_by": task_id} for check in checks] +
                                  [{"type": "command", "value": "git diff --check", "created_by": task_id,
                                    "purpose": "Whitespace and patch integrity", "category": "quality"}],
                   "recovery_task": True, "recovery_owner_tasks": affected_ids,
                   "bootstrap": {"required": True, "producer": "prepare_conflict_bootstrap",
                       "source_digests": list(selected.source_digests), "accepted_map_digest": selected.accepted_map_digest,
                       "parents": [side["snapshot_sha"] for side in source_sides], "marker_paths": marker_paths,
                       "current_base": {"task_id": base["task_id"], "accepted_attempt_id": base["accepted_attempt_id"],
                                        "snapshot_sha": base["snapshot_sha"]},
                       "after": sorted(set(predecessor_ids)), "never_select_as_accepted_base": True}}

    rebuilt = []
    if stale:
        stale_task_id = envelope.get("stale_descendant_task_id")
        if stale_task_id not in tasks or stale_task_id in affected_ids:
            raise ConvergenceError("stale descendant identity is missing or conflicts with a source")
        previous = tasks[stale_task_id]
        old_base = envelope.get("stale_descendant_base_sha")
        old_snapshot = envelope.get("stale_descendant_snapshot_sha")
        delta_paths = _unique(envelope.get("stale_descendant_delta_paths"), "stale descendant delta paths")
        previous_paths = previous.get("expected_paths", [])
        if not isinstance(old_base, str) or not _SHA.fullmatch(old_base) or \
                not isinstance(old_snapshot, str) or not _SHA.fullmatch(old_snapshot) or not delta_paths or \
                not isinstance(previous_paths, list) or any(not any(
                    path == prefix or path.startswith(prefix.rstrip("/") + "/")
                    for prefix in previous_paths if isinstance(prefix, str)) for path in delta_paths):
            raise ConvergenceError("stale descendant exact prior delta is required")
        task_numbers = [int(match.group(1)) for task_key in [*tasks, task_id]
                        if (match := re.fullmatch(r"T([0-9]+)", task_key))]
        max_task_number = max(task_numbers, default=0)
        rebuild_id = envelope.get("stale_descendant_rebuild_task_id", f"T{max_task_number + 1}")
        if not isinstance(rebuild_id, str) or not re.fullmatch(r"T[0-9]+", rebuild_id) or rebuild_id in tasks:
            raise ConvergenceError("stale descendant rebuild identity must be fresh")
        previous_checks = previous.get("verification", [])
        rebuilt.append({"id": rebuild_id, "kind": "implement", "title": f"Rebuild stale descendant {stale_task_id}",
                        "objective": f"Reapply the exact prior delta from {stale_task_id} onto the accepted convergence base.",
                        "after": [task_id], "repository": previous.get("repository", repo_id),
                        "milestone_id": previous.get("milestone_id"),
                        "covers": copy.deepcopy(previous.get("covers", [])),
                        "expected_paths": copy.deepcopy(previous_paths),
                        "preservation_input": {"base_sha": old_base, "snapshot_sha": old_snapshot,
                                               "snapshot_attempt_id": envelope.get("stale_descendant_attempt_id"),
                                               "paths": delta_paths},
                        "acceptance_criteria": copy.deepcopy(previous.get("acceptance_criteria", [])),
                        "verification": [{**copy.deepcopy(check), "created_by": rebuild_id}
                                         for check in previous_checks if _command(check)],
                        "unaccepted_until_independent_checks": True})

    # The caller may use these declarations while it builds the M1-authorized revision.
    # No ref or accepted-map override is produced here.
    rewire = {consumer: task_id for consumer in consumers}
    if future_defect:
        future_order = envelope.get("demonstrated_future_order")
        if not isinstance(future_order, dict) or not future_order:
            raise ConvergenceError("demonstrated future ownership/order evidence is required")
        if any(not isinstance(key, str) or not isinstance(value, list) for key, value in future_order.items()):
            raise ConvergenceError("demonstrated future order is malformed")
    replaced_ids = sorted({old_id for update in consumer_updates for old_id in update["remove_after"]})
    bootstrap = {"schema_version": "conflict-bootstrap/1", "task_id": task_id,
        "paths": marker_paths, "consumer_task_ids": sorted(consumers),
        "preservation_inputs": [{"task_id": side["task_id"], "attempt_id": side["attempt_id"],
                                  "snapshot_sha": side["snapshot_sha"], "tree_sha": side["tree_sha"]}
                                 for side in preservation],
        "source_digests": list(observed.evidence_digests), "accepted_map_digest": selected.accepted_map_digest,
        "current_base": {"task_id": base["task_id"], "accepted_attempt_id": base["accepted_attempt_id"],
                         "snapshot_sha": base["snapshot_sha"]}, "after": sorted(set(predecessor_ids)),
        "affected_task_ids": affected_ids, "retained_acceptance": affected_ids,
        "rebuilt_acceptance": [item["id"] for item in rebuilt], "source_snapshots": preservation,
        "verification_scope": checks, "observation_digest": _digest(envelope),
        "strategy_id": selected.strategy_id,
        "future_order": copy.deepcopy(envelope.get("demonstrated_future_order", {})),
        "result_base": {"kind": "accepted_convergence_attempt", "task_id": task_id,
                        "lookup": "M1.accepted_attempt -> M3.snapshot", "pre_acceptance_pointer": None},
        "integration": {"command_only": True, "independent_audit_required": True,
                        "cross_check_required": True, "max_corrective_tasks": 8,
                        "ordinary_attempt_limits_inherited": True}}
    if 1 + len(rebuilt) > bt_recovery_cycle.POLICY["max_corrective_tasks"]:
        raise ConvergenceError("recovery would add more corrective tasks than the cycle allows")
    return {"schema_version": SCHEMA, "convergence_task": convergence, "rebuilt_tasks": rebuilt,
            "consumer_updates": consumer_updates, "bootstrap": bootstrap,
            "replaced_task_ids": replaced_ids,
            "evidence_refs": ["conflict:" + digest_value for digest_value in observed.evidence_digests],
            "actions": []}
