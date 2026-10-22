"""Pure causal classification and bounded correlation helpers for conflict evidence."""
from __future__ import annotations

import hashlib
import json

from .conflict_contracts import ConflictLineageFacts, ConflictObservation, ConflictPlanFacts
from .diagnostic_contracts import DiagnosticCase, RecoveryProposal
from .validation import require


def classify_conflict(observation: ConflictObservation | dict, plan_facts: ConflictPlanFacts | dict,
                      lineage_facts: ConflictLineageFacts | dict) -> dict:
    """Classify validated data and return facts/actions only; no commands or side effects."""
    if type(observation) is dict:
        observation = ConflictObservation.from_dict(observation)
    if type(plan_facts) is dict:
        plan_facts = ConflictPlanFacts.from_dict(plan_facts)
    if type(lineage_facts) is dict:
        lineage_facts = ConflictLineageFacts.from_dict(lineage_facts)
    require(type(observation) is ConflictObservation and type(plan_facts) is ConflictPlanFacts and
            type(lineage_facts) is ConflictLineageFacts)

    # The adapter supplies current owner authority. It dominates every observed cause.
    if plan_facts.authority_status != "authorized":
        dominant = "owner_stop" if plan_facts.authority_status == "owner_stop" else "missing_authority"
        return _decision(dominant, observation, lineage_facts, (), (dominant,))

    identity_matches = all((observation.source_type == plan_facts.source_type,
        observation.run_id == plan_facts.run_id, observation.plan_id == plan_facts.plan_id,
        observation.revision == plan_facts.revision, observation.plan_sha256 == plan_facts.plan_sha256,
        observation.task_id == plan_facts.task_id, observation.attempt_id == plan_facts.attempt_id,
        observation.token == plan_facts.token, observation.consumer_id == plan_facts.consumer_id,
        observation.repository_id == plan_facts.repository_id))
    complete = (identity_matches and bool(observation.paths) and len(observation.sides) >= 2 and
                bool(observation.original_merge_base) and bool(observation.evidence_digests) and
                lineage_facts.evidence_complete and lineage_facts.status != "unknown")
    if not complete:
        return _decision("evidence_incomplete", observation, lineage_facts, (), ("evidence_incomplete",))

    approved_paths = (plan_facts.approved_start_paths if observation.source_type == "start"
                      else plan_facts.approved_integration_paths)
    escaped = tuple(sorted(set(observation.paths) - set(approved_paths)))
    if escaped:
        return _decision("scope_escape", observation, lineage_facts, (), ("scope_escape",), {
            "out_of_scope_paths": list(escaped), "candidate_rejected": True,
            "accepted_sources_preserved": True, "permission_expanded": False,
        })

    if lineage_facts.semantic_conflict:
        return _decision("semantic_conflict", observation, lineage_facts, (), ("semantic_conflict",), {
            "incompatible_requirements": list(lineage_facts.incompatible_requirements),
        })

    if lineage_facts.status == "stale":
        actions = ["rebuild_stale_descendant"]
        if lineage_facts.ownership_or_order_defect:
            actions.append("converge_owned_paths")
            if lineage_facts.demonstrated_future_defect:
                actions.append("repair_demonstrated_future_ownership_order")
        actions.append("inherit_additive_checks")
        return _decision("stale_lineage", observation, lineage_facts, tuple(actions), ("stale_lineage",))

    if lineage_facts.ownership_or_order_defect:
        actions = ["converge_owned_paths"]
        if lineage_facts.demonstrated_future_defect:
            actions.append("repair_demonstrated_future_ownership_order")
        actions.append("inherit_additive_checks")
        return _decision("ownership_or_order_defect", observation, lineage_facts,
                         tuple(actions), ("ownership_or_order_defect",))

    # Path overlap is evidence about the conflict, never proof of an ownership/order defect.
    return _decision("structural_conflict_unclassified", observation, lineage_facts, (),
                     ("structural_conflict_unclassified",))


def _decision(dominant: str, observation: ConflictObservation, lineage: ConflictLineageFacts,
              actions: tuple[str, ...], blockers: tuple[str, ...], extra: dict | None = None) -> dict:
    return {"schema_version": "conflict-decision/1", "dominant": dominant,
            "blockers": list(blockers), "allowable_actions": list(actions),
            "facts": {"source_type": observation.source_type, "run_id": observation.run_id,
                      "plan_id": observation.plan_id, "revision": observation.revision,
                      "plan_sha256": observation.plan_sha256, "task_id": observation.task_id,
                      "attempt_id": observation.attempt_id, "repository_id": observation.repository_id,
                      "paths": list(observation.paths), "lineage_status": lineage.status,
                      "lineage_aliases": list(lineage.aliases), **(extra or {})}}


def conflict_case(observation: ConflictObservation, *, lineage_facts: ConflictLineageFacts,
                  existing_case: DiagnosticCase | None = None) -> DiagnosticCase:
    """Reuse an existing integration-conflict case; unknown lineage cannot create a cycle."""
    require(type(observation) is ConflictObservation and type(lineage_facts) is ConflictLineageFacts)
    if existing_case is not None:
        require(type(existing_case) is DiagnosticCase and existing_case.symptom == "integration_conflict" and
                existing_case.run_id == observation.run_id and existing_case.plan_id == observation.plan_id)
        return existing_case
    require(lineage_facts.status != "unknown", "LINEAGE_UNKNOWN")
    trigger = "conflict-" + hashlib.sha256(
        f"{observation.run_id}:{observation.plan_id}:{observation.task_id}".encode()).hexdigest()[:32]
    return DiagnosticCase(trigger, observation.run_id, observation.plan_id, observation.revision,
                          observation.plan_sha256, "integration_conflict", ())


def initial_conflict_advice(case: DiagnosticCase, evidence_ref: str) -> RecoveryProposal:
    """Create the typed, non-executable initial /1 blocker advice."""
    require(type(case) is DiagnosticCase and case.symptom == "integration_conflict")
    return RecoveryProposal(case.trigger_id, 0, "block", "structural_conflict_review", (evidence_ref,), "confirmed")


def conflict_envelope_payload(observation: ConflictObservation, lineage_facts: ConflictLineageFacts) -> dict:
    """Build a validated payload suitable for an existing CAS event or checkpoint."""
    require(type(observation) is ConflictObservation and type(lineage_facts) is ConflictLineageFacts)
    # Unknown lineage may reuse a known case but cannot establish or persist new aliases.
    aliases = lineage_facts.aliases if lineage_facts.status != "unknown" else ()
    canonical = sorted(set(aliases))
    alias_digest = hashlib.sha256(json.dumps(canonical, separators=(",", ":")).encode()).hexdigest()
    return {"schema_version": "conflict-envelope-payload/1", "observation": observation.to_dict(),
            "lineage_aliases": canonical, "lineage_alias_digest": alias_digest}


